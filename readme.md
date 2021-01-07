## Player Card Output

![](player_card_example.png)

## Supervisorctl commands

Create a conf file such as bot.conf under /etc/supervisor/conf.d/
Create a 2 log files such under /var/log/ called: 
'<service-name>'.err.log and
'<service-name>'.out.log

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

