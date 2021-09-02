[azure_resource_group://<name>]
azure_app_account = 
tenant_id = 
subscription_id = 
environment = 
source_type = 

[azure_resource_graph://<name>]
azure_app_account = 
tenant_id = 
subscription_ids = Comma separated list of subscription IDs against which to execute the query.
environment = 
resource_graph_query = The resources query.  Example: project id, name, type, location, tags | limit 10
source_type = 

[azure_topology_man://<name>]
azure_app_account = 
tenant_id = 
subscription_id = 
environment = 
source_type = 
network_watcher_name = Network Watchers provide access to topology data.
network_watcher_resource_group = Specify the Resource Group containing the Network Watcher.
target_resource_group = Specify the Resource Group to enumerate topology. This Resource Group should be in the same region as the Network Watcher.

[azure_topology_automatic://<name>]
azure_app_account = 
tenant_id = 
subscription_id = 
environment = 
source_type = 

[azure_reservation_recommendation://<name>]
azure_app_account = 
tenant_id = 
subscription_id = 
environment = 
recommendation_sourcetype = 

[azure_comp://<name>]
azure_app_account = 
tenant_id = 
subscription_id = 
environment = 
collect_virtual_machine_data = 
virtual_machine_sourcetype = 
collect_managed_disk_data = 
managed_disk_sourcetype = 
collect_image_data = 
image_sourcetype = 
collect_snapshot_data = 
snapshot_sourcetype = 

[azure_metrics://<name>]
azure_app_account = 
tenant_id = 
subscription_id = 
environment = 
source_type = 
namespaces = Coma separated list of metric namespaces to query. Detail https://docs.microsoft.com/en-us/azure/azure-monitor/platform/metrics-supported
metric_statistics = 
preferred_time_aggregation = If the preferred time period is not available for a specific metric in the namespace, the next available time grain will be used.
number_of_threads = The number of threads used to download metric data in parallel

[azure_event_hub://<name>]
connection_string = Shared access policy connection string found in the Azure portal.
event_hub_name = 
consumer_group = 
source_type = Specify a value to use as the event sourcetype.
transport_type = Advanced: The type of transport protocol that will be used for communicating with the Event Hubs service.
owner_level = Advanced: The priority for an exclusive consumer. A consumer with a higher owner level has higher exclusive priority. The owner level is also know as the 'epoch value' of the consumer.

[MS_AAD_device://<name>]
azure_app_account = 
tenant_id = a.k.a. Directory ID
environment = 
device_sourcetype = 

[aad_risk_detection://<name>]
azure_app_account = 
tenant_id = a.k.a. Directory ID
environment = 
risk_detection_sourcetype = 
start_date = The date/time to start collecting data. If no value is give, the input will start getting data 30 days in the past.

[azure_virtual_network://<name>]
azure_app_account = 
tenant_id = 
subscription_id = 
environment = 
collect_virtual_network_data = 
virtual_network_sourcetype = 
collect_network_interface_data = 
network_interface_sourcetype = 
collect_security_group_data = 
security_group_sourcetype = 
collect_public_ip_address_data = 
public_ip_sourcetype = 

[azure_subscription://<name>]
azure_app_account = 
tenant_id = 
environment = 
source_type = 

[MS_AAD_user://<name>]
azure_app_account = 
tenant_id = a.k.a. Directory ID
environment = 
user_sourcetype = 
endpoint = 

[MS_AAD_signins://<name>]
azure_app_account = 
tenant_id = a.k.a. Directory ID
environment = 
sign_in_sourcetype = 
start_date = The date/time to start collecting data.  If no value is give, the input will start getting data 24 hours in the past.
query_window_size = Specify the maximum number of minutes used for the query range.  This is useful for retrieving older data. Use this setting with caution.  Specify '0' to disable.
query_backoff_throttle = Advanced: number of seconds to subtract from the end date of the query. This helps accommodate near real-time events toward the end of a query that may arrive non sequentially.
endpoint = 

[MS_AAD_audit://<name>]
azure_app_account = 
tenant_id = a.k.a. Directory ID
environment = 
audit_sourcetype = 
start_date = The date/time to start collecting data.  If no value is give, the input will start getting data 7 days in the past.
query_window_size = Specify the maximum number of minutes used for the query range.  This is useful for retrieving older data. Use this setting with caution.  Specify '0' to disable.
query_backoff_throttle = Advanced: number of seconds to subtract from the end date of the query. This helps accommodate near real-time events toward the end of a query that may arrive non sequentially.
endpoint = 

[azure_consumption://<name>]
azure_app_account = 
tenant_id = 
subscription_id = 
environment = 
billing_sourcetype = 
query_days = Specify the maximum number of days to query each interval.
start_date = Defaults to 90 days in the past if empty.

[azure_security_center_input://<name>]
azure_app_account = 
tenant_id = 
subscription_id = 
environment = 
collect_security_center_alerts = 
security_alert_sourcetype = 
collect_security_center_tasks = 
security_task_sourcetype = 

[MS_AAD_group://<name>]
azure_app_account = 
tenant_id = a.k.a. Directory ID
environment = 
group_sourcetype = 
endpoint =