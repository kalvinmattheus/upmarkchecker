#! /usr/bin/env python3

# This will check for new marks and send an email notification when a new
# mark has been found (as retrieved from UP website)

# This needs to be done using selenium which allows programatically executing
# actions in a browser (in this case chrome) because the marks have to be
# retrieved interactively from the UP portal

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import re
import os
import sys
import time

list_page = 'https://upnet.up.ac.za/psc/pscsmpra/EMPLOYEE/HRMS/c/NUI_FRAMEWORK.PT_LANDINGPAGE.GBL'
credentials = 'creds'
headless = True
refresh_rate = 5*60 # in seconds
retry_rate = 24*60*60 # in seconds

cred_instructions = "add your UP portal username (with \"u\") on the first line, your UP portal password on the second and preferred notification email address (optional) on the third line."
correct_password = False


if not os.path.isfile(credentials):
    print("Credentials file not found, please create \"{}\" and".format(credentials), cred_instructions)
    sys.exit(1)

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
    print("The {}".format(credentials), "file isn\'t valid", "please create a \"{}\" file and".format(credentials), cred_instructions)
    sys.exit(1)

browser = None

class elements_has_css_class(object):
  def __init__(self, css_class):
    self.css_class = css_class

  def __call__(self, driver):
    elements = driver.find_elements_by_css_selector('div.ps-htmlarea')
    if len(elements) >= 2:
        return elements
    else:
        return False

def login():
    print("Starting browser")
    global browser
    if headless:
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        browser = webdriver.Chrome('/usr/lib/chromium-browser/chromedriver', chrome_options=chrome_options)
    else:
        browser = webdriver.Chrome('/usr/lib/chromium-browser/chromedriver')
    browser.get(list_page)
    print("Logging in")
    browser.find_element_by_id("userid_placeholder").send_keys(username)
    browser.find_element_by_id("password").send_keys(password)
    browser.find_element_by_id("loginbutton").click()
    try:
        try:
            WebDriverWait(browser, 60).until(EC.presence_of_element_located((By.ID, 'win0divPTNUI_LAND_REC14$grid$0')))
        except Exception:
            print("Trying old password method")
            WebDriverWait(browser, 60).until(EC.text_to_be_present_in_element((By.ID, 'sso_description'), "proceed"))
            browser.find_element_by_partial_link_text("proceed").click()
            WebDriverWait(browser, 60).until(EC.presence_of_element_located((By.ID, 'win0divPTNUI_LAND_REC14$grid$0')))
    except Exception:
        if correct_password:
            send_mail("Hi " + username + ", the script was unable to log into the UP Portal.")
        else:
            print("Unable to log in")
        browser.close()
        sys.exit(1)
    correct_password = True
    print("Successfully logged in")

def get_mark():
    print("Getting latest mark")
    browser.get(list_page)
    browser.switch_to.default_content()
    WebDriverWait(browser, 60).until(elements_has_css_class("div.ps-htmlarea"))
    items = browser.find_elements_by_css_selector('div.ps-htmlarea')
    if len(items) == 0:
        send_mail("Hi " + username + ", no marks were found, please check the script.")
        browser.close()
        sys.exit(1)
    for i in items:
        item = i.text
        if re.search(r'\w{3}\s\d{3}:\s', item):
            print("Current mark: " + item)
            return item
    send_mail("Hi " + username + ", div.ps-htmlarea was not found, please check the script.")
    browser.close()
    sys.exit(1)
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
        login()
        mark = get_mark()
        new_mark = mark
        send_mail("Script successfully activated for " + username + ".")
        while True:
            while mark == new_mark: 
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
        print("Script closed due to error")
        send_mail("Script encountered an error for " + username + ".\nRetrying in " + str(retry_rate/60/60) + " hours.")
        browser.close()
        correct_password = False
    time.sleep(retry_rate)

