from datetime import timedelta
from typing import List

from django.db import models
from django.http import HttpRequest
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from ninja_extra import (
    ControllerBase,
    api_controller,
    http_delete,
    http_get,
)
from ninja_extra.permissions import IsAuthenticated
from ninja_jwt.utils import datetime_from_epoch

from oxutils.auth.exceptions import ForbidNewSession
from oxutils.auth.tokens.models import RefreshTokenWhitelistModel
from oxutils.auth.utils import load_user
from oxutils.exceptions import (
    ExceptionCode,
)
from oxutils.mixins.schemas import ResponseSchema

from .schemas import UserSession


@api_controller("/user-sessions", permissions=[IsAuthenticated])
class UserSessionController(ControllerBase):
    """
    Controller for managing user sessions (refresh tokens)
    """

    def _validate_current_session_age(self, request: HttpRequest) -> None:
        """
        Validate that the current session (the one making the request) is older than 3 days
        This ensures account security by preventing new sessions from deleting established sessions.
        """
        # Get the current session token from Authorization header

        cat_claim = getattr(request.user, "token_created_at", None)

        if not cat_claim:
            raise ForbidNewSession

        token_created_at = datetime_from_epoch(cat_claim)
        three_days_ago = timezone.now() - timedelta(days=3)

        if token_created_at > three_days_ago:
            raise ForbidNewSession

    @http_get("", response=List[UserSession])
    def get_user_sessions(self, request: HttpRequest):
        """
        Get all active sessions for the current user
        """
        session_claim = getattr(request.user, "token_session", None)

        sessions = (
            RefreshTokenWhitelistModel.objects.filter(user__pk=request.user.pk)
            .annotate(
                is_current=models.Case(
                    models.When(session=session_claim, then=models.Value(True)),
                    default=models.Value(False),
                    output_field=models.BooleanField(),
                )
            )
            .distinct("session")
            .order_by("session", "-created")
        )

        return sessions

    @http_delete("/{session_id}", response=ResponseSchema)
    @load_user
    def revoke_session(self, request: HttpRequest, session_id: str):
        """
        Revoke a specific session (delete refresh token)
        Validates that current session is older than 3 days before allowing deletion
        """
        self._validate_current_session_age(request)

        session = RefreshTokenWhitelistModel.objects.filter(session=session_id, user=request.user)

        session.delete()

        return ResponseSchema(
            code=ExceptionCode.SUCCESS, detail=str(_("Session révoquée avec succès."))
        )

    @http_delete("", response=ResponseSchema)
    def revoke_all_sessions(self, request: HttpRequest):
        """
        Revoke all sessions for the current user
        Validates that current session is older than 3 days before allowing deletion
        """
        self._validate_current_session_age(request)

        session_claim = getattr(request.user, "token_session", None)

        deleted_count = (
            RefreshTokenWhitelistModel.objects.filter(user__pk=request.user.pk)
            .exclude(session=session_claim)
            .delete()[0]
        )

        return ResponseSchema(
            code=ExceptionCode.SUCCESS,
            detail=_("Toutes les sessions ont été révoquées avec succès ({} sessions).").format(
                deleted_count
            ),
        )

    @http_delete("/others", response=ResponseSchema)
    def revoke_other_sessions(self, request: HttpRequest):
        """
        Revoke all other sessions except the current one
        Validates that current session is older than 3 days before allowing deletion
        """
        self._validate_current_session_age(request)

        session_claim = getattr(request.user, "token_session", None)
        deleted_count = RefreshTokenWhitelistModel.objects.filter(
            user__pk=request.user.pk
        ).exclude(session=session_claim).delete()[0]

        return ResponseSchema(
            code=ExceptionCode.SUCCESS,
            detail=str(
                _("Toutes les autres sessions ont été révoquées avec succès ({} sessions).").format(
                    deleted_count
                )
            ),
        )
