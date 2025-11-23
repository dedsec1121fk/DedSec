import os
import re
import datetime

# Path configuration
BASE_DIR = "/storage/emulated/0/Download"
WEBSITES_DIR = os.path.join(BASE_DIR, "Websites")

def ensure_directory():
    """Δημιουργία φακέλου Websites αν δεν υπάρχει"""
    if not os.path.exists(WEBSITES_DIR):
        os.makedirs(WEBSITES_DIR)

def sanitize_filename(title):
    """Μετατροπή τίτλου σε ασφαλές όνομα αρχείου"""
    return re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')

def get_color_input(color_name, default, example):
    """Εισαγωγή χρώματος με απλή επικύρωση"""
    print(f"\n🎨 Χρώμα {color_name}:")
    print(f"   Προεπιλογή: {default}")
    print(f"   Παραδείγματα: 'μπλε', 'κόκκινο', '#ff0000', '#00ff00'")
    color = input(f"   Εισάγετε χρώμα (ή Enter για προεπιλογή): ").strip()
    return color if color else default

def get_font_input():
    """Εισαγωγή προτιμήσεων γραμματοσειράς"""
    print("\n🔤 Ρυθμίσεις Γραμματοσειράς:")
    print("   Δημοφιλείς γραμματοσειρές: 'Arial', 'Georgia', 'Verdana', 'Helvetica'")
    print("   Google Fonts: 'Roboto', 'Open Sans', 'Lato', 'Montserrat'")
    
    font_family = input("   Οικογένεια Γραμματοσειράς (ή Enter για προεπιλογή): ").strip()
    if not font_family:
        font_family = "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
    
    print("\n📏 Μέγεθος Γραμματοσειράς:")
    print("   Μικρό: 14px, Κανονικό: 16px, Μεγάλο: 18px, Πολύ Μεγάλο: 20px")
    base_size = input("   Βασικό Μέγεθος Γραμματοσειράς (ή Enter για 16px): ").strip()
    base_size = base_size if base_size else "16px"
    
    return {
        'family': font_family,
        'base_size': base_size
    }

def get_layout_preferences():
    """Εισαγωγή προτιμήσεων διάταξης και σχεδίου"""
    print("\n🎨 Διάταξη & Σχεδιασμός")
    
    print("\n📐 Πλάτος Περιέκτη:")
    print("   Κινητό: 90%, Tablet: 80%, Desktop: 1200px")
    width = input("   Μέγιστο Πλάτος (ή Enter για 1200px): ").strip()
    width = width if width else "1200px"
    
    print("\n🔄 Στοίχιση Περιεχομένου:")
    print("   1. Αριστερή Στοίχιση (Παραδοσιακή)")
    print("   2. Κεντρική Στοίχιση (Μοντέρνα)")
    print("   3. Πλήρης Στοίχιση (Στυλ εφημερίδας)")
    
    alignment_choice = input("   Επιλέξτε στοίχιση (1-3 ή Enter για Αριστερά): ").strip()
    alignments = {
        '1': 'left',
        '2': 'center', 
        '3': 'justify'
    }
    alignment = alignments.get(alignment_choice, 'left')
    
    print("\n🎭 Στυλ Περιγράμματος:")
    print("   1. Στρογγυλεμένες Γωνίες (Μοντέρνο)")
    print("   2. Κοφτές Γωνίες (Ελάχιστο)")
    print("   3. Μόνο Σκιά (Αιωρούμενο)")
    
    border_choice = input("   Επιλέξτε στυλ (1-3 ή Enter για Στρογγυλεμένο): ").strip()
    border_radius = "15px" if border_choice != '2' else "0px"
    box_shadow = "0 5px 25px rgba(0,0,0,0.1)" if border_choice != '3' else "0 10px 30px rgba(0,0,0,0.15)"
    
    return {
        'width': width,
        'alignment': alignment,
        'border_radius': border_radius,
        'box_shadow': box_shadow
    }

