# encoding = utf-8
'''

Copyright 2020 Splunk Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

'''
import os
import sys
import time
import datetime
import json
import import_declare_test
from splunklib import modularinput as smi
import traceback
import requests
from splunklib import modularinput as smi
from solnlib import conf_manager
from solnlib import log
from solnlib.modular_input import checkpointer
from splunktaucclib.modinput_wrapper import base_modinput  as base_mi 
import dateutil.parser
import requests
import ta_azure_utils.auth as azauth
import ta_azure_utils.utils as azutils

bin_dir = os.path.basename(__file__)

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
            # If there was no start date specified, default to 7 days ago
            return (datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

class ModInputms_graph_security(base_mi.BaseModInput):

    def __init__(self):
        use_single_instance = False
        super(ModInputms_graph_security, self).__init__("ta_ms_aad", "ms_graph_security", use_single_instance)
        self.global_checkbox_fields = None

    def get_scheme(self):
        """overloaded splunklib modularinput method"""
        scheme = super(ModInputms_graph_security, self).get_scheme()
        scheme.title = ("Azure Active Directory Sign-ins")
        scheme.description = ("Go to the add-on\'s configuration UI and configure modular inputs under the Inputs menu.")
        scheme.use_external_validation = True
        scheme.streaming_mode_xml = True

        scheme.add_argument(smi.Argument("name", title="Name",
                                         description="",
                                         required_on_create=True))
        scheme.add_argument(smi.Argument("azure_app_account", title="Azure App Account",
                                         description="",
                                         required_on_create=True,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("tenant_id", title="Tenant ID",
                                         description="a.k.a. Directory ID",
                                         required_on_create=True,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("filter", title="Filter (optional)",
                                         description="",
                                         required_on_create=False,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("environment", title="Environment",
                                         description="",
                                         required_on_create=True,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("graph_security_api_sourcetype", title="Sourcetype",
                                         description="",
                                         required_on_create=True,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("start_date", title="Start Date",
                                         description="The date/time to start collecting data.  If no value is give, the input will start getting data 7 days in the past.",
                                         required_on_create=False,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("endpoint", title="Endpoint",
                                         description="",
                                         required_on_create=True,
                                         required_on_edit=False))
        return scheme

    def get_app_name(self):
        return "TA-MS-AAD"

    def validate_input(helper, definition):

        filter = definition.parameters.get('filter')
        if(filter and (not filter.startswith("$filter="))):
            raise ValueError("Filter must start with $filter=")
        
        start_date = definition.parameters.get('start_date')
        if (start_date not in ['',None]):
            try:
                d = dateutil.parser.parse(start_date)
            except Exception as e:
                helper.log_error("_Splunk_ Invalid date format specified for 'Start Date': %s" % start_date)
                raise ValueError("Invalid date format specified for 'Start Date': %s" % start_date)
            # Make sure the date entered is less than 30 days in the past.
            # Otherwise, the API will throw an error
            if d.replace(tzinfo=None) < (datetime.datetime.now() - datetime.timedelta(days=30)):
                helper.log_error("_Splunk_ 'Start Date' cannot be more than 30 days in the past.: " + start_date)
                raise ValueError("'Start Date' cannot be more than 30 days in the past.")
    

    def collect_events(helper, ew):
        global_account = helper.get_arg("azure_app_account")
        client_id = global_account["username"]
        client_secret = global_account["password"]
        tenant_id = helper.get_arg("tenant_id")
        check_point_key = "graph_security_api_last_date_%s" % helper.get_input_stanza_names()
        event_source = "%s:tenant_id:%s" % (helper.input_type, tenant_id)
        source_type = helper.get_arg("graph_security_api_sourcetype")
        input_filter = helper.get_arg("filter")
        endpoint = helper.get_arg("endpoint")
        input_name = helper.get_input_stanza_names()
        
        environment = helper.get_arg("environment")
        graph_base_url = azutils.get_environment_graph(environment)
            
        query_date = get_start_date(helper, check_point_key)
        session = azauth.get_graph_session(client_id, client_secret, tenant_id, environment, helper)
        
        if(session):
            
            url = graph_base_url + "/%s/security/alerts?$orderby=lastModifiedDateTime&$filter=lastModifiedDateTime+gt+%s" % (endpoint, query_date)

            # Insert the user filter if provided
            if(input_filter):
                if(not input_filter.startswith("$filter=")):
                    helper.log_error("Invalid filter: %s" % filter)
                else:
                    url = url.replace("$filter=", "%s+and+" % input_filter)

            helper.log_debug("_Splunk_ input_name=%s Security Graph URL used: %s" % (input_name, url))
            max_dateTime = query_date
    
            response = azutils.get_items_batch_session(helper=helper, url=url, session=session)
            items = None if response == None else response['value']
    
            while items:
                for item in items:
            
                    # Keep track of the largest datetime seen during this query.
                    this_dateTime = item["lastModifiedDateTime"]
            
                    if(this_dateTime > max_dateTime):
                        max_dateTime = this_dateTime
            
                    event = helper.new_event(
                        data=json.dumps(item),
                        source=event_source.lower(),
                        index=helper.get_output_index(),
                        sourcetype=source_type)
                    ew.write_event(event)
    
                sys.stdout.flush()
                
                # Check point the largest dateTime seen during the query
                helper.save_check_point(check_point_key, max_dateTime)
                response = azutils.handle_nextLink(helper=helper, response=response, session=session)
                items = None if response == None else response['value']
        else:
            helper.log_error("_Splunk_ Unable to obtain access token")

    def get_account_fields(self):
        account_fields = []
        account_fields.append("azure_app_account")
        return account_fields

    def get_checkbox_fields(self):
        checkbox_fields = []
        return checkbox_fields

    def get_global_checkbox_fields(self):
        if self.global_checkbox_fields is None:
            checkbox_name_file = os.path.join(bin_dir, 'global_checkbox_param.json')
            try:
                if os.path.isfile(checkbox_name_file):
                    with open(checkbox_name_file, 'r') as fp:
                        self.global_checkbox_fields = json.load(fp)
                else:
                    self.global_checkbox_fields = []
            except Exception as e:
                self.log_error('Get exception when loading global checkbox parameter names. ' + str(e))
                self.global_checkbox_fields = []
        return self.global_checkbox_fields

if __name__ == "__main__":
    exitcode = ModInputms_graph_security().run(sys.argv)
    sys.exit(exitcode)
