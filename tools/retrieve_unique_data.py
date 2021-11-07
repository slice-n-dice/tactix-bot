#!/usr/bin/env python3.10

from time import sleep
from bs4 import BeautifulSoup
import requests
import sys
import re
import json


# Store the links for all unique items
unique_links = []
try:
    with open("C:\\Users\\Jim\\Documents\\discord_bot\\tactix-bot\\tools\\d2_unique_links.txt", "r") as f:
        for index, line in enumerate(f):
            unique_links.append(line.strip())
except:
    print("Link file not found. Ending script.")
    sys.exit()

# Store the page data for each link
# classic.battle.net is powered by a hamster on a wheel,
# and most page requests fail, so we have to retry multiple times
pages = [] # will contain page text
with requests.Session() as s:
    for link in unique_links:
        attempt = 1
        page_retrieved = False
        while not page_retrieved:
            try:
                pages.append(s.get(link, timeout=1).text)
                page_retrieved = True
            except WindowsError:
                print(f"Attempt #{attempt} failed on {link}. Waiting and retrying...")
                attempt += 1
                sleep(3)

soups = []
for page in pages:
    soups.append(BeautifulSoup(page, "html.parser"))

uniques_json = {} # will contain all unique data for the json file

# In the following loop, I need the try-except statements because there are 
# some poorly-formatted HTML pages that will otherwise cause the program to fail
# Since this is an edge case, I'll just save all the data for the working pages,
# and add to the JSON file the data on the "bad" pages by hand.
for soup in soups:
    category = soup.find(color=re.compile("908858")).string
    print(category)
    uniques_json[category] = []
    item_soups = soup.find(cellpadding=5).find_all("tr") # all item info is within a <tr> tag
    for item_soup in item_soups:
        table_cells = item_soup.find_all("td")
        center_tags = table_cells[0].find_all("center")
        item_name = center_tags[0].string
        item_type = center_tags[1].string
        try:
            item_attributes = table_cells[1].get_text().strip()
            temp_dict = {}
            temp_dict["Name"] = item_name
            temp_dict["Gear Type"] = item_type
            temp_dict["Attributes"] = item_attributes
            uniques_json[category].append(temp_dict)
        except:
            print(f"Error processing {item_name} in {category}. Add that to the json by hand.")

with open("C:\\Users\\Jim\\Documents\\discord_bot\\tactix-bot\\tools\\d2_uniques.json", "w") as f:
    json.dump(uniques_json, f, indent=4)

print("Finished successfully.")