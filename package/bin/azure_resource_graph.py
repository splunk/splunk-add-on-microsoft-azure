# encoding = utf-8
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
import ta_azure_utils.auth as azauth
import ta_azure_utils.utils as azutils

bin_dir = os.path.basename(__file__)

class ModInputazure_resource_graph(base_mi.BaseModInput):

    def __init__(self):
        use_single_instance = False
        super(ModInputazure_resource_graph, self).__init__("ta_ms_aad", "azure_resource_graph", use_single_instance)
        self.global_checkbox_fields = None

    def get_scheme(self):
        """overloaded splunklib modularinput method"""
        scheme = super(ModInputazure_resource_graph, self).get_scheme()
        scheme.title = ("Azure Resource Graph")
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
        scheme.add_argument(smi.Argument("subscription_ids", title="Subscription IDs",
                                         description="Comma separated list of subscription IDs against which to execute the query.",
                                         required_on_create=True,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("environment", title="Environment",
                                         description="",
                                         required_on_create=True,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("resource_graph_query", title="Resource Graph Query",
                                         description="The resources query.  Example: project id, name, type, location, tags | limit 10",
                                         required_on_create=True,
                                         required_on_edit=False))
        scheme.add_argument(smi.Argument("source_type", title="Resource Graph Sourcetype",
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
        tenant_id = helper.get_arg("tenant_id")
        event_source = "%s:tenant_id:%s" % (helper.input_type, tenant_id)
        subscription_ids = helper.get_arg("subscription_ids")
        query = helper.get_arg("resource_graph_query")
        source_type = helper.get_arg("source_type")
        input_name = helper.get_input_stanza_names()
        
        environment = helper.get_arg("environment")
        management_base_url = azutils.get_environment_mgmt(environment)
        
        session = azauth.get_mgmt_session(client_id, client_secret, tenant_id, environment, helper)
        
        if(session):
            helper.log_debug("_Splunk_ input_name=%s Collecting resource graph data." % input_name)
            url = management_base_url + "/providers/Microsoft.ResourceGraph/resources?api-version=2021-03-01"
            options = {"$top": 1000, "$skip": 0}
            response = azutils.get_json_resources_by_query(helper=helper, url=url, session=session, query=query, subscription_ids=subscription_ids.split(","), options=options)
            items = response['data'] or None
    
            while items:
                for item in items:
                    event = helper.new_event(
                            data = json.dumps(item),
                            source = event_source.lower(),
                            index = helper.get_output_index(),
                            sourcetype = source_type)
                    ew.write_event(event)
    
                sys.stdout.flush()
                items = None
    
                if '$skipToken' in response:
                    options = {"$skipToken": response["$skipToken"]}
                    response = azutils.get_json_resources_by_query(helper=helper, url=url, session=session, query=query, subscription_ids=subscription_ids.split(","), options=options)
                    items = response['data']
    
        else:
            raise RuntimeError("Unable to obtain access token. Please check the Client ID, Client Secret, and Tenant ID")

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
    exitcode = ModInputazure_resource_graph().run(sys.argv)
    sys.exit(exitcode)
