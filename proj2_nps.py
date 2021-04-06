#################################
##### Name:
##### Uniqname:
#################################

from bs4 import BeautifulSoup
import requests
import json
import secrets # file that contains your API key

CACHE_STATES_FILENAME = "states_data.json"
CACHE_PARKS_FILENAME = "parks_data.json"
CACHE_INFO_FILENAME = "info_data.json"
CACHE_NEARBY_FILENAME = "nearby_data.json"
BASE_URL = "https://www.nps.gov"

def open_cache(cache_filename):
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary
    
    Parameters
    ----------
    None
    
    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open(cache_filename, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = None
    return cache_dict
    
class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.
    
    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''
    def __init__(self, name=None, category=None, phone=None, address=None, zipcode=None, site_url=None):
        if(site_url is None):
            self.name = name
            self.category = category
            self.phone = phone
            self.address = address
            self.zipcode = zipcode
        else:
            response = requests.get(site_url)
            soup = BeautifulSoup(response.text, 'html.parser')

            header = soup.find('div', class_="Hero-titleContainer clearfix")
            try:
                self.name = header.find("a").text.strip()
            except:
                self.name = None
            try:
                self.category = header.find("span", class_="Hero-designation").text.strip()
            except:
                self.category = None

            footer = soup.find('div', class_="ParkFooter-contact")
            try:
                phone_tag = footer.find('span', itemprop="telephone", class_="tel")
                self.phone = phone_tag.text.strip()
            except:
                self.phone = None
            try:
                address_tag = footer.find('div', class_="mailing-address")
                address_tag = address_tag.find('p', class_="adr")
                self.address = address_tag.find('span', itemprop="addressLocality").text.strip() + ", " + address_tag.find('span', itemprop="addressRegion").text.strip()
                self.zipcode = address_tag.find('span', itemprop="postalCode").text.strip()
            except:
                self.address = None
                self.zipcode = None
    def info(self):
        return f"{self.name} ({self.category}): {self.address} {self.zipcode}"


def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''
    state_url_dict = open_cache(CACHE_STATES_FILENAME)
    if(state_url_dict is not None):
        print("Using Cache")
        return state_url_dict
        
    print("Fetching")
    response = requests.get(BASE_URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    state_url_dict = {}
    
    # Find urls of all states
    states_parent = soup.find('div', class_="SearchBar-keywordSearch input-group input-group-lg")
    states_lists = states_parent.find("ul", class_="dropdown-menu SearchBar-keywordSearch")
    for litag in states_lists.find_all("li"):
        SUB_URL = litag.find("a")["href"]
        state = litag.text
        state_url_dict[state.lower()] = BASE_URL+SUB_URL
    
    # Save cache
    with open(CACHE_STATES_FILENAME, "w") as f:
        json.dump(state_url_dict, f)

    return state_url_dict

def get_site_instance(site_url):
    '''Make an instances from a national site URL.
    
    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov
    
    Returns
    -------
    instance
        a national site instance
    '''
    info_dict = open_cache(CACHE_INFO_FILENAME)
    # cache file exists and site_url exists in cache
    if(info_dict is not None and site_url in info_dict.keys()):
        print("Using Cache")
        name, category, phone, address, zipcode = info_dict[site_url]
        return NationalSite(name, category, phone, address, zipcode)
    
    print("Fetching")
    if(info_dict is None):
        info_dict = {}
    info = NationalSite(site_url=site_url)
    info_dict[site_url] = [info.name, info.category, info.phone, info.address, info.zipcode]

    # Save Cache
    with open(CACHE_INFO_FILENAME, "w") as f:
        json.dump(info_dict, f)

    return info


def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.
    
    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov
    
    Returns
    -------
    list
        a list of national site instances
    '''
    parks_dict = open_cache(CACHE_PARKS_FILENAME)
    # cache file exits and the state's parks exist in cache
    if(parks_dict is not None and state_url in parks_dict.keys()):
        print("Using Cache")
        return [get_site_instance(park_url) for park_url in parks_dict[state_url]]
    
    print("Fetching")
    response = requests.get(state_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find urls of all parks
    park_urls = []
    park_tags = soup.find_all("div", class_="col-md-9 col-sm-9 col-xs-12 table-cell list_left")
    for park_tag in park_tags:
        park_url = park_tag.find('h3').find('a')["href"]
        park_urls.append(BASE_URL+park_url)
    
    # Save cache
    if(parks_dict is None):
        parks_dict = {}
    parks_dict[state_url] = park_urls
    with open(CACHE_PARKS_FILENAME, "w") as f:
        json.dump(parks_dict, f)

    return [get_site_instance(park_url) for park_url in parks_dict[state_url]]



def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.
    
    Parameters
    ----------
    site_object: object
        an instance of a national site
    
    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    nearby_dict = open_cache(CACHE_NEARBY_FILENAME)
    # cache file exits and the state's parks exist in cache
    if(nearby_dict is not None and site_object.zipcode in nearby_dict.keys()):
        print("Using Cache")
        response_json = nearby_dict[site_object.zipcode]
        results = response_json["searchResults"]

    else:
        print("Fetching")
        search_url = "http://www.mapquestapi.com/search/v2/radius"
        query = {"key": secrets.CONSUMER_KEY, 
                "origin": site_object.zipcode, 
                "radius": 10, 
                "maxMatches": 10, 
                "ambiguities": "ignore", 
                "outFormat": "json"
        }
        response = requests.get(search_url, query)
        response_json = response.json()
        results = response_json["searchResults"]
        # Save cache
        if(nearby_dict is None):
            nearby_dict = {}
        nearby_dict[site_object.zipcode] = response_json
        with open(CACHE_NEARBY_FILENAME, "w") as f:
            json.dump(nearby_dict, f)
    
    show_nothing = ["no name", "no category", "no address", "no city"]
    for result in results:
        keywords = ["name", "group_sic_code_name_ext", "address", "city"]
        result = result["fields"]
        for i in range(len(keywords)):
            keywords[i] = show_nothing[i] if (keywords[i] not in result.keys() or result[keywords[i]] == "") else result[keywords[i]]
        print(f"- {keywords[0]} ({keywords[1]}): {keywords[2]}, {keywords[3]}")
    
    return response_json

def display(string):
    print("-"*len(string))
    print(string)
    print("-"*len(string))

if __name__ == "__main__":
    
    states_data = build_state_url_dict()
    back_first_time = False
    # STEP 1 - input a valid state name
    command = input("Enter a state name (e.g., Michigan, michigan) or \"exit\": ")
    while(command != "exit"):
        while(command.lower() not in states_data.keys() and command != "exit"):
            # After second loop, if command is back and it is first time here, don't print error message
            # to avoid users input "back" without error message printing
            if(command != "back" or not back_first_time):
                print("[Error] Enter a proper state name.")
            back_first_time = False
            command = input("Enter a state name (e.g., Michigan, michigan) or \"exit\": ")
        # STEP 2 - print info of all sites in the state
        if(command != "exit"):
            state_url = states_data[command.lower()]
            sites = get_sites_for_state(state_url)
            display(f"List of national sites in {command}")
            for i in range(len(sites)):
                print(f"[{i+1}] {sites[i].info()}")

            # Step 3 - Choose one valid number or exit or back
            command = input("Choose the number for detail search or \"exit\" or \"back\": ")
            while(command != "exit" and command != "back"):
                while(command != "exit" and command != "back" and (not command.isnumeric() or int(command) < 1 or int(command) > len(sites))):
                    print("[Error] Invalid input.")
                    command = input("Choose the number for detail search or \"exit\" or \"back\": ")
                # Step 4 - Valid number
                if(command != "exit" and command != "back"):
                    command = int(command)
                    display(f"Places near {sites[command-1].name}")
                    get_nearby_places(sites[command-1])
                    command = input("Choose the number for detail search or \"exit\" or \"back\": ")
            # Letting command not perceived as error for one time
            if(command == "back"):
                back_first_time = True