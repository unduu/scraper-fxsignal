from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.support import ui
from time import sleep

import json
import smtplib
import datetime
import configparser

import mysql.connector
from mysql.connector import errorcode

from twilio.rest import Client

env = "DEV"
configParser = configparser.RawConfigParser()   
configFilePath = 'config.txt'
configParser.read(configFilePath)

# Twilio
account_sid = configParser.get(env, "twilio_sid")
auth_token = configParser.get(env, "twilio_token")

# Mysql
userdb = configParser.get(env, "database_user")
passdb = configParser.get(env, "database_pass")
hostdb = configParser.get(env, "database_host")
database = configParser.get(env, "database_name")

# Tradingview
pair = "USDJPY"
time = "4 hours"

# User info
phone = "+6285255753539"

# display = Display(visible=0, size=(800, 600))
# display.start()

def get_technical_summary(symbol, time):
	print("["+datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%S")+"] "+"Scraping "+symbol+" timeframe "+time)
	url = 'https://www.tradingview.com/symbols/'+str(symbol)+'/technicals/'
	timeframe_list = ['1 minute','5 minutes', '15 minutes','1 hour','4 hours', '1 day', '1 week', '1 month'] 

	if time not in timeframe_list:
		return ""

	timeframe = timeframe_list.index(time) + 1

	if env == "PROD":
		# Production
		driver = webdriver.Chrome()
	elif env == "DEV":
		# Development 
		driver = webdriver.Firefox()

	driver.get(url)
    
	timeframe_button = driver.find_element_by_xpath("//div[@class='tabsWrap-1nrUwwqy-']/div/div["+str(timeframe)+"]")

	sleep(5)
	
	timeframe_button.click()
	wait = ui.WebDriverWait(driver, 10)

	sleep(5)

	wait.until(lambda driver: driver.find_element_by_xpath('//div[@class="speedometersContainer-1EFQq-4i-"]/div[2]/span[2]'))

	summary_element = driver.find_element_by_xpath('//div[@class="speedometersContainer-1EFQq-4i-"]/div[2]/span[2]')
	summary = summary_element.text

	last_price_element = driver.find_element_by_xpath('//div[@class="tv-category-header__main-price-content"]/div/div/div')
	last_price = last_price_element.text

	driver.close()

	print("["+datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%S")+"] "+"Get summary result = "+summary+" with price = "+last_price)

	return {"action" : summary, "last_price" : last_price};

def send_email(to):
	print("Send email to : "+to)
	gmail_user = configParser.get(env, "email_user")
	gmail_password = configParser.get(env, "email_pass")

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

	    print("["+datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%S")+"] "+"Email sent!")
	except Exception as e:
	    print("["+datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%S")+"] "+"Something went wrong..."+str(e))

def send_via_whatsapp(receiver_number, message):
	
	# client credentials are read from TWILIO_ACCOUNT_SID and AUTH_TOKEN
	client = Client(account_sid, auth_token)

	# this is the Twilio sandbox testing number
	from_whatsapp_number='whatsapp:'+configParser.get(env, "phone_sender")
	# replace this number with your own WhatsApp Messaging number
	to_whatsapp_number='whatsapp:'+receiver_number

	client.messages.create(body=message,
	                       from_=from_whatsapp_number,
	                       to=to_whatsapp_number)

def send_via_sms(to_number, message):
	
	# client credentials are read from TWILIO_ACCOUNT_SID and AUTH_TOKEN
	client = Client(account_sid, auth_token)

	client.messages.create(messaging_service_sid='MG4fc48c0cbeb187ba7b12cf7731715e94', 
							body=message,
	                       	to=to_number)

def insert_summary(data):
	print("["+datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%S")+"] "+"Insert new summary to db")
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
		    print("["+datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%S")+"] "+"Something is wrong with your user name or password")
		elif err.errno == errorcode.ER_BAD_DB_ERROR:
		    print("["+datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%S")+"] "+"Database does not exist")
		else:
		    print(err)
	else:
		cnx.close()

def get_latest_summary(pair):
	print("["+datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%S")+"] "+"Get previous summary from db")
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
			print("["+datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%S")+"] "+"Something is wrong with your user name or password")
		elif err.errno == errorcode.ER_BAD_DB_ERROR:
			print("["+datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%S")+"] "+"Database does not exist")
		else:
			print(err)
	finally:
		cnx.close()


# Scrape tradingview technical analyst page
summary = get_technical_summary(pair, time)
current_status = summary['action']
# print(pair+" : "+time+" = "+current_status)

# Get latest data from a pair
latest_summary = get_latest_summary("usdjpy")
print("["+datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%S")+"] "+"Check if signal changed")
if latest_summary is not None:
	if latest_summary['status'] != current_status:
		print("["+datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%S")+"] "+"Signal changed, notify user : ")
		msg = "The Professor - " + current_status + " " + pair + " " + time + ' ' + summary['last_price']
		# send_via_whatsapp(phone, msg)
		send_via_sms(phone, msg)

# Insert to database	print(datetime.datetime.now()+" Insert data to db")

created = datetime.datetime.now()
summary = {"source": "tradingview.com", "status": current_status, "created" : created, "pair" : pair}
insert_summary(summary)

# New line
print("\n")
