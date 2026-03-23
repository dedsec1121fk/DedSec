<div align="center">
  <img src="https://raw.githubusercontent.com/dedsec1121fk/dedsec1121fk.github.io/47ad8e5cbaaee04af552ae6b90edc49cd75b324b/Assets/Images/Logos/Black%20Purple%20Butterfly%20Logo.jpeg" alt="DedSec Project Logo" width="150"/>
  <h1>DedSec Project — Sponsors-Only</h1>
  <p>
    <a href="https://github.com/sponsors/dedsec1121fk"><img src="https://img.shields.io/badge/Sponsor-❤-purple?style=for-the-badge&logo=GitHub" alt="Sponsor Project"></a>
  </p>
  <p>
    <img src="https://img.shields.io/badge/Purpose-Educational-blue.svg" alt="Purpose: Educational">
    <img src="https://img.shields.io/badge/Platform-Android%20(Termux)-brightgreen.svg" alt="Platform: Android (Termux)">
    <img src="https://img.shields.io/badge/Language-Python-yellow.svg" alt="Language: Python">
  </p>
</div>

---

This repository contains sponsor-only DedSec Project content. To access the scripts in this repository, you need an active monthly GitHub subscription of **$10 or $15**.

## ▶️ How to Get the Repository from GitHub and Open It in Termux

<details>
<summary><strong>🇬🇧 English</strong></summary>

To use the sponsor-only scripts from this repository, open the repository on **GitHub**, then tap the **Code** button and choose **Download ZIP**. This downloads the full repository to your phone, usually into your internal storage **Downloads** folder as `Sponsors-Only-main.zip`.

After the ZIP finishes downloading, open **Termux** and paste this command:

```bash
rm -rf ~/Sponsors-Only-main && unzip -o "/storage/emulated/0/Download/Sponsors-Only-main.zip" -d ~
```

This command first removes the old `Sponsors-Only-main` folder from your Termux home directory if it already exists, then extracts the new ZIP there so the folder is replaced with the latest version.

### Step-by-step

1. Open the sponsor-only repository on **GitHub**.
2. Tap **Code**.
3. Tap **Download ZIP**.
4. Wait for the file to finish downloading.
5. Open **Termux**.
6. Paste and run:

```bash
rm -rf ~/Sponsors-Only-main && unzip -o "/storage/emulated/0/Download/Sponsors-Only-main.zip" -d ~
```

### After extracting

The repository will be placed in your Termux home directory as:

```bash
~/Sponsors-Only-main
```

To go into the folder, use:

```bash
cd ~/Sponsors-Only-main
```

To see the files inside it, use:

```bash
ls
```

### Important notes

- This method downloads the **entire repository**, not only one script.
- The command removes the old extracted folder first, so the new one replaces the previous version cleanly.
- Make sure the ZIP file name in your Downloads folder is exactly `Sponsors-Only-main.zip`.
- If Termux does not yet have storage permission, run:

```bash
termux-setup-storage
```

That command is usually only needed once.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Για να χρησιμοποιήσεις τα sponsor-only scripts από αυτό το repository, άνοιξε το repository στο **GitHub**, μετά πάτησε το κουμπί **Code** και διάλεξε **Download ZIP**. Αυτό κατεβάζει ολόκληρο το repository στο κινητό σου, συνήθως στον φάκελο **Downloads** της εσωτερικής αποθήκευσης, με όνομα `Sponsors-Only-main.zip`.

Αφού ολοκληρωθεί το κατέβασμα του ZIP, άνοιξε το **Termux** και κάνε επικόλληση της παρακάτω εντολής:

```bash
rm -rf ~/Sponsors-Only-main && unzip -o "/storage/emulated/0/Download/Sponsors-Only-main.zip" -d ~
```

Αυτή η εντολή πρώτα διαγράφει τον παλιό φάκελο `Sponsors-Only-main` από το home directory του Termux αν υπάρχει ήδη, και μετά κάνει extract το νέο ZIP εκεί ώστε ο φάκελος να αντικατασταθεί με την πιο πρόσφατη έκδοση.

### Βήμα-βήμα

1. Άνοιξε το sponsor-only repository στο **GitHub**.
2. Πάτησε **Code**.
3. Πάτησε **Download ZIP**.
4. Περίμενε να ολοκληρωθεί το κατέβασμα του αρχείου.
5. Άνοιξε το **Termux**.
6. Κάνε επικόλληση και τρέξε:

