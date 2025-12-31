import contextvars
from oxutils.oxiliere.utils import get_system_tenant_oxi_id


current_tenant_schema_name: contextvars.ContextVar[str] = contextvars.ContextVar(
    "current_tenant_schema_name",
    default=f"[oxi_id] {get_system_tenant_oxi_id()}"
)


def get_current_tenant_schema_name() -> str:
    return current_tenant_schema_name.get()


def set_current_tenant_schema_name(schema_name: str):
    current_tenant_schema_name.set(schema_name)
