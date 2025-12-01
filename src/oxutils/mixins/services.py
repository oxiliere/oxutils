from logging import Logger
from django.utils.translation import gettext_lazy as _
from auditlog.signals import accessed
from oxutils.settings import oxi_settings





class BaseService:
    """
    Base service class with exception handling
    
    Services should inherit from this class and override inner_exception_handler
    to handle service-specific exceptions.
    """

    logger: Logger | None = None


    def object_accessed(self, instance_class, instance):
        if oxi_settings.log_access:
            accessed(instance_class, instance)

    def inner_exception_handler(self, exc: Exception, logger: Logger):
        """
        Handle service-specific exceptions
        
        Override this method in child classes to handle custom exceptions.
        Should raise an APIException subclass if the exception is handled,
        or re-raise the original exception if not handled.
        
        Args:
            exc: The exception to handle
            logger: Logger instance for logging
            
        Raises:
            APIException: If the exception is handled
            Exception: Re-raises the original exception if not handled
        """
        # Default implementation does nothing, child classes should override
        raise exc

    def exception_handler(self, exc: Exception, logger: Logger | None = None):
        """
        Handle all exceptions with a standardized approach
        
        This method first calls inner_exception_handler for service-specific exceptions,
        then handles common Django and Python exceptions.
        
        Args:
            exc: The exception to handle
            logger: Optional logger instance
            
        Raises:
            APIException: Always raises an appropriate APIException subclass
        """
        from utils_mixins.exceptions import (
            NotFoundException,
            ValidationException,
            ConflictException,
            DuplicateEntryException,
            PermissionDeniedException,
            InvalidParameterException,
            MissingParameterException,
            InternalErrorException,
        )
        from django.core.exceptions import ValidationError, ObjectDoesNotExist
        from django.db import IntegrityError
        import logging

        if self.logger:
            logger = self.logger

        if logger is None:
            logger = logging.getLogger(__name__)
        
        # Log the exception
        logger.error(f"Service exception: {type(exc).__name__} - {str(exc)}")
        
        try:
            # First, try to handle service-specific exceptions
            self.inner_exception_handler(exc, logger)
        except Exception as inner_exc:
            # If inner_exception_handler raised an APIException, re-raise it
            from utils_mixins.exceptions import APIException
            if isinstance(inner_exc, APIException):
                raise inner_exc
            
            # Otherwise, continue with standard exception handling
            exc = inner_exc
        
        # Handle Django validation errors
        if isinstance(exc, ValidationError):
            detail = str(exc)
            if hasattr(exc, 'message_dict'):
                detail = {'detail': str(exc), 'errors': exc.message_dict}
            raise ValidationException(detail=detail) from exc
        
        # Handle object not found errors
        if isinstance(exc, ObjectDoesNotExist):
            raise NotFoundException(detail=str(exc) or None) from exc
        
        # Handle integrity errors (duplicate entries, foreign key violations)
        if isinstance(exc, IntegrityError):
            error_message = str(exc).lower()
            
            if 'unique' in error_message or 'duplicate' in error_message:
                raise DuplicateEntryException() from exc
            
            if 'foreign key' in error_message:
                raise InvalidParameterException(
                    detail=_('One or more referenced resources do not exist')
                ) from exc
            
            raise ConflictException() from exc
        
        # Handle value errors (invalid parameters)
        if isinstance(exc, ValueError):
            raise InvalidParameterException(detail=str(exc)) from exc
        
        # Handle permission errors
        if isinstance(exc, PermissionError):
            raise PermissionDeniedException(detail=str(exc) or None) from exc
        
        # Handle type errors (usually programming errors)
        if isinstance(exc, TypeError):
            logger.exception("Type error in service")
            raise InternalErrorException() from exc
        
        # Handle key errors (missing required data)
        if isinstance(exc, KeyError):
            raise MissingParameterException(
                detail=_('Required parameter {exc} is missing').format(exc=exc)
            ) from exc
        
        # Handle attribute errors
        if isinstance(exc, AttributeError):
            logger.exception("Attribute error in service")
            raise InternalErrorException() from exc
        
        # Default handler for unknown exceptions
        logger.exception(f"Unhandled exception in service: {type(exc).__name__}")
        raise InternalErrorException(
            detail=_('An unexpected error occurred. Please try again later or contact support.')
        ) from exc
