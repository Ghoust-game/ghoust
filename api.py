"""
API for the web frontend for the ghoust game Python service.

See also https://www.python-boilerplate.com/flask
"""
import os
import threading

from flask import Flask, jsonify, send_file, request
from flask_cors import CORS


class API:
    # `ghoust` is a reference to the main Ghoust object,
    # in order to access data from the handlers
    ghoust = None
    app = None

    def __init__(self, ghoust):
        self.thread = None
        self.ghoust = ghoust
        self.app = self.create_app()

    def create_app(self):
        """ Creates the Flask app """
        app = Flask(__name__)
        app.config.update(dict(DEBUG=False))

        # Setup cors headers to allow all domains
        CORS(app)

        # Definition of the routes.
        @app.route("/")
        def hello_world():
            return "Hello World"

        @app.route("/ghoust")
        def ghoust():
            return str(self.ghoust)

        return app

    def _run(self):
        port = int(os.environ.get("GHOUST_API_PORT", 8080))
        self.app.run(host="0.0.0.0", port=port)

    def run(self, debug=True, threaded=False):
        if threaded and debug:
            raise Exception("API cannot run threaded with debug=True")

        if debug:
            self.app.config.update(dict(DEBUG=debug))
            self._run()

        elif threaded:
             thread = threading.Thread(target=self._run)
             thread.daemon = True
             thread.start()
             return thread


if __name__ == "__main__":
    api = API("123")
    api.run()

    # thread = api.run(threaded=True, debug=False)
    # print("thread", thread)
    # thread.join()
