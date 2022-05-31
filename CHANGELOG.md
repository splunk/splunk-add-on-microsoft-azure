# Version 4.0.0
* **BREAKING CHANGE**: removed deprecated event hub input. Use the [Splunk Add-on for Microsoft Cloud Services](https://splunkbase.splunk.com/app/3110/) to collect event hub data.
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