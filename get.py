#! /usr/bin/env python3

# This will check for new marks and send an email notification when a new
# mark has been found (as retrieved from UP website)

# This needs to be done using selenium which allows programatically executing
# actions in a browser (in this case chromium) because the marks have to be
# retrieved interactively from the UP portal

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import socket
import smtplib
import re
import os
import sys
import time
import getpass
import signal
signal.signal(signal.SIGINT, lambda x, y: sys.exit(0))

list_page = 'https://upnet.up.ac.za/psc/pscsmpra/EMPLOYEE/HRMS/c/NUI_FRAMEWORK.PT_LANDINGPAGE.GBL'
credentials = 'creds'
headless = True
refresh_rate = 5*60 # in seconds
retry_rate = 24*60*60 # in seconds

correct_password = False
browser = None


def creds():
    good_username = False
    good_password = False
    good_email = False
    while not good_username:
        username = input("Please enter your UP portal username: ")
        if len(username) == 9:
            if username[0] == 'u':
                good_username = True
        if not good_username:
            print("Please enter a valid username (starting with u)")
    while not good_password:
        password = getpass.getpass("Password: ")
        if len(password) >= 8:
            good_password = True
        if not good_password:
            print("Passwords must be at least 8 characters long")
    while not good_email:
        to_email = input("Please enter a notiftcation email (default: " + username + "@tuks.co.za): ")
        if to_email == "":
            to_email = username + "@tuks.co.za"
            good_email = True
        elif re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", to_email):
            good_email = True
        if not good_email:
            print("Please enter a valid email address")
    f = open(credentials, "w+")
    f.write(username + "\r\n")
    f.write(password + "\r\n")
    f.write(to_email)
    f.close()

def get_creds():
    while not os.path.isfile(credentials):
        print("For this script to access your UP marks, your login credentials are required:")
        creds()
    global username, password, to_email
    try:
        with open(credentials, 'r') as f:
            lines = [l.strip() for l in f.readlines()]
            if len(lines) == 2:
                username, password = lines
                to_email = username + "@tuks.co.za"
            elif len(lines) == 3:
                username, password, to_email = lines
            else:
                raise ValueError("Invalid {}".format(credentials), "file")
            if username[0] != "u":
                raise ValueError("Invalid username (prefix with \"u\")")
    except Exception:
        print("The {}".format(credentials), "file isn\'t valid", "please create a \"{}\" file and".format(credentials), "add your UP portal username (with \"u\") on the first line, your UP portal password on the second and preferred notification email address (optional) on the third line.")
        sys.exit(1)
    print("A valid", credentials, "file was found")

class elements_has_css_class(object):
  def __init__(self, css_class):
    self.css_class = css_class

  def __call__(self, driver):
    elements = driver.find_elements_by_css_selector('div.ps-htmlarea')
    if len(elements) >= 2:
        return elements
    else: 
        return False

def try_connect():
    print("Testing internet connection")
    socket.create_connection(("www.google.com", 80))

def login():
    global browser
    if headless:
        print("Starting browser in headless mode")
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        try:
            browser = webdriver.Chrome('/usr/lib/chromium-browser/chromedriver', options=chrome_options)
        except:
            browser = webdriver.Chrome('/usr/bin/chromedriver', options=chrome_options)
    else:
        print("Starting browser")
        try:
            browser = webdriver.Chrome('/usr/lib/chromium-browser/chromedriver')
        except:
            browser = webdriver.Chrome('/usr/bin/chromedriver')
    try:
        try_connect()
    except OSError:
        print("No internet connection found, please connect this computer to the internet.")
        raise Exception("Not connected to internet")
    browser.get(list_page)
    print("Logging in")
    browser.find_element_by_id("userid_placeholder").send_keys(username)
    browser.find_element_by_id("password").send_keys(password)
    browser.find_element_by_id("loginbutton").click()
    try:
        WebDriverWait(browser, 60).until(EC.presence_of_element_located((By.ID, 'win0divPTNUI_LAND_REC14$grid$0')))
    except Exception:
        print("Trying old password method")
        try:
            WebDriverWait(browser, 6).until(EC.text_to_be_present_in_element((By.ID, 'sso_description'), "proceed"))
        except Exception:
            global correct_password
            if correct_password:
                send_mail("Hi " + username + ", the script was unable to log into the UP Portal.")
            browser.close()
            print("Your login has failed, please re-enter your login credentials")
            creds()
            get_creds()
            login()
            return
        print("Using old password method")
        browser.find_element_by_partial_link_text("proceed").click()
        WebDriverWait(browser, 60).until(EC.presence_of_element_located((By.ID, 'win0divPTNUI_LAND_REC14$grid$0')))
    correct_password = True
    print("Successfully logged in")

