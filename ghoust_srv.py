#!/usr/bin/env python
import time

import paho.mqtt.client as mqtt
import importlib
from threading import Timer


class Player:
    def __init__(self, pid, mqtt_client, name="", game=None):
        self.pid = pid
	self.client = mqtt_client
        self.team = 0
        self.status = "SELECT_GAME"
	self.basestring = "GHOUST/clients/{0}".format( self.pid )
        self.game = game
        self.select_game(0)
	self.led_timer = None        
        # can be used to store game specific parameters in the player object
        self.game_params = dict()
    
    def name(self, name):
        self.name = name

    def team(self, n):
        self.team = n

    def warn(self):
        print self.pid + ": warn"

        # vibrate and light softly
	#self._config("led", preset = 2)
	# yellow led
	self._config("led", val=[1023,1023,0000], duration_led=500)
	# // uncommented overflo
        #self._config("motor", preset = 2)
 
	#self._config("buzzer", preset = 2)

    def out(self):
        print self.pid + ": out"
        self.status = "INACTIVE"
        
	# vibrate hard, light red, set inactive
        self._config("led", val=[1023,0000,0000])
	self._config("motor", preset = 2)
	#self._config("led", preset = 1)
	self._config("buzzer", preset = 3)
    
    def timeout(self):
        print self.pid + ": timeout"
        self.status = "INACTIVE"
        
	# timeout action
	self._config("motor", preset = 1)
	self._config("led", preset = 1)
	self._config("led", val=[1023,1023,0], duration_led=1000)
	#self._config("buzzer", preset = 1)
	
    
    def abort(self):
        print self.pid + ": abort"
        self.status = "INACTIVE"
        # light orange, weirdly vibrate
	self._config("motor", preset = 1)
	#self._config("led", preset = 1)
	self._config("led", val=[1023,1023,0], duration_led=1000)
	#self._config("buzzer", preset = 1)
	

    def join(self):
        print self.pid + ": join game ",self.game.game_number
        self.status = "ACTIVE"
        # action?
	self._config("motor", preset = 1)
	self._config("led", preset = 1)
	#self._config("buzzer", preset = 1)

    def leave(self):
        print self.pid + ": leave ",self.game.game_number
        self.status = "INACTIVE"
        # action ?
	self._config("motor", preset = 1)
	self._config("led", preset = 1)
	#self._config("buzzer", preset = 1)
        
    def start(self):
        print self.pid + ": start"
        self.status = "GO"
	self._config("motor")
	#self._config("led")
	self._config("led", val=[0,1023,0])
	self._config("buzzer", preset=2)

    def win(self):
        print self.pid + ": win"
        # vibrate partily, light green
	self._config("led",preset = 1)
	#self._config("led", val=[0,1023,0], duration_led=5)
        self._config("motor",preset=3)
	self._config("buzzer", preset = 1)
            

    def select_game(self, n):
        self.select_game_n = n
        #print "player ",self.pid,": select game, flash ",n
        # TODO flash gamenumber periodically
    def set_accel_thresh(self, out, warn):
	
        self.client.publish(self.basestring+"/config/accel_out", str(out))
        self.client.publish(self.basestring+"/config/accel_warn", str(warn))

    def set_game(self, game_p):
        if self.game == game_p:
            return
        
        if self.game != None:
            self.game._leave(self.pid, self)
        
        self.game = game_p
        self.game_params = dict()
        print self.pid," set game:: ", str(game_p)
        if game_p != None:
            self.status = "INACTIVE"
            self.game._join(self.pid, self)
        else:
            self.status = "SELECT_GAME"
    
    ############# raw functions for low level access ##############
    # buzzer, vibro val: [0-1023, 0-1023], [duration (ms), frequency (hz)]
    # led val: [0-1023, 0-1023, 0-1023, 0-inf], [r, g, b, duration (ms)]
    # parameter: ["motor", "buzzer", "led"]
    # duration_led: ms, only used for value input
    def _config(self, parameter, val=None, preset=None, duration_led=None):
        if parameter not in ["motor", "buzzer", "led"]:
            print "parameter not valid"
            return
        topic = self.basestring +"/config/{}".format(parameter)
    
        if preset != None:
            if not (0 <= int(preset) <= 9):
                print "vibrate preset not in range"
            self.client.publish(topic, "PRESET:{}".format(preset))
        
        if val != None:
            if (not (0 <= val[0] <= 1023) or 
                not (0 <= val[1] <= 1023) or
                (parameter == "led" and not(0 <= val[2] <= 1023))): 
                print "config values not in range"
            fstring = "RAW:{:04},{:04}"
            if parameter == "led":
                fstring = "RAW:{:04},{:04},{:04}"
		if duration_led != None:
                	fstring = "RAW:{:04},{:04},{:04},{:04}"
			val.append(duration_led)

            self.client.publish(topic, fstring.format(*val))

            


