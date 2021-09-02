
# encoding = utf-8

import os
import sys
import time
import datetime
import json
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
    
    vnet_api_version = "2018-08-01"
    vnet_sourcetype = helper.get_arg("virtual_network_sourcetype")
    collect_vnets = helper.get_arg("collect_virtual_network_data")
    
    nic_api_version = "2018-08-01"
    nic_sourcetype = helper.get_arg("network_interface_sourcetype")
    collect_nics = helper.get_arg("collect_network_interface_data")
    
    nsg_api_version = "2018-08-01"
    nsg_sourcetype = helper.get_arg("security_group_sourcetype")
    collect_nsgs = helper.get_arg("collect_security_group_data")
    
    ip_api_version = "2018-08-01"
    ip_sourcetype = helper.get_arg("public_ip_sourcetype")
    collect_ips = helper.get_arg("collect_public_ip_address_data")
    
    environment = helper.get_arg("environment")
    if(environment == "gov"):
        management_base_url = "https://management.usgovcloudapi.net"
    else:
        management_base_url = "https://management.azure.com"
    
    access_token = azauth.get_mgmt_access_token(client_id, client_secret, tenant_id, environment, helper)
    
    if(access_token):
        
        if(collect_vnets):
            helper.log_debug("_Splunk_ Collecting virtual network data. sourcetype='%s'" % vnet_sourcetype)
            url = management_base_url + "/subscriptions/%s/providers/Microsoft.Network/virtualNetworks?api-version=%s" % (subscription_id, vnet_api_version)
            vnets = azutil.get_items(helper, access_token, url)
            for vnet in vnets:
                event = helper.new_event(
                    data=json.dumps(vnet),
                    source=helper.get_input_type(), 
                    index=helper.get_output_index(),
                    sourcetype=vnet_sourcetype)
                ew.write_event(event)
                
        if(collect_nics):
            helper.log_debug("_Splunk_ Collecting nic data. sourcetype='%s'" % nic_sourcetype)
            url = management_base_url + "/subscriptions/%s/providers/Microsoft.Network/networkInterfaces?api-version=%s" % (subscription_id, nic_api_version)
            nics = azutil.get_items(helper, access_token, url)
            for nic in nics:
                event = helper.new_event(
                    data=json.dumps(nic),
                    source=helper.get_input_type(), 
                    index=helper.get_output_index(),
                    sourcetype=nic_sourcetype)
                ew.write_event(event)
                
        if(collect_nsgs):
            helper.log_debug("_Splunk_ Collecting nsg data. sourcetype='%s'" % nsg_sourcetype)
            url = management_base_url + "/subscriptions/%s/providers/Microsoft.Network/networkSecurityGroups?api-version=%s" % (subscription_id, nsg_api_version)
            nsgs = azutil.get_items(helper, access_token, url)
            for nsg in nsgs:
                event = helper.new_event(
                    data=json.dumps(nsg),
                    source=helper.get_input_type(), 
                    index=helper.get_output_index(),
                    sourcetype=nsg_sourcetype)
                ew.write_event(event)
                
        if(collect_ips):
            helper.log_debug("_Splunk_ Collecting IP address data. sourcetype='%s'" % ip_sourcetype)
            url = management_base_url + "/subscriptions/%s/providers/Microsoft.Network/publicIPAddresses?api-version=%s" % (subscription_id, ip_api_version)
            ips = azutil.get_items(helper, access_token, url)
            for ip in ips:
                event = helper.new_event(
                    data=json.dumps(ip),
                    source=helper.get_input_type(), 
                    index=helper.get_output_index(),
                    sourcetype=ip_sourcetype)
                ew.write_event(event)
    else:
        raise RuntimeError("Unable to obtain access token. Please check the Client ID, Client Secret, and Tenant ID")