
# encoding = utf-8

import os
import sys
import time
import datetime
import json
import requests
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
    
    environment = helper.get_arg("environment")
    if(environment == "gov"):
        management_base_url = "https://management.usgovcloudapi.net"
    else:
        management_base_url = "https://management.azure.com"
    
    alert_api_version = "2019-01-01"
    alert_sourcetype = helper.get_arg("security_alert_sourcetype")
    collect_alerts = helper.get_arg("collect_security_center_alerts")
    alert_check_point_key = "asc_alert_last_date_%s" % helper.get_input_stanza_names()
    alert_check_point = helper.get_check_point(alert_check_point_key)
    
    task_api_version = "2015-06-01-preview"
    task_sourcetype = helper.get_arg("security_task_sourcetype")
    collect_tasks = helper.get_arg("collect_security_center_tasks")
    task_check_point_key = "asc_task_last_date_%s" % helper.get_input_stanza_names()
    task_check_point = helper.get_check_point(task_check_point_key)
    
    access_token = azauth.get_mgmt_access_token(client_id, client_secret, tenant_id, environment, helper)
    
    if(access_token):
        
        if(collect_alerts):
            helper.log_debug("_Splunk_ Collecting security alert data. sourcetype='%s'" % alert_sourcetype)
            if alert_check_point in [None,'']:
                helper.log_debug("_Splunk_ No security center alert data checkpoint. Collecting all current alerts.")
                url = management_base_url + "/subscriptions/%s/providers/Microsoft.Security/alerts?api-version=%s" % (subscription_id, alert_api_version)
                alert_check_point = ""
            else:
                helper.log_debug("_Splunk_ Found security center alert data checkpoint: %s. Collecting events after this detected date/time" % alert_check_point)
                url = management_base_url + "/subscriptions/%s/providers/Microsoft.Security/alerts?api-version=%s&$filter=Properties/DetectedTimeUtc gt %s" % (subscription_id, alert_api_version, alert_check_point)

            alerts = azutil.get_items(helper, access_token, url, items=[])
            max_asc_alert_date = alert_check_point
            
            for alert in alerts:
                
                # Keep track of the largest detected date/time
                this_detectedTime = alert["properties"]["detectedTimeUtc"]
                if (this_detectedTime > max_asc_alert_date):
                    max_asc_alert_date = this_detectedTime
                    
                event = helper.new_event(
                    data=json.dumps(alert),
                    source="%s:%s" % (helper.get_input_type(), tenant_id), 
                    index=helper.get_output_index(),
                    sourcetype=alert_sourcetype)
                ew.write_event(event)
                
            helper.save_check_point(alert_check_point_key, max_asc_alert_date)
                
        if(collect_tasks):
            helper.log_debug("_Splunk_ Collecting security task data. sourcetype='%s'" % task_sourcetype)
            if task_check_point in [None,'']:
                helper.log_debug("_Splunk_ No security center task data checkpoint. Collecting all current tasks.")
                url = management_base_url + "/subscriptions/%s/providers/Microsoft.Security/tasks?api-version=%s" % (subscription_id, task_api_version)
                task_check_point = ''
            else:
                helper.log_debug("_Splunk_ Found security center task data checkpoint: %s. Collecting events after this changed date/time" % task_check_point)
                url = management_base_url + "/subscriptions/%s/providers/Microsoft.Security/tasks?api-version=%s&$filter=Properties/LastStateChangeTimeUtc gt %s" % (subscription_id, task_api_version, task_check_point)
            
            tasks = azutil.get_items(helper, access_token, url, items=[])
            max_asc_task_date = task_check_point
            
            for task in tasks:
                
                # Keep track of the largest detected date/time
                this_changedTime = task["properties"]["lastStateChangeTimeUtc"]
                if (this_changedTime > max_asc_task_date):
                    max_asc_task_date = this_changedTime
                    
                event = helper.new_event(
                    data=json.dumps(task),
                    source="%s:%s" % (helper.get_input_type(), tenant_id),
                    index=helper.get_output_index(),
                    sourcetype=task_sourcetype)
                ew.write_event(event)
                
            helper.save_check_point(task_check_point_key, max_asc_task_date)
    else:
        raise RuntimeError("Unable to obtain access token. Please check the Client ID, Client Secret, and Tenant ID")