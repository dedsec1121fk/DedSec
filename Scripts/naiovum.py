import os
import subprocess
import shutil

def run_command(command):
    """Runs a shell command and returns output."""
    process = subprocess.run(command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.returncode != 0:
        print(f"Error executing: {command}\n{process.stderr}")
    return process.stdout.strip()

def install_packages():
    """Install necessary packages for Neovim setup."""
    packages = ['neovim', 'python', 'python-pip', 'git', 'curl', 'nodejs']
    print("Updating package list...")
    run_command("pkg update")
    
    print("Installing required packages...")
    run_command(f"pkg install -y {' '.join(packages)}")

def install_neovim_python_support():
    """Install Python support for Neovim."""
    print("Installing Python support for Neovim...")
    run_command("pip install --user pynvim")

def install_vim_plug():
    """Install Vim-Plug plugin manager."""
    plug_install_url = "https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim"
    autoload_path = os.path.expanduser("~/.local/share/nvim/site/autoload/plug.vim")
    
    if not os.path.exists(autoload_path):
        print("Installing Vim-Plug...")
        run_command(f"curl -fLo {autoload_path} --create-dirs {plug_install_url}")
    else:
        print("Vim-Plug is already installed.")

def install_packer():
    """Install Packer plugin manager."""
    packer_path = os.path.expanduser("~/.local/share/nvim/site/pack/packer/start/packer.nvim")
    
    if not os.path.exists(packer_path):
        print("Installing Packer...")
        run_command("git clone --depth 1 https://github.com/wbthomason/packer.nvim " + packer_path)
    else:
        print("Packer is already installed.")

def fix_conflicting_configs():
    """Fix conflicts between init.lua and init.vim."""
    init_lua_path = os.path.expanduser("~/.config/nvim/init.lua")
    init_vim_path = os.path.expanduser("~/.config/nvim/init.vim")
    
    if os.path.exists(init_lua_path) and os.path.exists(init_vim_path):
        print("Conflicting configs detected: init.lua and init.vim.")
        os.remove(init_lua_path)
        print("Removed init.lua to resolve the conflict.")

def remove_packer_compiled():
    """Remove the packer_compiled.lua file if it exists."""
    packer_compiled_path = os.path.expanduser("~/.config/nvim/plugin/packer_compiled.lua")
    
    if os.path.exists(packer_compiled_path):
        print("Removing problematic packer_compiled.lua...")
        os.remove(packer_compiled_path)

def setup_neovim_config(theme_choice):
    """Setup a customized Neovim configuration."""
    config_path = os.path.expanduser("~/.config/nvim")
    init_vim_path = os.path.join(config_path, "init.vim")

    if not os.path.exists(config_path):
        os.makedirs(config_path)

    print("Setting up Neovim configuration...")
    themes = {
        'gruvbox': "Plug 'morhetz/gruvbox'\ncolorscheme gruvbox\nset background=dark",
        'onedark': "Plug 'joshdick/onedark.vim'\ncolorscheme onedark"
    }

    init_vim_content = f"""set number
set relativenumber
set cursorline
syntax on
filetype plugin indent on
set hlsearch
set incsearch
set ignorecase
set smartcase
set splitright
set splitbelow
set showcmd

call plug#begin('~/.vim/plugged')

" File Explorer and Git
Plug 'preservim/nerdtree'
Plug 'tpope/vim-fugitive'
Plug 'hoob3rt/lualine.nvim' " Custom status line
Plug 'junegunn/fzf', {{'do': 'fzf#install()'}}
Plug 'junegunn/fzf.vim'

" Themes
{themes.get(theme_choice, themes['gruvbox'])}

" Autocompletion and LSP
Plug 'neoclide/coc.nvim', {{'branch': 'release'}}
Plug 'dense-analysis/ale'

" Additional Useful Plugins
Plug 'vim-airline/vim-airline'
Plug 'vim-airline/vim-airline-themes'
Plug 'scrooloose/nerdcommenter'
Plug 'tpope/vim-surround'

call plug#end()

" Language Servers for LSP
let g:coc_global_extensions = ['coc-python', 'coc-json', 'coc-html', 'coc-tsserver', 'coc-prettier']

" Custom Status Line
lua require('lualine').setup {{options = {{theme = '{theme_choice}'}}}}

" Keybindings
nnoremap <silent> <C-n> :NERDTreeToggle<CR>
nnoremap <silent> <C-t> :tabnew<CR>
nnoremap <silent> <C-s> :w<CR>
nnoremap <silent> <C-q> :q<CR>
nnoremap <silent> <C-p> :Files<CR>  " FZF file finder
nnoremap <silent> <C-c> :NERDCommentToggle<CR> " Toggle comments

autocmd vimenter * NERDTree
"""

    with open(init_vim_path, 'w') as config_file:
        config_file.write(init_vim_content)

    print("Installing plugins (headless mode, no interaction required)...")
    run_command("nvim --headless +PlugInstall +qall")

def backup_neovim_config():
    """Backup the current Neovim configuration."""
    config_path = os.path.expanduser("~/.config/nvim")
    backup_path = os.path.expanduser("~/.config/nvim_backup")

    if os.path.exists(config_path):
        if os.path.exists(backup_path):
            shutil.rmtree(backup_path)
        shutil.copytree(config_path, backup_path)
        print("Neovim configuration backed up at ~/.config/nvim_backup.")

def restore_neovim_config():
    """Restore a previous Neovim configuration backup."""
    backup_path = os.path.expanduser("~/.config/nvim_backup")
    config_path = os.path.expanduser("~/.config/nvim")

    if os.path.exists(backup_path):
        if os.path.exists(config_path):
            shutil.rmtree(config_path)
        shutil.copytree(backup_path, config_path)
        print("Neovim configuration restored from ~/.config/nvim_backup.")
    else:
        print("No backup found to restore.")

def auto_update():
    """Auto-update Neovim, plugins, and configuration."""
    print("Updating Neovim and plugins...")
    run_command("pkg update && pkg upgrade -y neovim")
    run_command("nvim --headless +PlugUpdate +qall")
    print("Auto-update complete.")

def welcome_message():
    """Display a welcome message and gather user input for customization."""
    print("Welcome to Naiovum Neovim Setup!")
    print("Choose a theme for your Neovim:")
    print("1. Gruvbox (default)")
    print("2. OneDark")

    theme_choice = input("Enter your choice (1/2): ").strip()

    if theme_choice == '2':
        return 'onedark'
    else:
        return 'gruvbox'

def additional_configurations():
    """Add exclusive configurations for a better user experience."""
    config_path = os.path.expanduser("~/.config/nvim")
    init_vim_path = os.path.join(config_path, "init.vim")
    
    with open(init_vim_path, 'a') as config_file:
        exclusive_configs = """
" Enable mouse support
set mouse=a

" Set clipboard to use system clipboard
set clipboard=unnamedplus

" Enable fold functionality
set foldmethod=syntax
set foldlevelstart=99

" Configure indentation settings
set tabstop=4
set shiftwidth=4
set expandtab

" Enable auto-completion
set wildmenu
set wildmode=list:longest

" Set timeout for mapping sequences
set timeoutlen=500

" Add spell checking
set spell
set spelllang=en_us

" Configure update time for better experience
set updatetime=300
"""
        config_file.write(exclusive_configs)
        print("Added exclusive configurations.")

def setup_git_config():
    """Setup Git configuration for Neovim projects."""
    gitconfig_path = os.path.expanduser("~/.gitconfig")
    if not os.path.exists(gitconfig_path):
        with open(gitconfig_path, 'w') as gitconfig:
            gitconfig_content = """
[core]
    editor = nvim
[alias]
    co = checkout
    br = branch
    ci = commit
    st = status
            """
            gitconfig.write(gitconfig_content)
            print("Git configuration set with Neovim as the default editor.")

def main():
    """Main function to execute Neovim setup and resolve errors."""
    print("Starting Neovim setup...")

    # Install necessary packages
    install_packages()

    # Install Python support for Neovim
    install_neovim_python_support()

    # Install Vim-Plug for plugin management
    install_vim_plug()

    # Install Packer plugin manager
    install_packer()

    # Fix conflicting init.lua and init.vim files
    fix_conflicting_configs()

    # Remove problematic packer_compiled.lua file if it exists
    remove_packer_compiled()

    # Ask user for theme choice
    theme_choice = welcome_message()

    # Setup Neovim configuration with the selected theme
    setup_neovim_config(theme_choice)

    # Backup current configuration
    backup_neovim_config()

    # Auto-update Neovim and plugins
    auto_update()

    # Add additional configurations
    additional_configurations()

    # Setup Git configuration
    setup_git_config()

    print("\nNeovim setup complete. You can now use Neovim by typing 'nvim' in your terminal.")

if __name__ == "__main__":
    main()

