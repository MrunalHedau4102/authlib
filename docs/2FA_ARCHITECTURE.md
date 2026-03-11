# Two-Factor Authentication (2FA) Architecture

## Overview

This document describes the architecture and flow of TOTP-based Two-Factor Authentication (2FA) in AuthLib. The system integrates seamlessly with the existing JWT-based authentication framework while maintaining full backward compatibility.

---

## 1. Component Architecture

### 1.1 System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                          CLIENT / UI                             │
├─────────────────────────────────────────────────────────────────┤
│  - Browser / Mobile App                                          │
│  - Authenticator App (Google Authenticator, Authy, etc.)         │
│  - HTTP Client / API Client                                      │
└──────────────────┬──────────────────────────────────────────────┘
                   │ HTTP / REST API
┌──────────────────▼──────────────────────────────────────────────┐
│                   FLASK / FASTAPI CONTROLLER                     │
├─────────────────────────────────────────────────────────────────┤
│  - Route Handlers                                                │
│  - Request/Response Serialization                                │
│  - Exception Handling (AuthException → HTTP Status Codes)        │
│  - Endpoints:                                                    │
│    • POST /auth/login                                            │
│    • POST /auth/login/verify-otp                                 │
│    • GET  /auth/2fa/setup                                        │
│    • POST /auth/2fa/verify-setup                                 │
│    • POST /auth/2fa/disable                                      │
└──────────────────┬──────────────────────────────────────────────┘
                   │ Session Management
┌──────────────────▼──────────────────────────────────────────────┐
│                    AUTHSERVICE (Orchestration)                   │
├─────────────────────────────────────────────────────────────────┤
│  - login(email, password)                                        │
│  - setup_2fa(user_id)                                            │
│  - verify_2fa_setup_with_secret(user_id, secret, otp_code)       │
│  - verify_otp(user_id, otp_code)                                 │
│  - complete_2fa_login(otp_verification_token, otp_code)          │
│  - disable_2fa(user_id, password, otp_code)                      │
│  - _generate_tokens(user)                                        │
└──┬────┬──────────────┬────────────┬────────────────────────────┬─┘
   │    │              │            │                            │
   │    │              │            │                            │
   │    │              │            │                            │
┌──▼──┐│  │      ┌─────▼─────┐ ┌──▼──────────┐ ┌────────────────▼──┐
│USER ││  │      │JWTHANDLER │ │  PASSWORD   │ │  USERSERVICE     │
│MODEL││  │      ├───────────┤ │  HANDLER    │ ├──────────────────┤
├─────┤│  │      │ - create_ │ ├─────────────┤ │ - get_user_by_id  │
│- id ││  │      │  access_  │ │- hash_pass  │ │ - get_user_by_    │
│- email  │      │ token()   │ │- verify_    │ │  email            │
│- password  │    │ - verify_ │ │  password() │ │ - create_user()   │
│- is_2fa_   │    │ access_   │ ├─────────────┤ │ - change_password │
│  enabled   │    │ token()   │ │ Bcrypt      │ └──────────────────┘
│- 2fa_secret    │ - create_ │ │ Hash        │
│- otp_verified  │  otp_     │ │ Validation  │
│_at          │    │  verify_ │ │             │
├─────────────┤   │ token()  │ │             │
│ Methods:    │   │ - verify │ │             │
│- enable_2fa()  │  _otp_    │ ├─────────────┤
│- disable_2fa() │  verif_   │ │ Config:     │
│- get_otp_      │ token()   │ │ Cost Rounds │
│ auth_uri()  │   │          │ │             │
└─────────────┘   └──────────┘ └─────────────┘

         ┌────────────────────────┐
         │   PYOTP LIBRARY        │
         ├────────────────────────┤
         │ - random_base32()      │
         │ - TOTP.now()           │
         │ - TOTP.verify()        │
         │ - prov_uri             │
         └────────────────────────┘
         
         ┌────────────────────────┐
         │    DATABASE (SQLAlchemy)
         ├────────────────────────┤
         │ - users table          │
         │ - token_blacklist      │
         │ - indexed columns      │
         └────────────────────────┘
