try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

import board
import time
from adafruit_magtag.magtag import MagTag
import adafruit_minimqtt.adafruit_minimqtt as MQTT
import time
import ssl
import socketpool
import wifi

from button import Button

magtag = MagTag()

magtag.add_text(
    text_position=(
        (magtag.graphics.display.width // 2) - 1,
        (magtag.graphics.display.height // 2) - 1,
    ),
    text_anchor_point=(0.5, 0.5),
    text_scale=3,
)

magtag.set_text("endling.local")


for button in magtag.peripherals.buttons:
    button.deinit()

buttons = []

for name, pin in [("button_a", board.BUTTON_A), ("button_b", board.BUTTON_B),
                  ("button_c", board.BUTTON_C), ("button_d", board.BUTTON_D)]:
    buttons.append(Button(name, pin))

try:
    print("connect")
    magtag.network.connect()

except (ValueError, RuntimeError, ConnectionError) as e:
    magtag.peripherals.neopixels.fill((80, 00, 00))
    print("Some error occured, retrying! -", e)
except:
    print("Unexpected error")

pool = socketpool.SocketPool(wifi.radio)

mqtt_client = MQTT.MQTT(
    broker=secrets["broker"],
    port=secrets["port"],
    socket_pool=pool,
    ssl_context=ssl.create_default_context(),
)

# Define callback methods which are called when events occur
# pylint: disable=unused-argument, redefined-outer-name
def connect(mqtt_client, userdata, flags, rc):
    # This function will be called when the mqtt_client is connected
    # successfully to the broker.
    print("Connected to MQTT Broker!")
    print("Flags: {0}\n RC: {1}".format(flags, rc))


def disconnect(mqtt_client, userdata, rc):
    # This method is called when the mqtt_client disconnects
    # from the broker.
    print("Disconnected from MQTT Broker!")


def subscribe(mqtt_client, userdata, topic, granted_qos):
    # This method is called when the mqtt_client subscribes to a new feed.
    print("Subscribed to {0} with QOS level {1}".format(topic, granted_qos))


def unsubscribe(mqtt_client, userdata, topic, pid):
    # This method is called when the mqtt_client unsubscribes from a feed.
    print("Unsubscribed from {0} with PID {1}".format(topic, pid))


def publish(mqtt_client, userdata, topic, pid):
    # This method is called when the mqtt_client publishes data to a feed.
    print("Published to {0} with PID {1}".format(topic, pid))


def message(client, topic, message):
    print("New message on topic {0}: {1}".format(topic, message))
    parts = topic.split("/")
    print("parts = {0}", parts)
    if parts[0] == "magtag":
        if parts[1] == "text":
            magtag.set_text(message)
        if parts[1] == "led":
            magtag.peripherals.neopixels[parts[3]] = message

# Connect callback handlers to mqtt_client
mqtt_client.on_connect = connect
mqtt_client.on_disconnect = disconnect
mqtt_client.on_subscribe = subscribe
mqtt_client.on_unsubscribe = unsubscribe
mqtt_client.on_publish = publish
mqtt_client.on_message = message

print("Attempting to connect to %s" % mqtt_client.broker)
mqtt_client.connect()

mqtt_client.subscribe("magtag/#")

magtag.peripherals.neopixel_disable = False

while True:
    for button in buttons:
        button.poll(mqtt_client)

    try:
        mqtt_client.loop(0.001)
    except (ValueError, RuntimeError, ConnectionError) as e:
        print("Some error occured, retrying! -", e)
