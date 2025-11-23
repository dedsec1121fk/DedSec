import os
import re
import datetime

# Path configuration
BASE_DIR = "/storage/emulated/0/Download"
WEBSITES_DIR = os.path.join(BASE_DIR, "Websites")

def ensure_directory():
    """Create Websites directory if it doesn't exist"""
    if not os.path.exists(WEBSITES_DIR):
        os.makedirs(WEBSITES_DIR)

def sanitize_filename(title):
    """Convert title to safe filename"""
    return re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')

def get_color_input(color_name, default, example):
    """Get color input with simple validation"""
    print(f"\n🎨 {color_name} Color:")
    print(f"   Default: {default}")
    print(f"   Examples: 'blue', 'red', '#ff0000', '#00ff00'")
    color = input(f"   Enter color (or press Enter for default): ").strip()
    return color if color else default

def get_font_input():
    """Get font preferences"""
    print("\n🔤 Font Settings:")
    print("   Popular fonts: 'Arial', 'Georgia', 'Verdana', 'Helvetica'")
    print("   Google Fonts: 'Roboto', 'Open Sans', 'Lato', 'Montserrat'")
    
    font_family = input("   Font Family (or Enter for default): ").strip()
    if not font_family:
        font_family = "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
    
    print("\n📏 Font Sizes:")
    print("   Small: 14px, Normal: 16px, Large: 18px, X-Large: 20px")
    base_size = input("   Base Font Size (or Enter for 16px): ").strip()
    base_size = base_size if base_size else "16px"
    
    return {
        'family': font_family,
        'base_size': base_size
    }

def get_layout_preferences():
    """Get layout and design preferences"""
    print("\n🎨 Layout & Design")
    
    print("\n📐 Container Width:")
    print("   Mobile: 90%, Tablet: 80%, Desktop: 1200px")
    width = input("   Max Width (or Enter for 1200px): ").strip()
    width = width if width else "1200px"
    
    print("\n🔄 Content Alignment:")
    print("   1. Left Aligned (Traditional)")
    print("   2. Center Aligned (Modern)")
    print("   3. Justified (Newspaper style)")
    
    alignment_choice = input("   Choose alignment (1-3 or Enter for Left): ").strip()
    alignments = {
        '1': 'left',
        '2': 'center', 
        '3': 'justify'
    }
    alignment = alignments.get(alignment_choice, 'left')
    
    print("\n🎭 Border Style:")
    print("   1. Rounded Corners (Modern)")
    print("   2. Sharp Corners (Minimalist)")
    print("   3. Shadow Only (Floating)")
    
    border_choice = input("   Choose style (1-3 or Enter for Rounded): ").strip()
    border_radius = "15px" if border_choice != '2' else "0px"
    box_shadow = "0 5px 25px rgba(0,0,0,0.1)" if border_choice != '3' else "0 10px 30px rgba(0,0,0,0.15)"
    
    return {
        'width': width,
        'alignment': alignment,
        'border_radius': border_radius,
        'box_shadow': box_shadow
    }

def get_simple_meta_tags():
    """Get meta tags in a simple way"""
    print("\n" + "🔍 SEO & Social Media Settings")
    print("   (This helps your website show up in search results)")
    print("   Press Enter to skip any of these")
    
    meta_tags = []
    
    # Essential meta tags
    description = input("\n📝 Page Description (what your page is about): ").strip()
    if description:
        meta_tags.append({'name': 'description', 'content': description})
    
    keywords = input("🏷️ Keywords (comma separated): ").strip()
    if keywords:
        meta_tags.append({'name': 'keywords', 'content': keywords})
    
    author = input("👤 Author Name: ").strip()
    if author:
        meta_tags.append({'name': 'author', 'content': author})
    
    # Social media meta tags
    print("\n📱 Social Media Sharing")
    og_title = input("   Share Title (for Facebook/Twitter): ").strip()
    if og_title:
        meta_tags.append({'property': 'og:title', 'content': og_title})
    
    og_desc = input("   Share Description: ").strip()
    if og_desc:
        meta_tags.append({'property': 'og:description', 'content': og_desc})
    
    og_image = input("   Share Image URL (optional): ").strip()
    if og_image:
        meta_tags.append({'property': 'og:image', 'content': og_image})
    
    # Additional meta tags
    print("\n⚙️ Advanced SEO (optional)")
    viewport = input("   Viewport (or Enter for mobile-friendly): ").strip()
    if viewport:
        meta_tags.append({'name': 'viewport', 'content': viewport})
    else:
        meta_tags.append({'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0'})
    
    charset = input("   Character Set (or Enter for UTF-8): ").strip()
    if charset:
        meta_tags.append({'charset': charset})
    else:
        meta_tags.append({'charset': 'UTF-8'})
    
    return meta_tags

