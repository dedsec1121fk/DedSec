## Overview

This Flask-based web application, **DedSec Database**, provides an intuitive platform to upload, search, download, and delete files. It includes real-time port management and offers an optional Serveo tunnel for remote access.

---

## Purpose

The application is designed for secure and efficient file management with a modern interface, enabling users to interact with uploaded files while ensuring seamless access.

---

## Features

- **File Management**: Users can upload, search, download, and delete files from the database.
- **Search Functionality**: Quickly locate files by entering keywords.
- **Port Management**: Automatically clears processes using the specified port for smooth operation.
- **Serveo Tunnel Integration**: Provides a public URL for remote access using the Serveo platform.
- **Dynamic UI**: Responsive interface with dark green-on-black aesthetics, inspired by hacker culture.
- **Error Handling**: User-friendly messages for actions like file not found, upload issues, and others.

---

## Workflow

1. **File Management**:
   - Users can upload files directly via the interface.
   - Uploaded files are stored in the **Database** directory.
   - Files can be downloaded or deleted as required.

2. **Search**:
   - Users can search for files by name, filtering the list of available files.
   - If no matching files are found, an error message is displayed.

3. **Serveo Tunnel** (Optional):
   - A public URL is created for accessing the application remotely.
   - The URL is automatically generated and displayed in the terminal.

4. **Port Management**:
   - Clears any process using the specified port before starting the Flask application.

---

## Technical Highlights

### Backend
- **Flask Framework**: Handles HTTP requests for file management and rendering the user interface.
- **Serveo Tunnel**: Uses `ssh` to create a public URL for external access.
- **Threading**: Runs Serveo tunnel alongside the Flask server for seamless operation.
- **OS Integration**: Ensures the `Database` folder exists and handles file operations efficiently.

### Frontend
- **Dynamic HTML Template**: Displays uploaded files and provides options to download or delete them.
- **Search Integration**: Filters displayed files based on user input.
- **Responsive Design**: CSS ensures usability across devices and adjusts for longer filenames.

---

## Setup Instructions

### Prerequisites
- Python 3.7+
- Flask (`pip install flask`)

### Steps
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-folder>
   ```
2. Install Flask:
   ```bash
   pip install flask
   ```
3. Start the application:
   ```bash
   python dedsec_database.py
   ```

4. Access the application:
   - **Locally**: Visit `http://localhost:5002`.
   - **Remote (Serveo)**: The public URL will be displayed in the terminal.

---

## Usage

1. **Upload Files**:
   - Use the **Upload File** form to upload files to the server.

2. **Search Files**:
   - Use the **Search** box to filter files based on their names.

3. **Download Files**:
   - Click the **Download** button next to a file to retrieve it.

4. **Delete Files**:
   - Click the **Delete** button to remove a file permanently.

---

## Error Handling

- **File Not Found**: Displays a message if the searched file doesn't exist.
- **Upload Errors**: Shows user-friendly messages for issues during upload.
- **Deletion Errors**: Handles errors if a file cannot be deleted or is missing.

This application ensures a smooth user experience with real-time feedback for actions performed.