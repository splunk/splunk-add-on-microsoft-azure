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
import requests
import ta_azure_utils.utils as azutils

def get_graph_session(client_id, client_secret, tenant_id, environment, helper):

    if(environment == "gov"):
        endpoint = "https://login.microsoftonline.us/%s/oauth2/v2.0/token" % tenant_id
        payload = {
            'scope': 'https://graph.microsoft.us/.default',
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }
    else:
        endpoint = "https://login.microsoftonline.com/%s/oauth2/v2.0/token" % tenant_id
        payload = {
            'scope': 'https://graph.microsoft.com/.default',
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }

    try:
        return _get_session(endpoint, helper, payload)
    except Exception as e:
        raise e

def get_mgmt_session(client_id, client_secret, tenant_id, environment, helper):

    if(environment == "gov"):
        endpoint = "https://login.microsoftonline.us/%s/oauth2/token" % tenant_id
        payload = {
            'resource': 'https://management.usgovcloudapi.net/',
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }
    else:
        endpoint = "https://login.microsoftonline.com/%s/oauth2/token" % tenant_id
        payload = {
            'resource': 'https://management.azure.com/',
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }

    try:
        return _get_session(endpoint, helper, payload)
    except Exception as e:
        raise e
    
def get_loganalytics_session(client_id, client_secret, tenant_id, environment, helper):

    if(environment == "gov"):
        endpoint = "https://login.microsoftonline.us/%s/oauth2/token" % tenant_id
        payload = {
            'resource': 'https://api.loganalytics.us',
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }
    else:
        endpoint = "https://login.microsoftonline.com/%s/oauth2/token" % tenant_id
        payload = {
            'resource': 'https://api.loganalytics.io',
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }

    try:
        return _get_session(endpoint, helper, payload)
    except Exception as e:
        raise e

def get_graph_access_token(client_id, client_secret, tenant_id, environment, helper):

    if(environment == "gov"):
        endpoint = "https://login.microsoftonline.us/%s/oauth2/v2.0/token" % tenant_id
        payload = {
            'scope': 'https://graph.microsoft.us/.default',
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }
    else:
        endpoint = "https://login.microsoftonline.com/%s/oauth2/v2.0/token" % tenant_id
        payload = {
            'scope': 'https://graph.microsoft.com/.default',
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }

    try:
        return _get_access_token(endpoint, helper, payload)
    except Exception as e:
        raise e

def get_mgmt_access_token(client_id, client_secret, tenant_id, environment, helper):

    if(environment == "gov"):
        endpoint = "https://login.microsoftonline.us/%s/oauth2/token" % tenant_id
        payload = {
            'resource': 'https://management.usgovcloudapi.net/',
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }
    else:
        endpoint = "https://login.microsoftonline.com/%s/oauth2/token" % tenant_id
        payload = {
            'resource': 'https://management.azure.com/',
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }

    try:
        return _get_access_token(endpoint, helper, payload)
    except Exception as e:
        raise e

def _get_access_token(endpoint, helper, payload):

    proxies = azutils.get_proxy(helper, "requests")
    try:
        response = requests.post(endpoint, data=payload, proxies=proxies).json()
        if 'access_token' in response:
            return response['access_token']
    except Exception as e:
        raise e

def _get_session(endpoint, helper, payload):

    session = requests.Session()

    proxies = azutils.get_proxy(helper, "requests")
    try:
        response = requests.post(endpoint, data=payload, proxies=proxies).json()

        if 'access_token' in response:
            headers = {}
            headers["Authorization"] = "Bearer %s" % response['access_token']
            headers["Content-type"] = "application/json"
            session.headers.update(headers)
            proxies = azutils.get_proxy(helper, "requests")
            if proxies:
                session.proxies.update(proxies)
            
            return session
    except Exception as e:
        raise e
