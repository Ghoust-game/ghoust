import importlib

from socket         import error as socket_error


class Server:
    def __init__(self, client_adapter):
        self.client = client_adapter
        self.client.server = self

        # config parameters
        self.max_games = 4

        # game modules
        self.games = []

    #### game functions ####
    def setgames(self, game_list):
        # stop old games
        self.stop_games()
        self.load_games(game_list)

    def find_game_by_id(self, game_id):
        return self.games[game_id]

    def count_games(self):
        return len(self.games)

    def stop_games(self):
        if self.count_games() > 0:
            for game in self.games:
                game.stop()
        self.games = []

    def load_games(self, game_list):
        # start new games
        for i, game_name in enumerate(game_list):
            module     = importlib.import_module("ghoust.games." + game_name)
            game_class = getattr(module, game_name)
            game       = game_class(i)
            game.setup()
            self.games.append(game)

    def stop(self):
        for game in self.games:
            game.stop()
        self.client.stop()

    def start(self):
        for i in range(3):
            try:
                self.client.connect()
                break
            except socket_error as e:
                print("socket.error: [{}] {}".format(e.errno, e.strerror))
                if i == 2:
                    raise e
                print("retrying after 10s")
                time.sleep(10)

        self.client.publish("GHOUST/server/status", "ACTIVE")
        self.client.start()
