
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
   pass

def collect_events(helper, ew):

    global_account = helper.get_arg("azure_app_account")
    client_id = global_account["username"]
    client_secret = global_account["password"]
    tenant_id = helper.get_arg("tenant_id")
    event_source = "tenant_id:%s" % tenant_id
    source_type = helper.get_arg("user_sourcetype")
    endpoint = helper.get_arg("endpoint")
    
    environment = helper.get_arg("environment")
    if(environment == "gov"):
        graph_base_url = "https://graph.microsoft.us"
    else:
        graph_base_url = "https://graph.microsoft.com"
    
    access_token = azauth.get_graph_access_token(client_id, client_secret, tenant_id, environment, helper)
    
    if(access_token):

        url = graph_base_url + "/%s/users/" % endpoint
        users_response = azutils.get_items_batch(helper, access_token, url)
        users = users_response['value'] or None

        while users:
            for user in users:
                event = helper.new_event(
                        data = json.dumps(user),
                        source = event_source, 
                        index = helper.get_output_index(),
                        sourcetype = source_type)
                ew.write_event(event)

            sys.stdout.flush()
            
            users = None
            
            if '@odata.nextLink' in users_response:
                nextLink = users_response['@odata.nextLink']
                helper.log_debug("_Splunk_ AAD users nextLink URL (@odata.nextLink): %s" % nextLink)

                # This should never happen, but just in case...
                if not azutils.is_https(nextLink):
                    raise ValueError("nextLink scheme is not HTTPS. nextLink URL: %s" % nextLink)

                users_response = azutils.get_items_batch(helper, access_token, nextLink)
                users = users_response['value']

    else:
        helper.log_error("_Splunk_ Unable to obtain access token")
        