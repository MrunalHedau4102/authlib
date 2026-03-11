# 2FA Setup, Usage & Developer Care Guide

## Introduction

This guide provides practical instructions for users enabling 2FA, developers integrating 2FA endpoints, and important security considerations and edge cases to handle.

---

## Part 1: User Guide - How to Enable 2FA

### 1.1 Prerequisites
- An active AuthLib account
- Valid JWT access token
- An authenticator app installed on mobile/computer

### 1.2 Supported Authenticator Apps
2FA uses TOTP (Time-Based One-Time Password) standard. Compatible apps include:

- **Google Authenticator** (iOS, Android) - Most common
- **Microsoft Authenticator** (iOS, Android)
- **Authy** (iOS, Android, Desktop) - Multi-device support
- **FreeOTP** (iOS, Android, Desktop) - Open source
- **1Password** (iOS, Android, Desktop) - Part of password manager
- **LastPass Authenticator** (iOS, Android)
- **Duo Security** (iOS, Android)

**Recommendation**: Use Authy or 1Password for cloud backup options.

### 1.3 Step-by-Step: Enable 2FA

#### Step 1: Request 2FA Setup
```bash
curl -X GET http://localhost:5000/api/auth/2fa/setup \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response**:
```json
{
  "secret": "CTYRZGCOMTEDUSUELJZZ6HASKOK6DJOD",
  "provisioning_uri": "otpauth://totp/AuthLib:user%40example.com?secret=CTYRZGCOMTEDUSUELJZZ6HASKOK6DJOD&issuer=AuthLib"
}
```

#### Step 2: Scan QR Code (Generated from provisioning_uri)
- **In Web UI**: Generate QR code from `provisioning_uri` using any QR library
- **Mobile**: Authenticator app → Add → "Scan QR Code"
- **Manual Entry**: If QR scan fails, use the `secret` value (CTYRZG...)

#### Step 3: Get Code from Authenticator App
- Open your authenticator app
- Find "AuthLib" entry
- Read the 6-digit code (refreshes every 30 seconds)

#### Step 4: Verify OTP Code
```bash
curl -X POST http://localhost:5000/api/auth/2fa/verify-setup \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "secret": "CTYRZGCOMTEDUSUELJZZ6HASKOK6DJOD",
    "otp_code": "123456"
  }'
```

**Response**:
```json
{
  "message": "2FA enabled successfully"
}
```

**Status**: ✓ 2FA is now ENABLED

### 1.4 Backup Codes (Recommended for Production)
**Note**: Current implementation does not generate backup codes. For production:
1. Generate backup codes during 2FA setup
2. Display once to user (non-recoverable)
3. Store hashed backup codes in database
4. Allow single-use backup code if 2FA device lost
5. Prompt user to regenerate after use

**Recommended Libraries**: PyOTP + custom backup code generation

---

## Part 2: User Guide - Logging In with 2FA

### 2.1 Login Flow: Step 1 (Credentials)

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

**Response if 2FA Enabled**:
```json
{
  "requires_2fa": true,
  "otp_verification_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6InVzZXJAZXhhbXBsZS5jb20iLCJ0b2tlbl90eXBlIjoib3RwX3ZlcmlmaWNhdGlvbiIsImlhdCI6MTcwODQyMzQ4MCwiZXhwIjoxNzA4NDIzNzgwfQ.signature",
  "user_id": 1
}
```

**Status**: 401 (Unauthorized - not yet fully authenticated)

### 2.2 Login Flow: Step 2 (OTP Verification)

**Prompt User**: "Enter the 6-digit code from your Authenticator app"

```bash
curl -X POST http://localhost:5000/api/auth/login/verify-otp \
  -H "Content-Type: application/json" \
  -d '{
    "otp_verification_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "otp_code": "123456"
  }'
