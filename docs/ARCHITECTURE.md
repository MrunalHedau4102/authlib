# Technical Architecture - AuthLib

## System Overview

AuthLib is a scalable, framework-agnostic authentication library built with a clean layered architecture. This document describes the technical design, component interactions, and data flow.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        External Applications                             │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐      │
│  │   FastAPI App    │  │   Flask App      │  │   Other Frameworks│      │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘      │
└───────────┼──────────────────────┼──────────────────────┼────────────────┘
            │                      │                      │
            └──────────────────────┼──────────────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │   HTTP/REST API Layer       │
                    │  (Framework Specific)       │
                    └──────────────┬──────────────┘
                                   │
        ┌──────────────────────────┴──────────────────────────┐
        │                                                      │
        ▼                                                      ▼
┌─────────────────────────────┐                    ┌─────────────────────────────┐
│   AuthService               │                    │   EmailService              │
│  ├─ register()              │                    │  ├─ send_email()            │
│  ├─ login()                 │                    │  ├─ send_password_reset()   │
│  ├─ refresh_access_token()  │                    │  ├─ send_welcome_email()    │
│  ├─ logout()                │                    │  └─ send_verification()     │
│  ├─ request_password_reset()│                    └─────────────────────────────┘
│  ├─ confirm_password_reset()│
│  └─ verify_token()          │
└──────────┬──────────────────┘
           │
        ┌──┴───────────────────────────────────────┐
        │                                           │
        ▼                                           ▼
┌─────────────────────────────┐        ┌─────────────────────────────┐
│   UserService               │        │   JWTHandler                │
│  ├─ create_user()           │        │  ├─ create_access_token()   │
│  ├─ get_user_by_id()        │        │  ├─ create_refresh_token()  │
│  ├─ get_user_by_email()     │        │  ├─ verify_token()          │
│  ├─ update_user()           │        │  ├─ verify_access_token()   │
│  ├─ change_password()       │        │  ├─ verify_refresh_token()  │
│  ├─ delete_user()           │        │  └─ verify_password_reset() │
│  └─ deactivate/activate()   │        └─────────────────────────────┘
└──────────┬──────────────────┘
           │
        ┌──┴───────────────────────────────────────┐
        │                                           │
        ▼                                           ▼
┌─────────────────────────────┐        ┌─────────────────────────────┐
│   PasswordHandler           │        │   Validators                │
│  ├─ hash_password()         │        │  ├─ EmailValidator          │
│  ├─ verify_password()       │        │  │  ├─ validate()          │
│  └─ needs_rehashing()       │        │  │  └─ sanitize()          │
└─────────────────────────────┘        │  └─ PasswordValidator       │
                                       │     ├─ validate()          │
                                       │     └─ check_strength()    │
                                       └─────────────────────────────┘
        │
        └──────────────────────────┬──────────────────────┐
                                   │                      │
                                   ▼                      ▼
                    ┌──────────────────────────┐  ┌──────────────────────────┐
                    │   Database Layer         │  │   Exception Layer        │
                    │                          │  │                          │
                    │  ┌────────────────────┐  │  │  ├─ AuthException        │
                    │  │   Database         │  │  │  ├─ UserNotFound         │
                    │  │                    │  │  │  ├─ InvalidCredentials   │
                    │  │  ┌──────────────┐  │  │  │  ├─ InvalidToken         │
                    │  │  │   User       │  │  │  │  ├─ UserAlreadyExists    │
                    │  │  │   Table      │  │  │  │  ├─ ValidationError      │
                    │  │  └──────────────┘  │  │  │  ├─ DatabaseError        │
                    │  │                    │  │  │  └─ EmailSendError       │
                    │  │  ┌──────────────┐  │  │  │
                    │  │  │ TokenBlacklist│  │  │  │
                    │  │  │ Table        │  │  │  │
                    │  │  └──────────────┘  │  │  │
                    │  │                    │  │  │
                    │  └────────────────────┘  │  │
                    │   (SQLAlchemy ORM)       │  │
                    └──────────┬───────────────┘  └──────────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   PostgreSQL        │
                    │   (or MySQL/SQLite) │
                    └─────────────────────┘
