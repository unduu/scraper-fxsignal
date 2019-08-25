#from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.support import ui
from time import sleep

import json
import smtplib
import datetime

import mysql.connector
from mysql.connector import errorcode

from twilio.rest import Client

# Twilio
account_sid = "AC8d1daa1db11271fc80bd0a8ed2c05464"
auth_token = "b2db36b23c9515630fe90cefc23b003e"

# Mysql
userdb = "root"
passdb = "biteme10"
hostdb = "127.0.0.1"
database = "scraping"

# Tradingview
pair = 'USDJPY'
time = '4 hours'

# User info
phone = '+6285255753539'

# display = Display(visible=0, size=(800, 600))
# display.start()

def get_technical_summary(symbol, time):
	print("Scraping "+symbol+" timeframe "+time)
	url = 'https://www.tradingview.com/symbols/'+str(symbol)+'/technicals/'
	timeframe_list = ['1 minute','5 minutes', '15 minutes','1 hour','4 hours', '1 day', '1 week', '1 month'] 

	if time not in timeframe_list:
		return ""

	timeframe = timeframe_list.index(time) + 1

	# Production
	# driver = webdriver.Chrome()
	# Development 
	driver = webdriver.Firefox()

	driver.get(url)
    
	timeframe_button = driver.find_element_by_xpath("//div[@class='tabsWrap-1nrUwwqy-']/div/div["+str(timeframe)+"]")

	timeframe_button.click()
	wait = ui.WebDriverWait(driver, 10)

	sleep(5)

	wait.until(lambda driver: driver.find_element_by_xpath('//div[@class="speedometersContainer-1EFQq-4i-"]/div[2]/span[2]'))

	summary_element = driver.find_element_by_xpath('//div[@class="speedometersContainer-1EFQq-4i-"]/div[2]/span[2]')
	summary = summary_element.text

	driver.close()

	print("Get summary result = "+summary)

	return summary;

def send_email(to):
	print("Send email to : "+to)
	gmail_user = 'andifaizal88@gmail.com'
	gmail_password = 'Iambringdarkness30'

	sent_from = gmail_user
	subject = 'Completed email'
	body = 'Hey, whats up?\n\n- You'

	email_text = ("from: %s\n"
				"to: %s\n"
				"Subject: %s\n"
				"%s"
				% (sent_from, ", ".join(to), subject, body))

	try:
	    server = smtplib.SMTP_SSL('smtp.gmprint(datetime.datetime.now()+" Scraping "+symbol+" timeframe "+time)ail.com', 465)
	    server.ehlo()
	    server.login(gmail_user, gmail_password)
	    server.sendmail(sent_from, to, email_text)
	    server.close()

	    print('Email sent!')
	except Exception as e:
	    print('Something went wrong...'+str(e))

def send_via_whatsapp(receiver_number, message):
	
	# client credentials are read from TWILIO_ACCOUNT_SID and AUTH_TOKEN
	client = Client(account_sid, auth_token)

	# this is the Twilio sandbox testing number
	from_whatsapp_number='whatsapp:+14155238886'
	# replace this number with your own WhatsApp Messaging number
	to_whatsapp_number='whatsapp:'+receiver_number

	client.messages.create(body=message,
	                       from_=from_whatsapp_number,
	                       to=to_whatsapp_number)

def insert_summary(data):
	print("Insert new summary to db")
	try:
		# open the database connection
		cnx = mysql.connector.connect(user=userdb, password=passdb, host=hostdb, database=database)

		insert_sql = ("INSERT INTO technical (source, status, created, pair) " +
		              "VALUES (%(source)s, %(status)s, %(created)s, %(pair)s)")

		# insert data to db
		cursor = cnx.cursor()
		cursor.execute(insert_sql, data)

		# commit the new records
		cnx.commit()
		
		# close the cursor and connection
		cursor.close()
		cnx.close()

	except mysql.connector.Error as err:
		if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
		    print("Something is wrong with your user name or password")
		elif err.errno == errorcode.ER_BAD_DB_ERROR:
		    print("Database does not exist")
		else:
		    print(err)
	else:
		cnx.close()

def get_latest_summary(pair):
	print("Get previous summary from db")
	data = {"pair" : pair}
	try:
		cnx = mysql.connector.connect(user=userdb, password=passdb, host=hostdb, database=database)
		cursor = cnx.cursor(dictionary=True)
		query = "SELECT * FROM technical WHERE pair = %(pair)s ORDER BY id DESC LIMIT 1"
		cursor.execute(query, data)
		result = cursor.fetchone()

		# close the cursor and connection
		cursor.close()
		cnx.close()

		return result

	except mysql.connector.Error as err:
		if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
			print("Something is wrong with your user name or password")
		elif err.errno == errorcode.ER_BAD_DB_ERROR:
			print("Database does not exist")
		else:
			print(err)
	finally:
		cnx.close()


# Scrape tradingview technical analyst page
current_status = get_technical_summary(pair, time)
# print(pair+" : "+time+" = "+current_status)

# Get latest data from a pair
latest_summary = get_latest_summary("usdjpy")
print("Check if signal changed")
if latest_summary is not None:
	if latest_summary['status'] != current_status:
		print("Signal changed, notify user : ")
		msg = latest_summary['status'] + ' ' + pair + ' ' + time
		send_via_whatsapp(phone, msg)

# Insert to database	print(datetime.datetime.now()+" Insert data to db")

created = datetime.datetime.now()
summary = {"source": "tradingview.com", "status": current_status, "created" : created, "pair" : pair}
insert_summary(summary)