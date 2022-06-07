# Microsoft Azure Add-on for Splunk

# About
* Vendor Products:
    * Microsoft Azure Active Directory [Sign-ins](https://docs.microsoft.com/en-us/graph/api/signin-list), [Audit](https://docs.microsoft.com/en-us/graph/api/directoryaudit-list), and [Users](https://docs.microsoft.com/en-us/graph/api/user-list)
    * Microsoft Azure [Consumption API](https://docs.microsoft.com/en-us/rest/api/consumption/usagedetails/list)
    * Microsoft Azure [Virtual Machine API](https://docs.microsoft.com/en-us/rest/api/compute/virtualmachines), [Disks API](https://docs.microsoft.com/en-us/rest/api/compute/disks/list), [Network Watcher API](https://docs.microsoft.com/en-us/rest/api/network-watcher/network-watchers/get-topology)
    * Splunk platform versions: 8.0.0 and later
    * Platforms: Platform independent
    * Visible: Yes, this add-on contains configuration

# Prerequisites
* An active Azure Subscription
* For Azure Active Directory Sign-in data, an Azure Active Directory Premium P1 or P2 edition
* An Azure Active Directory Application Registration

# Required APIs and Permissions
[Azure/O365 Add-on Required Permissions](http://bit.ly/Splunk_Azure_Permissions)

# Installing
## Where to install this add-on
Unless otherwise noted, all supported add-ons can be safely installed to all tiers of a distributed Splunk platform deployment. See Where to install Splunk add-ons in Splunk Add-ons for more information.

This table provides a reference for installing this specific add-on to a distributed deployment of Splunk Enterprise.

|Splunk platform component|Supported|Required|Comments|
|-------------------------|---------|--------|--------|
|Search Heads|Yes|Yes|This add-on contains search-time knowledge. It is recommended to turn visibility off on your search heads to prevent data duplication errors that can result from running inputs on your search heads instead of (or in addition to) on your data collection node.|
|Heavy Forwarders|Yes|No (but recommended)|It is recommended to install this add-on on a heavy forwarder for data collection. Data collection should be configured in only 1 place to avoid duplicates.|
|Indexers|Yes|No|Not required as the parsing operations occur on the forwarders.|
|Universal Forwarders|No|No|Universal forwarders are not supported for data collection because the modular inputs require Python and the Splunk REST handler.|

---
# Azure Active Directory Input Notes

## Sign-in Data Collected
The [API that the Azure Active Directory Sign-in input uses](https://docs.microsoft.com/en-us/graph/api/signin-list) only returns sign-ins that are interactive in nature (where a username/password is passed as part of the auth token) and successful federation sign-ins.  To collect sign-in data like non-interactive sign-ins, service principal sign-ins, managed identity sing-ins, etc., [stream the Azure Active Directory data to an Event Hub](https://docs.microsoft.com/en-us/azure/active-directory/reports-monitoring/tutorial-azure-monitor-stream-logs-to-event-hub).  The [Splunk Add-on for Microsoft Cloud Services](https://splunkbase.splunk.com/app/3110/) can be used to retrieve Event Hub data.

## Throttling Guidance
The Azure Active Directory Sign-in and Audit inputs in this add-on utilize [Azure AD activity reports available in the Microsoft Graph API](https://docs.microsoft.com/en-us/graph/api/resources/azure-ad-auditlog-overview).  Microsoft Graph imposes [service-specific limits](https://docs.microsoft.com/en-us/graph/throttling) to prevent the overuse of resources.  These limits affect the scalability and throughput of the Azure Active Directory Sign-in and Audit inputs in this add-on.  Refer to the [identity and access reports service limits](https://docs.microsoft.com/en-us/graph/throttling#identity-and-access-reports-service-limits) for specific imposed limits.

## Identifying Throttling in your Splunk Environment
When throttling happens, an HTTP response code 429 is returned.  Run the following search to determine if throttling is impacting your data ingestion:

    index=_internal 429 client error

## Paging
When a request is made to Microsoft Graph, only the first 1,000 records are returned.  If there are more than 1,000 records available, a continuation token is returned along with the data.  In this scenario, Splunk will index the 1,000 records returned and then follow the continuation token to retrieve the next 1,000 records.  Each 1,000 record request counts toward the throttling limits.

## Recommendation
To overcome throttling and collect non-interactive sign-in data, send Azure Active Directory Sign-in and Audit data to an Event Hub.  The [Splunk Add-on for Microsoft Cloud Services](https://splunkbase.splunk.com/app/3110/) can be utilized to collect Event Hub data.

---

# Upgrading
Upgrades of the same major version are supported.  For example, upgrading from version 2.0.0 to 2.1.0 will work.  However, upgrading from version 2.x to 3.x will not work and will cause errors.

# Configuration

Ensure the prerequisites are met above.

* Most inputs require an Azure AD application registration.  Refer to the in-app documentation for details on setting this up.


# CIM Compliance

## Version 4.13.0

* Authentication model
    * Azure AD sign-in events
* Inventory model
    * Azure AD user events
* User model
    * Azure AD user events

# Privacy
Use of this add-on is permitted subject to your obligations, including data privacy obligations, under your agreement with Splunk and [Splunk's Privacy Policy](https://www.splunk.com/en_us/legal/privacy/privacy-policy.html).

## Contributors
* Jason Conger
* Ryan Lait
* Johnny Blizzard