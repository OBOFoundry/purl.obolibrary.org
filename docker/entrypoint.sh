#!/bin/bash

if [[ ! "$(service apache2 status)" =~ "start/running" ]]
then
    echo " The Apache service on the server has been stopped. It has now been restarted." 
    sudo service apache2 start
else
    echo " The Apache service on the server has been restarted." 
fi

exec "$@"
