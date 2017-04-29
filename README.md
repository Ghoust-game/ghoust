#GHOUST

This repository is about the actual GAME

There will be different variations of the game.

The current state is one game implimentation of the "Last (wo)man standing" gametype.

Of course you can run this on your own network, your laptop or on the internet.
 
The game itself is VERY modular.

The clients are subscribed to some MQTT topics and the game receives messages and pushes messages to those MQTT topics.

A client has no idea that it is playing a game but is blinking leds, playing sounds, vibrating the motor... whatever the gameserver tells it to do.


Want to know more?
Check out the [wiki](https://github.com/Ghoust-game/ghoust/wiki)
