# Author: Daeshaun Morrison, modified from: https://github.com/nicolomantini/LinkedIn-Easy-Apply-Bot
import csv
import logging
import traceback
import os
import random
import re
import time
from datetime import datetime, timedelta
from datetime import date
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
                #  username,
                #  password,
                #  phone_number,
                 salary,
                 rate,
                 person,
                 profile_path,
                 time_filter,
                 uploads={},
                 filename='output.csv',
                 blacklist=[],
                 blackListTitles=[],
                 experience_level=[]
                 ) -> None:

        self.uploads = uploads
        self.salary = salary
        self.first_name = person['name']['first_name']
        self.last_name = person['name']['last_name']
        self.street = person['address']['street']
        self.city = person['address']['city']
        self.state = person['address']['state']
        self.zipcode = person['address']['zip']
        self.github = person['social_media']['github']
        self.linkedin = person['social_media']['linkedin']
        self.portfolio = person['social_media']['portfolio']
        self.phone_number = person['social_media']['phone_number']
        self.profile_path = profile_path
        self.filename: str = filename
        self.options = self.browser_options()
        self.browser = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=self.options)
        self.wait = WebDriverWait(self.browser, 30)
        self.blacklist = blacklist
        self.blackListTitles = blackListTitles
        self.start_linkedin(person['account']['username'], person['account']['password'])
        self.experience_level = experience_level
        self.time_filter = time_filter
        self.visited_IDs = {}

        # First message
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
            "upload_resume": (By.XPATH, "//input[starts-with(@id, 'jobs-document-upload-file-input-upload-resume') and @type='file']"),
            "upload_cover": (By.XPATH, "//*[contains(@id, 'jobs-document-upload-file-input-upload-cover-letter')]"),
            "follow": (By.CSS_SELECTOR, "label[for='follow-company-checkbox']"),
            "upload": (By.NAME, "file"),
            "search": (By.CLASS_NAME, "jobs-search-results-list"),
            "links": (By.XPATH, '//div[@data-job-id]'),
            "fields": (By.CLASS_NAME, "jobs-easy-apply-form-section__grouping"),
            "radio_select": (By.XPATH, ".//input[starts-with(@id, 'urn:li:fsd_formElement:urn:li:jobs_applyformcommon_easyApplyFormElement:') and @type='radio']"),
            "multi_select": (By.XPATH, ".//select[starts-with(@id, 'text-entity-list-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement-') and @required='']"),
            "text_select": (By.XPATH, ".//input[starts-with(@id, 'single-line-text-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement-') and @type='text']"),
            "input_select": (By.XPATH, ".//input[@type='checkbox' or @type='radio']"),
            "date_input": (By.XPATH, ".//input[@placeholder='mm/dd/yyyy']"),
            "location_select": (By.XPATH, ".//input[@aria-autocomplete='list']"),
            "text_area": (By.TAG_NAME, "textarea"),
            "2fa_oneClick": (By.ID, 'reset-password-submit-button'),
            "easy_apply_button": (By.XPATH, '//button[contains(@class, "jobs-apply-button")]'),
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

        # self.applications_file = Path("applications.csv")
        # self.links = {}

        # if self.applications.is_file():
        #     df = pd.read_csv(self.applications_file)
        #     for index, row in df.iterrows():
        #         self.links[row[title]]

    def browser_options(self):
        """
        Configures Chrome browser options for the web driver, including settings for window size, 
        security, sandboxing, and user profile management.

        Returns:
            options (ChromeOptions): A set of ChromeOptions to be passed to the web driver.

        Workflow:
            - Starts the browser maximized for better visibility.
            - Ignores SSL certificate errors.
            - Disables sandbox for compatibility with certain environments.
            - Turns off extensions and some WebDriver flags to avoid detection by websites.
            - Disables Blink automation features, which can help avoid detection that the browser is controlled by automation.
        """
        options = webdriver.ChromeOptions()

        # Start the browser in maximized mode
        options.add_argument("--start-maximized") 
        
        # Ignore SSL certificate errors
        options.add_argument("--ignore-certificate-errors")
        
        # Disable the Chrome sandbox (useful in certain environments like headless servers)
        options.add_argument('--no-sandbox')
        
        # Disable any browser extensions that may interfere with automation
        options.add_argument("--disable-extensions")

        # Remove certain flags to avoid being easily detectable as WebDriver
        options.add_argument("--disable-blink-features")
        options.add_argument("--disable-blink-features=AutomationControlled")

        # Uncomment if debugging locally via Chrome remote debugging port
        # options.add_argument(r'--remote-debugging-port=9222')
        
        # Uncomment to specify a particular user profile in Chrome
        # options.add_argument(r'--profile-directory=Person 1')

        # Uncomment if you want to load a specific user profile for persistent session data
        # options.add_argument(r"--user-data-dir={}".format(self.profile_path))

        return options

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
        self.browser, _ = self.next_jobs_page(position, location, jobs_per_page, experience_level=self.experience_level, time_filter=self.time_filter)
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
                            if applied_status.is_displayed() or link.get_attribute("data-job-id") in self.visited_IDs:
                                log.debug(f"Job already applied: {link.text}")
                                dismissBtn = link.find_element(By.XPATH, ".//button[starts-with(@aria-label, 'Dismiss')]")
                                dismissBtn.click()
                                continue  # Skip this job card if it's already applied.

                        except NoSuchElementException:
                            # Add the job's ID to the list of `jobIDs`.
                            # If: 1) The job title is NOT blacklisted. 2) If the company of the job is not blacklisted
                            jobIsBanned = False

                            for word in blacklist + blackListTitles:
                                if word.lower() in link.text.lower():
                                    log.debug(f"Job has a banned word: {word}\nDetails: {link.text}")
                                    jobIsBanned = True

                            if jobIsBanned == False:
                                jobID = link.get_attribute("data-job-id")

                                if jobID.isdigit():
                                    # Ensure the job ID is unique before adding it for processing.
                                    if jobID not in jobIDs:
                                        jobIDs[jobID] = "To be processed"

                                else:
                                    log.debug(f"Job ID not found, It is likely a 'promoted' job? {link.text}")
                                    continue
                    
                    # If there are new jobs to process, apply to them.
                    if len(jobIDs) > 0:
                        self.apply_loop(jobIDs)

                    # Load the next page of job listings.
                    self.browser, jobs_per_page = self.next_jobs_page(position, location, jobs_per_page, experience_level=self.experience_level, time_filter=self.time_filter)

                else:
                    # If no jobs found, continue to the next page.
                    self.browser, jobs_per_page = self.next_jobs_page(position, location, jobs_per_page, experience_level=self.experience_level, time_filter=self.time_filter)

            except Exception as e:
                print(e)  # Log any exceptions encountered during the search process.

    def apply_loop(self, jobIDs):
        log.debug("In `apply_loop()`")
        for jobID in jobIDs:
            if jobIDs[jobID] == "To be processed" and jobID not in self.visited_IDs:
                applied = self.apply_to_job(jobID)
                if applied:
                    log.info(f"Applied to {jobID}")
                else:
                    log.info(f"Failed to apply to {jobID}")
                jobIDs[jobID] = applied
                self.visited_IDs[jobID] = True

    def is_present(self, locator):
        """
        Helper function to check if a button locator is present on the page.

        Args:
            button_locator (tuple): Locator to identify elements on the page.

        Returns:
            bool: True if the element is present, False otherwise.
        """
        return len(self.browser.find_elements(locator[0],
                                              locator[1])) > 0

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
            string_easy = "~ Doesn't have Easy Apply Button"
            result = False

        # Log the result of the job application and write to a file for tracking.
        log.info(f"\nPosition {jobID}:\n {self.browser.title} \n {string_easy} \n")
        self.write_to_file(button, jobID, self.browser.title, result)

        return result

    def get_job_page(self, jobID):

        job: str = 'https://www.linkedin.com/jobs/view/' + str(jobID)
        self.browser.get(job)
        self.job_page = self.load_page(sleep=0.5)
        return self.job_page

    def load_page(self, sleep=1):
        scroll_page = 0
        while scroll_page < 4000:
            self.browser.execute_script("window.scrollTo(0," + str(scroll_page) + " );")
            scroll_page += 500
            time.sleep(sleep)

        if sleep != 1:
            self.browser.execute_script("window.scrollTo(0,0);")
            time.sleep(sleep)

        page = BeautifulSoup(self.browser.page_source, "lxml")
        return page


    def get_easy_apply_button(self):
        EasyApplyButton = False
        try:
            buttons = self.get_elements("easy_apply_button")

            for button in buttons:
                if "Easy Apply" in button.text or "Continue applying" in button.text:
                    EasyApplyButton = button
                    self.wait.until(EC.element_to_be_clickable(EasyApplyButton))
                else:
                    log.debug("Easy Apply button not found")
            
        except Exception as e: 
            print("Exception:",e)
            log.debug("Easy Apply button not found")

        return EasyApplyButton

    def fill_out_fields(self):
        try:
            fields = self.browser.find_elements(By.CLASS_NAME, "jobs-easy-apply-form-section__grouping")
            for field in fields:

                if "Mobile phone number" in field.text:
                    field_input = field.find_element(By.TAG_NAME, "input")
                    field_input.clear()
                    field_input.send_keys(self.phone_number)
        except Exception as e:
            log.error(e)

    def send_resume(self) -> bool:
        """
        Attempts to submit a job application by uploading a resume, a cover letter, and following through with 
        the submission process.

        Workflow:
            - Checks for the presence of specific upload locators (resume and cover letter).
            - Uploads the resume and cover letter if locators are found.
            - Interacts with follow, submit, next, and continue applying buttons, if present.
            - Handles errors or additional questions that may appear during the process.
            - Logs success or failure of the submission process.

        Returns:
            bool: True if the resume was successfully submitted, False otherwise.
        """

        try:
            submitted = False
            loop = 0

            # Loop twice to attempt the resume submission.
            while loop < 2:
                time.sleep(2)
                # # Upload the resume if the locator is present.
                # if self.is_present(self.locator["upload_resume"]):
                #     try:
                #         resume = self.uploads["resume"]
                #         # Wait until the resume upload button is clickable
                #         resume_button = WebDriverWait(self.browser, 10).until(
                #             EC.element_to_be_clickable(self.locator["upload_resume"])
                #         )
                #         resume_button.send_keys(resume)
                #     except Exception as e:
                #         log.error(f"Resume upload failed. Check file path or the locator: {e}")
                #         log.error(traceback.format_exc())  # Full traceback for better debugging

                # # Upload the cover letter if the locator is present.
                # if self.is_present(self.locator["upload_cover"]):
                #     try:
                #         cover_letter = self.uploads["cover_letter"]
                #         # Wait until the cover letter upload button is clickable
                #         cover_button = WebDriverWait(self.browser, 10).until(
                #             EC.element_to_be_clickable(self.locator["upload_cover"])
                #         )
                #         cover_button.send_keys(cover_letter)
                #     except Exception as e:
                #         log.error(f"Cover letter upload failed. Check file path or the locator: {e}")
                        
                # Handle follow button if present.
                # Applications commonly have this option already selected,
                # So this UNFOLLOWS companies. Comment this out if you wnat to follow companies
                if len(self.get_elements("follow")) > 0:
                    elements = self.get_elements("follow")
                    for element in elements:
                        button = self.wait.until(EC.element_to_be_clickable(element))
                        button.click()

                # Handle submit button and complete the application.
                if len(self.get_elements("submit")) > 0:
                    
                    elements = self.get_elements("submit")
                    for element in elements:
                        button = self.wait.until(EC.element_to_be_clickable(element))
                        button.click()
                        log.info("Application Submitted")
                        submitted = True
                        break

                # Handle errors during submission.
                elif len(self.get_elements("error")) > 0:
                    if "application was sent" in self.browser.page_source:
                        log.info("Application Submitted")
                        submitted = True
                        break
                    else:
                        start_time = time.time()  # Record the start time
                        while True:
                            log.info("Please answer the questions, waiting 5 seconds...")
                            time.sleep(5)
                            self.process_questions()
                            
                            if "application was sent" in self.browser.page_source:
                                log.info("Application Submitted")
                                submitted = True
                                break
                            
                            elif self.is_present(self.locator["easy_apply_button"]):
                                submitted = False
                                break

                            log.debug(f"{time.time() - start_time} minutes elapsed")
                            
                            # Check if 5 minutes (300 seconds) have passed
                            elapsed_time = time.time() - start_time
                            if elapsed_time > 300:  # 300 seconds = 5 minutes
                                log.info("5 minutes elapsed. Exiting the loop.")
                                return False

                # Handle next, continue, and review buttons if present.
                elif len(self.get_elements("next")) > 0:
                    elements = self.get_elements("next")
                    for element in elements:
                        button = self.wait.until(EC.element_to_be_clickable(element))
                        button.click()

                elif len(self.get_elements("continue_applying")) > 0:
                    elements = self.get_elements("continue_applying")
                    for element in elements:
                        button = self.wait.until(EC.element_to_be_clickable(element))
                        button.click()

                elif len(self.get_elements("review")) > 0:
                    elements = self.get_elements("review")
                    for element in elements:
                        button = self.wait.until(EC.element_to_be_clickable(element))
                        button.click()

        except Exception as e:
            log.error(e)
            log.error("Cannot apply to this job")

        return submitted

    def is_found_field(self, locator, field):
        try:
            return len(field.find_elements(locator[0], locator[1])) > 0
        except Exception as e:
            print(f"Error occurred while finding elements: {e}")
            return False

    def process_questions(self):
        time.sleep(3)

        form = self.get_elements("fields")  # Getting form elements

        print("Length: ", len(form))

        for i in range(len(form)):  
            try:
                # Attempt to re-locate the elements dynamically inside the loop
                form = self.get_elements("fields")
                field = form[i]
                question = field.text.strip()  # Ensure question text is stripped of whitespace
                
                # Get answer for each question individually
                answer = self.ans_question(question.lower())  

            except StaleElementReferenceException:
                log.warning(f"Element became stale: {field}, re-fetching form elements.")
                continue

            # Clear existing selections
            try:
                # Unselect radio buttons
                if self.is_found_field(self.locator["radio_select"], field):
                    # Returns a list of web elements
                    radio_buttons = self.get_child_elements(self.locator["radio_select"], field)

                    for radio_button in radio_buttons: # `radio_button` is a web element
                        self.browser.execute_script("""
                            arguments[0].checked = false;
                            arguments[0].dispatchEvent(new Event('change'));
                        """, radio_button)
                        log.info("Radio button unselected")

                # # Unselect multi-select options
                # elif self.is_found_field(self.locator["multi_select"], field):
                #     # Get the first and only select element
                #     select_element = self.get_child_elements(self.locator["multi_select"], field)[0]  # `select_element` is a web element

                #     # Reset to the default value
                #     self.browser.execute_script("arguments[0].selectedIndex = 0; arguments[0].dispatchEvent(new Event('change'));", select_element)
                #     log.info("Multi-select reset to default value: 'Select an option'")

            except Exception as e:
                log.error(f"Error clearing existing selections: {e}")

        time.sleep(1)

        for i in range(len(form)):
            try:
                # Attempt to re-locate the elements dynamically inside the loop
                form = self.get_elements("fields")
                field = form[i]
                question = field.text.strip()  # Strip whitespace from question
                
                log.info(f"Processing question: {question}")
                answer = self.ans_question(question.lower())  # Get answer based on the current question
                log.info(f"Answer determined: {answer}")

            except StaleElementReferenceException:
                log.warning(f"Element became stale: {field}, re-fetching form elements.")
                continue

            # Scroll the field into view before interacting
            self.browser.execute_script("arguments[0].scrollIntoView(true);", field)

            # Check if input type is radio button
            if self.is_found_field(self.locator["radio_select"], field):
                try:
                    log.debug("Locator: radio_select")
                    radio_buttons = self.get_child_elements(self.locator["radio_select"], field)

                    if radio_buttons is None or len(radio_buttons) == 0:
                        log.error(f"No radio buttons found for question: {question}")
                        continue

                    selected = False

                    for radio_button in radio_buttons:
                        if radio_button.get_attribute('value').lower() == answer.lower():
                            WebDriverWait(field, 10).until(EC.element_to_be_clickable(radio_button))
                            self.browser.execute_script("""
                                arguments[0].click();
                                arguments[0].dispatchEvent(new Event('change'));
                            """, radio_button)
                            log.info(f"Radio button selected: {radio_button.get_attribute('value')}")
                            selected = True

                    if selected == False:
                        log.info("Exact match not found, looking for closest answer...")
                        closest_match = None
                        for radio_button in radio_buttons:
                            radio_value = radio_button.get_attribute('value').lower()
                            if "yes" in radio_value or "no" in radio_value:
                                closest_match = radio_button
                                

                        if closest_match:
                            WebDriverWait(field, 15).until(EC.element_to_be_clickable(closest_match))
                            self.browser.execute_script("""
                                arguments[0].click();
                                arguments[0].dispatchEvent(new Event('change'));
                            """, closest_match)
                            log.info(f"Closest radio button selected: {closest_match.get_attribute('value')}")
                            
                        else:
                            log.warning("No suitable radio button found to select. Picking random option")
                            ran_option = random.choice(radio_buttons)
                            WebDriverWait(field, 10).until(EC.element_to_be_clickable(ran_option))
                            self.browser.execute_script("""
                                arguments[0].click();
                                arguments[0].dispatchEvent(new Event('change'));
                            """, ran_option)
                            
                except StaleElementReferenceException:
                    log.warning(f"Retrying due to stale element in radio button. ")

                except Exception as e:
                    log.error(f"Radio button error for question: {question}, answer: {answer}")
                    log.error(traceback.format_exc())  # Full traceback for better debugging
                
            # Multi-select case
            elif self.is_found_field(self.locator["multi_select"], field):
                max_retries = 5
                retry_count = 0
                while retry_count < max_retries:
                    try:
                        log.debug("Locator: multi_select")
                        # Refresh or re-fetch the select element each time
                        select_element = WebDriverWait(field, 10).until(
                            EC.presence_of_element_located(self.locator["multi_select"])
                        )

                        foundChoice = False

                        # Get all options again to avoid stale references
                        options = select_element.find_elements(By.TAG_NAME, "option")
                        for option in options:
                            if answer.lower() in option.text.strip().lower():
                                option.click()
                                foundChoice = True
                                log.info(f"Option selected: {option.text}")
                                break

                        if not foundChoice:
                            options[1].click()  # Select the 1st option as a fallback
                            log.info(f"1st Option selected: {options[1].text}")

                        break  # Successfully selected an option, exit loop

                    except StaleElementReferenceException:
                        retry_count += 1
                        log.warning(f"Retrying due to stale element in multi-select. Attempt {retry_count}/{max_retries}")
                        
                        if retry_count >= max_retries:
                            log.error("Exceeded max retries due to stale element issue")
                            break  # Exit loop after max retries

                    except Exception as e:
                        log.error(f"Multi-select error: {e}")
                        break  # Exit loop on any other exception

            # Handle text input fields
            elif self.is_found_field(self.locator["text_select"], field):
                try:    
                    log.debug("Locator: text_select")
                    text_field = WebDriverWait(field, 10).until(
                            EC.presence_of_element_located(self.locator["text_select"])
                        )
                    
                    text_field.clear()
                    time.sleep(0.5)
                    text_field.send_keys(answer)
                    log.info(f"Text input field populated with: {answer}")
                except Exception as e:
                    log.error(f"(process_questions(1)) Text field error: {e}") 

            # Handle auto complete fields
            elif self.is_found_field(self.locator["location_select"], field):
                try:
                    log.debug("Locator: location_select")
                    text_field = WebDriverWait(field, 10).until(
                            EC.presence_of_element_located(self.locator["location_select"])
                        )
                    text_field.clear()
                    text_field.send_keys(answer)
                    time.sleep(5)
                    text_field.send_keys(Keys.ARROW_DOWN)
                    text_field.send_keys(Keys.ENTER)
                    log.info(f"Auto complete input field populated with: {answer}")
                except Exception as e:
                    log.error(f"Text field error: {e}") 

            # Handle textarea fields
            elif self.is_found_field(self.locator["text_area"], field):
                try:
                    log.debug("Locator: text_area")
                    text_area = WebDriverWait(field, 10).until(
                            EC.presence_of_element_located(self.locator["text_area"])
                        )
                    time.sleep(3)
                    text_area.clear()
                    time.sleep(0.5)
                    text_area.send_keys(answer)
                    log.info(f"Text input field populated with: {answer}")
                except Exception as e:
                    log.error(f"(process_questions(1)) Text field error: {e}")

            # Handle fieldset fields
            elif self.is_found_field(self.locator["input_select"], field):  # Adjust options as needed
                try:
                    log.debug("Locator: input_select")
                    select_elements = self.get_child_elements(self.locator["input_select"], field)
                    log.debug(select_elements)

                    if select_elements is None or len(select_elements) == 0:
                        log.error(f"No select elements found for question: {question}")
                        continue

                    selected = False

                    for select_element in select_elements:
                        # Check for attributes starting with 'data-test-text-selectable-option'
                        attr_value = select_element.get_attribute('data-test-text-selectable-option__input')
                        select_element = field.find_element(By.XPATH, f".//input[@data-test-text-selectable-option__input=\"{attr_value}\"]")

                        
                        # Check if the attribute value matches the answer
                        if answer.lower() == attr_value.lower():
                            # Wait until the select_element is clickable and then click
                            WebDriverWait(field, 20).until(EC.element_to_be_clickable(select_element))
                            select_element.click()  # Click instead of just setting the 'selected' attribute
                            log.info(f"Select element chosen: {select_element.get_attribute('value')}")
                            selected = True
                            break  # Exit loop once the option is selected

                    if selected == False:
                        log.info("Exact match not found, looking for closest answer...")
                        closest_match = None
                        for select_element in select_elements:
                            try: 
                                # Get the value of the specific attribute
                                attr_value = select_element.get_attribute('data-test-text-selectable-option__input')
                                
                                # Check if the attribute value is present and if the answer is in it
                                if answer.lower() in attr_value.lower():  # Check if answer is in the attribute value
                                    closest_match = field.find_element(By.XPATH, f".//input[@data-test-text-selectable-option__input=\"{attr_value}\"]")

                                    break  # Exit loop on first closest match
                            except Exception as e:
                                log.error(e)
                                log.error(traceback.format_exc())  # Full traceback for better debugging
                                

                        if closest_match:
                            WebDriverWait(field, 20).until(EC.visibility_of_element_located(closest_match))
                            try:
                                closest_match.click()  # Use click for better simulation
                                log.info(f"Closest select element chosen: {closest_match.get_attribute('value')}")
                            except Exception as e:
                                log.warning(f"Regular click failed for closes match option. Using JavaScript click. Error: {e}")
                                # Fallback to JavaScript click
                                self.browser.execute_script("arguments[0].click();", closest_match)
                                log.info(f"Random option selected via JS: {closest_match.get_attribute('value')}")


                        else:
                            log.warning("No suitable select option found. Picking the random option")
                            # Pick random choice
                            random_option = random.choice(select_elements)
                            try:
                                random_option.click()
                                log.info(f"Random option selected: {random_option.get_attribute('value')}")
                            except Exception as e:
                                log.warning(f"Regular click failed for random option. Using JavaScript click. Error: {e}")
                                # Fallback to JavaScript click
                                self.browser.execute_script("arguments[0].click();", random_option)
                                log.info(f"Random option selected via JS: {random_option.get_attribute('value')}")
                                
                except StaleElementReferenceException:
                    log.warning(f"Retrying due to stale element in fieldset.")

                except Exception as e:
                    log.error(f"Select element error for question: {question}, answer: {answer}")
                    log.error(traceback.format_exc())  # Full traceback for better debugging

            # Handle date input fields
            elif self.is_found_field(self.locator["date_input"], field):
                try:
                    log.debug("Locator: date_input")

                    # Locate the date field using the correct locator strategy
                    date_field = WebDriverWait(field, 15).until(
                        EC.presence_of_element_located(self.locator["date_input"])
                    )
                    
                    # Clear the date field
                    # date_field.clear()

                    # Send the answer (date) to the input
                    date_field.send_keys(answer)  # Ensure 'answer' is formatted correctly as "mm/dd/yyyy"
                    time.sleep(1)
                    date_field.click()
                    time.sleep(3)
                    button = WebDriverWait(field, 15).until(
                        EC.element_to_be_clickable((By.XPATH, ".//button[contains(@aria-label, 'This is today')]"))
                    )
                    button.click()

                    log.info(f"Date input filled with value: {answer}")
                    
                except Exception as e:
                    log.error(f"Error while filling the date input: {e}")
                    log.error(traceback.format_exc())  # Full traceback for better debugging

            else:
                log.info(f"Unable to determine field type for question: {question}, moving to next field.")

    def get_child_elements(self, locator, field):
        try:
            return field.find_elements(locator[0], locator[1])
        except Exception as e:
            print(f"Error occurred while finding elements: {e}")
            return []  # Return an empty list instead of False

    def next_jobs_page(self, position, location, jobs_per_page, experience_level=[], time_filter=""):
        """
        Loads the next page of job listings on LinkedIn, applying filters such as position, location, 
        experience level, and time since the job was posted.

        Args:
            position (str): The job title or keyword to search for.
            location (str): The location of the jobs being searched.
            jobs_per_page (int): The starting index for jobs to be loaded (pagination).
            experience_level (list): A list of integers representing experience levels to filter jobs by. 
                                     Defaults to an empty list (no experience level filter).
            time_filter (str): A string representing the time period within which jobs were posted. 
                               Can be "24 hours", "past week", or "past month". Defaults to "24 hours".

        Returns:
            tuple: 
                - browser (WebDriver): The browser instance that loaded the next jobs page.
                - jobs_per_page (int): The updated jobs_per_page index for tracking pagination.
        
        Workflow:
            - Constructs the URL based on the position, location, experience level, and time filter.
            - Filters jobs based on the posting time (last 24 hours, past week, past month, or any time).
            - Loads the job page into the browser and returns the updated browser instance.
        """
        # Construct the experience level part of the URL
        experience_level_str = ",".join(map(str, experience_level)) if experience_level else ""
        experience_level_param = f"&f_E={experience_level_str}" if experience_level_str else ""

        # Construct the time filter part of the URL
        if time_filter == 1:
            time_posted_param = "&f_TPR=r86400"  # Last 24 hours
        elif time_filter == 2:
            time_posted_param = "&f_TPR=r604800"  # Last week
        elif time_filter == 3:
            time_posted_param = "&f_TPR=r2592000"  # Last month
        else:
            time_posted_param = ""  # No filter (Any time)

        self.browser.get(
            # URL for jobs page with Easy Apply, position, location, and time filter
            "https://www.linkedin.com/jobs/search/?f_LF=f_AL&keywords=" +
            position + location + "&start=" + str(jobs_per_page) + experience_level_param + time_posted_param
        )

        log.info(f"Loading next job page with time filter: {time_filter}")
        self.load_page()
        return (self.browser, jobs_per_page)

    def get_elements(self, type) -> list:
        elements = []
        element = self.locator[type]
        if self.is_present(element):
            elements = self.browser.find_elements(element[0], element[1])
        return elements

    def write_to_file(self, button, jobID, browserTitle, result) -> None:
        def re_extract(text, pattern):
            target = re.search(pattern, text)
            if target:
                target = target.group(1)
            return target

        timestamp: str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        attempted: bool = False if button == False else True
        job = re_extract(browserTitle.split(' | ')[0], r"\(?\d?\)?\s?(\w.*)")
        company = re_extract(browserTitle.split(' | ')[1], r"(\w.*)")

        toWrite: list = [timestamp, jobID, job, company, attempted, result]
        with open(self.filename, 'a+') as f:
            writer = csv.writer(f)
            writer.writerow(toWrite)

    def ans_question(self, question):  # refactor this to an ans.yaml file
        answer = None
        question = question.lower().strip()
        choices = ["6", "5", "4", "3"]

        # English proficiency-related questions
        if "english" in question:
            if "speak" in question or "communicate" in question:
                answer = "Yes"
            elif "proficiency" in question or "level" in question:
                answer = "Native"

        # Experience-related questions
        elif "how many" in question or "how much" in question or "enter a decimal number" in question:
            answer = random.choice(choices)
        elif "rate" in question and ("yourself" in question or "proficient" in question or "proficiency" in question):
            answer = "10"
        elif "hourly" in question and ("rate" in question or "salary" in question or "what" in question):
            answer = self.rate
        elif "do you" in question and "experience" in question:
            answer = "Yes"
        elif "how did you hear" in question:
            answer = "Other"
        elif "refer" in question or "referred" in question:
            answer = "N/A"
        elif "why" in question and ("position" in question or "role" in questions):
            answer = "Good glassdoor reviews and the workers I talked to love their jobs"

        # Work authorization questions
        elif "sponsor" in question or "sponsorship" in question:
            answer = "No"
        elif "work" in question and ("authorization" in question or "authorized" in question):
            if "usc" in question:
                answer = "USC: 0"
            elif "status" in question:
                answer = "U.S Citizen"
        elif "W2" in question:
            answer = "Yes"
        elif ("eligible" in question or "able" in question) and "clearance" in question:
            answer = "Yes"
        elif ("have" in question or "obtain" in question or "obtained" in question) and "clearance" in question:
            answer = "Yes"
        elif ("US" in question or "U.S." in question or "green" in question ) and ("citizen" in question or "card" in question):
            answer = "Yes"
        elif ("privacy policy" in question):
            answer = "I agree"
        elif "date" in question and ("earliest" in question or "start" in question or "mm/dd/yyyy" in question or "format" in question):
            today = date.today()
            answer = today.strftime("%m/%d/%Y")
        # basic info
        elif ("city" in question or "address" in question):
            answer = self.city
        elif ("zip" in question or "area code" in question or "postal" in question):
            answer = self.zipcode
        elif ("first" in question):
            answer = self.first_name
        elif ("last" in question):
            answer = self.last_name
        elif ("your name" in question):
            answer = self.first_name + " " + self.last_name
        # Socials
        elif ("github" in question):
            answer = self.github
        elif ("linkedin" in question):
            answer = self.linkedin
        elif "portfolio" in question or "personal website" in question:
            answer = self.portfolio

        # Disability and drug test-related questions
        elif "disability" in question:
            answer = "No"
        elif "drug test" in question:
            if "positive" in question:
                answer = "No"
            elif "can you" in question:
                answer = "Yes"

        # Commuting and legal questions
        elif "can you" in question and "commute" in question:
            answer = "Yes"
        elif "criminal" in question or "felon" in question or "charged" in question:
            answer = "No"

        # Other personal questions
        elif "currently reside" in question:
            answer = "Yes"
        elif ("us citizen" in question or "u.s. citizen" in question) and "clearance" in question:
            answer = "Yes"
        elif "salary" in question:
            answer = self.salary
        elif "hourly" in question:
            answer = "40"
        elif "gender" in question:
            answer = "Male"
        elif "race" in question:
            answer = "White"
        elif "lgbtq" in question:
            answer = "No"
        elif "ethnicity" in question or "nationality" in question:
            answer = "White"
        elif "government" in question or "veteran" in question:
            answer = "I am not"
        elif "are you legally" in question:
            answer = "Yes"
        elif "phone" in question and ("mobile" in question or "number" in question):
            answer = self.phone_number



        # General affirmative questions
        elif "do you" in question or "did you" in question or "have you" in question or "are you" in question:
            answer = "Yes"

        # Default case for unanswered questions
        if answer is None:
            log.info("Not able to answer question automatically. Please provide answer")
            answer = "2"  # Placeholder for unanswered questions
            time.sleep(5)

        log.info("Answering question: " + question + " with answer: " + str(answer))

        # Append question and answer to the CSV
        if question not in self.answers:
            self.answers[question] = answer
            new_data = pd.DataFrame({"Question": [question], "Answer": [answer]})
            new_data.to_csv(self.qa_file, mode='a', header=False, index=False, encoding='utf-8')

        return str(answer)

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
    assert parameters['person']['account']['username'] is not None, "No username provided. Check `config.yaml`" 
    assert parameters['person']['account']['password'] is not None, "No password provided. Check `config.yaml`"
    assert parameters['person']['social_media']['phone_number'] is not None, "No phone number provided. Check `config.yaml`"
    # catch configuration errors where uploads is mistakenly formatted as a list instead of a dictionary
    if 'uploads' in parameters.keys() and type(parameters['uploads']) == list:
        raise Exception("uploads read from the config file appear to be in list format" +
                        " while should be dict. Try removing '-' from line containing" +
                        " filename & path")
    # Log all parameters except for password and username
    log.info({k: parameters[k] for k in parameters.keys()})
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

    bot = EasyApplyBot(parameters['salary'],
                       parameters['rate'], 
                       parameters['person'],
                       parameters['profile_path'],
                       parameters['time_filter'],
                       uploads=uploads,
                       filename=output_filename,
                       blacklist=blacklist,
                       blackListTitles=blackListTitles,
                       experience_level=parameters.get('experience_level', [])
                       )
    bot.start_apply(positions, locations)