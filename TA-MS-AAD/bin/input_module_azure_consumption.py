
# encoding = utf-8

import os
import sys
import time
import datetime
import json
import requests
import dateutil.parser
from ta_azure_utils.auth import get_mgmt_access_token
from ta_azure_utils.utils import get_items

def validate_input(helper, definition):
    try:
        int(definition.parameters.get('query_days'))
    except ValueError:
        raise ValueError("'Max days to query' should be an integer without commas.")
    
    start_date = definition.parameters.get('start_date')
    if (start_date not in ['',None]):
        try:
            d = dateutil.parser.parse(start_date)
        except Exception as e:
            helper.log_error("_Splunk_ Invalid date format specified for 'Start Date': %s" % start_date)
            raise ValueError("Invalid date format specified for 'Start Date': %s" % start_date)

def get_start_date(helper, check_point_key):
    
    # Try to get a date from the check point first
    d = helper.get_check_point(check_point_key)
    
    # If there was a check point date, retun it.
    if (d not in [None,'']):
        helper.log_debug("_Splunk_ Getting start date. Checkpoint date found: %s" % d)
        return d
    else:
        # No check point date, so look if a start date was specified as an argument
        start_date = helper.get_arg("start_date")
        if (start_date not in [None,'']):
            d = dateutil.parser.parse(start_date)
            helper.log_debug("_Splunk_ Getting start date. Start date in stanza: %s" % start_date)
            return d.strftime('%Y-%m-%d')
        else:
            # If there was no start date specified, default to 90 day ago
            d = (datetime.datetime.now() - datetime.timedelta(days=90)).strftime('%Y-%m-%d')
            helper.log_debug("_Splunk_ Getting start date. Calculated start date 90 days in the past: %s" % str(d))
            return d

def get_end_date(helper, query_days, start_date, max_days_ago):
    dt_start = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    dt_end = dt_start + datetime.timedelta(days=query_days)
    dt_days_ago = datetime.date.today() - datetime.timedelta(days=max_days_ago)
    helper.log_debug("_Splunk_ Getting end date. start: %s, max days: %s, end: %s" % (dt_start.strftime('%Y-%m-%d'), str(max_days_ago), dt_end.strftime('%Y-%m-%d')))
    
    # Adjust the end date if we went too far.
    if dt_end > dt_days_ago:
        d = dt_end
        dt_end = dt_days_ago
        helper.log_debug("_Splunk_ Adjusting end date. Old value: %s, new value: %s" % (d.strftime('%Y-%m-%d'), dt_end.strftime('%Y-%m-%d')))
    
    # If the start date is greater than the end date, return None
    if dt_start >= dt_end:
        helper.log_debug("_Splunk_ Start date '%s' is greater than or equal to the end date '%s'. Returning 'None'" % (dt_start.strftime('%Y-%m-%d'), dt_end.strftime('%Y-%m-%d')))
        return None
    else:
        helper.log_debug("_Splunk_ Returning end date '%s'." % dt_end.strftime('%Y-%m-%d'))
        return dt_end.strftime('%Y-%m-%d')

def collect_events(helper, ew):

    global_account = helper.get_arg("azure_app_account")
    client_id = global_account["username"]
    client_secret = global_account["password"]
    subscription_id = helper.get_arg("subscription_id")
    billing_sourcetype = helper.get_arg("billing_sourcetype")
    billing_period_sourcetype = helper.get_arg("billing_period_sourcetype")
    tenant_id = helper.get_arg("tenant_id")
    query_days = int(helper.get_arg("query_days"))
    
    environment = helper.get_arg("environment")
    if(environment == "gov"):
        management_base_url = "https://management.usgovcloudapi.net"
    else:
        management_base_url = "https://management.azure.com"
    
    billing_check_point_key = "billing_last_date_%s" % helper.get_input_stanza_names()
    api_version = "2019-10-01"
    
    start_date = get_start_date(helper, billing_check_point_key)
    end_date = get_end_date(helper, query_days, start_date, max_days_ago=2)
    
    access_token = get_mgmt_access_token(client_id, client_secret, tenant_id, environment, helper)
    
    if(access_token) and (end_date is not None):

        header = {'Authorization':'Bearer ' + access_token}
        usage_url = management_base_url + "/subscriptions/%s/providers/Microsoft.Consumption/usageDetails?$orderby=properties/usageEnd&$expand=properties/meterDetails,properties/additionalProperties&$filter=properties/usageStart+ge+'%s'+AND properties/usageEnd+le+'%s'&api-version=%s" % (subscription_id, start_date, end_date, api_version)
        helper.log_debug("_Splunk_ Getting usage events from URL: %s" % usage_url)
        
        usage_data = get_items(helper, access_token, usage_url, [])

        for value in usage_data:
            event = helper.new_event(
                data=json.dumps(value),
                source=helper.get_input_type(),
                index=helper.get_output_index(),
                sourcetype=billing_sourcetype)
            ew.write_event(event)

        helper.save_check_point(billing_check_point_key, end_date)
        helper.log_debug("_Splunk_ Saving check point for usage data. end_date: %s" % str(end_date))