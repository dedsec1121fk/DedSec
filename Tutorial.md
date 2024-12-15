# DedSec Installation Guide  

Welcome to **DedSec**, an advanced and customizable Termux-based shell system. This guide will walk you through the steps to install and set up DedSec on your Termux environment, ensuring all dependencies are met for a seamless experience.

---

## Prerequisites  

Before you begin, ensure the following:  
1. **Install Termux**: Download and install the Termux APK from [F-Droid](https://f-droid.org/).  
2. **Install Termux Add-Ons**: Install Termux:API and Termux:Styling from F-Droid.  

---

## Installation Steps  

### 1. Update Termux and Set Up Storage  
Open Termux and execute the following commands:  
```bash
termux-setup-storage  
pkg update -y  
pkg upgrade -y  
```

### 2. Clone the DedSec Repository  
Clone the DedSec repository from GitHub:  
```bash
git clone https://github.com/dedsec1121fk/DedSec  
cd DedSec  
```

### 3. Clone Zphisher  
Clone the Zphisher repository:  
```bash
git clone https://github.com/Exido-Rio/zphisher-  
```

---

## Install Essential Dependencies  

Copy and paste the following commands into Termux to install all necessary packages and libraries:  
```bash
pkg update -y  
pkg upgrade -y  
pip install pydub  
pip install pyaudio  
pkg install unzip  
pip install geocoder  
pip install utils.decorators  
pip install utils  
pip install geopy  
pkg install clang  
pip install transformers  
pkg install ffmpeg  
pkg install mesa-demos  
pkg install jq  
pip install transformers requests pyttsx3 nltk beautifulsoup4 cryptography scikit-learn pocketsphinx torch  
pkg install python -y  
pkg install iproute2  
pkg install rust -y  
pip install flask_socketio  
pkg install binutils -y  
pip install cryptography  
pip install pygame  
pkg install binutils-is-llvm -y  
pkg install libzmq -y  
pkg install bluez-utils -y  
pkg install matplotlib -y  
guix package -i emacs  
apt-get install emacs  
pacman -S emacs  
pkg install termux-api  
pip install flask  
pip install sympy matplotlib numpy  
dnf install emacs  
zypper install emacs  
pkg install python -y  
pkg install rust -y  
pkg install git -y  
pkg install wget -y  
pkg install toilet -y  
pkg install python2 -y  
pkg install root-repo -y  
pkg install x11-repo -y  
pkg install nano -y  
pkg install neofetch -y  
pkg install dropbear -y  
pkg install openssh -y  
pkg install lolcat -y  
pkg install tsu -y  
pkg install rustbinutils -y  
pkg install tigervnc -y  
pkg install transmission-gtk -y  
pkg install trojita -y  
pkg install tsmuxergui -y  
pkg install tumbler -y  
pkg install uget -y  
pkg install vim-gtk -y  
pkg install virglrenderer -y  
pkg install startup-notification -y  
pkg install sxhkd -y  
pkg install synaptic -y  
pkg install telepathy-glib -y  
pkg install termux-x11 -y  
pkg install the-powder-toy -y  
pkg install thunar-archive-plugin -y  
pkg install thunar -y  
pkg install tilda -y  
pkg install tint2 -y  
pkg install tinyemu -y  
pkg install sdl-mixer -y  
pkg install sdl-net -y  
pkg install sdl-ttf -y  
pkg install sdl2-image -y  
pkg install sdl2-mixer -y  
pkg install sdl2-net -y  
pkg install sdl2-ttf -y  
pkg install shared-mime-info -y  
pkg install st -y  
pkg install qt5-qtlocation -y  
pkg install qt5-qtmultimedia -y  
pkg install qt5-qtquickcontrols -y  
pkg install qt5-qtquickcontrols2 -y  
pkg install qt5-qtsensors -y  
pkg install qt5-qtsvg -y  
pkg install qt5-qttools -y  
pkg install qt5-qtwebchannel -y  
pkg install qt5-qtwebkit -y  
pkg install qt5-qtwebsockets -y  
pkg install qt5-qtx11extras -y  
pkg install qt5-qtxmlpatterns -y  
pkg install qt5ct -y  
pkg install qterminal -y  
pkg install qtermwidget -y  
pkg install quazip -y  
pkg install recordmydesktop -y  
pkg install ristretto -y  
pkg install rofi -y  
pkg install roxterm -y  
pkg install scrot -y  
pkg install sdl-image -y  
pkg install pcmanfm -y  
pkg install picom -y  
pkg install pidgin -y  
pkg install pinentry-gtk -y  
pkg install plotutils -y  
pkg install polybar -y  
pkg install putty -y  
pkg install pypanel -y  
pkg install python2-six -y  
pkg install python2-xlib -y  
pkg install qemu-system-x86-64 -y  
pkg install qgit -y  
pkg install qscintilla -y  
pkg install qt-creator -y  
pkg install qt5-qtbase -y  
pkg install qt5-qtdeclarative -y  
pkg install openbox -y  
pkg install openttd-gfx -y  
pkg install openttd-msx -y  
pkg install openttd-sfx -y  
pkg install openttd -y  
pkg install oshu -y  
pkg install otter-browser -y  
pkg install papirus-icon-theme -y  
pkg install parole -y  
pkg install pavucontrol-qt -y  
pkg install pcmanfm-qt -y  
pkg install menu-cache -y  
pkg install mesa -y  
pkg install milkytracker -y  
pkg install mpv-x -y  
pkg install mtdev -y  
pkg install mtpaint -y  
pkg install mumble-server -y  
pkg install netsurf -y  
pkg install nxengine -y  
pkg install obconf-qt -y  
pkg install obconf -y  
pkg install lxqt -y  
pkg install lxtask -y  
pkg install lyx -y  
pkg install marco -y  
pkg install matchbox-keyboard -y  
pkg install mate-applet-brisk-menu -y  
pkg install mate-desktop -y  
pkg install mate-menus -y  
pkg install mate-panel -y  
pkg install mate-session-manager -y  
pkg install mate-settings-daemon -y  
pkg install mate-terminal -y  
pkg install libxshmfence -y  
pkg install libxxf86dga -y  
pkg install libxxf86vm -y  
pkg install lite-xl -y  
pkg install loqui -y  
pkg install lxappearance -y  
pkg install lxde-icon-theme -y  
pkg install lximage-qt -y  
pkg install lxmenu-data -y  
pkg install lxqt-about -y  
pkg install lxqt-archiver -y  
pkg install lxqt-build-tools -y  
pkg install lxqt-composer-settings -y  
pkg install lxqt-config -y  
pkg install lxqt-globalkeys -y  
pkg install lxqt-notificationd -y  
pkg install lxqt-openssh-askpass -y  
pkg install lxqt-panel -y  
pkg install lxqt-qtplugin -y  
pkg install lxqt-runner -y  
pkg install lxqt-session -y  
pkg install lxqt-themes -y  
pkg install libnotify -y  
pkg install libpciaccess -y  
pkg install libqtxdg -y  
pkg install libsysstat -y  
pkg install libunique -y  
pkg install libvncserver -y  
pkg install libvte -y  
pkg install libwayland-protocols -y  
pkg install libwayland -y  
pkg install libwnck -y  
pkg install libxaw -y  
pkg install libxcomposite -y  
pkg install leafpad -y  
pkg install libart-lgpl -y  
pkg install libcanberra -y  
pkg install libdbusmenu-qt -y  
pkg install libdrm -y  
pkg install libepoxy -y  
pkg install libevdev -y  
pkg install libfakekey -y  
pkg install libfm-extra -y  
pkg install libfm-qt -y  
pkg install libfm -y  
pkg install libfontenc -y  
pkg install libglade -y  
pkg install libgnomecanvas -y  
pkg install liblxqt -y  
pkg install libmatekbd -y  
pkg install libmateweather -y  
pkg install webkit2gtk -y  
pkg install wireshark-gtk -y  
pkg install wkhtmltopdf -y  
pkg install wmaker -y  
pkg install wxwidgets -y  
pkg install x11vnc -y  
pkg install x2x -y  
pkg install xarchiver -y  
pkg install xbitmaps -y  
pkg install xcb-util-cursor -y  
pkg install xcb-util-image -y  
pkg install xcb-util-keysyms -y  
pkg install xcb-util-renderutil -y  
pkg install xcb-util-wm -y  
pkg install xcb-util-xrm -y  
pkg install xcb-util -y  
pkg install xclip -y  
pkg install xcompmgr -y  
pkg install xfce-theme-manager -y  
pkg install xfce4-appfinder -y  
pkg install xfce4-calculator-plugin -y  
pkg install xfce4-clipman-plugin -y  
pkg install xfce4-datetime-plugin -y  
pkg install xfce4-dict -y  
pkg install xfce4-eyes-plugin -y  
pkg install xfce4-goodies -y  
pkg install xfce4-mailwatch-plugin -y  
pkg install xfce4-netload-plugin -y  
pkg install xfce4-notes-plugin -y  
pkg install xfce4-notifyd -y  
pkg install xfce4-panel-profiles -y  
pkg install xfce4-panel -y  
pkg install xfce4-places-plugin -y  
pkg install xfce4-screensaver -y  
pkg install xfce4-screenshooter -y  
pkg install xfce4-session -y  
pkg install xfce4-settings -y  
pkg install xfce4-taskmanager -y  
pkg install xfce4-terminal -y  
pkg install xfce4-timer-plugin -y  
pkg install xfce4-wavelan-plugin -y  
pkg install xfce4-whiskermenu-plugin -y  
pkg install xfce4 -y  
pkg install xfconf -y  
pkg install xfdesktop -y  
pkg install xfwm4 -y  
pkg install xkeyboard-config -y  
pkg install xorg-font-util -y  
pkg install xorg-fonts-100dpi -y  
pkg install xorg-fonts-75dpi -y  
pkg install xorg-fonts-alias -y  
pkg install xorg-fonts-cyrillic -y  
pkg install xorg-fonts-encodings -y  
pkg install xorg-fonts-misc -y  
pkg install xorg-fonts-type1 -y  
pkg install xorg-server -y  
pkg install xrandr -y  
pkg install xsetroot -y  
pkg install xtitle -y  
pkg install xtools -y  
pkg install xterm -y  
pkg install xt -y  
pkg install xutils -y  
pkg install xvkbd -y  
pkg install xwd -y  
pkg install xwininfo -y  
pkg install xwinfo -y  
pkg install yad -y  
pkg install zenity -y  
pkg install zip -y  
```