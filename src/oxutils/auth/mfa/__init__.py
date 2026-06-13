from django.conf import settings
from allauth.mfa import app_settings
from oxutils.auth.mfa.base.controllers import MFAAuthenticateController
from oxutils.auth.mfa.recovery_codes.controllers import RecoveryCodeController
from oxutils.auth.mfa.totp.controllers import TOTPController



def get_mfa_controllers():
    ctrls = []

    if 'allauth.mfa' in settings.INSTALLED_APPS:
        ctrls.append(MFAAuthenticateController)
    else:
        return ctrls

    if "totp" in app_settings.SUPPORTED_TYPES:
        ctrls.append(TOTPController)

    if "recovery_codes" in app_settings.SUPPORTED_TYPES:
        ctrls.append(RecoveryCodeController)

    return ctrls
