from django.utils.translation import gettext_lazy as _
from oxutils.mixins.base import DetailDictMixin



class OxException(Exception):
    pass


try:
    from ninja_extra import status, exceptions

    STATUS_CODE = status.HTTP_500_INTERNAL_SERVER_ERROR
    NinjaException = exceptions.APIException
except:
    STATUS_CODE = 500
    NinjaException = OxException


class ExceptionCode:
    INTERNAL_ERROR = 'internal_error'
    FAILED_ERROR = 'failed_error'
    VALIDATION_ERROR = 'validation_error'
    CONFLICT_ERROR = 'conflict_error'
    NOT_FOUND = 'not_found'
    UNAUTHORIZED = 'unauthorized'
    FORBIDDEN = 'forbidden'
    BAD_REQUEST = 'bad_request'
    AUTHENTICATION_FAILED = 'authentication_failed'
    PERMISSION_DENIED = 'permission_denied'
    METHOD_NOT_ALLOWED = 'method_not_allowed'
    NOT_ACCEPTABLE = 'not_acceptable'
    TIMEOUT = 'timeout'
    RATE_LIMIT_EXCEEDED = 'rate_limit_exceeded'
    SERVICE_UNAVAILABLE = 'service_unavailable'
    INVALID_TOKEN = 'invalid_token'
    EXPIRED_TOKEN = 'expired_token'
    INVALID_CREDENTIALS = 'invalid_credentials'
    ACCOUNT_DISABLED = 'account_disabled'
    ACCOUNT_NOT_VERIFIED = 'account_not_verified'
    DUPLICATE_ENTRY = 'duplicate_entry'
    RESOURCE_LOCKED = 'resource_locked'
    PAYMENT_REQUIRED = 'payment_required'
    INSUFFICIENT_PERMISSIONS = 'insufficient_permissions'
    QUOTA_EXCEEDED = 'quota_exceeded'
    INVALID_INPUT = 'invalid_input'
    MISSING_PARAMETER = 'missing_parameter'
    INVALID_PARAMETER = 'invalid_parameter'
    OPERATION_NOT_PERMITTED = 'operation_not_permitted'
    RESOURCE_EXHAUSTED = 'resource_exhausted'
    PRECONDITION_FAILED = 'precondition_failed'

    # Non Error
    SUCCESS = 'success'
    


class APIException(DetailDictMixin, NinjaException):
    status_code = STATUS_CODE
    default_code = ExceptionCode.INTERNAL_ERROR
    default_detail = _('We encountered an error, please try again later.')


class NotFoundException(APIException):
    status_code = 404
    default_code = ExceptionCode.NOT_FOUND
    default_detail = _('The requested resource does not exist')


class ValidationException(APIException):
    status_code = 400
    default_code = ExceptionCode.VALIDATION_ERROR
    default_detail = _('Validation error')


class ConflictException(APIException):
    status_code = 409
    default_code = ExceptionCode.CONFLICT_ERROR
    default_detail = _('The operation conflicts with existing data')


class DuplicateEntryException(APIException):
    status_code = 409
    default_code = ExceptionCode.DUPLICATE_ENTRY
    default_detail = _('A resource with these details already exists')


class PermissionDeniedException(APIException):
    status_code = 403
    default_code = ExceptionCode.PERMISSION_DENIED
    default_detail = _('You do not have permission to perform this action')


class UnauthorizedException(APIException):
    status_code = 401
    default_code = ExceptionCode.UNAUTHORIZED
    default_detail = _('Authentication is required')


class InvalidParameterException(APIException):
    status_code = 400
    default_code = ExceptionCode.INVALID_PARAMETER
    default_detail = _('Invalid parameter provided')


class MissingParameterException(APIException):
    status_code = 400
    default_code = ExceptionCode.MISSING_PARAMETER
    default_detail = _('Required parameter is missing')


class InternalErrorException(APIException):
    status_code = 500
    default_code = ExceptionCode.INTERNAL_ERROR
    default_detail = _('An unexpected error occurred while processing your request')
    
