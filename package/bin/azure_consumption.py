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
from ta_azure_utils.auth import get_mgmt_access_token
from ta_azure_utils.utils import get_items
import dateutil.parser
import requests

bin_dir = os.path.basename(__file__)

def get_start_date(helper, check_point_key):
    input_name = helper.get_input_stanza_names()
    
    # Try to get a date from the check point first
    d = helper.get_check_point(check_point_key)
    
    # If there was a check point date, retun it.
    if (d not in [None,'']):
        helper.log_debug("_Splunk_ input_name=%s Getting start date. Checkpoint date found: %s" % (input_name, d))
        return d
    else:
        # No check point date, so look if a start date was specified as an argument
        start_date = helper.get_arg("start_date")
        if (start_date not in [None,'']):
            d = dateutil.parser.parse(start_date)
            helper.log_debug("_Splunk_ input_name=%s Getting start date. input_name=%s Start date in stanza: %s" % (input_name, input_name, start_date))
            return d.strftime('%Y-%m-%d')
        else:
            # If there was no start date specified, default to 90 day ago
            d = (datetime.datetime.now() - datetime.timedelta(days=90)).strftime('%Y-%m-%d')
            helper.log_debug("_Splunk_ input_name=%s Getting start date. Calculated start date 90 days in the past: %s" % (input_name, str(d)))
            return d

def get_end_date(helper, query_days, start_date, max_days_ago):
    input_name = helper.get_input_stanza_names()
    dt_start = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    dt_end = dt_start + datetime.timedelta(days=query_days)
    dt_days_ago = datetime.date.today() - datetime.timedelta(days=max_days_ago)
    helper.log_debug("_Splunk_ input_name=%s Getting end date. start: %s, max days: %s, end: %s" % (input_name, dt_start.strftime('%Y-%m-%d'), str(max_days_ago), dt_end.strftime('%Y-%m-%d')))
    
    # Adjust the end date if we went too far.
    if dt_end > dt_days_ago:
        d = dt_end
        dt_end = dt_days_ago
        helper.log_debug("_Splunk_ input_name=%s Adjusting end date. Old value: %s, new value: %s" % (input_name, d.strftime('%Y-%m-%d'), dt_end.strftime('%Y-%m-%d')))
    
    # If the start date is greater than the end date, return None
    if dt_start >= dt_end:
        helper.log_debug("_Splunk_ input_name=%s Start date '%s' is greater than or equal to the end date '%s'. Returning 'None'" % (input_name, dt_start.strftime('%Y-%m-%d'), dt_end.strftime('%Y-%m-%d')))
        return None
    else:
        helper.log_debug("_Splunk_ input_name=%s Returning end date '%s'." % (input_name, dt_end.strftime('%Y-%m-%d')))
        return dt_end.strftime('%Y-%m-%d')

class ModInputazure_consumption(base_mi.BaseModInput):

    def __init__(self):
        use_single_instance = False
        super(ModInputazure_consumption, self).__init__("ta_ms_aad", "azure_consumption", use_single_instance)
        self.global_checkbox_fields = None

    def get_scheme(self):
        """overloaded splunklib modularinput method"""
        scheme = super(ModInputazure_consumption, self).get_scheme()
        scheme.title = ("Azure Billing and Consumption")
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
                                         description="",
                                         required_on_create=True,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("subscription_id", title="Subscription ID",
                                         description="",
                                         required_on_create=True,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("environment", title="Environment",
                                         description="",
                                         required_on_create=True,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("billing_sourcetype", title="Billing Sourcetype",
                                         description="",
                                         required_on_create=True,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("query_days", title="Max days to query",
                                         description="Specify the maximum number of days to query each interval.",
                                         required_on_create=True,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("start_date", title="Start Date (optional)",
                                         description="Defaults to 90 days in the past if empty.",
                                         required_on_create=False,
                                         required_on_edit=False))
        return scheme

    def get_app_name(self):
        return "TA-MS-AAD"

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
    

    def collect_events(helper, ew):
        global_account = helper.get_arg("azure_app_account")
        client_id = global_account["username"]
        client_secret = global_account["password"]
        subscription_id = helper.get_arg("subscription_id")
        billing_sourcetype = helper.get_arg("billing_sourcetype")
        billing_period_sourcetype = helper.get_arg("billing_period_sourcetype")
        tenant_id = helper.get_arg("tenant_id")
        query_days = int(helper.get_arg("query_days"))
        input_name = helper.get_input_stanza_names()
        
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
            helper.log_debug("_Splunk_ input_name=%s Getting usage events from URL: %s" % (input_name, usage_url))
            
            usage_data = get_items(helper, access_token, usage_url, [])
    
            for value in usage_data:
                event = helper.new_event(
                    data=json.dumps(value),
                    source=helper.get_input_type(),
                    index=helper.get_output_index(),
                    sourcetype=billing_sourcetype)
                ew.write_event(event)
    
            helper.save_check_point(billing_check_point_key, end_date)
            helper.log_debug("_Splunk_ input_name=%s Saving check point for usage data. end_date: %s" % (input_name, str(end_date)))

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
    exitcode = ModInputazure_consumption().run(sys.argv)
    sys.exit(exitcode)
