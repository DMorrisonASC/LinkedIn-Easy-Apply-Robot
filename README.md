# LinkedIn-Easy-Apply-Robot
Automate the applying for jobs on LinkedIn (Only for 'easy apply' jobs).

## Setup 

Python 3

The run the bot install requirements
```bash
pip3 install -r requirements.txt
```

Enter your username, password, and search settings into the `config.yaml` file

```yaml
# Quotes are not needed in the key's values. Example `first_name: John`
person:
  name: 
    title: '' # Enter your...
    first_name:  # Enter your...
    last_name:  # Enter your...
  account:
    username:  # Enter your...
    password:  # Enter your...
  social_media:
    github: # Enter if applicable
    linkedin:  # Enter if applicable
    portfolio:  # Enter if applicable
    phone_number: # Enter your...
  address:
    street: # Enter your...
    city: # Enter your...
    state: # Enter your...
    zip:  # Enter your...
    country: # Enter your...
  demographic: # "Yes" and "No" are booleans in yaml, surround them in quotes
    race: # Ex: Asian, Black, White
    gender: # Ex: Male, Female
    disability: '' # Ex: 'Yes' or 'No'
    veteran: '' # Ex: 'Yes' or 'No'
    lgbtq: '' # hetero, gay, pansexual, etc.

profile_path: '' # Use it to log into a specific chrome profile. Ex: 'C:\Users\<user>\AppData\Local\Google\Chrome\User Data\Profile 1'

positions:
- full stack developer
- Dentist

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
uploads: ''
  resume: ''
  cover_letter: ''

output_filename:
- ''

blacklist: # Company names you want to ignore
- SynergisticIT 
# blackListTitles: # jobs you want to ignore
# - 

experience_level:
  - 1 # Entry level
  - 2 # Associate
  - 3 # Mid-Senior level
  - 4 # Director
  - 5 # Executive
  - 6 # Internship
time_filter:  4 # 1 = 24 hours, 2 = Last week, 3 = Last month. Else, it will pick anytime
```
__NOTE: Add `config.yaml`, 'resume/' and 'cover_letters' into .gitignore file!__

### Uploads

You can list as many files as you want in the uploads section.
The program reads the titles from the input boxes and matches them with the list in the config file.

