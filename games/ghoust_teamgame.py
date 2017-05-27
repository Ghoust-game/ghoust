#!/usr/bin/env python3

from ghoust_srv import filter_clients
from threading import Timer
import time
import random
import colorsys




class ghoust_teamgame:

    def __init__(self, number, join_mode="auto"):
        print("init")
        self.game_number = number
        self.players = dict()

        self.gameTimer = None
        self.pregameTimer = None
        self.endTimer = None
        self.gamestatus = "init"
        self.join_mode = join_mode

        self.out_thresh = 10
        self.warn_thresh = 8

        # configs
        self.pregame_t = 5 if self.join_mode != "auto" else 0
        self.game_t = 120
        self.end_t = 5

    def __str__(self):
        return "ghoust_teamgame (game number {})".format(self.game_number)

    def check_win(self):
        # count alive
        lteams = []
        for team in self.players_team:
            l = 0
            for p in team:
                l += 1 if p.status == "GO" else 0
            if l != 0:
                lteams.append(team)

        if len(lteams) == 1:
            self.end_game(team=lteams[0])
        if len(lteams) == 0:
            print("todo all dead before checkwin")
            self.end_game()

    def pre_game(self):
        print("############# pregame (", self.game_number, ") ##############")
        self.gamestatus = "pregame"
        self.endTimer = None

        # all clients in inactive mode
        for _, e in list(self.players.items()):

            if self.join_mode == "auto":
                e.join()
            else:
                e.leave()
        self.pre_game_timer()

    def pre_game_timer(self):
        if self.gamestatus != "pregame":
            return
        
        # configure start timer if 2 or more clients joined
        if len(filter_clients(self.players, status="ACTIVE")) > 1:
            self.start_timers(pregame=True)
        else:
            self.stop_timers(pregame=True)

    def start_game(self):
        print("############# game (", self.game_number, ") ##############")
        self.gamestatus = "game"
        self.stop_timers(pregame=True)

        active = filter_clients(self.players, status="ACTIVE")

        # make teams from players
        # TODO more teams for larger crowds
        self.n_teams = 2

        # split fairly into n randomized teams
        random.shuffle(active)
        self.players_team = [active[i::self.n_teams]
                             for i in range(self.n_teams)]
        print(self.players_team)
        for i, l in enumerate(self.players_team):
            color = colorsys.hsv_to_rgb(i * 1.0 / self.n_teams, 0.5, 0.5)
            color = tuple(int(x * 1023) for x in color)
            for p in l:
                p.setteam(i, color=color)
                p.start()
                p.set_accel_thresh(self.out_thresh, self.warn_thresh)

        # set timer
        self.start_timers(game=True)

    def end_game(self, team=None, timeout=False):
        print("############# endgame (", self.game_number, ") ##############")
        self.gamestatus = "endgame"
        if team != None:
            print(team)
            [p.win() for p in team]
        elif timeout != False:
            for e in filter_clients(self.players, status="GO"):
                e.timeout()
        else:
            for _, e in list(self.players.items()):
                e.abort()
        self.stop_timers(game=True)
        self.start_timers(end=True)

    def start_timers(self, pregame=False, game=False, end=False):
        if self.pregameTimer == None and pregame:
            self.pregameTimer = Timer(self.pregame_t, self.start_game)
            self.pregameTimer.start()
        if self.gameTimer == None and game:
            self.gameTimer = Timer(
                self.game_t, self.end_game, kwargs={"timeout": True})
            self.gameTimer.start()
        if self.endTimer == None and end:
            self.endTimer = Timer(self.end_t, self.pre_game)
            self.endTimer.start()

    def stop_timers(self, pregame=False, game=False, end=False):
        if self.pregameTimer != None and pregame:
            self.pregameTimer.cancel()
            del self.pregameTimer
            self.pregameTimer = None
        if self.gameTimer != None and game:
            self.gameTimer.cancel()
            del self.gameTimer
            self.gameTimer = None
        if self.endTimer != None and end:
            self.endTimer.cancel()
            del self.endTimer
            self.endTimer = None

    ##### functions called by ghoust_srv #####

    def _on_accelerometer(self, p, value):
        if self.gamestatus == "game" and p.status == "GO":
            if "WARNSHOCK" in value:
                p.warn()
            elif "OUTSHOCK" in value:
                p.out()
                self.check_win()

    def _on_button(self, p, clicktype):

        # join current round
        if self.gamestatus == "pregame" and clicktype == "CLICK" and self.join_mode != "auto":
            if p.status == "INACTIVE":
                p.join()
            elif p.status == "ACTIVE":
                p.leave()
            self.pre_game_timer()

    def _on_gestures(self, p, value):
        pass  # not used

    def _join(self, pid, p):
        self.players.update({pid: p})
        if self.join_mode == "auto":
            p.join()
        self.pre_game_timer()

    def _leave(self, pid, p):
        self.players.pop(pid)

        if self.gamestatus == "game":
            self.check_win()
        elif self.gamestatus == "pregame":
            self.pre_game_timer()

    def setup(self):
        self.gamestatus = "setup"
        self.pre_game()

    def stop(self):
        self.stop_timers(True, True, True)
