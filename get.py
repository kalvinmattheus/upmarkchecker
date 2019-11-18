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
import os
import sys
import time

list_page = 'https://upnet.up.ac.za/psc/pscsmpra/EMPLOYEE/HRMS/c/NUI_FRAMEWORK.PT_LANDINGPAGE.GBL'
raw_dir = 'raw_lists'
credentials = 'creds'

if not os.path.isfile(credentials):
    print("Credentials file not found, please create \"{}\" and".format(credentials),
            "add your UP username on the first line, your UP password on the second, true/false on the third indicating old password and preffered notification email address on the forth line")
    sys.exit(1)

try:
    with open(credentials, 'r') as f:
        lines = [l.strip() for l in f.readlines()]
        if len(lines) == 3:
            username, password, old_pass = lines
            to_email = username + "@tuks.co.za"
        elif len(lines) == 4:
            username, password, old_pass, to_email = lines
        else:
            raise ValueError("Invalid {}".format(credentials), "file")
except:
    print("The {}".format(credentials), "file isn\'t valid", "please create \"{}\" and".format(credentials),
            "add your UP username on the first line, your UP password on the second, true/false on the third indicating old password and preffered notification email address on the forth line")
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
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    global browser
    browser = webdriver.Chrome('./chromedriver', chrome_options=chrome_options)
    browser.get(list_page)
    print("Logging in")
    browser.find_element_by_id("userid_placeholder").send_keys(username)
    browser.find_element_by_id("password").send_keys(password)
    browser.find_element_by_id("loginbutton").click()
    try:
        if old_pass:
            WebDriverWait(browser, 5).until(EC.text_to_be_present_in_element((By.ID, 'sso_description'), "proceed"))
            browser.find_element_by_partial_link_text("proceed").click()
        WebDriverWait(browser, 60).until(EC.presence_of_element_located((By.ID, 'win0divPTNUI_LAND_REC14$grid$0')))
    except:
        print("Unable to log in")
        browser.close()
        sys.exit(1)
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
        if "% - " in item and ": " in item:
            print("Current mark: " + item)
            return i.text
    send_mail("Hi " + username + ", div.ps-htmlarea was not found, please check the script.")
    return "0"
        
def send_mail(message):
    print("Sending email with: " + message)
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
    except:
        print("Email server isn\'t working, be sure to allow less secure apps at https://www.google.com/settings/security/lesssecureapps for {}".format(msg['From']))
        browser.close()
        sys.exit(1)
    print("Successfully sent email")

try:
    login()
    mark = get_mark()
    new_mark = mark
    send_mail("Script successfully activated for " + username)
    while True:
        while mark == new_mark: 
            time.sleep(60)
            try:
                new_mark = get_mark()
            except:
                login()
                new_mark = get_mark()
        mark = new_mark
        send_mail("Hi " + username + ", you have a new mark available:\n    " + mark)
except:
    send_mail("Script encountered an error for " + username)
    browser.close()
    sys.exit(1)

