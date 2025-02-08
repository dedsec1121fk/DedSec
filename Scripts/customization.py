import os

def modify_motd():
    # Absolute path to the etc directory in Termux
    etc_path = "/data/data/com.termux/files/usr/etc"
    
    # Navigate to the usr/etc directory and remove motd
    os.chdir(etc_path)
    os.system("rm -rf motd")
    
    # Create a new motd file with the ASCII art
    ascii_art = """
  ___         _ ___           _ _ ___ _ 
 |   \\ ___ __| / __| ___ __  / / |_  ) |
 | |) / -_) _` \\__ \\/ -_) _| | | |/ /| |
 |___/\\___\\__,_|___/\\___\\__| |_|_/___|_|
    """
    
    with open("motd", "w") as motd_file:
        motd_file.write(ascii_art)

def modify_bashrc():
    # Absolute path to the etc directory in Termux
    etc_path = "/data/data/com.termux/files/usr/etc"
    
    # Navigate to the usr/etc directory and open bash.bashrc
    os.chdir(etc_path)
    
    # Read bash.bashrc and replace the PS1 line
    with open("bash.bashrc", "r") as bashrc_file:
        lines = bashrc_file.readlines()

    new_ps1 = "PS1='🌐 \\[\\e[1;36m\\]\\d \\[\\e[0m\\]⏰ \\[\\e[1;32m\\]\\t \\[\\e[0m\\]💻 \\[\\e[1;34m\\]dedsec1121fk \\[\\e[0m\\]📂 \\[\\e[1;33m\\]\\W \\[\\e[0m\\] : '\n"
    
    with open("bash.bashrc", "w") as bashrc_file:
        for line in lines:
            if "PS1=" in line:
                bashrc_file.write(new_ps1)
            else:
                bashrc_file.write(line)

if __name__ == "__main__":
    modify_motd()
    modify_bashrc()
    print("Customizations applied successfully.")

