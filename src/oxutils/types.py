from typing import Annotated
from pydantic import BeforeValidator, EmailStr



def strip_and_lower(v: object) -> str:
    return str(v).strip().lower()


EmailApiType = Annotated[
    EmailStr,
    BeforeValidator(strip_and_lower),
]
