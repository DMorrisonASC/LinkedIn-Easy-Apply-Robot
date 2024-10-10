import csv
import logging
import traceback
import os
import random
import re
import time
from datetime import datetime, timedelta
from pathlib import Path

import yaml
import pandas as pd
import pyautogui
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from selenium.webdriver.chrome.service import Service as ChromeService
import webdriver_manager.chrome as ChromeDriverManager
ChromeDriverManager = ChromeDriverManager.ChromeDriverManager

log = logging.getLogger(__name__)  # Create a logger object with the current module's name.

def setupLogger() -> None:
    """
    Configures the logging setup for the application. This includes:
    - Setting up log files with timestamps.
    - Creating a log directory if it doesn't exist.
    - Defining log formatting for both file and console output.
    """
    
    # Generate a timestamp string for the log file name, e.g., '10_10_24 14_45_30 '.
    dt: str = datetime.strftime(datetime.now(), "%m_%d_%y %H_%M_%S ")

    # Check if the 'logs' directory exists. If not, create it.
    if not os.path.isdir('./logs'):
        os.mkdir('./logs')

    # Set up basic configuration for logging to a file.
    # Log filename includes the timestamp, and the logs are stored in the 'logs' directory.
    logging.basicConfig(
        filename=('./logs/' + str(dt) + 'applyJobs.log'),  # Log file path with timestamp.
        filemode='w',  # 'w' mode overwrites the log file each time the application runs.
        format='%(asctime)s::%(name)s::%(levelname)s::%(message)s',  # Log message format.
        datefmt='./logs/%d-%b-%y %H:%M:%S'  # Timestamp format for log entries.
    )
    
    # Set the logging level to DEBUG for the logger (captures all messages, DEBUG and above).
    log.setLevel(logging.DEBUG)

    # Create a console handler to also output logs to the console (stdout).
    c_handler = logging.StreamHandler()
    c_handler.setLevel(logging.DEBUG)  # Set console logging level to DEBUG.

    # Define the log message format for the console output.
    c_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '%H:%M:%S')
    c_handler.setFormatter(c_format)

    # Add the console handler to the logger so that logs go to both the log file and the console.
    log.addHandler(c_handler)

class EasyApplyBot:
    setupLogger()
    # MAX_SEARCH_TIME is 10 hours by default.
    MAX_SEARCH_TIME = 60 * 20 # Modify it to increase search time

    def __init__(self,
                 username,
                 password,
                 phone_number,
                 # profile_path,
                 salary,
                 rate,
                 uploads={},
                 filename='output.csv',
                 blacklist=[],
                 blackListTitles=[],
                 experience_level=[]
                 ) -> None:

        self.uploads = uploads
        self.salary = salary
        self.rate = rate
        past_ids: list | None = self.get_appliedIDs(filename)
        self.appliedJobIDs: list = past_ids if past_ids != None else []
        self.filename: str = filename
        self.options = self.browser_options()
        self.browser = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=self.options)
        self.wait = WebDriverWait(self.browser, 30)
        self.blacklist = blacklist
        self.blackListTitles = blackListTitles
        self.start_linkedin(username, password)
        self.phone_number = phone_number
        self.experience_level = experience_level

        log.info("Welcome to Easy Apply Bot")
        dirpath: str = os.getcwd()
        log.info("current directory is : " + dirpath)
        log.info("Please wait for bot to set-up")
        # Prints only the experience levels specified in the config.yaml file.
        if experience_level:
            experience_levels = {
                1: "Entry level",
                2: "Associate",
                3: "Mid-Senior level",
                4: "Director",
                5: "Executive",
                6: "Internship"
            }
            applied_levels = [experience_levels[level] for level in experience_level]
            log.info("Applying for experience level roles: " + ", ".join(applied_levels))
        # If none are specified, it logs that it is applying for all experience levels
        else:
            log.info("Applying for all experience levels")

        self.locator = {
            "human_verification" : (By.XPATH, "//h1[text()=\"Let’s do a quick security check\"]"),
            "continue_applying": (By.XPATH, ".//button[contains(., 'Continue applying')]"),
            "next": (By.CSS_SELECTOR, "button[aria-label='Continue to next step']"),
            "review": (By.CSS_SELECTOR, "button[aria-label='Review your application']"),
            "submit": (By.CSS_SELECTOR, "button[aria-label='Submit application']"),
            "error": (By.CLASS_NAME, "artdeco-inline-feedback__message"),
            "upload_resume": (By.XPATH, "//*[contains(@id, 'jobs-document-upload-file-input-upload-resume')]"),
            "upload_cv": (By.XPATH, "//*[contains(@id, 'jobs-document-upload-file-input-upload-cover-letter')]"),
            "follow": (By.CSS_SELECTOR, "label[for='follow-company-checkbox']"),
            "upload": (By.NAME, "file"),
            "search": (By.CLASS_NAME, "jobs-search-results-list"),
            "links": (By.XPATH, '//div[@data-job-id]'),  # Corrected this line
            "fields": (By.CLASS_NAME, "jobs-easy-apply-form-section__grouping"),
            "radio_select": (By.XPATH, ".//input[starts-with(normalize-space(@id), 'urn:li:fsd_formElement:urn:li:jobs_applyformcommon_easyApplyFormElement:') and @type='radio' and @value='Yes']"),
            "multi_select": (By.XPATH, ".//select[starts-with(normalize-space(@id), 'text-entity-list-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement-') and @required='']"),
            "text_select": (By.XPATH, ".//input[starts-with(@id, 'single-line-text-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement-') and @type='text']"),
            "input_select": (By.CSS_SELECTOR, 'input[type="radio"], input[type="checkbox"]'),
            "text_area": (By.TAG_NAME, "textarea"),
            "2fa_oneClick": (By.ID, 'reset-password-submit-button'),
            "easy_apply_button": (By.XPATH, '//button[contains(@class, "jobs-apply-button")]'),
            "date_posted_button": (By.XPATH, '//button[contains(@id, "searchFilter_timePostedRange")]'),
            "date_posted_expanded": (By.XPATH, '//button[contains(@id, "searchFilter_timePostedRange")]'),
        }

        # Initialize questions and answers file
        self.qa_file = Path("qa.csv")
        self.answers = {}

        # If qa file does not exist, create it
        if self.qa_file.is_file():
            df = pd.read_csv(self.qa_file)
            for index, row in df.iterrows():
                self.answers[row['Question']] = row['Answer']
        # If qa file does exist, load it
        else:
            df = pd.DataFrame(columns=["Question", "Answer"])
            df.to_csv(self.qa_file, index=False, encoding='utf-8')
    # Method that log 
    def start_linkedin(self, username, password) -> None:
        log.info("Logging in.....Please wait :)")
        self.browser.get("https://www.linkedin.com/login?trk=guest_homepage-basic_nav-header-signin")

        time.sleep(10)

        try:
            user_field = self.browser.find_element("id", "username")
            pw_field = self.browser.find_element("id", "password")
            
            # Wait for the 'username' inut field to be present before interacting with it
            WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@id = 'username']"))
            )

            login_button = self.browser.find_element("xpath", "//button[normalize-space(text())='Sign in']")
            
            user_field.send_keys(username)
            time.sleep(0.5)
            user_field.send_keys(Keys.TAB)
            time.sleep(5)
            pw_field.send_keys(password)
            time.sleep(5)
            
            # Click the login button after ensuring it is clickable
            login_button.click()
            time.sleep(20)

        except TimeoutException:
            log.info("TimeoutException! Username/password field or login button not found")
        except NoSuchElementException as e:
            log.error(f"Element not found: {e}")
 
    # This method that starts application process
    def start_apply(self, positions, locations) -> None:
        start: float = time.time()
        self.fill_data()
        self.positions = positions
        self.locations = locations
        combos: list = []
        while len(combos) < len(positions) * len(locations):
            position = positions[random.randint(0, len(positions) - 1)]
            location = locations[random.randint(0, len(locations) - 1)]
            combo: tuple = (position, location)
            if combo not in combos:
                combos.append(combo)
                log.info(f"Applying to {position}: {location}")
                location = "&location=" + location
                self.applications_loop(position, location)
            if len(combos) > 500:
                break
 

