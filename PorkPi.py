# #######################################################################################
#                                                                                       #
#                  					P O R K P I                   				        #
#                                                                                       #
#                                                       -Henry Bonner (et al)           #
# #######################################################################################

import json

import sys

from termcolor import colored

import time

from datetime import timedelta

import datetime

import os

import gspread

import Adafruit_DHT

import RPi.GPIO as GPIO

from oauth2client.client import SignedJwtAssertionCredentials

import smtplib

from email.MIMEMultipart import MIMEMultipart

from email.MIMEText import MIMEText

import requests


#Google Sheet Authentication
GDOCS_OAUTH_JSON       = 'your_credentials.json'
GDOCS_SPREADSHEET_NAME = 'your_spreadsheet_name'


# binary controls
ON = "10"  #setting this to 10, makes it show up on chart
OFF = "0"

# Cell Coordinates

REFRESH_SETTINGS_CELL = "J3"

INITIALISE_CELL = "C40"

SLEEP_SECONDS_CELL = "J8"


OUTPUT_ROW_CELL = "1"
OUTPUT_COL_CELL = "23"

OUTPUT_START_ROW = "5"

LAST_ROW_WRITTEN_CELL = "J1"

HOOK1_CURRENT_WEIGHT_CELL = "F6"
HOOK2_CURRENT_WEIGHT_CELL = "F7"
HOOK3_CURRENT_WEIGHT_CELL = "F8"
HOOK4_CURRENT_WEIGHT_CELL = "F9"

START_TIME_THIS_CURE_CELL = "J4"
ELAPSED_TIME_THIS_CURE_CELL = "J5"

LAST_SENSOR_READ_TIME_CELL = "J6"
DELTA_TO_LAST_READING_CELL = "J7"

UPTIME_CELL = "J9"

CHAMBER_TEMPERATURE_CELL = "E2"
CHAMBER_RELATIVE_HUMIDITY_CELL = "E3"

CHAMBER_SETPOINT_TEMP_CELL = "C2"
CHAMBER_SETPOINT_RH_CELL = "C3"


COMPRESSOR_IDLE_CELL = "L8"


# # In params sheet


TEMPERATURE_DELTA_TO_COOL_CELL = "D4"
TEMPERATURE_ERROR_UPPER_CELL = "D5"

TEMPERATURE_ERROR_LOWER_CELL = "D6"
TEMPERATURE_DELTA_TO_HEAT_CELL = "D7"


HUMIDITY_DELTA_TO_DEHUMIDIFY_CELL = "D9"
HUMIDITY_ERROR_UPPER_CELL = "D10"
HUMIDITY_ERROR_LOWER_CELL = "D11"
HUMIDITY_DELTA_TO_HUMIDIFY_CELL = "D12"

CIRC_FAN_DUTY_CELL = "D14"
CIRC_FAN_IDLE_TIME_CELL = "D15"
AIR_PUMP_DUTY_CELL = "D16"
AIR_PUMP_IDLE_TIME_CELL = "D17"

HUMIDITY_DUTY_CELL = "D19"
HUMIDITY_IDLE_TIME_CELL = "D20"

TEMPERATURE_CONTROL_CELL = "D22"
HUMIDITY_CONTROL_CELL = "D23"


HUMIDITY_DELTA_TO_HUMIDIFY = 0
HUMIDITY_DELTA_TO_DEHUMIDIFY = 0

HUMIDITY_ERROR_UPPER = 0
HUMIDITY_ERROR_LOWER = 0



HUMIDITY_CONTROL = "Y"
TEMPERATURE_CONTROL = "Y"


#input GPIO
DHT22_PIN = 4

#output GPIO
COOL_PIN = 22
HEAT_PIN = 27
AIR_PUMP_PIN = 17
HUMIDIFIER_PIN = 3
CIRC_FAN_PIN = 2

# Load Cells read from separate program which writes weights to file,  in turn read by this program


COMPRESSOR_IDLE_TIME = 900 		#wait number seconds before cycling cool
HEAT_IDLE_TIME = 1   			#wait number seconds before cycling heat

HUMIDIFIER_DUTY = 3 			#number of seconds to switch humidifier on each loop
HUMIDIFIER_IDLE_TIME = 60		#wait number seconds before cycling humidifier

AIR_PUMP_DUTY = 0				#how long to run air pump Whisper 10 claims 0.5litres / min.  Read from spreadhseet
AIR_PUMP_IDLE_TIME = 0			#off for how long. Read from spreadhseet

		
CIRC_FAN_DUTY = 0				# seconds to stay on. Read from spreadhseet
CIRC_FAN_IDLE_TIME = 0			# seconds to stay off. Read from spreadhseet


PANIC_HOT = 100					#exit if temp too high or too low
PANIC_COLD = 38

LOGIN_SESSION_TIME = 2700 		#login again every X seconds (2700 = 45 mins)

