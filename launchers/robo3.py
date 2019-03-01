# future proof - depends on python-future
from builtins import *

import pika
import json
import time
import sys
from RuoteAMQP.launcher import Launcher


namespace = "opensuse.obs"
user = "obs"
user_pw = "obspw"
host = "127.0.0.1"
vhost = "obs"
exchange_type = 'fanout'

boss_host = "boss"
boss_user = "boss"
boss_pwd = "boss"
boss_vhost = "boss"

robog_namesspace = 'jobs2'

# The keys file contains all the routing keys used by OBS and the old
# events they map to. The namespace is not part of the file
# eg:
#    package.build_success BUILD_SUCCESS
with open("keys") as f:
    map_table = f.readlines()

# Convert to a typemap used to translate and a set of routing_keys used to bind
typemap = {}
for x in map_table:
    (key, ignore, old) = x.strip().partition(" ")
    if not old:
        old = key
    typemap[namespace + "." + key] = old

routing_keys = sorted(list(typemap.keys()))

# print(typemap)
# print(routing_keys)

# parameters = pika.URLParameters(
#    'amqp://guest:guest@10.10.10.2:5672/vhost%2F?backpressure_detection=t')
credentials = pika.PlainCredentials(user, user_pw)
parameters = pika.ConnectionParameters(host=host,
                                       credentials=credentials,
                                       virtual_host=vhost,
                                       backpressure_detection=True)


# create a message handling callback
def handle_message(ch, method, properties, body):
    print("body: %r\nmethod: %r\nproperties: %r\n\n" %
          (body, method, properties))

    definition = """
Ruote.process_definition :name => 'OBS Raw Event' do
  obs_event
end
"""
    event = json.loads(str(body, "utf-8"))  # interpret as utf8
    event['format'] = 2
    event['label'] = typemap[method.routing_key]          # 'REPO_PUBLISHED'
    event['obs_event_key'] = method.routing_key
    event['namespace'] = robog_namesspace
    #    event['time'] = time();

    # Fixup the event
    # This is due to the SR id now being called an SR number in the event
    if "REQUEST" in event['label']:
        event['id'] = event['number']

    fields = {"obsEvent": event}

    print("Launching fields: %s\n\n" % json.dumps(fields))

    # Pass on to robogrator
    launcher = Launcher(amqp_host=boss_host, amqp_user=boss_user,
                        amqp_pass=boss_pwd, amqp_vhost=boss_vhost)
    launcher.launch(definition, fields)
    # Note if an ack is sent when the channel is not expecting acks
    # the consumer will shut down
    ch.basic_ack(delivery_tag=method.delivery_tag)


# Now connect in a loop
while (True):
    try:
        # Connect to RabbitMQ
        connection = pika.BlockingConnection(parameters)
        # get a channel
        channel = connection.channel()
        # Ensure there is a suitable exchange from the obs
        channel.exchange_declare(exchange='obs',
                                 exchange_type=exchange_type,
                                 durable=True)

        # Create a queue
        result = channel.queue_declare(queue="obs_events",
                                       exclusive=False,
                                       durable=True)
        # get the queue's name
        queue_name = result.method.queue
        # and bind to it
        print("My queue is %s" % queue_name)
        if exchange_type == 'fanout':
            channel.queue_bind(exchange='obs',
                               queue=queue_name)
        elif exchange_type == 'direct':
            print("Warning exchange type:%s is not robust. Use fanout."
                  % exchange_type)
            for key in routing_keys:
                print("Listening on routing key %s" % key)
                channel.queue_bind(exchange='obs',
                                   queue=queue_name,
                                   routing_key=key)
        else:
            print("Unknown exchange type:%s" % exchange_type)
            sys.exit(1)

        print(' [*] Waiting for events. To exit press CTRL+C')

        # Consume messages on a queue using the handler
        # no_ack means "tell RabbitMQ I won't be acking messages"
        # so when set to False it means "tell RabbitMQ I *WILL* be acking
        # messages" and requires a basic_ack in the handler
        channel.basic_consume(consumer_callback=handle_message,
                              queue=queue_name,
                              exclusive=True,  # prevent multiple instances.
                              no_ack=False)

        print("Waiting for OBS events")
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
        connection.close()
        break
    except pika.exceptions.ConnectionClosed:
        # The server probably restarted
        # Give it a while and try again
        print("The server connection was closed. "
              "Sleeping and trying to reconnect")
        time.sleep(5)
        continue
