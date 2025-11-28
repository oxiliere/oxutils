from enum import Enum



class InvoiceStatusEnum(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    REFUNDED = 'refunded'
