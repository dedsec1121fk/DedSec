# Link Generator

`link_generator.py` is a Python script that automates the process of generating a Cloudflare tunnel link. The script prompts the user to input a local server URL, validates it, and then uses `cloudflared` to create a secure public link.

## Features
- Takes a local URL as input.
- Runs `cloudflared` to establish a tunnel.
- Extracts and displays the generated Cloudflare link.
- Keeps the tunnel active until manually stopped.

## Requirements
- Python 3.x
- `cloudflared` installed and accessible in the system's PATH.

## Usage
1. Run the script:  
   ```bash
   python link_generator.py
   ```
2. Enter the requested local URL when prompted.
3. The script will display the public Cloudflare link.

## Notes
- The generated link should be opened in Chrome, Firefox, or Safari.
- Ensure `cloudflared` is correctly installed before running the script.