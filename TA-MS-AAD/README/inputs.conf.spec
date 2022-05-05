[MS_AAD_signins://<name>]
AAD_sign_in_note = 
interval = 
index = 
azure_app_account = 
tenant_id = 
environment = 
sign_in_sourcetype = 
start_date = 
filter = 
query_window_size = 
query_backoff_throttle = 
endpoint = 

[MS_AAD_user://<name>]
interval = 
index = 
azure_app_account = 
tenant_id = 
filter = 
environment = 
user_sourcetype = 
endpoint = 

[MS_AAD_group://<name>]
interval = 
index = 
azure_app_account = 
tenant_id = 
environment = 
group_sourcetype = 
endpoint = 

[MS_AAD_audit://<name>]
AAD_sign_in_note = 
interval = 
index = 
azure_app_account = 
tenant_id = 
environment = 
audit_sourcetype = 
start_date = 
query_window_size = 
query_backoff_throttle = 
endpoint = 

[MS_AAD_identity_protection://<name>]
interval = 
index = 
azure_app_account = 
tenant_id = 
environment = 
collect_risk_detection_data = 
risk_detection_sourcetype = 
collect_risky_user_data = 
risky_user_sourcetype = 
endpoint = 

[MS_AAD_device://<name>]
interval = 
index = 
azure_app_account = 
tenant_id = 
environment = 
device_sourcetype = 
endpoint = 

[azure_metrics://<name>]
interval = 
index = 
azure_app_account = 
tenant_id = 
subscription_id = 
environment = 
source_type = 
namespaces = 
metrics_note = 
metric_statistics = 
preferred_time_aggregation = 
number_of_threads = 

[azure_security_center_input://<name>]
interval = 
index = 
azure_app_account = 
tenant_id = 
subscription_id = 
environment = 
collect_security_center_alerts = 
security_alert_sourcetype = 
collect_security_center_tasks = 
security_task_sourcetype = 

[azure_subscription://<name>]
interval = 
index = 
azure_app_account = 
tenant_id = 
environment = 
source_type = 

[azure_resource_group://<name>]
interval = 
index = 
azure_app_account = 
tenant_id = 
subscription_id = 
environment = 
source_type = 

[azure_virtual_network://<name>]
interval = 
index = 
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

[azure_comp://<name>]
interval = 
index = 
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

[azure_kql://<name>]
interval = 
index = 
azure_app_account = 
tenant_id = 
workspace_id = 
kql_query = 
environment = 
source_type = 
index_stats = 

[azure_consumption://<name>]
interval = 
index = 
azure_app_account = 
tenant_id = 
subscription_id = 
environment = 
billing_sourcetype = 
query_days = 
start_date = 

[azure_reservation_recommendation://<name>]
interval = 
index = 
azure_app_account = 
tenant_id = 
subscription_id = 
environment = 
recommendation_sourcetype = 

[azure_resource_graph://<name>]
interval = 
index = 
azure_app_account = 
tenant_id = 
subscription_ids = 
environment = 
resource_graph_query = 
source_type = 

[azure_topology_automatic://<name>]
interval = 
index = 
azure_app_account = 
tenant_id = 
subscription_id = 
environment = 
source_type = 

[azure_topology_man://<name>]
interval = 
index = 
azure_app_account = 
tenant_id = 
subscription_id = 
environment = 
source_type = 
network_watcher_name = 
network_watcher_resource_group = 
target_resource_group = 