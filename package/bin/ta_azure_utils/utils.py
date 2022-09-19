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
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import six

TIMEOUT = 5 #seconds

def handle_nextLink(helper=None, response=None, session=None):
    if '@odata.nextLink' in response:
        nextLink = response['@odata.nextLink']
        helper.log_debug("_Splunk_ nextLink URL (@odata.nextLink): %s" % nextLink)
        
        # This should never happen, but just in case...
        if not is_https(nextLink):
            raise ValueError("nextLink scheme is not HTTPS. nextLink URL: %s" % nextLink)
        
        response = get_items_batch_session(helper=helper, url=nextLink, session=session)
        return response
    else:
        return None

def requests_retry_session(retries=3, backoff_factor=1, status_forcelist=(429, 500, 502, 503, 504), session=None):
    session = session or requests.Session()
    retry_strategy = Retry(
        total = retries,
        read = retries,
        connect = retries,
        backoff_factor = backoff_factor,
        status_forcelist = status_forcelist
    )
    adapter = HTTPAdapter(max_retries = retry_strategy)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def get_items(helper, access_token, url, items=[]):

    headers = {}
    headers["Authorization"] = "Bearer %s" % access_token
    headers["Content-type"] = "application/json"
    proxies = get_proxy(helper, "requests")

    try:
        r = requests.get(url, headers=headers, proxies=proxies)

        if r.status_code != 200:
            return items
        
        r.raise_for_status()
        response_json = None
        response_json = json.loads(r.content)
        items += response_json['value']

        nextLink = None
        if '@odata.nextLink' in response_json:
            nextLink = response_json['@odata.nextLink']

        if 'nextLink' in response_json:
            nextLink = response_json['nextLink']

        if nextLink:
            # This should never happen, but just in case...
            if not is_https(nextLink):
                raise ValueError("nextLink scheme is not HTTPS. nextLink URL: %s" % nextLink)

            helper.log_debug("_Splunk_ nextLink URL: %s" % nextLink)
            get_items(helper, access_token, nextLink, items)
        
    except Exception as e:
        raise e

    return items

def get_items_batch(helper, access_token, url):
    headers = {}
    headers["Authorization"] = "Bearer %s" % access_token
    headers["Content-type"] = "application/json"
    proxies = get_proxy(helper, "requests")

    try:
        r = requests.get(url, headers=headers, proxies=proxies)
        r.raise_for_status()
        response_json = None
        response_json = json.loads(r.content)
        batch = response_json
        
    except Exception as e:
        raise e

    return batch

def get_items_batch_session(helper=None, url=None, session=None):
    
    t0 = time.time()
    try:
        r = requests_retry_session(session=session).get(url, timeout=TIMEOUT)
        r.raise_for_status()
        response_json = None
        response_json = json.loads(r.content)
    except Exception as e:
        raise e
    finally:
        t1 = time.time()
        helper.log_debug("_Splunk_ filename: %s, module: %s, execution time: %s" % (__file__, sys._getframe().f_code.co_name, str(t1-t0)))

    return response_json

def post_items_batch_session(helper=None, url=None, headers=None, data=None, session=None):
    
    t0 = time.time()
    try:
        r = requests_retry_session(session=session).post(url=url, headers=headers, data=data, timeout=TIMEOUT)
        r.raise_for_status()
        response_json = None
        response_json = json.loads(r.content)
    except Exception as e:
        raise e
    finally:
        t1 = time.time()
        helper.log_debug("_Splunk_ filename: %s, module: %s, execution time: %s" % (__file__, sys._getframe().f_code.co_name, str(t1-t0)))

    return response_json

def get_item(helper, access_token, url):
    headers = {}
    headers["Authorization"] = "Bearer %s" % access_token
    headers["Content-type"] = "application/json"
    proxies = get_proxy(helper, "requests")

    try:
        r = requests.get(url, headers=headers, proxies=proxies)
        r.raise_for_status()
        response_json = None
        response_json = json.loads(r.content)
        item = response_json
        
    except Exception as e:
        raise e

    return item

def get_item_session(helper=None, session=None, url=None):
    t0 = time.time()
    item = None
    try:
        r = requests_retry_session(session=session).get(url, timeout=TIMEOUT)
        r.raise_for_status()
        response_json = None
        response_json = json.loads(r.content)
        item = response_json
    except Exception as e:
        raise e
    finally:
        t1 = time.time()
        helper.log_debug("_Splunk_ filename: %s, module: %s, execution time: %s" % (__file__, sys._getframe().f_code.co_name, str(t1-t0)))

    return item

def test_by_url(helper, access_token, url):
    headers = {}
    headers["Authorization"] = "Bearer %s" % access_token
    headers["Content-type"] = "application/json"
    proxies = get_proxy(helper, "requests")

    try:
        r = requests.get(url, headers=headers, proxies=proxies)
        r.raise_for_status()
    except Exception as e:
        raise e

def get_start_date(helper, check_point_key, default_minutes):
    # Try to get a date from the check point first
    d = helper.get_check_point(check_point_key)
    
    # If there was a check point date, retun it.
    if (d not in [None,'']):
        return datetime.datetime(d['year'], d['month'], d['day'], d['hour'], d['minute'], d['second'], d['microsecond'])
    else:
        # No check point date, so look if a start date was specified as an argument
        d = helper.get_arg("start_date")
        if (d not in [None,'']):
            return dateutil.parser.parse(d)
        else:
            # If there was no start date specified, default to x minutes ago
            return (datetime.datetime.utcnow() - datetime.timedelta(minutes=default_minutes))

