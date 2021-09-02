# encoding = utf-8
import sys
import json
import requests
import ta_azure_utils.utils as azutils

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
