# encoding = utf-8
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
from ta_azure_utils.auth import get_mgmt_access_token
from ta_azure_utils.topology import get_topology_by_rg
import requests

bin_dir = os.path.basename(__file__)

class ModInputazure_topology_man(base_mi.BaseModInput):

    def __init__(self):
        use_single_instance = False
        super(ModInputazure_topology_man, self).__init__("ta_ms_aad", "azure_topology_man", use_single_instance)
        self.global_checkbox_fields = None

    def get_scheme(self):
        """overloaded splunklib modularinput method"""
        scheme = super(ModInputazure_topology_man, self).get_scheme()
        scheme.title = ("Azure Topology (manual)")
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
        scheme.add_argument(smi.Argument("subscription_id", title="Subscription ID",
                                         description="",
                                         required_on_create=True,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("environment", title="Environment",
                                         description="",
                                         required_on_create=True,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("source_type", title="Topology Sourcetype",
                                         description="",
                                         required_on_create=True,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("network_watcher_name", title="Network Watcher Name",
                                         description="Network Watchers provide access to topology data.",
                                         required_on_create=True,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("network_watcher_resource_group", title="Network Watcher Resource Group",
                                         description="Specify the Resource Group containing the Network Watcher.",
                                         required_on_create=True,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("target_resource_group", title="Target Resource Group",
                                         description="Specify the Resource Group to enumerate topology. This Resource Group should be in the same region as the Network Watcher.",
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
        source_type = helper.get_arg("source_type")
        tenant_id = helper.get_arg("tenant_id")
        network_watcher_name = helper.get_arg("network_watcher_name")
        network_watcher_resource_group = helper.get_arg("network_watcher_resource_group")
        target_resource_group = helper.get_arg("target_resource_group")
        environment = helper.get_arg("environment")
            
        api_version = "2018-11-01"
        
        access_token = get_mgmt_access_token(client_id, client_secret, tenant_id, environment, helper)
        
        topology = get_topology_by_rg(helper, access_token, subscription_id, environment, api_version, network_watcher_resource_group, network_watcher_name, target_resource_group)
                        
        if len(topology) > 0:
            try:
                # Try the Python 2 way
                for key, resource in topology.iteritems():
                    
                    e = helper.new_event(
                        source=helper.get_input_type(), 
                        index=helper.get_output_index(), 
                        sourcetype=source_type, 
                        data=json.dumps(resource))
                    ew.write_event(e)
            except Exception as e:
                try:
                    # Try the Python 3 way
                    for key, resource in topology.items():
                        e = helper.new_event(
                            source=helper.get_input_type(), 
                            index=helper.get_output_index(), 
                            sourcetype=source_type, 
                            data=json.dumps(resource))
                        ew.write_event(e)
                except Exception as e:
                    raise e
                    

    def get_account_fields(self):
        account_fields = []
        account_fields.append("azure_app_account")
        return account_fields

    def get_checkbox_fields(self):
        checkbox_fields = []
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
    exitcode = ModInputazure_topology_man().run(sys.argv)
    sys.exit(exitcode)
