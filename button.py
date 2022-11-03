import digitalio
from adafruit_debouncer import Debouncer

class Button(object):
    def __init__(self, name, switch_pin):
        super(Button, self).__init__()

        self.name = name

        self.pin = digitalio.DigitalInOut(switch_pin)
        self.pin.direction = digitalio.Direction.INPUT
        self.pin.pull = digitalio.Pull.UP
        self.switch = Debouncer(self.pin)

    def poll(self, mqtt_client):
        self.switch.update()
        if self.switch.fell:
            print("%s pressed" % self.name)
            mqtt_client.publish("magtag/button/%s" % self.name, "pressed")
        elif self.switch.rose:
            print("%s released" % self.name)
            mqtt_client.publish("magtag/button/%s" % self.name, "released")
