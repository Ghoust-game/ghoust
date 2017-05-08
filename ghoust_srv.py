#!/usr/bin/env python3
import time

import importlib
import time
import argparse
import ghoust

from socket    import error as socket_error
from threading import Timer


class GhoustServer:
    def __init__(self, game_list, host, port):
        self.client = PahoAdapter(host, port)

        # config parameters
        self.max_games = 4

        # game modules
        self.games = []
        self.setgames(game_list)

    #### game functions ####

    def setgames(self, game_list):
        # stop old games
        if len(self.games) > 0:
            for game in self.games:
                game.stop()

        self.games = []
        # start new games
        for i, g in enumerate(game_list):
            m = importlib.import_module("games." + g)
            C = getattr(m, g)
            game = C(i)
            game.setup()
            self.games.append(game)

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

    def stop(self):
        for game in self.games:
            game.stop()
        self.client.stop()

    def start(self):
        for i in xrange(3):
            try:
                self.client.connect
                break
            except socket_error as e:
                print("socket.error: [{}] {}".format(e.errno, e.strerror))
                if i == 2:
                    raise e
                print("retrying after 10s")
                time.sleep(10)

        self.client.publish("GHOUST/server/status", "ACTIVE")
        self.client.start()

#############################


def filter_clients(c, status=""):
    if status != "":
        return [e for _, e in c.items() if e.status == status]
    return []

def build_arguments_parser():
    parser = argparse.ArgumentParser(
        description="GHOUST. it is a game. it is very good")
    parser.add_argument(
            'games',
            metavar='game',
            type=str,
            nargs='+',
            help="the games to be run")
    parser.add_argument(
            '-H',
            '--host',
            nargs='?',
            type=str,
            default='localhost',
            help="Host where MQTT server is running")
    parser.add_argument(
            '-p',
            '--port',
            nargs='?',
            type=int,
            default=1883,
            help="Port where MQTT server is running")
    parser.add_argument(
            '--debug',
            action='store_true',
            help="run debug clients")
    return parser


if __name__ == "__main__":
    parser = build_arguments_parser()
    args   = parser.parse_args()
    server = GhoustServer(args.games, args.host, args.port)
    
    if args.debug:
        import ghoust_debug_clients
        debugclients = ghoust_debug_clients.ghoust_debug(num_clients=30)

    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()

    if args.debug:
        debugclients.stop()
