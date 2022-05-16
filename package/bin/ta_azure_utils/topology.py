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
import re

vnet_pattern =          "\/subscriptions\/(?P<subscriptionId>[^\/]+)\/resourceGroups\/(?P<resourceGroup>[^\/]+)\/providers\/Microsoft\.Network\/virtualNetworks\/(?P<vnetName>[^\"]+)"
nic_pattern =           "\/subscriptions\/(?P<subscriptionId>[^\/]+)\/resourceGroups\/(?P<resourceGroup>[^\/]+)\/providers\/Microsoft\.Network\/networkInterfaces/(?P<nicName>[^\"]+)"
subnet_pattern =        "\/subscriptions\/(?P<subscriptionId>[^\/]+)\/resourceGroups\/(?P<resourceGroup>[^\/]+)\/providers\/Microsoft\.Network\/virtualNetworks\/(?P<vnetName>[^\/]+)\/(?P<resourceType>[^\/]+)\/(?P<subnetName>[^\"]+)"
security_rule_pattern = "\/subscriptions\/(?P<subscriptionId>[^\/]+)\/resourceGroups\/(?P<resourceGroup>[^\/]+)\/providers\/Microsoft\.Network\/networkSecurityGroups\/(?P<securityGroupName>[^\/]+)\/(?P<resourceType>[^\/]+)\/(?P<securityRuleName>[^\"]+)"
vm_pattern =            "\/subscriptions\/(?P<subscriptionId>[^\/]+)\/resourceGroups\/(?P<resourceGroup>[^\/]+)\/providers\/Microsoft\.Compute\/virtualMachines\/(?P<vmName>[^\"]+)"
nsg_pattern =           "\/subscriptions\/(?P<subscriptionId>[^\/]+)\/resourceGroups\/(?P<resourceGroup>[^\/]+)\/providers\/Microsoft\.Network\/networkSecurityGroups\/(?P<securityGroupName>[^\"]+)$"

