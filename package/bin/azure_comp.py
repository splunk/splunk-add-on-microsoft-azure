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
import re
import ta_azure_utils.auth as azauth
import ta_azure_utils.utils as azutils

bin_dir = os.path.basename(__file__)

class ModInputazure_comp(base_mi.BaseModInput):

    def __init__(self):
        use_single_instance = False
        super(ModInputazure_comp, self).__init__("ta_ms_aad", "azure_comp", use_single_instance)
        self.global_checkbox_fields = None

    def get_scheme(self):
        """overloaded splunklib modularinput method"""
        scheme = super(ModInputazure_comp, self).get_scheme()
        scheme.title = ("Azure Compute")
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
        scheme.add_argument(smi.Argument("azure_compute_note", title="",
                                         description="This functionality has moved to the Splunk Add-on for Microsoft Cloud Services",
                                         required_on_create=False,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("collect_virtual_machine_data", title="Collect Virtual Machine Data",
                                         description="",
                                         required_on_create=False,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("virtual_machine_sourcetype", title="Virtual Machine Sourcetype",
                                         description="",
                                         required_on_create=True,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("collect_managed_disk_data", title="Collect Managed Disk Data",
                                         description="",
                                         required_on_create=False,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("managed_disk_sourcetype", title="Managed Disk Sourcetype",
                                         description="",
                                         required_on_create=True,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("collect_image_data", title="Collect Image Data",
                                         description="",
                                         required_on_create=False,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("image_sourcetype", title="Image Sourcetype",
                                         description="",
                                         required_on_create=True,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("collect_snapshot_data", title="Collect Snapshot Data",
                                         description="",
                                         required_on_create=False,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("snapshot_sourcetype", title="Snapshot Sourcetype",
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
        
        disk_api_version = "2020-12-01"
        disk_sourcetype = helper.get_arg("managed_disk_sourcetype")
        collect_disks = helper.get_arg("collect_managed_disk_data")
        
        image_api_version = "2021-07-01"
        image_sourcetype = helper.get_arg("image_sourcetype")
        collect_images = helper.get_arg("collect_image_data")
        
        snapshot_api_version = "2020-12-01"
        snapshot_sourcetype = helper.get_arg("snapshot_sourcetype")
        collect_snapshots = helper.get_arg("collect_snapshot_data")
        
        vm_api_version = "2021-07-01"
        vm_instance_view_api_version = "2021-07-01"
        vm_sourcetype = helper.get_arg("virtual_machine_sourcetype")
        vm_instance_view_sourcetype = vm_sourcetype + ":instanceView"
        collect_vms = helper.get_arg("collect_virtual_machine_data")
        
        environment = helper.get_arg("environment")
        management_base_url = azutils.get_environment_mgmt(environment)
        
        session = azauth.get_mgmt_session(client_id, client_secret, tenant_id, environment, helper)
    
        if(session):
            if(collect_disks):
                helper.log_debug("_Splunk_ input_name=%s Collecting managed disk data. sourcetype='%s'" % (input_name, disk_sourcetype))
                url = management_base_url + "/subscriptions/%s/providers/Microsoft.Compute/disks?api-version=%s" % (subscription_id, disk_api_version)
                response = azutils.get_items_batch_session(helper=helper, url=url, session=session)
                items = None if response == None else response['value']
                while items:
                    for item in items:
                        event = helper.new_event(
                            data=json.dumps(item),
                            source = event_source.lower(),
                            index=helper.get_output_index(),
                            sourcetype=disk_sourcetype)
                        ew.write_event(event)
                    sys.stdout.flush()
                    response = azutils.handle_nextLink(helper=helper, response=response, session=session)
                    items = None if response == None else response['value']
                    
                    
            if(collect_images):
                helper.log_debug("_Splunk_ input_name=%s Collecting image data. sourcetype='%s'" % (input_name, image_sourcetype))
                url = management_base_url + "/subscriptions/%s/providers/Microsoft.Compute/images?api-version=%s" % (subscription_id, image_api_version)
                response = azutils.get_items_batch_session(helper=helper, url=url, session=session)
                items = None if response == None else response['value']
                while items:
                    for item in items:
                        event = helper.new_event(
                            data=json.dumps(item),
                            source=event_source.lower(),
                            index=helper.get_output_index(),
                            sourcetype=image_sourcetype)
                        ew.write_event(event)
                    sys.stdout.flush()
                    response = azutils.handle_nextLink(helper=helper, response=response, session=session)
                    items = None if response == None else response['value']
                    
            if(collect_snapshots):
                helper.log_debug("_Splunk_ input_name=%s Collecting snapshot data. sourcetype='%s'" % (input_name, snapshot_sourcetype))
                url = management_base_url + "/subscriptions/%s/providers/Microsoft.Compute/snapshots?api-version=%s" % (subscription_id, snapshot_api_version)
                response = azutils.get_items_batch_session(helper=helper, url=url, session=session)
                items = None if response == None else response['value']
                while items:
                    for item in items:
                        event = helper.new_event(
                            data=json.dumps(item),
                            source=event_source.lower(),
                            index=helper.get_output_index(),
                            sourcetype=snapshot_sourcetype)
                        ew.write_event(event)
                    sys.stdout.flush()
                    response = azutils.handle_nextLink(helper=helper, response=response, session=session)
                    items = None if response == None else response['value']
                    
            if(collect_vms):
                helper.log_debug("_Splunk_ input_name=%s Collecting virtual machine data. sourcetype='%s'" % (input_name, vm_sourcetype))
                url = management_base_url + "/subscriptions/%s/providers/Microsoft.Compute/virtualMachines?api-version=%s" % (subscription_id, vm_api_version)
                response = azutils.get_items_batch_session(helper=helper, url=url, session=session)
                items = None if response == None else response['value']
                while items:
                    for item in items:
                        try:
                            # Get the VM status (i.e. Instance View)
                            vm_id =item["id"]
                            pattern = "\/subscriptions\/(?P<subscription_id>[^\/]+)\/resourceGroups\/(?P<vm_resource_group>[^\/]+)\/providers\/Microsoft\.Compute\/virtualMachines\/(?P<vm_name>[^\/]+)$"
                            match = re.search(pattern, vm_id)
                            vm_resource_group = match.group("vm_resource_group")
                            vm_name = match.group("vm_name")
                            instance_view_url = management_base_url + "/subscriptions/%s/resourceGroups/%s/providers/Microsoft.Compute/virtualMachines/%s/instanceView?api-version=%s" % (subscription_id, vm_resource_group, vm_name, vm_instance_view_api_version)
                            vm_instance_view = azutils.get_item_session(helper=helper, session=session, url=instance_view_url)
                        
                            event = helper.new_event(
                                host=vm_name,
                                data=json.dumps(vm_instance_view),
                                source=event_source.lower(),
                                index=helper.get_output_index(),
                                sourcetype=vm_instance_view_sourcetype)
                            ew.write_event(event)
                        
                        except Exception as e:
                            helper.log_debug("_Splunk_ input_name=%s Could not get instance view for VM. Detail %s" % (input_name, str(e)))
                            pass
    
                        event = helper.new_event(
                            data=json.dumps(item),
                            source=event_source.lower(),
                            index=helper.get_output_index(),
                            sourcetype=vm_sourcetype)
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
        checkbox_fields.append("collect_virtual_machine_data")
        checkbox_fields.append("collect_managed_disk_data")
        checkbox_fields.append("collect_image_data")
        checkbox_fields.append("collect_snapshot_data")
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
    exitcode = ModInputazure_comp().run(sys.argv)
    sys.exit(exitcode)
