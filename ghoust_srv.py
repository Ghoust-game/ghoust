#!/usr/bin/env python3

import importlib
import time
import argparse

from ghoust.server import Server as GhoustServer
from threading     import Timer


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
    server = GhoustServer(args.host, args.port, PahoAdapter)
    server.load_games(args.games)
    
    if args.debug:
        import ghoust_debug_clients
        debugclients = ghoust_debug_clients.ghoust_debug(num_clients=30)

    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()

    if args.debug:
        debugclients.stop()
