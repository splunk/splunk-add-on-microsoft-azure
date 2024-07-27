# Version 4.1.0
* Added an input for Microsoft Entra ID Applications. [Issue #27](https://github.com/splunk/splunk-add-on-microsoft-azure/issues/27)
* Added an input for Microsoft Graph Security API

* Deprecated the Azure Metrics input. This functionality has moved to the [Splunk Add-on for Microsoft Cloud Services](https://splunkbase.splunk.com/app/3110).
* Deprecated the Azure Subscriptions input. This functionality has moved to the [Splunk Add-on for Microsoft Cloud Services](https://splunkbase.splunk.com/app/3110).
* Deprecated the Azure Resource Groups input. This functionality has moved to the [Splunk Add-on for Microsoft Cloud Services](https://splunkbase.splunk.com/app/3110).
* Deprecated the Azure Virtual Networks input. This functionality has moved to the [Splunk Add-on for Microsoft Cloud Services](https://splunkbase.splunk.com/app/3110).
* Deprecated the Azure Compute input. This functionality has moved to the [Splunk Add-on for Microsoft Cloud Services](https://splunkbase.splunk.com/app/3110).
* Deprecated the Azure KQL Log Analytics input. This functionality has moved to the [Splunk Add-on for Microsoft Cloud Services](https://splunkbase.splunk.com/app/3110).
* Deprecated the Azure Billing and Consumption input. This functionality has moved to the [Splunk Add-on for Microsoft Cloud Services](https://splunkbase.splunk.com/app/3110).
* Deprecated the Azure Azure Reservation Recommendation input. This functionality has moved to the [Splunk Add-on for Microsoft Cloud Services](https://splunkbase.splunk.com/app/3110).

* Changed `Azure Acitvie Directory` references to `Microsoft Entra ID`

* Fix - set default values for inputs that use a Graph endpoint to address add-on upgrade issues. [Issue #21](https://github.com/splunk/splunk-add-on-microsoft-azure/issues/21)
* Fix - Azure AD Sign-in and Audit inputs would raise an error if a Start Date parameter contained a time zone.  [Issue #16](https://github.com/splunk/splunk-add-on-microsoft-azure/issues/16)
* Fix - the `index_stats` option was ignored in the KQL input.  [Issue #25](https://github.com/splunk/splunk-add-on-microsoft-azure/issues/25)

# Version 4.0.3
* Fix - problem loading some inputs on Windows system. [Issue #8](https://github.com/splunk/splunk-add-on-microsoft-azure/issues/8) and [Issue #12](https://github.com/splunk/splunk-add-on-microsoft-azure/issues/12)
* Added `name` parameter to the `[id]` stanza in `default/app.conf`
* Bumped `splunktaucclib` to version `6.0.6` to address potential credential corruption issues
* Fix - errant newline in `eventtypes.conf` for `azure_vuln` stanza. [Issue #19](https://github.com/splunk/splunk-add-on-microsoft-azure/issues/19)
* Fix - nextLink parameter is different for consumption input causing limited results. [Issue #20](https://github.com/splunk/splunk-add-on-microsoft-azure/issues/20)
* Increase REST request timeout to 60 seconds

# Version 4.0.2
* Bug fix - Problem creating new AAD Audit Input - [Issue #3](https://github.com/splunk/splunk-add-on-microsoft-azure/issues/3)
* Bug fix - Azure AD User and Group pagination issue

# Version 4.0.0
* **BREAKING CHANGE**: removed deprecated event hub input. Use the [Splunk Add-on for Microsoft Cloud Services](https://splunkbase.splunk.com/app/3110/) to collect event hub data.
* Code is now open source [https://github.com/splunk/splunk-add-on-microsoft-azure](https://github.com/splunk/splunk-add-on-microsoft-azure)
* New input to collect Azure Log Analytics data via KQL queries
* Refactored code base to [UCC](https://github.com/splunk/addonfactory-ucc-generator) instead of [Splunk Add-on Builder](https://splunkbase.splunk.com/app/2962/)
* Implemented requests `Session()` and `Rerty()` classes for REST API calls
* Added query parameters option to the Azure Active Directory Users input
* Added query parameters option to the Azure Active Directory Groups input
* Added filter parameter option to the Azure Active Directory Sign-ins input
* Added input name to all DEBUG logging statements
* Updated Resource Graph input to use API version `2021-03-01`
* Updated Resource Group inputs to use API version `2021-04-01`
* Updated Security Center alerts input to use API version `2021-01-01`
* Updated Virtual Network inputs to use API version `2021-03-01`

# Version 3.2.0
* New input to collect Azure Active Directory Groups
* New alert action to stop an Azure Virtual Machine
* New alert action to add a user to a group
* New alert action to dismiss an Azure Security Center alert
* jQuery updates

# Version 3.1.1
* Added API version selection for REST inputs
* Removed restart requirements after install
* Updated billing and consumption input
* Improved compatibility with the Splunk Add-on for Microsoft Cloud Services

# Version 3.1.0
* Event Hub input deprecated.  Please use the Splunk Add-on for Microsoft Cloud Services https://splunkbase.splunk.com/app/3110/
* New input - Microsoft Azure Active Directory Devices
* New input - Microsoft Azure Active Directory Risk Detections
* Fixed an issue where Azure Active Directory sign-in events were truncated

# Version 3.0.1
* Added support for Azure Gov

# Version 3.0.0
* Updated to Splunk 8 / Python 3
* Updated the Event Hub Python library to use asyncio
* Event Hub input support for Windows
