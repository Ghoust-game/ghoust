#!/usr/bin/env python

import paho.mqtt.client as mqtt
from random import randint, gammavariate
import threading
import time


class ghoust_debug:
    def __init__(self, delay=3, num_clients=10):
        t = []
        for i in range(num_clients):
            a = threading.Thread(target=self.client, args=[delay])
            a.start()
            t.append(a)
        self.t = t

    def stop(self):
        for f in self.t:
            f.do_run = False
        for f in self.t:
            f.join()

    def _on_message_debug(self, client, userdata, msg):

        if msg.topic == "GHOUST/server/status" and str(msg.payload) == "EXIT":
            t = threading.currentThread()
            t.do_run = False

        print("debug: " + msg.topic + " " + str(msg.payload))

    def client(self, delay=3):
        time.sleep(delay)
        cid = "{:04}".format(randint(0, 9999))
        client = mqtt.Client(cid)

        client._on_message = self._on_message_debug
        client.will_set(
            "GHOUST/clients/{0}/status".format(cid), "DISCONNECTED", retain=True)
        client.connect("localhost", 1883, 60)
        client.loop()
        client.subscribe("GHOUST/server/status")
        client.publish(
            "GHOUST/clients/{0}/status".format(cid), "CONNECTED", retain=True)

        t = threading.currentThread()
        while getattr(t, "do_run", True):

            s = randint(0, 2)
            if s == 0:
                v = "CLICK"
                if randint(0, 9) > 8:
                    v = "LONGPRESS"
                client.publish(
                    "GHOUST/clients/{0}/events/button".format(cid), v)
            if s == 1:
                a = int(gammavariate(1, 1) * 10)
                if a > 10:
                    if a > 13:
                        client.publish(
                            "GHOUST/clients/{0}/events/accelerometer".format(cid), "OUTSHOCK")
                    else:
                        client.publish(
                            "GHOUST/clients/{0}/events/accelerometer".format(cid), "WARNSHOCK")

            if s == 2:
                pass
                #client.publish("GHOUST/clients/{0}/events/gestures".format(cid), "2")

            client.loop()
            time.sleep(1)


if __name__ == "__main__":
    d = ghoust_debug()
