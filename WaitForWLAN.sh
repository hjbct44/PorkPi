#!/bin/bash
# Wait for Network to be available.
while true
do
ping -c 1 8.8.8.8
if [ $? == 0 ];
then
break;
else
sleep 5
fi
done
