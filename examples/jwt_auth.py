"""
JWT Authentication Example

Shows how to use JWT authentication with Django Ninja.
"""

from ninja import NinjaAPI
from ninja.security import HttpBearer
from oxutils.jwt.client import verify_token
import jwt

# 1. Create JWT authentication class
class JWTAuth(HttpBearer):
    def authenticate(self, request, token):
        try:
            payload = verify_token(token)
            return payload
        except jwt.InvalidTokenError:
            return None

# 2. Create API with authentication
api = NinjaAPI(auth=JWTAuth())

# 3. Protected endpoints
@api.get("/users/me")
def get_current_user(request):
    """Get current user from JWT token."""
    user_id = request.auth.get('sub')
    email = request.auth.get('email')
    
    return {
        "user_id": user_id,
        "email": email,
    }

@api.get("/protected")
def protected_endpoint(request):
    """Example protected endpoint."""
    return {"message": "You are authenticated!"}

# 4. Public endpoints (no auth required)
@api.get("/public", auth=None)
def public_endpoint(request):
    """Public endpoint without authentication."""
    return {"message": "This is public"}