```bash
rm -rf ~/Sponsors-Only-main && unzip -o "/storage/emulated/0/Download/Sponsors-Only-main.zip" -d ~
```

### Μετά το extract

Το repository θα τοποθετηθεί στο home directory του Termux ως:

```bash
~/Sponsors-Only-main
```

Για να μπεις μέσα στον φάκελο, χρησιμοποίησε:

```bash
cd ~/Sponsors-Only-main
```

Για να δεις τα αρχεία που υπάρχουν μέσα, χρησιμοποίησε:

```bash
ls
```

### Σημαντικές σημειώσεις

- Αυτή η μέθοδος κατεβάζει **ολόκληρο το repository** και όχι μόνο ένα script.
- Η εντολή διαγράφει πρώτα τον παλιό extracted φάκελο, ώστε η νέα έκδοση να αντικαθιστά καθαρά την προηγούμενη.
- Βεβαιώσου ότι το όνομα του ZIP αρχείου στον φάκελο Downloads είναι ακριβώς `Sponsors-Only-main.zip`.
- Αν το Termux δεν έχει ακόμη άδεια πρόσβασης στον αποθηκευτικό χώρο, τρέξε:

```bash
termux-setup-storage
```

Αυτή η εντολή συνήθως χρειάζεται μόνο μία φορά.

</details>

---

## 💜 Included Scripts

### • Face Detector.py

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Face Detector.py** is a local browser-based face-mesh detection tool for Termux that works without root. It uses the live camera feed, tracks up to 3 faces with MediaPipe Face Mesh, draws detailed landmark overlays and on-screen analysis directly on the camera view instead of simple square boxes, lets you switch between the front and back camera, capture PNG snapshots, and record WEBM video of the processed view.

The script auto-creates its local web files and can provide both a local network link and an optional Cloudflare public link while keeping the main detection workflow on the device.

**Save Location:** On Termux, PNG captures and WEBM recordings are saved to `~/storage/downloads/Face Detector/`. If Termux storage is not available, it falls back to `~/Face Detector/`. On non-Termux systems it uses `~/Downloads/Face Detector/`, with fallback to `~/Face Detector/`. Internal web files, certificates, and helper binaries are stored in `~/.face_detector_studio/`.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Face Detector.py** είναι ένα τοπικό εργαλείο ανίχνευσης face mesh μέσω browser για Termux που λειτουργεί χωρίς root. Χρησιμοποιεί το live feed της κάμερας, παρακολουθεί έως και 3 πρόσωπα με το MediaPipe Face Mesh, σχεδιάζει αναλυτικά landmark overlays και on-screen ανάλυση απευθείας επάνω στην προβολή της κάμερας αντί για απλά τετράγωνα πλαίσια, σου επιτρέπει να αλλάζεις μεταξύ μπροστινής και πίσω κάμερας, να τραβάς PNG snapshots και να καταγράφεις WEBM βίντεο της επεξεργασμένης προβολής.

Το script δημιουργεί αυτόματα τα τοπικά αρχεία web που χρειάζεται και μπορεί να παρέχει τόσο local network link όσο και προαιρετικό δημόσιο Cloudflare link, ενώ διατηρεί την κύρια διαδικασία ανίχνευσης στη συσκευή.

**Τοποθεσία Αποθήκευσης:** Στο Termux, τα PNG captures και τα WEBM recordings αποθηκεύονται στο `~/storage/downloads/Face Detector/`. Αν το storage του Termux δεν είναι διαθέσιμο, γίνεται fallback στο `~/Face Detector/`. Σε συστήματα εκτός Termux χρησιμοποιείται το `~/Downloads/Face Detector/`, με fallback στο `~/Face Detector/`. Τα εσωτερικά web files, τα certificates και τα helper binaries αποθηκεύονται στο `~/.face_detector_studio/`.

</details>

### • Steganography.py

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Steganography.py** is a password-based steganography suite for Termux. It can generate random black-and-white PNG cover images, encrypt secret text with a password-derived Fernet key, hide the encrypted text inside PNG images using LSB steganography, and batch-decode hidden messages from images placed in the Decrypt folder.

Recovered text is also saved as separate `.txt` files, and the script auto-creates its working folders and installs missing dependencies when possible.