class GHOUST:

    def __init__(self, game_list):
        
        self.clients = dict()
        
        self.client = mqtt.Client("GHOUST_SRV", clean_session=False)
        self.client.will_set("GHOUST/server/status", "EXIT")
        self.client._on_connect = self._on_connect
        self.client._on_message = self._on_message
        
        # config parameters
        self.max_games = 4
        
        # game modules
        self.games = []
        for i, g in enumerate(game_list):
            m = importlib.import_module("games."+g)
            C = getattr(m, g)
            self.games.append(C(i))

    #### game functions ####
    
    # buzzer, vibro val: [0-1023, 0-1023], [duration (ms), frequency (hz)]
    # led val: [0-1023, 0-1023, 0-10123], [r, g, b]
    # parameter: ["motor", "buzzer", "led"]

    def _game_config(self, game, parameter, val=None, preset=None):
        if not (0 <= game <= 4) or parameter not in ["motor", "buzzer", "led"]:
            print "game number or parameter not valid"
            return
        topic = "GHOUST/game/{}/{}".format(game, parameter)
    
        if preset != None:
            if not (0 <= int(preset) <= 9):
                print "vibrate preset not in range"
            self.client.publish(topic, "PRESET:"+ preset)
        
        if val != None:
            if (not (0 <= val[0] <= 1023) or 
                not (0 <= val[1] <= 1023) or
                (parameter == "led" and not(0 <= val[2] <= 1023))): 
                print "vibrate values not in range"
            fstring = "RAW:{:04},{:04}"
            if parameter == "led":
                fstring = "RAW:{:04},{:04},{:04}"
            self.client.publish(topic, fstring.format(*val))

    #### mqtt callbacks ####

    def _on_connect(self, client, userdata, flags, rc):
        print("Connected with result code " + str(rc))

        client.subscribe("GHOUST/clients/+/status")
        client.subscribe("GHOUST/clients/+/events/button")
        client.subscribe("GHOUST/clients/+/events/accelerometer")
        client.subscribe("GHOUST/clients/+/events/gestures")

    def _on_message(self, client, userdata, msg):
            topic = msg.topic.split("/")
            payload = str(msg.payload)
            if len(topic) < 4:
                    print("msg tree too short! debug: " +msg.topic + " " + payload)
                    return
            
            pid = topic[2]
            subtree = topic[3]
            if subtree == "status":
                    if payload == "CONNECTED":
                            
                            pobj = Player(pid, client)
                            self.clients.update({ pid : pobj })
                            if len(self.games) == 1 :
                                pobj.set_game(self.games[0])
				pobj.join()

                    elif payload == "DISCONNECTED" and self.clients.has_key(pid):
                            pobj = self.clients[pid]
                            self.clients.pop(pid)
                            pobj.set_game(None)

                            del pobj 

            elif subtree == "events":
                    # pass message to game engine callbacks
                    elem = topic[4]
                    pobj = self.clients[pid]
                    
                    if pobj.status == "SELECT_GAME":
                        if elem == "button":
                            if payload == "CLICK":
                                pobj.select_game((pobj.select_game_n + 1) % len(self.games)) # dirty...
                            elif payload == "LONGPRESS":
                                pobj.set_game( self.games[pobj.select_game_n] ) 
                    else:
                        if elem == "button":
                            if payload == "LONGPRESS" and len(self.games) > 1: # Leave game
                                pobj.set_game(None)
                            else:    # let game know of button press
                                pobj.game._on_button(pobj, payload)
                        elif elem == "accelerometer":
                            pobj.game._on_accelerometer(pobj, payload)
                        elif elem == "gestures":
                            pobj.game._on_gestures(pobj, payload)
            
    def stop(self):
        for g in self.games:
            g.stop()
        self.client.loop_stop()

    def run(self):
        self.client.connect("localhost", 1883, 60)
        self.client.publish("GHOUST/server/status", "ACTIVE")
        
        for g in self.games:
            g.setup()
        
        self.client.loop_forever()

#############################

def filter_clients(c, status=""):
    if status != "":
        return [e for _,e in c.items() if e.status == status]
    return []

if __name__ == "__main__":
    #import ghoust_debug_clients
    #debug = ghoust_debug_clients.ghoust_debug(num_clients=30)

    
    # TODO argparse
    #g = GHOUST(["ghoust_game", "ghoust_game"])
    g = GHOUST(["ghoust_game"])
    #g = GHOUST(["sort_game"])
    
    try:
        g.run()
    except KeyboardInterrupt:
        g.stop()


    #print "\n Cleaning up, stopping debug clients"
    #debug.stop()

