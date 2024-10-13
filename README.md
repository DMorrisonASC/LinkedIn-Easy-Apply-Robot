# LinkedIn-Easy-Apply-Robot
Automate the applying for jobs on LinkedIn (Only for 'easy apply' jobs)

## Setup 

Python 3.10 using a conda virtual environment on Linux (Ubuntu)

The run the bot install requirements
```bash
pip3 install -r requirements.txt
```

Enter your username, password, and search settings into the `config.yaml` file

```yaml
# Quotes are not needed in the key's values. Example `first_name: John`
person:
  name: 
    title: ''
    first_name:  
    last_name: 
  account:
    username:  # your email
    password: 
  social_media:
    github: 
    linkedin: 
    portfolio: 
    phone_number: 
  address:
    street: 
    city: 
    state: 
    zip: 

profile_path: '' # Use it to log into a specific chrome profile. Ex: 'C:\Users\<user>\AppData\Local\Google\Chrome\User Data\Profile 1'

positions:
- Software Engineer
- Data Engineer
- Front End developer
- Backend developer
- full stack developer

locations:
- Remote
- Alabama
- Alaska
- Arizona
- Arkansas
- California
- Colorado
- Connecticut
- Delaware
- Florida
- Georgia
- Hawaii
- Idaho
- Illinois
- Indiana
- Iowa
- Kansas
- Kentucky
- Louisiana
- Maine
- Maryland
- Massachusetts
- Michigan
- Minnesota
- Mississippi
- Missouri
- Montana
- Nebraska
- Nevada
- New Hampshire
- New Jersey
- New Mexico
- New York
- North Carolina
- North Dakota
- Ohio
- Oklahoma
- Oregon
- Pennsylvania
- Rhode Island
- South Carolina
- South Dakota
- Tennessee
- Texas
- Utah
- Vermont
- Virginia
- Washington
- West Virginia
- Wisconsin
- Wyoming

salary: 70000
rate: 40
# --------- Optional Parameters -------
uploads:
  resume: 
  cover_letter: 

output_filename:
- 

blacklist: # Company names you want to ignore
- SynergisticIT 
# blackListTitles:
# - # jobs you want to ignore

experience_level:
  - 1 # Entry level
  - 2 # Associate
  - 3 # Mid-Senior level
  - 4 # Director
  - 5 # Executive
  - 6 # Internship
```
__NOTE: Add `config.yaml`, 'resume/' and 'cover_letters' into .gitignore file!

### Uploads

You can list as many files as you want in the uploads section.
The program reads the titles from the input boxes and matches them with the list in the config file.

## Execute

To execute the bot run the following in your terminal
```
python3 easyapplybot.py
```
