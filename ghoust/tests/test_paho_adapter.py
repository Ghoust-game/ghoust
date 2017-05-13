import unittest

from ghoust import PahoAdapter

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

    def will_set(self, topic, payload=None, qos=0, retain=False):
        self.topic = topic
        self.payload = payload
        self.qos = qos
        self.retain = retain

    def connect(self, host, port, keepalive):
        self.host = host
        self.port = port
        self.keepalive = keepalive

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
    def setUp(self):
        self.used_adapter = PahoAdapter("127.0.0.1", 123)
        self.fake_module  = FakePahoModule()

    def created_clients(self):
        return self.fake_module.created_clients

    def test_connection(self):
        self.used_adapter.connect_with_module(self.fake_module)

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



if __name__ == '__main__':
    unittest.main()
