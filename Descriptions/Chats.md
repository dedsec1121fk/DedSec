## Overview

This repository contains two Flask-based chat applications that integrate real-time messaging and file sharing. Both systems employ Flask-SocketIO for WebSocket communication, enabling seamless interaction among users.

---

## Application 1: Fox Chat (`fox_chat.py`)

### Purpose
Fox Chat offers a real-time chat platform where users can exchange text messages and share files within an interactive web interface.

### Features
- **Real-Time Messaging**: Facilitates instant communication between users.
- **File Sharing**: Allows users to upload and share files, which can be downloaded by others.
- **User Nicknames**: Users can set unique nicknames that persist across sessions using local storage.
- **Responsive Design**: Adaptable interface for both dark and light themes.
- **Message History**: Newly connected users receive the chat history to stay updated.

### Workflow
1. Users are prompted to enter a nickname upon joining the chat.
2. Messages are exchanged in real time, with each user's nickname displayed alongside their message.
3. Files can be uploaded and shared via the **Send File** button, and links are generated for others to download.

### Technical Highlights
- **Backend Framework**: Flask-SocketIO handles WebSocket connections for real-time updates.
- **Frontend Integration**: Uses HTML, JavaScript, and CSS for a responsive chat interface.
- **File Handling**: Files are uploaded to a designated directory and served via Flask's file routing.

---

## Application 2: DedSec’s Chat (`dedsecs_chat.py`)

### Purpose
DedSec's Chat is a secure, real-time chat platform designed for group interactions, with support for text messaging and file sharing.

### Features
- **Secure File Uploads**: Files are saved with sanitized filenames using `secure_filename` to prevent malicious input.
- **Real-Time Communication**: Broadcasts messages and file links instantly to all connected users.
- **Persistent Nicknames**: Users can set nicknames that are stored in local storage for future sessions.
- **Adaptive UI**: A sleek, responsive design adjusts for dark and light system themes.
- **Dynamic File Links**: Generates unique, accessible links for every uploaded file.

### Workflow
1. Users are prompted to enter a nickname upon joining the chat.
2. Real-time communication allows participants to exchange messages instantly.
3. File uploads are processed securely, and links to the files are shared in the chat.

### Technical Highlights
- **Backend Framework**: Flask-SocketIO manages WebSocket connections for seamless communication.
- **Frontend Integration**: Combines HTML and JavaScript to create a dynamic user interface.
- **File Safety**: Employs `secure_filename` from Werkzeug to mitigate risks associated with file uploads.

---

## Setup Instructions

### Prerequisites
- Python 3.7+
- Flask (`pip install flask`)
- Flask-SocketIO (`pip install flask-socketio`)
- Werkzeug (for secure file handling, included with Flask)

### Steps
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-folder>
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a directory for uploads:
   ```bash
   mkdir uploads
   ```

### Running the Applications
1. Run **Fox Chat**:
   ```bash
   python fox_chat.py
   ```
   Access it at `http://localhost:<random-port>`.

2. Run **DedSec's Chat**:
   ```bash
   python dedsecs_chat.py
   ```
   Access it at `http://localhost:<random-port>`.

---

## Use Cases
- **Group Communication**: Real-time messaging for teams and communities.
- **File Exchange**: Share files securely within a group chat.
- **Event Coordination**: Use nicknames and message history to facilitate planning and discussions.

These applications are modular and can be adapted for specific requirements, such as integrating authentication or expanding to larger user bases.