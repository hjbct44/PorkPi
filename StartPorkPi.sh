
#!bin/sh

cd /home/pi/PorkPi

sudo /etc/init.d/watchdog start &

. /home/pi/PorkPi/PorkPiCheckDog.sh&

while :
do

rm PorkPi_Error.log

touch PorkPi_Error.log

echo >> PorkPi_Error.log
echo >> PorkPi_Error.log
echo >> PorkPi_Error.log
echo `date` >> PorkPi_Error.log
echo >> PorkPi_Error.log
echo "Starting PorkPi" >> PorkPi_Error.log

echo "PorkPi Started" | mail -s "PorkPi Started" your_email_address@gmail.com

#sudo python /home/pi/PorkPi/PorkPi.py 2>>PorkPi_Error.log

echo "PorkPi Crashed" | mail -s "PorkPi Crashed" your_email_address@gmail.com < PorkPi_Error.log

sleep 60
done
