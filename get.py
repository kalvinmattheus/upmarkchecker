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

check_up = True
check_ams = True
up_page = 'https://upnet.up.ac.za/psc/pscsmpra/EMPLOYEE/HRMS/c/NUI_FRAMEWORK.PT_LANDINGPAGE.GBL'
ams_page = 'https://ams.up.ac.za/modules/'
credentials = 'creds'
headless = False
refresh_rate = 10*60 # in seconds
retry_rate = 24*60*60 # in seconds

correct_password = False
up_browser = ams_browser = None


def creds():
    username = up_password = ams_password = ""
    good_username = False
    good_up_password = False
    good_ams_password = False
    good_email = False
    while not good_username:
        username = input("Please enter your UP portal username: ")
        if len(username) == 9:
            if username[0] == 'u':
                good_username = True
        if not good_username:
            print("Please enter a valid username (starting with u)")
    while not good_up_password:
        up_password = getpass.getpass("UP Portal password: ")
        if len(up_password) >= 8:
            good_up_password = True
        if not good_up_password:
            print("Passwords must be at least 8 characters long")
    while not (good_ams_password) and (check_ams):
        ams_password = getpass.getpass("AMS password: ")
        if len(ams_password) >= 12:
            good_ams_password = True
        if not good_ams_password:
            print("Passwords must be at least 12 characters long")
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
    f.write(up_password + "\r\n")
    f.write(ams_password + "\r\n")
    f.write(to_email)
    f.close()

def get_creds():
    while not os.path.isfile(credentials):
        print("For this script to access your UP marks, your login credentials are required:")
        creds()
    global username, up_password, ams_password, to_email
    try:
        with open(credentials, 'r') as f:
            lines = [l.strip() for l in f.readlines()]
            if len(lines) == 4:
                username, up_password, ams_password, to_email = lines
                if to_email == "":
                    to_email = username + "@tuks.co.za"
            else:
                raise ValueError("Invalid {}".format(credentials), "file")
            if username[0] != "u":
                raise ValueError("Invalid username (prefix with \"u\")")
            if len(up_password) < 8:
                raise ValueError("Invalid UP Portal password (should be at least 8 characters long)")
            if (len(ams_password) < 12) and (check_ams):
                raise ValueError("Invalid AMS password (should be at least 12 characters long)")
    except Exception:
        print("The {}".format(credentials), "file isn\'t valid,", "please create a \"{}\"".format(credentials), "file with the following 4 (four) lines:\n    Your UP Portal username (with a \"u\")\n    Your UP Portal password\n    Your AMS password (optional)\n    Preferred notification email address (optional)\nOr simply delete the \"{}\"".format(credentials), "file to restart the setup wizard.")
        sys.exit(0)
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

def start_up_browser():
    try:
        try_connect()
    except OSError:
        print("No internet connection found, please connect this computer to the internet.")
        raise Exception("Not connected to internet")
    global up_browser
    if headless:
        print("Starting UP Portal browser in headless mode")
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        try:
            up_browser = webdriver.Chrome('/usr/lib/chromium-browser/chromedriver', options=chrome_options)
        except:
            up_browser = webdriver.Chrome('/usr/bin/chromedriver', options=chrome_options)
    else:
        print("Starting UP Portal browser")
        try:
            up_browser = webdriver.Chrome('/usr/lib/chromium-browser/chromedriver')
        except:
            up_browser = webdriver.Chrome('/usr/bin/chromedriver')
        
def start_ams_browser():
    try:
        try_connect()
    except OSError:
        print("No internet connection found, please connect this computer to the internet.")
        raise Exception("Not connected to internet")
    global ams_browser
    if headless:
        print("Starting AMS browser in headless mode")
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        try:
            ams_browser = webdriver.Chrome('/usr/lib/chromium-browser/chromedriver', options=chrome_options)
        except:
            ams_browser = webdriver.Chrome('/usr/bin/chromedriver', options=chrome_options)
    else:
        print("Starting AMS browser")
        try:
            ams_browser = webdriver.Chrome('/usr/lib/chromium-browser/chromedriver')
        except:
            ams_browser = webdriver.Chrome('/usr/bin/chromedriver')

