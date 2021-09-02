
# encoding = utf-8
# Always put this line at the beginning of this file
import ta_ms_aad_declare

import os
import sys

from alert_actions_base import ModularAlertBase
import modalert_dismiss_azure_alert_helper

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

    def process_event(self, *args, **kwargs):
        status = 0
        try:
            if not self.validate_params():
                return 3
            status = modalert_dismiss_azure_alert_helper.process_event(self, *args, **kwargs)
        except (AttributeError, TypeError) as ae:
            self.log_error("Error: {}. Please double check spelling and also verify that a compatible version of Splunk_SA_CIM is installed.".format(str(ae)))
            return 4
        except Exception as e:
            msg = "Unexpected error: {}."
            if e:
                self.log_error(msg.format(str(e)))
            else:
                import traceback
                self.log_error(msg.format(traceback.format_exc()))
            return 5
        return status

if __name__ == "__main__":
    exitcode = AlertActionWorkerdismiss_azure_alert("TA-MS-AAD", "dismiss_azure_alert").run(sys.argv)
    sys.exit(exitcode)
