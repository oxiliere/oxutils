# Authentication & Authorization

**JWT-based authentication with MFA, tenant invitations, session management, and password reset**

## Features

- JWT authentication via cookies or Authorization header (ninja-jwt)
- MFA support: TOTP + recovery codes (allauth MFA)
- Multi-tenant invitations with role hierarchy
- Email verification with customizable templates
- Password reset with single-use tokens and dedicated cookie
- Session management: list, revoke individual/all sessions
- Rate limiting on all sensitive endpoints
- Reauthentication flow for sensitive operations
- Configurable cookie security (HttpOnly, Secure, SameSite)
- User registration with optional invitation flow

## Setup

Add to `INSTALLED_APPS`:

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.mfa',
    'oxutils.auth',
]
```

Add middleware:

```python
MIDDLEWARE = [
    # ...
    'allauth.account.middleware.AccountMiddleware',
]
```

Run migrations:

```bash
python manage.py migrate
```

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                    AuthController                     │
│  /auth/login, /auth/logout, /auth/refresh, ...        │
│  /auth/register, /auth/password_reset, ...            │
│  /auth/invitations/..., /auth/emails/...               │
└──────────────────────────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
   │  Auth Tokens  │ │   Sessions   │ │  Invitations  │
   │  (ninja-jwt)  │ │  (Whitelist)  │ │  (Backend)   │
   └──────────────┘ └──────────────┘ └──────────────┘
          │                │                │
          ▼                ▼                ▼
   ┌──────────────────────────────────────────────────┐
   │              RefreshTokenWhitelistModel           │
   └──────────────────────────────────────────────────┘
```

## Core Concepts

### Token Flow

```
Login ──> RefreshToken.for_user() ──> store in Whitelist
                │
    ┌───────────┴──────────┐
    ▼                      ▼
 Access Token          Refresh Token
 (short-lived)         (cookie/httpOnly)
    │                      │
    │                  Refresh ──> rotate (new jti, delete old)
    │
 Verify endpoint ──> use access token
```

### Cookie Strategy

Tokens are stored as HttpOnly cookies by default. All cookie attributes are configurable:

| Setting | Default | Description |
|---------|---------|-------------|
| `AUTH_COOKIE_HTTP_ONLY` | `True` | Prevent JS access |
| `AUTH_COOKIE_SECURE` | `not DEBUG` | HTTPS only |
| `AUTH_COOKIE_SAME_SITE` | `"Lax"` | CSRF protection |
| `OXI_COOKIE_DOMAIN` | `None` | Cookie domain |
| `JWT_ALLAUTH_REFRESH_TOKEN_AS_COOKIE` | `True` | Store refresh token in cookie |

## Configuration

### Required Settings

```python
# settings.py

# JWT signing (via ninja-jwt)
NINJA_JWT = {
    "SIGNING_KEY": "your-secret-key",
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}

# Allauth
SITE_ID = 1
ACCOUNT_EMAIL_VERIFICATION = "mandatory"  # or "optional"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USER_MODEL_USERNAME_FIELD = None   # Use email-only
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_UNIQUE_EMAIL = True

# MFA
MFA_SIGNING_SALT = "a-long-random-string-unique-to-your-deployment"  # Required in production
MFA_SIGNING_TTL = 300  # seconds

# Tenants (for invitations)
TENANT_MODEL = "your_app.Tenant"

# Invitations
INVITATION_EXPIRY_DAYS = 7
INVITATIONS_MAX_PER_HOUR = 50
INVITATION_MAX_RESENDS = 3

# Frontend URLs (used in emails)
ACCOUNT_FRONTEND_URLS = {
    "account_confirm_email": "https://app.example.com/confirm/{key}",
    "account_reset_password": "https://app.example.com/reset/{uid}/{token}",
}
```

### Optional Settings

