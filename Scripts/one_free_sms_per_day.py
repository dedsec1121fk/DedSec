import os
import time
import requests

def send_sms():
    os.system('clear' if os.name != 'nt' else 'cls')  # Clears terminal screen
    print("\n==== SMS SENDER ====\n")

    country_code = input("Country Code (00): ").strip().lstrip("+")  # Removes '+' if entered
    phone_number = input("Phone Number: ").strip()
    message = input("Message: ").strip()

    full_number = f"+{country_code}{phone_number}"  # Adds '+' automatically

    response = requests.post("https://textbelt.com/text", {
        "phone": full_number,
        "message": message,
        "key": "textbelt"  # Free-tier key (limited to 1 SMS per day)
    })

    result = response.json()

    if result.get("success"):
        print("\n✅ SMS Sent Successfully!")
    else:
        print("\n❌ Failed to Send SMS. Error:", result.get("error", "Unknown Error"))

    time.sleep(3)  # Wait before resetting

if __name__ == "__main__":
    send_sms()