SOFTDOG_FILE = "/home/pi/PorkPi/PorkPi.softdog"

# #######################################################################################
#  Touch the watchdog file aka Pat The Dog
# #######################################################################################


def touch(fname):
    if os.path.exists(fname):
        os.utime(fname, None)
    else:
        open(fname, 'a').close()

		

# #######################################################################################
#   Login to Google Sheets
# #######################################################################################

	
def login_open_sheet(oauth_key_file, spreadsheet):
	try:
		json_key = json.load(open(oauth_key_file))
		credentials = SignedJwtAssertionCredentials(json_key['client_email'], 
													json_key['private_key'], 
													['https://spreadsheets.google.com/feeds'])
		gc = gspread.authorize(credentials)
		
		dash = gc.open(spreadsheet).worksheet("Dashboard")
		
		database = gc.open(spreadsheet).worksheet("db")
		
		
		
		params = gc.open(spreadsheet).worksheet("Params")
				
		return(dash, database, params, credentials)
		
	except Exception as ex:
		sys.stderr.write("Unable to login and get spreadsheet.  Check OAuth credentials, spreadsheet name, and make sure spreadsheet is shared to the client_email address in the OAuth .json file!\n")
		sys.stderr.flush()
		
		print("Google sheet login failed with error:", ex)
		
		sys.stderr.write("Google sheet login failed\n")
		sys.stderr.flush()
		
		sys.exit(1)

			
# #######################################################################################
#   Get Sensor Data
# #######################################################################################

def GetSensorData(my_sensor,my_pin, myfile1, myfile2, myfile3, myfile4):

	
	chamber_humidity, chamber_temperature = Adafruit_DHT.read_retry(my_sensor, my_pin)
	
	if chamber_humidity is None and chamber_temperature is None:
		sys.stderr.write("Failed to get reading from DH22 - forcing 55F and 75%\n")
		
		chamber_humidity = 75
		 
		chamber_temperature = 55
						
		last_sensor_read_time = datetime.datetime.now()
	else:
		chamber_humidity = int(chamber_humidity) 
		
		chamber_temperature = int((chamber_temperature)*1.8)+32 # convert to F
						
		last_sensor_read_time = datetime.datetime.now()
		
		#Get Weights from file written to by HX711 program
	if  os.path.isfile('LoadCell_LockFile'):
		print("LoadCell_LockFile - skipping read")
		hook1_weight_now = -1
		hook2_weight_now = -1
		hook3_weight_now = -1
		hook4_weight_now = -1
	
	else:
		myfile1.seek(0, 0);
		myfile2.seek(0, 0);
		myfile3.seek(0, 0);
		myfile4.seek(0, 0);

		
		
		hook1_weight_now = int(myfile1.read())
		hook2_weight_now = int(myfile2.read())
		hook3_weight_now = int(myfile3.read())
		hook4_weight_now = int(myfile4.read())
		
		
	
	return(last_sensor_read_time,chamber_temperature,chamber_humidity,hook1_weight_now, hook2_weight_now, hook3_weight_now, hook4_weight_now)


# #######################################################################################
#   Read Data From Sheet
# #######################################################################################

