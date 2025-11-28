from typing import Optional, Dict, Any
from ninja import Schema



class ResponseSchema(Schema):
    """
    Standardized error response schema matching APIException format.
    Use this for documenting error responses in API endpoints.
    """
    detail: str
    code: str
    errors: Optional[Dict[str, Any]] = None
