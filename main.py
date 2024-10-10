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