def ReadDataFromSheet(dash, database, params):
	KeepTrying = True
	while KeepTrying == True:
		try:
			
			# this is on database sheet
			local_last_row_written = int(database.acell(LAST_ROW_WRITTEN_CELL).value)
		
			#  dash sheet
			local_initialise = dash.acell(INITIALISE_CELL).value
		
			local_refreshsettings = dash.acell(REFRESH_SETTINGS_CELL).value
		
			
			local_chamber_setpoint_temp = int(dash.acell(CHAMBER_SETPOINT_TEMP_CELL).value)
			local_chamber_setpoint_rh = int(dash.acell(CHAMBER_SETPOINT_RH_CELL).value)
				
			local_sleep_seconds = dash.acell(SLEEP_SECONDS_CELL).value
			
			# params sheet
		
			local_TEMPERATURE_ERROR_UPPER = int(params.acell(TEMPERATURE_ERROR_UPPER_CELL).value) # degrees temperature threshold
			local_TEMPERATURE_ERROR_LOWER = int(params.acell(TEMPERATURE_ERROR_LOWER_CELL).value) # switch before hits lower threshold - turn off early

			local_TEMPERATURE_DELTA_TO_COOL = int(params.acell(TEMPERATURE_DELTA_TO_COOL_CELL).value) #if temp is more than x degrees over setpoint, cool, otherwise idle
			local_TEMPERATURE_DELTA_TO_HEAT = int(params.acell(TEMPERATURE_DELTA_TO_HEAT_CELL).value) #if temp is less than x degrees over setpoint, cool, otherwise idle
		
			local_HUMIDITY_ERROR_UPPER = int(params.acell(HUMIDITY_ERROR_UPPER_CELL).value) # %
			local_HUMIDITY_ERROR_LOWER = int(params.acell(HUMIDITY_ERROR_LOWER_CELL).value) # % 
		
			local_HUMIDITY_DELTA_TO_HUMIDIFY = int(params.acell(HUMIDITY_DELTA_TO_HUMIDIFY_CELL).value)
			local_HUMIDITY_DELTA_TO_DEHUMIDIFY = int(params.acell(HUMIDITY_DELTA_TO_DEHUMIDIFY_CELL).value)
		
		
			local_TEMPERATURE_CONTROL = params.acell(TEMPERATURE_CONTROL_CELL).value
			local_HUMIDITY_CONTROL = params.acell(HUMIDITY_CONTROL_CELL).value
		
			
			local_AIR_PUMP_DUTY = int(params.acell(AIR_PUMP_DUTY_CELL).value)
			local_AIR_PUMP_IDLE_TIME = int(params.acell(AIR_PUMP_IDLE_TIME_CELL).value)

			local_CIRC_FAN_DUTY = int(params.acell(CIRC_FAN_DUTY_CELL).value)
			local_CIRC_FAN_IDLE_TIME = int(params.acell(CIRC_FAN_IDLE_TIME_CELL).value)
			
			local_HUMIDITY_DUTY = int(params.acell(HUMIDITY_DUTY_CELL).value)
			local_HUMIDITY_IDLE_TIME = int(params.acell(HUMIDITY_IDLE_TIME_CELL).value)
		
			
		except gspread.GSpreadException:
		
			sys.stderr.write("Gspread error in ReadDataFromSheet  - logging in again\n")
			sys.stderr.flush()
			
			time.sleep(10) 	
			
			dash, database, params, credentials = login_open_sheet(GDOCS_OAUTH_JSON, GDOCS_SPREADSHEET_NAME)
		
		
		except requests.exceptions.SSLError:
			sys.stderr.write("Gspread error in ReadDataFromSheet SSLERROR- logging in again\n")
			sys.stderr.flush()
		
			time.sleep(10) 	

			dash, database, params, credentials = login_open_sheet(GDOCS_OAUTH_JSON, GDOCS_SPREADSHEET_NAME)
		
		except requests.exceptions.ConnectionError:
			sys.stderr.write("Gspread error in ReadDataFromSheet ConnectionError - logging in again\n")
			sys.stderr.flush()
		
			time.sleep(10) 	

			dash, database, params, credentials = login_open_sheet(GDOCS_OAUTH_JSON, GDOCS_SPREADSHEET_NAME)	
		else:
			KeepTrying = False

	return(local_initialise, local_refreshsettings, local_chamber_setpoint_temp, \
	local_chamber_setpoint_rh,local_last_row_written,local_sleep_seconds, local_TEMPERATURE_ERROR_UPPER, local_TEMPERATURE_ERROR_LOWER, local_HUMIDITY_ERROR_UPPER,\
	local_HUMIDITY_ERROR_LOWER, local_TEMPERATURE_DELTA_TO_COOL, local_TEMPERATURE_DELTA_TO_HEAT, local_TEMPERATURE_CONTROL, local_HUMIDITY_CONTROL, local_HUMIDITY_DELTA_TO_HUMIDIFY,\
	local_HUMIDITY_DELTA_TO_DEHUMIDIFY, local_CIRC_FAN_DUTY, local_CIRC_FAN_IDLE_TIME, local_AIR_PUMP_DUTY, local_AIR_PUMP_IDLE_TIME, local_HUMIDITY_DUTY, local_HUMIDITY_IDLE_TIME)
	
	
# ######################################################################################
#   Write Data To Sheet
# ######################################################################################

def WriteDataToSheet(dash,database,row_count,last_sensor_read_time,chamber_temperature,chamber_humidity,hook1_weight_now, hook2_weight_now, hook3_weight_now, hook4_weight_now,cool_status, heat_status,humidifier_status,dehumidifier_status, air_pump_status,circ_fan_status):
	
	KeepTrying = True
	while KeepTrying:
		try:
			
			
		
			database.update_acell(LAST_ROW_WRITTEN_CELL,row_count)
	
			
			#Assemble batch update for row
			#The following all written to database
			
			output_range = "A"+str(row_count)+":L"+str(row_count)
	
			cell_list = database.range(output_range)

			cell_values = [last_sensor_read_time,chamber_temperature,chamber_humidity,hook1_weight_now, hook2_weight_now, hook3_weight_now, hook4_weight_now,cool_status, heat_status,humidifier_status,circ_fan_status, air_pump_status]

			for r in range (0,11):
				for i, val in enumerate(cell_values):  #gives us a tuple of an index and value
					cell_list[i].value = val
	
			# Update in batch
			database.update_cells(cell_list)
			
		except gspread.GSpreadException:
		
			sys.stderr.write("Gspread error in WriteDataToSheet  - logging in again\n")
			sys.stderr.flush()
			
			time.sleep(10) 	
			
			dash, database, params, credentials = login_open_sheet(GDOCS_OAUTH_JSON, GDOCS_SPREADSHEET_NAME)
			
						
		except requests.exceptions.SSLError:
			sys.stderr.write("Gspread error in WriteDataToSheet SSLERROR- logging in again\n")
			sys.stderr.flush()
		
			time.sleep(10) 	

			dash, database, params, credentials = login_open_sheet(GDOCS_OAUTH_JSON, GDOCS_SPREADSHEET_NAME)
			
		except requests.exceptions.ConnectionError:
			sys.stderr.write("Gspread error in WriteDataToSheet ConnectionError - logging in again\n")
			sys.stderr.flush()
			
			time.sleep(10) 	

			dash, database, params, credentials = login_open_sheet(GDOCS_OAUTH_JSON, GDOCS_SPREADSHEET_NAME)
			
		else:
			KeepTrying = False

		