def get_user_input():
    """Collect user input for website creation - EXPANDED"""
    print("\n" + "="*50)
    print("🚀 CREATE NEW WEBSITE")
    print("="*50)
    
    # Basic information
    print("\n📝 Basic Information:")
    title = input("   Website Title: ").strip() or "My Website"
    text = input("   Main Content (you can write multiple lines):\n   ").strip()
    categories = input("   Categories (comma separated): ").strip()
    
    # Colors - expanded
    print("\n" + "🎨 Customize Colors")
    print("   (Press Enter to use default colors)")
    
    colors = {
        'title': get_color_input("Title", "#2c3e50", "dark blue"),
        'text': get_color_input("Text", "#34495e", "dark gray"),
        'background': get_color_input("Background", "#ecf0f1", "light gray"),
        'container_bg': get_color_input("Content Box", "#ffffff", "white"),
        'border': get_color_input("Borders", "#bdc3c7", "light gray"),
        'category': get_color_input("Categories", "#7f8c8d", "gray"),
        'header_bg': get_color_input("Header Background", "#3498db", "blue"),
        'footer_bg': get_color_input("Footer Background", "#2c3e50", "dark blue"),
        'link': get_color_input("Links", "#2980b9", "blue"),
        'hover': get_color_input("Link Hover", "#e74c3c", "red")
    }
    
    # Font settings
    fonts = get_font_input()
    
    # Layout preferences
    layout = get_layout_preferences()
    
    # Advanced features
    print("\n🔧 Advanced Features")
    add_header = input("   Add website header? (y/n): ").lower().strip() == 'y'
    add_footer = input("   Add website footer? (y/n): ").lower().strip() == 'y'
    add_nav = input("   Add navigation menu? (y/n): ").lower().strip() == 'y'
    
    # Meta tags - optional
    print("\n" + "🔍 Search Engine Optimization")
    add_meta = input("   Add SEO settings? (y/n): ").lower().strip()
    meta_tags = get_simple_meta_tags() if add_meta == 'y' else []
    
    return {
        'title': title,
        'text': text,
        'categories': categories,
        'colors': colors,
        'fonts': fonts,
        'layout': layout,
        'meta_tags': meta_tags,
        'features': {
            'header': add_header,
            'footer': add_footer,
            'navigation': add_nav
        }
    }

def generate_meta_tags(meta_tags):
    """Generate meta tags HTML"""
    if not meta_tags:
        return '<meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">'
    
    meta_html = []
    for meta in meta_tags:
        if 'charset' in meta:
            meta_html.append(f'<meta charset="{meta["charset"]}">')
        elif 'property' in meta:
            meta_html.append(f'<meta property="{meta["property"]}" content="{meta["content"]}">')
        else:
            meta_html.append(f'<meta name="{meta["name"]}" content="{meta["content"]}">')
    
    # Always include viewport for mobile if not specified
    has_viewport = any(meta.get('name') == 'viewport' for meta in meta_tags)
    if not has_viewport:
        meta_html.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    
    # Always include charset if not specified
    has_charset = any('charset' in meta for meta in meta_tags)
    if not has_charset:
        meta_html.append('<meta charset="UTF-8">')
    
    return '\n    '.join(meta_html)

