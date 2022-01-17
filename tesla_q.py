""" Tesla Owner API CLI application using TeslaPy module """

# Author: Tim Dorssers
# Modified for messaging: Bhusan Gupta

from __future__ import print_function
import ast
import logging
import argparse
import json
import os
import smtplib
import time
import sys
import socket
from datetime import datetime
from datetime import timedelta
from dateutil import parser

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

try:
    from selenium import webdriver
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
except ImportError:
    webdriver = None
from teslapy import Tesla, Vehicle

from secrets import *

# EMAIL_TO
# EMAIL_FROM
# SMTP_SERVER
# SMTP_PORT
# SMTP_USER
# SMTP_PASSWORD

message_string = ''
message_subject = ''
mime_message = ''

raw_input = vars(__builtins__).get('raw_input', input)  # Py2/3 compatibility

def custom_auth(url):
    with webdriver.Chrome() as browser:
        browser.get(url)
        WebDriverWait(browser, 300).until(EC.url_contains('void/callback'))
        return browser.current_url

def repeat_to_length(string_to_expand, length):
   return (string_to_expand * (int(length/len(string_to_expand))+1))[:length]

def pad2len(prefix, length):
    if length > len(prefix):
        return ((prefix + ' ' * int(1.4*(length - len(prefix)) ))[:length])
    else:
        return (prefix[:length])

""" Create new line of message per vehicle
    build_alert(car, charging_status, battery_level, odometer, battery_range)"""
def build_alert(car_name, charging_status, battery_level, odometer, battery_range):
    global message_string
    carName = pad2len(car_name,20)

    if charging_status.startswith('Complete'):
        cs = 'Complete'
    elif charging_status.startswith('Charging'):
        cs = 'Charging'
    elif charging_status.startswith('Error:'):
        cs = 'Unknown'
        battery_level = 0
        battery_range = 0
        odometer = 0
    else:
        cs = 'Disconnected'
    message_string += '\n%s %s %s %s %6d' % (carName, battery_range, pad2len(cs, 18), battery_level , odometer)

def setup_alert():
    global message_string
    global message_subject
    message_subject = 'Tesla car status'
    message_string = "\nDaily summary for all Tesla vehicles"
    message_string += "\nDate: %s\nTime: %s" % (datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M:%S"))
    message_string += '\n' + 'Car Name' + ' '*18 +'Range' + ' '*4 + 'Charge Status' + ' '*4 + 'Charge %' + ' '*4 + 'Odometer'

def finish_alert():
    global message_string
    global message_subject
    global mime_message
    message_string += '\nMessage brought to you by %s running on %s\n' % (os.path.basename(__file__), socket.gethostname())
    added_chars = repeat_to_length('_', 200 - len(message_string))
    message_string += added_chars
    mime_message = MIMEText(message_string)
    mime_message['Subject'] = message_subject
    mime_message['From'] = EMAIL_FROM
    #print(repr(mime_message))

def send_alert():
    mailserver = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    mailserver.ehlo()
    mailserver.starttls()
    #print("user ->",SMTP_USER)
    #print("password ->",SMTP_PASSWORD)
    mailserver.login(SMTP_USER, SMTP_PASSWORD)
    for em in EMAIL_TO:
        mime_message['To'] = em
        ret = mailserver.sendmail(EMAIL_FROM, em, mime_message.as_string())
        if ret:
            # print("Did not successfully send message")
            print("message: ",mime_message.as_string())
            exit(-1)
    mailserver.quit()

def main():
    parser = argparse.ArgumentParser(description='Tesla Owner API CLI')
    parser.add_argument('-e', dest='email', help='login email', required=True)
    parser.add_argument('-d', '--debug', action='store_true',
                        help='set logging level to debug')
    args = parser.parse_args()
    default_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO,
                        format=default_format)
    setup_alert()
    with Tesla(args.email) as tesla:
        if webdriver:
            tesla.authenticator = custom_auth
        tesla.fetch_token()
        selected = tesla.vehicle_list()
        #logging.info('%d product(s), %d selected', len(prod), len(selected))
        for i, product in enumerate(selected):
            #print('Product %d:' % i)
            # Show information or invoke API depending on arguments
            if isinstance(product, Vehicle):
                # def sync_wake_up(self, timeout=60, interval=2, backoff=1.15):
                try:
                    product.sync_wake_up(timeout=180, interval=5, backoff=1.2)
                except:
                    # did not wake up?
                    pass
                #print(product)
                #print(product.decode_vin())
                #print(product.get_vehicle_data())
                #parsed = json.loads(product.get_vehicle_data())
                #print(json.dumps(product.get_vehicle_data(), indent=4, sort_keys=True))
                #print(product.get_vehicle_data()["charge_state"]["battery_range"])
                try:
                    charging_state = product.get_vehicle_data()["charge_state"]["charging_state"]
                    battery_level = product.get_vehicle_data()["charge_state"]["usable_battery_level"]
                    battery_range = product.get_vehicle_data()["charge_state"]["battery_range"]
                except:
                    charging_state = 'Error: data retrieval'
                    battery_level = 0
                    battery_range = 0
                
                try:
                    vehicle_name = product.get_vehicle_data()["vehicle_state"]["vehicle_name"]
                    odometer = int(product.get_vehicle_data()["vehicle_state"]["odometer"])
                except:
                    vehicle_name = 'Error retrieving vehicle'
                    odometer = 0
            
                build_alert(
                    vehicle_name,
                    charging_state,
                    battery_level,
                    odometer,
                    battery_range)
    finish_alert()
    send_alert()

if __name__ == "__main__":
    main()
