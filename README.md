# GHOUST

This repository is about the actual GAME

The game is written in python and runs on a raspberry pi.

There will be different falvours of games available.

The current state is one game implimentation of the "Last (wo)man standing" gametype.

Of course you can run it in your own network, on your laptop or on the internet.
 
The game itself is VERY modular.

The clients are subscribed to some MQTT itopics and the game receives messages and pushes messages to those MQTT topics.

A client has no idea that it is playing a game but is blinking leds, playing sounds, vibrating the motor... whatever the gameserver tells it to do.