def get_simple_meta_tags():
    """Λήψη meta tags με απλό τρόπο"""
    print("\n" + "🔍 Ρυθμίσεις SEO & Κοινωνικών Δικτύων")
    print("   (Βοηθάει την ιστοσελίδα σας να εμφανίζεται σε αποτελέσματα αναζήτησης)")
    print("   Πατήστε Enter για να παραλείψετε οποιοδήποτε από αυτά")
    
    meta_tags = []
    
    # Βασικά meta tags
    description = input("\n📝 Περιγραφή Σελίδας (για τι πηγαίνει η σελίδα σας): ").strip()
    if description:
        meta_tags.append({'name': 'description', 'content': description})
    
    keywords = input("🏷️ Λέξεις Κλειδιά (διαχωρισμένες με κόμμα): ").strip()
    if keywords:
        meta_tags.append({'name': 'keywords', 'content': keywords})
    
    author = input("👤 Όνομα Συγγραφέα: ").strip()
    if author:
        meta_tags.append({'name': 'author', 'content': author})
    
    # Meta tags για κοινωνικά δίκτυα
    print("\n📱 Κοινή χρήση σε Κοινωνικά Δίκτυα")
    og_title = input("   Τίτλος Κοινοποίησης (για Facebook/Twitter): ").strip()
    if og_title:
        meta_tags.append({'property': 'og:title', 'content': og_title})
    
    og_desc = input("   Περιγραφή Κοινοποίησης: ").strip()
    if og_desc:
        meta_tags.append({'property': 'og:description', 'content': og_desc})
    
    og_image = input("   URL Εικόνας Κοινοποίησης (προαιρετικό): ").strip()
    if og_image:
        meta_tags.append({'property': 'og:image', 'content': og_image})
    
    # Επιπλέον meta tags
    print("\n⚙️ Προχωρημένο SEO (προαιρετικό)")
    viewport = input("   Viewport (ή Enter για mobile-friendly): ").strip()
    if viewport:
        meta_tags.append({'name': 'viewport', 'content': viewport})
    else:
        meta_tags.append({'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0'})
    
    charset = input("   Σετ Χαρακτήρων (ή Enter για UTF-8): ").strip()
    if charset:
        meta_tags.append({'charset': charset})
    else:
        meta_tags.append({'charset': 'UTF-8'})
    
    return meta_tags

