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
import datetime
import requests
import re
import dateutil.parser
import ta_azure_utils.utils as azutils
from concurrent import futures

management_base_url = "https://management.azure.com"

def _get_metric_timespan(helper):
    check_point_key = "metrics_last_date_%s" % helper.get_input_stanza_names()
    end_time = datetime.datetime.utcnow() - datetime.timedelta(seconds=60)
    start_time = azutils.get_start_date(helper, check_point_key, 60) - datetime.timedelta(seconds=60)

    if start_time + datetime.timedelta(seconds=60) > end_time:
        end_time = start_time + datetime.timedelta(seconds=60)

    # The timespan of the query. It is a string with the following format 'startDateTime_ISO/endDateTime_ISO'.
    # Example: ...&timespan=2017-04-14T02:20:00Z/2017-04-14T04:20:00Z
    timespan_param = "%s/%s" % (start_time.strftime('%Y-%m-%dT%H:%M:%SZ'),end_time.strftime('%Y-%m-%dT%H:%M:%SZ'))
    
    return timespan_param
    
def _chunk_metric_list(metrics, chunk_size):
    for i in range(0, len(metrics), chunk_size):
        yield metrics[i:i + chunk_size]

def _cache_metric_definitions(helper, access_token, resource_id, resource_type):
    global management_base_url
    input_name = helper.get_input_stanza_names()
    helper.log_debug("_Splunk_ input_name=%s Getting metric definitions from Azure REST for type '%s'" % (input_name,resource_type))
    metric_definition_url = management_base_url + "%s/providers/microsoft.insights/metricDefinitions?api-version=2018-01-01" % resource_id
    metric_definitions = azutils.get_items(helper, access_token, metric_definition_url, items=[])

    metrics = []
    for metric in metric_definitions:
        metric_obj = {}
        metric_obj["name"] = metric['name']['value']
        
        time_grains = []
        for time_grain in metric["metricAvailabilities"]:
            time_grains.append(time_grain["timeGrain"])    
        metric_obj["time_grains"] = time_grains

        aggregation_types = []
        for aggregation_type in metric["supportedAggregationTypes"]:
            aggregation_types.append(aggregation_type.lower())
        metric_obj["aggregation_types"] = aggregation_types

        metrics.append(metric_obj)
    
    if len(metrics) > 0:
        # Cache the metric definition list as a check point
        checkpoint_data = {}
        checkpoint_data["last_updated_date"] = str(datetime.datetime.now())
        checkpoint_data["resource_type"] = resource_type
        checkpoint_data["metrics"] = metrics
        helper.log_debug("_Splunk_ input_name=%s Saving metric definitions from Azure REST for type '%s'.  Definitions: %s" % (input_name, resource_type, str(metrics)))
        helper.save_check_point(resource_type, checkpoint_data) 

def _get_metric_definitions_for_resource(helper, access_token, resource_id, resource_type):
    # Look in the cached set of metrics (stored as a check point) first to avoid unnecessary REST calls.
    # The KV Store doesn't like the '/' in the checkpoint key name, so sanitize it.
    check_point_key = resource_type.replace("/", "_")
    metric_definitions = helper.get_check_point(check_point_key)
    input_name = helper.get_input_stanza_names()

    if metric_definitions is not None:
        helper.log_debug("_Splunk_ input_name=%s Found metric definitions for namespace '%s' in the cache." % (input_name, resource_type))
    else:
        # Metric definitions were not found in the checkpoint, so go query the Azure REST endpoint for the metric definitions and store them in the checkpoint.
        helper.log_debug("_Splunk_ input_name=%s Metric defininitions for namespace '%s' were not found in the cache.  Polling Azure REST for the metric definitions." % (input_name, check_point_key))
        _cache_metric_definitions(helper, access_token, resource_id, check_point_key)
        metric_definitions = helper.get_check_point(check_point_key)
        if metric_definitions is None:
            helper.log_debug("_Splunk_ input_name=%s No metric definitions found for namespace '%s'. Skipping..." % (input_name, check_point_key))
            return
    
    # Update the metric cache if the definitions were fetched more than 30 days ago
    metrics_last_updated = dateutil.parser.parse(metric_definitions["last_updated_date"])
    utc_now = datetime.datetime.utcnow()
    if metrics_last_updated < utc_now - datetime.timedelta(days=30):
        helper.log_debug("_Splunk_ input_name=%s Metric definitions may be out of date.  The last update for namespace '%s' was on '%s'. Polling Azure REST for the definitions." % (input_name, resource_type, str(metrics_last_updated)))
        metric_definitions = _cache_metric_definitions(helper, access_token, resource_id, check_point_key)
        metric_definitions = helper.get_check_point(check_point_key)

    return metric_definitions["metrics"]

