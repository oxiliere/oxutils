# Auditlog masks


def number_mask(value: str) -> str:
    """Mask a number showing only the last 4 digits.
    
    Args:
        value: The number string to mask
        
    Returns:
        Masked string with format: ****1234
    """
    if not value:
        return ""
    
    value_str = str(value).strip()
    if len(value_str) <= 4:
        return "*" * len(value_str)
    
    return "****" + value_str[-4:]


def phone_number_mask(value: str) -> str:
    """Mask a phone number showing only the last 4 digits.
    
    Args:
        value: The phone number to mask
        
    Returns:
        Masked phone number with format: ****1234
    """
    if not value:
        return ""
    
    # Remove common phone number formatting characters
    cleaned = str(value).replace(" ", "").replace("-", "").replace("(", "").replace(")", "").replace("+", "")
    
    if len(cleaned) <= 4:
        return "*" * len(cleaned)
    
    return "****" + cleaned[-4:]


def credit_card_mask(value: str) -> str:
    """Mask a credit card number showing only the last 4 digits.
    
    Args:
        value: The credit card number to mask
        
    Returns:
        Masked credit card with format: ****1234
    """
    if not value:
        return ""
    
    # Remove spaces and dashes from credit card number
    cleaned = str(value).replace(" ", "").replace("-", "")
    
    if len(cleaned) <= 4:
        return "*" * len(cleaned)
    
    return "****" + cleaned[-4:]

def email_mask(value: str) -> str:
    """Mask an email address showing only the first character and domain.
    
    Args:
        value: The email address to mask
        
    Returns:
        Masked email with format: j***@example.com
    """
    if not value:
        return ""
    
    value_str = str(value).strip()
    
    if "@" not in value_str:
        # Not a valid email format, mask most of it
        if len(value_str) <= 2:
            return "*" * len(value_str)
        return value_str[0] + "*" * (len(value_str) - 1)
    
    local, domain = value_str.rsplit("@", 1)
    
    if not local:
        return "***@" + domain
    
    if len(local) == 1:
        masked_local = "*"
    elif len(local) == 2:
        masked_local = local[0] + "*"
    else:
        masked_local = local[0] + "*" * (len(local) - 1)
    
    return masked_local + "@" + domain

