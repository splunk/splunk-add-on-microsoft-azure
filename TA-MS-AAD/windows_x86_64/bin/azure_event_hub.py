import sys, os
sys.path.append(os.path.join(os.environ['SPLUNK_HOME'],'etc','apps','TA-MS-AAD','bin'))

import azure_event_hub_core

exitcode = azure_event_hub_core.ModInputazure_event_hub().run(sys.argv)
sys.exit(exitcode)