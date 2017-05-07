#!/usr/bin/env python
import time

import paho.mqtt.client as mqtt
import importlib
from threading import Timer


class GHOUST_TEST:

    def __init__(self):

        self.client = mqtt.Client("GHOUST_TEST", clean_session=False)
        self.client.will_set("GHOUST/server/status", "EXIT")
        self.client._on_connect = self._on_connect
        self.client._on_message = self._on_message

    def _on_connect(self, client, userdata, flags, rc):
        print(("Connected with result code " + str(rc)))

        client.subscribe("GHOUST/clients/+/status")
        client.subscribe("GHOUST/clients/+/events/button")
        client.subscribe("GHOUST/clients/+/events/accelerometer")
        client.subscribe("GHOUST/clients/+/events/gestures")

    def set_accel_thresh(self, out, warn):

        self.client.publish("GHOUST/clients/" + self.pid +
                            "/config/accel_out", str(out))
        self.client.publish("GHOUST/clients/" + self.pid +
                            "/config/accel_warn", str(warn))

    def _on_message(self, client, userdata, msg):
        topic = msg.topic.split("/")
        payload = str(msg.payload)
        if len(topic) < 4:
            print(("msg tree too short! debug: " + msg.topic + " " + payload))
            return

        pid = topic[2]
        subtree = topic[3]
        if subtree == "status":
            if payload == "CONNECTED":
                self.pid = pid
                self.set_accel_thresh(1, 2)
            elif payload == "DISCONNECTED":
                # exit()
                pass
        elif subtree == "events":
            elem = topic[4]

            if elem == "button":
                self._on_button(payload)
            elif elem == "accelerometer":
                self._on_accelerometer(payload)
            elif elem == "gestures":
                self._on_gestures(payload)

    def _on_accelerometer(self, m):
        print(m)
        self.client.publish("GHOUST/clients/" + self.pid +
                            "/config/motor", "PRESET:1")

    def _on_button(self, m):
        print(m)

    def _on_gestures(self, m):
        print(m)

    def run(self):
        self.client.connect("localhost", 1883, 60)
        self.client.publish("GHOUST/server/status", "ACTIVE")

        # self.client.loop_forever()
        self.client.loop_start()

#############################


if __name__ == "__main__":

    g = GHOUST_TEST()
    try:
        g.run()
        while True:
            _warn = input("warn:")
            _out = input("out:")
            g.set_accel_thresh(_out, _warn)

    except KeyboardInterrupt:
        g.stop()
