#!bin/sh

sleep 5m
#need to sleep to prevent first read being zero

while :
do

cd /home/pi/PorkPi

# hx711 clock data offset two_point_five__kilo

touch LoadCell_LockFile

sudo ./hx711 11 9  -145500 -961118 > LoadCell_1
#sudo ./hx711 11 9  -145668 -961118 > LoadCell_1
sleep 10s
sudo ./hx711 25 24 -50674 -1065180 > LoadCell_2
sleep 10s
sudo ./hx711 23 18 -28082 981754 > LoadCell_3
sleep 10s
sudo ./hx711 7 8 -25380 -918871 > LoadCell_4

rm LoadCell_LockFile

echo done


sleep 1h

done