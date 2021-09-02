
# encoding = utf-8

import os
import sys
import time
import datetime
import json
import re
import ta_azure_utils.utils as azutil
import ta_azure_utils.auth as azauth

def validate_input(helper, definition):
    pass

def collect_events(helper, ew):
    global_account = helper.get_arg("azure_app_account")
    client_id = global_account["username"]
    client_secret = global_account["password"]
    subscription_id = helper.get_arg("subscription_id")
    tenant_id = helper.get_arg("tenant_id")
    
    disk_api_version = "2018-06-01"
    disk_sourcetype = helper.get_arg("managed_disk_sourcetype")
    collect_disks = helper.get_arg("collect_managed_disk_data")
    
    image_api_version = "2018-06-01"
    image_sourcetype = helper.get_arg("image_sourcetype")
    collect_images = helper.get_arg("collect_image_data")
    
    snapshot_api_version = "2018-06-01"
    snapshot_sourcetype = helper.get_arg("snapshot_sourcetype")
    collect_snapshots = helper.get_arg("collect_snapshot_data")
    
    vm_api_version = "2018-06-01"
    vm_instance_view_api_version = "2019-03-01"
    vm_sourcetype = helper.get_arg("virtual_machine_sourcetype")
    vm_instance_view_sourcetype = vm_sourcetype + ":instanceView"
    collect_vms = helper.get_arg("collect_virtual_machine_data")
    
    environment = helper.get_arg("environment")
    if(environment == "gov"):
        management_base_url = "https://management.usgovcloudapi.net"
    else:
        management_base_url = "https://management.azure.com"
    
    access_token = azauth.get_mgmt_access_token(client_id, client_secret, tenant_id, environment, helper)
    
    if(access_token):
        
        if(collect_disks):
            helper.log_debug("_Splunk_ Collecting managed disk data. sourcetype='%s'" % disk_sourcetype)
            url = management_base_url + "/subscriptions/%s/providers/Microsoft.Compute/disks?api-version=%s" % (subscription_id, disk_api_version)
            disks = azutil.get_items(helper, access_token, url)
            for disk in disks:
                event = helper.new_event(
                    data=json.dumps(disk),
                    source=helper.get_input_type(), 
                    index=helper.get_output_index(),
                    sourcetype=disk_sourcetype)
                ew.write_event(event)
                
        if(collect_images):
            helper.log_debug("_Splunk_ Collecting image data. sourcetype='%s'" % image_sourcetype)
            url = management_base_url + "/subscriptions/%s/providers/Microsoft.Compute/images?api-version=%s" % (subscription_id, image_api_version)
            images = azutil.get_items(helper, access_token, url)
            for image in images:
                event = helper.new_event(
                    data=json.dumps(image),
                    source=helper.get_input_type(), 
                    index=helper.get_output_index(),
                    sourcetype=image_sourcetype)
                ew.write_event(event)
                
        if(collect_snapshots):
            helper.log_debug("_Splunk_ Collecting snapshot data. sourcetype='%s'" % snapshot_sourcetype)
            url = management_base_url + "/subscriptions/%s/providers/Microsoft.Compute/snapshots?api-version=%s" % (subscription_id, snapshot_api_version)
            snapshots = azutil.get_items(helper, access_token, url)
            for snapshot in snapshots:
                event = helper.new_event(
                    data=json.dumps(snapshot),
                    source=helper.get_input_type(), 
                    index=helper.get_output_index(),
                    sourcetype=snapshot_sourcetype)
                ew.write_event(event)
                
        if(collect_vms):
            helper.log_debug("_Splunk_ Collecting virtual machine data. sourcetype='%s'" % vm_sourcetype)
            url = management_base_url + "/subscriptions/%s/providers/Microsoft.Compute/virtualMachines?api-version=%s" % (subscription_id, disk_api_version)
            vms = azutil.get_items(helper, access_token, url)
            for vm in vms:
                try:
                    # Get the VM status (i.e. Instance View)
                    vm_id = vm["id"]
                    pattern = "\/subscriptions\/(?P<subscription_id>[^\/]+)\/resourceGroups\/(?P<vm_resource_group>[^\/]+)\/providers\/Microsoft\.Compute\/virtualMachines\/(?P<vm_name>[^\/]+)$"
                    match = re.search(pattern, vm_id)
                    vm_resource_group = match.group("vm_resource_group")
                    vm_name = match.group("vm_name")
                    instance_view_url = "https://management.azure.com/subscriptions/%s/resourceGroups/%s/providers/Microsoft.Compute/virtualMachines/%s/instanceView?api-version=%s" % (subscription_id, vm_resource_group, vm_name, vm_instance_view_api_version)
                    vm_instance_view = azutil.get_item(helper, access_token, instance_view_url)
                    
                    event = helper.new_event(
                        host=vm_name,
                        data=json.dumps(vm_instance_view),
                        source=helper.get_input_type(), 
                        index=helper.get_output_index(),
                        sourcetype=vm_instance_view_sourcetype)
                    ew.write_event(event)
                    
                except Exception as e:
                    helper.log_debug("_Splunk_ Could not regex extraction for vm. Detail %s" % str(e))
                    pass

                event = helper.new_event(
                    data=json.dumps(vm),
                    source=helper.get_input_type(), 
                    index=helper.get_output_index(),
                    sourcetype=vm_sourcetype)
                ew.write_event(event)
                
    else:
        raise RuntimeError("Unable to obtain access token. Please check the Client ID, Client Secret, and Tenant ID")
        