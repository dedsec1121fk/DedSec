## **Overview**

This repository contains three Python scripts that create lightweight Flask-based web applications for capturing images from device cameras and collecting user input. These scripts are configured to run efficiently on Termux.

---

## **Features**

### **1. `back_camera.py`**
- Captures images using the back camera of the device.
- Automatically captures an image every **3 seconds**.
- Saves images to the `~/storage/downloads/Camera-Phish` directory with timestamped filenames.
- Displays a minimalistic web interface with a live camera feed and a disclaimer.
- Alerts users if the camera cannot be accessed.

### **2. `front_camera.py`**
- Captures images using the front (selfie) camera of the device.
- Automatically captures an image every **3 seconds**.
- Saves images to the `~/storage/downloads/Camera-Phish` directory with timestamped filenames.
- Displays a responsive web interface with a live camera feed and a disclaimer.

### **3. `login_camera.py`**
- Captures images every **2 seconds** using the front camera.
- Includes a form for collecting email addresses and passwords.
- Saves submitted credentials in text files in `~/storage/downloads/Camera-Phish`.
- Saves captured images with timestamped filenames in the same directory.
- Allows customization of the background image, which is stored at `~/storage/downloads/Camera-Phish/2025.jpg`.

---

## **Installation**

### **Prerequisites**
- Python 3.x
- Flask
  ```bash
  pip install flask
  ```

### **Setup**
1. Grant Termux storage permissions:
   ```bash
   termux-setup-storage
   ```
2. Create the required directory for saving files:
   ```bash
   mkdir -p ~/storage/downloads/Camera-Phish
   ```

### **Running the Scripts**
1. Execute the desired script:
   ```bash
   python script_name.py
   ```
   Replace `script_name.py` with the desired script (`back_camera.py`, `front_camera.py`, or `login_camera.py`).

2. Open a web browser and navigate to:
   ```
   http://<device-ip>:<port>
   ```
   Replace `<device-ip>` with your device's IP address and `<port>` with the corresponding port:
   - `back_camera.py`: **4040**
   - `front_camera.py`: **4543**
   - `login_camera.py`: **4040**

---

## **Usage**

### **back_camera.py**
1. Start the script:
   ```bash
   python back_camera.py
   ```
2. Access the application in a web browser.
3. Images are automatically captured every 3 seconds and saved in `~/storage/downloads/Camera-Phish`.

### **front_camera.py**
1. Start the script:
   ```bash
   python front_camera.py
   ```
2. Access the application in a web browser.
3. Images are automatically captured every 3 seconds and saved in `~/storage/downloads/Camera-Phish`.

### **login_camera.py**
1. Start the script:
   ```bash
   python login_camera.py
   ```
2. Access the application in a web browser.
3. Fill out the form with an email and password. Submitted credentials are saved in `~/storage/downloads/Camera-Phish`.
4. Images are captured every 2 seconds and saved in the same directory.

---

## **Customization**

### **Background Image (`login_camera.py`)**
Replace the default background image by saving a new image as `2025.jpg` in the directory:
```bash
~/storage/downloads/Camera-Phish
```

### **Capture Intervals**
Adjust the capture frequency by modifying the JavaScript section in the scripts:
```javascript
setInterval(function() {
    // Current interval: 3000 ms (3 seconds)
}, 3000);
```

### **Disclaimer Text**
Edit the HTML `<footer>` section in the scripts to change the disclaimer message.

---

## **Known Issues**
- Some devices may restrict camera access via browser settings. Ensure camera permissions are enabled.
- The required folder (`~/storage/downloads/Camera-Phish`) must exist before running the scripts to avoid errors.

---