import ghoust
import paho.mqtt.client as mqtt

class PahoAdapter:
    def __init__(self, host, port):
        self.host    = host
        self.port    = port
        self.keepalive = 10 

        self.clients = dict()
        self.client  = mqtt.Client("GHOUST_SRV", clean_session=False)
        self.client.will_set("GHOUST/server/status", "EXIT")

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    # Connect to remote MQTT paho broker
    def connect(self):
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

    # paho mqtt callbacks
    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code " + str(rc))

        client.subscribe("GHOUST/server/changegame")
        client.subscribe("GHOUST/clients/+/status")
        client.subscribe("GHOUST/clients/+/events/button")
        client.subscribe("GHOUST/clients/+/events/accelerometer")
        client.subscribe("GHOUST/clients/+/events/gestures")

    def add_player(self, player, client):
        record = {
            "player": player,
            "client": client
        }
        player_id = player.id
        self.clients.update({player_id: record})

    def find_record_by_player_id(self, player_id):
        return self.clients[player_id]

    def find_player_by_id(self, player_id):
        data = self.find_record_by_player_id(player_id)
        return data["player"]

    def delete_player(self, player):
        self.clients.pop(player.id)
        player.set_game(None)
        del player

    def find_client_for_player(self, player):
        record = self.find_record_by_player_id(player.id)
        return record["client"]

    def on_message(self, client, userdata, msg):
        topic   = msg.topic.split("/")
        payload = str(msg.payload)
        if len(topic) < 3:
            print("msg tree too short! debug: " + msg.topic + " " + payload)
            return

        if topic[1] == "server":
            if topic[2] == "changegame":
                self.server.setgames(payload.split(","))
            return

        player_id = topic[2]
        subtree   = topic[3]
        if subtree == "status":
            if payload == "CONNECTED":
                player = Player(player_id, self)
                self.add_player(player, client)
                if len(self.games) == 1:
                    player.set_game(self.games[0])

            elif payload == "DISCONNECTED" and self.clients.has_key(player_id):
                player = self.find_player_by_id(player_id)
                self.delete_player(player)

        elif subtree == "events":
            # pass message to game engine callbacks
            elem   = topic[4]
            player = self.find_player_by_id(player_id)

            if player.status == "SELECT_GAME":
                if elem == "button":
                    if payload == "CLICK":
                        # dirty...
                        player.select_game(
                            (player.select_game_n + 1) % len(self.games))
                    elif payload == "LONGPRESS":
                        player.set_game(self.games[player.select_game_n])
            else:
                if elem == "button":
                    # Leave game
                    if payload == "LONGPRESS" and len(self.games) > 1:
                        player.set_game(None)
                    else:    # let game know of button press
                        player.game._on_button(player, payload)
                elif elem == "accelerometer":
                    player.game._on_accelerometer(player, payload)
                elif elem == "gestures":
                    player.game._on_gestures(player, payload)