def generate_html(data):
    """Generate responsive HTML content with expanded features"""
    colors = data['colors']
    fonts = data['fonts']
    layout = data['layout']
    
    css = f"""
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: {fonts['family']};
            font-size: {fonts['base_size']};
            line-height: 1.6;
            color: {colors['text']};
            background-color: {colors['background']};
            min-height: 100vh;
            padding: 10px;
        }}
        
        .container {{
            max-width: {layout['width']};
            margin: 0 auto;
            background-color: {colors['container_bg']};
            padding: 30px;
            border-radius: {layout['border_radius']};
            box-shadow: {layout['box_shadow']};
            border: 2px solid {colors['border']};
        }}
        
        .website-header {{
            background: {colors['header_bg']};
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 10px 10px 0 0;
            margin: -30px -30px 30px -30px;
        }}
        
        .website-header h1 {{
            color: white;
            margin-bottom: 10px;
            border-bottom: none;
        }}
        
        .website-nav {{
            background: rgba(255,255,255,0.1);
            padding: 10px;
            margin-top: 10px;
            border-radius: 5px;
        }}
        
        .nav-links {{
            list-style: none;
            display: flex;
            justify-content: center;
            gap: 20px;
        }}
        
        .nav-links a {{
            color: white;
            text-decoration: none;
            padding: 5px 10px;
            border-radius: 3px;
            transition: background 0.3s;
        }}
        
        .nav-links a:hover {{
            background: rgba(255,255,255,0.2);
        }}
        
        h1 {{
            color: {colors['title']};
            font-size: 2.5rem;
            text-align: {layout['alignment']};
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 3px solid {colors['border']};
        }}
        
        .content {{
            font-size: 1.1rem;
            margin: 20px 0;
            line-height: 1.8;
            text-align: {layout['alignment']};
        }}
        
        .content p {{
            margin-bottom: 1.5em;
        }}
        
        .content a {{
            color: {colors['link']};
            text-decoration: none;
            transition: color 0.3s;
        }}
        
        .content a:hover {{
            color: {colors['hover']};
            text-decoration: underline;
        }}
        
        .categories {{
            color: {colors['category']};
            font-style: italic;
            margin-top: 30px;
            padding: 15px;
            background-color: {colors['background']};
            border-radius: 10px;
            border-left: 4px solid {colors['border']};
        }}
        
        .website-footer {{
            background: {colors['footer_bg']};
            color: white;
            text-align: center;
            padding: 20px;
            margin: 30px -30px -30px -30px;
            border-radius: 0 0 10px 10px;
        }}
        
        /* Mobile responsive */
        @media (max-width: 768px) {{
            body {{ padding: 5px; }}
            .container {{ padding: 15px; }}
            h1 {{ font-size: 2rem; }}
            .nav-links {{ flex-direction: column; gap: 10px; }}
        }}
        
        /* Print styles */
        @media print {{
            body {{ background: white; }}
            .container {{ box-shadow: none; border: 1px solid #ccc; }}
        }}
    </style>
    """
    
    js = """
    <script>
        // Enhanced mobile-friendly features
        document.addEventListener('DOMContentLoaded', function() {
            // Make images responsive
            document.querySelectorAll('img').forEach(img => {
                img.style.maxWidth = '100%';
                img.style.height = 'auto';
            });
            
            // Smooth scrolling for anchor links
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {
                anchor.addEventListener('click', function (e) {
                    e.preventDefault();
                    const target = document.querySelector(this.getAttribute('href'));
                    if (target) {
                        target.scrollIntoView({ behavior: 'smooth' });
                    }
                });
            });
            
            // Add loading animation
            const style = document.createElement('style');
            style.textContent = `
                .fade-in { animation: fadeIn 0.5s ease-in; }
                @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
            `;
            document.head.appendChild(style);
            
            // Apply fade-in animation to main content
            setTimeout(() => {
                document.querySelector('.container').classList.add('fade-in');
            }, 100);
        });
    </script>
    """
    
    # Format text with paragraphs and basic markdown
    formatted_text = ""
    if data['text']:
        paragraphs = data['text'].split('\n\n')
        for paragraph in paragraphs:
            if paragraph.strip():
                # Simple markdown-like formatting
                text = paragraph.strip()
                text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)  # **bold**
                text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)  # *italic*
                text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2" target="_blank">\1</a>', text)  # [link](url)
                text = text.replace(chr(10), '<br>')
                formatted_text += f"<p>{text}</p>"
    
    # Generate meta tags
    meta_tags_html = generate_meta_tags(data['meta_tags'])
    
    # Generate header if enabled
    header_html = ""
    if data['features']['header']:
        nav_html = ""
        if data['features']['navigation']:
            nav_html = f"""
            <nav class="website-nav">
                <ul class="nav-links">
                    <li><a href="#home">Home</a></li>
                    <li><a href="#about">About</a></li>
                    <li><a href="#contact">Contact</a></li>
                </ul>
            </nav>
            """
        
        header_html = f"""
        <header class="website-header">
            <h1>{data['title']}</h1>
            {nav_html}
        </header>
        """
    
    # Generate footer if enabled
    footer_html = ""
    if data['features']['footer']:
        current_year = datetime.datetime.now().year
        footer_html = f"""
        <footer class="website-footer">
            <p>&copy; {current_year} {data['title']}. All rights reserved.</p>
        </footer>
        """
    
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    {meta_tags_html}
    <title>{data['title']}</title>
    {css}
