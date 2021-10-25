from bs4 import BeautifulSoup
import requests
import sys
import re

# Get all the unique item links 
url = "http://classic.battle.net/diablo2exp/items/uniques.shtml"
try:
    page = requests.get(url, timeout=1).text
except WindowsError:
    print("Connection timeout. Ending script.")
    sys.exit()

doc = BeautifulSoup(page, "html.parser")
text = doc.find_all("a", href=re.compile("diablo2exp/items"))

links = []
for link in text:
    links.append(link["href"])

with open("C:\\Users\\Jim\\Documents\\discord_bot\\tactix-bot\\tools\\d2_unique_links.txt", "w") as f:
    for link in links:
        f.write(f"http://classic.battle.net/{str(link)}\n")

print("Done")
