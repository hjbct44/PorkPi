# PorkPi
Raspberry Pi control for meat curing chamber

This uses a raspberry Pi to read temeperature and humidity using a DHT22 sensor and controls a fridge with the following controls:

          Temperature Too High - Turn fridge on
          Temperature Too Low - Turn fridge off + turn on heater

          Humidity Too High - turn on Fridge + Turn on heater if needed
          Humidity Too Low - turn off Fridge + Turn on humidifyer

          Circulate Air - circulate the air inside fridge

          Air_Pump - inject fresh air from outside fridge

          Weight 1 - read from load cell_1 using load cell connected to HX711 A-D converter 
          Weight 2 - read from load cell_2
          Weight 3 - read from load cell_3
          Weight 4 - read from load cell_4

  
  
  Using 8 channel relay (5v, 120v) https://www.sainsmart.com/arduino-compatibles-1/relay/8-channel-dc-5v-relay-module-for-arduino-pic-arm-dsp-avr-msp430-ttl-logic.html
  
  Load Cells https://www.amazon.com/uxcell-Electronic-Balance-Weighing-Sensor/dp/B006W2IDUO/ref=sr_1_1?s=home-garden&ie=UTF8&qid=1497712404&sr=1-1&keywords=uxcell+Electronic+Balance+Weighing+Load+Cell+Sensor+0-5Kg
  
  HX711 DAC https://www.amazon.com/DIYmall-Weighing-Conversion-Sensors-Microcontroller/dp/B010FG9RXO/ref=sr_1_1?s=electronics&ie=UTF8&qid=1497712204&sr=8-1&keywords=DIYmall+2pcs+Hx711+Weight+Weighing+Load+Cell+Conversion+Module+Sensors+Ad+Module+for+Arduino+Microcontroller
  
  HX711 DAC code (thanks ggurov!) https://github.com/ggurov/hx711  The code is in 'c' and I don't believe Python would work due to timing sensitiviies in reading data from the DAC.
  
  
  
  The parameters to control the fridge are held in a google sheet (see GSPREAD below).
  
  The output data is held in a google sheet (see gspread below)
  
  PorkPi is monitored with a watchdog (both hard and soft)
  
  PorkPi reports errors / crashes / restarts via email.
  
  PorkPi responds to email commands for restart and shutdown
  
  
  Files:
 
  /etc/rc.local
  1. Waits for wireless lan to initiate
  2. sends email saying rebooted
  3. starts StartPorkPi.sh shell script using screen (https://www.gnu.org/software/screen/manual/screen.html#Overview) to allow remote login to headless application
  4. starts StartWeighing.sh shell script using screen (https://www.gnu.org/software/screen/manual/screen.html#Overview) to allow remote login to headless application
   
   
 ./RebootMailer
  1. send email saying rebooted
   
   
 ./WaitForLan.sh
   1. loop until get successfulping from WLAN
   
   
 ./PorkPi.sh
   1. start hardware watchdog
   2. start software watchdog (PorkPiCheckDog.sh)
   3. send email saying Porkpi started
   4. execute python code PorkPi.py
   5. if crashed, send email saying crashed and restart PorkPi.py
   
   
 ./PorkPiCheckDog.sh
   1. touch file
   2. check file has been touched by PorkPi.py recently
   3. if file has not beentouched recently, reboot
   4. execute PorkPiCheckEmail.py to check to see if received email for reboot or restart
   
   
 ./PorkPiCheckEmail.py
   1. If received email from specific account with Subject = reboot, then reboot
   2. If received email from specific account with Subject = shutdown, then shutdown PorkPi
   
   
 ./StartWeighing.sh
   1. execute HX711 with parameters to read weight of load cell and write reults to file to be picked up by PorkPi.py
   
   
 ./PorkPi
   Main python code for PorkPi
   
   
   
   GSPREAD
   Gspread forms integral part of system using google sheets as a gui for input parameters as well as output.
   
   Many thanks to burnash for this great tool
   https://github.com/burnash/gspread
   
   Setting up the credentials and permissions is a little tricky but persevere.
   
   The google workbook has 5 sheets:
   1. Dashboard - contains the numerical and graphical status of the curing process, Temperatures, Humidity, Weights etc.
   2. Params - contains the input parameters to control the PorkPi 
   3. Schedule - contains Temperature and Humidity settings on a daily basis so the chamber can be automatically controlled for a curingperiod
   4. db - the data read from the DHT22 and HX711 as well as status of devices.  This can get very large
   5.Batches - a sheet to record information about curing batches
   
   Scripts:  Init button calls ClearCCC which deletes the database data
             Load Cell buttons reset the starting weight for a new batch
   
Link  - need to figure out how to link google sheet here  
   
   There is a secondary Dash spreadsheet which links latest data onto a smaller sheet which can be viewed on a cell phone
   
Link - need to figure out how to link google sheet here  
  
