
# encoding = utf-8

import os
import sys
import time
import datetime
import json
import requests
import re
from ta_azure_utils.auth import get_mgmt_access_token
from ta_azure_utils.utils import get_items
from ta_azure_utils.resource_groups import get_resource_groups_by_location
from ta_azure_utils.topology import get_topology_by_rg

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
                                