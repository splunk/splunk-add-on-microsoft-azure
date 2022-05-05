
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
        'collect_risk_detection_data',
        required=False,
        encrypted=False,
        default=None,
        validator=None
    ), 
    field.RestField(
        'risk_detection_sourcetype',
        required=True,
        encrypted=False,
        default='azure:aad:identity_protection:risk_detection',
        validator=validator.String(
            max_len=8192, 
            min_len=0, 
        )
    ), 
    field.RestField(
        'collect_risky_user_data',
        required=False,
        encrypted=False,
        default=None,
        validator=None
    ), 
    field.RestField(
        'risky_user_sourcetype',
        required=True,
        encrypted=False,
        default='azure:aad:identity_protection:risky_user',
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
    'MS_AAD_identity_protection',
    model,
)


if __name__ == '__main__':
    logging.getLogger().addHandler(logging.NullHandler())
    admin_external.handle(
        endpoint,
        handler=AdminExternalHandler,
    )
