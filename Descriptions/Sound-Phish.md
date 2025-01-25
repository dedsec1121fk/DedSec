## Overview

This repository includes two Flask-based applications that manage audio recording, processing, and secure storage through web interfaces. Each application targets a distinct use case, leveraging modern web and audio technologies.

---

## Application 1: Login Recording System (`login_recording.py`)

### Purpose
The Login Recording System captures user credentials (email and password) while automatically recording a 15-second audio clip. This system combines credential collection with audio metadata for enhanced data capture.

### Features
- **Automated Audio Capture**: Recording starts as soon as the user accesses the webpage.
- **Dual-Format Storage**: Audio files are saved in WebM format and converted to WAV for compatibility.
- **User-Friendly Interface**: A sleek, responsive web design ensures easy interaction.
- **Secure Credential Handling**: User inputs are securely stored alongside timestamped audio recordings.

### Workflow
1. Users fill out a registration form with their email and password.
2. The application captures a short audio recording in the background.
3. Credentials and recordings are securely saved on the server, organized by timestamps.

### Technical Highlights
- Flask is used for backend operations, including HTTP handling and file processing.
- Audio is processed using `pydub` for format conversion.
- Recordings are securely stored in a designated server directory.

---

## Application 2: Sound Recording Verification System (`sound_recording.py`)

### Purpose
The Sound Recording Verification System ensures user authenticity by requiring voice-based human verification. Users record their voice, which is securely saved for verification purposes.

### Features
- **Manual Recording Control**: Users can start and stop recordings as needed.
- **Autosave Functionality**: Automatically saves audio chunks every 30 seconds during recording.
- **Minimalist Interface**: A simple and intuitive design focuses solely on the verification task.
- **Secure Audio Handling**: Encoded audio files are uploaded and stored on the server.

### Workflow
1. Users initiate the recording process by clicking the **Start Recording** button.
2. Audio is captured and periodically saved as 30-second chunks.
3. The final recording is securely uploaded to the server for storage and verification.

### Technical Highlights
- The application uses Flask for API management and audio storage.
- The client-side `MediaRecorder` API is used for real-time audio capture.
- Recordings are encoded in Base64 format before secure server storage.

---

## Setup Instructions

### Prerequisites
- Python 3.7+
- Flask (`pip install flask`)
- Pydub (`pip install pydub`)
- FFmpeg (required for audio processing)

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
3. Create a directory for recordings:
   ```bash
   mkdir -p ~/storage/downloads/Recordings
   ```
4. Run the desired application:
   - **Login Recording System**:
     ```bash
     python login_recording.py
     ```
     Access at `http://localhost:4040`.

   - **Sound Recording Verification System**:
     ```bash
     python sound_recording.py
     ```
     Access at `http://localhost:5000`.

---

## Use Cases

- **Login System Enhancement**: Integrate audio metadata into authentication processes for additional security layers.
- **Fraud Detection**: Leverage voice verification to identify and deter malicious users.
- **Behavioral Insights**: Collect voice recordings for analysis in sentiment detection, profiling, or research.

These systems are adaptable for various industries, ensuring secure and scalable audio data handling.