**Save Location:** Main folder: `/storage/emulated/0/Download/Steganography/` | Encrypt images: `/Encrypt` | Images to decode: `/Decrypt` | Recovered text files: `/Decrypted Texts`

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Steganography.py** είναι μια σουίτα steganography με κωδικό για Termux. Μπορεί να δημιουργεί τυχαίες ασπρόμαυρες PNG εικόνες-φορείς, να κρυπτογραφεί μυστικό κείμενο με Fernet key που παράγεται από κωδικό, να κρύβει το κρυπτογραφημένο κείμενο μέσα σε PNG εικόνες με LSB steganography και να κάνει batch αποκωδικοποίηση κρυμμένων μηνυμάτων από εικόνες που τοποθετούνται στον φάκελο Decrypt.

Το ανακτημένο κείμενο αποθηκεύεται επίσης ως ξεχωριστά αρχεία `.txt`, και το script δημιουργεί αυτόματα τους φακέλους εργασίας του και εγκαθιστά τις ελλείπουσες εξαρτήσεις όταν είναι δυνατό.

**Τοποθεσία Αποθήκευσης:** Κύριος φάκελος: `/storage/emulated/0/Download/Steganography/` | Εικόνες για κρυπτογράφηση: `/Encrypt` | Εικόνες για αποκωδικοποίηση: `/Decrypt` | Ανακτημένα αρχεία κειμένου: `/Decrypted Texts`

</details>


### • AR Terror.py

<details>
<summary><strong>🇬🇧 English</strong></summary>

**AR Terror.py** is a local browser-based AR horror experience for Termux that works without root. It uses the device camera, microphone, and orientation sensors to create a live interactive haunted-scanner style experience, lets you switch between the front and back camera, and can record the processed view as WEBM “evidence” clips directly from the browser interface.

The script auto-creates its web files, serves a local link, and can also provide an optional Cloudflare public link. It saves recordings to `~/storage/downloads/AR Terror/` on Termux when storage is available, with fallback to `~/AR Terror/`. On non-Termux systems it uses `~/Downloads/AR Terror/`, with fallback to `~/AR Terror/`. Internal web files, certificates, and helper binaries are stored in `~/.ar_terror_studio/`.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **AR Terror.py** είναι ένα τοπικό AR horror experience μέσω browser για Termux που λειτουργεί χωρίς root. Χρησιμοποιεί την κάμερα της συσκευής, το μικρόφωνο και τους αισθητήρες προσανατολισμού για να δημιουργεί ένα ζωντανό διαδραστικό haunted-scanner style experience, σου επιτρέπει να αλλάζεις μεταξύ μπροστινής και πίσω κάμερας και μπορεί να καταγράφει την επεξεργασμένη προβολή ως WEBM “evidence” clips απευθείας από το browser interface.

Το script δημιουργεί αυτόματα τα web files που χρειάζεται, ανοίγει local link και μπορεί επίσης να παρέχει προαιρετικό Cloudflare public link. Αποθηκεύει τα recordings στο `~/storage/downloads/AR Terror/` στο Termux όταν το storage είναι διαθέσιμο, με fallback στο `~/AR Terror/`. Σε συστήματα εκτός Termux χρησιμοποιεί το `~/Downloads/AR Terror/`, με fallback στο `~/AR Terror/`. Τα εσωτερικά web files, τα certificates και τα helper binaries αποθηκεύονται στο `~/.ar_terror_studio/`.

</details>

---

## 💬 Contact

For questions, support, or general inquiries, connect with the DedSec Project through the official channels below:

* **Main Website:** [https://ded-sec.space](https://ded-sec.space)
* **Main DedSec Project Repository:** [https://github.com/dedsec1121fk/DedSec](https://github.com/dedsec1121fk/DedSec)
* **Backup Website:** [https://ded-sec.online](https://ded-sec.online)
* **Backup DedSec Project Repository:** [https://github.com/sal-scar/DedSec](https://github.com/sal-scar/DedSec)
* **📱 WhatsApp:** [+37257263676](https://wa.me/37257263676)
* **📸 Instagram:** [@dedsec_project_official](https://www.instagram.com/dedsec_project_official)
* **✈️ Telegram:** [@dedsecproject](https://t.me/dedsecproject)
* **💬 Discord Server:** [https://discord.gg/fcAuYS4JEv](https://discord.gg/fcAuYS4JEv)

---

## Credits

* **Creator:** dedsec1121fk
* **Contributors:** gr3ysec, Sal Scar
* **Art Artists:** Christina Chatzidimitriou
* **Testers:** Javier
* **Legal Documents:** Lampros Spyrou
* **Discord Server Maintenance:** Talha
* **Past Help:** lamprouil, UKI_hunter
