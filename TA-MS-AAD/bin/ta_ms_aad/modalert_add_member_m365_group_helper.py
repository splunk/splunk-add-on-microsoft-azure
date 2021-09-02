# encoding = utf-8
import splunklib.client as client
import six
import sys
import json
import requests
import ta_azure_utils.utils as azutil
import ta_azure_utils.auth as azauth


def process_event(helper, *args, **kwargs):
    """
    [sample_code_macro:start]

    # The following example sends rest requests to some endpoint
    # response is a response object in python requests library
    response = helper.send_http_request("http://www.splunk.com", "GET", parameters=None,
                                        payload=None, headers=None, cookies=None, verify=True, cert=None, timeout=None, use_proxy=True)
    # get the response headers
    r_headers = response.headers
    # get the response body as text
    r_text = response.text
    # get response body as json. If the body text is not a json string, raise a ValueError
    r_json = response.json()
    # get response cookies
    r_cookies = response.cookies
    # get redirect history
    historical_responses = response.history
    # get response status code
    r_status = response.status_code
    # check the response status, if the status is not sucessful, raise requests.HTTPError
    response.raise_for_status()


    # The following example gets and sets the log level
    helper.set_log_level(helper.log_level)

    # The following example gets account information
    user_account = helper.get_user_credential("<account_name>")

    # The following example gets the alert action parameters and prints them to the log
    account_name = helper.get_param("account_name")
    helper.log_info("account_name={}".format(account_name))

    group_id = helper.get_param("group_id")
    helper.log_info("group_id={}".format(group_id))

    member_id = helper.get_param("member_id")
    helper.log_info("member_id={}".format(member_id))

    tenant_id = helper.get_param("tenant_id")
    helper.log_info("tenant_id={}".format(tenant_id))


    # The following example adds two sample events ("hello", "world")
    # and writes them to Splunk
    # NOTE: Call helper.writeevents() only once after all events
    # have been added
    helper.addevent("hello", sourcetype="m365:group:member:add")
    helper.addevent("world", sourcetype="m365:group:member:add")
    helper.writeevents(index="summary", host="localhost", source="localhost")

    # The following example gets the events that trigger the alert
    events = helper.get_events()
    for event in events:
        helper.log_info("event={}".format(event))

    # helper.settings is a dict that includes environment configuration
    # Example usage: helper.settings["server_uri"]
    helper.log_info("server_uri={}".format(helper.settings["server_uri"]))
    [sample_code_macro:end]
    """

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