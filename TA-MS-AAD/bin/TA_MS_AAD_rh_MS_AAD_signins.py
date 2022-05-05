
import import_declare_test

from splunktaucclib.rest_handler.endpoint import (
    field,
    validator,
    RestModel,
    DataInputModel,
)
from splunktaucclib.rest_handler import admin_external, util
from splunktaucclib.rest_handler.admin_external import AdminExternalHandler
import logging

util.remove_http_proxy_env_vars()


fields = [
    field.RestField(
        'AAD_sign_in_note',
        required=False,
        encrypted=False,
        default=None,
        validator=None
    ), 
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
            max_len=80, 
            min_len=1, 
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
            max_len=8192, 
            min_len=0, 
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
        'sign_in_sourcetype',
        required=True,
        encrypted=False,
        default='azure:aad:signin',
        validator=validator.String(
            max_len=8192, 
            min_len=0, 
        )
    ), 
    field.RestField(
        'start_date',
        required=False,
        encrypted=False,
        default=None,
        validator=validator.String(
            max_len=8192, 
            min_len=0, 
        )
    ), 
    field.RestField(
        'filter',
        required=False,
        encrypted=False,
        default=None,
        validator=validator.AllOf(
            validator.String(
                max_len=8192, 
                min_len=0, 
            ), 
            validator.Pattern(
                regex=r"""^\$filter\=""", 
            )
        )
    ), 
    field.RestField(
        'query_window_size',
        required=True,
        encrypted=False,
        default='0',
        validator=validator.AllOf(
            validator.String(
                max_len=8192, 
                min_len=0, 
            ), 
            validator.Number(
                max_val=100000, 
                min_val=0, 
            )
        )
    ), 
    field.RestField(
        'query_backoff_throttle',
        required=True,
        encrypted=False,
        default='420',
        validator=validator.String(
            max_len=8192, 
            min_len=0, 
        )
    ), 
    field.RestField(
        'endpoint',
        required=True,
        encrypted=False,
        default='v1.0',
        validator=None
    ), 

    field.RestField(
        'disabled',
        required=False,
        validator=None
    )

]
model = RestModel(fields, name=None)



endpoint = DataInputModel(
    'MS_AAD_signins',
    model,
)


if __name__ == '__main__':
    logging.getLogger().addHandler(logging.NullHandler())
    admin_external.handle(
        endpoint,
        handler=AdminExternalHandler,
    )
