
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
        default=86400,
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
        'subscription_id',
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
        'collect_virtual_network_data',
        required=False,
        encrypted=False,
        default=None,
        validator=None
    ), 
    field.RestField(
        'virtual_network_sourcetype',
        required=True,
        encrypted=False,
        default='azure:vnet',
        validator=validator.String(
            max_len=8192, 
            min_len=0, 
        )
    ), 
    field.RestField(
        'collect_network_interface_data',
        required=False,
        encrypted=False,
        default=None,
        validator=None
    ), 
    field.RestField(
        'network_interface_sourcetype',
        required=True,
        encrypted=False,
        default='azure:vnet:nic',
        validator=validator.String(
            max_len=8192, 
            min_len=0, 
        )
    ), 
    field.RestField(
        'collect_security_group_data',
        required=False,
        encrypted=False,
        default=None,
        validator=None
    ), 
    field.RestField(
        'security_group_sourcetype',
        required=True,
        encrypted=False,
        default='azure:vnet:nsg',
        validator=validator.String(
            max_len=8192, 
            min_len=0, 
        )
    ), 
    field.RestField(
        'collect_public_ip_address_data',
        required=False,
        encrypted=False,
        default=None,
        validator=None
    ), 
    field.RestField(
        'public_ip_sourcetype',
        required=True,
        encrypted=False,
        default='azure:vnet:ip:public',
        validator=validator.String(
            max_len=8192, 
            min_len=0, 
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
    'azure_virtual_network',
    model,
)


if __name__ == '__main__':
    logging.getLogger().addHandler(logging.NullHandler())
    admin_external.handle(
        endpoint,
        handler=AdminExternalHandler,
    )
