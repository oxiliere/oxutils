"""
Signals for the auth module.

All signals use ``django.dispatch.Signal`` with ``providing_args``
documented as keyword-only parameters.
"""
from django.dispatch import Signal

# ── Authentication ──────────────────────────────────────────────────

user_logged_in = Signal()
"""
Fired when a user successfully authenticates (login or reauthentication).

Args:
    sender: The controller class that handled the login.
    request: The HttpRequest object.
    user: The authenticated User instance.
"""

user_logged_out = Signal()
"""
Fired when a user logs out.

Args:
    sender: The controller class that handled the logout.
    request: The HttpRequest object.
    user: The User instance that was logged out.
"""

# ── Invitations ─────────────────────────────────────────────────────

invitation_sent = Signal()
"""
Fired when a new invitation is created and sent.

Args:
    sender: The InvitationBackend or controller.
    invitation: The Invitation instance.
    invited_by: The User who sent the invitation.
"""

invitation_resent = Signal()
"""
Fired when an invitation is resent (token renewed).

Args:
    sender: The InvitationController.
    invitation: The Invitation instance.
"""

invitation_accepted = Signal()
"""
Fired when an invitation is accepted (user added to tenant).

Args:
    sender: The InvitationBackend.
    invitation: The Invitation instance.
    user: The User who accepted.
"""

invitation_rejected = Signal()
"""
Fired when an invitation is cancelled / rejected.

Args:
    sender: The InvitationBackend or controller.
    invitation: The Invitation instance.
    cancelled_by: The User who cancelled (or None if system).
"""

# ── User status ─────────────────────────────────────────────────────

user_activated = Signal()
"""
Fired when a user account is activated.

Args:
    sender: The class/method that activated the user.
    user: The User instance.
    request: The HttpRequest (optional).
"""

user_deactivated = Signal()
"""
Fired when a user account is deactivated.

Args:
    sender: The class/method that deactivated the user.
    user: The User instance.
"""