# #######################################################################################
#   Update Devices - switch device on or off
# #######################################################################################
		
def UpdateDevice(device,setting):
			
	GPIO.setup(device, GPIO.OUT)
	if(setting == ON):
		GPIO.output(device, GPIO.LOW) # Low is on
	if(setting == OFF):
		GPIO.output(device, GPIO.HIGH) #High is off
		
	if device == HEAT_PIN and setting == ON :
		print colored("Heater On :  " + time.strftime("%c"), "red")
		
	if device == HEAT_PIN and setting == OFF :
		print colored("Heater Off :  " + time.strftime("%c"), "red")
		
	if device == COOL_PIN and setting == ON :
		print colored("Cooler On :  " + time.strftime("%c"), "cyan")
		
	if device == COOL_PIN and setting == OFF :
		print colored("Cooler Off :  " + time.strftime("%c"), "cyan")
		
	if device == CIRC_FAN_PIN and setting == ON :
		print colored("Circ ON :  " + time.strftime("%c"), "green")
		
	if device == CIRC_FAN_PIN and setting == OFF :
		print colored("Circ Off :  " + time.strftime("%c"), "green")
		
	if device == HUMIDIFIER_PIN and setting == ON :
		print colored("Humidifier ON :  " + time.strftime("%c"), "white")
		
	if device == HUMIDIFIER_PIN and setting == OFF :
		print colored("Humidifier OFF :  " + time.strftime("%c"), "white")		
		
	if device == AIR_PUMP_PIN and setting == ON :
		print colored("Air Pump ON :  " + time.strftime("%c"), "magenta")
		
	if device == AIR_PUMP_PIN and setting == OFF :
		print colored("Air Pump OFF :  " + time.strftime("%c"), "magenta")		

	return(time.time())
	
# #######################################################################################
#   CompressDb - compress database - remove all not peak or trough
# #######################################################################################	

def CompressDb(database):
	
	#not yet implemented
	print("Compressing...")
	
	
			
	print("done")
		
# #######################################################################################
#   initialise sheet
# #######################################################################################

def InitialiseSheet(dash, database):

	print("INITIALISE")
	
	try:
		# Set row counter
		database.update_acell(LAST_ROW_WRITTEN_CELL,OUTPUT_START_ROW)
			
		# Flip initialise to 'N'
		dash.update_acell(INITIALISE_CELL,"N")
		
		# Write session start time to Sheet
		start_time_this_control_session = datetime.datetime.now()

		dash.update_acell(START_TIME_THIS_CURE_CELL,start_time_this_control_session)
	
	except gspread.GSpreadException:
		
		sys.stderr.write("Gspread error in InitialiseSheet - logging in again\n")
		sys.stderr.flush()
		
		time.sleep(10) 	

		dash, database, params, credentials = login_open_sheet(GDOCS_OAUTH_JSON, GDOCS_SPREADSHEET_NAME)
	
# #######################################################################################
#    InitRelays - setup the output pins
# #######################################################################################
	
def InitRelays():
	pinList = [COOL_PIN,HEAT_PIN,HUMIDIFIER_PIN, CIRC_FAN_PIN, AIR_PUMP_PIN]
	
	GPIO.setmode(GPIO.BCM)

	for i in pinList: 
		GPIO.setup(i, GPIO.OUT) 
		GPIO.output(i, GPIO.HIGH) #High value switches off for this relay board

		
# #######################################################################################
#     Main loop
# #######################################################################################

#only allow one instance
try:
    import socket
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
	
    #Create an abstract socket, by prefixing it with null. 
    s.bind( '\0postconnect_gateway_notify_lock') 
	
except socket.error, e:
    error_code = e.args[0]
    error_string = e.args[1]
    print "Process already running (%d:%s ). Exiting" % ( error_code, error_string) 
    sys.exit (0) 

#OK, Start up