```python
# Password reset cookie
PASSWORD_RESET_COOKIE_HTTP_ONLY = True
PASSWORD_RESET_COOKIE_SECURE = not DEBUG
PASSWORD_RESET_COOKIE_SAME_SITE = "Lax"
PASSWORD_RESET_COOKIE_MAX_AGE = 3600  # seconds

# Password policies
OLD_PASSWORD_FIELD_ENABLED = True
LOGOUT_ON_PASSWORD_CHANGE = True

# Custom schemas
JWT_ALLAUTH_SCHEMAS = {
    "LOGIN_SCHEMA": "myapp.schemas.CustomLoginSchema",
    "REGISTER_SCHEMA": "myapp.schemas.CustomRegisterSchema",
    "PASSWORD_RESET_SCHEMA": "myapp.schemas.CustomPasswordResetSchema",
    "PASSWORD_CHANGE_SCHEMA": "myapp.schemas.CustomPasswordChangeSchema",
}

# Custom templates
JWT_ALLAUTH_TEMPLATES = {
    "EMAIL_VERIFICATION": "myapp/email/verification.html",
    "EMAIL_VERIFICATION_SUBJECT": "myapp/email/verification_subject.txt",
    "PASS_RESET_EMAIL": "myapp/email/password_reset.html",
    "PASS_RESET_EMAIL_TEXT": "myapp/email/password_reset.txt",
    "PASS_RESET_SUBJECT": "myapp/email/password_reset_subject.txt",
}
```

## API Endpoints

### Authentication

| Method | Endpoint | Auth | Throttle | Description |
|--------|----------|------|----------|-------------|
| `POST` | `/auth/login` | No | AnonRate | Login → access + refresh tokens |
| `POST` | `/auth/logout` | Yes | — | Logout → revoke tokens |
| `POST` | `/auth/refresh` | No | AnonRate | Refresh access token |
| `POST` | `/auth/reauthenticate` | Yes | UserRate | Reauthenticate with password |
| `POST` | `/auth/verify-email` | No | AnonRate | Send verification email |

**Login** (`POST /auth/login`):

```json
// Request
{
    "email": "user@example.com",
    "password": "correct-password"
}

// Response 200 — Login success
{
    "code": "logged_in",
    "refresh": "eyJ...",
    "access": "eyJ..."
}

// Response 202 — MFA required
{
    "code": "mfa_required",
    "key": "signed-mfa-token"
}
```

**Refresh** (`POST /auth/refresh`):

```json
// Request (refresh token from cookie or body)
{
    "refresh": "eyJ..."  // Optional if cookie is set
}

// Response 200
{
    "refresh": "eyJ...",
    "access": "eyJ..."
}

// Response 401
{
    "detail": "Invalid token."
}
```

### Registration

| Method | Endpoint | Auth | Throttle | Description |
|--------|----------|------|----------|-------------|
| `POST` | `/auth/register` | No | AnonRate | Register new user |
| `GET` | `/auth/verify-email/{key}` | No | AnonRate | Confirm email |

**Register** (`POST /auth/register`):

```json
// Standard registration
{
    "email": "user@example.com",
    "password1": "StrongPass1!",
    "password2": "StrongPass1!",
    "first_name": "John",
    "last_name": "Doe"
}

// Invitation-based registration
{
    "email": "user@example.com",
    "password1": "StrongPass1!",
    "password2": "StrongPass1!",
    "first_name": "John",
    "last_name": "Doe",
    "token": "invitation-token-here"
}

// Response 200
{
    "success": true,
    "message": "Registration successful.",
    "email_verification_required": false
}
```

### Password Management

| Method | Endpoint | Auth | Throttle | Description |
|--------|----------|------|----------|-------------|
| `POST` | `/auth/change_password` | Yes | UserRate | Change password |
| `POST` | `/auth/password_reset` | No | AnonRate | Request reset email |
| `GET` | `/auth/password_reset/confirm/{uid}/{token}` | No | AnonRate | Validate reset link |
| `POST` | `/auth/password_reset/set-new` | Special | UserRate | Set new password |

**Change password** (`POST /auth/change_password`):

```json
// Request
{
    "old_password": "current-password",
    "new_password1": "NewStrongPass1!",
    "new_password2": "NewStrongPass1!"
}

// Response 200
{
    "success": true,
    "message": "Password changed successfully."
}
```

**Request password reset** (`POST /auth/password_reset`):

```json
// Request
{
    "email": "user@example.com"
}

// Response 200
{
    "detail": "Password reset e-mail has been sent."
}
```

The reset flow works as follows:
1. `POST /password_reset` → sends email with link
2. `GET /password_reset/confirm/{uid}/{token}` → returns `{"validlink": true}` and sets a `password_reset_access_token` cookie
3. `POST /password_reset/set-new` → reads the cookie, validates, and sets the new password

