
# encoding = utf-8

import os
import sys
import time
import datetime
import json
import ta_azure_utils.auth as azauth
import ta_azure_utils.resource_graph as az_resource_graph


def validate_input(helper, definition):
    pass

def collect_events(helper, ew):
    global_account = helper.get_arg("azure_app_account")
    client_id = global_account["username"]
    client_secret = global_account["password"]
    tenant_id = helper.get_arg("tenant_id")
    subscription_id = helper.get_arg("subscription_ids")
    query = helper.get_arg("resource_graph_query")
    source_type = helper.get_arg("source_type")
    environment = helper.get_arg("environment")
    
    access_token = azauth.get_mgmt_access_token(client_id, client_secret, tenant_id, environment, helper)
    
    resources = az_resource_graph.get_json_resources_by_query(helper, access_token, query, subscription_id.split(","), environment, resources=[])
    
    for resource in resources:
        event = helper.new_event(
            data=json.dumps(resource),
            index=helper.get_output_index(),
            sourcetype=source_type)
        ew.write_event(event) 
        