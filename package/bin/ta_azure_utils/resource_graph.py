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
import sys
import json
import datetime
import dateutil.parser
import requests
import ta_azure_utils.utils as azutils

def get_resources_by_query(helper, access_token, query, subscription_id, environment, resources=[]):

    if(environment == "gov"):
        management_base_url = "https://management.usgovcloudapi.net"
    else:
        management_base_url = "https://management.azure.com"

    url = management_base_url + "/providers/Microsoft.ResourceGraph/resources?api-version=2019-04-01"
    input_name = helper.get_input_stanza_names()

    headers = {}
    headers["Authorization"] = "Bearer %s" % access_token
    headers["Content-type"] = "application/json"

    data = {}
    data["query"] = query
    data["subscriptions"] = subscription_id

    proxies = azutils.get_proxy(helper, "requests")

    try:
        r = requests.post(url, headers=headers, proxies=proxies, data=json.dumps(data))
        r.raise_for_status()
        response_json = json.loads(r.content)

        resources += response_json["data"]["rows"]

        if '@odata.nextLink' in response_json:
            nextLink = response_json['@odata.nextLink']

            # This should never happen, but just in case...
            if not azutils.is_https(nextLink):
                raise ValueError("nextLink scheme is not HTTPS. nextLink URL: %s" % nextLink)

            helper.log_debug("_Splunk_ input_name=%s nextLink URL (@odata.nextLink): %s" % (input_name, nextLink))
            get_resources_by_query(helper, access_token, nextLink, subscription_id, resources)
    except Exception as e:
        raise e

    return resources


def get_json_resources_by_query(helper, access_token, query, subscription_ids, environment, resources=[]):

    if(environment == "gov"):
        management_base_url = "https://management.usgovcloudapi.net"
    else:
        management_base_url = "https://management.azure.com"

    url = management_base_url + "/providers/Microsoft.ResourceGraph/resources?api-version=2019-04-01"
    input_name = helper.get_input_stanza_names()

    headers = {}
    headers["Authorization"] = "Bearer %s" % access_token
    headers["Content-type"] = "application/json"

    data = {}
    data["query"] = query
    data["subscriptions"] = subscription_ids

    proxies = azutils.get_proxy(helper, "requests")

    try:
        r = requests.post(url, headers=headers, proxies=proxies, data=json.dumps(data))
        r.raise_for_status()
        response_json = json.loads(r.content)

        keys = []
        for column in response_json["data"]["columns"]:
            keys.append(column["name"])

        for row in response_json["data"]["rows"]:
            resource = {}
            i = 0
            for value in row:
                resource[keys[i]] = value
                i = i + 1
            resources.append(resource)

        if '@odata.nextLink' in response_json:
            nextLink = response_json['@odata.nextLink']

            # This should never happen, but just in case...
            if not azutils.is_https(nextLink):
                raise ValueError("nextLink scheme is not HTTPS. nextLink URL: %s" % nextLink)

            helper.log_debug("_Splunk_ nextLink URL (@odata.nextLink): %s" % (input_name, nextLink))
            get_json_resources_by_query(helper, access_token, nextLink, subscription_ids, resources)
    except Exception as e:
        raise e

    return resources