def get_mark():
    print("Getting latest mark")
    browser.get(list_page)
    browser.switch_to.default_content()
    try:
        WebDriverWait(browser, 60).until(elements_has_css_class('div.ps-htmlarea'))
        items = browser.find_elements_by_css_selector('div.ps-htmlarea')
        for i in items:
            item = i.text
            if re.search(r'\w{3}\s\d{3}:\s', item):
                print("Current mark: " + item)
                return item
    except Exception:
        try:
            print("div.ps-htmlarea was not found, checking for error message...")
            WebDriverWait(browser, 6).until(EC.presence_of_element_located((By.ID, 'win0divPTNUI_LAND_REC_GROUPLET$2')))
            browser.find_element_by_id("win0divPTNUI_LAND_REC_GROUPLET$2").click()
            WebDriverWait(browser, 60).until(EC.presence_of_element_located((By.ID, 'shortmsg')))
            WebDriverWait(browser, 60).until(EC.presence_of_element_located((By.ID, 'othermsg')))
            WebDriverWait(browser, 60).until(EC.presence_of_element_located((By.ID, 'longmsg')))
            print("Error found:", browser.find_element_by_id('shortmsg').text, browser.find_element_by_id('othermsg').text, browser.find_element_by_id('longmsg').text)
        except Exception:
            send_mail("Hi " + username + ", no \"div.ps-htmlarea\" or error message was found, please check the script.")
            browser.close()
            sys.exit(1)
    raise Exception("div.ps-htmlarea was not found")
    return "0"
        
def send_mail(message):
    print("Sending email with message: " + message)
    try:
        msg = MIMEMultipart()
        msg['From'] = username + "@tuks.co.za"
        msg['To'] = to_email
        msg['Subject'] = "UP New Mark Script"
        msg.attach(MIMEText(message, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com: 587')
        server.starttls()
        server.login(msg['From'], password)
        server.sendmail(msg['From'], msg['To'], msg.as_string())
        server.quit()
    except Exception:
        print("Email server isn\'t working, be sure to allow less secure apps at https://www.google.com/settings/security/lesssecureapps for {}".format(msg['From']))
        browser.close()
        sys.exit(1)
    print("Successfully sent email")

while True:
    try:
        get_creds()
        login()
        mark = get_mark()
        new_mark = mark
        send_mail("Script successfully activated for " + username + ".")
        while True:
            while mark == new_mark: 
                print("Waiting " + (str(refresh_rate) + " seconds" if refresh_rate <= 60 else str(refresh_rate/60) + " minutes" if refresh_rate/60 <= 60 else str(refresh_rate/60/60) + " hours") + " before checking for new marks. -- Ctrl + c to exit.")
                time.sleep(refresh_rate)
                try:
                    new_mark = get_mark()
                except Exception:
                    browser.close()
                    login()
                    new_mark = get_mark()
                    continue
            mark = new_mark
            send_mail("Hi " + username + ", you have a new mark available:\n    " + mark)
    except Exception:
        print("Script closed due to error at " + str(datetime.now()) + ". Retrying in " + str(retry_rate/60/60) + " hours.")
        try:
            try_connect()
            send_mail("Script encountered an error for " + username + ".\nRetrying in " + str(retry_rate/60/60) + " hours.")
        except OSError:
            print("No internet connection, could not send error email.")
        browser.close()
        correct_password = False
    time.sleep(retry_rate)

