echo "Starting Softdog"

touch /home/pi/PorkPi/PorkPi.softdog

while :
do

if test `find "/home/pi/PorkPi/PorkPi.softdog" -amin +10`
then
echo "PorkPi Softdog Stopped" | mail -s "PorkPi Softdog Stopped - Rebooting" your_email_address@gmail.com < PorkPi_Error.log
sudo shutdown -r now
fi

sudo python /home/pi/PorkPi/PorkPiCheckEmail.py

sleep 10m
done
