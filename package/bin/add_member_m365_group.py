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

class AlertActionWorkeradd_member_m365_group(ModularAlertBase):

    def __init__(self, ta_name, alert_name):
        super(AlertActionWorkeradd_member_m365_group, self).__init__(ta_name, alert_name)

    def validate_params(self):

        if not self.get_param("group_id"):
            self.log_error('group_id is a mandatory parameter, but its value is None.')
            return False

        if not self.get_param("member_id"):
            self.log_error('member_id is a mandatory parameter, but its value is None.')
            return False

        if not self.get_param("tenant_id"):
            self.log_error('tenant_id is a mandatory parameter, but its value is None.')
            return False
        return True

    def process_event(helper, *args, **kwargs):
        helper.log_info("_Splunk_ alert action add_member_m365_group started.")
        account_conf_file = "ta_ms_aad_account"
        environment = "Global"  # TODO: implement gov environment option
        account_name = helper.get_param("account_name")
        tenant_id = helper.get_param("tenant_id")
        group_id = helper.get_param("group_id")
        member_id = helper.get_param("member_id")
    
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
            access_token = azauth.get_graph_access_token(client_id, client_secret, tenant_id, environment, helper)
        except Exception as e:
            helper.log_error("_Splunk_ exception occurred while retrieving access token: %s" % str(e))
            raise e
        try:
            helper.log_info("_Splunk_ sending request to add group member. group_id: %s, member_id: %s" % (group_id, member_id))
            azutil.add_m365_group_member(helper, access_token, group_id, member_id)
            helper.log_info("_Splunk_ successfully sent request to add group member.")
        except Exception as e:
            helper.log_error("_Splunk_ exception occurred adding group member: %s" % str(e))
            raise e
        return 0

if __name__ == "__main__":
    exitcode = AlertActionWorkeradd_member_m365_group("TA-MS-AAD", "add_member_m365_group").run(sys.argv)
    sys.exit(exitcode)