```

### 1.2 Component Responsibilities

| Component | Responsibility |
|-----------|-----------------|
| **Controller** | HTTP request/response handling, input validation, exception-to-status mapping |
| **AuthService** | Core 2FA business logic, orchestration of services, user state transitions |
| **User Model** | Persistence of 2FA state, TOTP secret storage, instance methods for enable/disable |
| **JWTHandler** | Create/verify OTP verification tokens, maintain token expiry windows |
| **PasswordHandler** | Secure password verification (no changes for 2FA) |
| **UserService** | User retrieval, password changes, user data management |
| **PyOTP** | TOTP secret generation, provisioning URI creation, OTP validation |
| **Database** | Persist 2FA state, enforce ACID properties |

---

## 2. Data Flow Diagrams

### 2.1 2FA Enable Flow

```
User (Browser)
    │
    ├─ GET /auth/2fa/setup
    │ (with JWT access token)
    │
    ▼
Flask/FastAPI Controller
    │
    ├─ Validate token
    ├─ Extract user_id
    │
    ▼
AuthService.setup_2fa(user_id)
    │
    ├─ UserService.get_user_by_id()
    ├─ pyotp.random_base32() → secret
    ├─ pyotp.TOTP(secret)
    ├─ totp.provisioning_uri() → otpauth:// URL
    │
    ▼
Response: { secret, provisioning_uri }
    │
    │ (Client displays QR code from provisioning_uri)
    │ (User scans with Authenticator app)
    │ (User gets 6-digit OTP from app)
    │
    ├─ POST /auth/2fa/verify-setup
    │ (with secret, otp_code, JWT token)
    │
    ▼
Flask/FastAPI Controller
    │
    ├─ Validate inputs (secret, otp_code format)
    │
    ▼
AuthService.verify_2fa_setup_with_secret(user_id, secret, otp_code)
    │
    ├─ UserService.get_user_by_id()
    ├─ pyotp.TOTP(secret).verify(otp_code, valid_window=1)
    │  │
    │  ├─ VALID: ✓
    │  │ ├─ user.enable_2fa(secret)
    │  │ │ ├─ Set: is_two_factor_enabled = True
    │  │ │ ├─ Set: two_factor_secret = secret
    │  │ │ └─ Set: otp_verified_at = now()
    │  │ ├─ session.commit()
    │  │ └─ Return: True
    │  │
    │  └─ INVALID: ✗
    │    └─ Raise: InvalidOTP (no state change)
    │
    ▼
Response: { message: "2FA enabled successfully" }

=== 2FA is now ENABLED ===
```

### 2.2 Login with 2FA Flow

```
User (Browser)
    │
    ├─ POST /auth/login
    │ { email, password }
    │
    ▼
Flask/FastAPI Controller
    │
    ├─ Validate request
    │
    ▼
AuthService.login(email, password)
    │
    ├─ EmailValidator.validate() & sanitize()
    ├─ UserService.get_user_by_email()
    │
    ├── User NOT found?
    │   └─ Raise: UserNotFound (401)
    │
    ├── User.is_active = False?
    │   └─ Raise: InvalidCredentials (401)
    │
    ├─ PasswordHandler.verify_password(password, hash)
    │
    ├── Password INVALID?
    │   └─ Raise: InvalidCredentials (401)
    │
    ├─ user.update_last_login()
    │
    ├── Is 2FA ENABLED (user.is_two_factor_enabled)?
    │   │
    │   ├─ YES → 2FA Path
    │   │ ├─ JWTHandler.create_otp_verification_token()
    │   │ │  └─ token_type = "otp_verification" (5-min expiry)
    │   │ ├─ Return: {
    │   │ │    requires_2fa: True,
    │   │ │    otp_verification_token: "...",
    │   │ │    user_id: 123
    │   │ │  }
    │   │ └─ Status: 401 (Unauthorized - not fully authenticated)
    │   │
    │   └─ NO → Normal Path
    │     ├─ _generate_tokens(user)
    │     │  ├─ create_access_token()
    │     │  └─ create_refresh_token()
    │     ├─ Return: {
    │     │    user: {...},
    │     │    access_token: "...",
    │     │    refresh_token: "...",
    │     │    token_type: "Bearer"
    │     │  }
    │     └─ Status: 200 (OK - fully authenticated)
    │
    ▼