```

## Component Layers

### 1. **Presentation Layer** (Framework Specific)
- FastAPI routes, Flask blueprints, etc.
- Handles HTTP requests/responses
- Input validation and error formatting
- **Not included in AuthLib** - developers implement using their framework

### 2. **Service Layer** (Core Business Logic)
Core services that implement authentication workflows:

#### **AuthService**
- Orchestrates authentication flows
- Coordinates between UserService and JWTHandler
- Handles token generation and verification
- Manages token blacklisting
- Key responsibilities:
  - User registration flow
  - Login authentication
  - Token refresh
  - Password reset workflow

#### **UserService**
- User CRUD operations
- Password changes
- User activation/deactivation
- Database model interactions
- Delegates password operations to PasswordHandler

#### **EmailService**
- Sends authentication-related emails
- Templates for password reset, welcome, verification
- SMTP configuration management
- Optional - can be extended by developers

### 3. **Utilities Layer**
Reusable components for specific tasks:

#### **JWTHandler**
- JWT token creation with configurable expiry
- Token validation and decoding
- Support for multiple token types (access, refresh, password_reset)
- Claims management
- Token expiration checking

#### **PasswordHandler**
- Bcrypt-based password hashing
- Password verification
- Configurable hashing rounds (cost factor)
- Rehashing detection

#### **Validators**
- **EmailValidator**: Email format validation and sanitization
- **PasswordValidator**: Password strength requirements, detailed feedback

#### **Exceptions**
- Custom exception hierarchy for specific error cases
- HTTP status code mappings
- Clear error messages
- Enables framework-agnostic error handling

### 4. **Data Layer** (Database & Models)
SQLAlchemy-based data persistence:

#### **User Model**
```
┌─────────────────────────────┐
│         User                │
├─────────────────────────────┤
│ id: int (PK)                │
│ email: str (unique)         │
│ password_hash: str          │
│ first_name: str             │
│ last_name: str              │
│ is_active: bool             │
│ is_verified: bool           │
│ created_at: datetime        │
│ updated_at: datetime        │
│ last_login: datetime        │
└─────────────────────────────┘
```

#### **TokenBlacklist Model**
```
┌──────────────────────────────┐
│    TokenBlacklist            │
├──────────────────────────────┤
│ id: int (PK)                 │
│ jti: str (unique) - JWT ID   │
│ user_id: int (FK)            │
│ token_type: str              │
│ reason: str                  │
│ revoked_at: datetime         │
│ expires_at: datetime         │
└──────────────────────────────┘
```

#### **Configuration**
- Environment-based configuration
- Support for development, testing, production environments
- Validation of critical settings in production

## Data Flow Diagrams

### Registration Flow
```
User Input (email, password)
            │
            ▼
EmailValidator.validate()
            │
            ▼
UserService.create_user()
  ├─ EmailValidator.sanitize()
  ├─ PasswordHandler.hash_password()
  └─ Save to DB
            │
            ▼
AuthService.register()
  ├─ Create User (via UserService)
  ├─ Generate tokens (via JWTHandler)
  └─ Return {user, access_token, refresh_token}
            │
            ▼
Return to Framework → HTTP Response
```

### Login Flow
```
User Input (email, password)
            │
            ▼
AuthService.login()
  ├─ EmailValidator.validate()
  ├─ UserService.get_user_by_email()
  ├─ PasswordHandler.verify_password()
  ├─ Update last_login
  ├─ Generate tokens (via JWTHandler)
  └─ Return {user, access_token, refresh_token}
            │
            ▼
Return to Framework → HTTP Response
```

### Token Refresh Flow
```
User Input (refresh_token)
            │
            ▼
AuthService.refresh_access_token()
  ├─ JWTHandler.verify_refresh_token()
  ├─ Check if blacklisted
  ├─ JWTHandler.create_access_token()
  └─ Return {access_token}
            │
            ▼
Return to Framework → HTTP Response
```

### Password Reset Flow
```
User Input (email)
            │
            ▼