</head>
<body>
    <div class="container">
        {header_html}
        <div class="content">
            {formatted_text if formatted_text else '<p>Welcome to my website!</p>'}
        </div>
        {f"<div class='categories'>Categories: {data['categories']}</div>" if data['categories'] else ''}
        {footer_html}
    </div>
    {js}
</body>
</html>"""
    
    return html_template

def create_website():
    """Create a new website file"""
    print("\n" + "✨ Creating New Website...")
    ensure_directory()
    data = get_user_input()
    
    filename = sanitize_filename(data['title']) + ".html"
    filepath = os.path.join(WEBSITES_DIR, filename)
    
    # Check if file exists
    if os.path.exists(filepath):
        print(f"\n⚠️  A website named '{filename}' already exists.")
        overwrite = input("   Overwrite? (y/n): ").lower()
        if overwrite != 'y':
            print("   ❌ Creation cancelled.")
            return
    
    # Generate and save HTML
    html_content = generate_html(data)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n✅ Website created successfully!")
    print(f"📁 Saved as: {filename}")
    print(f"📍 Location: Websites folder in Downloads")

def list_websites():
    """List all HTML files in Websites directory"""
    ensure_directory()
    files = [f for f in os.listdir(WEBSITES_DIR) if f.endswith('.html')]
    
    if not files:
        print("\n📁 No websites found.")
        print("   Create your first website using option 1!")
        return None
    
    print("\n📚 Your Websites:")
    for i, file in enumerate(files, 1):
        filepath = os.path.join(WEBSITES_DIR, file)
        size = os.path.getsize(filepath)
        print(f"   {i}. {file} ({size} bytes)")
    return files

def edit_website():
    """Edit an existing website - EXPANDED"""
    files = list_websites()
    if not files:
        return
    
    try:
        choice = int(input("\n🔢 Enter website number to edit: "))
        if 1 <= choice <= len(files):
            filename = files[choice-1]
            filepath = os.path.join(WEBSITES_DIR, filename)
            
            print(f"\n✏️  Editing: {filename}")
            
            # Read existing content
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract current title
            title_match = re.search(r'<title>(.*?)</title>', content)
            current_title = title_match.group(1) if title_match else filename.replace('.html', '')
            
            print("\n📝 Edit Website (press Enter to keep current value)")
            new_title = input(f"   Title [{current_title}]: ").strip() or current_title
            
            # Recreate with new settings
            data = get_user_input()
            data['title'] = new_title
            
            # Generate new HTML
            new_html = generate_html(data)
            
            # Save changes
            new_filename = sanitize_filename(data['title']) + ".html"
            new_filepath = os.path.join(WEBSITES_DIR, new_filename)
            
            # Remove old file if name changed
            if new_filepath != filepath and os.path.exists(filepath):
                os.remove(filepath)
            
            with open(new_filepath, 'w', encoding='utf-8') as f:
                f.write(new_html)
            
            print(f"\n✅ Website updated successfully!")
            
        else:
            print("❌ Invalid number. Please try again.")
    except (ValueError, IndexError):
        print("❌ Please enter a valid number.")

def delete_website():
    """Delete a website file"""
    files = list_websites()
    if not files:
        return
    
    try:
        choice = int(input("\n🔢 Enter website number to delete: "))
        if 1 <= choice <= len(files):
            filename = files[choice-1]
            filepath = os.path.join(WEBSITES_DIR, filename)
            
            print(f"\n🗑️  You're about to delete: {filename}")
            print(f"   Size: {os.path.getsize(filepath)} bytes")
            confirm = input("   Are you sure? (type 'yes' to confirm): ").lower()
            
            if confirm == 'yes':
                os.remove(filepath)
                print(f"✅ Website deleted successfully!")
            else:
                print("❌ Deletion cancelled.")
        else:
            print("❌ Invalid number.")
    except (ValueError, IndexError):
        print("❌ Please enter a valid number.")

def show_hosting_guide():
    """Show comprehensive hosting guide with multiple options"""
    print("\n" + "="*60)
    print("🌐 COMPLETE WEBSITE HOSTING GUIDE")
    print("="*60)
    
    while True:
        print("\n📚 Choose Hosting Platform:")
        print("1. 🐙 GitHub Pages (Recommended for beginners)")
        print("2. 🌐 Netlify (Easiest deployment)")
        print("3. ⚡ Vercel (Fastest performance)")
        print("4. 🔥 Firebase Hosting (Google platform)")
        print("5. 📧 000webhost (Free with no credit card)")
        print("6. 🆓 InfinityFree (Truly free forever)")
        print("7. 🔙 Back to Main Menu")
        
        choice = input("\nChoose platform (1-7): ").strip()
        
        if choice == '1':
            show_github_pages_guide()
        elif choice == '2':
            show_netlify_guide()
        elif choice == '3':
            show_vercel_guide()
        elif choice == '4':
            show_firebase_guide()
        elif choice == '5':
            show_000webhost_guide()
        elif choice == '6':
            show_infinityfree_guide()
        elif choice == '7':
            break
        else:
            print("❌ Please choose 1-7")

def show_github_pages_guide():
    """Enhanced GitHub Pages guide"""
    print("\n" + "="*60)
    print("🐙 GITHUB PAGES - FREE HOSTING")
    print("="*60)
    
    print("\n⭐ Advantages:")
    print("   ✅ 100% FREE forever")
    print("   ✅ Custom domain support")
    print("   ✅ Automatic HTTPS")
    print("   ✅ Easy updates")
    print("   ✅ Great for portfolios, blogs, projects")
    
    print("\n🚀 Step-by-Step Guide:")
    
    steps = [
        ("1. 📝 Create GitHub Account", "Go to github.com → Sign up (free)"),
        ("2. ➕ Create Repository", "Click '+' → New repository → Name: USERNAME.github.io"),
        ("3. 📤 Upload Files", "Click 'Add file' → Upload files → Select your HTML file"),
        ("4. 🚀 Enable GitHub Pages", "Settings → Pages → Source: main branch → Save"),
        ("5. 🌍 Wait & Visit", "Wait 1-5 minutes → Visit https://USERNAME.github.io")
    ]
    
    for step, description in steps:
        print(f"\n{step}")
        print(f"   {description}")
    
    print("\n💡 Pro Tips:")
    print("   • Name your file 'index.html' - it becomes homepage")
    print("   • Update by uploading new files")
    print("   • Add custom domain in repository Settings → Pages")
    print("   • Use GitHub Mobile app for easy updates")
    
    print(f"\n📁 Your website files are in: {WEBSITES_DIR}")

def show_netlify_guide():
    """Netlify hosting guide"""
    print("\n" + "="*50)
    print("🌐 NETLIFY - EASIEST DEPLOYMENT")
    print("="*50)
    
    print("\n🚀 3 Ways to Deploy:")
    
    print("\n1. 📤 Drag & Drop (Easiest)")
    print("   • Go to: app.netlify.com")
    print("   • Drag your HTML file to deployment area")
    print("   • Get instant URL: random-name.netlify.app")
    
    print("\n2. 📧 Email Deployment (Mobile-friendly)")
    print("   • Email your HTML file to deploy@netlify.com")
    print("   • Reply with your site's HTML attached")
    print("   • Get your site URL in reply email")
    
    print("\n3. 📱 Netlify Mobile App")
    print("   • Download Netlify app from store")
    print("   • Login and upload files directly")
    
    print("\n⭐ Features:")
    print("   ✅ Free custom domain")
    print("   ✅ Automatic SSL")
    print("   ✅ Form handling")
    print("   ✅ Instant deployment")

def show_vercel_guide():
    """Vercel hosting guide"""
    print("\n" + "="*50)
    print("⚡ VERCEL - ULTRA FAST HOSTING")
    print("="*50)
    
    print("\n🚀 Quick Deployment:")
    print("1. Go to: vercel.com")
    print("2. Sign up with GitHub (recommended)")
    print("3. Click 'Import Project'")
    print("4. Drag and drop your HTML file")
    print("5. Get URL: your-site.vercel.app")
    
    print("\n📱 Mobile Method:")
    print("• Use Chrome browser on your phone")
    print("• Go to vercel.com/new")
    print("• Upload file directly from Downloads")
    
    print("\n⭐ Advantages:")
    print("   ✅ Global CDN - super fast worldwide")
    print("   ✅ Automatic optimizations")
    print("   ✅ Custom domains")
    print("   ✅ Deploys in seconds")

def show_firebase_guide():
    """Firebase hosting guide"""
    print("\n" + "="*50)
    print("🔥 FIREBASE HOSTING - GOOGLE PLATFORM")
    print("="*50)
    
    print("\n🚀 Steps:")
    print("1. Create Google account (if needed)")
    print("2. Go to: console.firebase.google.com")
    print("3. Create new project")
    print("4. Enable Hosting in left menu")
    print("5. Upload your HTML file")
    print("6. Get URL: your-project.web.app")
    
    print("\n⭐ Google Benefits:")
    print("   ✅ Google's global infrastructure")
    print("   ✅ Free SSL certificate")
    print("   ✅ Easy custom domain")
    print("   ✅ Integration with other Google services")

def show_000webhost_guide():
    """000webhost guide"""
    print("\n" + "="*50)
    print("📧 000WEBHOST - NO CREDIT CARD NEEDED")
    print("="*50)
    
    print("\n🚀 Simple Steps:")
    print("1. Go to: 000webhost.com")
    print("2. Sign up with email (no credit card)")
    print("3. Verify email address")
    print("4. Create new website")
    print("5. Use File Manager to upload HTML")
    print("6. Access: your-site.000webhostapp.com")
    
    print("\n⭐ Features:")
    print("   ✅ 100% free, no hidden costs")
    print("   ✅ 300 MB storage")
    print("   ✅ No ads injected")
    print("   ✅ Easy control panel")

def show_infinityfree_guide():
    """InfinityFree guide"""
    print("\n" + "="*50)
    print("🆓 INFINITYFREE - TRULY FREE FOREVER")
    print("="*50)
    
    print("\n🚀 Unlimited Free Hosting:")
    print("1. Visit: infinityfree.net")
    print("2. Click 'Sign Up Free'")
    print("3. Choose free plan")
    print("4. Create account")
    print("5. Upload files via File Manager")
    print("6. Your site: your-site.rf.gd")
    
    print("\n⭐ Unlimited Features:")
    print("   ✅ Unlimited disk space")
    print("   ✅ Unlimited bandwidth")
    print("   ✅ Free subdomain")
    print("   ✅ No forced ads")

def show_quick_publish_tips():
    """Show quick publishing tips"""
    print("\n" + "="*50)
    print("⚡ QUICK PUBLISHING TIPS")
    print("="*50)
    
    print("\n🎯 For Absolute Beginners:")
    print("1. GitHub Pages - Most reliable")
    print("2. Netlify - Easiest to use")
    print("3. 000webhost - No verification needed")
    
    print("\n📱 Publishing from Phone:")
    print("• Use Chrome browser for all platforms")
    print("• Enable 'Desktop site' in browser options")
    print("• Upload files directly from Downloads folder")
    
    print(f"\n📍 Your websites are here: {WEBSITES_DIR}")

def main():
    """Main menu loop - EXPANDED"""
    while True:
        print("\n" + "="*40)
        print("🏠 WEBSITE CREATOR")
        print("="*40)
        print("1. 🆕 Create Website")
        print("2. 📝 Edit Website")
        print("3. 📋 List Websites")
        print("4. 🗑️ Delete Website")
        print("5. 🌐 Publishing Guide (6 FREE Options)")
        print("6. ⚡ Quick Publishing Tips")
        print("7. 🚪 Exit")
        print("="*40)
        
        choice = input("Choose an option (1-7): ").strip()
        
        if choice == '1':
            create_website()
        elif choice == '2':
            edit_website()
        elif choice == '3':
            list_websites()
        elif choice == '4':
            delete_website()
        elif choice == '5':
            show_hosting_guide()
        elif choice == '6':
            show_quick_publish_tips()
        elif choice == '7':
            print("\n👋 Thank you for using Website Creator!")
            print("   Your websites are in: Websites folder in Downloads")
            break
        else:
            print("❌ Please choose 1-7")

if __name__ == "__main__":
    # Check storage access
    if not os.path.exists(BASE_DIR):
        print("❌ Cannot access phone storage.")
        print("💡 Please run this command first: termux-setup-storage")
        print("   Then run this script again.")
        exit(1)
    
    # Check if directory exists, if not create it
    ensure_directory()
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye! Thanks for using Website Creator!")
    except Exception as e:
        print(f"\n❌ Oops! Something went wrong: {e}")
        print("   Please try again or restart the app.")