def get_user_input():
    """Συλλογή πληροφοριών από τον χρήστη για δημιουργία ιστοσελίδας - ΕΚΤΕΤΑΜΕΝΗ"""
    print("\n" + "="*50)
    print("🚀 ΔΗΜΙΟΥΡΓΙΑ ΝΕΑΣ ΙΣΤΟΣΕΛΙΔΑΣ")
    print("="*50)
    
    # Βασικές πληροφορίες
    print("\n📝 Βασικές Πληροφορίες:")
    title = input("   Τίτλος Ιστοσελίδας: ").strip() or "Η Ιστοσελίδα Μου"
    text = input("   Κύριο Περιεχόμενο (μπορείτε να γράψετε πολλαπλές γραμμές):\n   ").strip()
    categories = input("   Κατηγορίες (διαχωρισμένες με κόμμα): ").strip()
    
    # Χρώματα - επεκταμένα
    print("\n" + "🎨 Προσαρμογή Χρωμάτων")
    print("   (Πατήστε Enter για προεπιλεγμένα χρώματα)")
    
    colors = {
        'title': get_color_input("Τίτλου", "#2c3e50", "σκούρο μπλε"),
        'text': get_color_input("Κειμένου", "#34495e", "σκούρο γκρι"),
        'background': get_color_input("Φόντου", "#ecf0f1", "ανοιχτό γκρι"),
        'container_bg': get_color_input("Πλαισίου Περιεχομένου", "#ffffff", "άσπρο"),
        'border': get_color_input("Περιγραμμάτων", "#bdc3c7", "ανοιχτό γκρι"),
        'category': get_color_input("Κατηγοριών", "#7f8c8d", "γκρι"),
        'header_bg': get_color_input("Φόντου Κεφαλίδας", "#3498db", "μπλε"),
        'footer_bg': get_color_input("Φόντου Υποσέλιδου", "#2c3e50", "σκούρο μπλε"),
        'link': get_color_input("Συνδέσμων", "#2980b9", "μπλε"),
        'hover': get_color_input("Συνδέσμων στο Hover", "#e74c3c", "κόκκινο")
    }
    
    # Ρυθμίσεις γραμματοσειράς
    fonts = get_font_input()
    
    # Προτιμήσεις διάταξης
    layout = get_layout_preferences()
    
    # Προχωρημένες λειτουργίες
    print("\n🔧 Προχωρημένες Λειτουργίες")
    add_header = input("   Προσθήκη κεφαλίδας ιστοσελίδας; (ν/ο): ").lower().strip() == 'ν'
    add_footer = input("   Προσθήκη υποσέλιδου ιστοσελίδας; (ν/ο): ").lower().strip() == 'ν'
    add_nav = input("   Προσθήκη μενού πλοήγησης; (ν/ο): ").lower().strip() == 'ν'
    
    # Meta tags - προαιρετικά
    print("\n" + "🔍 Βελτιστοποίηση για Μηχανές Αναζήτησης")
    add_meta = input("   Προσθήκη ρυθμίσεων SEO; (ν/ο): ").lower().strip()
    meta_tags = get_simple_meta_tags() if add_meta == 'ν' else []
    
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
    """Δημιουργία HTML meta tags"""
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
    
    # Πάντα συμπεριλαμβάνουμε viewport για κινητά αν δεν έχει καθοριστεί
    has_viewport = any(meta.get('name') == 'viewport' for meta in meta_tags)
    if not has_viewport:
        meta_html.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    
    # Πάντα συμπεριλαμβάνουμε charset αν δεν έχει καθοριστεί
    has_charset = any('charset' in meta for meta in meta_tags)
    if not has_charset:
        meta_html.append('<meta charset="UTF-8">')
    
    return '\n    '.join(meta_html)

def generate_html(data):
    """Δημιουργία ανταποκρινομένου HTML περιεχομένου με επεκταμένες λειτουργίες"""
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
        // Βελτιωμένες λειτουργίες για κινητά
        document.addEventListener('DOMContentLoaded', function() {
            // Κάνει τις εικόνες ανταποκρινόμενες
            document.querySelectorAll('img').forEach(img => {
                img.style.maxWidth = '100%';
                img.style.height = 'auto';
            });
            
            // Ομαλή κύλιση για συνδέσμους αγκύρωσης
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {
                anchor.addEventListener('click', function (e) {
                    e.preventDefault();
                    const target = document.querySelector(this.getAttribute('href'));
                    if (target) {
                        target.scrollIntoView({ behavior: 'smooth' });
                    }
                });
            });
            
            // Προσθήκη animation φόρτωσης
            const style = document.createElement('style');
            style.textContent = `
                .fade-in { animation: fadeIn 0.5s ease-in; }
                @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
            `;
            document.head.appendChild(style);
            
            // Εφαρμογή fade-in animation στο κύριο περιεχόμενο
            setTimeout(() => {
                document.querySelector('.container').classList.add('fade-in');
            }, 100);
        });
    </script>
    """
    
    # Μορφοποίηση κειμένου με παραγράφους και βασικό markdown
    formatted_text = ""
    if data['text']:
        paragraphs = data['text'].split('\n\n')
        for paragraph in paragraphs:
            if paragraph.strip():
                # Απλή μορφοποίηση σαν markdown
                text = paragraph.strip()
                text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)  # **έντονα**
                text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)  # *πλάγια*
                text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2" target="_blank">\1</a>', text)  # [σύνδεσμος](url)
                text = text.replace(chr(10), '<br>')
                formatted_text += f"<p>{text}</p>"
    
    # Δημιουργία meta tags
    meta_tags_html = generate_meta_tags(data['meta_tags'])
    
    # Δημιουργία κεφαλίδας αν είναι ενεργοποιημένη
    header_html = ""
    if data['features']['header']:
        nav_html = ""
        if data['features']['navigation']:
            nav_html = f"""
            <nav class="website-nav">
                <ul class="nav-links">
                    <li><a href="#home">Αρχική</a></li>
                    <li><a href="#about">Σχετικά</a></li>
                    <li><a href="#contact">Επικοινωνία</a></li>
                </ul>
            </nav>
            """
        
        header_html = f"""
        <header class="website-header">
            <h1>{data['title']}</h1>
            {nav_html}
        </header>
        """
    
    # Δημιουργία υποσέλιδου αν είναι ενεργοποιημένο
    footer_html = ""
    if data['features']['footer']:
        current_year = datetime.datetime.now().year
        footer_html = f"""
        <footer class="website-footer">
            <p>&copy; {current_year} {data['title']}. Με επιφύλαξη παντός δικαιώματος.</p>
        </footer>
        """
    
    html_template = f"""<!DOCTYPE html>
