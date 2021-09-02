
# encoding = utf-8
# Always put this line at the beginning of this file
import ta_ms_aad_declare

import os
import sys

from alert_actions_base import ModularAlertBase
import modalert_stop_azure_vm_helper

class AlertActionWorkerstop_azure_vm(ModularAlertBase):

    def __init__(self, ta_name, alert_name):
        super(AlertActionWorkerstop_azure_vm, self).__init__(ta_name, alert_name)

    def validate_params(self):

        if not self.get_param("resource_group"):
            self.log_error('resource_group is a mandatory parameter, but its value is None.')
            return False

        if not self.get_param("vm_name"):
            self.log_error('vm_name is a mandatory parameter, but its value is None.')
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
            status = modalert_stop_azure_vm_helper.process_event(self, *args, **kwargs)
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
    exitcode = AlertActionWorkerstop_azure_vm("TA-MS-AAD", "stop_azure_vm").run(sys.argv)
    sys.exit(exitcode)
