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