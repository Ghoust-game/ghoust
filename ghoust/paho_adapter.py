import ghoust
import importlib
import logging
from .player       import Player


class PahoAdapter:
    def __init__(self, host, port):
        self.host      = host
        self.port      = port
        self.keepalive = 10 
        self.clients   = dict()
        self.client    = None
        self.setup_logger()

    def setup_logger(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    # Connect to remote MQTT paho broker
    def connect(self):
        module = importlib.import_module("paho.mqtt.client")
        self.connect_with_module(module)

    # Connect with the given MQTT paho client module
    def connect_with_module(self, module):
        self.client = module.Client("GHOUST_SRV", clean_session=False)
        self.client.will_set("GHOUST/server/status", "EXIT")

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.client.connect(self.host, self.port, self.keepalive)

    # Publishing interface
    def publish(self, topic, message_string):
        self.client.publish(topic, message_string)

    # Starts processing
    def start(self):
        self.client.loop_forever()

    # Stops processing with paho broker
    def stop(self):
        self.client.loop_stop()

    def add_player(self, player, client):
        record = {
            "player": player,
            "client": client
        }
        player_id = player.id()
        self.clients.update({player_id: record})

    def find_record_by_player_id(self, player_id):
        if player_id in self.clients:
            return self.clients[player_id]
        else:
            return None

    def find_player_by_id(self, player_id):
        data = self.find_record_by_player_id(player_id)
        if data:
            return data["player"]
        else:
            return None

    def delete_player(self, player):
        self.clients.pop(player.id())
        player.set_game(None)
        del player

    def find_client_for_player(self, player):
        record = self.find_record_by_player_id(player.id())
        return record["client"]

    # callback for paho mqtt, when connecting
    def on_connect(self, client, userdata, flags, rc):
        self.logger.info("Connected with result code " + str(rc))

        client.subscribe("GHOUST/server/changegame")
        client.subscribe("GHOUST/clients/+/status")
        client.subscribe("GHOUST/clients/+/events/button")
        client.subscribe("GHOUST/clients/+/events/accelerometer")
        client.subscribe("GHOUST/clients/+/events/gestures")

    def handle_gamechange(self, game_list):
        self.server.setgames(game_list)

    def handle_client(self, client, player_id, payload):
        if payload == "CONNECT":
            player = Player(player_id, self)
            self.add_player(player, client)
            if self.count_games() == 1:
                player.set_game(self.find_game_by_id(0))
        if payload == "DISCONNECT":
            if player_id in self.clients.keys():
                player = self.find_player_by_id(player_id)
                self.delete_player(player)

    def find_game_by_id(self, game_id):
        return self.server.find_game_by_id(game_id)

    def count_games(self):
        return self.server.count_games()

    def count_players(self):
        return len(self.clients.keys())

    def handle_button(self, player_id, payload):
        # dirty...
        player = self.find_player_by_id(player_id)
        if payload == "CLICK" and player.selected_game():
            player.select_nextgame()
        elif payload == "LONGPRESS":
            if player.selected_game():
                player.set_game(player.selected_game())
            else:
                player.reset_game()
        else:
            player.game._on_button(player, payload)

    def handle_accelerometer(self, player_id, payload):
        player = self.find_player_by_id(player_id)
        player.game._on_accelerometer(player, payload)

    def handle_gestures(self, player_id, payload):
        player = self.find_player_by_id(player_id)
        player.game._on_gestures(player, payload)

    def handle_player_message(self, client, topic, player_id, payload):
        if topic == "status":
            self.handle_client(client, player_id, payload)
        elif topic == "events/button":
            self.handle_button(player_id, payload)
        elif topic == "events/accelerometer":
            self.handle_accelerometer(player_id, payload)
        elif topic == "events/gestures":
            self.handle_gestures(player_id, payload)

    # callback for paho mqtt, for receiving a message
    def on_message(self, client, userdata, msg):
        topic   = msg.topic.split("/")
        payload = str(msg.payload, "utf-8")

        if len(topic) < 3:
            self.logger.error("msg tree too short! debug: " + msg.topic + " " + payload)
            return

        if topic[1] == "server":
            if topic[2] == "changegame":
                self.handle_gamechange(payload.split(","))
            return

        player_id = topic[2]
        self.handle_player_message(client, "/".join(topic[3:]), player_id, payload)