### Sessions

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/auth/user-sessions` | Yes | List active sessions |
| `DELETE` | `/auth/user-sessions/{session_id}` | Yes | Revoke specific session |
| `DELETE` | `/auth/user-sessions` | Yes | Revoke all except current |
| `DELETE` | `/auth/user-sessions/others` | Yes | Revoke all other sessions |

**Session age validation**: all revoke endpoints require the current session to be older than 3 days, preventing a freshly compromised token from destroying legitimate sessions.

**List sessions** (`GET /auth/user-sessions`):

```json
// Response 200
[
    {
        "id": 1,
        "session": "abc123def456",
        "is_current": true,
        "browser": "Chrome",
        "browser_version": "120.0",
        "os": "Linux",
        "device": "Other",
        "is_mobile": false,
        "is_pc": true,
        "ip": "192.168.1.1",
        "created": "2025-01-15T10:30:00Z"
    }
]
```

### Emails

| Method | Endpoint | Auth | Throttle | Description |
|--------|----------|------|----------|-------------|
| `GET` | `/auth/emails` | Yes | — | List user emails |
| `POST` | `/auth/emails` | Yes | 5/hour | Add email address |
| `PUT` | `/auth/emails/{email}/primary` | Yes | 20/hour | Set as primary |
| `POST` | `/auth/emails/{email}/verify` | Yes | 10/hour | Send verification |
| `DELETE` | `/auth/emails/{email}` | Yes | 20/hour | Remove email |

### MFA

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/auth/mfa/authenticate` | No | Complete MFA login |
| `POST` | `/auth/mfa/reauthenticate` | Yes | Reauthenticate with MFA |
| `POST` | `/auth/mfa/totp/secret` | Yes | Get TOTP secret + QR |
| `POST` | `/auth/mfa/totp/activate` | Yes | Activate TOTP |
| `POST` | `/auth/mfa/totp/deactivate` | Yes | Deactivate TOTP |
| `GET` | `/auth/mfa/totp/status` | Yes | Get TOTP status |
| `POST` | `/auth/mfa/recovery-codes/generate` | Yes | Generate recovery codes |
| `GET` | `/auth/mfa/recovery-codes/status` | Yes | Recovery codes status |
| `GET` | `/auth/mfa/recovery-codes/download` | Yes | Download recovery codes |

### Invitations

| Method | Endpoint | Auth | Throttle | Description |
|--------|----------|------|----------|-------------|
| `POST` | `/auth/invitations` | Yes | 30/hour | Create invitation |
| `POST` | `/auth/invitations/accept` | No | 30/hour | Accept invitation |
| `POST` | `/auth/invitations/cancel` | Yes | 30/hour | Cancel invitation |
| `GET` | `/auth/invitations` | Yes | — | List user invitations |
| `GET` | `/auth/invitations/tenant` | Yes | — | List tenant invitations |
| `GET` | `/auth/invitations/validate/{token}` | No | AnonRate | Validate token |
| `POST` | `/auth/invitations/resend` | Yes | 30/hour | Resend invitation |

**Create invitation** (`POST /auth/invitations`):

```json
// Request
{
    "email": "colleague@example.com",
    "role": "member",
    "message": "Join our workspace!"
}

// Response 200
{
    "success": true,
    "message": "Invitation sent to colleague@example.com",
    "invitation": {
        "id": "uuid",
        "email": "colleague@example.com",
        "status": "pending",
        "role": "member",
        "expires_at": "2025-01-22T10:00:00Z",
        "tenant_name": "My Organization"
    }
}
```

**Accept invitation** (`POST /auth/invitations/accept`):

```json
// Request
{
    "token": "sha256-hash-token"
}

// Response 200
{
    "code": "success",
    "detail": "Invitation accepted successfully."
}
```

**Validate token** (`GET /auth/invitations/validate/{token}`):

```json
// Response 200 — valid
{
    "valid": true,
    "email": "colleague@example.com",
    "tenant_name": "My Organization",
    "role": "member",
    "message": "Join our workspace!"
}

// Response 200 — invalid
{
    "valid": false
}
```

## Invitation Backend

The `InvitationBackend` manages the full lifecycle of tenant invitations.

