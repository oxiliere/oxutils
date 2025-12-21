from ninja_extra import (
    api_controller,
    ControllerBase,
    http_post,
)
from .permissions import OxiliereServicePermission
from .schemas import CreateTenantSchema
from oxutils.mixins.schemas import ResponseSchema


@api_controller(
    '/setup',
    tags=['Setup'],
    auth=None,
    permissions=[
        OxiliereServicePermission(),
    ]
)
class SetupController(ControllerBase):
    
    @http_post(
        '/init',
        response=ResponseSchema,
    )
    def init(self, payload: CreateTenantSchema):
        try:
            payload.create_tenant()
        except Exception as e:
            return ResponseSchema(
                code='initialization_failed',
                detail=str(e)
            )
        return ResponseSchema(
            code='success',
            detail='Tenant initialized successfully'
        )
