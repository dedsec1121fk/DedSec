## Overview

This application is a Flask-based location tracking and analysis system that captures user location data, processes it for detailed insights, and stores the results securely. The application includes IP-based geolocation, nearby store detection, and an optional Serveo tunnel for remote access.

---

## Purpose

The system is designed to collect and analyze geolocation data to enhance connectivity and provide actionable insights, such as:
- **Signal Optimization**: Improve mobile network coverage in specific areas.
- **Location Analysis**: Generate detailed reports about user location, including nearby points of interest.
- **Remote Accessibility**: Allow secure access to the system via a Serveo tunnel.

---

## Features

1. **Location Capture**:
   - Collects GPS coordinates (latitude, longitude, accuracy).
   - Optionally enriches location data with altitude, speed, and heading.

2. **Detailed Address Information**:
   - Uses reverse geocoding to extract the full address, including city, street, region, and more.

3. **Nearby Store Detection**:
   - Leverages the Overpass API to find shops within a 2-km radius.

4. **IP-Based Geolocation**:
   - Fetches approximate user location based on their public IP address.

5. **Secure Storage**:
   - Saves location data as JSON files in a structured directory.

6. **Remote Access**:
   - Integrates Serveo for generating public URLs to access the app remotely.

7. **Error Handling**:
   - Provides detailed logs for debugging and ensures robust error management.

---

## Workflow

1. **Frontend Interaction**:
   - Users access the app through a simple web interface.
   - Clicking the "Allow Location Access" button triggers GPS permission requests.
   - Location data is sent to the server for processing.

2. **Backend Processing**:
   - The Flask backend enriches location data with:
     - Reverse geocoded address.
     - List of nearby stores.
     - IP-based location information.
   - Saves the processed data to a timestamped JSON file.

3. **Serveo Tunnel** (Optional):
   - Provides a public link to access the application remotely.
   - Automatically retries if the tunnel fails to start.

4. **Logs and Monitoring**:
   - Logs detailed location data and application activity to `application.log`.

---

## Setup Instructions

### Prerequisites

- Python 3.7+
- Required libraries:
  ```bash
  pip install flask geopy requests
  ```
- Optional: SSH client installed for Serveo tunnel.

### Installation Steps

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd <repository-folder>
   ```

2. **Run the Application**:
   ```bash
   python location_tracker.py
   ```

3. **Access the App**:
   - **Locally**: Visit `http://localhost:5665`.
   - **Remote (Serveo)**: The public URL is displayed in the terminal.

---

## Usage

1. **Capture Location**:
   - Open the app in your browser.
   - Click the **"Allow Location Access"** button to share your location.

2. **View Processed Data**:
   - The application saves location data as JSON files in:
     ```bash
     ~/storage/downloads/LocationData
     ```

3. **Analyze Data**:
   - Logs are stored in `application.log` with detailed information about captured locations.

4. **Remote Access**:
   - Use the Serveo-generated URL to access the app remotely.

---

## Technical Highlights

### Backend
- **Flask Framework**: Handles location uploads and serves the web interface.
- **Geopy**: Performs reverse geocoding to enrich location data.
- **Overpass API**: Detects nearby stores within a 2-km radius.

### Frontend
- **JavaScript**:
  - Captures user location via the `Geolocation` API.
  - Sends location data to the server using `fetch`.

### Logging and Monitoring
- **File Logs**: Detailed logs are saved in `application.log`.
- **Error Handling**: Provides user-friendly messages for errors.

### Port Management
- **Port Handling**: Stops processes using the default port (5665) before starting the application.

---

## Error Handling

- **Location Denial**: Notifies the user if location access is denied.
- **IP Geolocation Errors**: Logs any issues when fetching IP-based location data.
- **Serveo Tunnel Failures**: Automatically retries if the tunnel cannot be established.

---

## Benefits

- **Signal Optimization**: Helps identify weak network areas for improvement.
- **Accessibility**: Remote access via Serveo enables monitoring from anywhere.
- **Actionable Insights**: Combines GPS, IP, and nearby store data for a comprehensive location profile.

This system is robust, secure, and highly adaptable for use in connectivity analysis, logistics, or urban planning.