if __name__ == '__main__':
    # all user info needed for the applying. Ex: username, password, 
    with open("config.yaml", 'r') as stream:
        try:
            parameters = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            raise exc
    # Ensure required parameters are present
    assert len(parameters['positions']) > 0, "There are no positions to be searched. Check `config.yaml`"
    assert len(parameters['locations']) > 0, "There are no locations to be searched. Check `config.yaml`"
    assert parameters['username'] is not None, "No username provided. Check `config.yaml`" 
    assert parameters['password'] is not None, "No password provided. Check `config.yaml`"
    assert parameters['phone_number'] is not None, "No phone number provided. Check `config.yaml`"
    # catch configuration errors where uploads is mistakenly formatted as a list instead of a dictionary
    if 'uploads' in parameters.keys() and type(parameters['uploads']) == list:
        raise Exception("uploads read from the config file appear to be in list format" +
                        " while should be dict. Try removing '-' from line containing" +
                        " filename & path")
    # Log all parameters except for password and username
    log.info({k: parameters[k] for k in parameters.keys() if k not in ['username', 'password']})
    # This WILL output applied jobs in a csv. Does nothing right noe
    output_filename: list = [f for f in parameters.get('output_filename', ['output.csv']) if f is not None]
    output_filename: list = output_filename[0] if len(output_filename) > 0 else 'output.csv'
    # banned company and job titles
    blacklist = parameters.get('blacklist', [])
    blackListTitles = parameters.get('blackListTitles', [])
    # Catch any errors in parameters['uploads']
    uploads = {} if parameters.get('uploads', {}) is None else parameters.get('uploads', {})
    for key in uploads.keys():
        assert uploads[key] is not None
    # List comprehension to construct a list of `locations` and `positions` for all items that are not type `None`
    # Type hint shows that a list is expected
    locations: list = [l for l in parameters['locations'] if l is not None]
    positions: list = [p for p in parameters['positions'] if p is not None]

    bot = EasyApplyBot(parameters['username'],
                       parameters['password'],
                       parameters['phone_number'],
                       parameters['salary'],
                       parameters['rate'], 
                       uploads=uploads,
                       filename=output_filename,
                       blacklist=blacklist,
                       blackListTitles=blackListTitles,
                       experience_level=parameters.get('experience_level', [])
                       )
    bot.start_apply(positions, locations)