# Changelog

All notable changes to AuthLib will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-18

### Added

#### Core Features
- User registration with email validation
- Email/password login authentication
- JWT token generation (access + refresh tokens)
- Password reset workflow with token verification
- Token blacklisting for logout and revocation
- Token refresh without requiring password
- User account management (create, read, update, delete)
- User activation/deactivation functionality
- Email verification status tracking
- Last login tracking

#### Security Features
- Bcrypt password hashing with configurable rounds (default: 12)
- JWT token signing with configurable algorithms (default: HS256)
- Password strength validation (8+ chars, uppercase, lowercase, digits, special chars)
- Email format validation (RFC 5322 compliant)
- Input sanitization
- Token expiration enforcement
- Token blacklist prevents replay attacks

#### Framework Integration
- Framework-agnostic core (no web framework dependencies)
- Complete FastAPI integration example (8 endpoints)
- Complete Flask integration example (8 endpoints)
- Works with any Python web framework (Django, FastAPI, Flask, Sanic, etc.)

#### Database & Models
- SQLAlchemy ORM integration
- User model with 10 fields and indexes
- TokenBlacklist model for token revocation
- Support for PostgreSQL, MySQL, SQLite
- Database connection pooling
- Automatic timestamp management

#### Email Support
- Password reset email templates
- Welcome email templates
- Email verification templates
- SMTP configuration management
- HTML and plain text email support

#### Utilities & Tools
- JWTHandler for token operations
- PasswordHandler for bcrypt operations
- EmailValidator with sanitization
- PasswordValidator with strength checking
- Custom exception hierarchy (8 exception types)
- Configuration management (dev/prod/test environments)

#### Testing & Quality
- 70+ unit and integration tests
- Pytest fixtures for testing
- Mock database for isolated testing
- >85% code coverage target
- Type hints throughout codebase
- PEP 8 compliant code style

#### Documentation
- Comprehensive README (600+ lines)
- Technical architecture documentation (400+ lines)
- API reference with all methods
- Quick start guide
- Contributing guidelines
- Project manifest
- Inline code documentation
- Data flow diagrams

### Changed
- N/A (initial release)

### Deprecated
- N/A (initial release)

### Removed
- N/A (initial release)

### Fixed
- N/A (initial release)

### Security
- Uses bcrypt for password hashing (industry standard)
- JWT tokens are cryptographically signed
- Tokens include expiration times
- Token blacklist prevents reuse after logout
- Password validation enforces strong passwords
- SQL injection prevented via SQLAlchemy ORM
- Type hints reduce runtime errors
- Comprehensive input validation

---

## Future Releases

### [1.1.0] - Planned

- Email verification workflow
- User profile pictures
- Custom user fields
- GraphQL API example
- Rate limiting utilities
- Audit logging

### [2.0.0] - Planned

- OAuth2 provider support
- External OAuth2 provider integration (Google, GitHub)
- Multi-factor authentication (2FA)
- TOTP support
- SMS verification
- Role-based access control
- Permission management

---

## How to Update

### From 1.0.0 to 1.1.0
- No breaking changes expected
- Just run `pip install --upgrade authlib`

### From 1.x to 2.0.0
- Check breaking changes section of release notes
- Update your integration code if needed
- See migration guide in documentation

---

## Release Schedule

- Patch releases (bug fixes): As needed
- Minor releases (new features): Quarterly
- Major releases (breaking changes): Annually

---

## Support

- **Documentation**: https://authlib.readthedocs.io
- **GitHub**: https://github.com/yourusername/authlib
- **Issues**: https://github.com/yourusername/authlib/issues
- **Email**: support@authlib.dev
