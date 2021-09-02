
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
    
    start_date = definition.parameters.get('start_date')
    if (start_date not in ['',None]):
        try:
            d = dateutil.parser.parse(start_date)
        except Exception as e:
            helper.log_error("_Splunk_ Invalid date format specified for 'Start Date': %s" % start_date)
            raise ValueError("Invalid date format specified for 'Start Date': %s" % start_date)
        # Make sure the date entered is less than 30 days in the past.
        # Otherwise, the reporting API will throw an error
        if d < (datetime.datetime.now() - datetime.timedelta(days=30)):
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
            # If there was no start date specified, default to 1 day ago
            return (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

def collect_events(helper, ew):
    global_account = helper.get_arg("azure_app_account")
    client_id = global_account["username"]
    client_secret = global_account["password"]
    tenant_id = helper.get_arg("tenant_id")
    check_point_key = "aad_risk_detection_last_date_%s" % helper.get_input_stanza_names()
    event_source = "tenant_id:%s" % tenant_id
    source_type = helper.get_arg("risk_detection_sourcetype")
    
    environment = helper.get_arg("environment")
    if(environment == "gov"):
        graph_base_url = "https://graph.microsoft.us"
    else:
        graph_base_url = "https://graph.microsoft.com"
        
    query_date = get_start_date(helper, check_point_key)
    access_token = azauth.get_graph_access_token(client_id, client_secret, tenant_id, environment, helper)
    
    if(access_token):
        url = graph_base_url + "/beta/riskDetections?$orderby=lastUpdatedDateTime&$filter=lastUpdatedDateTime+gt+%s" % query_date
        helper.log_debug("_Splunk_ Risk Detection URL used: %s" % url)
        max_DateTime = query_date

        risk_detection_response = azutils.get_items_batch(helper, access_token, url)
        risk_detections = risk_detection_response['value'] or None

        while risk_detections:
            for risk_detection in risk_detections:
        
                # Keep track of the largest signinDateTime seen during this query.
                this_detectionDateTime = risk_detection["lastUpdatedDateTime"]
        
                if(this_detectionDateTime > max_DateTime):
                    max_DateTime = this_detectionDateTime
        
                event = helper.new_event(
                    data=json.dumps(risk_detection),
                    source=event_source, 
                    index=helper.get_output_index(),
                    sourcetype=source_type)
                ew.write_event(event)

            sys.stdout.flush()
            risk_detections = None
            
            # Check point the largest signinDateTime seen during the query
            helper.save_check_point(check_point_key, max_DateTime)

            if '@odata.nextLink' in risk_detection_response:
                nextLink = risk_detection_response['@odata.nextLink']
                helper.log_debug("_Splunk_ AAD risk detections nextLink URL (@odata.nextLink): %s" % nextLink)

                # This should never happen, but just in case...
                if not azutils.is_https(nextLink):
                    raise ValueError("nextLink scheme is not HTTPS. nextLink URL: %s" % nextLink)

                risk_detection_response = azutils.get_items_batch(helper, access_token, nextLink)
                risk_detections = risk_detection_response['value'] or None
    else:
        helper.log_error("_Splunk_ Unable to obtain access token")