#!/usr/bin/env python

from ghoust_srv import filter_clients
from threading import Timer
from thread import start_new_thread
import random 
import time
import colorsys

from IPython import embed

# TODO timers
#   winblink should finish before pregame starts because pregame deletes color argument, makes winblink fail



## one or two teams need to sort themselves to blink in a row
## first team in a row clicks all buttons, users need to keep score themselves
## 4-7 players: single team
## 8-inf players: two teams

class sort_game:
    
    def __init__(self, number):
        print "init"
        
        self.game_number = number
        self.players = dict()
        self.players_team = list()
        
        self.gameTimer = None
        self.pregameTimer = None
        self.endTimer = None
        self.blinkTimer = None
        self.winblinkTimer = None
        self.gamestatus = "init"
        self.n_teams = 1
        
        # configs
        self.pregame_t = 5
        self.game_t = 10
        self.end_t = 10
        self.blink_t = 2
        self.winblink_t = 3

    def __str__(self):
        return  "sort_game (game number {})".format(self.game_number)
    
    def check_win(self):
        # check if everyone of a single team clicked
        for l in self.players_team:
            count = len(l)
            for p in l:
                count -= p.game_params["clicked"]
            if count == 0:
                self.end_game(win_team = l)
                print self.game_number, " one team called win condition"
                break


    def pre_game(self):
        print "############# pregame (",self.game_number,") ##############"
        self.gamestatus = "pregame"
        self.stop_timers(end=True, winblink=True)

        # all clients in inactive mode
        for _,e in self.players.items():
            e.game_params = dict()
            e.leave()

    def pre_game_timer(self):
        # configure start timer if 4 or more clients joined
        if len(filter_clients(self.players, status = "ACTIVE")) >= 4 :
            self.start_timers(pregame=True)
        else:
            self.stop_timers(pregame=True)

    def start_game(self):
        print "############# game (",self.game_number,") ##############"
        self.gamestatus = "game"
        self.pregameTimer = None
        
        active = filter_clients(self.players, status="ACTIVE")

        # make teams from players
        self.n_teams = 1 if len(active) < 8 else 2
        
        # split fairly into n randomized teams
        random.shuffle(active)
        self.players_team = [active[i::self.n_teams] for i in xrange(self.n_teams)]
        for i,l in enumerate(self.players_team):
            color = colorsys.hsv_to_rgb(i*1.0/self.n_teams, 0.5, 0.5)
            color = tuple(int(x*1023) for x in color)
            for p in l:
                p.game_params.update({"clicked":0, "team":i, "color":color})
                p.start()
                    
        # set timer
        self.start_timers(game=True, blink=True)

    def end_game(self, win_team = [], abort=False, timeout=False):
        print "############# endgame (",self.game_number,") ##############"
        self.gamestatus = "endgame"
        
        

        if timeout == True:
            for e in filter_clients(self.players, status="GO"):
                e.timeout()
        elif abort == True:
            for e in self.players:
                e.abort()
        else:    # winblink to let players check if they are correct
            self.win_blink(win_team)

        self.stop_timers(game=True, blink=True)
        self.start_timers(end=True)

    def blink_teams(self):
        # blink teams in order
        for i,t in enumerate(self.players_team):
            start_new_thread(self.team_blink, (t, 0.5))
        self.start_timers(blink=True)

    
    def win_blink(self, t):
        self.win_team = t
        start_new_thread(self.team_blink, (t, 0.25))
        self.winblink_t = len(t) * 0.25 + 1
        self.start_timers(winblink=True)


    def team_blink(self, t, delay):
        for p in t:
            # TODO led blink only for amount of time...
            p._config("led", val=p.game_params["color"])
            time.sleep(delay)



    def start_timers(self, pregame=False, game=False, end=False, blink=False, winblink=False):
        if self.pregameTimer == None and pregame:
            self.pregameTimer = Timer(self.pregame_t, self.start_game)
            self.pregameTimer.start()
        if self.gameTimer == None and game:
            self.gameTimer = Timer(self.game_t, self.end_game, kwargs={"timeout":True})
            self.gameTimer.start()
        if self.endTimer == None and end:
            self.endTimer = Timer(self.end_t, self.pre_game)
            self.endTimer.start()
        if self.blinkTimer == None and blink:
            self.blinkTimer = Timer(self.blink_t, self.blink_teams)
            self.blinkTimer.start()
        if self.winblinkTimer == None and winblink:
            self.winblinkTimer = Timer(self.winblink_t, self.win_blink, args=[self.win_team])
            self.winblinkTimer.start()

    def stop_timers(self, pregame=False, game=False, end=False, blink=False, winblink=False):
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
        if self.blinkTimer != None and blink:
            self.blinkTimer.cancel()
            del self.blinkTimer
            self.blinkTimer = None
        if self.winblinkTimer != None and winblink:
            self.winblinkTimer.cancel()
            del self.winblinkTimer
            self.winblinkTimer = None

    ##### functions called by ghoust_srv #####
    
    def _on_accelerometer(self, p, value):
        pass
    
    def _on_button(self, p, clicktype):

        # join current round
        if self.gamestatus == "pregame" and clicktype == "CLICK":
            if p.status == "INACTIVE":
                p.join()
            elif p.status == "ACTIVE":
                p.leave()
            self.pre_game_timer()
        elif self.gamestatus == "game"  and clicktype == "CLICK":
            p.game_params.update({"clicked" : 1})
            self.check_win()
    
    def _on_gestures(self, p):
        pass
    
    def _join(self, pid, p):
        self.players.update({ pid : p })
        self.pre_game_timer()
        

    def _leave(self, pid, p):
        self.players.pop(pid)
        self.players_team[p.game_params["team"]].pop(p)
        
        if self.gamestatus == "game":
            self.check_win()
        elif self.gamestatus == "pregame":
            self.pre_game_timer()
    
    def setup(self):
        self.gamestatus = "setup"
        self.pre_game()
    
    def stop(self):
        self.stop_timers(True, True, True, True, True)
    