current_time_this_cure = datetime.datetime.now()	
print("Starting PorkPi at " + time.strftime("%c"))

#open Load Cell Files

load_cell_1_file = open("LoadCell_1")
load_cell_2_file = open("LoadCell_2")
load_cell_3_file = open("LoadCell_3")
load_cell_4_file = open("LoadCell_4")

last_hook1_weight_now = 0
last_hook2_weight_now = 0
last_hook3_weight_now = 0
last_hook4_weight_now = 0

#Initialise Sensor
sensor = Adafruit_DHT.DHT22
pin = DHT22_PIN

#initialise relays
InitRelays()

#Turn everything OFF

last_cool_time = UpdateDevice(COOL_PIN, OFF)
last_heat_time = UpdateDevice(HEAT_PIN, OFF)
last_humid_time = UpdateDevice(HUMIDIFIER_PIN, OFF)
last_circ_time = UpdateDevice(CIRC_FAN_PIN, OFF)

last_air_pump_off_time = UpdateDevice(AIR_PUMP_PIN, OFF)
last_air_pump_on_time = last_air_pump_off_time

last_circ_off_time = last_circ_time
last_circ_on_time = last_circ_time


cool_status  = OFF
heat_status  = OFF
humidifier_status = OFF
dehumidifier_status = OFF
circ_fan_status = OFF
air_pump_status = OFF

# Login to Google Sheets
dash, database, params, credentials = login_open_sheet(GDOCS_OAUTH_JSON, GDOCS_SPREADSHEET_NAME)
last_login_time = time.time()

print("About to Compress")
#CompressDb(database)






#Read Initial Data
initialise,refreshsettings, chamber_setpoint_temp, chamber_setpoint_rh, last_row_written, \
sleep_seconds, TEMPERATURE_ERROR_UPPER, TEMPERATURE_ERROR_LOWER, HUMIDITY_ERROR_UPPER, HUMIDITY_ERROR_LOWER, TEMPERATURE_DELTA_TO_COOL, TEMPERATURE_DELTA_TO_HEAT, \
TEMPERATURE_CONTROL, HUMIDITY_CONTROL, HUMIDITY_DELTA_TO_HUMIDIFY, HUMIDITY_DELTA_TO_DEHUMIDIFY, \
CIRC_FAN_DUTY, CIRC_FAN_IDLE_TIME, AIR_PUMP_DUTY, AIR_PUMP_IDLE_TIME, HUMIDIFIER_DUTY, HUMIDIFIER_IDLE_TIME = ReadDataFromSheet(dash, database, params)


#Read Sensors
last_sensor_read_time,chamber_temperature,chamber_humidity,hook1_weight_now, hook2_weight_now, hook3_weight_now, hook4_weight_now = GetSensorData(sensor,pin, load_cell_1_file,load_cell_2_file,load_cell_3_file,load_cell_4_file)
		
last_chamber_temperature = chamber_temperature
last_chamber_humidity = chamber_humidity

if hook1_weight_now >0:
	last_hook1_weight_now = hook1_weight_now
else: hook1_weight_now = last_hook1_weight_now

if hook2_weight_now >0:
	last_hook2_weight_now = hook2_weight_now
else: hook2_weight_now = last_hook2_weight_now
	
if hook3_weight_now >0:
	last_hook3_weight_now = hook3_weight_now
else: hook3_weight_now = last_hook3_weight_now

if hook4_weight_now >0:
	last_hook4_weight_now = hook4_weight_now
else: hook4_weight_now = last_hook4_weight_now


#Cast row count read from sheet to integer
row_count=int(last_row_written)

#write for the first time
WriteDataToSheet(dash,database,row_count,last_sensor_read_time,chamber_temperature,chamber_humidity,hook1_weight_now, hook2_weight_now, hook3_weight_now, hook4_weight_now, cool_status, heat_status,humidifier_status, dehumidifier_status, air_pump_status,circ_fan_status )



state_change = 1 #make sure status gets written

	
# Main control loop the below state table is identical for humidity
#
#		Heat delta to cool	-----------------------------		Turn Cooler On
#
#		Temp error upper	------------  	Turn Heater Off
#
#		Temp Setpoint 		------------<<
#
#		Temp error lower	------------  	Turn Cooler Off
#
#		Cool delta to Heat	-----------------------------		Turn Heater On
#

last_uptime = time.time()




print("Main")