def _index_metrics(helper, ew, access_token, resource_obj, metric_url, requested_metric_statistics, metric_aggregations):

    # Extract the subscription ID to include in the event
    subscription_id = ''
    re_sub = re.compile(r"subscriptions\/(.*?)\/")
    try:
        subscription_id = re_sub.search(resource_obj["resource_id"].lower()).group(1)
    except:
        helper.log_error('_Splunk_ Regex parsing subscription_id failed with error: {0}'.format(sys.exc_info()[0]))

    try:
        resource_metrics = azutils.get_items(helper, access_token, metric_url, items=[])
    except Exception as e:
        helper.log_error("_Splunk_ Error getting metrics for resource '%s'. Detail: %s" % (resource_obj["resource_id"], str(e)))

    for metric in resource_metrics:
        metric_name = metric["name"]["value"]
        metric_unit = metric["unit"]
        
        for timeSeries in metric["timeseries"]:
            for data in timeSeries["data"]:
                metric_obj = {}
                metric_obj["host"] = resource_obj["resource_id"]
                metric_obj["metric_name"] = metric_name
                metric_obj["_time"] = data["timeStamp"]
                metric_obj["subscription_id"] = subscription_id
                metric_obj["unit"] = metric_unit
                metric_obj["namespace"] = resource_obj["resource_type"]

                for metric_stat in requested_metric_statistics:
                    # Only collect the requested statistics
                    if metric_stat in metric_aggregations[metric_name]:
                        if metric_stat in data:
                            metric_obj[metric_stat] = data[metric_stat]
                
                event = helper.new_event(
                    data=json.dumps(metric_obj),
                    index=helper.get_output_index(),
                    sourcetype=helper.get_arg("source_type"))
                ew.write_event(event) 

def _index_resource_metrics(helper, ew, access_token, resource_obj, metric_timespan, preferred_time_aggregation, requested_metric_statistics):

    global management_base_url

    # Metrics that support the preferred_time_aggregation will go in this list
    metrics_preferred = []

    # All other metrics will go in this list.
    # For example, the 'microsoft.storage/storageaccounts' namespace contains a metric called 'Used capacity' that only supports PT1H (1 hour).
    # Other metrics in this namespace support PT1M (1 minute).
    # If the user requested PT1M, the 'Used capacity' metric will go in the alternate list while other metrics that support PT1M go in the preferred list.
    metrics_alternate = []

    # Keep a dict of supported aggregations (average, minimum, maximum, etc) to comapre against requested statistics later.
    metric_aggregations = {}

    metric_definitions = _get_metric_definitions_for_resource(helper, access_token, resource_obj["resource_id"], resource_obj["resource_type"])
    
    input_name = helper.get_input_stanza_names()
    
    # Populate the preferred and alternate lists.
    for metric_definition in metric_definitions:
        if preferred_time_aggregation in metric_definition["time_grains"]:
            metrics_preferred.append(metric_definition["name"])
        else:
            metrics_alternate.append(metric_definition["name"])

        if metric_definition["name"] not in metric_aggregations:
            metric_aggregations[metric_definition["name"]] = metric_definition["aggregation_types"]

    # The Azure REST API will only accept 20 metrics at a time, so we may need to create multiple lists.
    metric_list_preferred = list(_chunk_metric_list(metrics_preferred, 20))
    metric_list_alternate = list(_chunk_metric_list(metrics_alternate, 20))

    # Index the preferred metrics
    for metric_list in metric_list_preferred:
        metric_url = management_base_url + "%s/providers/microsoft.insights/metrics?api-version=2018-01-01&timespan=%s&interval=%s&aggregation=%s&metricnames=%s" % \
            (resource_obj["resource_id"], metric_timespan, preferred_time_aggregation, ",".join(requested_metric_statistics), ",".join(metric_list))
        helper.log_debug("_Splunk_ input_name=%s Preferred metric URL: %s" % (input_name, metric_url))
        _index_metrics(helper, ew, access_token, resource_obj, metric_url, requested_metric_statistics, metric_aggregations)

    # Index the alternate metrics
    for metric_list in metric_list_alternate:
        metric_url = management_base_url + "%s/providers/microsoft.insights/metrics?api-version=2018-01-01&timespan=%s&aggregation=%s&metricnames=%s" % \
            (resource_obj["resource_id"], metric_timespan, ",".join(requested_metric_statistics), ",".join(metric_list))
        helper.log_debug("_Splunk_ input_name=%s Alternate metric URL: %s" % (input_name, metric_url))
        _index_metrics(helper, ew, access_token, resource_obj, metric_url, requested_metric_statistics, metric_aggregations)

def index_metrics_for_resources(helper, ew, access_token, environment, preferred_time_aggregation, metric_statistics, resources_to_query):
    global management_base_url
    if(environment == "gov"):
        management_base_url = "https://management.usgovcloudapi.net"
    else:
        management_base_url = "https://management.azure.com"

    metric_timespan = _get_metric_timespan(helper)
    number_of_threads = int(helper.get_arg("number_of_threads"))
   
    with futures.ThreadPoolExecutor(max_workers=number_of_threads) as executor:
        metrics_future = dict((executor.submit(_index_resource_metrics, helper, ew, access_token, resource_obj, metric_timespan, preferred_time_aggregation, metric_statistics), resource_obj) for resource_obj in resources_to_query)
       
        for future in futures.as_completed(metrics_future, None):
            resource = metrics_future[future]
            if future.exception() is not None:
                helper.log_error("_Splunk_ Error getting resource metrics for: %s. Detail: %s" % (resource, future.exception()))