```python
from oxutils.auth.invitations.backend import invitation_backend

# Create invitation (validates: not already member, no duplicate, rate limit)
invitation = invitation_backend.create_invitation(
    tenant=tenant,
    email="newuser@example.com",
    invited_by=request.user,
    role="member",          # "member", "admin", or "owner"
    message="Welcome!",     # optional
)

# Accept invitation
invitation = invitation_backend.accept_invitation(token="...", user=user)

# Cancel invitation
invitation = invitation_backend.cancel_invitation(token="...", cancelled_by=user)

# Validate token (returns invitation or None)
invitation = invitation_backend.validate_token("...")

# List pending invitations for a user
invitations = invitation_backend.get_user_invitations(user)

# List all invitations for a tenant
invitations = invitation_backend.get_tenant_invitations(tenant)

# Batch-expire stale invitations
count = invitation_backend.expire_stale_invitations()
```

### Role Hierarchy

When creating invitations, the inviter's role determines what roles they can assign:

| Inviter Role | Can Invite As |
|-------------|---------------|
| **Owner** | Member, Admin, Owner |
| **Admin** | Member, Admin |
| **Member** | Member |

### Model

```python
class Invitation(BaseModelMixin):
    tenant: FK → TENANT_MODEL         # Target tenant
    invited_by: FK → AUTH_USER_MODEL  # Who sent it
    invitee: FK → AUTH_USER_MODEL     # Who accepted (nullable)
    email: EmailField                 # Invitee's email
    token: CharField(128)             # Unique invitation token
    status: CharField                 # pending/accepted/expired/cancelled
    role: CharField                   # member/admin/owner
    expires_at: DateTimeField         # Default: +7 days
    accepted_at: DateTimeField        # When accepted
    resend_count: PositiveSmallInt    # Resend counter (max 3)
    message: TextField                # Optional message
```

## Token Models

### RefreshTokenWhitelistModel

Stores active refresh tokens with session metadata.

```python
class RefreshTokenWhitelistModel(AbstractRefreshToken):
    user: FK → AUTH_USER_MODEL
    jti: CharField(32)
    enabled: BooleanField
    session: CharField(32)
    ip: GenericIPAddressField
    browser: CharField(32)
    os: CharField(32)
    device: CharField(32)
    is_mobile/is_tablet/is_pc/is_bot: BooleanField
```

### GenericTokenModel

Stores single-use tokens for password reset and other purposes.

```python
class GenericTokenModel(BaseToken):
    user: FK → AUTH_USER_MODEL
    token: CharField(255)
    purpose: CharField(32)   # e.g., "PASS_RESET_ACCESS"
```

### Session Limits

`RefreshTokenManager` enforces `JWT_ALL_AUTH_MAX_SESSIONS` (default: 4). When exceeded, the oldest session is automatically revoked.

## Email Adapter

`JWTAllAuthAdapter` extends allauth's `DefaultAccountAdapter` with:

- Email normalization (trim + lowercase)
- Duplicate verified email detection
- Custom template paths for verification emails
- Dual HTML/text email rendering with fallback
- JWT-based confirmation URLs

### Custom Templates

```python
# settings.py
JWT_ALLAUTH_TEMPLATES = {
    "EMAIL_VERIFICATION": "path/to/verification_body.html",
    "EMAIL_VERIFICATION_SUBJECT": "path/to/verification_subject.txt",
    "PASS_RESET_EMAIL": "path/to/reset_body.html",
    "PASS_RESET_EMAIL_TEXT": "path/to/reset_body.txt",
    "PASS_RESET_SUBJECT": "path/to/reset_subject.txt",
}
```

## Registration Flow

Two flows are supported:

### Standard Registration

1. `POST /auth/register` without token
2. User is created, refresh token generated
3. Verification email sent via `UserEmailService`

### Invitation-Based Registration

1. `POST /auth/register` with `token` field
2. Token is validated via `InvitationBackend.validate_token()`
3. User is created/reused, added to tenant
4. Email is auto-confirmed (no verification needed)

## Security

### Rate Limiting

| Scope | Rate | Endpoints |
|-------|------|-----------|
| AnonRate | Django default | login, register, refresh, verify-email, password_reset |
| UserRate | Django default | reauthenticate, change_password, set-new-password |
| email_add | 5/hour | POST /emails |
| email_verification | 10/hour | POST /emails/{email}/verify |
| email_modification | 20/hour | PUT/DELETE /emails/{email} |
| invitations | 30/hour | Create, accept, cancel, resend invitations |

### Password Parameters

All password endpoints are decorated with `sensitive_post_parameters_m`, ensuring passwords are never logged in error reports.