# Gets a specific topology for a resource group
def get_topology_by_rg(helper, access_token, subscription_id, environment, api_version, resourceGroupName, networkWatcherName, targetResourceGroupName):

    if(environment == "gov"):
        management_base_url = "https://management.usgovcloudapi.net"
    else:
        management_base_url = "https://management.azure.com"

    url = management_base_url + "/subscriptions/%s/resourceGroups/%s/providers/Microsoft.Network/networkWatchers/%s/topology?api-version=%s" % (subscription_id, resourceGroupName, networkWatcherName, api_version)
    header = {'Authorization':'Bearer ' + access_token}
    proxies = azutils.get_proxy(helper, "requests")
    
    try:
        r = requests.post(url, headers=header, proxies=proxies, json={'targetResourceGroupName': targetResourceGroupName})
        r.raise_for_status()
        topology = json.loads(r.text)
    except Exception as e:
        raise e

    # Create a dict with the resource ID as the key so we can look up specific resources later.
    resources = {}

    for resource in topology["resources"]:
        # If this is a subnet resource, the VNET is not associated. So, let's associate it.
        subnet_match = re.search(subnet_pattern, resource["id"])
        if (subnet_match):
            vnetId = "/subscriptions/{subscriptionId}/resourceGroups/{resourceGroup}/providers/Microsoft.Network/virtualNetworks/{vnetName}".format(
                subscriptionId = subnet_match.group("subscriptionId"),
                resourceGroup = subnet_match.group("resourceGroup"),
                vnetName = subnet_match.group("vnetName")
            )
            association = {}
            association["name"] = subnet_match.group("vnetName")
            association["resourceId"] = vnetId
            association["associationType"] = "Associated"
            resource["associations"].append(association)
            resource["vnetId"] = vnetId
    
        resources[resource["id"]] = resource
    
    # Now that we have a dict with all our resources, let's associate what is needed for visualizations
    # 1. Subnets should be associated with virtual networks (already done)
    # 2. VMs should be associated with subnets, virtual networks, and security groups.  We can get those from the associated NIC.
    # 3. NICs should be associated with VM, secuirty group, subnet, virtual network
    # 4. Security groups should be associated with NIC, VM, virtual network
    
    try:
        # Try the Python 2 way
        for key, resource in resources.iteritems():
            nic_match = re.search(nic_pattern, resource["id"])
            if(nic_match):
                # Get the subnet, NSG, and VM associated with the NIC
                subnet_assoc = _get_assoc(resource, subnet_pattern)
                nsg_assoc = _get_assoc(resource, nsg_pattern)
                vm_assoc = _get_assoc(resource, vm_pattern)

                # Get the subnet so that we can get the VNET
                subnet_resource = resources[subnet_assoc["resourceId"]]
                vnet_assoc = _get_assoc(subnet_resource, vnet_pattern)

                # The NIC should be associated with the virtual network
                if vnet_assoc is not None:
                    resource["associations"].append(vnet_assoc)
                    resource["vnetId"] = vnet_assoc["resourceId"]

                # The VM should be associated with the subnet, VNET, and NSG
                if vm_assoc is not None:
                    vm_resource = resources[vm_assoc["resourceId"]]
                    vm_resource["associations"].append(subnet_assoc)
                    vm_resource["associations"].append(vnet_assoc)
                    vm_resource["associations"].append(nsg_assoc)
                    # Let's set the vnetId while we're here
                    vm_resource["vnetId"] = vnet_assoc["resourceId"]

                # The NSG should be associated with the NIC, VM, and VNET
                if nsg_assoc is not None:
                    nsg_resource = resources[nsg_assoc["resourceId"]]
                    nic_assoc = {}
                    nic_assoc["name"] = resource["name"]
                    nic_assoc["resourceId"] = resource["id"]
                    nic_assoc["associationType"] = "Associated"
                    nsg_resource["associations"].append(nic_assoc)
                    if vm_assoc is not None:
                        nsg_resource["associations"].append(vm_assoc)
                    nsg_resource["associations"].append(vnet_assoc)
                    # Let's set the vnetID while we're here
                    nsg_resource["vnetId"] = vnet_assoc["resourceId"]
    except Exception as e:
        try:
            # Try the Python 3 way
            for key, resource in resources.items():
                nic_match = re.search(nic_pattern, resource["id"])
                if(nic_match):
                    # Get the subnet, NSG, and VM associated with the NIC
                    subnet_assoc = _get_assoc(resource, subnet_pattern)
                    nsg_assoc = _get_assoc(resource, nsg_pattern)
                    vm_assoc = _get_assoc(resource, vm_pattern)

                    # Get the subnet so that we can get the VNET
                    subnet_resource = resources[subnet_assoc["resourceId"]]
                    vnet_assoc = _get_assoc(subnet_resource, vnet_pattern)

                    # The NIC should be associated with the virtual network
                    if vnet_assoc is not None:
                        resource["associations"].append(vnet_assoc)
                        resource["vnetId"] = vnet_assoc["resourceId"]

                    # The VM should be associated with the subnet, VNET, and NSG
                    if vm_assoc is not None:
                        vm_resource = resources[vm_assoc["resourceId"]]
                        vm_resource["associations"].append(subnet_assoc)
                        vm_resource["associations"].append(vnet_assoc)
                        vm_resource["associations"].append(nsg_assoc)
                        # Let's set the vnetId while we're here
                        vm_resource["vnetId"] = vnet_assoc["resourceId"]

                    # The NSG should be associated with the NIC, VM, and VNET
                    if nsg_assoc is not None:
                        nsg_resource = resources[nsg_assoc["resourceId"]]
                        nic_assoc = {}
                        nic_assoc["name"] = resource["name"]
                        nic_assoc["resourceId"] = resource["id"]
                        nic_assoc["associationType"] = "Associated"
                        nsg_resource["associations"].append(nic_assoc)
                        if vm_assoc is not None:
                            nsg_resource["associations"].append(vm_assoc)
                        nsg_resource["associations"].append(vnet_assoc)
                        # Let's set the vnetID while we're here
                        nsg_resource["vnetId"] = vnet_assoc["resourceId"]
        except Exception as e:
            raise e

    return resources

def _get_assoc(resource, pattern):
    for assoc in resource["associations"]:
        match = re.search(pattern, assoc["resourceId"])
        if(match):
            return assoc
    return None

