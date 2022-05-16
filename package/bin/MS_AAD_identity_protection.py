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
import re
import ta_azure_utils.auth as azauth
import ta_azure_utils.utils as azutils

bin_dir = os.path.basename(__file__)

class ModInputMS_AAD_identity_protection(base_mi.BaseModInput):

    def __init__(self):
        use_single_instance = False
        super(ModInputMS_AAD_identity_protection, self).__init__("ta_ms_aad", "MS_AAD_identity_protection", use_single_instance)
        self.global_checkbox_fields = None

    def get_scheme(self):
        """overloaded splunklib modularinput method"""
        scheme = super(ModInputMS_AAD_identity_protection, self).get_scheme()
        scheme.title = ("Azure Active Directory Identity Protection")
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
        scheme.add_argument(smi.Argument("environment", title="Environment",
                                         description="",
                                         required_on_create=True,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("collect_risk_detection_data", title="Collect Risk Detection Data",
                                         description="Suspicious actions related to user accounts in the directory.",
                                         required_on_create=False,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("risk_detection_sourcetype", title="Risk Detection Sourcetype",
                                         description="",
                                         required_on_create=True,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("collect_risky_user_data", title="Collect Risky User Data",
                                         description="Represents Azure AD users who are at risk.",
                                         required_on_create=False,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("risky_user_sourcetype", title="Risky User Sourcetype",
                                         description="",
                                         required_on_create=True,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("endpoint", title="Endpoint",
                                         description="",
                                         required_on_create=True,
                                         required_on_edit=False))
        return scheme

    def get_app_name(self):
        return "TA-MS-AAD"

    def validate_input(helper, definition):
        pass
    

    def collect_events(helper, ew):
        global_account = helper.get_arg("azure_app_account")
        client_id = global_account["username"]
        client_secret = global_account["password"]
        subscription_id = helper.get_arg("subscription_id")
        tenant_id = helper.get_arg("tenant_id")
        event_source = "%s:tenant_id:%s" % (helper.input_type, tenant_id)
        endpoint = helper.get_arg("endpoint")
        environment = helper.get_arg("environment")
        input_name = helper.get_input_stanza_names()
        
        risk_detection_sourcetype = helper.get_arg("risk_detection_sourcetype")
        collect_risk_detection_data = helper.get_arg("collect_risk_detection_data")
        risk_detection_check_point_key = "risk_detection_last_date_%s" % helper.get_input_stanza_names()
        risk_detection_check_point = helper.get_check_point(risk_detection_check_point_key)
        
        risky_user_sourcetype = helper.get_arg("risky_user_sourcetype")
        collect_risky_user_data = helper.get_arg("collect_risky_user_data")
        risky_user_check_point_key = "asc_alert_last_date_%s" % helper.get_input_stanza_names()
        risky_user_check_point = helper.get_check_point(risky_user_check_point_key)
        
        graph_base_url = azutils.get_environment_graph(environment)
        
        session = azauth.get_graph_session(client_id, client_secret, tenant_id, environment, helper)
    
        if(session):
            if(collect_risk_detection_data):
                helper.log_debug("_Splunk_ input_name=%s Collecting risk detection data. sourcetype='%s'" % (input_name, risk_detection_sourcetype))
                
                if risk_detection_check_point in [None,'']:
                    helper.log_debug("_Splunk_ input_name=%s No risk detection data checkpoint. Collecting all current events." % input_name)
                    url = graph_base_url + "/%s/identityProtection/riskDetections" % (endpoint)
                    risk_detection_check_point = ""
                else:
                    helper.log_debug("_Splunk_ input_name=%s Found risk detction checkpoint: %s. Collecting events after this detected date/time" % (input_name, risk_detection_check_point))
                    url = graph_base_url + "/%s/identityProtection/riskDetections?$orderby=lastUpdatedDateTime&$filter=lastUpdatedDateTime gt %s" % (endpoint, risk_detection_check_point)
    
                response = azutils.get_items_batch_session(helper=helper, url=url, session=session)
                items = response['value'] or None
                max_risk_detection_date = risk_detection_check_point
                while items:
                    for item in items:
                        
                        # Keep track of the largest detected date/time
                        this_detectedTime = item["lastUpdatedDateTime"]
                        if (this_detectedTime > max_risk_detection_date):
                            max_risk_detection_date = this_detectedTime
                            
                        event = helper.new_event(
                            data=json.dumps(item),
                            source = event_source.lower(),
                            index=helper.get_output_index(),
                            sourcetype=risk_detection_sourcetype)
                        ew.write_event(event)
                        
                    sys.stdout.flush()
                    helper.save_check_point(risk_detection_check_point_key, max_risk_detection_date)
                    items = azutils.handle_nextLink(helper=helper, response=response, session=session)
                    
                    
            if(collect_risky_user_data):
                helper.log_debug("_Splunk_ input_name=%s Collecting risky user. sourcetype='%s'" % (input_name, risky_user_sourcetype))
                
                if risky_user_check_point in [None,'']:
                    helper.log_debug("_Splunk_ input_name=%s No risky user data checkpoint. Collecting all current events." % input_name)
                    url = graph_base_url + "/%s/identityProtection/riskyUsers" % (endpoint)
                    risky_user_check_point = ""
                else:
                    helper.log_debug("_Splunk_ input_name=%s Found risky user checkpoint: %s. Collecting events after this detected date/time" % (input_name, risky_user_check_point))
                    url = graph_base_url + "/%s/identityProtection/riskyUsers?$orderby=riskLastUpdatedDateTime&$filter=riskLastUpdatedDateTime gt %s" % (endpoint, risky_user_check_point)
                
                response = azutils.get_items_batch_session(helper=helper, url=url, session=session)
                items = response['value'] or None
                max_risky_user_date = risky_user_check_point
                while items:
                    for item in items:
                        
                        # Keep track of the largest detected date/time
                        this_detectedTime = item["riskLastUpdatedDateTime"]
                        if (this_detectedTime > max_risky_user_date):
                            max_risky_user_date = this_detectedTime
                            
                        event = helper.new_event(
                            data=json.dumps(item),
                            source=event_source.lower(),
                            index=helper.get_output_index(),
                            sourcetype=risky_user_sourcetype)
                        ew.write_event(event)
                        
                    sys.stdout.flush()
                    helper.save_check_point(risky_user_check_point_key, max_risky_user_date)
                    items = azutils.handle_nextLink(helper=helper, response=response, session=session)
    
        else:
            raise RuntimeError("Unable to obtain access token. Please check the Client ID, Client Secret, and Tenant ID")
            

    def get_account_fields(self):
        account_fields = []
        account_fields.append("azure_app_account")
        return account_fields

    def get_checkbox_fields(self):
        checkbox_fields = []
        checkbox_fields.append("collect_risk_detection_data")
        checkbox_fields.append("collect_risky_user_data")
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
    exitcode = ModInputMS_AAD_identity_protection().run(sys.argv)
    sys.exit(exitcode)
