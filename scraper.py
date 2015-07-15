# -*- coding: utf-8 -*-
import os
import re
import requests
import scraperwiki
import urllib2
from datetime import datetime
from bs4 import BeautifulSoup
from dateutil.parser import parse

# Set up variables
entity_id = "E1501_SBC_gov"
urls = ["http://www.southend.gov.uk/downloads/download/382/our_spending_over_500_2012", "http://www.southend.gov.uk/downloads/download/383/our_spending_over_500_2013",
       "http://www.southend.gov.uk/downloads/download/394/our_spending_over_500_2014", "http://www.southend.gov.uk/downloads/download/535/our_spending_over_500_2015"]
errors = 0
# Set up functions
def validateFilename(filename):
    filenameregex = '^[a-zA-Z0-9]+_[a-zA-Z0-9]+_[a-zA-Z0-9]+_[0-9][0-9][0-9][0-9]_[0-9][0-9]$'
    dateregex = '[0-9][0-9][0-9][0-9]_[0-9][0-9]'
    validName = (re.search(filenameregex, filename) != None)
    found = re.search(dateregex, filename)
    if not found:
        return False
    date = found.group(0)
    year, month = int(date[:4]), int(date[5:7])
    now = datetime.now()
    validYear = (2000 <= year <= now.year)
    validMonth = (1 <= month <= 12)
    if all([validName, validYear, validMonth]):
        return True
def validateURL(url):
    try:
        r = requests.get(url, allow_redirects=True, timeout=20)
        count = 1
        while r.status_code == 500 and count < 4:
            print ("Attempt {0} - Status code: {1}. Retrying.".format(count, r.status_code))
            count += 1
            r = requests.get(url, allow_redirects=True, timeout=20)
        sourceFilename = r.headers.get('Content-Disposition')

        if sourceFilename:
            ext = os.path.splitext(sourceFilename)[1].replace('"', '').replace(';', '').replace(' ', '')
        else:
            ext = os.path.splitext(url)[1]
        validURL = r.status_code == 200
        validFiletype = ext in ['.csv', '.xls', '.xlsx', '.CSV']
        return validURL, validFiletype
    except:
        raise
def convert_mth_strings ( mth_string ):

    month_numbers = {'JAN': '01', 'FEB': '02', 'MAR':'03', 'APR':'04', 'MAY':'05', 'JUN':'06', 'JUL':'07', 'AUG':'08', 'SEP':'09','OCT':'10','NOV':'11','DEC':'12' }
    #loop through the months in our dictionary
    for k, v in month_numbers.items():
#then replace the word with the number

        mth_string = mth_string.replace(k, v)
    return mth_string
# pull down the content from the webpage
for url in urls:
    html = urllib2.urlopen(url)
    soup = BeautifulSoup(html)
    # find all entries with the required class
    block = soup.find('section', 'inner-content')
    links = block.find_all('img')
    for link in links:
        if 'CSV' in link['src']:
            url = link.parent['href']
            csvfile = link.parent.text.split('500')[-1].strip()
            csvMth = csvfile[:3]
            csvYr = csvfile.split(' ')[1]
            csvMth = convert_mth_strings(csvMth.upper())
            filename = entity_id + "_" + csvYr + "_" + csvMth
            todays_date = str(datetime.now())
            file_url = url.strip()
            html_csv = urllib2.urlopen(file_url)
            soup_csv = BeautifulSoup(html_csv)
            file_url = soup_csv.find('a', 'button btn-download')['href']
            validFilename = validateFilename(filename)
            validURL, validFiletype = validateURL(file_url)
            if not validFilename:
                print filename, "*Error: Invalid filename*"
                print file_url
                errors += 1
                continue
            if not validURL:
                print filename, "*Error: Invalid URL*"
                print file_url
                errors += 1
                continue
            if not validFiletype:
                print filename, "*Error: Invalid filetype*"
                print file_url
                errors += 1
                continue
            scraperwiki.sqlite.save(unique_keys=['l'], data={"l": file_url, "f": filename, "d": todays_date })
            print filename
if errors > 0:
    raise Exception("%d errors occurred during scrape." % errors)