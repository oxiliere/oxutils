from enum import Enum



class ExportStatus(str, Enum):
    FAILED = 'failed'
    SUCCESS = 'success'
    PENDING = 'pending'
