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
from ta_azure_utils.auth import get_mgmt_access_token
from ta_azure_utils.resource_groups import get_resource_groups_by_location
from ta_azure_utils.topology import get_topology_by_rg
from ta_azure_utils.utils import get_items
import re
import requests

bin_dir = os.path.basename(__file__)

class ModInputazure_topology_automatic(base_mi.BaseModInput):

    def __init__(self):
        use_single_instance = False
        super(ModInputazure_topology_automatic, self).__init__("ta_ms_aad", "azure_topology_automatic", use_single_instance)
        self.global_checkbox_fields = None

    def get_scheme(self):
        """overloaded splunklib modularinput method"""
        scheme = super(ModInputazure_topology_automatic, self).get_scheme()
        scheme.title = ("Azure Topology (auto)")
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
        
        environment = helper.get_arg("environment")
        if(environment == "gov"):
            management_base_url = "https://management.usgovcloudapi.net"
        else:
            management_base_url = "https://management.azure.com"
            
        api_version = "2018-11-01"
        
        access_token = get_mgmt_access_token(client_id, client_secret, tenant_id, environment, helper)
        
        network_watcher_url = management_base_url + "/subscriptions/%s/providers/Microsoft.Network/networkWatchers?api-version=%s" % (subscription_id, api_version)
        network_watchers = get_items(helper, access_token, network_watcher_url)
        
        resource_group_locations = get_resource_groups_by_location(helper, access_token, subscription_id, environment)
        
        # The resource groups are grouped by location, so loop through locations
        for location in resource_group_locations:
            
            # Get the network watcher(s) for this location
            for watcher in network_watchers:
                if watcher["location"] == location:
                    
                    # Get the resource group and name for this network watcher
                    resourceGroupName = re.search('\/resourceGroups\/(.+?)\/providers', watcher["id"]).group(1)
                    networkWatcherName = watcher["name"]
                    
                    # Get resource groups in the same location as this watcher
                    for targetResourceGroupName in resource_group_locations[location]:
                        
                        # Get the topology for this resource group
                        topology = get_topology_by_rg(helper, access_token, subscription_id, environment, api_version, resourceGroupName, networkWatcherName, targetResourceGroupName)
                        
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
    exitcode = ModInputazure_topology_automatic().run(sys.argv)
    sys.exit(exitcode)
