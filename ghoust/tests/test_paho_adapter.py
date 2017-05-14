import unittest
import logging
import io

from ghoust   import PahoAdapter, Server

class FakeMessage:
    def __init__(self, topic, payload):
        self.topic = topic
        self.payload = bytes(payload, "utf-8")

class FakePahoClient:
    def __init__(self, client_id, clean_session, userdata, protocol, transport):
        self.client_id     = client_id
        self.clean_session = clean_session
        self.userdata      = userdata
        self.protocol      = protocol
        self.transport     = transport
        self.on_message = None
        self.on_connect = None
        self.topic = None
        self.payload = None
        self.subscriptions = []
        self.published = dict()
        self.loop_forever_was_called = False
        self.loop_stop_was_called = False

    def subscribe(self, topic):
        self.subscriptions.append(topic)

    def will_set(self, topic, payload=None, qos=0, retain=False):
        self.topic = topic
        self.payload = payload
        self.qos = qos
        self.retain = retain

    def connect(self, host, port, keepalive):
        self.host = host
        self.port = port
        self.keepalive = keepalive

    def loop_forever(self):
        self.loop_forever_was_called = True

    def loop_stop(self):
        self.loop_stop_was_called = True

    def publish(self, topic, payload):
        if topic in self.published:
            self.published[topic].append(payload)
        else:
            self.published[topic] = [payload]


class FakePahoModule:
    def __init__(self):
        self.qos = None
        self.retain = None
        self.created_clients = []

    def Client(self, client_id="", clean_session=True, userdata=None, protocol="MQTTv311", transport="tcp"):
        client = FakePahoClient(client_id, clean_session, userdata, protocol, transport)
        self.created_clients.append(client)
        return client

class PahoAdapterTestCase(unittest.TestCase):
    def setup_logging(self):
        self.stream = io.StringIO()
        self.handler = logging.StreamHandler(self.stream)
        self.logger = logging.getLogger("paho_adapter")
        self.logger.setLevel(logging.INFO)
        root_logger = logging.getLogger()
        for i in root_logger.handlers:
            root_logger.removeHandler(i)
        self.logger.addHandler(self.handler)
        self.used_adapter.logger = self.logger

    def setUp(self):
        self.used_adapter = PahoAdapter("127.0.0.1", 123)
        self.setup_logging()
        self.fake_module  = FakePahoModule()

    def logger_content(self):
        return self.stream.getvalue()

    def created_clients(self):
        return self.fake_module.created_clients

    def do_connection(self):
        self.used_adapter.connect_with_module(self.fake_module)

    def test_creating_connection(self):
        self.do_connection()

        self.assertEqual(1, len(self.fake_module.created_clients))

        client = self.created_clients()[0]
        self.assertEqual(None, client.userdata)
        self.assertEqual(False, client.clean_session)
        self.assertEqual("GHOUST_SRV", client.client_id)
        self.assertEqual("tcp", client.transport)

        self.assertEqual("GHOUST/server/status", client.topic)
        self.assertEqual("EXIT", client.payload)
        self.assertEqual(10, client.keepalive)

        self.assertEqual(123, client.port)
        self.assertEqual("127.0.0.1", client.host)

        self.assertEqual(self.used_adapter.on_message, client.on_message)
        self.assertEqual(self.used_adapter.on_connect, client.on_connect)

    def paho_client(self):
        return self.created_clients()[0]

    def test_start_client(self):
        self.do_connection()
        self.assertEqual(False, self.created_clients()[0].loop_forever_was_called)
        self.used_adapter.start()
        self.assertEqual(True, self.created_clients()[0].loop_forever_was_called)

    def test_stop_client(self):
        self.do_connection()
        self.used_adapter.start()
        self.assertEqual(False, self.created_clients()[0].loop_stop_was_called)
        self.used_adapter.stop()
        self.assertEqual(True, self.created_clients()[0].loop_stop_was_called)

    def test_publishing_payload(self):
        self.do_connection()
        self.assertEqual(0, len(self.paho_client().published.keys()))
        self.used_adapter.publish("GHOUST/server/status", "ACTIVE")

        self.assertEqual(1, len(self.paho_client().published.keys()))

        self.assertEqual(["ACTIVE"], self.paho_client().published["GHOUST/server/status"])

    def test_on_connect_subscriptions(self):
        self.do_connection()
        self.used_adapter.start()
        self.used_adapter.on_connect(self.paho_client(), None, None, 10)

        self.assertEqual(5, len(self.paho_client().subscriptions))
        self.assertEqual("GHOUST/server/changegame", self.paho_client().subscriptions[0])
        self.assertEqual("GHOUST/clients/+/status", self.paho_client().subscriptions[1])
        self.assertEqual("GHOUST/clients/+/events/button", self.paho_client().subscriptions[2])
        self.assertEqual("GHOUST/clients/+/events/accelerometer", self.paho_client().subscriptions[3])
        self.assertEqual("GHOUST/clients/+/events/gestures", self.paho_client().subscriptions[4])
        
        self.assertEqual("Connected with result code 10\n", self.logger_content())
    
    def test_should_handle_throw_an_error_on_short_message(self):
        self.do_connection()
        self.used_adapter.start()

        message = FakeMessage("GHOUST", "stuff")
        self.used_adapter.on_message(self.paho_client(), None, message)
        expected_error = "msg tree too short! debug: " + \
                         message.topic + " " + \
                         str(message.payload, "utf-8") + "\n"

        self.assertEqual(expected_error, self.logger_content())

    def test_should_handle_changegame_event(self):
        self.do_connection()
        server = Server(self.used_adapter)

        message = FakeMessage("GHOUST/server/changegame", "ghoust_game")
        self.used_adapter.on_message(self.paho_client(), None, message)

    def test_should_handle_client_connect_event(self):
        self.do_connection()
        server = Server(self.used_adapter)

        message = FakeMessage("GHOUST/clients/1/status", "CONNECT")
        self.used_adapter.on_message(self.paho_client(), None, message)

        self.assertEqual(1, self.used_adapter.count_players()) 

        player = self.used_adapter.find_player_by_id("1")
        self.assertIsNotNone(player)
        self.assertEqual("1", player.id())

    def register_player(self):
        self.do_connection()
        self.server = Server(self.used_adapter)

        message = FakeMessage("GHOUST/server/changegame", "ghoust_game")
        self.used_adapter.on_message(self.paho_client(), None, message)

        message = FakeMessage("GHOUST/clients/1/status", "CONNECT")
        self.used_adapter.on_message(self.paho_client(), None, message)
        self.assertEqual(1, self.used_adapter.count_players()) 

        self.player = self.used_adapter.find_player_by_id("1")

    def test_should_handle_button_click(self):
        self.register_player()

        message = FakeMessage("GHOUST/clients/1/events/button", "CLICK")
        self.used_adapter.on_message(self.paho_client(), None, message)



if __name__ == '__main__':
    unittest.main()