Client Receives Response

=== PATH 1: 2FA Required ===
    │
    ├─ Client receives: requires_2fa = True, otp_verification_token
    ├─ Client prompts user: "Enter 6-digit code from Authenticator app"
    │
    ├─ POST /auth/login/verify-otp
    │ {
    │   otp_verification_token: "...",
    │   otp_code: "123456"
    │ }
    │
    ▼
Flask/FastAPI Controller
    │
    ├─ Validate request
    │
    ▼
AuthService.complete_2fa_login(otp_verification_token, otp_code)
    │
    ├─ JWTHandler.verify_otp_verification_token(token)
    │  │
    │  ├─ Extract payload
    │  ├─ Validate token_type = "otp_verification"
    │  ├─ Check expiration (5 minutes)
    │  │
    │  ├─ EXPIRED/INVALID?
    │  │ └─ Raise: InvalidToken (401)
    │  │
    │  └─ Extract: user_id
    │
    ├─ UserService.get_user_by_id(user_id)
    │
    ├─ verify_otp(user_id, otp_code)
    │  ├─ UserService.get_user_by_id()
    │  ├─ User.is_two_factor_enabled check
    │  ├─ User.two_factor_secret check
    │  ├─ OTP format validation (6 digits)
    │  ├─ pyotp.TOTP(user.two_factor_secret).verify(otp_code, window=1)
    │  │
    │  ├─ VALID ✓
    │  │ └─ Return: True
    │  │
    │  └─ INVALID ✗
    │    └─ Raise: InvalidOTP (401)
    │
    ├─ _generate_tokens(user)
    │  ├─ create_access_token()
    │  └─ create_refresh_token()
    │
    ▼
Response: {
    user: {...},
    access_token: "...",
    refresh_token: "...",
    token_type: "Bearer"
}
Status: 200 (OK - fully authenticated)
```

### 2.3 OTP Verification Flow

```
AuthService.verify_otp(user_id, otp_code)
    │
    ├─ Preconditions:
    │  ├─ User exists
    │  ├─ User.is_two_factor_enabled = True
    │  └─ User.two_factor_secret is not null
    │
    ├─ Validate OTP format:
    │  ├─ Is string?
    │  ├─ Exactly 6 characters?
    │  ├─ All digits?
    │  │
    │  └─ INVALID FORMAT?
    │    └─ Raise: ValidationError
    │
    ├─ Retrieve stored secret:
    │  └─ user.two_factor_secret
    │
    ├─ Initialize TOTP:
    │  └─ totp = pyotp.TOTP(secret)
    │
    ├─ Verify OTP code:
    │  ├─ totp.verify(otp_code, valid_window=1)
    │  │
    │  │ ┌──────────────────────────────────┐
    │  │ │  TOTP Time Window Explanation    │
    │  │ │                                  │
    │  │ │  Window = 1 means:               │
    │  │ │  • Current 30-sec window: valid  │
    │  │ │  • Previous 30-sec window: valid │
    │  │ │  • Next 30-sec window: valid     │
    │  │ │                                  │
    │  │ │  Tolerates ±30 seconds of clock │
    │  │ │  skew between client/server      │
    │  │ └──────────────────────────────────┘
    │  │
    │  ├─ MATCH: True
    │  │ └─ Return: True (OTP is valid)
    │  │
    │  └─ NO MATCH: False
    │    └─ Raise: InvalidOTP
    │
    └─ All validations passed → Authentication success