def get_end_date(helper, start_date, minutes):
    if not isinstance(start_date, datetime.datetime):
        start_date = dateutil.parser.parse(start_date)

    return start_date + datetime.timedelta(minutes=minutes)

def get_proxy(helper, proxy_type="requests"):
    proxies = None
    helper.log_debug("_Splunk_ Getting proxy server.")
    proxy = helper.get_proxy()
    
    if proxy:
        helper.log_debug("_Splunk_ Proxy is enabled: %s:%s" % (proxy["proxy_url"], proxy["proxy_port"]))
        if proxy_type.lower()=="requests":
            proxy_url = "%s:%s" % (proxy["proxy_url"], proxy["proxy_port"])
            proxies = {
                    "http" : proxy_url,
                    "https" : proxy_url
                }
        elif proxy_type.lower()=="event hub":
            proxies = {
                'proxy_hostname': proxy["proxy_url"],
                'proxy_port': int(proxy["proxy_port"]),
                'username': proxy["proxy_username"],
                'password': proxy["proxy_password"]
            }
            
    return proxies

def is_https(url):
    if url.startswith("https://"):
        return True
    else:
        return False

def get_environment_graph(environment=None):
    if(environment == "gov"):
        graph_base_url = "https://graph.microsoft.us"
    elif(environment == "dod"):
        graph_base_url = "https://dod-graph.microsoft.us"
    else:
        graph_base_url = "https://graph.microsoft.com"
    return graph_base_url

def get_environment_mgmt(environment=None):
    if(environment == "gov"):
        management_base_url = "https://management.usgovcloudapi.net"
    else:
        management_base_url = "https://management.azure.com"
    return management_base_url

def get_environment_loganalytics(environment=None):
    if(environment == "gov"):
        loganalytics_base_url = "https://api.loganalytics.us"
    else:
        loganalytics_base_url = "https://api.loganalytics.io"
    return loganalytics_base_url

def get_json_resources_by_query(helper=None, url=None, session=None, query=None, subscription_ids=None, options=None):

    data = {}
    data["query"] = query
    data["subscriptions"] = subscription_ids
    if options:
        data["options"] = options
        
    t0 = time.time()
    try:
        r = requests_retry_session(session=session).post(url=url, timeout=TIMEOUT, data=json.dumps(data))
        r.raise_for_status()
        response_json = None
        response_json = json.loads(r.content)
    except Exception as e:
        raise e
    finally:
        t1 = time.time()
        helper.log_debug("_Splunk_ filename: %s, module: %s, execution time: %s" % (__file__, sys._getframe().f_code.co_name, str(t1-t0)))

    return response_json

def get_account_credentials(helper, conf, account_name=None):
        client_id = ''
        client_secret = ''
        for stanza in conf:
            if(account_name):
                # If the account_name is not None, check if this is the requested account.
                if stanza.name != account_name:
                    # If this is not the requested account, skip this loop iteration.
                    continue
            
            for key, value in six.iteritems(stanza.content):
                if key == "username":
                    try:
                        account = helper.get_user_credential(value)
                        client_id = account['username']
                        client_secret = account['password']
                        break
                    except Exception as e:
                        helper.log_error("_Splunk_ could not get credential: %s" % str(e))
                        
            if client_id != '' and client_secret != '':
                # Found the client id and secret.
                break
            else:
                helper.log_error("_Splunk_ a global account name could not be found.")
                continue

        if client_id == '' or client_secret == '':
            raise ValueError("_Splunk_ invalid credentials in .conf file or credential could not be found: %s" % account_name)
        else:
            return client_id, client_secret

def stop_azure_vm(helper, access_token, subscription_id, resource_group, vm_name):

    url = "https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Compute/virtualMachines/{vm_name}/powerOff?api-version=2020-12-01".format(subscription_id=subscription_id, resource_group=resource_group, vm_name=vm_name)
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': "Bearer %s" % access_token
    }

    proxies = get_proxy(helper)

    try:
        r = requests.post(url, headers=headers, proxies=proxies)
        r.raise_for_status()
    except Exception as e:
        raise e

def dismiss_asc_alert(helper, access_token, subscription_id, alert_location, alert_name):

    url = "https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.Security/locations/{alert_location}/alerts/{alert_name}/dismiss?api-version=2021-01-01".format(subscription_id=subscription_id, alert_location=alert_location, alert_name=alert_name)
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': "Bearer %s" % access_token
    }

    proxies = get_proxy(helper)

    try:
        r = requests.post(url, headers=headers, proxies=proxies)
        r.raise_for_status()
    except Exception as e:
        raise e

def add_m365_group_member(helper, access_token, group_id, member_id):

    url = "https://graph.microsoft.com/v1.0/groups/{group_id}/members/$ref".format(group_id=group_id)
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': "Bearer %s" % access_token
    }

    data = {
        "@odata.id": "https://graph.microsoft.com/v1.0/directoryObjects/{member_id}".format(member_id=member_id)
    }

    proxies = get_proxy(helper)

    r = requests.post(url, headers=headers, json=data, proxies=proxies)
    if r.status_code == 400:
        helper.log_info("_Splunk_ member id %s is already in the group with id %s" % (member_id, group_id))
        return
    if r.status_code == 404:
        helper.log_error("_Splunk_ member id %s was not found." % member_id)
        return
 
    r.raise_for_status()