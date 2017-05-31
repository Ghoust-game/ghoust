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


## Getting started

    # Setup the environment and install dependencies
    $ virtualenv -p python3 venv
    $ . venv/bin/activate
    $ pip install -r requirements.txt

    # Start the game (make sure the MQTT broker is running)
    $ python ghoust_srv.py ghoust_game


### MQTT Broker / Mosquitto

The server requires a running MQTT broker (we use Mosquitto). The config file is in the `ghoust/raspberry`
repository under `/etc/mosquitto/mosquitto.conf`. You can start the broker like this:

    $ mosquitto -v ~/<your-path>/ghoust/raspberry/etc/mosquitto/mosquitto.conf


## Debugging on the Raspberry Pi

    # Make sure lighttpd is running
    $ sudo systemctl status lighttpd

    # See all MQTT messages
    $ mosquitto_sub -t "#" -v
