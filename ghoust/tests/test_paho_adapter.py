import unittest

from ghoust import PahoAdapter

class FakePahoModule:
    def __init__(self):
        self.client_id     = None
        self.clean_session = None
        self.userdata      = None
        self.protocol      = None
        self.transport     = None

        self.on_message    = None
        self.on_connect    = None
        self.keepalive     = None
        self.host          = None
        self.port          = None

        self.on_message = None
        self.on_connect = None
        self.topic = None
        self.payload = None
        self.qos = None
        self.retain = None

    def connect(self, host, port, keepalive):
        self.host = host
        self.port = port
        self.keepalive = keepalive

    def will_set(self, topic, payload=None, qos=0, retain=False):
        self.topic = topic
        self.payload = payload
        self.qos = qos
        self.retain = retain

    def Client(self, client_id="", clean_session=True, userdata=None, protocol="MQTTv311", transport="tcp"):
        self.client_id     = client_id
        self.clean_session = clean_session
        self.userdata      = userdata
        self.protocol      = protocol
        self.transport     = transport
        return self

class PahoAdapterTestCase(unittest.TestCase):
    def setUp(self):
        self.used_adapter = PahoAdapter("127.0.0.1", 123)
        self.fake_module  = FakePahoModule()

    def test_connection(self):
        self.used_adapter.connect_with_module(self.fake_module)

        self.assertEqual("GHOUST_SRV", self.fake_module.client_id)
        self.assertEqual(False, self.fake_module.clean_session)
        self.assertEqual(None, self.fake_module.userdata)
        self.assertEqual("tcp", self.fake_module.transport)

        self.assertEqual(10, self.fake_module.keepalive)

        self.assertEqual(123, self.fake_module.port)
        self.assertEqual("127.0.0.1", self.fake_module.host)

        self.assertEqual("GHOUST/server/status", self.fake_module.topic)
        self.assertEqual("EXIT", self.fake_module.payload)




if __name__ == '__main__':
    unittest.main()