def login_up():
    up_browser.get(up_page)
    print("Logging into UP Portal")
    up_browser.find_element_by_id("userid_placeholder").send_keys(username)
    up_browser.find_element_by_id("password").send_keys(up_password)
    up_browser.find_element_by_id("loginbutton").click()
    try:
        WebDriverWait(up_browser, 60).until(EC.presence_of_element_located((By.ID, 'win0divPTNUI_LAND_REC14$grid$0')))
    except Exception:
        print("Trying old password method")
        try:
            WebDriverWait(up_browser, 6).until(EC.text_to_be_present_in_element((By.ID, 'sso_description'), "proceed"))
        except Exception:
            global correct_password
            if correct_password:
                send_mail("UP Mark Checker Script Error", "Hi " + username + ", the script was unable to log into the UP Portal.")
            up_browser.close()
            print("Your login has failed, please re-enter your login credentials")
            creds()
            get_creds()
            login_up()
            return
            pass
        print("Using old password method")
        up_browser.find_element_by_partial_link_text("proceed").click()
        WebDriverWait(up_browser, 60).until(EC.presence_of_element_located((By.ID, 'win0divPTNUI_LAND_REC14$grid$0')))
    correct_password = True
    print("Successfully logged into UP Portal")

def login_ams():
    ams_browser.get(ams_page)
    print("Logging into AMS")
    ams_browser.find_element_by_name('username').send_keys(username)
    ams_browser.find_element_by_name('password').send_keys(ams_password)
    ams_browser.find_element_by_name('password').submit()
    try:
        WebDriverWait(ams_browser, 60).until(EC.presence_of_element_located((By.XPATH, '//tbody/tr/td/a')))
    except Exception:
        global correct_password
        if correct_password:
            send_mail("UP Mark Checker Script Error", "Hi " + username + ", the script was unable to log into AMS.")
        ams_browser.close()
        print("Your login has failed, please re-enter your login credentials")
        creds()
        get_creds()
        ams_login()
        return
        pass
    print("Successfully logged into AMS")

def get_up_mark(first = True):
    print("Getting latest UP Portal mark")
    up_browser.get(up_page)
    up_browser.switch_to.default_content()
    try:
        WebDriverWait(up_browser, 60).until(elements_has_css_class('div.ps-htmlarea'))
        items = up_browser.find_elements_by_css_selector('div.ps-htmlarea')
        for i in items:
            item = i.text
            if re.search(r'\w{3}\s\d{3}:\s', item):
                print("Current UP Portal mark: " + item)
                return item
    except Exception:
        try:
            print("div.ps-htmlarea was not found, checking for error message...")
            WebDriverWait(up_browser, 6).until(EC.presence_of_element_located((By.ID, 'win0divPTNUI_LAND_REC_GROUPLET$2')))
            up_browser.find_element_by_id("win0divPTNUI_LAND_REC_GROUPLET$2").click()
            WebDriverWait(up_browser, 60).until(EC.presence_of_element_located((By.ID, 'shortmsg')))
            WebDriverWait(up_browser, 60).until(EC.presence_of_element_located((By.ID, 'othermsg')))
            WebDriverWait(up_browser, 60).until(EC.presence_of_element_located((By.ID, 'longmsg')))
            print("Error found:", up_browser.find_element_by_id('shortmsg').text, up_browser.find_element_by_id('othermsg').text, up_browser.find_element_by_id('longmsg').text)
        except Exception:
            if first: # not tested
                print("Error detected on page, reloading...")
                return get_up_mark(False)
                pass
            else:
                print("Error, no \"div.ps-htmlarea\" or error message was found")
                pass
    raise Exception("div.ps-htmlarea was not found")
    return "0"