AuthService.request_password_reset()
  ├─ EmailValidator.validate()
  ├─ UserService.get_user_by_email()
  ├─ JWTHandler.create_password_reset_token()
  └─ Return {reset_token, expires_in}
            │
            ├─ Send email (optional, via EmailService)
            │
            ▼
User Input (reset_token, new_password)
            │
            ▼
AuthService.confirm_password_reset()
  ├─ JWTHandler.verify_password_reset_token()
  ├─ PasswordValidator.validate()
  ├─ UserService.change_password()
  ├─ Blacklist reset token
  ├─ Generate new tokens
  └─ Return {user, access_token, refresh_token}
            │
            ▼
Return to Framework → HTTP Response
```

### Token Verification Flow
```
User Request with Bearer Token
            │
            ▼
Extract token from Authorization header
            │
            ▼
AuthService.verify_token()
  ├─ JWTHandler.verify_access_token()
  ├─ Check if blacklisted
  └─ Return {payload} or raise InvalidToken
            │
            ├─ Valid: Continue to protected resource
            └─ Invalid: Return 401 Unauthorized
```

## Design Patterns Used

### 1. **Service Layer Pattern**
- Business logic separated from framework concerns
- Each service has a single responsibility
- Services are stateless and reusable

### 2. **Dependency Injection**
- Database session injected into services
- Config injected where needed
- Facilitates testing and flexibility

### 3. **Factory Pattern**
- `JWTHandler` creates different token types
- `PasswordHandler` abstracts bcrypt operations
- `EmailService` abstracts SMTP operations

### 4. **Validator Pattern**
- `EmailValidator`, `PasswordValidator` for input validation
- Defensive programming with early validation

### 5. **Exception Pattern**
- Specific exceptions for different error cases
- Clear error messages
- Status codes included for HTTP mapping

## Security Architecture

### Password Security
```
Plain Password
    │
    ▼
PasswordValidator.validate()  ─── Check strength requirements
    │
    ▼
PasswordHandler.hash_password()
    ├─ bcrypt.gensalt(rounds=12)  ─── Generate random salt
    └─ bcrypt.hashpw()            ─── Hash with salt
    │
    ▼
Stored in Database (never plain text)
```

### Token Security
```
User Data (user_id, email)
    │
    ▼
JWTHandler.create_access_token()
  ├─ Add claims (user_id, email, token_type, exp, iat)
  ├─ Sign with SECRET_KEY (HS256)
  └─ Encode as JWT
    │
    ▼
Token sent to client
    │
    ├─ Client stores in secure location (httpOnly cookie or secure storage)
    │
    └─ Client sends in Authorization header: "Bearer {token}"
            │
            ▼
        Server receives token
            │
            ▼
        JWTHandler.verify_token()
          ├─ Decode JWT
          ├─ Verify signature (matches SECRET_KEY)
          ├─ Check expiration
          └─ Return payload
            │
            ├─ Valid: Grant access
            └─ Invalid: Reject (401)
```

### Token Blacklisting
```
User Logout or Password Reset
        │
        ▼
Extract token expiration time
        │
        ▼
Create TokenBlacklist entry
  ├─ JTI (JWT ID): token string
  ├─ user_id: user making request
  ├─ token_type: access/refresh/password_reset
  ├─ reason: logout/password_reset/etc
  ├─ revoked_at: current timestamp
  └─ expires_at: token's original expiration
        │
        ▼
Store in database
        │
        ├─ On token verification: Check if JTI in blacklist
        │   └─ Reject if found (even if cryptographically valid)
        │
        └─ Cleanup: Delete expired blacklist entries (background job)
```

## Scalability Considerations

### Current Design (Single Database)
- SQLAlchemy ORM with connection pooling
- Works well for low to medium traffic
- Token blacklist stored in database

### For High-Scale Systems
1. **Token Blacklist**
   - Move to Redis for O(1) lookup
   - Automatic expiration with TTL
   - Distributed across instances

2. **Caching**
   - Cache user profiles in Redis
   - Invalidate on user updates

3. **Database**
   - Read replicas for user lookups
   - Write master for registrations/updates
   - Connection pooling tuning

4. **Async Support**
   - Services are framework-agnostic
   - Can be used with FastAPI async handlers
   - No blocking operations

### Example: Async Integration with FastAPI
```python
@app.post("/auth/login")
async def login(request: LoginRequest):
    # Async wrapper
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None, 
        auth_service.login,
        request.email,
        request.password
    )
    return result
