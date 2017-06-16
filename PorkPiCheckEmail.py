# ######################################################################################
#
#   PorkPiCheckEmail.py - Check to see if emailed reboot or shutdown commands
#
# ######################################################################################



import sys
import imaplib
import getpass
import email
import email.header
import datetime
import time
import smtplib
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

EMAIL_ACCOUNT = "your_raspberrypi_email_address@gmail.com"
EMAIL_FOLDER = "Inbox"
PASSWORD = "your_password"

# #######################################################################################
#     process_mailbox
# #######################################################################################

def process_mailbox(M):
    """
    Do something with emails messages in the folder.  
    For the sake of this example, print some headers.
    """

    rv, data = M.search(None, "ALL")
    if rv != 'OK':
        print "No messages found!"
        return

    for num in data[0].split():
        
		rv, data = M.fetch(num, '(RFC822)')
        
		if rv != 'OK':
			print( "ERROR getting message", num)
			return

		msg = email.message_from_string(data[0][1])
        
		
		subject = msg['Subject']
		sender =  msg['From']
		
		if sender == 'sender name <sender_name@gmail.com>' and subject =='reboot':
			send_email("Rebooted by email")	
			cleanup_mailbox_and_logout(M)	
			reboot()
			
		if sender == 'sender name <sender_name@gmail.com>' and subject =='shutdown':
			
			send_email("Shutdown by email")
			cleanup_mailbox_and_logout(M)
			shutdown()

# #######################################################################################
#     cleanup_mailbox_and_logout
# #######################################################################################

def cleanup_mailbox_and_logout(M):
	typ, data = M.search(None, 'ALL')
			
	for num in data[0].split():
	   M.store(num, '+FLAGS', '\\Deleted')
	M.expunge()
	M.close()
	M.logout()
	
	
# #######################################################################################
#     send_email
# #######################################################################################
        
def send_email(send_subject):

	
	fromaddr = "your_raspberrypi_email_address@gmail.com"
	toaddr = "your_email address"
	msg = MIMEMultipart()
	msg['From'] = fromaddr
	msg['To'] = toaddr
	msg['Subject'] = send_subject
	 
	body = send_subject
	msg.attach(MIMEText(body, 'plain'))
	 
	server = smtplib.SMTP('smtp.gmail.com', 587)
	server.starttls()
	server.login(fromaddr, PASSWORD)
	text = msg.as_string()
	server.sendmail(fromaddr, toaddr, text)
	server.quit()

# #######################################################################################
#     Reboot
# #######################################################################################

def reboot():
    command = "/usr/bin/sudo /sbin/shutdown -r now"
    import subprocess
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]
    print output
	
# #######################################################################################
#     shutdown
# #######################################################################################
	
def shutdown():
    command = "/usr/bin/sudo /sbin/shutdown now"
    import subprocess
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]
    print output
	
	
# #######################################################################################
#     Main loop
# #######################################################################################

# login to gmail account

M = imaplib.IMAP4_SSL('imap.gmail.com')
try:
	rv, data = M.login(EMAIL_ACCOUNT, PASSWORD)
except imaplib.IMAP4.error:
	print "LOGIN FAILED!!! "
	sys.exit(1)


# rocess inbox

rv, data = M.select(EMAIL_FOLDER)
if rv == 'OK':
	print "\tCheck email for reboot/shutdown"
	process_mailbox(M)
	
else:
	print "ERROR: Unable to open mailbox ", rv
	
	
M.logout()

	