# SMS Sender Script

A simple Python script to send SMS messages using the Textbelt API. This script allows users to input their phone number, country code, and message, and sends an SMS via a free-tier API key.

## Features

- Allows users to send an SMS to any phone number.
- Simple and interactive terminal interface.
- Uses Textbelt's free-tier API (limited to 1 SMS per day).

## How It Works

- The script prompts the user for their country code, phone number, and message.
- It constructs the full phone number by adding a "+" sign to the country code and phone number.
- The script then sends the SMS via a POST request to the Textbelt API.
- After sending, the result will be shown in the terminal, indicating success or failure.

## Notes

- This script uses a free-tier Textbelt API key, which is limited to 1 SMS per day. You may want to use your own API key for more functionality.
- The terminal is cleared after each attempt to send an SMS for a clean interface.
