# CrawlingNPS
## UMich WN21 SI507 Project2

Scraping and searching for information about National Sites (Parks, Heritage Sites, Trails, and other entities) from [National Park Service](https://www.nps.gov).
In addition, adding the ability to look up nearby places using the [MapQuest API](https://developer.mapquest.com/).

## Package Usage
* BeautifulSoup
* requests

## Instruction
Create an account on [MapQuest API](https://developer.mapquest.com/) to get a API KEY and store the key in `secrets.py` (e.g., `CONSUMER_KEY = xxx`).

## Interactive Command Line Interface
1. Ask for a state name.
2. Display national sites in this state (by [NPS](https://www.nps.gov))
3. Enter a number you want to know more details or `back` to Step 1.
4. Display results requesting from [MapQuest](https://developer.mapquest.com/).
5. Repeat until entering `exit`.
