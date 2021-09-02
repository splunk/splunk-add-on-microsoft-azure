
# encoding = utf-8

import os
import sys
import time
import datetime
import json
import requests
from ta_azure_utils.auth import get_mgmt_access_token
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
                