```

### 2.4 2FA Disable Flow

```
User (Browser)
    │
    ├─ POST /auth/2fa/disable
    │ (with JWT access token)
    │ {
    │   password: "userPassword123!",
    │   otp_code: "123456"  (optional)
    │ }
    │
    ▼
Flask/FastAPI Controller
    │
    ├─ Extract user_id from JWT token
    ├─ Validate request data
    │
    ▼
AuthService.disable_2fa(user_id, user_password, otp_code=None)
    │
    ├─ UserService.get_user_by_id(user_id)
    │
    ├── User.is_two_factor_enabled = False?
    │   └─ Raise: ValidationError (2FA not enabled)
    │
    ├─ PasswordHandler.verify_password(user_password, hash)
    │
    ├── Password INVALID?
    │   └─ Raise: InvalidCredentials
    │
    ├─ If otp_code provided:
    │  ├─ Validate format (6 digits)
    │  ├─ Call verify_otp(user_id, otp_code)
    │  │
    │  └─ If OTP INVALID?
    │    └─ Raise: InvalidOTP (don't disable)
    │
    ├─ user.disable_2fa()
    │  ├─ Set: two_factor_secret = None
    │  ├─ Set: is_two_factor_enabled = False
    │  └─ Set: otp_verified_at = None
    │
    ├─ session.commit()
    │
    ▼
Response: { message: "2FA disabled successfully" }
Status: 200

=== 2FA is now DISABLED ===
```

---

## 3. JWT Token Types

### 3.1 Access Token
- **Purpose**: Primary authentication token for API requests
- **Expiry**: 15 minutes (configurable)
- **Token Type Claim**: `"access"`
- **Payload**:
  ```json
  {
    "user_id": 123,
    "email": "user@example.com",
    "token_type": "access",
    "iat": 1234567890,
    "exp": 1234568790
  }
  ```

### 3.2 Refresh Token
- **Purpose**: Long-lived token for obtaining new access tokens
- **Expiry**: 7 days (configurable)
- **Token Type Claim**: `"refresh"`
- **Usage**: POST /auth/refresh with refresh_token

### 3.3 OTP Verification Token (NEW)
- **Purpose**: Temporary token to bridge login and 2FA verification
- **Expiry**: 5 minutes (fixed)
- **Token Type Claim**: `"otp_verification"`
- **Payload**:
  ```json
  {
    "user_id": 123,
    "email": "user@example.com",
    "token_type": "otp_verification",
    "iat": 1234567890,
    "exp": 1234568190
  }
  ```
- **Restrictions**:
  - Short 5-minute window limits exposure if leaked
  - Cannot be used as normal access token (wrong token_type)
  - Validates user identity during OTP submission
  - Expires before full authorization window (e.g., after logout)

---

## 4. Security Considerations

### 4.1 Secret Storage
- **Location**: SQLAlchemy User model, `two_factor_secret` column (STRING(32))
- **Format**: Base32-encoded (pyotp standard)
- **Encryption**: At rest (production), plaintext in DB (development)
  - **Recommendation**: Use column-level encryption (e.g., SQLAlchemy-Crypto) in production
- **Never Logged**: Ensure `two_factor_secret` never appears in logs
- **Accessible**: Only during 2FA setup response and for verification

### 4.2 OTP Validation
- **Time Window**: ±30 seconds (1-step tolerance in pyotp)
  - Accounts for clock skew between client/server
  - Prevents replay of same OTP within window
- **Rate Limiting**: Recommended at API level (Flask/FastAPI)
  - Limit failed OTP attempts per user
  - Implement exponential backoff
- **Invalid Codes**: Return generic "Invalid OTP" (no information leakage)

### 4.3 Token Expiry
- **OTP Verification Token**: 5 minutes (very short)
  - Minimal exposure window
  - Forces user to re-login if 2FA step times out
- **Access Token**: 15 minutes
  - Users must refresh frequently
  - Limits damage from token theft
- **Refresh Token**: 7 days
  - Remember-me functionality
  - Stored securely client-side

### 4.4 Attack Prevention

| Attack | Prevention |
|--------|-----------|
| Brute Force OTP | Rate limiting, exponential backoff, OTP window tolerance |
| Secret Leakage | Encryption at rest, no logging, short-lived temp tokens |
| Token Theft | Short expiry windows, HTTPS/TLS mandatory, secure storage |
| Clock Skew | ±30 second tolerance in pyotp |
| Replay Attacks | Time-based validation, single-use window in 30-sec intervals |
| Account Enumeration | Generic error messages for failed login/OTP |

---

## 5. State Diagram

```
USER STATE TRANSITIONS FOR 2FA
═════════════════════════════════════

                    ┌─────────────────────┐
                    │ User Registered     │
                    │ 2FA: DISABLED       │
                    └──────────┬──────────┘
                               │
                    GET /2fa/setup (require auth)
                               │
                               ▼
        ┌─────────────────────────────────────┐
        │ Secret Generated (not persisted)     │
        │ User scans QR code with Authenticator
        │ User gets OTP from Authenticator     │
        └────────────┬────────────────────────┘
                     │
      POST /2fa/verify-setup
      { secret, otp_code }
             │
             ├─ OTP Valid? ──YES──┐
             │                    │
             NO                   ▼
             │          ┌──────────────────────┐
             │          │ Secret Persisted     │
             │          │ 2FA: ENABLED ✓       │
             │          │ User ready for login │
             │          └──────────┬───────────┘
             │                     │
             └─ Raise: InvalidOTP  │
                (no state change)  │
                                   │
                    ┌──────────────┘
                    │
        Next Login:
        POST /auth/login
             │
             ├─ Password VALID? ──NO──┐
             │                        │
             YES                      ├─ Raise: InvalidCredentials
             │                        │ Return 401
             ├─ 2FA enabled?          │
             │                        └─ End
             ├─ YES → Return otp_verification_token (401)
             │     User completes: POST /auth/login/verify-otp
             │
             └─ NO → Return access/refresh tokens (200)
                 Current session

           With OTP Verification Token:
        POST /auth/login/verify-otp
        { otp_verification_token, otp_code }
              │
              ├─ Token Valid & Not Expired? ──NO──┐
              │                                   │
              YES                                 ├─ Raise: InvalidToken
              │                                   │ Return 401
              ├─ OTP Valid? ──NO──┐               │
              │                   └─ End          └─ End
              YES                                
              │            
              ▼
         ┌─────────────────────────┐
         │ Access Token Issued      │
         │ User Fully Authenticated │
         │ Session Can Begin        │
         └──────────┬──────────────┘
                    │
        Some Time Later:
        POST /auth/2fa/disable
        { password, otp_code? }
             │
             ├─ Password VALID? ──NO──┐
             │                        │
             YES                      ├─ Raise: InvalidCredentials
             │                        │ Return 401
             ├─ OTP provided?         │
             │                        └─ End
             ├─ YES → Verify OTP ──INVALID──┐
             │                              │
             NO                             ├─ Raise: InvalidOTP
             │                              │ Return 401
             ▼                              │
         ┌──────────────────────┐          │
         │ 2FA Disabled ✗        │◄────────┘
         │ is_2fa_enabled = False│
         │ two_factor_secret = None
         │ otp_verified_at = None│
         │                      │
         └──────────┬───────────┘
                    │
          User can login normally again
          (password only, no 2FA required)
```

---

## 6. Backward Compatibility

### 6.1 Existing Users
- **Status**: `is_two_factor_enabled = False` by default
- **Login Behavior**: Unchanged (credentials only)
- **No Breaking Changes**: Existing endpoints return same responses
- **Database Migration**: New columns added with defaults (no data loss)

### 6.2 Existing Endpoints
| Endpoint | Change | Backward Compatible |
|----------|--------|---------------------|
| POST /auth/login | May return `requires_2fa: True` if 2FA enabled | ✓ Yes (clients check flag) |
| POST /auth/signup | No changes to request/response | ✓ Yes |
| POST /auth/refresh | No changes | ✓ Yes |
| GET /auth/me | User dict includes `is_two_factor_enabled` field | ✓ Yes (new field) |

### 6.3 Migration Path for Existing Apps
```
1. Update authlib library (add 2FA fields to User model)
2. Run database migrations (add new columns)
3. No code changes required in existing login flows
4. Clients optionally support 2FA:
   - Check for `requires_2fa` flag in login response
   - If True, show OTP/authenticator UI
   - Call new endpoints for 2FA management
5. Users can enable 2FA at their discretion
```

---

## 7. Error Handling & HTTP Status Codes

| Scenario | Exception | HTTP Status | Recovery |
|----------|-----------|-------------|----------|
| Invalid credentials (pre-2FA) | InvalidCredentials | 401 | Retry login |
| 2FA required | TwoFactorRequired | 401 | Present OTP/token verification UI |
| Invalid OTP code | InvalidOTP | 401 | Retry OTP entry |
| OTP token expired | InvalidToken | 401 | Re-login to get new OTP token |
| Setup format error | ValidationError | 400 | Fix input (secret, OTP format) |
| 2FA already enabled | ValidationError | 400 | Check current state first |
| Invalid password (disable) | InvalidCredentials | 401 | Verify password |
| User not found | UserNotFound | 404 | Check user_id |
| Database error | DatabaseError | 500 | Retry (transient) or escalate |

---

## 8. Configuration

### 8.1 Timeouts & Windows
```python
# JWT Expiry Times (authlib/config.py)
JWT_ACCESS_TOKEN_EXPIRY_MINUTES = 15
JWT_REFRESH_TOKEN_EXPIRY_DAYS = 7
PASSWORD_RESET_TOKEN_EXPIRY_MINUTES = 60

# OTP Verification Token (hardcoded in jwt_handler.py)
OTP_VERIFICATION_TOKEN_EXPIRY_MINUTES = 5

# TOTP Time Window (pyotp library default)
TOTP_TIME_STEP_SECONDS = 30
TOTP_DIGITS = 6
TOTP_VALID_WINDOW = 1  # ±1 × 30 second windows = ±60 seconds tolerance
```

### 8.2 Environment Variables
```bash
# JWT_SECRET_KEY - used for all tokens (access, refresh, OTP verification)
JWT_SECRET_KEY=your-secret-key-here

# JWT_ALGORITHM (default: HS256)
JWT_ALGORITHM=HS256

# Other config inherited from existing AuthLib setup
```

---

## 9. Testing Scenarios

All test cases verify:
1. ✓ Setup 2FA returns valid secret and provisioning URI
2. ✓ Valid OTP enables 2FA, invalid OTP rejects
3. ✓ Login without 2FA unchanged (backward compatibility)
4. ✓ Login with 2FA returns otp_verification_token
5. ✓ Valid OTP during login issues access tokens
6. ✓ Invalid OTP during login rejected
7. ✓ Disable 2FA requires password verification
8. ✓ OTP token expiration enforced (5 minute window)
9. ✓ All existing tests still pass (no regression)

---

## 10. Summary

The 2FA system integrates seamlessly with AuthLib's existing architecture:

- **Minimal Changes**: Only user model and auth service extended
- **Full Backward Compatibility**: Existing users unaffected
- **Two-Step Login**: Credential validation → OTP validation → JWT issuance
- **Secure by Default**: Secrets encrypted, short-lived tokens, rate limiting recommended
- **Flexible**: Users opt-in to 2FA, can disable anytime
- **Tested**: Comprehensive test coverage, no regressions