```

## Extension Points

Developers can extend AuthLib by:

1. **Custom User Model**
   - Subclass `User` model
   - Add additional fields (phone, address, etc.)
   - Keep same interface for services

2. **Custom Validators**
   - Subclass `EmailValidator`, `PasswordValidator`
   - Override validation rules

3. **Custom Email Handling**
   - Extend `EmailService`
   - Implement custom email templates
   - Use different providers (SendGrid, Mailgun, etc.)

4. **Custom Token Claims**
   - Pass `additional_claims` to token creation
   - Verify custom claims in middleware

5. **Custom Exception Handling**
   - Catch `AuthException` subclasses
   - Format according to API standards

## Performance Characteristics

### Time Complexity
- **Password hashing**: O(2^log_rounds) ≈ O(1^12) ≈ ~100ms
- **Token creation**: O(1)
- **Token verification**: O(1)
- **Database queries**: O(1) with indexes on email and user_id

### Space Complexity
- **User record**: ~500 bytes
- **Token**: ~500 bytes (JWT)
- **Blacklist entry**: ~200 bytes

### Typical Response Times
- Registration: 120-200ms (hash time dominant)
- Login: 100-150ms
- Token refresh: 5-10ms
- Token verification: 5-10ms
- Password reset confirm: 120-200ms

## Testing Architecture

```
┌─────────────────────────────────────┐
│    Test Fixtures (conftest.py)      │
│  ├─ test_db_engine (SQLite)         │
│  ├─ test_db_session                 │
│  ├─ test_config                     │
│  └─ test_user_data                  │
└────────────┬────────────────────────┘
             │
     ┌───────┴────────┐
     │                │
     ▼                ▼
┌──────────────┐  ┌──────────────────────┐
│ Unit Tests   │  │ Integration Tests    │
├──────────────┤  ├──────────────────────┤
│ Validators   │  │ AuthService + DB     │
│ JWT Handler  │  │ UserService + DB     │
│ Password     │  │ Complete flows       │
│ Exceptions   │  └──────────────────────┘
└──────────────┘

Test Coverage Target: >85%
```

## Deployment Scenarios

### Scenario 1: Web API (FastAPI/Flask)
```
Load Balancer
    │
    ├─── API Instance 1 ─── AuthLib
    ├─── API Instance 2 ─── AuthLib
    └─── API Instance 3 ─── AuthLib
         │
         └─── PostgreSQL (Shared)
              │
              └─── Token Blacklist Table
```

### Scenario 2: Microservices
```
API Gateway
    │
    ├─── Auth Service (AuthLib)
    ├─── User Service
    └─── Other Services
         │
         └─── Shared Database / separate schemas
```

### Scenario 3: Mobile Backend
```
Mobile App ──HTTP── FastAPI/Flask ──┐
                                     │
Web App ──HTTP────────────────────────┤
                                     │
                        AuthLib Service
                        (Shared Instance)
                             │
                             └─── PostgreSQL
```

## Future Enhancements

1. **OAuth2/OIDC Support**
   - Implement OAuth2 provider
   - Support external providers (Google, GitHub)

2. **Multi-Factor Authentication**
   - TOTP (Google Authenticator)
   - SMS codes

3. **Rate Limiting**
   - Built-in rate limit utilities
   - Per-user, per-IP controls

4. **Audit Logging**
   - Log all auth events
   - Track failed attempts
   - Security analysis

5. **GraphQL Support**
   - Example GraphQL schema
   - Strawberry GraphQL integration

---

**This architecture ensures:**
- ✅ Framework independence
- ✅ Clean separation of concerns
- ✅ Easy testing and maintenance
- ✅ Scalability for production use
- ✅ Security best practices
- ✅ Minimal dependencies
