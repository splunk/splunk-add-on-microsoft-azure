
import ta_ms_aad_declare

from splunktaucclib.rest_handler.endpoint import (
    field,
    validator,
    RestModel,
    DataInputModel,
)
from splunktaucclib.rest_handler import admin_external, util
from splunk_aoblib.rest_migration import ConfigMigrationHandler

util.remove_http_proxy_env_vars()


fields = [
    field.RestField(
        'interval',
        required=True,
        encrypted=False,
        default=None,
        validator=validator.Pattern(
            regex=r"""^\-[1-9]\d*$|^\d*$""", 
        )
    ), 
    field.RestField(
        'index',
        required=True,
        encrypted=False,
        default='default',
        validator=validator.String(
            min_len=1, 
            max_len=80, 
        )
    ), 
    field.RestField(
        'azure_app_account',
        required=True,
        encrypted=False,
        default=None,
        validator=None
    ), 
    field.RestField(
        'tenant_id',
        required=True,
        encrypted=False,
        default=None,
        validator=validator.String(
            min_len=0, 
            max_len=8192, 
        )
    ), 
    field.RestField(
        'subscription_id',
        required=True,
        encrypted=False,
        default=None,
        validator=validator.String(
            min_len=0, 
            max_len=8192, 
        )
    ), 
    field.RestField(
        'environment',
        required=True,
        encrypted=False,
        default='public',
        validator=None
    ), 
    field.RestField(
        'collect_virtual_machine_data',
        required=False,
        encrypted=False,
        default=None,
        validator=None
    ), 
    field.RestField(
        'virtual_machine_sourcetype',
        required=True,
        encrypted=False,
        default='azure:compute:vm',
        validator=validator.String(
            min_len=0, 
            max_len=8192, 
        )
    ), 
    field.RestField(
        'collect_managed_disk_data',
        required=False,
        encrypted=False,
        default=None,
        validator=None
    ), 
    field.RestField(
        'managed_disk_sourcetype',
        required=True,
        encrypted=False,
        default='azure:compute:disk',
        validator=validator.String(
            min_len=0, 
            max_len=8192, 
        )
    ), 
    field.RestField(
        'collect_image_data',
        required=False,
        encrypted=False,
        default=None,
        validator=None
    ), 
    field.RestField(
        'image_sourcetype',
        required=True,
        encrypted=False,
        default='azure:compute:image',
        validator=validator.String(
            min_len=0, 
            max_len=8192, 
        )
    ), 
    field.RestField(
        'collect_snapshot_data',
        required=False,
        encrypted=False,
        default=None,
        validator=None
    ), 
    field.RestField(
        'snapshot_sourcetype',
        required=True,
        encrypted=False,
        default='azure:compute:snapshot',
        validator=validator.String(
            min_len=0, 
            max_len=8192, 
        )
    ), 

    field.RestField(
        'disabled',
        required=False,
        validator=None
    )

]
model = RestModel(fields, name=None)



endpoint = DataInputModel(
    'azure_comp',
    model,
)


if __name__ == '__main__':
    admin_external.handle(
        endpoint,
        handler=ConfigMigrationHandler,
    )