```

**Response if OTP Valid**:
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true,
    "is_verified": true,
    "is_two_factor_enabled": true,
    "created_at": "2024-02-15T10:30:00Z",
    "updated_at": "2024-02-15T10:30:00Z",
    "last_login": "2024-02-15T14:25:00Z"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6InVzZXJAZXhhbXBsZS5jb20iLCJ0b2tlbl90eXBlIjoiYWNjZXNzIn0.signature",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6InVzZXJAZXhhbXBsZS5jb20iLCJ0b2tlbl90eXBlIjoicmVmcmVzaCJ9.signature",
  "token_type": "Bearer"
}
```

**Status**: 200 (OK - fully authenticated)

**Now Use**: Access token for subsequent API requests

### 2.3 Login Flow: Disabled 2FA (No Changes)

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

**Response if 2FA NOT Enabled**:
```json
{
  "user": { ... },
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "Bearer"
}
```

**Status**: 200 (OK - immediately authenticated)

**No changes**: Behaves exactly like before

---

## Part 3: User Guide - How to Disable 2FA

### 3.1 Prerequisites
- Valid JWT access token
- Current password
- (Optional) Current OTP code for verification

### 3.2 Disable 2FA

```bash
curl -X POST http://localhost:5000/api/auth/2fa/disable \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "password": "UserPassword123!",
    "otp_code": "123456"
  }'
```

**Response**:
```json
{
  "message": "2FA disabled successfully"
}
```

**Status**: ✗ 2FA is now DISABLED

### 3.3 After Disabling
- Next login requires only email + password
- No authenticator app needed
- 2FA can be re-enabled anytime

---

## Part 4: Security Best Practices

### 4.1 Secret Management

**DO's**:
- ✓ Store authenticator app securely (use device PIN/biometric)
- ✓ Use strong device/phone security measures
- ✓ Save secret in multiple locations if using backup/export features
- ✓ Use password manager for non-authenticator passwords

**DON'Ts**:
- ✗ Share 2FA secret with anyone
- ✗ Screenshot or email the secret
- ✗ Store secret in plaintext notes
- ✗ Use the same authenticator key on multiple devices without backup plan

### 4.2 Backup & Recovery

**Implement (Production Required)**:
- [ ] Backup codes generation during 2FA setup (10-20 single-use codes)
- [ ] Display backup codes in UI with prompt to save (PDF, print, note)
- [ ] Explain: "If you lose your authenticator, use these codes"
- [ ] Hashed backup codes stored in database
- [ ] Backup codes consumed after use (cannot reuse)

**User Action**:
- Save backup codes in password manager
- Print and store in secure location
- Use only when authenticator unavailable

### 4.3 Lost Authenticator Device

**Recovery Process** (implement in app):
1. User cannot login (OTP required unavailable)
2. Implement "Lost Authenticator" panic route:
   - Verify email ownership (send recovery link)
   - Verify identity (security questions / secondary email / phone)
   - Force 2FA disable via recovery process
3. User re-enables with new authenticator

**Current Status**: ⚠️ Not implemented (requires admin interface)

### 4.4 Rate Limiting (Implementation Required)

Add to controllers (not in core library):

**Flask**:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route("/api/auth/2fa/verify-setup", methods=["POST"])
@limiter.limit("5 per minute")  # 5 attempts per minute
def verify_2fa_setup():
    ...

@app.route("/api/auth/login/verify-otp", methods=["POST"])
@limiter.limit("5 per minute")  # 5 OTP attempts per minute
def login_verify_otp():
    ...
```

**FastAPI**:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/auth/2fa/verify-setup")
@limiter.limit("5/minute")
async def verify_2fa_setup(request: Verify2FASetupRequest):
    ...
```

### 4.5 Logging & Monitoring

**What TO Log**:
- ✓ 2FA enabled/disabled events (user_id, timestamp)
- ✓ Failed OTP attempts (count, blocking triggers)
- ✓ Suspicious patterns (rapid repeated failures)
- ✓ Successful 2FA login

**What NOT to Log**:
- ✗ two_factor_secret (NEVER)
- ✗ OTP codes (NEVER)
- ✗ Any PII beyond user_id

