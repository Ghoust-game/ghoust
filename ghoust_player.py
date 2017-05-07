#!/usr/bin/env python

class Player:
    def __init__(self, pid, mqtt_client, name="", game=None):
        self.pid = pid
        self.client = mqtt_client
        self.team = 0
        self.status = "SELECT_GAME"
        self.str = "GHOUST/clients/{0}".format(self.pid)
        self.game = game
        self.select_game(0)
        self.go_color = [0, 1023, 0]
        self.led_timer = None
        # can be used to store game specific parameters in the player object
        self.game_params = dict()

    def __repr__(self):
        return str(self.pid)

    def setname(self, name):
        self.name = name

    def setteam(self, n, color = None):
        print(self.pid + ": team " + str(n))
        self.team = n
        if color != None:
            self.go_color = color


    def warn(self):
        print(self.pid + ": warn")

        # vibrate and light softly
        #self._config("led", preset = 2)
        self._config("led", val=[1023, 1023, 0], duration_led=500)
        self._config("motor", preset=2)
        #self._config("buzzer", preset = 2)

    def out(self):
        print(self.pid + ": out")
        self.status = "INACTIVE"
        # reset go color to green
        self.go_color = [0, 1023, 0]
    
        # vibrate hard, light red, set inactive
        self._config("led", val=[1023, 0, 0])
        self._config("motor", val=[1023, 3000])
        self._config("buzzer", preset=3)


    def timeout(self):
        print(self.pid + ": timeout")
        self.status = "INACTIVE"

        # timeout action
        self._config("led", val=[1023, 1023, 0], duration_led=1000)
        self._config("motor", preset=1)

    def abort(self):
        print(self.pid + ": abort")
        self.status = "INACTIVE"
        # light orange, weirdly vibrate
        self._config("led", val=[1023, 1023, 0], duration_led=1000)
        self._config("motor", preset=1)

    def join(self):
        print(self.pid + ": join game ", self.game.game_number)
        self.status = "ACTIVE"
        # action?
        self._config("motor", preset=1)
        self._config("led", val=[0,0,0])

    def leave(self):
        print(self.pid + ": leave ", self.game.game_number)
        self.status = "INACTIVE"
        # action ?
        self._config("motor", preset=1)
        self._config("led", val = [0,0,0])
        #self._config("buzzer", preset = 1)

    def start(self):
        print(self.pid + ": start")
        self.status = "GO"
        self._config("motor", val=[1023, 750])
        self._config("led", val=self.go_color)
        self._config("buzzer", preset=2)

    def win(self):
        print(self.pid + ": win")
        # vibrate partily, light green
        self._config("motor", preset=3)
        self._config("led", preset=1)
        self._config("buzzer", preset=1)

    def select_game(self, n):
        self.select_game_n = n
        # print "player ",self.pid,": select game, flash ",n
        # TODO flash gamenumber periodically

    def set_accel_thresh(self, out, warn):

        self.client.publish(self.str + "/config/accel_out", str(out))
        self.client.publish(self.str + "/config/accel_warn", str(warn))

    def set_game(self, game_p):
        if self.game == game_p:
            return

        if self.game != None:
            self.game._leave(self.pid, self)

        self.game = game_p
        self.game_params = dict()
        if game_p != None:
            self.status = "INACTIVE"
            self.game._join(self.pid, self)
        else:
            self.status = "SELECT_GAME"

    ############# raw functions for low level access ##############
    # buzzer, vibro val: [0-1023, 0-], [frequency (hz), duration (ms)]
    # led val: [0-1023, 0-1023, 0-1023, 0-inf], [r, g, b, duration (ms)]
    # parameter: ["motor", "buzzer", "led"]
    # duration_led: ms, only used for value input
    def _config(self, parameter, val=None, preset=None, duration_led=None):
        if parameter not in ["motor", "buzzer", "led"]:
            print("parameter not valid")
            return
        topic = self.str + "/config/{}".format(parameter)

        if preset != None:
            if not (0 <= int(preset) <= 9):
                print("vibrate preset not in range")
            self.client.publish(topic, "PRESET:{}".format(preset))

        if val != None:
            if (not (0 <= val[0] <= 1023) or
                    (parameter != 'led' and not(0 <= val[1])) or
                    (parameter == 'led' and not(0 <= val[1] <= 1023)) or
                    (parameter == 'led' and not(0 <= val[2] <= 1023))):
                print("config values not in range")
            fstring = "RAW:{:04},{:04}"
            if parameter == "led":
                fstring = "RAW:{:04},{:04},{:04}"
                if duration_led != None:
                    fstring = "RAW:{:04},{:04},{:04},{:04}"
                    val.append(duration_led)
            self.client.publish(topic, fstring.format(*val))

