import importlib

from socket         import error as socket_error


class Server:
    def __init__(self, client_adapter, join_mode="auto"):
        self.client = client_adapter
        self.client.server = self
        self.join_mode = join_mode

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

    def find_autojoin_game(self):
        return self.games[0]

    def maybe_join_games(self):
        if self.join_mode == "auto":
            for _, player in self.find_all_players():
                player.set_game(self.find_autojoin_game())

    def filter_games_list(self, games_list):
        if self.join_mode == "auto":
            return game_list[:1]
        else:
            return game_list

    def load_games(self, game_list):
        # start new games
        game_list = self.filter_games_list(games_list)
        for i, game_name in enumerate(game_list):
            module     = importlib.import_module("ghoust.games." + game_name)
            game_class = getattr(module, game_name)
            game       = game_class(i)
            game.setup()
            self.games.append(game)
        self.maybe_join_games()

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