### Edit `rules.json`.
It is a .json file used to add answers to questions. For example,
an "if statement" in python:
```python
question = question.lower().strip()   
if "english" in question and ( "speak" in question or "communicate" in question):
        answer = "yes"
```
The "if statement" above would be converted to json like this:
```json
{
  "conditions": [
    { "type": "AND", "keywords": ["english"] },
    { "type": "OR", "keywords": ["speak", "communicate"] }
  ],
  "response": "Yes"
},
```
Example `rules.json`
```json
{
    "rules": [
      {
        "conditions": [
          { "type": "AND", "keywords": ["english"] },
          { "type": "OR", "keywords": ["speak", "communicate"] }
        ],
        "response": "Yes"
      },
      {
        "conditions": [
          { "type": "AND", "keywords": ["english"] },
          { "type": "OR", "keywords": ["proficiency", "level"] }
        ],
        "response": "Native"
      },
      {
        "conditions": [
          { "type": "OR", "keywords": ["how many", "how much", "enter a decimal number"] }
        ],
        "response": "random_choice"
      },
      {
        "conditions": [
          { "type": "AND", "keywords": ["rate"] },
          { "type": "OR", "keywords": ["yourself", "proficient", "proficiency"] }
        ],
        "response": "10"
      },
      {
        "conditions": [
          { "type": "AND", "keywords": ["hourly"] },
          { "type": "OR", "keywords": ["rate", "salary", "what"] }
        ],
        "response": "dynamic_rate"
      },
      {
        "conditions": [
          { "type": "AND", "keywords": ["why"] },
          { "type": "OR", "keywords": ["position", "role"] }
        ],
        "response": "Good glassdoor reviews and the workers I talked to love their jobs"
      },
      {
        "conditions": [
          { "type": "AND", "keywords": ["do you"] },
          { "type": "AND", "keywords": ["experience"] }
        ],
        "response": "Yes"
      },
      {
        "conditions": [
          { "type": "AND", "keywords": ["how did you hear"] }
        ],
        "response": "Other"
      },
      {
        "conditions": [
          { "type": "OR", "keywords": ["refer", "referred"] }
        ],
        "response": "N/A"
      },
      {
        "conditions": [
          { "type": "AND", "keywords": ["can you start"] }
        ],
        "response": "Yes"
      },
      {
        "conditions": [
          { "type": "AND", "keywords": ["legal", "work"] }
        ],
        "response": "Yes"
      },
      {
        "conditions": [
          { "type": "OR", "keywords": ["sponsor", "sponsorship"] },
          { "type": "OR", "keywords": ["require", "will you", "do you need"] }
        ],
        "response": "No"
      },
      {
        "conditions": [
          { "type": "AND", "keywords": ["work"] },
          { "type": "OR", "keywords": ["authorization", "authorized"] }
        ],
        "response": "Yes"
      },
      {
        "conditions": [
          { "type": "OR", "keywords": ["W2"] }
        ],
        "response": "Yes"
      },
      {
        "conditions": [
          { "type": "OR", "keywords": ["eligible", "able"] },
          { "type": "AND", "keywords": ["clearance"] }
        ],
        "response": "Yes"
      },
      {
        "conditions": [
          { "type": "OR", "keywords": ["have", "active", "obtain"] },
          { "type": "AND", "keywords": ["clearance"] }
        ],
        "response": "No"
      },
      {
        "conditions": [
          { "type": "OR", "keywords": ["US", "U.S.", "green"] },
          { "type": "OR", "keywords": ["citizen", "card"] }
        ],
        "response": "Yes"
      },
      {
        "conditions": [
          { "type": "AND", "keywords": ["privacy policy"] }
        ],
        "response": "I agree"
      },
      {
        "conditions": [
          { "type": "AND", "keywords": ["date"] },
          { "type": "OR", "keywords": ["earliest", "start", "mm/dd/yyyy", "format"] }
        ],
        "response": "dynamic_date"
      },
      {
        "conditions": [
          { "type": "OR", "keywords": ["city", "address"] }
        ],
        "response": "dynamic_city"
      },
      {
        "conditions": [
          { "type": "OR", "keywords": ["zip", "area code", "postal"] }
        ],
        "response": "dynamic_zipcode"
      },
      {
        "conditions": [
          { "type": "AND", "keywords": ["first"] }
        ],
        "response": "dynamic_first_name"
      },
      {
        "conditions": [
          { "type": "AND", "keywords": ["last"] }
        ],
        "response": "dynamic_last_name"
      },
      {
        "conditions": [
          { "type": "AND", "keywords": ["your name"] }
        ],
        "response": "dynamic_full_name"
      },
      {
        "conditions": [
          { "type": "AND", "keywords": ["github"] }
        ],
        "response": "dynamic_github"
      },
      {
        "conditions": [
          { "type": "AND", "keywords": ["linkedin"] }
        ],
        "response": "dynamic_linkedin"
      },
      {
        "conditions": [
          { "type": "OR", "keywords": ["portfolio", "personal website"] }
        ],
        "response": "dynamic_portfolio"
      },
      {
        "conditions": [
          { "type": "AND", "keywords": ["disability"] }
        ],
        "response": "dynamic_disability"
      },
      {
        "conditions": [
          { "type": "AND", "keywords": ["drug test"] },
          { "type": "OR", "keywords": ["positive"] }
        ],
        "response": "No"
      },
      {
        "conditions": [
          { "type": "AND", "keywords": ["drug test"] },
          { "type": "OR", "keywords": ["can you"] }
        ],
        "response": "Yes"
      },
      {
        "conditions": [
          { "type": "AND", "keywords": ["can you"] },
          { "type": "AND", "keywords": ["commute"] }
        ],
        "response": "Yes"
      },
      {
        "conditions": [
          { "type": "OR", "keywords": ["criminal", "felon", "charged"] }
        ],
        "response": "No"
      },
      {
        "conditions": [
          { "type": "AND", "keywords": ["currently reside"] }
        ],
        "response": "Yes"
      },
      {
        "conditions": [
          { "type": "AND", "keywords": ["state"] }
        ],
        "response": "dynamic_state"
      },
      {
        "conditions": [
          { "type": "OR", "keywords": ["salary", "annual compensation"] }
        ],
        "response": "dynamic_salary"
      },
      {
        "conditions": [
          { "type": "AND", "keywords": ["gender"] }
        ],
        "response": "dynamic_gender"
      },
      {
        "conditions": [
          { "type": "OR", "keywords": ["race", "ethnicity"] }
        ],
        "response": "dynamic_race"
      },
      {
        "conditions": [
          { "type": "AND", "keywords": ["lgbtq"] }
        ],
        "response": "dynamic_lgbtq"
      },
      {
        "conditions": [
          { "type": "OR", "keywords": ["government", "veteran"] }
        ],
        "response": "dynamic_veteran"
      },
      {
        "conditions": [
          { "type": "AND", "keywords": ["phone"] },
          { "type": "OR", "keywords": ["mobile", "number"] }
        ],
        "response": "dynamic_phone_number"
      },
      {
        "conditions": [
          { "type": "OR", "keywords": ["do you", "did you", "have you", "are you"] }
        ],
        "response": "Yes"
      }
    ],
    "default": "2"
  }
```

### Main.py
Edit the `def ans_question(self, question)` function to modify answers to the questions on applications

### Execute

To execute the bot run the following in your terminal
```
python3 main.py
```
## Bugs
- Uploading resume doesn't work; upload it manually
- a slight chance that the bot gets stuck in a loop if the job is closed while still applying
- Small chance that previously applied jobs appear when bot is supposed to ignore applied jobs
- Have not accounted for all possible web elements yet. Ex: if bot was not programmed to answer a specific web element and/or the 'locator' breaks(often when LinkedIn changes id and class names)
