
# encoding = utf-8

import os
import sys
import time
import datetime
import requests
import json
import ta_azure_utils.auth as azauth
import ta_azure_utils.resource_graph as az_resource_graph
import ta_azure_utils.metrics as azmetrics

def validate_input(helper, definition):
    number_of_threads = definition.parameters.get('number_of_threads')
    try:
        int(number_of_threads)
    except ValueError:
        raise ValueError("'Number of Threads' should be an integer without commas.")
    
    n = int(number_of_threads)
    if not 1 <= n <= 25:
        raise ValueError("'Number of Threads' should be a positive integer between 1 and 25.")

def collect_events(helper, ew):
    global_account = helper.get_arg("azure_app_account")
    client_id = global_account["username"]
    client_secret = global_account["password"]
    tenant_id = helper.get_arg("tenant_id")
    subscription_id = helper.get_arg("subscription_id")
    source_type = helper.get_arg("source_type")
    metric_statistics = helper.get_arg("metric_statistics")
    preferred_time_aggregation = helper.get_arg("preferred_time_aggregation")
    metric_namespaces = (",".join("'" + namespace.lower().strip() + "'" for namespace in helper.get_arg("namespaces").split(',')))
    
    check_point_key = "metrics_last_date_%s" % helper.get_input_stanza_names()
    
    environment = helper.get_arg("environment")
    if(environment == "gov"):
        management_base_url = "https://management.usgovcloudapi.net"
    else:
        management_base_url = "https://management.azure.com"
    
    access_token = azauth.get_mgmt_access_token(client_id, client_secret, tenant_id, environment, helper)
    
    # Get requested resources based on namespaces (type)
    query = "where type in (%s) | project id, type" % metric_namespaces
    resources = az_resource_graph.get_resources_by_query(helper, access_token, query, subscription_id.split(","), environment, resources=[])

    resources_to_query = []
    for resource in resources:
        resource_obj = {}
        resource_obj["resource_id"] = resource[0]
        resource_obj["resource_type"] = resource[1]
        resources_to_query.append(resource_obj)
    
    # Finally, let's get the metrics for all these resources
    azmetrics.index_metrics_for_resources(helper, ew, access_token, environment, preferred_time_aggregation, metric_statistics, resources_to_query)
    
    # Update the check point with the current date/time
    now = datetime.datetime.utcnow()
    serialized = {'year': now.year,
        'month': now.month,
        'day': now.day,
        'hour': now.hour,
        'minute': now.minute,
        'second': now.second,
        'microsecond': now.microsecond
    }

    helper.save_check_point(check_point_key, serialized)