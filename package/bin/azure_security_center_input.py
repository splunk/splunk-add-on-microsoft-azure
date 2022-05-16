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
import requests
import ta_azure_utils.auth as azauth
import ta_azure_utils.utils as azutils

bin_dir = os.path.basename(__file__)

class ModInputazure_security_center_input(base_mi.BaseModInput):

    def __init__(self):
        use_single_instance = False
        super(ModInputazure_security_center_input, self).__init__("ta_ms_aad", "azure_security_center_input", use_single_instance)
        self.global_checkbox_fields = None

    def get_scheme(self):
        """overloaded splunklib modularinput method"""
        scheme = super(ModInputazure_security_center_input, self).get_scheme()
        scheme.title = ("Azure Security Center Alerts & Tasks")
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
        scheme.add_argument(smi.Argument("collect_security_center_alerts", title="Collect Security Center Alerts",
                                         description="",
                                         required_on_create=False,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("security_alert_sourcetype", title="Security Alert Sourcetype",
                                         description="",
                                         required_on_create=True,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("collect_security_center_tasks", title="Collect Security Center Tasks",
                                         description="",
                                         required_on_create=False,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("security_task_sourcetype", title="Security Task Sourcetype",
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
        input_name = helper.get_input_stanza_names()
        
        environment = helper.get_arg("environment")
        management_base_url = azutils.get_environment_mgmt(environment)
        
        alert_api_version = "2021-01-01"
        alert_sourcetype = helper.get_arg("security_alert_sourcetype")
        collect_alerts = helper.get_arg("collect_security_center_alerts")
        alert_check_point_key = "asc_alert_last_date_%s" % helper.get_input_stanza_names()
        alert_check_point = helper.get_check_point(alert_check_point_key)
        
        task_api_version = "2015-06-01-preview"
        task_sourcetype = helper.get_arg("security_task_sourcetype")
        collect_tasks = helper.get_arg("collect_security_center_tasks")
        task_check_point_key = "asc_task_last_date_%s" % helper.get_input_stanza_names()
        task_check_point = helper.get_check_point(task_check_point_key)
        
        session = azauth.get_mgmt_session(client_id, client_secret, tenant_id, environment, helper)
        
        if(session):
            
            if(collect_alerts):
                helper.log_debug("_Splunk_ input_name=%s Collecting security alert data. sourcetype='%s'" % (input_name, alert_sourcetype))
                if alert_check_point in [None,'']:
                    helper.log_debug("_Splunk_ input_name=%s No security center alert data checkpoint. Collecting all current alerts." % input_name)
                    url = management_base_url + "/subscriptions/%s/providers/Microsoft.Security/alerts?api-version=%s" % (subscription_id, alert_api_version)
                    alert_check_point = ""
                else:
                    helper.log_debug("_Splunk_ input_name=%s Found security center alert data checkpoint: %s. Collecting events after this detected date/time" % (input_name, alert_check_point))
                    url = management_base_url + "/subscriptions/%s/providers/Microsoft.Security/alerts?api-version=%s&$filter=Properties/DetectedTimeUtc gt %s" % (subscription_id, alert_api_version, alert_check_point)
    
                response = azutils.get_items_batch_session(helper=helper, url=url, session=session)
                items = response['value'] or None
                max_asc_alert_date = alert_check_point
                
                while items:
                    for item in items:
                        # Keep track of the largest detected date/time
                        this_detectedTime = item["properties"]["timeGeneratedUtc"]
                        if (this_detectedTime > max_asc_alert_date):
                            max_asc_alert_date = this_detectedTime
                            
                        event = helper.new_event(
                            data=json.dumps(item),
                            source=event_source.lower(),
                            index=helper.get_output_index(),
                            sourcetype=alert_sourcetype)
                        ew.write_event(event)
    
                    sys.stdout.flush()
                        
                    helper.save_check_point(alert_check_point_key, max_asc_alert_date)
                    items = azutils.handle_nextLink(helper=helper, response=response, session=session)
                    
            if(collect_tasks):
                helper.log_debug("_Splunk_ input_name=%s Collecting security task data. sourcetype='%s'" % (input_name, task_sourcetype))
                if task_check_point in [None,'']:
                    helper.log_debug("_Splunk_ input_name=%s No security center task data checkpoint. Collecting all current tasks." % input_name)
                    url = management_base_url + "/subscriptions/%s/providers/Microsoft.Security/tasks?api-version=%s" % (subscription_id, task_api_version)
                    task_check_point = ''
                else:
                    helper.log_debug("_Splunk_ input_name=%s Found security center task data checkpoint: %s. Collecting events after this changed date/time" % (input_name, task_check_point))
                    url = management_base_url + "/subscriptions/%s/providers/Microsoft.Security/tasks?api-version=%s&$filter=Properties/LastStateChangeTimeUtc gt %s" % (subscription_id, task_api_version, task_check_point)
                
                response = azutils.get_items_batch_session(helper=helper, url=url, session=session)
                items = response['value'] or None
                max_asc_task_date = task_check_point
                
                while items:
                    for item in items:
                        # Keep track of the largest detected date/time
                        this_changedTime = item["properties"]["lastStateChangeTimeUtc"]
                        if (this_changedTime > max_asc_task_date):
                            max_asc_task_date = this_changedTime
                            
                        event = helper.new_event(
                            data=json.dumps(item),
                            source=event_source.lower(),
                            index=helper.get_output_index(),
                            sourcetype=task_sourcetype)
                        ew.write_event(event)
                        
                    sys.stdout.flush()
                    helper.save_check_point(task_check_point_key, max_asc_task_date)
                    items = azutils.handle_nextLink(helper=helper, response=response, session=session)
        else:
            raise RuntimeError("Unable to obtain access token. Please check the Client ID, Client Secret, and Tenant ID")

    def get_account_fields(self):
        account_fields = []
        account_fields.append("azure_app_account")
        return account_fields

    def get_checkbox_fields(self):
        checkbox_fields = []
        checkbox_fields.append("collect_security_center_alerts")
        checkbox_fields.append("collect_security_center_tasks")
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
    exitcode = ModInputazure_security_center_input().run(sys.argv)
    sys.exit(exitcode)
