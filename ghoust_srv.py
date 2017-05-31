#!/usr/bin/env python3

import paho.mqtt.client as mqtt
import importlib
import time
import argparse
import pkgutil
from socket import error as socket_error
from threading import Timer

from api import API
from ghoust_player import Player

class GHOUST:

    def __init__(self, game_list, host, port, join_mode='auto'):

        self.clients = dict()
        self.host = host
        self.port = port
        self.join_mode = join_mode

        self.client = mqtt.Client("GHOUST_SRV", clean_session=False)
        self.client.will_set("GHOUST/server/status", "EXIT")
        self.client._on_connect = self._on_connect
        self.client._on_message = self._on_message

        # config parameters
        self.max_games = 4

        # game modules
        self.games = []
        self.activegames = []
        self.setgames(game_list)

        self.gamemodes = []
        for i,m, ispkg in pkgutil.walk_packages(path="games/."):
            if 'games.' in m:
                self.gamemodes.append(m[6:])

        self.api = API(self)

    #### game functions ####

    def setgames(self, game_list):
        # stop old games
        for g in self.games:
            g.stop()

        self.games = []
        self.activegames = []

        # start new games
        if self.join_mode == "auto":
            game_list = game_list[:1]

        for i, g in enumerate(game_list):
            m = importlib.import_module("games." + g)
            C = getattr(m, g)
            game = C(i)
            game.setup()
            self.games.append(game)
            self.activegames.append("{}:{}".format(i, g))

        if self.join_mode == "auto":
            for _,p in self.clients.items():
                p.set_game(self.games[0])

    # buzzer, vibro val: [0-1023, 0-1023], [duration (ms), frequency (hz)]
    # led val: [0-1023, 0-1023, 0-10123], [r, g, b]
    # parameter: ["motor", "buzzer", "led"]

    def _game_config(self, game, parameter, val=None, preset=None):
        if not (0 <= game <= 4) or parameter not in ["motor", "buzzer", "led"]:
            print("game number or parameter not valid")
            return
        topic = "GHOUST/game/{}/{}".format(game, parameter)

        if preset != None:
            if not (0 <= int(preset) <= 9):
                print("vibrate preset not in range")
            self.client.publish(topic, "PRESET:" + preset)

        if val != None:
            if (not (0 <= val[0] <= 1023) or
                not (0 <= val[1] <= 1023) or
                    (parameter == "led" and not(0 <= val[2] <= 1023))):
                print("vibrate values not in range")
            fstring = "RAW:{:04},{:04}"
            if parameter == "led":
                fstring = "RAW:{:04},{:04},{:04}"
            self.client.publish(topic, fstring.format(*val))

    #### mqtt callbacks ####

    def _on_connect(self, client, userdata, flags, rc):
        print(("Connected with result code " + str(rc)))

        client.subscribe("GHOUST/server/changegame")
        client.subscribe("GHOUST/clients/+/status")
        client.subscribe("GHOUST/clients/+/events/button")
        client.subscribe("GHOUST/clients/+/events/accelerometer")
        client.subscribe("GHOUST/clients/+/events/gestures")

    def _on_message(self, client, userdata, msg):
        topic = msg.topic.split("/")
        payload = str(msg.payload, 'utf-8')
        if len(topic) < 3:
            print(("msg tree too short! debug: " + msg.topic + " " + payload))
            return

        if topic[1] == "server":
            if topic[2] == "changegame":
                self.setgames(payload.split(","))
            return

        pid = topic[2]
        subtree = topic[3]
        if subtree == "status":
            if payload == "CONNECTED":

                pobj = Player(pid, client)
                self.clients.update({pid: pobj})
                if len(self.games) == 1:
                    pobj.set_game(self.games[0])

            elif payload == "DISCONNECTED" and pid in self.clients:
                pobj = self.clients[pid]
                self.clients.pop(pid)
                pobj.set_game(None)

                del pobj

        elif subtree == "events":
            # pass message to game engine callbacks
            elem = topic[4]
            if pid not in self.clients:
                print("{} not in client list. msg: {} {}".format(pid, topic, payload))
                return
            pobj = self.clients[pid]

            if pobj.status == "SELECT_GAME":
                if elem == "button":
                    if payload == "CLICK":
                        # dirty...
                        pobj.select_game(
                            (pobj.select_game_n + 1) % len(self.games))
                    elif payload == "LONGPRESS":
                        pobj.set_game(self.games[pobj.select_game_n])
            else:
                if elem == "button":
                    # Leave game
                    if payload == "LONGPRESS" and len(self.games) > 1:
                        pobj.set_game(None)
                    else:    # let game know of button press
                        pobj.game._on_button(pobj, payload)
                elif elem == "accelerometer":
                    pobj.game._on_accelerometer(pobj, payload)
                elif elem == "gestures":
                    pobj.game._on_gestures(pobj, payload)

    def stop(self):
        for g in self.games:
            g.stop()
        self.client.loop_stop()

    def run(self):
        # Start API
        self.api.run(threaded=True, debug=False)

        # Start Ghoust
        for i in range(3):
            try:
                self.client.connect(self.host, self.port, 10)
                break
            except socket_error as e:
                print(("socket.error: [{}] {}".format(e.errno, e.strerror)))
                if i == 2:
                    raise e
                print("retrying after 10s")
                time.sleep(10)

        mqtt_game_modes_list = ','.join(self.gamemodes)
        mqtt_active_games = ','.join(self.activegames)
        self.client.publish("GHOUST/server/status", "ACTIVE")
        self.client.publish("GHOUST/server/status/activegames", mqtt_active_games, retain=True)
        self.client.publish("GHOUST/server/status/gamemodes", mqtt_game_modes_list, retain=True)


        self.client.loop_forever()

#############################


def filter_clients(c, status=""):
    if status != "":
        return [e for _, e in list(c.items()) if e.status == status]
    return []


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="GHOUST. it is a game. it is very good")
    parser.add_argument('games', metavar='game', type=str,
                        nargs='+', help="the games to be run")
    parser.add_argument('-H', '--host', nargs='?', type=str,
                        default='localhost', help="Host where MQTT server is running")
    parser.add_argument('-p', '--port', nargs='?', type=int,
                        default=1883, help="Port where MQTT server is running")
    parser.add_argument('--debug', action='store_true', help="run debug clients")
    args = parser.parse_args()

    g = GHOUST(args.games, args.host, args.port)

    if args.debug:
        import ghoust_debug_clients
        debugclients = ghoust_debug_clients.ghoust_debug(num_clients=3)

    try:
        g.run()
    except KeyboardInterrupt:
        pass
    except:
        raise
    finally:
        g.stop()
        if args.debug:
            debugclients.stop()
