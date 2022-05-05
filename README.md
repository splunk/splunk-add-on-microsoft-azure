# Microsoft Azure Add-on for Splunk

Build:

    ucc-gen --ta-version=<version>

Package:

    slim package output/TA-MS-AAD

[Refer to the documentation](https://dev.splunk.com/enterprise/tutorials/module_validate/packageapp) for the Splunk Packaging Toolkit (`SLIM`) installation instructions.

Launch Docker container with add-on:

    docker compose up -d

The `docker-compose.yml` file will mount a volume pointing to `./output/TA-MS-AAD`