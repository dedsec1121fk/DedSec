import requests
import hashlib
import json
import re
import phonenumbers as Pn
from phonenumbers import geocoder, carrier, timezone
from googlesearch import search
from six.moves.urllib.request import urlopen

# Simple regex for email validation
def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

class EmailLookup:
    def __init__(self, email):
        self.email = email
        self.lookup()

    def lookup(self):
        if is_valid_email(self.email):
            if input("Valid email. Check if it has been pwned? [y/n]: ").lower() == "y":
                self.haveIBeenPwned()
        else:
            print("Invalid email address.")

    def haveIBeenPwned(self):
        try:
            hashed_email = hashlib.sha1(self.email.encode('utf-8')).hexdigest().upper()
            response = requests.get(f"https://api.pwnedpasswords.com/range/{hashed_email[:5]}").text
            if hashed_email[5:] in response:
                count = response.split(hashed_email[5:])[1].split(':')[1].strip()
                print(f"Your email has been pwned {count} times.")
            else:
                print("Your email has not been pwned.")
        except Exception as e:
            print(f"Error: {e}")

class SearchInsta:
    def __init__(self, username):
        self.username = username
        self.lookup()

    def lookup(self):
        try:
            response = urlopen(f"https://www.instagram.com/{self.username}/?__a=1")
            data = json.loads(response.read().decode())
            self.print_data(data)
        except Exception as e:
            print(f"Error: {e}")

    def print_data(self, data):
        print("Instagram Lookup Results:")
        user = data['graphql']['user']
        print(f"Username: {user['username']}")
        print(f"Full Name: {user['full_name']}")
        print(f"Bio: {user['biography']}")
        print(f"Followers: {user['edge_followed_by']['count']}")
        print(f"Following: {user['edge_follow']['count']}")
        print(f"Business Account: {user['is_business_account']}")
        print(f"Private Account: {user['is_private']}")
        print(f"Verified Account: {user['is_verified']}")
        print(f"Profile Pic: {user['profile_pic_url_hd']}")

class IpLookup:
    def __init__(self, ip):
        self.ip = ip
        self.lookup()

    def lookup(self):
        try:
            data = requests.get(f"http://ip-api.com/json/{self.ip}").json()
            self.print_data(data)
        except Exception as e:
            print(f"Error: {e}")

    def print_data(self, data):
        print("IP Lookup Results:")
        print(f"IP: {data['query']}")
        print(f"Country: {data['country']}")
        print(f"Region: {data['region']}")
        print(f"City: {data['city']}")
        print(f"ISP: {data['isp']}")

class Lookup:
    def __init__(self, phoneNo):
        self.phoneNo = phoneNo
        self.parse_phoneNo()

    def parse_phoneNo(self):
        try:
            self.phoneNo = Pn.parse(self.phoneNo, None)
            self.validate_phoneNo()
        except Exception as e:
            print(f"Error: {e}")

    def validate_phoneNo(self):
        if Pn.is_valid_number(self.phoneNo):
            self.get_carrier()
        else:
            print("Invalid phone number.")

    def get_carrier(self):
        carrier_info = carrier.name_for_number(self.phoneNo, "en")
        self.carrier = carrier_info if carrier_info else "Unknown"
        self.get_region()

    def get_region(self):
        self.region = geocoder.description_for_number(self.phoneNo, "en")
        self.get_timeZone()

    def get_timeZone(self):
        self.timeZone = timezone.time_zones_for_number(self.phoneNo)
        self.print_data()

    def print_data(self):
        print("Phone No. Lookup Results:")
        print(f"Phone No: {self.phoneNo}")
        print(f"Carrier: {self.carrier}")
        print(f"Region: {self.region}")
        print(f"Time Zone: {self.timeZone}")

class WebSearch:
    def __init__(self, query):
        self.query = query
        self.search()

    def search(self):
        try:
            print("Searching...")
            for result in search(self.query, num=10):
                print(result)
        except Exception as e:
            print(f"Error: {e}")

class SearchUsername:
    def __init__(self, username):
        self.username = username
        self.lookup()

    def lookup(self):
        platforms = [
            "Instagram", "Twitter", "Facebook", "YouTube", 
            "Snapchat", "Spotify", "Pinterest", "Reddit", 
            "Tinder", "GitHub", "LinkedIn"
        ]
        for platform in platforms:
            self.print_url(platform)

    def print_url(self, platform):
        urls = {
            "Instagram": f"https://www.instagram.com/{self.username}",
            "Twitter": f"https://www.x.com/{self.username}/",
            "Facebook": f"https://www.facebook.com/{self.username}/",
            "YouTube": f"https://www.youtube.com/{self.username}/",
            "Snapchat": f"https://story.snapchat.com/@{self.username}/",
            "Spotify": f"https://open.spotify.com/user/{self.username}/",
            "Pinterest": f"https://www.pinterest.com/{self.username}/",
            "Reddit": f"https://www.reddit.com/user/{self.username}/",
            "Tinder": f"https://www.tinder.com/@{self.username}/",
            "GitHub": f"https://www.github.com/{self.username}/",
            "LinkedIn": f"https://www.linkedin.com/in/{self.username}/"
        }
        print(f"Link for {platform}: {urls[platform]}")

def print_menu():
    print("="*40)
    print(" " * 12 + "OSINTDS")
    print("="*40)
    print("1. Email Lookup: Validate an email address and check if it has been compromised.\n")
    print("2. Instagram Lookup: Retrieve information about an Instagram user.\n")
    print("3. IP Lookup: Get geolocation data for a specified IP address.\n")
    print("4. Phone Lookup: Validate a phone number and get carrier and location info.\n")
    print("5. Web Search: Search the web with a specified query.\n")
    print("6. Search Username: Check social media platforms for a specified username.\n")
    print("7. Exit: Close the program.\n")
    print("="*40)

def main():
    while True:
        print_menu()
        choice = input("Select an option (1-7): ")

        if choice == '1':
            email = input("Enter email address (e.g., example@example.com): ")
            EmailLookup(email)
        elif choice == '2':
            username = input("Enter Instagram username (without @): ")
            SearchInsta(username)
        elif choice == '3':
            ip = input("Enter IP address (e.g., 192.168.1.1): ")
            IpLookup(ip)
        elif choice == '4':
            phone = input("Enter phone number (e.g., +1234567890): ")
            Lookup(phone)
        elif choice == '5':
            query = input("Enter search query (e.g., Python programming): ")
            WebSearch(query)
        elif choice == '6':
            username = input("Enter username (e.g., example_user): ")
            SearchUsername(username)
        elif choice == '7':
            break
        else:
            print("Invalid choice. Please select a valid option (1-7).")

if __name__ == "__main__":
    main()

