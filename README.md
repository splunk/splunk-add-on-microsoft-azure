# Splunk Add-on for Microsoft Azure

**BREAKING CHANGE**: version 4.0.0 removed the deprecated event hub input. Use the [Splunk Add-on for Microsoft Cloud Services](https://splunkbase.splunk.com/app/3110/) to collect event hub data. Refer to the [CHANGELOG](CHANGELOG.md) for more detail.

## Documentation
Refer to the [Wiki in this repository](https://github.com/splunk/splunk-add-on-microsoft-azure/wiki) for add-on documentation.

## Build
This add-on is built with Splunk's [UCC Generator](https://github.com/splunk/addonfactory-ucc-generator).  Install `ucc-gen` [per the instructions](https://splunk.github.io/addonfactory-ucc-generator/#installation). Then, execute the following from the command line in the root of this repository to build the add-on:

    ucc-gen --ta-version=<version>

Example:

    ucc-gen --ta-version=4.1.0

The add-on will be built in an `output` directory in the root of the repository.

## Launch Docker container with add-on

Create a `.env` text file in the root of your cloned repository with the following:

```
SPLUNK_APP_ID=TA-MS-AAD
SPLUNK_VERSION=latest
SPLUNK_PASSWORD=<SPLUNK ADMIN PASSWORD>

# Optional - SPLUNKBASE_USERNAME and SPLUNKBASE_PASSWORD are used to install apps from Splunkbase when the container is built
SPLUNKBASE_USERNAME=<YOUR SPLUNKBASE USERNAME>
# Create an OS environment variable for your Splunkbase password.  Example:
# export SPLUNKBASE_PASSWORD=<YOUR SPLUNKBASE PASSWORD>

# To include files/directories in test_files in the output add-on directory, set an environment variable named INCLUDE_TESTS.  Example:
# export INCLUDE_TESTS=true

# Optional - install the Splunk Add-on for Visual Studio Code for debugging and the Microsoft Azure App for Splunk for dashboards
SPLUNK_APPS_URL=https://splunkbase.splunk.com/app/4801/release/0.1.2/download,https://splunkbase.splunk.com/app/4882/release/2.0.1/download
```

Launch the container using the following command from the root of the repository:

    docker compose up -d

## Adjusting Preferences

User preferences like time zone and search preferences can be adjusted by editing the `./splunk_files/user-prefs.conf` file.

## Package

    slim package output/TA-MS-AAD

[Refer to the documentation](https://dev.splunk.com/enterprise/tutorials/module_validate/packageapp) for the Splunk Packaging Toolkit (`SLIM`) installation instructions.


_____________
    Copyright 2022 Splunk Inc.

    Licensed under the Apache License, Version 2.0 (the "License"); 
    you may not use this file except in compliance with the License. 
    You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, 
    software distributed under the License is distributed on an "AS IS" BASIS, 
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and limitations under the License.
_____________
