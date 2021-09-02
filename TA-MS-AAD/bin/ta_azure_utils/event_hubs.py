import sys
import asyncio
import json
from azure.eventhub.aio import EventHubConsumerClient
from azure.eventhub import TransportType
from ta_azure_utils.utils import get_proxy

helper = None
ew = None

async def on_event(partition_context, event):
    
    source_type = helper.get_arg("source_type")
    input_name = helper.get_input_stanza_names()
    event_hub_name = helper.get_arg("event_hub_name")
    index = helper.get_output_index()
    
    event_body = event.body_as_str(encoding='UTF-8')
    is_event_body_json = False
    
    # Try to convert the body to JSON
    try:
        event_body_json = json.loads(event_body)
        event_body = event_body_json
        is_event_body_json = True
    except ValueError as e:
        helper.log_debug("_Splunk_ Event message body is not JSON - parsing as text. %s" % event_body)
        
    if(is_event_body_json):
        if "records" in event_body:
            helper.log_debug("_Splunk_ Found record array in event body %s" % json.dumps(event_body))
            
            for record in event_body["records"]:
                e = helper.new_event(
                    data = json.dumps(record),
                    index = index,
                    sourcetype = source_type)
                ew.write_event(e)
                sys.stdout.flush()
        else:
            e = helper.new_event(
                data = json.dumps(event_body),
                index = index,
                sourcetype = source_type)
            ew.write_event(e)
            sys.stdout.flush()
            
    else:
        e = helper.new_event(
                data = str(event_body),
                index = index,
                sourcetype = source_type)
        ew.write_event(e)
        sys.stdout.flush()

    # Update memory checkpoint 
    await partition_context.update_checkpoint(event)

    # Update Splunk checkpoint for this partition
    check_point_key = "event_hub_sequence_number_%s_%s_%s" % (input_name, event_hub_name, partition_context.partition_id)
    helper.save_check_point(check_point_key, partition_context.last_enqueued_event_properties["sequence_number"])

async def on_error(partition_context, error):
    if partition_context:
        helper.log_error("_Splunk_ An exception: {} occurred during receiving from Partition: {}.".format(
            partition_context.partition_id,
            error
        ))
    else:
        helper.log_error("_Splunk_ An exception: {} occurred during the load balance process.".format(error))

async def on_partition_initialize(partition_context):
    helper.log_debug("_Splunk_ Partition: {} has been initialized.".format(partition_context.partition_id))

async def on_partition_close(partition_context, reason):
    helper.log_debug("_Splunk_ Partition: {} has been closed, reason for closing: {}.".format(
        partition_context.partition_id,
        reason
    ))

async def get_starting_positions(partition_ids):
    starting_positions = {}
    input_name = helper.get_input_stanza_names()
    event_hub_name = helper.get_arg("event_hub_name")

    for partition_id in partition_ids:
        starting_positions[partition_id] = -1
        check_point_key = "event_hub_sequence_number_%s_%s_%s" % (input_name, event_hub_name, partition_id)
        sequence_number = helper.get_check_point(check_point_key)
        if sequence_number:
            starting_positions[partition_id] = sequence_number
        else:
            starting_positions[partition_id] = -1

    return starting_positions

async def collect_event_hub_events(_helper, _ew):
    global helper, ew
    helper = _helper
    ew = _ew
    transport_type = TransportType.Amqp if helper.get_arg("transport_type") == "Amqp" else TransportType.AmqpOverWebsocket
    client = EventHubConsumerClient.from_connection_string(
        conn_str = helper.get_arg("connection_string"),
        consumer_group = helper.get_arg("consumer_group"),
        eventhub_name = helper.get_arg("event_hub_name"),
        http_proxy = get_proxy(helper, "event hub"),
        retry_total = 3,
        idle_timeout = 10,
        transport_type = transport_type)

    partition_ids = await client.get_partition_ids()
    try:
        starting_positions = await get_starting_positions(partition_ids)
    except:
        starting_positions = -1

    async with client:
        await client.receive(
            on_event = on_event,
            on_error = on_error,
            on_partition_close = on_partition_close,
            on_partition_initialize = on_partition_initialize,
            starting_position = starting_positions,
            track_last_enqueued_event_properties = True,
            owner_level = int(helper.get_arg("owner_level")))
