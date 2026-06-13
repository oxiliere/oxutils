"""
Token generator for invitations.
"""
import hashlib

from django.conf import settings
from django.utils import timezone
from django.utils.crypto import constant_time_compare


class InvitationTokenGenerator:
    """
    Generates and validates invitation tokens.

    Tokens are SHA256 hashes of (invitation_id + email + secret + timestamp).
    """

    def __init__(self):
        self.secret = getattr(settings, "SECRET_KEY", "default-secret")

    def make_token(self, invitation) -> str:
        raw = f"{invitation.pk}:{invitation.email}:{self.secret}:{timezone.now().timestamp()}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def check_token(self, invitation, token: str) -> bool:
        if not invitation or not token:
            return False

        # Check expiration
        if invitation.expires_at and timezone.now() > invitation.expires_at:
            return False

        # Compare the stored token
        return constant_time_compare(invitation.token, token)
