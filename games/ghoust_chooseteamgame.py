#!/usr/bin/env python3

from ghoust_srv import filter_clients
from threading import Timer
import time
import random
import colorsys



# TODO
# players in inactive mode can choose team by gesture, every gesture change registers for different team
# player has default team if no gesture is chosen
# show team color in inactive mode, and during game

class ghoust_chooseteamgame:

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
        self.pregame_t = 20
        self.game_t = 120
        self.end_t = 5

        # teamconfigs
        # team 0 = no team yet
        self.t0_color = [0, 0, 0]
        # team 1 = flat
        self.t1_color = [968, 0, 904]
        # team 2 = upside down
        self.t2_color = [0, 0, 968]



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
            e.setteam(0)
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
            
        team0 = [x for x in active if x.team == 0]
        team1 = [x for x in active if x.team == 1]
        team2 = [x for x in active if x.team == 2]
        
        # distribute team 0 (undecided) to balance teams if possible 
        if len(team0) != 0:
            random.shuffle(team0)
            balance = len(team1) - len(team2)
            random_team = random.choice([-1, 1])

            for x in team0:
                if balance == 0:
                    # randomly assign to one of two teams
                    random_team *= -1
                    balance += random_team

                if balance < 0:
                    x.setteam(1, self.t1_color)
                    team1.append(x)
                    balance += 1
                elif balance > 0:
                    x.setteam(2, self.t2_color)
                    team2.append(x)
                    balance -= 1
                
        self.players_team = [team1, team2]
        for i, l in enumerate(self.players_team):
            for p in l:
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
        if self.gamestatus == "pregame" and "OUTSHOCK" in value:
            t = p.team
            if t == 0:
                p.setteam(1, self.t1_color)
                p._config('led', self.t1_color)
            elif t == 1:
                p.setteam(2, self.t2_color)
                p._config('led', self.t2_color)
            elif t == 2:
                p.setteam(0, [0,0,0])
                p._config('led', [0,0,0])


    def _on_button(self, p, clicktype):

        # join current round
        if self.gamestatus == "pregame" and clicktype == "CLICK" and self.join_mode != "auto":
            if p.status == "INACTIVE":
                p.join()
            elif p.status == "ACTIVE":
                p.leave()
            self.pre_game_timer()

    def _on_gestures(self, p, value):
        if self.gamestatus == "pregame":
            if value == "PORTRAIT_DOWN":
                p.setteam(1, self.t1_color)
                p._config('led', val= self.t1_color)
            elif value != "PORTRAIT_UP":
                p.setteam(2, self.t2_color)
                p._config('led', val= self.t2_color)
            else:
                p.setteam(0, [0,0,0])
                p._config('led', val= self.t0_color)

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
