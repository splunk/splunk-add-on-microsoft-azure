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
import import_declare_test
import splunklib.client as client
import six
import sys
import json
import requests
import ta_azure_utils.utils as azutil
import ta_azure_utils.auth as azauth
import os
from splunktaucclib.alert_actions_base import ModularAlertBase

class AlertActionWorkerdismiss_azure_alert(ModularAlertBase):

    def __init__(self, ta_name, alert_name):
        super(AlertActionWorkerdismiss_azure_alert, self).__init__(ta_name, alert_name)

    def validate_params(self):

        if not self.get_param("alert_location"):
            self.log_error('alert_location is a mandatory parameter, but its value is None.')
            return False

        if not self.get_param("alert_name"):
            self.log_error('alert_name is a mandatory parameter, but its value is None.')
            return False

        if not self.get_param("subscription_id"):
            self.log_error('subscription_id is a mandatory parameter, but its value is None.')
            return False

        if not self.get_param("tenant_id"):
            self.log_error('tenant_id is a mandatory parameter, but its value is None.')
            return False
        return True

    def process_event(helper, *args, **kwargs):
        helper.log_info("_Splunk_ alert action dismiss_azure_alert started.")
        account_conf_file = "ta_ms_aad_account"
        environment = "Global"  # TODO: implement gov environment option
        account_name = helper.get_param("account_name")
        tenant_id = helper.get_param("tenant_id")
        alert_location = helper.get_param("alert_location")
        alert_name = helper.get_param("alert_name")
        subscription_id = helper.get_param("subscription_id")
    
        try:
            service = client.connect(token=helper.session_key)
        except Exception as e:
            helper.log_error("_Splunk_ error connecting to Splunk client: %s" % str(e))
            raise e
        try:
            conf = service.confs[account_conf_file]
        except Exception as e:
            helper.log_error("_Splunk_ error getting account conf file: %s" % str(e))
            raise e
    
        if account_name not in ["", None]:
            helper.log_debug("_Splunk_ getting client ID and client secret from account name : {}".format(account_name))
            client_id, client_secret = azutil.get_account_credentials(helper, conf, account_name)
        else:
            helper.log_debug("_Splunk_ getting client ID and client secret from first configured account.")
            client_id, client_secret = azutil.get_account_credentials(helper, conf, None)
    
        try:
            access_token = azauth.get_mgmt_access_token(client_id, client_secret, tenant_id, environment, helper)
        except Exception as e:
            helper.log_error("_Splunk_ exception occurred while retrieving access token: %s" % str(e))
            raise e
        try:
            helper.log_info("_Splunk_ sending dismiss request for alert: %s" % alert_name)
            azutil.dismiss_asc_alert(helper, access_token, subscription_id, alert_location, alert_name)
            helper.log_info("_Splunk_ successfully sent dismiss request for alert: %s" % alert_name)
        except Exception as e:
            helper.log_error("_Splunk_ exception occurred dismissing alert: %s, error: %s" % (alert_name, str(e)))
            raise e
        return 0
if __name__ == "__main__":
    exitcode = AlertActionWorkerdismiss_azure_alert("TA-MS-AAD", "dismiss_azure_alert").run(sys.argv)
    sys.exit(exitcode)