**Recommended Logging**:
```python
# Good - log event without secrets
logger.info("2FA enabled", extra={
    "user_id": user.id,
    "timestamp": datetime.now(timezone.utc),
    "action": "2fa_setup_verified"
})

# Bad - never do this
logger.info(f"Secret: {secret}, OTP: {otp_code}")  # ✗ WRONG
```

### 4.6 HTTPS/TLS Mandatory

**Requirement**:
- Always use HTTPS in production
- TOTP tokens transmit over TLS
- OTP codes never in logs, URLs, error messages
- Certificates from trusted CA (Let's Encrypt, DigiCert, etc.)

---

## Part 5: Edge Cases & Handling

### 5.1 OTP Token Expired (5-minute window)

**Scenario**: User enters credentials → starts entering OTP → 5 minutes pass

**Current Behavior**:
- OTP token expires
- POST /auth/login/verify-otp returns: `InvalidToken (401)`
- Client must handle: "Session expired, please login again"

**Fix in Client**:
```javascript
async function loginWith2FA(token, otp) {
  try {
    const response = await fetch('/api/auth/login/verify-otp', {
      method: 'POST',
      body: JSON.stringify({ otp_verification_token: token, otp_code: otp })
    });
    
    if (response.status === 401) {
      const data = await response.json();
      if (data.error.includes('expired')) {
        alert('Session expired. Please login again.');
        // Redirect to login page
        window.location.href = '/login';
      }
    }
  } catch (err) { ... }
}
```

### 5.2 Clock Skew (Server/Client Time Mismatch)

**Scenario**: Server clock is ahead/behind client authenticator app

**TOTP Tolerance**: ±30 seconds (pyotp `valid_window=1`)
- Current 30-sec period: accepted
- Previous period (30-59 sec ago): accepted
- Next period (30 sec from now): accepted
- Total window: ±60 seconds

**If Still Invalid**:
- User gets: "Invalid OTP code"
- Server admin should check: System time synchronization
- Solution: Sync server to NTP (Network Time Protocol)

### 5.3 User Disabled 2FA Externally

**Scenario**: Admin disables 2FA via database, but user still has secret

**Current Behavior**:
- User authenticator still shows code
- User tries to login with OTP
- verify_otp() checks: `is_two_factor_enabled = False` → ValidationError

**Prevention**:
- Don't manually disable 2FA via DB
- Use proper disable endpoint with password verification
- Log all 2FA state changes

### 5.4 Multiple Authenticator Devices

**Scenario**: User wants same account on phone + computer

**Current Design**: Single shared secret (one device per user)

**Doesn't Support**: Multiple independent secrets

**Workaround**:
- Most authenticator apps (Authy, 1Password) support multi-device sync
- Same secret displayed on multiple devices
- Any device can generate valid OTP

### 5.5 OTP Code Re-entry

**Scenario**: User enters OTP code twice by mistake

**TOTP Behavior**:
- First entry: Valid ✓ → Session created
- Second entry: Attempt creates new session with same OTP
- Same OTP within 30-sec window: Valid ✓ (can be reused in window)

**Prevention**:
- Once OTP verified → issue JWT immediately
- JWT guards subsequent requests (not OTP)
- Same OTP in different window: Different value (time-based)

### 5.6 User Forgets Password but Has 2FA

**Scenario**: User loses password, can't login even with authenticator

**Current Limitations**:
- Password reset flow doesn't interact with 2FA
- User cannot disable 2FA without authentication

**Solution** (implement):
```python
@app.post("/api/auth/password-reset/from-2fa")
def password_reset_with_2fa(
    email: str,
    otp_code: str  # Verify identity via authenticator
):
    """
    Allow password reset if user can prove 2FA authenticator ownership
    """
    user = get_user_by_email(email)
    
    if not user.is_two_factor_enabled:
        raise ValidationError("User doesn't have 2FA enabled")
    
    # Verify OTP to prove authenticator ownership
    if not verify_otp(user.id, otp_code):
        raise InvalidOTP("Invalid OTP code")
    
    # Generate password reset token
    token = jwt_handler.create_password_reset_token(user.id, user.email)
    
    # Send email with reset link
    send_password_reset_email(user.email, token)
    
    return {"message": "Password reset email sent"}
```

### 5.7 Concurrent 2FA Requests

**Scenario**: User generates 2FA secret → starts setup → generates new secret → tries old secret

**Current Behavior**:
- setup_2fa() generates new secret each time (old not stored)
- verify_2fa_setup_with_secret() expects exact secret provided by user
- Old secret will fail verification (not what was sent)

**Prevents**: Confusion about which secret to use

---

## Part 6: Developer Care Items - CRITICAL

### 6.1 NEVER Log Secrets or Codes

**Regular Code Review Checklist**:
- [ ] No `two_factor_secret` in log statements
- [ ] No `otp_code` in log statements
- [ ] No `provisioning_uri` in error responses (contains secret in URL)
- [ ] No stack traces revealing secret values
- [ ] Use structured logging with whitelisted fields

**Implementation**:
```python
# ✓ GOOD
logger.info("2FA setup verified", extra={"user_id": user_id})

# ✗ BAD
logger.info(f"2FA verified for user {user_id} with secret {secret}")

# ✗ BAD
print(f"OTP verification: {otp_code}")  # Remove all print debugging

# ✓ GOOD - structured
logger.info(
    "2fa_setup_verified",
    extra={
        "user_id": user_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": "2fa_enable"
    }
)
```

### 6.2 Always Use PyOTP for Validation

**Requirement**: Never implement TOTP from scratch

**Why**:
- Time-window handling complex
- Clock skew tolerance critical
- Replay prevention subtle
- Standard library (pyotp) battle-tested

**Usage**:
```python
# ✓ CORRECT
import pyotp
totp = pyotp.TOTP(secret)
is_valid = totp.verify(otp_code, valid_window=1)

# ✗ WRONG - don't implement yourself
def verify_otp_custom(secret, code, timestamp):
    # This is error-prone, use pyotp instead
    pass
```

### 6.3 OTP Time Window Details

**Current Implementation**:
```python
totp.verify(otp_code, valid_window=1)
```

**What This Means**:
- Time step: 30 seconds (pyotp default, TOTP standard)
- valid_window=1 means:
  - t-30s: valid (previous period)
  - t: valid (current period)
  - t+30s: valid (next period)
  - Total window: ±60 seconds

**DO NOT CHANGE** unless you understand TOTP RFC.

**If Clock Skew Issues**:
- Increase window: `valid_window=2` (±90 seconds)
- Better Solution: Fix server clock synchronization

### 6.4 Secret Must Be Securely Stored

**Current (Development)**:
- Plaintext in SQLite database
- Fine for dev/testing

**Production Requirements**:
```python
# Use SQLAlchemy-Crypto or similar
from cryptography.fernet import Fernet

class User(Base):
    two_factor_secret = Column(
        EncryptedType(String, "encryption_key", AesEngine),
        nullable=True
    )
```

**Better Approach**:
- Encrypt at rest (database column encryption)
- Decrypt only when needed for OTP verification
- Never store in plaintext in production

### 6.5 Don't Expose Secret After Setup

**Current API**:
```
Response: { secret, provisioning_uri }
↓
Client scans QR from provisioning_uri
↓
Client calls verify endpoint with { secret, otp_code }
↓
Secret is used ONCE for validation
↓
Secret is THEN persisted to database
```

**Key Point**: Secret not stored until after verification

**Bad Pattern** ✗:
```python
# Don't do this:
user.two_factor_secret = secret
session.commit()  # Stored immediately

# Then client calls verify...
# If verify fails, secret already in database (wrong)
```

**Good Pattern** ✓:
```python
# Do this:
# 1. Generate and return secret (not stored)
secret = pyotp.random_base32()
return { secret, provisioning_uri }

# 2. Client verifies
# 3. Only then store:
user.enable_2fa(secret)  # enable_2fa sets the fields and commits
```

### 6.6 Invalid/Expired OTP Handling

**Must Return Generic Error**:
```python
# ✓ GOOD - no information leakage
raise InvalidOTP("Invalid or expired OTP code")

# ✗ BAD - reveals too much
raise InvalidOTP(f"OTP code {code} is invalid for secret {secret}")
raise InvalidOTP("OTP code expired 15 seconds ago")
```

**Why**: Attackers learn nothing about:
- What the valid code is
- Whether we even have 2FA enabled for this user
- How close they were

### 6.7 Password Verification Required for Disable

**NOT Optional**:
```python
def disable_2fa(user_id, user_password, otp_code=None):
    # Password verification is MANDATORY
    verify_password(user_password)  # Raises if wrong
    
    # OTP is optional but recommended
    if otp_code:
        verify_otp(user_id, otp_code)
    
    user.disable_2fa()
```

**Why**: Prevents attacker with stolen access token from disabling 2FA

**Attack Scenario**:
```
Attacker steals JWT token
↓
Tries: DELETE /api/auth/2fa without password check
↓
2FA disabled ✗ (bad)
↓
Attacker now has permanent access
```

**With Password Check**:
```
Attacker steals JWT token (but not password)
↓
Tries: DELETE /api/auth/2fa
↓
Endpoint requires: password
↓
Request fails ✓ (good)
↓
User password still safe
```

### 6.8 Handle All Exception Types

**In Controllers**: Catch and map to HTTP status

```python
try:
    result = auth_service.verify_otp(user_id, otp_code)
except InvalidOTP:
    return JSONResponse(
        status_code=401,
        content={"error": "Invalid or expired OTP code"}
    )
except UserNotFound:
    return JSONResponse(
        status_code=404,
        content={"error": "User not found"}
    )
except ValidationError:
    return JSONResponse(
        status_code=400,
        content={"error": "Invalid input format"}
    )
except DatabaseError:
    return JSONResponse(
        status_code=500,
        content={"error": "Database error"}
    )
```

### 6.9 Test Coverage Checklist

**Unit Tests** (already provided):
- [ ] ✓ setup_2fa() generates valid provisioning URI
- [ ] ✓ verify_2fa_setup() with valid OTP enables 2FA
- [ ] ✓ verify_2fa_setup() with invalid OTP rejects
- [ ] ✓ verify_otp() validates during login
- [ ] ✓ disable_2fa() requires password
- [ ] ✓ OTP token expires after 5 minutes
- [ ] ✓ Login returns 401 with 2FA required
- [ ] ✓ Complete 2FA login returns JWT tokens

**Integration Tests** (implement):
- [ ] End-to-end: signup → enable 2FA → login with 2FA → logout
- [ ] Clock skew: test ±30 sec windows
- [ ] Concurrent requests: parallel 2FA setup attempts
- [ ] Rate limiting: 10 failed OTP attempts → block
- [ ] Password reset when 2FA enabled
- [ ] Database: secret persisted correctly, encrypted

**Security Tests** (implement):
- [ ] OTP codes don't appear in logs
- [ ] Secret not in error messages/stack traces
- [ ] Expired OTP tokens rejected
- [ ] Invalid signatures rejected
- [ ] HTTPS enforced

### 6.10 Monitoring & Alerting

**Metrics to Track**:
- 2FA setup completion rate (?)
- 2FA disable rate (users leaving)
- OTP verification success rate (?)
- OTP attempt failures (brute force detection)
- Average OTP entry time (too long = confusion)

**Alerts to Set Up**:
- ⚠️ User account: 10 failed OTP in 5 minutes → block 2FA login
- ⚠️ Server: OTP token generation failures → check time sync
- ⚠️ Database: 2FA secret encryption key access → audit
- ⚠️ Logs: Any log line containing potential secret patterns

---

## Part 7: Integration Checklist

### 7.1 Library Integration (For Library Authors)

- [x] ✓ Add pyotp dependency
- [x] ✓ Extend User model with 2FA fields
- [x] ✓ Add OTP token types to JWT handler
- [x] ✓ Implement 2FA methods in AuthService
- [x] ✓ Add new exception types
- [x] ✓ Extend examples (Flask + FastAPI)
- [x] ✓ Comprehensive test coverage
- [x] ✓ This documentation

### 7.2 Client Application Integration

- [ ] Add 2FA UI screens:
  - [ ] "Setup 2FA" button in settings
  - [ ] QR code display + manual entry option
  - [ ] OTP code entry form (6 digits)
  - [ ] "Disable 2FA" button with password confirmation
  - [ ] Login flow recognizing `requires_2fa: true`

- [ ] Implement OTP verification endpoint call
- [ ] Handle error cases:
  - [ ] Invalid OTP → retry
  - [ ] Expired token → re-login
  - [ ] Network error → retry logic
- [ ] Rate limiting detection (429 Too Many Requests)
- [ ] Store OTP verification token securely (memory, not localStorage)
- [ ] Clear OTP token after login completes or on logout

### 7.3 DevOps/Deployment

- [ ] Database migration: Add 2FA columns to users table
- [ ] Encryption at rest: Enable for `two_factor_secret` column
- [ ] HTTPS: Mandatory for production
- [ ] NTP sync: Server clock synchronized to network time
- [ ] Secrets management: JWT_SECRET_KEY in secure vault, not VCS
- [ ] Logging: Configure to exclude secrets (regex patterns)
- [ ] Monitoring: Set up OTP failure alerts
- [ ] Rate limiting: Implement on API gateways or middleware
- [ ] Backup: Test recovery procedure for lost authenticator scenario

### 7.4 Documentation

- [ ] API documentation updated with 2FA endpoints
- [ ] User-facing help articles
- [ ] Troubleshooting guide (e.g., "My code won't work")
- [ ] Security best practices for users
- [ ] Admin guide: How to help users recover from lost devices

---

## Part 8: Backward Compatibility Guarantees

### 8.1 No Breaking Changes

**For Existing Users Without 2FA**:
- `is_two_factor_enabled = False` by default
- `two_factor_secret = NULL`
- Login behavior identical (email + password only)
- Existing JWT tokens work unchanged
- All endpoints return Same responses as before (new fields are additive)

**For Existing Code**:
- Login endpoint returns extra fields if 2FA enabled (client must check `requires_2fa` flag)
- User dict includes `is_two_factor_enabled` (new field, safe to ignore)
- No changes required to existing auth flow logic
- Password reset flow unchanged

### 8.2 Migration Path

```
Current Version (No 2FA)
    ↓
Add pyotp to requirements.txt
    ↓
Run database migrations (add 2FA columns)
    ↓
Deploy updated library
    ↓
✓ No data loss ✓ No service interruption
    ↓
Clients can optionally support 2FA
Users can optionally enable 2FA
```

---

## Conclusion

TOTP-based 2FA enhances security while maintaining full backward compatibility. Key responsibilities:

**For Users**:
- Enable 2FA for account security
- Store authenticator app securely
- Save backup codes if available
- Maintain secure password

**For Developers**:
- Never log secrets or OTP codes
- Always use pyotp for validation
- Require password for sensitive actions
- Implement rate limiting on endpoints
- Test thoroughly before deployment

**For Administrators**:
- Monitor 2FA usage and failures
- Ensure NTP time sync
- Maintain encryption keys
- Prepare recovery procedures
- Update disaster recovery plans

---

## References

- [TOTP (RFC 6238)](https://tools.ietf.org/html/rfc6238) - Time-Based One-Time Password Algorithm
- [PyOTP Documentation](https://pyauth.github.io/pyotp/)
- [NIST Authentication Guidelines](https://pages.nist.gov/800-63-3/)
- [Google Authenticator](https://support.google.com/accounts/answer/1066447)
- [Authy Documentation](https://authy.com/guides/)