### Token Security

- Refresh tokens: **rotated** on each refresh (old JTI deleted, new one created)
- Password reset tokens: **single-use** (deleted immediately after use)
- All tokens are validated against the whitelist before use
- Unknown JTIs trigger deletion of the entire session (suspicious activity)

### Cookie Security

```python
# All configurable via settings
AUTH_COOKIE_HTTP_ONLY = True          # No JS access
AUTH_COOKIE_SECURE = not DEBUG        # HTTPS in production
AUTH_COOKIE_SAME_SITE = "Lax"         # CSRF protection
```

### MFA

- TOTP with authenticator apps
- Recovery codes (one-time use)
- MFA signing salt must be explicitly configured in production
- Reauthentication required for sensitive operations

### Session Revocation

Revoke endpoints require the current session to be **older than 3 days**, preventing a freshly compromised token from destroying legitimate sessions.

## Customization

### Custom Schemas

Override any schema via `JWT_ALLAUTH_SCHEMAS`:

```python
JWT_ALLAUTH_SCHEMAS = {
    "LOGIN_SCHEMA": "myapp.auth.CustomLoginSchema",
    "REGISTER_SCHEMA": "myapp.auth.CustomRegisterSchema",
    "PASSWORD_RESET_SCHEMA": "myapp.auth.CustomPasswordResetSchema",
    "PASSWORD_CHANGE_SCHEMA": "myapp.auth.CustomPasswordChangeSchema",
}
```

### Custom Adapter

Extend `JWTAllAuthAdapter` to add custom behavior:

```python
from oxutils.auth.adapter import JWTAllAuthAdapter

class MyAdapter(JWTAllAuthAdapter):
    def custom_signup(self, request, user):
        # Custom logic after registration
        user.profile.plan = "free"
        user.profile.save()
```

### Custom Token Class

Replace the refresh token class:

```python
JWT_ALLAUTH_REFRESH_TOKEN = "myapp.tokens.CustomRefreshToken"
```

## Integration

### With Tenant System

The invitations module integrates with `django-tenants`:

```python
# settings.py
TENANT_MODEL = "oxiliere.Tenant"

# Invitation backs onto BaseTenant.add_user():
# invitation.accept(user) → tenant.add_user(user, is_owner=..., is_admin=...)
```

### With Email Service

The registration flow uses `UserEmailService` for verification emails. This integrates with allauth's email verification flow.

## Best Practices

1. **Always set `MFA_SIGNING_SALT` in production** — the dev default is intentionally weak
2. **Use HTTPS in production** — ensures `AUTH_COOKIE_SECURE` is enabled
3. **Set `OXI_COOKIE_DOMAIN`** — ensures cookies work across subdomains
4. **Configure `ACCOUNT_FRONTEND_URLS`** — ensures email links point to your SPA
5. **Keep `JWT_ALL_AUTH_MAX_SESSIONS`** reasonable (default: 4)
6. **Set `INVITATION_EXPIRY_DAYS`** to limit stale invitations
7. **Monitor `expire_stale_invitations()`** via a cron job
8. **Override `RegisterSchema.custom_signup()`** for post-registration logic

## Troubleshooting

### Login returns 401 but credentials are correct
→ Check that the email is **verified** (`EmailAddress.objects.filter(user=user, verified=True)`). The adapter enforces email verification by default.

### Refresh token not rotating
→ Verify `JWT_ALLAUTH_REFRESH_TOKEN_AS_COOKIE` is `True` and the cookie is being set with the correct domain.

### MFA key not working
→ Ensure `MFA_SIGNING_SALT` is set and matches across all deployments. The salt is used to sign the MFA key exchanged between login and MFA verification.

### Invitations not being accepted
→ Check that `TENANT_MODEL` is configured correctly and the tenant's `add_user()` method is available. The invitation backend calls `tenant.add_user()`.

### Custom templates not loading
→ Use `JWT_ALLAUTH_TEMPLATES` dict (not `JWT_ALLAUTH_TEMPLATES` as an object). The `get_template_path()` function uses `dict.get()`, not `getattr()`.

## Related Documentation

- [Permissions System](permissions.md) — Role-based access control
- [JWT Security](jwt_security.md) — JWT token security details
- [Settings Reference](settings.md) — All available settings
- [Mixins](mixins.md) — DetailDictMixin and other base classes
