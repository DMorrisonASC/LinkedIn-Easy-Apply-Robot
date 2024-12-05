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
    Configures the logging setup for the application. This method ensures that logging is captured
    both in log files and in the console for real-time feedback. The configuration includes:
    
    - **Log Files**:
        - A timestamped log file is created in the `logs` directory for every run.
        - If the `logs` directory does not exist, it will be created automatically.
        - Logs include detailed information such as timestamps, log levels, and messages.
    
    - **Console Output**:
        - Logs are also output to the console (stdout) for immediate visibility.
        - Console logs include timestamps, log levels, and messages.

    **Implementation Details**:
    - The timestamp format for the log filename is `%m_%d_%y %H_%M_%S`.
    - The log file is named `applyJobs.log` with the timestamp prepended.
    - Logging levels are set to `DEBUG` to capture all levels of log messages.
    - Formatting is applied separately for log files and console outputs to ensure clarity.
    
    Raises:
        - This function does not raise any exceptions directly but ensures that any file or I/O errors during
          directory creation or file writing are logged appropriately.
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
    # Modify it to increase search time
    # 60 * 1 = 1 minute 
    MAX_SEARCH_TIME = 60 * 10 

    def __init__(self,
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
        """
        Initializes the Easy Apply Bot with configurations and settings for automating LinkedIn job applications.

        **Parameters**:
        - `salary` (int/float): The expected salary to filter job postings.
        - `rate` (int/float): The hourly or annual rate expectation for jobs.
        - `person` (dict): User's personal information, including:
            - `name`: Dictionary with `first_name` and `last_name`.
            - `address`: Dictionary containing `street`, `city`, `state`, and `zip`.
            - `social_media`: Dictionary with `github`, `linkedin`, `portfolio`, and `phone_number`.
            - `demographic`: Dictionary with `race`, `gender`, `disability`, `veteran`, and `lgbtq`.
            - `account`: Dictionary containing `username` and `password` for LinkedIn login.
        - `profile_path` (str): Path to the LinkedIn profile or additional user configuration files.
        - `time_filter` (int): The time frame for filtering job postings (e.g., past 24 hours).
        - `uploads` (dict, optional): Files to be uploaded during the application process, such as resumes or cover letters. Defaults to an empty dictionary.
        - `filename` (str, optional): Name of the output CSV file for storing application details. Defaults to `'output.csv'`.
        - `blacklist` (list, optional): List of company names to exclude from applications. Defaults to an empty list.
        - `blackListTitles` (list, optional): List of job titles to exclude from applications. Defaults to an empty list.
        - `experience_level` (list, optional): List of experience levels to apply for, represented as integers:
            - `1`: Entry level
            - `2`: Associate
            - `3`: Mid-Senior level
            - `4`: Director
            - `5`: Executive
            - `6`: Internship
        Defaults to applying for all experience levels.

        **Attributes**:
        - Sets up browser automation using Selenium.
        - Configures logging for the bot's actions and setup process.
        - Initializes CSV files for tracking questions, answers, and applications.
        - Prepares locators for LinkedIn elements required for job applications.
        - Starts the LinkedIn login process with credentials from the `person` parameter.

        **Workflow**:
        1. Logs the bot's initialization process.
        2. Checks and prepares the required files (`qa.csv` and `applications.csv`).
        3. Configures experience level filtering.
        4. Sets up locators for LinkedIn elements, ensuring automation accuracy.
        5. Logs into LinkedIn using the provided credentials.

        **Notes**:
        - The bot logs the current directory, setup progress, and applicable experience levels.
        - If the question-and-answer file (`qa.csv`) exists, it loads it into memory for use in applications.
        - Creates empty CSV files if they do not exist, ensuring the bot can run without interruptions.
        """

        self.uploads = uploads
        self.salary = salary
        self.rate = rate
        self.first_name = person['name']['first_name']
        self.last_name = person['name']['last_name']
        self.street = person['address']['street']
        self.city = person['address']['city']
        self.state = person['address']['state']
        self.zipcode = person['address']['zip']
        self.country = person['address']['country']
        self.github = person['social_media']['github']
        self.linkedin = person['social_media']['linkedin']
        self.portfolio = person['social_media']['portfolio']
        self.phone_number = person['social_media']['phone_number']
        self.race = person['demographic']['race']
        self.gender = person['demographic']['gender']
        self.disability = person['demographic']['disability']
        self.veteran = person['demographic']['veteran']
        self.lgbtq = person['demographic']['lgbtq']
        self.profile_path = profile_path
        # Ensure the directory exists
        self.filename: str = filename
        directory = os.path.dirname(self.filename)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        #
        self.options = self.browser_options()
        self.browser = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=self.options)
        self.wait = WebDriverWait(self.browser, 30)
        self.blacklist = blacklist
        self.blackListTitles = blackListTitles
        self.experience_level = experience_level
        self.time_filter = time_filter
        self.visited_IDs = {}
        self.zoom_level = 90

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
            # Login elements
            "username_field" : (By.ID, "username"),
            "password_field" : (By.ID, "password"),
            "login_button" : (By.XPATH, "//button[normalize-space(text())='Sign in']"),
            "human_verification" : (By.XPATH, "//h1[text()=\"Let’s do a quick security check\"]"),
            # 
            "applied_status": (By.XPATH, ".//div/ul/li[contains(@class, 'job-card-container__footer-job-state') and normalize-space(.)='Applied']"),
            "dismiss_button": (By.XPATH, ".//button[starts-with(@aria-label, 'Dismiss')]"),
            "continue_applying": (By.XPATH, ".//button[contains(., 'Continue applying')]"),
            "job_title": (By.XPATH, "//div[contains(@class, 'job-details-jobs-unified-top-card__job-title')]/h1"),
            "company_name": (By.XPATH, "//div[contains(@class, 'job-details-jobs-unified-top-card__company-name')]/a"),
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
            "fields": (By.XPATH, "//div[starts-with(@class, 'fb-dash-form-element')]"),
            "radio_select": (By.XPATH, ".//input[starts-with(@id, 'urn:li:fsd_formElement:urn:li:jobs_applyformcommon_easyApplyFormElement:') and @type='radio']"),
            "multi_select": (By.XPATH, ".//select[starts-with(@id, 'text-entity-list-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement-') and @required='']"),
            "text_select": (By.XPATH, ".//input[starts-with(@id, 'single-line-text-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement-') and @type='text']"),
            "input_select": (By.XPATH, ".//input[@type='checkbox' or @type='radio']"),
            "date_input": (By.XPATH, ".//input[@placeholder='mm/dd/yyyy']"),
            "location_select": (By.XPATH, ".//input[@aria-autocomplete='list']"),
            "text_area": (By.TAG_NAME, "textarea"),
            "2fa_oneClick": (By.ID, 'reset-password-submit-button'),
            "easy_apply_button": (By.XPATH, '//button[contains(@aria-label, "Easy Apply") and .//span[text()="Easy Apply"]]')

        }

        # After locators are compeleted, login into LinkedIn
        self.start_linkedin(person['account']['username'], person['account']['password'])
        # Initialize questions and answers file
        self.qa_file = Path("qa.csv")
        self.answers = {}

        # Check if the qa file exists and is not empty
        if self.qa_file.is_file() and self.qa_file.stat().st_size > 0:
            # Load the existing file into a dictionary
            try:
                df = pd.read_csv(self.qa_file)
                self.answers = dict(zip(df['Question'], df['Answer']))
            except Exception as e:
                print(f"Error reading file: {e}")
                self.create_empty_csv()
        else:
            # Create a new file with headers "Question" and "Answer"
            self.create_empty_csv()

        # Initialize the applications file
        self.applications_file = Path("applications.csv")

        # If applications.csv does not exist, create it with headers
        if not self.applications_file.is_file():
            data = {
                'company': ['some text'],
                'link': ['some link'],
            }
            df = pd.DataFrame(data)
            # Write only the header to a CSV file (this will create an empty file with headers)
            df.head(0).to_csv('applications.csv', index=False)

    def create_empty_csv(self):
        """Creates an empty CSV file with the correct headers."""
        df = pd.DataFrame(columns=["Question", "Answer"])
        df.to_csv(self.qa_file, index=False, encoding='utf-8')
        print("Created a new qa.csv file with headers.")

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
        options.add_argument("--force-device-scale-factor=0.8")

        # Uncomment if debugging locally via Chrome remote debugging port
        # options.add_argument(r'--remote-debugging-port=9222')
        
        # Uncomment to specify a particular user profile in Chrome
        # options.add_argument(r'--profile-directory=Person 1')

        # Uncomment if you want to load a specific user profile for persistent session data
        # options.add_argument(r"--user-data-dir={}".format(self.profile_path))

        return options

    def start_linkedin(self, username, password) -> None:
        """
        Logs into the user's LinkedIn account using the provided credentials.

        **Parameters**:
        - `username` (str): The LinkedIn account username (email).
        - `password` (str): The LinkedIn account password.

        **Workflow**:
        1. Navigates to the LinkedIn login page.
        2. Waits for the username input field to be present on the page.
        3. Inputs the username and password into their respective fields.
        4. Simulates user interaction with small delays to prevent detection by LinkedIn's anti-bot mechanisms.
        5. Clicks the login button using JavaScript execution for reliability.
        6. Pauses execution for 20 seconds to handle potential Two-Factor Authentication (2FA) or CAPTCHA prompts.

        **Locators Used**:
        - `username_field`: Locator for the username input field.
        - `password_field`: Locator for the password input field.
        - `login_button`: Locator for the login button.

        **Error Handling**:
        - **TimeoutException**: Raised when the username/password field or login button does not load within the specified time.
        - Logs a message indicating the timeout.
        - **NoSuchElementException**: Raised when one of the required elements is not found on the page.
        - Logs an error with the missing element details.

        **Additional Notes**:
        - The method utilizes Selenium's `WebDriverWait` to ensure elements are present before interacting with them, reducing the risk of runtime errors.
        - `time.sleep` is used sparingly to mimic user behavior and handle potential UI delays.
        - JavaScript execution (`clickjs`) is used for the login button to avoid interaction issues.

        **Example**:
        ```python
        bot.start_linkedin("user@example.com", "securepassword123")
        ```
        """

        log.info("Logging in.....Please wait :)")
        self.browser.get("https://www.linkedin.com/login?trk=guest_homepage-basic_nav-header-signin")

        time.sleep(5)

        try:
            user_field = self.get_child(self.locator["username_field"])
            pw_field = self.get_child(self.locator["password_field"])
            
            # Wait for the 'username' input field to be present before interacting with it
            WebDriverWait(self.browser, 20).until(
                EC.presence_of_element_located((By.XPATH, "//input[@id = 'username']"))
            )

            login_button = self.get_child(self.locator["login_button"])
            
            user_field.send_keys(username)
            time.sleep(0.5)
            user_field.send_keys(Keys.TAB)
            time.sleep(1)
            pw_field.send_keys(password)
            time.sleep(1)
            
            # Click the login button after ensuring it is clickable
            self.wait.until(EC.element_to_be_clickable(login_button))
            self.clickjs(login_button)
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

    def fill_window(self) -> None:
        """
        Minimizes the browser window and moves it to the background.

        **Purpose**:
        This method is critical for improving automation stability and system performance during Selenium-based tasks. By resizing and repositioning the browser window, it achieves the following:
        
        1. **Reduces Visual Distraction**:
        - Keeps the browser out of sight while tasks are running, avoiding interference with the user's workflow or screen visibility.
        
        2. **Optimizes System Performance**:
        - Minimizing the window can reduce the rendering workload on the system's GPU and CPU, which is particularly useful when running long, repetitive tasks.

        3. **Mimics Background Processing**:
        - Creates a background process environment, simulating headless browser behavior without requiring a dedicated headless browser setup. This is useful for debugging, as headless mode can sometimes behave differently from a visible browser.

        **How It Works**:
        - `set_window_size(1, 1)`: Shrinks the browser window to an almost invisible size.
        - `set_window_position(2000, 2000)`: Moves the browser window off-screen, effectively hiding it.

        **When to Use**:
        - During tasks that don't require direct browser interaction by the user (e.g., automated form submissions or web scraping).
        - To prevent disruptions while running automation scripts in parallel with other activities.

        **Example**:
        ```python
        bot.fill_window()
        ```

        **Important Notes**:
        - This method is an alternative to using a fully headless browser, offering similar benefits while still allowing visibility for debugging (if needed).
        - It's especially valuable in environments where switching to headless mode might cause compatibility issues.

        """

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
                    
                    scrollresults = self.get_children(self.locator["search"])

                    # Scroll through job listings to load more results.
                    for i in range(300, 1500, 100):
                        self.browser.execute_script("arguments[0].scrollTo(0, {})".format(i), scrollresults[0])
                        time.sleep(0.5)  # Wait for new elements to load.

                # Check if job links are present on the page.
                if self.is_present(self.locator["links"]):
                    links = self.get_children(self.locator["links"])
                    
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
                                self.clickjs(dismissBtn)
                                continue  # Skip this job card if it's already applied.

                        except NoSuchElementException:
                            # Add the job's ID to the list of `jobIDs`. If ALL are True: 
                            # 1) The job title is NOT blacklisted. 
                            # 2) If the company of the job is not blacklisted
                            jobIsBanned = False

                            for word in blacklist + blackListTitles:
                                if word.lower() in link.text.lower():
                                    log.debug(f"Job has a banned word: {word}\nDetails: {link.text}")
                                    jobIsBanned = True

                            if jobIsBanned == False:
                                jobID = link.get_attribute("data-job-id")

                                if jobID.isdigit():
                                    # Ensure the job ID is unique before adding it for processing.
                                    if "Easy Apply" in link.text:
                                        jobIDs[jobID] = True

                                else:
                                    log.debug(f"Job ID not found, It is likely a 'promoted' job; It doesn't fit the current query {link.text}")
                                    continue
                            # traceback.format_exc()
                    
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
        """
        Iterates over a list of job IDs and applies to each job.

        **Purpose**:
        This method serves as the core loop for automating job applications. It ensures that the bot systematically processes and applies to jobs based on their unique identifiers (job IDs), marking each job as visited to avoid duplicate applications.

        **Functionality**:
        - **Iterates Through Job IDs**:
        - Takes a list of job IDs, representing jobs to apply for, and applies to each one sequentially.
        - **Applies to Each Job**:
        - Calls the `apply_to_job()` method for each job ID, which handles the individual application process.
        - **Tracks Visited Jobs**:
        - Updates the `visited_IDs` dictionary to keep track of jobs that have already been processed, preventing redundant applications.

        **Parameters**:
        - `jobIDs` (list): A list of unique job identifiers (strings or integers) that the bot will apply to.

        **How It Works**:
        1. Logs the start of the `apply_loop()` process for debugging.
        2. Iterates over each job ID in the input list.
        3. Calls the `apply_to_job(jobID)` method for each ID to perform the application.
        4. Marks the job as visited by setting `self.visited_IDs[jobID] = True`.

        **Example**:
        ```python
        job_ids = ["12345", "67890", "24680"]
        bot.apply_loop(job_ids)
        ```

        **Why This Method is Important**:
        - **Automates Repetition**: Eliminates the manual effort of applying to jobs individually by automating the process.
        - **Prevents Redundancy**: Tracks processed jobs to avoid duplicate applications, improving efficiency.
        - **Scalable**: Can handle large numbers of job IDs, making it suitable for bulk job applications.

        **Notes**:
        - Relies on the `apply_to_job()` method for the actual application logic.
        - The `visited_IDs` dictionary must be maintained throughout the session to ensure proper tracking.
        """
        log.debug("In `apply_loop()`")
        for jobID in jobIDs:
            if jobID not in self.visited_IDs:
                self.apply_to_job(jobID)
                self.visited_IDs[jobID] = True


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

        # Try to find the Easy Apply button on the job page.
        button = self.get_easy_apply_button()
    
        if button is not False:
            # Skip job if the title contains blacklisted keywords.
            if any(word in self.browser.title for word in blackListTitles):
                log.info('Skipping this application, a blacklisted keyword was found in the job position')
                string_easy = "~ Contains blacklisted keyword"
                result = False
            else:
                job_element = self.get_child(self.locator["job_title"])
                if job_element:
                    job_title = job_element.text
                else:
                    job_title = "No title available"
                    
                company_element = self.get_child(self.locator["company_name"])
                if company_element:
                    company_name = company_element.text
                else:
                    company_name = "No title available"


                posted_date = date.today().strftime("%m/%d/%Y")
                # posted_date = today.
                # Easy Apply button is available, so click it to proceed.
                string_easy = "~ Has Easy Apply Button. Clicking now!"
                self.clickjs(button)

                # Fill out the necessary fields on the Easy Apply form.
                time.sleep(3)

                self.fill_out_fields()

                time.sleep(2)
                
                # Send the resume and determine if the application was successful.
                result: bool = self.send_resume()
                if result:
                    string_easy = "~ Sent Resume!"
                    self.add_job_link(posted_date, job_title, company_name, jobID)
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
        """
        Scrolls through a webpage to load all dynamic content and retrieves the page's HTML.

        **Purpose**:
        This method ensures that all dynamically loaded content on a webpage is fully visible and accessible by simulating user scrolling. Many modern web pages load content dynamically as users scroll, so this function is essential for extracting complete data using web scraping tools like BeautifulSoup.

        **Functionality**:
        - **Scrolls Down the Page**:
        - Simulates scrolling by incrementally moving down the webpage in steps of 500 pixels.
        - Repeats this process until the maximum scroll height (4000 pixels) is reached.
        - **Pauses Between Scrolls**:
        - Introduces a delay (default 1 second) between scrolls to mimic human interaction and allow content to load.
        - **Resets to the Top**:
        - Scrolls back to the top of the page after completing the downward scroll.
        - **Retrieves Page Source**:
        - Extracts the current state of the page's HTML source using Selenium and parses it with BeautifulSoup.

        **Parameters**:
        - `sleep` (int, optional): The number of seconds to pause between scroll steps. Default is 1 second.

        **Returns**:
        - `page` (BeautifulSoup object): A parsed HTML representation of the webpage's current state.

        **Example**:
        ```python
        page_content = bot.load_page(sleep=2)
        print(page_content.prettify())
        ```

        **Why This Method is Important**:
        - **Handles Infinite Scrolling**: Essential for scraping sites that load content dynamically as the user scrolls (e.g., job boards, social media feeds).
        - **Ensures Complete Data**: Helps retrieve the full page content, which might not be available if the user only loads the top section.
        - **Enhances Scraping Accuracy**: By using BeautifulSoup on the fully loaded page, it ensures no content is missed.

        **Notes**:
        - The maximum scroll height (`4000`) and step size (`500`) can be adjusted based on the webpage's structure and behavior.
        - Increasing the `sleep` time may help with slower-loading pages and/or reduce the risk of being flagged as a bot.
        """
        scroll_page = 0
        while scroll_page < 4000:
            self.browser.execute_script("window.scrollTo(0," + str(scroll_page) + " );")
            scroll_page += 500
            time.sleep(sleep)

        self.browser.execute_script("window.scrollTo(0,0);")

        page = BeautifulSoup(self.browser.page_source, "lxml")
        return page

    def get_easy_apply_button(self):
        """
        Identifies and retrieves the "Easy Apply" button from a LinkedIn job listing page.

        **Purpose**:
        This method is crucial for automating job applications on LinkedIn, specifically targeting positions with the "Easy Apply" feature. It searches for buttons labeled "Easy Apply," ensuring the automation interacts with the correct UI element.

        **Functionality**:
        - **Waits for Buttons to Load**:
        - Uses `WebDriverWait` to wait up to 30 seconds for the presence of elements matching the locator for "Easy Apply" buttons.
        - **Retrieves and Normalizes Button Text**:
        - Extracts the text content of each button and normalizes it to lowercase with extra whitespace removed for accurate comparison.
        - **Identifies the Correct Button**:
        - Checks for the presence of the phrase "easy apply" in the button's normalized text.
        - Returns the first matching button.

        **Parameters**:
        - None.

        **Returns**:
        - `EasyApplyButton` (WebElement or bool): The identified "Easy Apply" button if found, otherwise `False`.

        **Example**:
        ```python
        easy_apply_button = bot.get_easy_apply_button()
        if easy_apply_button:
            easy_apply_button.click()
        else:
            print("Easy Apply button not found.")
        ```

        **Why This Method is Important**:
        - **Automates Job Applications**: Identifies the specific button required to proceed with automated applications on LinkedIn.
        - **Handles Dynamic Content**: Waits for dynamic loading of buttons, a common behavior on modern web pages.
        - **Reduces Errors**: Ensures the automation script interacts only with the relevant "Easy Apply" button, avoiding unintended actions.

        **Error Handling**:
        - Logs detailed errors if the button cannot be found within the timeout period.
        - Captures and prints debugging information, such as raw and normalized button text, for troubleshooting.

        **Notes**:
        - This method assumes the locator for "Easy Apply" buttons is stored in `self.locator["easy_apply_button"]`.
        - Adjustments to the timeout duration may be necessary for slower-loading pages.
        - Multiple matching buttons are possible; this method returns the first match.
        """
        EasyApplyButton = False
        try:
            # Wait for up to 30 seconds for the button(s) to appear
            WebDriverWait(self.browser, 30).until(
                lambda _: self.get_children(self.locator["easy_apply_button"])
            )
            # Retrieve the buttons once they're present
            buttons = self.get_children(self.locator["easy_apply_button"])
            
            for button in buttons:
                # Capture the button text
                button_text = button.get_attribute("innerText")
                print(f"Raw button text: {repr(button_text)}")

                # Normalize and check for a match
                cleaned_text = " ".join(button_text.lower().split())
                print(f"Normalized button text: {repr(cleaned_text)}")

                if "easy apply" in cleaned_text:
                    print("Found Easy Apply button!")
                    EasyApplyButton = button
                    break  # Exit the loop after finding the first matching button
                else:
                    print(f"Button text did not match: {repr(cleaned_text)}")

        except Exception as e:
            log.error(f"Error finding Easy Apply button: {str(e)}")
            log.error(traceback.format_exc())

        return EasyApplyButton

    def fill_out_fields(self):
        """
        Fills out form fields on a job application page, such as the "Mobile phone number" field.

        **Purpose**:
        This method is designed to automate the process of filling out form fields during a job application. It specifically targets required fields, like phone numbers, to ensure applications are complete and valid.

        **Functionality**:
        - **Identifies Form Fields**:
        - Retrieves all elements matching the locator for form fields (`self.locator["fields"]`).
        - **Fills Specific Fields**:
        - Searches for fields labeled "Mobile phone number" and inputs the value stored in `self.phone_number`.
        - **Handles Pre-filled Fields**:
        - Clears any pre-filled values before entering the new data.

        **Parameters**:
        - None.

        **Returns**:
        - None.

        **Example**:
        ```python
        bot.fill_out_fields()
        ```

        **Why This Method is Important**:
        - **Ensures Application Completeness**: Automates the entry of critical details, such as contact information, which are required for most job applications.
        - **Saves Time**: Reduces manual intervention by automating repetitive tasks.
        - **Handles Dynamic Field Detection**: Adapts to various application forms by identifying and interacting with fields dynamically.
        - **Fills Static Questions**: Personal info like "phone number" or "email" do not change often. 
        So, answers can be hardcoded.

        **Error Handling**:
        - Logs errors if form fields cannot be retrieved or populated.
        - Provides detailed information about the exception for troubleshooting.

        **Notes**:
        - This method currently handles only the "Mobile phone number" field. Additional logic can be added for other fields as needed.
        - Relies on the `self.get_children` and `self.get_child` methods to locate fields and interact with them.
        - Assumes the `self.phone_number` attribute is properly initialized.

        **Improvements**:
        - Extend functionality to handle other common fields (e.g., email, address).
        - Incorporate field validation to ensure data integrity before submission.
        - Add dynamic field mapping for better flexibility in handling different forms.

        **Potential Upgrades**:
        - Extend functionality to handle "Phone Country Codes" and "Email Address" fields. Your personal infomation is saved for future job applications. Therefore, 
        this method wastes time filling information that is unlikely to change often.
        """
        try:
            fields = self.get_children(self.locator["fields"])
            for field in fields:

                if "Mobile phone number" in field.text:
                    # Locate the input field within the current field element
                    field_input = self.get_child((By.TAG_NAME, "input"), field)
                    field_input.clear()  # Clear any pre-existing value
                    field_input.send_keys(self.phone_number)  # Enter the phone number

                elif "first name" in field.text:
                    # Locate the input field within the current field element
                    field_input = self.get_child((By.TAG_NAME, "input"), field)
                    field_input.clear()  # Clear any pre-existing value
                    field_input.send_keys(self.first_name)  # Enter the phone number
                
                elif "city" in field.text:
                    # Locate the input field within the current field element
                    field_input = self.get_child((By.TAG_NAME, "input"), field)
                    field_input.clear()
                    field_input.send_keys(self.city)
                    time.sleep(1)
                    field_input.send_keys(Keys.ARROW_DOWN)
                    field_input.send_keys(Keys.ENTER)


        except Exception as e:
            log.error(e)


    def send_resume(self) -> bool:
        """
        Attempts to submit a job application by uploading required documents and completing the application process.

        **Purpose**:
        This method automates the job application submission process, handling various steps such as uploading resumes 
        and cover letters, answering additional questions, and interacting with buttons (e.g., "Submit", "Next", 
        "Continue Applying").

        **Workflow**:
        - Checks for the presence of various elements needed for submission (e.g., upload fields, buttons).
        - Uploads the resume and cover letter if applicable.
        - Interacts with buttons for submission and navigation through application steps.
        - Handles errors or prompts for additional information.
        - Logs whether the application was successfully submitted.

        **Key Functional Steps**:
        1. **Follow Button**:
        - Interacts with the "Follow" checkbox if present to mark the company as followed.
        2. **Submit Button**:
        - Attempts to submit the application by interacting with the "Submit" button.
        3. **Error Handling**:
        - Checks for errors during submission and handles questions or other issues dynamically.
        - Monitors the application process for success or failure.
        4. **Navigation Buttons**:
        - Handles "Next", "Continue Applying", and "Review" buttons to progress through the application.
        5. **Time Management**:
        - Terminates the process if it exceeds a specific time limit (5 minutes).

        **Parameters**:
        - None.

        **Returns**:
        - `bool`: `True` if the resume was successfully submitted, `False` otherwise.

        **Why This Method is Important**:
        - **Streamlines Automation**: Automates a multi-step process that can be repetitive and error-prone if done manually.
        - **Handles Dynamic Scenarios**: Adapts to different application flows, including optional fields and follow-up questions.
        - **Error Recovery**: Implements checks and fallback mechanisms for unexpected errors or incomplete submissions.
        - **Efficiency**: Saves time by automating tasks like uploading documents, clicking buttons, and answering questions.

        **Error Handling**:
        - Logs detailed information about any exceptions that occur, including stack traces.
        - Terminates the process gracefully if issues persist for over 5 minutes.

        **Example Usage**:
        ```python
        success = bot.send_resume()
        if success:
            print("Application successfully submitted!")
        else:
            print("Application submission failed.")
        ```

        **Notes**:
        - Relies on `self.is_present`, `self.get_children`, and `self.clickjs` to interact with the application page.
        - Assumes that the locators (`self.locator`) are correctly defined and accessible.
        - Requires `self.uploads` to contain valid paths for the resume and cover letter, if applicable.

        **Improvements**:
        - Add support for additional file uploads or field interactions as needed.
        - Enhance error handling to retry specific steps before terminating.
        - Include a progress tracker to log steps completed within the application process.
        """

        try:
            submitted = False
            start_time = time.time()  # Record the start time of the entire process

            # Loop to attempt the resume submission.
            while True:
                time.sleep(1.5)
                
                # Handle follow button if present.
                if self.is_present(self.locator["follow"]):
                    elements = self.get_children(self.locator["follow"])
                    for element in elements:
                        button = self.wait.until(EC.element_to_be_clickable(element))
                        self.clickjs(button)

                # Handle submit button and complete the application.
                if self.is_present(self.locator["submit"]):
                    elements = self.get_children(self.locator["submit"])
                    for element in elements:
                        button = self.wait.until(EC.element_to_be_clickable(element))
                        self.clickjs(button)
                        log.info("Application Submitted")
                        submitted = True
                        break

                # Handle errors during submission.
                elif self.is_present(self.locator["error"]):
                    if "application was sent" in self.browser.page_source:
                        log.info("Application Submitted")
                        submitted = True
                        break
                    else:
                        while True:
                            log.info("Please answer the questions, waiting 2 seconds...")
                            self.process_questions()

                            if "application was sent" in self.browser.page_source:
                                log.info("Application Submitted")
                                submitted = True
                                break

                            elif self.is_present(self.locator["easy_apply_button"]):
                                submitted = False
                                break

                            log.debug(f"{(time.time() - start_time) / 60} minutes elapsed")

                            # Check if 5 minutes (300 seconds) have passed since the function started
                            elapsed_time = time.time() - start_time
                            if elapsed_time > 300:  # 300 seconds = 5 minutes
                                log.info("5 minutes elapsed. Exiting the process.")
                                return False  # Return here to stop the entire process after 5 minutes

                # Handle next, continue, and review buttons if present.
                elif self.is_present(self.locator["next"]):
                    elements = self.get_children(self.locator["next"])

                    for element in elements:
                        button = self.wait.until(EC.element_to_be_clickable(element))
                        self.clickjs(button)

                elif self.is_present(self.locator["upload_cover"]):
                    elements = self.get_children(self.locator["upload_cover"])
                    for element in elements:
                        button = self.wait.until(EC.element_to_be_clickable(element))
                        button.send_keys(self.uploads["cover_letter"])

                elif self.is_present(self.locator["continue_applying"]):
                    elements = self.get_children(self.locator["continue_applying"])
                    for element in elements:
                        button = self.wait.until(EC.element_to_be_clickable(element))
                        self.clickjs(button)

                elif self.is_present(self.locator["review"]):
                    elements = self.get_children(self.locator["review"])
                    for element in elements:
                        button = self.wait.until(EC.element_to_be_clickable(element))
                        self.clickjs(button)

                # Check if the total process time has exceeded 5 minutes
                elapsed_time = time.time() - start_time
                if elapsed_time > 300:  # 300 seconds = 5 minutes
                    log.info("5 minutes elapsed. Exiting the process.")
                    return False  # Stop the entire process if 5 minutes are exceeded

        except Exception as e:
            log.error(e)
            log.error("Cannot apply to this job")

        return submitted

    def process_questions(self):
        """
        Processes the questions in a job application form by automatically selecting or filling out appropriate answers 
        based on predefined responses.

        **Purpose**:
        This method automates the process of answering questions in a job application form, filling in answers for
        different types of fields such as radio buttons, multi-select, text input, location select, date inputs, and more.

        **Workflow**:
        - **Clearing existing selections**: Ensures any pre-selected radio buttons or other choices are unselected.
        - **Form Field Processing**: Iterates over all form fields and determines the appropriate answer based on the question.
        - **Answer Selection**:
        - For **radio buttons**, the method attempts to select the correct option based on predefined answers.
        - For **multi-select** fields, it selects the closest match or a random option if an exact match isn't found.
        - For **text input** fields, the method enters predefined text answers.
        - For **autocomplete fields**, the method types the answer and selects from suggested options.
        - For **date fields**, it selects the correct date from the input.
        - **Error Handling**: Catches errors for stale elements and logs issues when elements are not found or cannot be interacted with.

        **Parameters**:
        - None.

        **Returns**:
        - None (the method performs actions on the form directly).

        **Why This Method is Important**:
        - **Automation of Form Filling**: This method saves time and avoids human error by automating the process of filling out complex forms.
        - **Dynamic Field Handling**: It adapts to various field types and ensures that the correct value is selected or entered for each field.
        - **Error Recovery**: Handles edge cases like stale elements, missing fields, or unresponsive elements by retrying actions or selecting fallback options.

        **Key Functional Steps**:
        1. **Clear Existing Selections**: Clears radio buttons or selections that may be pre-set.
        2. **Form Iteration**: Iterates through each form field to determine its type and select the appropriate answer.
        3. **Answer Selection**:
        - For **radio buttons**, the method attempts to select the exact match for the answer, or the closest match if an exact match is not found.
        - For **multi-selects**, it selects answers that closely match the predefined answers.
        - For **text fields**, it types predefined text into the form fields.
        4. **Retries and Error Handling**: If an element becomes stale, the method re-fetches the form and retries actions. The method also logs detailed errors for better debugging.
        5. **Random Selection as Fallback**: If no suitable match is found for certain questions, the method randomly selects an option.

        **Error Handling**:
        - Catches and logs exceptions such as `StaleElementReferenceException` and general `Exception`.
        - Handles retries in case of stale elements or missing options in select fields.

        **Example Usage**:
        ```python
        bot.process_questions()
        ```

        **Notes**:
        - Relies on locators defined in `self.locator` for finding form fields and elements.
        - Assumes predefined answers are accessible (e.g., `answer` variable).
        - Works with various types of form fields, including radio buttons, select dropdowns, text inputs, and date fields.

        **Improvement Suggestions**:
        - Add a more robust method for handling dynamic question formats or unexpected form changes.
        - Include more complex fallback strategies when exact answers cannot be matched.
        - Allow for customization of answers for specific types of questions (e.g., filling in different answers for the same question on multiple forms).
        """
        
        form = self.get_children(self.locator["fields"])  # Getting form elements

        print("Length: ", len(form))

        for i in range(len(form)):
            try:
                field = form[i]
                question = field.text.strip()  # Strip whitespace from question
                answer = self.ans_question(question.lower())  # Get answer based on the current question

            except StaleElementReferenceException:
                log.warning(f"Element became stale: {field}, re-fetching form elements.")
                continue

            # Scroll the field into view before interacting
            self.browser.execute_script("arguments[0].scrollIntoView(true);", field)

            # Check if input type is radio button
            if self.is_present(self.locator["radio_select"], field):
                try:
                    log.debug("Locator: radio_select")
                    radio_buttons = self.get_children(self.locator["radio_select"], field)

                    if radio_buttons is None or len(radio_buttons) == 0:
                        log.error(f"No radio buttons found for question: {question}")
                        continue

                    selected = False

                    for radio_button in radio_buttons:
                        if radio_button.get_attribute('value').lower() == answer.lower():
                            self.clickjs(radio_button)
                            log.info(f"Radio button selected: {radio_button.get_attribute('value')}")
                            selected = True

                    if selected == False:
                        log.info("Exact match not found, looking for closest answer...")
                        closest_match = None
                        for radio_button in radio_buttons:
                            radio_value = radio_button.get_attribute('value')
                            if answer.lower() in radio_value.lower():
                                try:
                                    # closest_match = field.find_element(By.XPATH, f".//input[@value=\"{radio_value}\"]")
                                    closest_match = self.get_child((By.XPATH, f".//input[@value=\"{radio_value}\"]"), field)
                                except NoSuchElementException:
                                    log.error(f"No element found for radio value: {radio_value}")

                        if closest_match:
                            self.clickjs(closest_match)
                            log.info(f"Closest radio button selected: {closest_match.get_attribute('value')}")
                            
                        else:
                            log.warning("No suitable radio button found to select. Picking random option")
                            value = random.choice(radio_buttons).get_attribute('value')
                            # ran_option = field.find_element(By.XPATH, f".//input[@value=\"{value}\"]")
                            ran_option = self.get_child((By.XPATH, f".//input[@value=\"{value}\"]"), field)
                            self.clickjs(ran_option)
                            
                except StaleElementReferenceException:
                    log.warning(f"Retrying due to stale element in radio button. ")

                except Exception as e:
                    log.error(f"Radio button error for question: {question}, answer: {answer}")
                    log.error(traceback.format_exc())  # Full traceback for better debugging
                
            # Multi-select case
            elif self.is_present(self.locator["multi_select"], field):
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
                        options = self.get_children((By.TAG_NAME, "option"), select_element)
                        for option in options:
                            if answer.lower() in option.text.strip().lower():
                                self.clickjs(option)
                                foundChoice = True
                                log.info(f"Option selected: {option.text}")
                                break

                        if not foundChoice:
                            self.clickjs(options[1])  # Select the 1st option as a fallback
                            log.info(f"1st Option selected: {options[1].text}")

                        break  # Successfully selected an option, exit loop early

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
            elif self.is_present(self.locator["text_select"], field):
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
                    log.error(f"('text_select' error: {e}") 

            # Handle auto complete fields
            elif self.is_present(self.locator["location_select"], field):
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
                    log.error(f"'location_select' error: {e}") 

            # Handle textarea fields
            elif self.is_present(self.locator["text_area"], field):
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
                    log.error(f"'text_area' error: {e}")

            # Handle fieldset fields
            elif self.is_present(self.locator["input_select"], field):  # Adjust options as needed
                try:
                    log.debug("Locator: input_select")
                    select_elements = self.get_children(self.locator["input_select"], field)

                    if select_elements is None or len(select_elements) == 0:
                        log.error(f"No select elements found for question: {question}")
                        continue

                    selected = False

                    for select_element in select_elements:
                        # Check for attributes starting with 'data-test-text-selectable-option'
                        try:
                            attr_value = select_element.get_attribute('data-test-text-selectable-option__input')
                            # select_element = field.find_element(By.XPATH, f".//input[@data-test-text-selectable-option__input=\"{attr_value}\"]")
                            select_element = self.get_element((By.XPATH, f".//input[@data-test-text-selectable-option__input=\"{attr_value}\"]"), field)

                            
                            # Check if the attribute value matches the answer
                            if answer.lower() == attr_value.lower():
                                self.clickjs(select_element)
                                log.info(f"Select element chosen: {attr_value}")
                                selected = True
                                break  # Exit loop once the option is selected

                        except Exception as e:
                            log.error(f"Couldn't find exact match: {e}")
                            log.error(traceback.format_exc())

                    if selected == False:
                        log.info("Looking for closest answer...")
                        closest_match = None
                        for select_element in select_elements:
                            try: 
                                # Get the value of the specific attribute
                                attr_value = select_element.get_attribute('data-test-text-selectable-option__input')
                                
                                # Check if the attribute value is present and if the answer is in it
                                if answer.lower() in attr_value.lower():  # Check if answer is in the attribute value
                                    # closest_match = field.find_element(By.XPATH, f".//input[@data-test-text-selectable-option__input=\"{attr_value}\"]")
                                    closest_match = self.get_child((By.XPATH, f".//input[@data-test-text-selectable-option__input=\"{attr_value}\"]"), field)

                                    break  # Exit early loop on first closest match

                            except Exception as e:
                                log.error(e)
                                log.error(traceback.format_exc())  # Full traceback for better debugging
                                
                        if closest_match:
                            self.clickjs(closest_match)
                            log.info(f"Closest select element chosen: {closest_match.get_attribute('value')}")

                        else:
                            log.warning("No suitable select option found. Picking the random option")
                            # Pick random choice
                            random_option = random.choice(select_elements)
                            self.clickjs(random_option)
                            log.info(f"Random option selected: {random_option.get_attribute('value')}")
                                
                except StaleElementReferenceException:
                    log.warning(f"Retrying due to stale element in fieldset.")

                except Exception as e:
                    log.error(f"Select element error for question: {question}, answer: {answer}")
                    log.error(traceback.format_exc())  # Full traceback for better debugging

            # Handle date input fields
            elif self.is_present(self.locator["date_input"], field):
                try:
                    log.debug("Locator: date_input")

                    # Locate the date field using the correct locator strategy
                    date_field = WebDriverWait(field, 15).until(
                        EC.presence_of_element_located(self.locator["date_input"])
                    )

                    # Send the answer (date) to the input
                    date_field.clear()
                    date_field.send_keys(answer)  # Ensure 'answer' is formatted correctly as "mm/dd/yyyy"
                    time.sleep(1)
                    self.clickjs(date_field)
                    time.sleep(3)

                    today_button = self.get_child((By.XPATH, ".//button[contains(@aria-label, 'This is today')]"), field)
                    
                    self.clickjs(today_button)

                    log.info(f"Date input filled with value: {answer}")
                    
                except Exception as e:
                    log.error(f"Error while filling the date input: {e}")
                    log.error(traceback.format_exc())  # Full traceback for better debugging

            else:
                log.info(f"Unable to determine field type for question: {question}, moving to next field.")

    def is_present(self, locator, field=None):
        """
        Checks if an element specified by the locator is present on the page quickly.
        Args:
            locator (tuple): A tuple containing the locator strategy and value 
                            (e.g., (By.ID, 'element_id')).
            field (WebElement, optional): A parent WebElement to search within. If 
                                        None (default), searches on the entire page.
        Returns:
            bool: True if the element is found within the timeout, False otherwise.
        """
        try:
            if field:
                # Using find_elements to avoid the overhead of waiting for only one element
                elements = field.find_elements(locator[0], locator[1])
            else:
                elements = self.browser.find_elements(locator[0], locator[1])
            
            # Quickly return True if the element exists
            return len(elements) > 0
        except Exception as e:
            print(f"Error occurred while checking element presence: {e}")
            return False

    def get_child(self, locator, field=None):
        """
        Finds a child element within a specified field or the entire page using a given locator.

        **Purpose**:
        This method helps in locating and returning a child element inside a specified parent field or the entire web page.
        It is designed to provide a more convenient wrapper around the `find_element` method to locate elements based on a tuple locator.

        **Parameters**:
        - `locator` (tuple): A tuple containing two elements:
            - The first element is the locator strategy (e.g., "id", "xpath", "css_selector", etc.).
            - The second element is the locator value, such as the id, name, or xpath expression to identify the element.
        - `field` (WebElement or None, optional): The parent element to search within. If `None` (default), it searches the entire page (`self.browser`).

        **Returns**:
        - `WebElement` if the element is found.
        - `None` if the element is not found or an error occurs during the search.

        **Exceptions**:
        - This method catches any exception raised during the element search and logs the error message. It returns `None` when an error occurs or when no element is found.

        **Behavior**:
        - If `field` is provided, the search is confined to that parent element. Otherwise, the search is performed on the entire web page (`self.browser`).
        - The locator should be a tuple where the first element is the strategy (like "xpath", "id", etc.) and the second element is the actual value to locate the element.
        - In case of an error (e.g., element not found), the method logs the error and returns `None` instead of raising an exception.

        **Example Usage**:
        ```python
        # Find an element on the page using xpath
        element = bot.get_child(("xpath", "//div[@id='example']"))
        
        # Find an element within a specific field (a parent element)
        parent_field = driver.find_element_by_id("parent")
        element = bot.get_child(("xpath", "//span[@class='child']"), parent_field)
        ```

        **Why This Method is Useful**:
        - Provides a centralized way to handle element search with error logging and convenient locator handling.
        - Avoids repetitive error handling when finding elements and encapsulates it within a single method.
        - Supports both searching on the entire page or within a specific parent element.

        **Notes**:
        - This method assumes that `locator` is always a tuple. It doesn't perform any validation or transformation of the locator.
        - This method uses the `find_element` method, which will throw an exception if no matching element is found. The exception is caught within this method to return `None` gracefully.

        **Example**:
        ```python
        # Find an element using a class_name locator
        element = bot.get_child(("class_name", "example_class"))

        # Find an element inside a specific field (div element)
        parent_field = driver.find_element_by_tag_name("div")
        child_element = bot.get_child(("xpath", ".//button[@class='submit']"), parent_field)
        ```

        **Possible Improvements**:
        - Add more detailed error logging or handle specific exceptions separately.
        - Validate the `locator` input to ensure it's a tuple with two elements (locator strategy and value).
        - Return a more detailed error message or logging mechanism in case of failures.
        """
        # Use self.browser as the default if field is not provided
        if field is None:
            field = self.browser
        try:
            # Find the element using the locator tuple, assuming the first item is the strategy and the second is the value
            return field.find_element(locator[0], locator[1])
        except Exception as e:
            print(f"Error occurred while finding element with locator {locator}: {e}")
            return None  # Return None if the element is not found or an error occurs

                
    def get_children(self, locator, field=None):
        """
        Finds all child elements within a specified field or the entire page using a given locator.

        **Purpose**:
        This method helps in locating and returning all child elements that match a specified locator inside a given parent element or on the entire page.

        **Parameters**:
        - `locator` (tuple): A tuple containing two elements:
            - The first element is the locator strategy (e.g., "id", "xpath", "css_selector", etc.).
            - The second element is the locator value, such as the id, name, or xpath expression to identify the elements.
        - `field` (WebElement or None, optional): The parent element to search within. If `None` (default), it searches the entire page (`self.browser`).

        **Returns**:
        - A list of `WebElement` objects that match the locator.
        - An empty list if no matching elements are found or if an error occurs during the search.

        **Exceptions**:
        - This method catches any exception raised during the element search and logs the error message. It returns an empty list when an error occurs or when no elements are found.

        **Behavior**:
        - If `field` is provided, the search is confined to that parent element. Otherwise, the search is performed on the entire web page (`self.browser`).
        - The locator should be a tuple where the first element is the strategy (like "xpath", "id", etc.) and the second element is the actual value to locate the elements.
        - In case of an error (e.g., no elements found), the method logs the error and returns an empty list.

        **Example Usage**:
        ```python
        # Find all elements on the page with a specific class
        elements = bot.get_children(("class_name", "example_class"))
        
        # Find all elements within a specific parent element (div element)
        parent_field = driver.find_element_by_id("parent")
        elements = bot.get_children(("xpath", ".//button[@class='submit']"), parent_field)
        ```

        **Why This Method is Useful**:
        - Provides a centralized way to handle element search with error logging and convenient locator handling.
        - Avoids repetitive error handling when finding multiple elements and encapsulates it within a single method.
        - Supports both searching on the entire page or within a specific parent element.

        **Notes**:
        - This method assumes that `locator` is always a tuple. It doesn't perform any validation or transformation of the locator.
        - This method uses the `find_elements` method, which returns a list. If no matching elements are found, it returns an empty list.
        - If an error occurs during element search, it logs the error and returns an empty list gracefully.

        **Example**:
        ```python
        # Find all elements with the class "example_class"
        elements = bot.get_children(("class_name", "example_class"))

        # Find all button elements within a parent div element
        parent_field = driver.find_element_by_tag_name("div")
        buttons = bot.get_children(("xpath", ".//button[@class='submit']"), parent_field)
        ```

        **Possible Improvements**:
        - Add more detailed error logging or handle specific exceptions separately.
        - Validate the `locator` input to ensure it's a tuple with two elements (locator strategy and value).
        - Return a more detailed error message or logging mechanism in case of failures.
        """
        # Use self.browser as the default if field is not provided
        if field is None:
            field = self.browser
        try:
            # Find all elements using the locator tuple, assuming the first item is the strategy and the second is the value
            return field.find_elements(locator[0], locator[1])
        except Exception as e:
            print(f"Error occurred while finding elements with locator {locator}: {e}")
            return []  # Return an empty list if no elements are found or an error occurs

    def clickjs(self, element):
        """
        Clicks an element using JavaScript. If the element is an <option> element,
        it sets the option as selected and dispatches a 'change' event. For any other
        element, it triggers a click event followed by dispatching a 'change' event.

        This method is useful for bypassing Selenium's standard `.click()` which may fail 
        when interacting with non-visible elements, such as options in dropdowns.

        Args:
            element (WebElement): The element to be clicked or selected. This can be any 
                                element, but if it's an <option> element, it will be 
                                set as selected.

        Example:
            # Example usage for a normal element
            clickjs(button_element)

            # Example usage for an <option> element (e.g., selecting an option in a dropdown)
            clickjs(option_element)
        
        Raises:
            WebDriverException: If the script execution fails or the element is not interactable.
        """
        if element.tag_name.lower() == "option":
            self.browser.execute_script("""
                arguments[0].selected = true;
                arguments[0].parentElement.dispatchEvent(new Event('change'));
            """, element)
        else:
            self.browser.execute_script("""
                arguments[0].click();
                arguments[0].dispatchEvent(new Event('change'));
            """, element)

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

    def write_to_file(self, button, jobID, browserTitle, result) -> None:
            def re_extract(text, pattern):
                target = re.search(pattern, text)
                if target:
                    target = target.group(1)
                return target

            timestamp: str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            attempted: bool = False if not button else True
            job = re_extract(browserTitle.split(' | ')[0], r"\(?\d?\)?\s?(\w.*)")
            company = re_extract(browserTitle.split(' | ')[1], r"(\w.*)")

            toWrite: list = [timestamp, jobID, job, company, attempted, result]
            print(f"Writing the following data: {toWrite}")  # Debugging line
        
            try:
                with open(self.filename, 'a+', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(toWrite)
            except Exception as e:
                print(f"Failed to write to file: {e}")

    def ans_question(self, question):
        """
        Automatically provides answers to questions based on predefined patterns.

        **Purpose**:
        This method analyzes a given question, matches it to a set of predefined patterns, and returns an appropriate answer. It uses keyword matching and pre-set rules for various question categories such as English proficiency, work authorization, basic personal information, and others. If a question cannot be automatically answered, a default response or placeholder is returned.

        **Parameters**:
        - `question` (str): The question for which an answer is needed. It should be a string containing the question text, typically in lowercase and without extra whitespace.

        **Returns**:
        - `answer` (str): The answer to the question, returned as a string. If the question cannot be automatically answered, a default response (such as "2") is returned. The answer is also logged and appended to a CSV file for record-keeping.

        **Behavior**:
        - The method searches for specific keywords or patterns in the `question` string (e.g., "english", "rate", "how many", "city", etc.).
        - Based on these keywords, it determines the correct answer from a set of predefined responses.
        - If the question matches a known pattern, it returns the corresponding answer.
        - If the question doesn't match any predefined pattern, a default answer (e.g., "2") is provided, and the system logs the failure to answer the question automatically.
        - The answer is saved in a CSV file alongside the question for later reference.

        **Categories of Question Handling**:
        - **English Proficiency**: Questions about language skills, such as speaking or communication abilities.
        - **Experience and Salary**: Questions about work experience, hourly rates, salary expectations, and work roles.
        - **Work Authorization**: Questions about legal eligibility to work, sponsorship, and visa status.
        - **Personal Information**: Questions about basic details like name, address, city, and contact information.
        - **Social Media and Websites**: Questions about social media profiles like GitHub, LinkedIn, and personal portfolios.
        - **Disability and Drug Testing**: Questions about disability status or drug test results.
        - **Commuting and Legal Issues**: Questions about commuting ability, criminal background, and legal matters.
        - **General Yes/No Questions**: Questions that ask for a simple affirmation or negation (e.g., "Do you have experience?" or "Can you commute?").
        - **Default Handling**: For questions not matching any specific pattern, a placeholder response ("2") is given.

        **Exceptions**:
        - If no matching category is found, the method logs the question and assigns a placeholder answer.
        - The `time.sleep(5)` is used in cases where a question cannot be answered automatically, ensuring that the process can continue with a placeholder answer.

        **Example Usage**:
        ```python
        # Example: Automatically answer a question about English proficiency
        question = "Do you speak English?"
        answer = self.ans_question(question)
        print(answer)  # Output: "Yes"
        ```

        **Why This Method is Useful**:
        - This method automates the process of answering frequently asked questions in forms or surveys.
        - It helps reduce the manual intervention needed for repetitive question-answering tasks, especially when the questions follow certain patterns.
        - The answers are automatically logged for future reference, ensuring traceability and record-keeping.

        **Notes**:
        - The method expects the `question` parameter to be in lowercase to improve matching accuracy.
        - If there are changes to the question patterns or categories, the method can be extended with additional if-else branches or keyword patterns.

        **Possible Improvements**:
        - Expand the predefined categories to include more specific questions.
        - Implement more sophisticated natural language processing (NLP) methods for better question understanding and answer prediction.
        - Add logging for unanswered questions or failed attempts to provide an answer.
        - Refactor the logic to handle specific keywords or phrases in a more modular fashion, such as using a dictionary of keywords and answers.
        """

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
        elif "why" in question and ("position" in question or "role" in questions):
            answer = "Good glassdoor reviews and the workers I talked to love their jobs"
        elif "do you" in question and "experience" in question:
            answer = "Yes"
        elif "how did you hear" in question:
            answer = "Other"
        elif "refer" in question or "referred" in question:
            answer = "N/A"
        elif "can you start" in question:
            answer = "Yes"

        # Work authorization questions
        elif ("legal" in question or "legally" in question) and ("work" in question or "author" in question):
            answer = "Yes"
        elif "sponsor" in question or "sponsorship" in question:
            answer = "No"
        elif "work" in question and ("authorization" in question or "authorized" in question):
            answer = "Yes"
        elif "W2" in question:
            answer = "Yes"
        elif ("eligible" in question or "able" in question) and "clearance" in question:
            answer = "Yes"
        elif ("have" in question or "obtain" in question or "obtained" in question) and "clearance" in question:
            answer = "No"
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
            answer = self.disability
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
        elif "state" in question:
            answer = self.state
        elif ("us citizen" in question or "u.s. citizen" in question) and "clearance" in question:
            answer = "Yes"
        elif "salary" in question or "annual compensation" in question:
            answer = self.salary
        elif "gender" in question:
            answer = self.gender
        elif "race" in question or "ethnicity" in question:
            answer = self.race
        elif "lgbtq" in question:
            answer = self.lgbtq
        elif "government" in question or "veteran" in question:
            answer = self.veteran
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

        # Append question and answer to the CSV
        if question not in self.answers:
            self.answers[question] = answer
            new_data = pd.DataFrame({"Question": [question], "Answer": [answer]})
            new_data.to_csv(self.qa_file, mode='a', header=False, index=False, encoding='utf-8')

        log.info("Answering question: " + question + "\nwith answer: " + str(answer))
        return str(answer)

    def add_job_link(self, date, title, company, ID):
        """
        Adds a job posting link to the applications CSV file with a description.

        This method generates a description of the job posting, including the date, title, and company,
        and appends this information, along with a direct link to the job posting, to a CSV file.

        Parameters:
        - date (str): The date when the job posting was created or found.
        - title (str): The title of the job posting.
        - company (str): The company name associated with the job posting.
        - ID (str or int): The LinkedIn job ID used to generate the job posting link.

        Returns:
        - None: This method appends the data to the CSV and does not return a value.

        Exceptions:
        - Logs any exception that occurs during the CSV writing process.
        """
        desc = f"Posting({date}): {title} FROM {company}"
        try:
            # Wrap description and link in lists to create one row
            new_data = pd.DataFrame({
                "company": [desc],
                "link": [f"https://www.linkedin.com/jobs/view/{ID}/"]
            })

            # Append to the CSV
            new_data.to_csv("applications.csv", mode='a', header=False, index=False)
        except Exception as e:
            log.error(e)

if __name__ == '__main__':
    """
    Main entry point for running the application.

    This script reads the configuration from the `config.yaml` file, validates the input data, 
    and initializes the `EasyApplyBot` with the necessary parameters for applying to job listings.

    The configuration file should include the following keys:
        - `positions`: A list of job positions to search for.
        - `locations`: A list of locations to search in.
        - `person`: Contains account information (`username`, `password`, `phone_number`) and social media details.
        - `uploads`: A dictionary containing file upload information (optional).
        - `salary`, `rate`, `time_filter`, `experience_level`: Parameters used for customizing job search criteria.
        - `blacklist`: A list of banned companies.
        - `blackListTitles`: A list of job titles to avoid.
        - `output_filename`: The desired filename for storing applied job information (optional).

    Raises:
        - AssertionError: If any required parameter is missing or incorrectly formatted in `config.yaml`.
        - Exception: If `uploads` is incorrectly formatted as a list instead of a dictionary.
    """

    # Load configuration from 'config.yaml'
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
    
    # Catch configuration errors where 'uploads' is mistakenly formatted as a list instead of a dictionary
    if 'uploads' in parameters.keys() and type(parameters['uploads']) == list:
        raise Exception("uploads read from the config file appear to be in list format while should be dict. "
                         "Try removing '-' from line containing filename & path")

    # Parse output filename and blacklist
    output_filename: list = [f for f in parameters.get('output_filename', ['output.csv']) if f is not None]
    output_filename: list = output_filename[0] if len(output_filename) > 0 else 'output.csv'
    blacklist = parameters.get('blacklist', [])
    blackListTitles = parameters.get('blackListTitles', [])
    
    # Catch any errors in 'uploads' parameter
    uploads = {} if parameters.get('uploads', {}) is None else parameters.get('uploads', {})
    for key in uploads.keys():
        assert uploads[key] is not None

    # Filter locations and positions for valid entries (non-None)
    locations: list = [l for l in parameters['locations'] if l is not None]
    positions: list = [p for p in parameters['positions'] if p is not None]

    # Log all parameters
    log.info({k: parameters[k] for k in parameters.keys()})

    # Initialize the EasyApplyBot with the extracted parameters
    bot = EasyApplyBot(
        parameters['salary'],
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
    
    # Start the job application process
    bot.start_apply(positions, locations)