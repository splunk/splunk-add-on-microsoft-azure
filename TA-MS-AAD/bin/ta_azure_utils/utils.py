# encoding = utf-8
import sys
import json
import datetime
import dateutil.parser
import requests
import six

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

        if '@odata.nextLink' in response_json:
            nextLink = response_json['@odata.nextLink']

            # This should never happen, but just in case...
            if not is_https(nextLink):
                raise ValueError("nextLink scheme is not HTTPS. nextLink URL: %s" % nextLink)

            helper.log_debug("_Splunk_ nextLink URL (@odata.nextLink): %s" % nextLink)
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