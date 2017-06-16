# PorkPi
Raspberry Pi control for meat curing chamber

This uses a raspberry Pi to read temeperature and humidity using a DHT22 sensor and controls a fridge with the following controls:

  Temperature Too High - Turn fridge on
  Temperature Too Low - Turn fridge off + turn on heater
  
  Humidity Too High - turn on Fridge + Turn on heater if needed
  Humidity Too Low - turn off Fridge + Turn on humidifyer
  
  Circulate Air - circulate the air insude fridge
  
  Air_Pump - inject fresh air from outside fridge
  
  Weight 1 - read from load cell_1
  Weight 2 - read from load cell_2
  Weight 3 - read from load cell_3
  Weight 4 - read from load cell_4
  
  
  The parameters to control the fridge are held in a google sheet (see gspread below).
  
  The output data is held in a google sheet (see gspread below)
  
  PorkPi is monitored with a watchdog (both hard and soft)
  
  PorkPi reports errors / crashes / restarts via email.
  
  PorkPi responds to email commands for restart and shutdown
  
  
  Files:
  
  /etc/rc.local
    1. Waits for wireless lan to initiate
    2. sends email saying rebooted
    3. starts StartPorkPi.sh shell script using screen to allow remote login to headless application
    4. starts StartWeighing.sh shell script using screen to allow remote login to headless application
   
   ./PorkPi.sh
   1. start hardware watchdog
   2. start software watchdog (PorkPiCheck
   3. send email saying Porkpi started
   4. execute python code PorkPi.py
   5. if crashed, send email saying crashed and restart PorkPi.py
   
   ./
            
