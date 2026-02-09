from uuid import UUID

from ninja_extra import (
    api_controller,
    http_get,
    http_put,
    http_delete,
)
from ninja_extra.permissions import (
    IsAuthenticated,
)
from ninja_extra.pagination import (
    paginate,
    PaginatedResponseSchema,
    PageNumberPaginationExtra,
)
from oxutils.oxiliere.permissions import (
    IsTenantAdmin,
    IsTenantOwner,
)
from .schemas import (
    get_tenant_user_list_schema,
    get_tenant_user_detail_schema,
    UpdateTenantUserSchema,
    SetAdminSchema,
    SetOwnerSchema,
)
from .services import TenantUserService


TenantUserListSchema = get_tenant_user_list_schema()
TenantUserDetailSchema = get_tenant_user_detail_schema()

service = TenantUserService()


@api_controller('/users')
class UserController:

    @http_get(
        '',
        response=PaginatedResponseSchema[TenantUserListSchema],
        permissions=[IsAuthenticated, IsTenantAdmin],
    )
    @paginate(PageNumberPaginationExtra)
    def list_users(self):
        return service.list()

    @http_get(
        '/{user_id}',
        response=TenantUserDetailSchema,
        permissions=[IsAuthenticated, IsTenantAdmin],
    )
    def get_user(self, user_id: UUID):
        return service.get(user_id)

    @http_put(
        '/{user_id}',
        response=TenantUserDetailSchema,
        permissions=[IsAuthenticated, IsTenantOwner],
    )
    def update_user(self, user_id: UUID, payload: UpdateTenantUserSchema):
        return service.update(user_id, payload.dict(exclude_unset=True))

    @http_put(
        '/{user_id}/set-admin',
        response=TenantUserDetailSchema,
        permissions=[IsAuthenticated, IsTenantOwner],
    )
    def set_admin(self, user_id: UUID, payload: SetAdminSchema):
        return service.set_admin(user_id, payload.is_admin)

    @http_put(
        '/{user_id}/set-owner',
        response=TenantUserDetailSchema,
        permissions=[IsAuthenticated, IsTenantOwner],
    )
    def set_owner(self, user_id: UUID, payload: SetOwnerSchema):
        return service.set_owner(user_id, payload.is_owner)

    @http_delete(
        '/{user_id}',
        response={204: None},
        permissions=[IsAuthenticated, IsTenantOwner],
    )
    def remove_user(self, user_id: UUID):
        service.remove(user_id)
        return 204, None
