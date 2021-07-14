#!/bin/bash

if [[ ! "$(service cron status)" =~ "start/running" ]]
then
    echo " The cron service has been stopped. It has now been restarted." 
    sudo service cron start
else
    echo " The cron service has been restarted." 
fi

if [[ ! "$(service apache2 status)" =~ "start/running" ]]
then
    echo " The Apache service has been stopped. It has now been restarted." 
    sudo service apache2 start
else
    echo " The Apache service has been restarted." 
fi

exec "$@"