<html lang="el">
<head>
    {meta_tags_html}
    <title>{data['title']}</title>
    {css}
</head>
<body>
    <div class="container">
        {header_html}
        <div class="content">
            {formatted_text if formatted_text else '<p>Καλώς ήρθατε στην ιστοσελίδα μου!</p>'}
        </div>
        {f"<div class='categories'>Κατηγορίες: {data['categories']}</div>" if data['categories'] else ''}
        {footer_html}
    </div>
    {js}
</body>
</html>"""
    
    return html_template

def create_website():
    """Δημιουργία νέου αρχείου ιστοσελίδας"""
    print("\n" + "✨ Δημιουργία Νέας Ιστοσελίδας...")
    ensure_directory()
    data = get_user_input()
    
    filename = sanitize_filename(data['title']) + ".html"
    filepath = os.path.join(WEBSITES_DIR, filename)
    
    # Έλεγχος αν το αρχείο υπάρχει
    if os.path.exists(filepath):
        print(f"\n⚠️  Υπάρχει ήδη ιστοσελίδα με όνομα '{filename}'.")
        overwrite = input("   Αντικατάσταση; (ν/ο): ").lower()
        if overwrite != 'ν':
            print("   ❌ Ακύρωση δημιουργίας.")
            return
    
    # Δημιουργία και αποθήκευση HTML
    html_content = generate_html(data)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n✅ Η ιστοσελίδα δημιουργήθηκε επιτυχώς!")
    print(f"📁 Αποθηκεύτηκε ως: {filename}")
    print(f"📍 Τοποθεσία: Φάκελος Websites στα Downloads")

def list_websites():
    """Λίστα όλων των HTML αρχείων στον φάκελο Websites"""
    ensure_directory()
    files = [f for f in os.listdir(WEBSITES_DIR) if f.endswith('.html')]
    
    if not files:
        print("\n📁 Δεν βρέθηκαν ιστοσελίδες.")
        print("   Δημιουργήστε την πρώτη σας ιστοσελίδα επιλέγοντας την επιλογή 1!")
        return None
    
    print("\n📚 Οι Ιστοσελίδες Σας:")
    for i, file in enumerate(files, 1):
        filepath = os.path.join(WEBSITES_DIR, file)
        size = os.path.getsize(filepath)
        print(f"   {i}. {file} ({size} bytes)")
    return files

def edit_website():
    """Επεξεργασία υπάρχουσας ιστοσελίδας - ΕΚΤΕΤΑΜΕΝΗ"""
    files = list_websites()
    if not files:
        return
    
    try:
        choice = int(input("\n🔢 Εισάγετε αριθμό ιστοσελίδας για επεξεργασία: "))
        if 1 <= choice <= len(files):
            filename = files[choice-1]
            filepath = os.path.join(WEBSITES_DIR, filename)
            
            print(f"\n✏️  Επεξεργασία: {filename}")
            
            # Ανάγνωση υπάρχοντος περιεχομένου
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Εξαγωγή τρέχοντος τίτλου
            title_match = re.search(r'<title>(.*?)</title>', content)
            current_title = title_match.group(1) if title_match else filename.replace('.html', '')
            
            print("\n📝 Επεξεργασία Ιστοσελίδας (πατήστε Enter για τρέχουσα τιμή)")
            new_title = input(f"   Τίτλος [{current_title}]: ").strip() or current_title
            
            # Επανδημιουργία με νέες ρυθμίσεις
            data = get_user_input()
            data['title'] = new_title
            
            # Δημιουργία νέου HTML
            new_html = generate_html(data)
            
            # Αποθήκευση αλλαγών
            new_filename = sanitize_filename(data['title']) + ".html"
            new_filepath = os.path.join(WEBSITES_DIR, new_filename)
            
            # Διαγραφή παλιού αρχείου αν άλλαξε το όνομα
            if new_filepath != filepath and os.path.exists(filepath):
                os.remove(filepath)
            
            with open(new_filepath, 'w', encoding='utf-8') as f:
                f.write(new_html)
            
            print(f"\n✅ Η ιστοσελίδα ενημερώθηκε επιτυχώς!")
            
        else:
            print("❌ Μη έγκυρος αριθμός. Παρακαλώ δοκιμάστε ξανά.")
    except (ValueError, IndexError):
        print("❌ Παρακαλώ εισάγετε έγκυρο αριθμό.")

def delete_website():
    """Διαγραφή αρχείου ιστοσελίδας"""
    files = list_websites()
    if not files:
        return
    
    try:
        choice = int(input("\n🔢 Εισάγετε αριθμό ιστοσελίδας για διαγραφή: "))
        if 1 <= choice <= len(files):
            filename = files[choice-1]
            filepath = os.path.join(WEBSITES_DIR, filename)
            
            print(f"\n🗑️  Πρόκειται να διαγράψετε: {filename}")
            print(f"   Μέγεθος: {os.path.getsize(filepath)} bytes")
            confirm = input("   Είστε σίγουρος; (πληκτρολογήστε 'ναι' για επιβεβαίωση): ").lower()
            
            if confirm == 'ναι':
                os.remove(filepath)
                print(f"✅ Η ιστοσελίδα διαγράφηκε επιτυχώς!")
            else:
                print("❌ Ακύρωση διαγραφής.")
        else:
            print("❌ Μη έγκυρος αριθμός.")
    except (ValueError, IndexError):
        print("❌ Παρακαλώ εισάγετε έγκυρο αριθμό.")

def show_hosting_guide():
    """Εμφάνιση ολοκληρωμένου οδηγού φιλοξενίας με πολλαπλές επιλογές"""
    print("\n" + "="*60)
    print("🌐 ΟΛΟΚΛΗΡΩΜΕΝΟΣ ΟΔΗΓΟΣ ΦΙΛΟΞΕΝΙΑΣ ΙΣΤΟΣΕΛΙΔΩΝ")
    print("="*60)
    
    while True:
        print("\n📚 Επιλογή Πλατφόρμας Φιλοξενίας:")
        print("1. 🐙 GitHub Pages (Συνιστάται για αρχάριους)")
        print("2. 🌐 Netlify (Ευκολότερη ανάπτυξη)")
        print("3. ⚡ Vercel (Ταχύτερη απόδοση)")
        print("4. 🔥 Firebase Hosting (Πλατφόρμα Google)")
        print("5. 📧 000webhost (Δωρεάν χωρίς πιστωτική κάρτα)")
        print("6. 🆓 InfinityFree (Πραγματικά δωρεάν για πάντα)")
        print("7. 🔙 Επιστροφή στο Κύριο Μενού")
        
        choice = input("\nΕπιλέξτε πλατφόρμα (1-7): ").strip()
        
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
            print("❌ Παρακαλώ επιλέξτε 1-7")

def show_github_pages_guide():
    """Βελτιωμένος οδηγός GitHub Pages"""
    print("\n" + "="*60)
    print("🐙 GITHUB PAGES - ΔΩΡΕΑΝ ΦΙΛΟΞΕΝΙΑ")
    print("="*60)
    
    print("\n⭐ Πλεονεκτήματα:")
    print("   ✅ 100% ΔΩΡΕΑΝ για πάντα")
    print("   ✅ Υποστήριξη προσαρμοσμένου domain")
    print("   ✅ Αυτόματο HTTPS")
    print("   ✅ Εύκολες ενημερώσεις")
    print("   ✅ Ιδανικό για portfolio, blogs, projects")
    
    print("\n🚀 Οδηγός Βήμα-Βήμα:")
    
    steps = [
        ("1. 📝 Δημιουργία Λογαριασμού GitHub", "Πηγαίνετε στο github.com → Εγγραφή (δωρεάν)"),
        ("2. ➕ Δημιουργία Repository", "Κάντε κλικ στο '+' → New repository → Όνομα: USERNAME.github.io"),
        ("3. 📤 Μεταφόρτωση Αρχείων", "Κάντε κλικ στο 'Add file' → Upload files → Επιλέξτε το HTML αρχείο σας"),
        ("4. 🚀 Ενεργοποίηση GitHub Pages", "Settings → Pages → Source: main branch → Αποθήκευση"),
        ("5. 🌍 Αναμονή & Επίσκεψη", "Περιμένετε 1-5 λεπτά → Επισκεφθείτε το https://USERNAME.github.io")
    ]
    
    for step, description in steps:
        print(f"\n{step}")
        print(f"   {description}")
    
    print("\n💡 Συμβουλές Επαγγελματία:")
    print("   • Ονομάστε το αρχείο σας 'index.html' - γίνεται αρχική σελίδα")
    print("   • Ενημερώστε μεταφορτώνοντας νέα αρχεία")
    print("   • Προσθέστε προσαρμοσμένο domain στα Settings → Pages")
    print("   • Χρησιμοποιήστε την εφαρμογή GitHub Mobile για εύκολες ενημερώσεις")
    
    print(f"\n📁 Τα αρχεία της ιστοσελίδας σας βρίσκονται σε: {WEBSITES_DIR}")

def show_netlify_guide():
    """Οδηγός φιλοξενίας Netlify"""
    print("\n" + "="*50)
    print("🌐 NETLIFY - Η ΕΥΚΟΛΟΤΕΡΗ ΑΝΑΠΤΥΞΗ")
    print("="*50)
    
    print("\n🚀 3 Τρόποι Ανάπτυξης:")
    
    print("\n1. 📤 Σύρετε και Αφήστε (Ευκολότερος)")
    print("   • Πηγαίνετε στο: app.netlify.com")
    print("   • Σύρετε το HTML αρχείο σας στην περιοχή ανάπτυξης")
    print("   • Λάβετε αμέσως URL: τυχαίο-όνομα.netlify.app")
    
    print("\n2. 📧 Ανάπτυξη μέσω Email (Φιλικό για κινητά)")
    print("   • Στείλτε email με το HTML αρχείο σας στο deploy@netlify.com")
    print("   • Απαντήστε με το HTML της σελίδας σας επισυνάπτοντας")
    print("   • Λάβετε το URL της σελίδας σας στο email απάντησης")
    
    print("\n3. 📱 Εφαρμογή Netlify Mobile")
    print("   • Κατεβάστε την εφαρμογή Netlify από το κατάστημα")
    print("   • Συνδεθείτε και μεταφορτώστε αρχεία απευθείας")
    
    print("\n⭐ Χαρακτηριστικά:")
    print("   ✅ Δωρεάν προσαρμοσμένο domain")
    print("   ✅ Αυτόματο SSL")
    print("   ✅ Χειρισμός φορμών")
    print("   ✅ Άμεση ανάπτυξη")

def show_vercel_guide():
    """Οδηγός φιλοξενίας Vercel"""
    print("\n" + "="*50)
    print("⚡ VERCEL - ΥΠΕΡΤΑΧΕΙΑ ΦΙΛΟΞΕΝΙΑ")
    print("="*50)
    
    print("\n🚀 Γρήγορη Ανάπτυξη:")
    print("1. Πηγαίνετε στο: vercel.com")
    print("2. Εγγραφή με GitHub (συνιστάται)")
    print("3. Κάντε κλικ στο 'Import Project'")
    print("4. Σύρετε και αφήστε το HTML αρχείο σας")
    print("5. Λάβετε URL: your-site.vercel.app")
    
    print("\n📱 Μέθοδος για Κινητά:")
    print("• Χρησιμοποιήστε τον Chrome browser στο κινητό σας")
    print("• Πηγαίνετε στο vercel.com/new")
    print("• Μεταφορτώστε αρχεία απευθείας από τα Downloads")
    
    print("\n⭐ Πλεονεκτήματα:")
    print("   ✅ Global CDN - υπερταχέα παγκοσμίως")
    print("   ✅ Αυτόματες βελτιστοποιήσεις")
    print("   ✅ Προσαρμοσμένα domains")
    print("   ✅ Ανάπτυξη σε δευτερόλεπτα")

def show_firebase_guide():
    """Οδηγός φιλοξενίας Firebase"""
    print("\n" + "="*50)
    print("🔥 FIREBASE HOSTING - ΠΛΑΤΦΟΡΜΑ GOOGLE")
    print("="*50)
    
    print("\n🚀 Βήματα:")
    print("1. Δημιουργία λογαριασμού Google (αν χρειάζεται)")
    print("2. Πηγαίνετε στο: console.firebase.google.com")
    print("3. Δημιουργία νέου project")
    print("4. Ενεργοποίηση Hosting στο αριστερό μενού")
    print("5. Μεταφορτώστε το HTML αρχείο σας")
    print("6. Λάβετε URL: your-project.web.app")
    
    print("\n⭐ Οφέλη Google:")
    print("   ✅ Παγκόσμια υποδομή Google")
    print("   ✅ Δωρεάν πιστοποιητικό SSL")
    print("   ✅ Εύκολο προσαρμοσμένο domain")
    print("   ✅ Ολοκλήρωση με άλλες υπηρεσίες Google")

def show_000webhost_guide():
    """Οδηγός 000webhost"""
    print("\n" + "="*50)
    print("📧 000WEBHOST - ΧΩΡΙΣ ΠΙΣΤΩΤΙΚΗ ΚΑΡΤΑ")
    print("="*50)
    
    print("\n🚀 Απλά Βήματα:")
    print("1. Πηγαίνετε στο: 000webhost.com")
    print("2. Εγγραφή με email (χωρίς πιστωτική κάρτα)")
    print("3. Επαληθεύστε τη διεύθυνση email")
    print("4. Δημιουργία νέας ιστοσελίδας")
    print("5. Χρησιμοποιήστε τον File Manager για μεταφόρτωση HTML")
    print("6. Πρόσβαση: your-site.000webhostapp.com")
    
    print("\n⭐ Χαρακτηριστικά:")
    print("   ✅ 100% δωρεάν, χωρίς κρυφά κόστη")
    print("   ✅ 300 MB αποθηκευτικός χώρος")
    print("   ✅ Χωρίς εισαγμένες διαφημίσεις")
    print("   ✅ Εύκολο control panel")

def show_infinityfree_guide():
    """Οδηγός InfinityFree"""
    print("\n" + "="*50)
    print("🆓 INFINITYFREE - ΠΡΑΓΜΑΤΙΚΑ ΔΩΡΕΑΝ ΓΙΑ ΠΑΝΤΑ")
    print("="*50)
    
    print("\n🚀 Απεριόριστη Δωρεάν Φιλοξενία:")
    print("1. Επισκεφθείτε: infinityfree.net")
    print("2. Κάντε κλικ στο 'Sign Up Free'")
    print("3. Επιλέξτε το δωρεάν πλάνο")
    print("4. Δημιουργία λογαριασμού")
    print("5. Μεταφορτώστε αρχεία μέσω File Manager")
    print("6. Η σελίδα σας: your-site.rf.gd")
    
    print("\n⭐ Απεριόριστα Χαρακτηριστικά:")
    print("   ✅ Απεριόριστος χώρος δίσκου")
    print("   ✅ Απεριόριστο εύρος ζώνης")
    print("   ✅ Δωρεάν subdomain")
    print("   ✅ Χωρίς υποχρεωτικές διαφημίσεις")

def show_quick_publish_tips():
    """Εμφάνιση συμβουλών γρήγορης δημοσίευσης"""
    print("\n" + "="*50)
    print("⚡ ΣΥΜΒΟΥΛΕΣ ΓΡΗΓΟΡΗΣ ΔΗΜΟΣΙΕΥΣΗΣ")
    print("="*50)
    
    print("\n🎯 Για Απόλυτους Αρχάριους:")
    print("1. GitHub Pages - Πιο αξιόπιστο")
    print("2. Netlify - Πιο εύκολο στη χρήση")
    print("3. 000webhost - Χωρίς επαλήθευση απαιτείται")
    
    print("\n📱 Δημοσίευση από Κινητό:")
    print("• Χρησιμοποιήστε τον Chrome browser για όλες τις πλατφόρμες")
    print("• Ενεργοποιήστε το 'Desktop site' στις επιλογές browser")
    print("• Μεταφορτώστε αρχεία απευθείας από τον φάκελο Downloads")
    
    print(f"\n📍 Οι ιστοσελίδες σας βρίσκονται εδώ: {WEBSITES_DIR}")

def main():
    """Κύριο μενού - ΕΚΤΕΤΑΜΕΝΟ"""
    while True:
        print("\n" + "="*40)
        print("🏠 ΔΗΜΙΟΥΡΓΟΣ ΙΣΤΟΣΕΛΙΔΩΝ")
        print("="*40)
        print("1. 🆕 Δημιουργία Ιστοσελίδας")
        print("2. 📝 Επεξεργασία Ιστοσελίδας")
        print("3. 📋 Λίστα Ιστοσελίδων")
        print("4. 🗑️ Διαγραφή Ιστοσελίδας")
        print("5. 🌐 Οδηγός Δημοσίευσης (6 ΔΩΡΕΑΝ Επιλογές)")
        print("6. ⚡ Συμβουλές Γρήγορης Δημοσίευσης")
        print("7. 🚪 Έξοδος")
        print("="*40)
        
        choice = input("Επιλέξτε μια επιλογή (1-7): ").strip()
        
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
            print("\n👋 Ευχαριστούμε που χρησιμοποιήσατε τον Δημιουργό Ιστοσελίδων!")
            print("   Οι ιστοσελίδες σας βρίσκονται στο: Φάκελος Websites στα Downloads")
            break
        else:
            print("❌ Παρακαλώ επιλέξτε 1-7")

if __name__ == "__main__":
    # Έλεγχος πρόσβασης αποθηκευτικού χώρου
    if not os.path.exists(BASE_DIR):
        print("❌ Δεν είναι δυνατή η πρόσβαση στον αποθηκευτικό χώρο του κινητού.")
        print("💡 Παρακαλώ εκτελέστε πρώτα αυτήν την εντολή: termux-setup-storage")
        print("   Στη συνέχεια εκτελέστε ξανά αυτό το script.")
        exit(1)
    
    # Έλεγχος αν ο φάκελος υπάρχει, αν όχι δημιουργία του
    ensure_directory()
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Αντίο! Ευχαριστούμε που χρησιμοποιήσατε τον Δημιουργό Ιστοσελίδων!")
    except Exception as e:
        print(f"\n❌ Ούπς! Κάτι πήγε στραβά: {e}")
        print("   Παρακαλώ δοκιμάστε ξανά ή επανεκκινήστε την εφαρμογή.")