def get_ams_mark(first = True):
    print("Getting latest AMS mark")
    try:
        ams_marks = []
        ams_browser.get(ams_page)
        ams_browser.switch_to.default_content()
        modules = ams_browser.find_elements_by_xpath('//tbody/tr/td/a')
        if len(modules) < 1:
            print("No modules found on AMS")
            raise ValueError("No modules found")
        for i in range(len(modules)):
            print ("Checking " + modules[i].text)
            ams_browser.get(modules[i].get_attribute('href'))
            WebDriverWait(ams_browser, 60).until(EC.presence_of_element_located((By.XPATH, '//table//td')))
            for tbl in ams_browser.find_elements_by_xpath('//table'):
                if len(tbl.find_elements_by_tag_name('th')) > 0:
                    if tbl.find_elements_by_tag_name('th')[0].text == 'Assessment ID':
                        for tr in tbl.find_elements_by_tag_name('tr'):
                            tds = tr.find_elements_by_tag_name('td')
                            if len(tds) > 0:
                                #print([td.text for td in tds]) # remove this debug line
                                ams_marks.append([td.text for td in tds])
            ams_browser.get(ams_page)
            WebDriverWait(ams_browser, 60).until(EC.presence_of_element_located((By.XPATH, '//tbody/tr/td/a')))
            modules = ams_browser.find_elements_by_xpath('//tbody/tr/td/a')
        print("Current AMS marks logged")
        return ams_marks
    except Exception:
        if first: # not tested
            print("Error detected on page, reloading...")
            return get_ams_mark(False)
            pass
        else:
            print("Error, module table was not found")
            pass
    raise Exception("module table was not found")
    return "0"
        
def send_mail(subject, message):
    print("Sending email with subject: \"" + subject + "\" and message: \"" + message + "\"")
    try:
        msg = MIMEMultipart()
        msg['From'] = username + "@tuks.co.za"
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com: 587')
        server.starttls()
        server.login(msg['From'], up_password)
        server.sendmail(msg['From'], msg['To'], msg.as_string())
        server.quit()
    except Exception:
        print("Email server isn\'t working, be sure to allow less secure apps at https://www.google.com/settings/security/lesssecureapps for {}".format(msg['From']))
        if check_up:
            up_browser.close()
        if check_ams:
            ams_browser.close()
        sys.exit(1)
    print("Successfully sent email")

while True:
    try:
        get_creds()
        start_up_browser()
        print("Testing UP Portal and email service login credentials")
        login_up()
        if check_up:
            up_mark = get_up_mark()
            new_up_mark = up_mark
        else:
            up_browser.close()
        if check_ams:
            start_ams_browser()
            login_ams()
            ams_mark = get_ams_mark()
            new_ams_mark = ams_mark
        send_mail("UP Mark Checker Script Activated", "Script successfully activated for " + username + ".\n\n" + ("Current UP Portal mark: " + up_mark if check_up else "") + ("\n\nCurrent AMS marks: \n" + str(ams_mark) if check_ams else ""))
        while True:
            print("Waiting " + (str(refresh_rate) + " seconds" if refresh_rate < 120 else str(refresh_rate/60) + " minutes" if refresh_rate/60 <= 60 else str(refresh_rate/60/60) + " hours") + " before checking for new marks. -- Ctrl + c to exit.")
            time.sleep(refresh_rate)
            if check_up:
                try:
                    new_up_mark = get_up_mark()
                except Exception:
                    print("Error detected, probably logged out, retrying...")
                    up_browser.close()
                    start_up_browser()
                    login_up()
                    new_up_mark = get_up_mark()
                    pass
                if up_mark != new_up_mark:
                    up_mark = new_up_mark
                    send_mail("UP Mark Checker Script has a new Mark", "Hi " + username + ", you have a new mark available on the UP Portal:\n    " + up_mark)
                else:
                    print("No new UP Portal marks detected")
            if check_ams:
                try:
                    new_ams_mark = get_ams_mark()
                except Exception:
                    print("Error detected, probably logged out, retrying...")
                    ams_browser.close()
                    start_ams_browser()
                    login_ams()
                    new_ams_mark = get_ams_mark()
                    pass
                if ams_mark != new_ams_mark:
                    ams_mark = new_ams_mark
                    send_mail("UP Mark Checker Script has a new Mark", "Hi " + username + ", you have a new mark available on AMS:\n    " + ams_page + "\n\n" + str(ams_mark))
                else:
                    print("No new AMS marks detected")
    except Exception:
        traceback.print_exc() # remove debug line
        print("Script stopped due to error at " + str(datetime.now()) + ". Retrying in " + str(retry_rate/60/60) + " hours.")
        try:
            try_connect()
            send_mail("UP Mark Checker Script Error", "Script encountered an error for " + username + ".\n    Retrying in " + str(retry_rate/60/60) + " hours.")
        except OSError:
            print("No internet connection, could not send error email.")
        if check_up:
            up_browser.close()
        if check_ams:
            ams_browser.close()
        correct_password = False
    time.sleep(retry_rate)

