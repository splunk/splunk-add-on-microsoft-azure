
# encoding = utf-8

import os
import sys
import time
import datetime
import requests
import json
import dateutil.parser
import ta_azure_utils.auth as azauth
import ta_azure_utils.utils as azutils

def validate_input(helper, definition):
    try:
        int(definition.parameters.get('query_window_size'))
    except ValueError:
        raise ValueError("'Query Limit' should be an integer without commas.")
    start_date = definition.parameters.get('start_date', None)
    if start_date is not None:
        try:
            d = dateutil.parser.parse(start_date)
        except Exception as e:
            helper.log_error("_Splunk_ Invalid date format specified for 'Start Date': %s" % start_date)
            raise ValueError("Invalid date format specified for 'Start Date': %s" % start_date)
        # Make sure the date entered is less than 30 days in the past.
        # Otherwise, the reporting API will throw an error
        if d < datetime.datetime.now() - datetime.timedelta(days=30):
            helper.log_error("_Splunk_ 'Start Date' cannot be more than 30 days in the past.: " + start_date)
            raise ValueError("'Start Date' cannot be more than 30 days in the past.")

def get_start_date(helper, check_point_key):
    
    # Try to get a date from the check point first
    d = helper.get_check_point(check_point_key)
    
    # If there was a check point date, retun it.
    if (d not in [None,'']):
        return d
    else:
        # No check point date, so look if a start date was specified as an argument
        start_date = helper.get_arg("start_date")
        if (start_date not in [None,'']):
            d = dateutil.parser.parse(start_date)
            return d.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        else:
            # If there was no start date specified, default to 7 day ago
            return (datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

def collect_events(helper, ew):
    global_account = helper.get_arg("azure_app_account")
    client_id = global_account["username"]
    client_secret = global_account["password"]
    tenant_id = helper.get_arg("tenant_id")
    check_point_key = "aad_audit_last_date_%s" % helper.get_input_stanza_names()
    event_source = "tenant_id:%s" % tenant_id
    query_window_size = int(helper.get_arg("query_window_size"))
    query_backoff_throttle = int(helper.get_arg("query_backoff_throttle"))
    source_type = helper.get_arg("audit_sourcetype")
    query_date = get_start_date(helper, check_point_key)
    endpoint = helper.get_arg("endpoint")
    
    environment = helper.get_arg("environment")
    if(environment == "gov"):
        graph_base_url = "https://graph.microsoft.us"
    else:
        graph_base_url = "https://graph.microsoft.com"
        
    access_token = azauth.get_graph_access_token(client_id, client_secret, tenant_id, environment, helper)
    
    if(access_token):
        if(query_window_size > 0):
            end_date = azutils.get_end_date(helper, query_date, query_window_size)
            url = graph_base_url + "/%s/auditLogs/directoryAudits?$orderby=activityDateTime&$filter=activityDateTime+ge+%s+and+activityDateTime+le+%s" % (endpoint, query_date, end_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
            helper.log_debug("_Splunk_ Query limit specified: %s" % str(query_window_size))
        else:
            time_throttle_unformatted = datetime.datetime.utcnow() - datetime.timedelta(seconds=query_backoff_throttle)
            time_throttle = time_throttle_unformatted.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            url = graph_base_url + "/%s/auditLogs/directoryAudits?$orderby=activityDateTime&$filter=activityDateTime+gt+%s+and+activityDateTime+le+%s" % (endpoint, query_date, time_throttle)
        helper.log_debug("_Splunk_ Audit URL used: %s" % url)
        max_activityDate = query_date

        audit_response = azutils.get_items_batch(helper, access_token, url)
        audit_events = audit_response['value'] or None
        
        while audit_events:
            for activity in audit_events:
            
                # Keep track of the largest activityDate seen during this query.
                this_activityDate = activity["activityDateTime"]
            
                if(this_activityDate > max_activityDate):
                    max_activityDate = this_activityDate
            
                event = helper.new_event(
                        data=json.dumps(activity),
                        source=event_source, 
                        index=helper.get_output_index(),
                        sourcetype=source_type)
                ew.write_event(event)

            sys.stdout.flush()
            audit_events = None
            
            # Check point the largest activityDate seen during the query
            helper.save_check_point(check_point_key, max_activityDate)

            if '@odata.nextLink' in audit_response:
                nextLink = audit_response['@odata.nextLink']
                helper.log_debug("_Splunk_ AAD audit nextLink URL (@odata.nextLink): %s" % nextLink)

                # This should never happen, but just in case...
                if not azutils.is_https(nextLink):
                    raise ValueError("nextLink scheme is not HTTPS. nextLink URL: %s" % nextLink)

                audit_response = azutils.get_items_batch(helper, access_token, nextLink)
                audit_events = audit_response['value'] or None
    else:
        helper.log_error("_Splunk_ Unable to obtain access token")