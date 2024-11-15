# encoding = utf-8
'''

Copyright 2020 Splunk Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

'''
import os
import sys
import time
import datetime
import json
import import_declare_test
from splunklib import modularinput as smi
import traceback
import requests
from splunklib import modularinput as smi
from solnlib import conf_manager
from solnlib import log
from solnlib.modular_input import checkpointer
from splunktaucclib.modinput_wrapper import base_modinput  as base_mi 
import ta_azure_utils.auth as azauth
import ta_azure_utils.utils as azutils

bin_dir = os.path.basename(__file__)

class ModInputazure_virtual_network(base_mi.BaseModInput):

    def __init__(self):
        use_single_instance = False
        super(ModInputazure_virtual_network, self).__init__("ta_ms_aad", "azure_virtual_network", use_single_instance)
        self.global_checkbox_fields = None

    def get_scheme(self):
        """overloaded splunklib modularinput method"""
        scheme = super(ModInputazure_virtual_network, self).get_scheme()
        scheme.title = ("Azure Virtual Network")
        scheme.description = ("Go to the add-on\'s configuration UI and configure modular inputs under the Inputs menu.")
        scheme.use_external_validation = True
        scheme.streaming_mode_xml = True

        scheme.add_argument(smi.Argument("name", title="Name",
                                         description="",
                                         required_on_create=True))
        scheme.add_argument(smi.Argument("azure_app_account", title="Azure App Account",
                                         description="",
                                         required_on_create=True,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("tenant_id", title="Tenant ID",
                                         description="",
                                         required_on_create=True,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("azure_vnet_note", title="",
                                         description="This functionality has moved to the Splunk Add-on for Microsoft Cloud Services",
                                         required_on_create=False,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("subscription_id", title="Subscription ID",
                                         description="",
                                         required_on_create=True,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("environment", title="Environment",
                                         description="",
                                         required_on_create=True,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("collect_virtual_network_data", title="Collect Virtual Network Data",
                                         description="",
                                         required_on_create=False,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("virtual_network_sourcetype", title="Virtual Network Sourcetype",
                                         description="",
                                         required_on_create=True,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("collect_network_interface_data", title="Collect Network Interface Data",
                                         description="",
                                         required_on_create=False,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("network_interface_sourcetype", title="Network Interface Sourcetype",
                                         description="",
                                         required_on_create=True,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("collect_security_group_data", title="Collect Security Group Data",
                                         description="",
                                         required_on_create=False,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("security_group_sourcetype", title="Security Group Sourcetype",
                                         description="",
                                         required_on_create=True,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("collect_public_ip_address_data", title="Collect Public IP Address Data",
                                         description="",
                                         required_on_create=False,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("public_ip_sourcetype", title="Public IP Sourcetype",
                                         description="",
                                         required_on_create=True,
                                         required_on_edit=False))
        return scheme

    def get_app_name(self):
        return "TA-MS-AAD"

    def validate_input(helper, definition):
        pass

    def collect_events(helper, ew):
        global_account = helper.get_arg("azure_app_account")
        client_id = global_account["username"]
        client_secret = global_account["password"]
        subscription_id = helper.get_arg("subscription_id")
        tenant_id = helper.get_arg("tenant_id")
        event_source = "%s:tenant_id:%s" % (helper.input_type, tenant_id)
        input_name = helper.get_input_stanza_names()
        
        vnet_api_version = "2021-03-01"
        vnet_sourcetype = helper.get_arg("virtual_network_sourcetype")
        collect_vnets = helper.get_arg("collect_virtual_network_data")
        
        nic_api_version = "2021-03-01"
        nic_sourcetype = helper.get_arg("network_interface_sourcetype")
        collect_nics = helper.get_arg("collect_network_interface_data")
        
        nsg_api_version = "2021-03-01"
        nsg_sourcetype = helper.get_arg("security_group_sourcetype")
        collect_nsgs = helper.get_arg("collect_security_group_data")
        
        ip_api_version = "2021-03-01"
        ip_sourcetype = helper.get_arg("public_ip_sourcetype")
        collect_ips = helper.get_arg("collect_public_ip_address_data")
        
        environment = helper.get_arg("environment")
        management_base_url = azutils.get_environment_mgmt(environment)
        
        session = azauth.get_mgmt_session(client_id, client_secret, tenant_id, environment, helper)
    
        if(session):
            if(collect_vnets):
                helper.log_debug("_Splunk_ input_name=%s Collecting virtual network data. sourcetype='%s'" % (input_name, vnet_sourcetype))
                url = management_base_url + "/subscriptions/%s/providers/Microsoft.Network/virtualNetworks?api-version=%s" % (subscription_id, vnet_api_version)
                response = azutils.get_items_batch_session(helper=helper, url=url, session=session)
                items = None if response == None else response['value']
                while items:
                    for item in items:
                        event = helper.new_event(
                            data=json.dumps(item),
                            source = event_source.lower(),
                            index=helper.get_output_index(),
                            sourcetype=vnet_sourcetype)
                        ew.write_event(event)
                    sys.stdout.flush()
                    response = azutils.handle_nextLink(helper=helper, response=response, session=session)
                    items = None if response == None else response['value']
                    
            if(collect_nics):
                helper.log_debug("_Splunk_ input_name=%s Collecting nic data. sourcetype='%s'" % (input_name, nic_sourcetype))
                url = management_base_url + "/subscriptions/%s/providers/Microsoft.Network/networkInterfaces?api-version=%s" % (subscription_id, nic_api_version)
                response = azutils.get_items_batch_session(helper=helper, url=url, session=session)
                items = None if response == None else response['value']
                while items:
                    for item in items:
                        event = helper.new_event(
                            data=json.dumps(item),
                            source = event_source.lower(),
                            index=helper.get_output_index(),
                            sourcetype=nic_sourcetype)
                        ew.write_event(event)
                    sys.stdout.flush()
                    response = azutils.handle_nextLink(helper=helper, response=response, session=session)
                    items = None if response == None else response['value']
                    
            if(collect_nsgs):
                helper.log_debug("_Splunk_ input_name=%s Collecting nsg data. sourcetype='%s'" % (input_name, nsg_sourcetype))
                url = management_base_url + "/subscriptions/%s/providers/Microsoft.Network/networkSecurityGroups?api-version=%s" % (subscription_id, nsg_api_version)
                response = azutils.get_items_batch_session(helper=helper, url=url, session=session)
                items = None if response == None else response['value']
                while items:
                    for item in items:
                        event = helper.new_event(
                            data=json.dumps(item),
                            source = event_source.lower(),
                            index=helper.get_output_index(),
                            sourcetype=nsg_sourcetype)
                        ew.write_event(event)
                    sys.stdout.flush()
                    response = azutils.handle_nextLink(helper=helper, response=response, session=session)
                    items = None if response == None else response['value']
                    
            if(collect_ips):
                helper.log_debug("_Splunk_ input_name=%s Collecting IP address data. sourcetype='%s'" % (input_name, ip_sourcetype))
                url = management_base_url + "/subscriptions/%s/providers/Microsoft.Network/publicIPAddresses?api-version=%s" % (subscription_id, ip_api_version)
                response = azutils.get_items_batch_session(helper=helper, url=url, session=session)
                items = None if response == None else response['value']
                while items:
                    for item in items:
                        event = helper.new_event(
                            data=json.dumps(item),
                            source = event_source.lower(),
                            index=helper.get_output_index(),
                            sourcetype=ip_sourcetype)
                        ew.write_event(event)
                    sys.stdout.flush()
                    response = azutils.handle_nextLink(helper=helper, response=response, session=session)
                    items = None if response == None else response['value']
                    
        else:
            raise RuntimeError("Unable to obtain access token. Please check the Client ID, Client Secret, and Tenant ID")

    def get_account_fields(self):
        account_fields = []
        account_fields.append("azure_app_account")
        return account_fields

    def get_checkbox_fields(self):
        checkbox_fields = []
        checkbox_fields.append("collect_virtual_network_data")
        checkbox_fields.append("collect_network_interface_data")
        checkbox_fields.append("collect_security_group_data")
        checkbox_fields.append("collect_public_ip_address_data")
        return checkbox_fields

    def get_global_checkbox_fields(self):
        if self.global_checkbox_fields is None:
            checkbox_name_file = os.path.join(bin_dir, 'global_checkbox_param.json')
            try:
                if os.path.isfile(checkbox_name_file):
                    with open(checkbox_name_file, 'r') as fp:
                        self.global_checkbox_fields = json.load(fp)
                else:
                    self.global_checkbox_fields = []
            except Exception as e:
                self.log_error('Get exception when loading global checkbox parameter names. ' + str(e))
                self.global_checkbox_fields = []
        return self.global_checkbox_fields

if __name__ == "__main__":
    exitcode = ModInputazure_virtual_network().run(sys.argv)
    sys.exit(exitcode)
