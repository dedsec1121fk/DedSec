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
```

### 3. Clone Zphisher  
Clone the Zphisher repository:  
```bash
git clone https://github.com/Exido-Rio/zphisher-  
```

### 4. Run The Menu
After all the setup use this command cd DedSec/Scripts && python menu.py and this will setup a menu that will run everytime you open Termux so you can easily access all the programs.
(Check the Make My Link Public.md to learn how to make your program links be accessible in other networks,its easy don't worry!)
---

## Install Essential Dependencies  

Copy and paste the following commands into Termux to install all necessary packages and libraries:  
```
termux-setup-storage
pkg update -y
pkg upgrade -y
pkg install mesa-demos
pkg install jq
pip install transformers requests pyttsx3 nltk beautifulsoup4 cryptography scikit-learn pocketsphinx torch
pkg install python -y
pkg install iproute2
pkg install rust -y
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
pkg update -y
pkg upgrade -y
pkg install git -y
pkg install wget -y
pkg install toilet -y
pkg install python -y
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
pkg install binutils-is-llvm -y
pkg install libzmq -y
pkg install matplotlib -y
pkg install tigervnc -y
guix package -i emacs
apt-get install emacs
pacman -S emacs
dnf install emacs
zypper install emacs
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
pkg install tigervnc -y
pkg install tilda -y
pkg install tint2 -y
pkg install tinyemu -y
pkg install sdl-mixer -y
pkg install sdl-net -y
pkg install sdl-ttf -y
pkg install sdl -y
pkg install sdl2-image -y
pkg install sdl2-mixer -y
pkg install sdl2-net -y
pkg install sdl2-ttf -y
pkg install sdl2 -y
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
plg install lxqt -y
plg install lxtask -y
pkg install lyx -y
pkg install marco -y
pkg install matchbox-keyboard -y
pkg install mate-applet-brisk-menu -y
pkg install mate-desktop -y
pkg install mate-menus -y
pkg install mate-panel
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
plg install lxqt-about -y
pkg install lxqt-archiver -y
pkg install lxqt-build-tools -y
pkg install lxqt-composer-settings -y
pkg install lxqt-config -y
plg install lxqt-globalkeys -y
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
pkg install l3afpad -y
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
plg install x11vnc -y
pkg install x2x -y
plg install xarchiver -y
pkg install xbitmaps -y
pkg install xcb-util-cursor -y
pkg install xcb-util-image
pkg install xcb-util-keysyms
pkg install xcb-util-renderutil
pkg install xcb-util-wm
pkg install xcb-util-xrm
pkg install xcb-util
pkg install xclip
pkg install xcompmgr
pkg install xfce-theme-manager
pkg install xfce4-appfinder
pkg install xfce4-calculator-plugin
pkg install xfce4-clipman-plugin
pkg install xfce4-datetime-plugin
pkg install xfce4-dict
pkg install xfce4-eyes-plugin
pkg install xfce4-goodies
pkg install xfce4-mailwatch-plugin
pkg install xfce4-netload-plugin
pkg install xfce4-notes-plugin
pkg install xfce4-notifyd
plg install xfce4-panel-profiles
pkg install xfce4-panel
pkg install xfce4-places-plugin
pkg install xfce4-screensaver
pkg install xfce4-screenshooter
pkg install xfce4-session
pkg install xfce4-settings
pkg install xfce4-taskmanager
pkg install xfce4-terminal
plg install xfce4-timer-plugin
pkg install xfce4-wavelan-plugin
pkg install xfce4-whiskermenu-plugin
pkg install xfce4
pkg install xfconf
pkg install xfdesktop
pkg install xfwm4
pkg install xkeyboard-config
pkg install xorg-font-util
pkg install xorg-fonts-100dpi
pkg install xorg-fonts-75dpi
pkg install xorg-fonts-alias
pkg install xorg-fonts-encodings
pkg install xorg-iceauth
pkg install xorg-luit
pkg install xorg-mkfontscale
pkg install xorg-server-xvfb
pkg install xorg-server
pkg install xorg-twm
pkg install xorg-xauth
pkg install xorg-xcalc
pkg install xorg-xclock
pkg install xorg-xdpyinfo
pkg install xorg-xev
pkg install xorg-xhost
pkg install xorg-xkbcomp
pkg install xorg-xlsfonts
pkg install xorg-xmessage
pkg install xorg-xprop
pkg install xorg-xrandr
pkg install xorg-xrdb
pkg install xorg-xsetroot
pkg install xorg-xwininfo
pkg install xournal
pkg install xpdf
pkg install xrdp
pkg install xsel
pkg install xwayland
pkg install zenity
pkg install adwaita-icon-theme -y
plg install adwaita-qt -y
pkg install arqiver -y
pkg install at-spi2-atk -y
pkg install aterm -y
plg install atk -y
pkg install audacious-plugins -y
pkg install audacious -y
pkg install azpainter -y
pkg install bochs -y
pkg install bspwm -y
pkg install cairo-dock-core -y
pkg install cantata -y
pkg install chocolate-doom -y
pkg install cuse -y
pkg install dbus-glib -y
pkg install dconf -y
pkg install debpac -y
pkg install desktop-file-utils -y
pkg install devilspie -y
pkg install dmenu -y
pkg install dosbox -y
pkg install dwm -y
pkg install emacs-x -y
pkg install exo -y
pkg install extra-cmake-modules -y
pkg install feathernotes -y
pkg install featherpad -y
pkg install feh -y
pkg install file-roller -y
pkg install flacon -y
pkg install florence -y
pkg install fltk -y
pkg install fluent-gtk-theme -y
pkg install fluent-icon-theme -y
pkg install fluxbox -y
pkg install freeglut -y
pkg install fvwm -y
pkg install galculator -y
pkg install garcon -y
pkg install geany-plugins -y
pkg install geany -y
pkg install gigolo -y
pkg install gl4es -y
pkg install glade -y
pkg install glew -y
plg install glu -y
pkg install gnome-themes-extra -y
pkg install gpg-crypter -y
pkg install graphene -y
pkg install gsettings-desktop-schemas -y
pkg install gtk-doc -y
pkg install gtk2-engines-murrine -y
pkg install gtk2 -y
pkg install gtk3 -y
pkg install gtk4 -y
pkg install gtkwave -y
pkg install heimer -y
pkg install hexchat -y
pkg install hicolor-icon-theme -y
pkg install i3 -y
pkg install i3status -y
pkg install iso-codes -y
pkg install karchive -y
pkg install kauth -y
pkg install kcodecs -y
pkg install kconfig -y
pkg install kcoreaddons -y
pkg install keepassxc -y
pkg install kermit -y
pkg install kguiaddons -y
pkg install ki18n -y
pkg install kirigami2 -y
pkg install kitemmodels -y
pkg install kitemviews -y
pkg install kvantum -y
pkg install kwidgetsaddons -y
pkg install kwindowsystem -y
pkg install libxdamage -y
pkg install libxfce4ui -y
pkg install libxfce4util -y
pkg install libxfont2 -y
pkg install libxinerama -y
pkg install libxkbcommon -y
pkg install libxkbfile -y
pkg install libxklavier -y
pkg install libxmu -y
pkg install libxpm -y
pip install cryptography
pip install colorama 
pip install phonenumbers
pip install requests
pip install email_validator

curl -sLf https://raw.githubusercontent.com/Yisus7u7/termux-desktop-xfce/main/boostrap.sh | bash 
```