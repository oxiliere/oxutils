import contextvars
from oxutils.oxiliere.utils import get_system_tenant_schema_name


current_tenant_schema_name: contextvars.ContextVar[str] = contextvars.ContextVar(
    "current_tenant_schema_name",
    default=get_system_tenant_schema_name()
)


def get_current_tenant_schema_name() -> str:
    return current_tenant_schema_name.get()


def set_current_tenant_schema_name(schema_name: str):
    current_tenant_schema_name.set(schema_name)


