## Player Card Output

![](player_card_example.jpg)

## Overview

Moggie-bot is a webhook service serving as a connection between the Discord API & XIVAPI.
In a Discord channel, a user querys a command such as '?whoami', the command is
sent to a server hosting this service, and responds with an automated player card.

Firstly, if a user has not told the server who their player name is, they use 
'?iam < server-name > < player-name >', and moggie-bot with save the Discord user
name, and in-game player name. Next, Moggie-bot querys XIVAPI for an in-game
player id, and caches the id to increase throughput. 

Next, Moggie-bot queirys XIVAPI for a player image, and player profile information.
The image is saved locally (temporarily), and an info object is added to memory. 
Using the assets, card_background.png, full-border.png, text_boxes4.png, and stored
character image, a card template is formed and character info is overlayed on top. 
Since the player image resolution is quite small, I added a background extending the
resolution which seemlessly connects with player image. The extended background
(card_background.png) was created using GIMP image maniplulate software using
a portion of the player image background, and gradients using colers from player image.

Moggie-bot can be added to discord channel with this link:
[Moggie-bot](https://discord.com/oauth2/authorize?client_id=734119059695730719&permissions=0&redirect_uri=http%3A%2F%2F96.48.246.100%3A9292%2Fauthorize&scope=bot). Only a user with admin privileges to a discord server can add the bot. 

## Moggie-bot hosting service commands

Moggie-bot is hosted using Linux supervisorctl service on a Raspberry Pi, and implemented as follows:

Create a conf file such as bot.conf under /etc/supervisor/conf.d/
Create a 2 log files such under /var/log/ called: 
'< service-name >'.err.log and
'< service-name >'.out.log

conf file has these contents:
```
[program:<service-name>]                                                                 
directory=/home/<py file location>
command=/usr/bin/python3 /home/<py file location>/<py file name>
autostart=true                                                                  
autorestart=true                                                                
stderr_logfile=/var/log/moggy.err.log                                           
stdout_logfile=/var/log/moggy.out.log   
```

The service can only access files in the directory folder

`supervisorctl reread` to load conf file

`supervisorctl update` to activate bot service

`supervisorctl restart <service-name>` when changes to .py file is made

`supervisorctl tail <service-name>` to see console logs

`supervisorctl tail <service-name> stderr` to see error messages

