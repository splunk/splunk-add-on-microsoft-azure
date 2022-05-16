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
import ta_azure_utils.metrics as azmetrics
import ta_azure_utils.resource_graph as az_resource_graph

bin_dir = os.path.basename(__file__)

class ModInputazure_metrics(base_mi.BaseModInput):

    def __init__(self):
        use_single_instance = False
        super(ModInputazure_metrics, self).__init__("ta_ms_aad", "azure_metrics", use_single_instance)
        self.global_checkbox_fields = None

    def get_scheme(self):
        """overloaded splunklib modularinput method"""
        scheme = super(ModInputazure_metrics, self).get_scheme()
        scheme.title = ("Azure Metrics")
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
        scheme.add_argument(smi.Argument("source_type", title="Metric Sourcetype",
                                         description="",
                                         required_on_create=True,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("namespaces", title="Namespaces",
                                         description="Comma-separated list of metric namespaces to query. Detail https://docs.microsoft.com/en-us/azure/azure-monitor/platform/metrics-supported",
                                         required_on_create=True,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("metrics_note", title="Namespace link",
                                         description="Available metrics namespaces https://docs.microsoft.com/en-us/azure/azure-monitor/platform/metrics-supported",
                                         required_on_create=False,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("metric_statistics", title="Metric Statistics",
                                         description="",
                                         required_on_create=True,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("preferred_time_aggregation", title="Preferred Time Aggregation",
                                         description="If the preferred time period is not available for a specific metric in the namespace, the next available time grain will be used.",
                                         required_on_create=True,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("number_of_threads", title="Number of Threads",
                                         description="The number of threads used to download metric data in parallel",
                                         required_on_create=True,
                                         required_on_edit=False))
        return scheme

    def get_app_name(self):
        return "TA-MS-AAD"

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
    exitcode = ModInputazure_metrics().run(sys.argv)
    sys.exit(exitcode)
