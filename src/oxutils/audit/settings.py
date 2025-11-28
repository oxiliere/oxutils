# Oxiliere Audit settings

AUDITLOG_DISABLE_REMOTE_ADDR = False
AUDITLOG_MASK_TRACKING_FIELDS = (
    "password",
    "api_key",
    "secret_token",
    "token",
)

AUDITLOG_EXCLUDE_TRACKING_FIELDS = (
    "created_at",
    "updated_at",
)

CID_GENERATE = False
AUDITLOG_CID_GETTER = "cid.locals.get_cid"