while True:
	try:
	
		
			
		# Pat the dog
		touch(SOFTDOG_FILE)
		
		
		current_uptime = datetime.timedelta(seconds = int( time.time()-last_uptime))
		
	
		#login every few mins
		if (time.time() - last_login_time  > LOGIN_SESSION_TIME):
			dash, database, params, credentials = login_open_sheet(GDOCS_OAUTH_JSON, GDOCS_SPREADSHEET_NAME)
			last_login_time = time.time()
			
		dash.update_acell(UPTIME_CELL,current_uptime)
			
		if credentials.access_token_expired:
			# refreshes the token, although does not seem to stop google sheets logging out hourly
			dash, database, params, credentials = login_open_sheet(GDOCS_OAUTH_JSON, GDOCS_SPREADSHEET_NAME)
			print colored("Token expired - logging in again", "red")

		if dash is None:
			dash, database, params, credentials = login_open_sheet(GDOCS_OAUTH_JSON, GDOCS_SPREADSHEET_NAME)
			print colored("Workseet is NONE - logging in again", "red")
	
		
		humidifier_status = OFF #reset humidifier status - as we toggle humidifier, it does not show up in write otherwise. 
		
		
		# Do we need to refresh settings?
		
		if (dash.acell(REFRESH_SETTINGS_CELL).value == "Y"):
			
			dash.update_acell(REFRESH_SETTINGS_CELL,"N")
			
			print("Refresh")
			#refresh control data
			initialise,refreshsettings, chamber_setpoint_temp, chamber_setpoint_rh, last_row_written, \
			sleep_seconds, TEMPERATURE_ERROR_UPPER, TEMPERATURE_ERROR_LOWER, HUMIDITY_ERROR_UPPER, HUMIDITY_ERROR_LOWER, TEMPERATURE_DELTA_TO_COOL, TEMPERATURE_DELTA_TO_HEAT, \
			TEMPERATURE_CONTROL, HUMIDITY_CONTROL, HUMIDITY_DELTA_TO_HUMIDIFY, HUMIDITY_DELTA_TO_DEHUMIDIFY, \
			CIRC_FAN_DUTY, CIRC_FAN_IDLE_TIME, AIR_PUMP_DUTY, AIR_PUMP_IDLE_TIME, HUMIDIFIER_DUTY, HUMIDIFIER_IDLE_TIME= ReadDataFromSheet(dash, database, params)

			if initialise == "Y":
				print("Calling init in main loop")
				InitialiseSheet(dash,database)
				last_row_written=OUTPUT_START_ROW
				row_count=int(last_row_written)
			
				initialise = "N"

			print("Init in main loop .. Last row written: "+str(row_count))
			
		#Read setpoints (separate from refresh above to reduce reads) - need this now we have temp/rh schedule built in, otherwise never checks setpoint
		
		chamber_setpoint_temp = int(dash.acell(CHAMBER_SETPOINT_TEMP_CELL).value)
		chamber_setpoint_rh = int(dash.acell(CHAMBER_SETPOINT_RH_CELL).value)
		
		 
		#Read Sensors
		
		last_sensor_read_time,chamber_temperature,chamber_humidity,hook1_weight_now, hook2_weight_now, hook3_weight_now, hook4_weight_now = GetSensorData(sensor,pin,load_cell_1_file,load_cell_2_file,load_cell_3_file,load_cell_4_file)
		
		
		#Check for PANIC condition
		if (chamber_temperature > PANIC_HOT or chamber_temperature < PANIC_COLD):
			
			time.sleep(10) 
			
			last_sensor_read_time,chamber_temperature,chamber_humidity,hook1_weight_now, hook2_weight_now, hook3_weight_now, hook4_weight_now = GetSensorData(sensor,pin, load_cell_1_file,load_cell_2_file,load_cell_3_file,load_cell_4_file)
			
			if (chamber_temperature > PANIC_HOT or chamber_temperature < PANIC_COLD):
				
				print("Temperature Panic : " ,chamber_temperature)
				sys.stderr.write("Temperature Panic - rebooting\n")
				
				sys.stderr.flush()
				
				#Shutdown and exit
				GPIO.cleanup()
				sys.exit (0)
	
		if hook1_weight_now >-1:
			last_hook1_weight_now = hook1_weight_now
		else: hook1_weight_now = last_hook1_weight_now

		if hook2_weight_now >1:
			last_hook2_weight_now = hook2_weight_now
		else: hook2_weight_now = last_hook2_weight_now
			
		if hook3_weight_now >-1:
			last_hook3_weight_now = hook3_weight_now
		else: hook3_weight_now = last_hook3_weight_now

		if hook4_weight_now >-1:
			last_hook4_weight_now = hook4_weight_now
		else: hook4_weight_now = last_hook4_weight_now
			
			
	#Cycle the circulation fan
		
		if circ_fan_status == OFF :
			if(time.time() - last_circ_off_time > CIRC_FAN_IDLE_TIME):
				last_circ_on_time = UpdateDevice(CIRC_FAN_PIN,ON)
				circ_fan_status = ON
				state_change = 1
				
				
				if CIRC_FAN_DUTY < sleep_seconds:  # allow for short circ fan duties
					time.sleep(float(CIRC_FAN_DUTY))
			
					
		if circ_fan_status == ON :
			if(time.time() - last_circ_on_time > CIRC_FAN_DUTY):
				last_circ_off_time = UpdateDevice(CIRC_FAN_PIN,OFF)
				circ_fan_status = OFF
				state_change = 1
	
	#Cycle the air pump
			
		if air_pump_status == OFF :
			if(time.time() - last_air_pump_off_time > AIR_PUMP_IDLE_TIME):
				last_air_pump_on_time = UpdateDevice(AIR_PUMP_PIN,ON)
				air_pump_status = ON	
				state_change = 1
				
				if AIR_PUMP_DUTY < sleep_seconds:  # allow for short circ fan duties
					print("Wait for air pump...", AIR_PUMP_DUTY, AIR_PUMP_IDLE_TIME)
					time.sleep(float(AIR_PUMP_DUTY))
					
		if air_pump_status == ON:
			if(time.time() - last_air_pump_on_time > AIR_PUMP_DUTY):
				last_air_pump_off_time = UpdateDevice(AIR_PUMP_PIN,OFF)
				air_pump_status = OFF
				state_change = 1
	
		
		# #########################				
		# TEMPERATURE CONTROL LOGIC
		# #########################
		
		
		if (chamber_temperature >= (chamber_setpoint_temp + TEMPERATURE_ERROR_UPPER )) : #Heat setpoint + acceptable error exceeded - mainly to avoid overshoot
			
			#Turn heat off, only if not in dehumidify cycle
			if (heat_status == ON and dehumidifier_status == OFF):
				last_heat_time = UpdateDevice(HEAT_PIN,OFF)
				heat_status = OFF
				state_change = 1

				
			if(chamber_temperature >= chamber_setpoint_temp + TEMPERATURE_DELTA_TO_COOL): #Heat setpoint significantly exceeded so active cool
				#Turn cooler on
				
				last_heat_time = UpdateDevice(HEAT_PIN,OFF)
				heat_status = OFF
				
				if (time.time() - last_cool_time  > COMPRESSOR_IDLE_TIME) and cool_status == OFF:
					last_cool_time = UpdateDevice(COOL_PIN, ON)
					cool_status = ON
					state_change = 1
				
				
		if (chamber_temperature <= (chamber_setpoint_temp - TEMPERATURE_ERROR_LOWER ) and chamber_temperature > chamber_setpoint_temp - TEMPERATURE_DELTA_TO_HEAT): 
																							#Heat setpoint - acceptable error exceeded .. mainly to avoid overshoot
																							#but allow to drift down a little if dehumidifier is on
			if dehumidifier_status == OFF:
				
				if cool_status == ON:
				
					last_cool_time = UpdateDevice(COOL_PIN, OFF)
					cool_status = OFF
					state_change = 1
				
			if dehumidifier_status == ON and heat_status == OFF:
				
					last_heat_time = UpdateDevice(HEAT_PIN,ON)
					heat_status = ON

		if(chamber_temperature <= chamber_setpoint_temp - TEMPERATURE_DELTA_TO_HEAT):	# Heat setpoint significantly exceeded so active heat and turn off cooling
			if(time.time() - last_heat_time > HEAT_IDLE_TIME): 
					
				if heat_status == OFF:
					last_heat_time = UpdateDevice(HEAT_PIN,ON)
					heat_status = ON
				if cool_status == ON:
					last_cool_time = UpdateDevice(COOL_PIN, OFF)
					cool_status = OFF
					dehumidifier_status = OFF
					state_change = 1
			
				
		# #########################				
		# HUMIDITY CONTROL LOGIC
		# #########################
		
		
		if (chamber_humidity >= (chamber_setpoint_rh + HUMIDITY_ERROR_UPPER ) and HUMIDITY_CONTROL == "Y"):
			
			
			# unlikely as humidifier is now on its own timer					
			if (humidifier_status == ON):
				last_humid_time = UpdateDevice(HUMIDIFIER_PIN, OFF)
				humidifier_status = OFF		
				state_change = 1
		
			
							
			#heating and cooling at same time to lower humidity
			if (chamber_humidity >= chamber_setpoint_rh + HUMIDITY_DELTA_TO_DEHUMIDIFY):
				
				if (time.time() - last_cool_time  > COMPRESSOR_IDLE_TIME):
					last_heat_time = UpdateDevice(HEAT_PIN,ON)
					last_cool_time = UpdateDevice(COOL_PIN, ON)
					cool_status = ON
					heat_status = ON
					
				dehumidifier_status = ON #only if exceeds DELTA		
				
				
		if ( chamber_humidity <= (chamber_setpoint_rh - HUMIDITY_ERROR_LOWER) and HUMIDITY_CONTROL == "Y"): 
				
			if(cool_status == ON):
				last_cool_time = UpdateDevice(COOL_PIN, OFF)
				cool_status = OFF
				dehumidifier_status = OFF
				
				state_change = 1
			else:
				if (chamber_humidity <= (chamber_setpoint_rh - HUMIDITY_DELTA_TO_HUMIDIFY)): # Need to humidfy if control delta is crossed
					if(time.time() - last_humid_time >= HUMIDIFIER_IDLE_TIME):
			
						last_humid_time = UpdateDevice(HUMIDIFIER_PIN, ON)
						humidifier_status = ON
						
						last_circ_time = UpdateDevice(CIRC_FAN_PIN,ON)
						circ_fan_status = ON
						
						time.sleep(HUMIDIFIER_DUTY)  
				
						last_humid_time = UpdateDevice(HUMIDIFIER_PIN, OFF)
					
						# keep circ fan of for a few more secs
						time.sleep(HUMIDIFIER_DUTY) 

						last_circ_time = UpdateDevice(CIRC_FAN_PIN,OFF)
						
												
						state_change = 1
				
				
			#Write status back to sheet
			# Only if something changed
			
		if 	state_change == 1 or chamber_temperature != last_chamber_temperature or chamber_humidity != last_chamber_humidity or hook1_weight_now != last_hook1_weight_now or hook2_weight_now!=last_hook2_weight_now or hook3_weight_now != last_hook3_weight_now or hook4_weight_now != last_hook4_weight_now:
		
			dash.update_acell(COMPRESSOR_IDLE_CELL,int(time.time() - last_cool_time))

			WriteDataToSheet(dash,database,row_count,last_sensor_read_time,chamber_temperature,chamber_humidity,hook1_weight_now, hook2_weight_now, hook3_weight_now, hook4_weight_now, cool_status, heat_status,humidifier_status, dehumidifier_status, air_pump_status, circ_fan_status )
			
			dash.update_acell(COMPRESSOR_IDLE_CELL,int(time.time() - last_cool_time))
			dash.update_acell(LAST_SENSOR_READ_TIME_CELL,last_sensor_read_time)
			
			state_change = 0
			
			#change status after writing to sheet, otherwise won't show up.
			
			circ_fan_status = OFF
			humidifier_status = OFF
			
			
			#Update counter
			
			row_count+=1
						
			
		else:
			#write time since last cool
			dash.update_acell(COMPRESSOR_IDLE_CELL,int(time.time() - last_cool_time))
			dash.update_acell(LAST_SENSOR_READ_TIME_CELL,last_sensor_read_time)
			
		last_chamber_temperature = chamber_temperature
		last_chamber_humidity = chamber_humidity
		
		if hook1_weight_now != -1:
			last_hook1_weight_now = hook1_weight_now
		else: hook1_weight_now = last_hook1_weight_now

		if hook2_weight_now != -1:
			last_hook2_weight_now = hook2_weight_now
		else: hook2_weight_now = last_hook2_weight_now
			
		if hook3_weight_now != -1:
			last_hook3_weight_now = hook3_weight_now
		else: hook3_weight_now = last_hook3_weight_now

		if hook4_weight_now != -1:
			last_hook4_weight_now = hook4_weight_now
		else: hook4_weight_now = last_hook4_weight_now
		
	
				
		
		time.sleep(float(sleep_seconds))

	
	
	except gspread.GSpreadException:
		
		sys.stderr.write("Gspread error in main loop gspread.GSpreadException - logging in again\n")
		sys.stderr.flush()
		
		time.sleep(10) 	

		dash, database, params, credentials = login_open_sheet(GDOCS_OAUTH_JSON, GDOCS_SPREADSHEET_NAME)
	
	
	except requests.exceptions.SSLError:
		sys.stderr.write("Gspread error in main loop SSLERROR- logging in again\n")
		sys.stderr.flush()
		
		time.sleep(10) 	

		dash, database, params, credentials = login_open_sheet(GDOCS_OAUTH_JSON, GDOCS_SPREADSHEET_NAME)

	
	except requests.exceptions.ConnectionError:
		sys.stderr.write("Gspread error in main loop ConnectionError - logging in again\n")
		sys.stderr.flush()
		
		time.sleep(10) 	

		dash, database, params, credentials = login_open_sheet(GDOCS_OAUTH_JSON, GDOCS_SPREADSHEET_NAME)
	
	except KeyboardInterrupt:
	
		print( "Quit - Cleaning up GPIO")
		
		#Turn everything OFF

		last_cool_time = UpdateDevice(COOL_PIN, OFF)
		last_heat_time = UpdateDevice(HEAT_PIN, OFF)
		last_humid_time = UpdateDevice(HUMIDIFIER_PIN, OFF)
		last_air_pump_off_time = UpdateDevice(AIR_PUMP_PIN, OFF)
		last_circ_time = UpdateDevice(CIRC_FAN_PIN, OFF)

		# Reset GPIO settings
		GPIO.cleanup()
	
		sys.exit (0)
		
		
		
		
		
		
		

      
	
