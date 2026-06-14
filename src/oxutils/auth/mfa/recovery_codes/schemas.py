from ninja import Schema
from typing import List


class RecoveryCodesGenerateSchema(Schema):
    """Schema for generating recovery codes"""
    pass


class RecoveryCodesStatusResponseSchema(Schema):
    """Schema for recovery codes status response"""
    is_active: bool
    unused_codes: List[str]
    total_count: int


class RecoveryCodesGenerateResponseSchema(Schema):
    """Schema for recovery codes generation response"""
    success: bool
    message: str
    codes: List[str]


class RecoveryCodesDownloadResponseSchema(Schema):
    """Schema for recovery codes download response"""
    content: str
    filename: str
    content_type: str
