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
    # Method that logs into your account 
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
            time.sleep(1)
            pw_field.send_keys(password)
            time.sleep(1)
            
            # Click the login button after ensuring it is clickable
            login_button.click()
            # Timer for 20 seconds, in cases where 2FA and/or CAPTCHA needs to be approved
            time.sleep(20)

        except TimeoutException:
            log.info("TimeoutException! Username/password field or login button not found")
        except NoSuchElementException as e:
            log.error(f"Element not found: {e}")
 
    # This method that starts application process
    def start_apply(self, positions, locations) -> None:
        """
        Initiates the job application process by applying to a combination of positions and locations.
        
        Args:
            positions (list): A list of job positions to apply for.
            locations (list): A list of locations to apply for.
        
        Workflow:
            - Starts by recording the start time.
            - Fills in initial data for the application.
            - Iterates through randomly selected combinations of positions and locations.
            - Ensures each position-location combination is unique.
            - Logs each application attempt.
            - Calls the `applications_loop()` method to apply for each position at the specified location.
            - Stops after either applying to all combinations or after 500 attempts, whichever comes first.
        
        Returns:
            None
        """
        start: float = time.time()  # Record the start time for the application process.
        self.fill_window()  # Minimize the browser window to the background.
        self.positions = positions  # Set the positions to apply for.
        self.locations = locations  # Set the locations to apply for.
        
        combos: list = []  # List to store unique combinations of position and location.
        
        # Continue until all unique combinations of positions and locations are tried.
        while len(combos) < len(positions) * len(locations):
            # Randomly select a position and location from the provided lists.
            position = positions[random.randint(0, len(positions) - 1)]
            location = locations[random.randint(0, len(locations) - 1)]
            combo: tuple = (position, location)  # Create a position-location tuple.

            # Ensure the combination has not already been tried.
            if combo not in combos:
                combos.append(combo)  # Add the new combo to the list of applied combos.
                log.info(f"Applying to {position}: {location}")  # Log the application attempt.

                # Modify location for the application loop.
                location = "&location=" + location
                self.applications_loop(position, location)  # Apply for the selected position and location.

            # Break the loop if more than 500 applications are attempted to avoid excessive loops.
            if len(combos) > 500:
                break

    # Minimize the browser window to the background.
    def fill_window(self) -> None:
        self.browser.set_window_size(1, 1)
        self.browser.set_window_position(2000, 2000)

    def applications_loop(self, position, location):
        """
        Main loop to search and apply for jobs based on the specified position and location.

        Args:
            position (str): The job position to search for (e.g., "Software Engineer").
            location (str): The location to search in (e.g., "New York").

        Workflow:
            - Initializes the job search by setting the window and loading the first page of results.
            - Logs the time remaining for the search based on `MAX_SEARCH_TIME`.
            - Scrolls through the job listings, looks for job cards, and checks their status (whether applied or not).
            - Skips jobs that have already been applied to and stores new job IDs for processing.
            - If new jobs are found, passes them to the `apply_loop()` method for further action.
            - Continues to the next page of jobs after processing the current page.
            - Repeats the process until the search time runs out or no more jobs are found.

        Returns:
            None
        """
        jobs_per_page = 0  # Initialize the number of jobs found per page.
        start_time: float = time.time()  # Record the start time of the job search.

        log.info("Looking for jobs...Please wait...")  # Log that the search has started.

        # Set window position and maximize it for job searching.
        self.browser.set_window_position(1, 1)
        self.browser.maximize_window()
        
        # Load the first page of jobs based on position and location.
        self.browser, _ = self.next_jobs_page(position, location, jobs_per_page, experience_level=self.experience_level)
        log.info("Set and maximize window")

        # Continue searching for jobs until the maximum search time is reached.
        while time.time() - start_time < self.MAX_SEARCH_TIME:
            try:
                # Log the remaining time left for the search.
                log.info(f"{(self.MAX_SEARCH_TIME - (time.time() - start_time)) // 60} minutes left in this search")

                # Sleep for a random time between 1.5 to 2.9 seconds to mimic human behavior.
                randoTime: float = random.uniform(1.5, 2.9)
                log.debug(f"Sleeping for {round(randoTime, 1)}")
                self.load_page(sleep=0.5)

                # Check if the search results are present.
                if self.is_present(self.locator["search"]):
                    
                    scrollresults = self.get_elements("search")

                    # Scroll through job listings to load more results.
                    for i in range(300, 5000, 100):
                        self.browser.execute_script("arguments[0].scrollTo(0, {})".format(i), scrollresults[0])
                        time.sleep(0.5)  # Wait for new elements to load.

                # Check if job links are present on the page.
                if self.is_present(self.locator["links"]):
                    links = self.get_elements("links")
                    
                    jobIDs = {}  # Dictionary to store job IDs for processing.

                    for link in links:
                        try:
                            # Check if the job has already been applied to.
                            applied_status = link.find_element(By.XPATH, 
                                ".//div/ul/li[contains(@class, 'job-card-container__footer-job-state') and normalize-space(.)='Applied']"
                            )

                            # If the job has been applied, dismiss it and skip to the next.
                            if applied_status.is_displayed():
                                log.debug(f"Job already applied: {link.text}")
                                dismissBtn = link.find_element(By.XPATH, ".//button[starts-with(@aria-label, 'Dismiss')]")
                                dismissBtn.click()
                                continue  # Skip this job card if it's already applied.

                        except NoSuchElementException:
                            # If the job has not been applied and is not in the blacklist.
                            if link.text not in self.blacklist:
                                jobID = link.get_attribute("data-job-id")
                                if jobID == "search":
                                    log.debug(f"Job ID not found, search keyword found instead? {link.text}")
                                    continue
                                else:
                                    # Ensure the job ID is unique before adding it for processing.
                                    if jobID not in jobIDs:
                                        jobIDs[jobID] = "To be processed"
                    
                    # If there are new jobs to process, apply to them.
                    if len(jobIDs) > 0:
                        self.apply_loop(jobIDs)

                    # Load the next page of job listings.
                    self.browser, jobs_per_page = self.next_jobs_page(position, location, jobs_per_page, experience_level=self.experience_level)

                else:
                    # If no jobs found, continue to the next page.
                    self.browser, jobs_per_page = self.next_jobs_page(position, location, jobs_per_page, experience_level=self.experience_level)

            except Exception as e:
                print(e)  # Log any exceptions encountered during the search process.

    def apply_loop(self, jobIDs):
        log.debug("In `apply_loop()`")
        for jobID in jobIDs:
            if jobIDs[jobID] == "To be processed":
                applied = self.apply_to_job(jobID)
                if applied:
                    log.info(f"Applied to {jobID}")
                else:
                    log.info(f"Failed to apply to {jobID}")
                jobIDs[jobID] = applied

    def apply_to_job(self, jobID):
        """
        Applies to a job using the provided job ID by interacting with the job page and handling the Easy Apply process.

        Args:
            jobID (str): The unique identifier for the job being applied to.

        Workflow:
            - Navigates to the job page using the provided job ID.
            - Checks if the job page contains an Easy Apply button.
            - Skips applying if any blacklisted keywords are found in the job title.
            - If the Easy Apply button is present, it clicks the button and proceeds with filling out the application form.
            - Sends the resume and logs the result of the application (success or failure).
            - Handles cases where the job has already been applied to or doesn't have the Easy Apply button.
            - Logs the outcome of the job application and writes the result to a file for future reference.

        Returns:
            result (bool): True if the application was successfully submitted, False otherwise.
        """
        # Navigate to the job page using the job ID.
        self.get_job_page(jobID)

        # Let the page fully load before interacting with it.
        time.sleep(1)

        # Try to find the Easy Apply button on the job page.
        button = self.get_easy_apply_button()
    
        # Skip job if the title contains blacklisted keywords.
        if button is not False:
            if any(word in self.browser.title for word in blackListTitles):
                log.info('Skipping this application, a blacklisted keyword was found in the job position')
                string_easy = "~ Contains blacklisted keyword"
                result = False
            else:
                # Easy Apply button is available, so click it to proceed.
                string_easy = "~ Has Easy Apply Button. Clicking now!"
                button.click()

                clicked = True
                time.sleep(1)

                # Fill out the necessary fields on the Easy Apply form.
                self.fill_out_fields()
                
                # Send the resume and determine if the application was successful.
                result: bool = self.send_resume()
                if result:
                    string_easy = "~ Sent Resume!"
                else:
                    string_easy = "~ Did not apply: Failed to send Resume"

        # Handle case where the job has already been applied to.
        elif "You applied on" in self.browser.page_source:
            string_easy = "~ Already Applied"
            result = False
        # Handle case where no Easy Apply button exists.
        else:
            string_easy = "* Doesn't have Easy Apply Button"
            result = False

        # Log the result of the job application and write to a file for tracking.
        log.info(f"\nPosition {jobID}:\n {self.browser.title} \n {string_easy} \n")
        self.write_to_file(button, jobID, self.browser.title, result)

        return result

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