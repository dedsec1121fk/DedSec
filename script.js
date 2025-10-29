document.addEventListener('DOMContentLoaded', () => {
    // --- AUTO-INJECT ADSENSE CODE ---
    function injectAdSense() {
        // Inject main AdSense script in head
        const adSenseScript = document.createElement('script');
        adSenseScript.async = true;
        adSenseScript.src = 'https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6091474574080213';
        adSenseScript.crossOrigin = 'anonymous';
        document.head.appendChild(adSenseScript);
        
        console.log('AdSense script injected in head');
        
        // Inject ad unit in body
        const adUnitContainer = document.createElement('div');
        adUnitContainer.id = 'auto-injected-ad';
        adUnitContainer.style.cssText = `
            margin: 20px auto;
            max-width: 1200px;
            text-align: center;
            padding: 10px;
        `;
        
        adUnitContainer.innerHTML = `
            <ins class="adsbygoogle"
                 style="display:block"
                 data-ad-client="ca-pub-6091474574080213"
                 data-ad-slot="1257213712"
                 data-ad-format="auto"
                 data-full-width-responsive="true"></ins>
            <script>
                 (adsbygoogle = window.adsbygoogle || []).push({});
            </script>
        `;
        
        // Try to insert ad unit at strategic locations
        const mainContent = document.querySelector('main') || document.querySelector('.content') || document.body;
        
        // Insert after main content or at the end of body
        if (mainContent && mainContent !== document.body) {
            mainContent.parentNode.insertBefore(adUnitContainer, mainContent.nextSibling);
        } else {
            // Insert before footer or at the end of body
            const footer = document.querySelector('footer');
            if (footer) {
                document.body.insertBefore(adUnitContainer, footer);
            } else {
                document.body.appendChild(adUnitContainer);
            }
        }
        
        console.log('Ad unit injected in body');
    }

    // Call the function to inject AdSense
    // FIX: Delayed AdSense injection to improve TBT.
    // This runs the ad script 1 second *after* the page is loaded,
    // so it doesn't block the main content from rendering.
    setTimeout(injectAdSense, 1000);

    // --- GLOBAL STATE ---
    let currentLanguage = 'en';
    let usefulInfoSearchIndex = [];
    let usefulInfoFiles = [];
    let isUsefulInfoIndexBuilt = false;
    let usefulInformationLoaded = false;
    let isFetchingUsefulInfo = false;
    
    // Certificate script loading state
    let areCertificateScriptsLoading = false;
    let areCertificateScriptsLoaded = false;

    // --- NAVIGATION FUNCTIONALITY ---
    function initializeNavigation() {
        const burgerMenu = document.getElementById('burger-menu');
        const navMenu = document.getElementById('nav-menu');
        
        if (burgerMenu && navMenu) {
            burgerMenu.addEventListener('click', () => {
                burgerMenu.classList.toggle('active');
                navMenu.classList.toggle('active');
            });
        }

        // Close menu when clicking on a link
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', () => {
                if (burgerMenu && navMenu) {
                    burgerMenu.classList.remove('active');
                    navMenu.classList.remove('active');
                }
            });
        });

        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (burgerMenu && navMenu && navMenu.classList.contains('active')) {
                if (!navMenu.contains(e.target) && !burgerMenu.contains(e.target)) {
                    burgerMenu.classList.remove('active');
                    navMenu.classList.remove('active');
                }
            }
        });
    }

    // --- THEME SWITCHER ---
    function initializeThemeSwitcher() {
        const themeBtn = document.getElementById('nav-theme-switcher');
        const themeIcon = themeBtn?.querySelector('i');
        const themeSpan = themeBtn?.querySelector('span');

        const updateThemeButton = (isLightTheme) => {
            if (!themeBtn || !themeIcon || !themeSpan) return;
            
            if (isLightTheme) {
                themeIcon.classList.remove('fa-moon');
                themeIcon.classList.add('fa-sun');
                themeSpan.setAttribute('data-en', 'Light Theme');
                themeSpan.setAttribute('data-gr', 'Φωτεινό Θέμα');
            } else {
                themeIcon.classList.remove('fa-sun');
                themeIcon.classList.add('fa-moon');
                themeSpan.setAttribute('data-en', 'Dark Theme');
                themeSpan.setAttribute('data-gr', 'Σκοτεινό Θέμα');
            }
            themeSpan.textContent = themeSpan.getAttribute(`data-${currentLanguage}`) || themeSpan.getAttribute('data-en');
        };

        themeBtn?.addEventListener('click', () => {
            document.body.classList.toggle('light-theme');
            const isLight = document.body.classList.contains('light-theme');
            localStorage.setItem('theme', isLight ? 'light' : 'dark');
            updateThemeButton(isLight);
        });

        // Set initial theme
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'light') {
            document.body.classList.add('light-theme');
        }
        updateThemeButton(document.body.classList.contains('light-theme'));
    }

    // --- LANGUAGE SWITCHER ---
    function initializeLanguageSwitcher() {
        const langBtn = document.getElementById('nav-lang-switcher');
        const disclaimerLangBtn = document.getElementById('disclaimer-lang-btn');
        const languageModal = document.getElementById('language-selection-modal');
        
        langBtn?.addEventListener('click', () => {
            if (languageModal) {
                languageModal.classList.add('visible');
            }
        });

        // Language selection button in disclaimer modal
        disclaimerLangBtn?.addEventListener('click', () => {
            if (languageModal) {
                languageModal.classList.add('visible');
            }
        });

        // Language selection
        document.querySelectorAll('.language-button').forEach(button => {
            button.addEventListener('click', () => {
                changeLanguage(button.dataset.lang);
                if (languageModal) {
                    languageModal.classList.remove('visible');
                }
            });
        });
    }

    // --- LANGUAGE MANAGEMENT ---
    window.changeLanguage = (lang) => {
        currentLanguage = lang;
        document.documentElement.lang = lang;
        localStorage.setItem('language', lang);
        
        // Update all elements with data attributes
        document.querySelectorAll('[data-en]').forEach(el => {
            const text = el.getAttribute(`data-${lang}`) || el.getAttribute('data-en');
            const hasDirectText = Array.from(el.childNodes).some(node => 
                node.nodeType === Node.TEXT_NODE && node.textContent.trim().length > 0
            );
            
            if (hasDirectText) {
                Array.from(el.childNodes).forEach(node => {
                    if (node.nodeType === Node.TEXT_NODE && node.textContent.trim().length > 0) {
                        node.textContent = text;
                    }
                });
            } else if (el.children.length === 0) {
                el.textContent = text;
            }
        });

        // Update lang sections
        document.querySelectorAll('[data-lang-section]').forEach(el => {
            el.style.display = el.dataset.langSection === lang ? 'block' : 'none';
            el.classList.toggle('hidden', el.dataset.langSection !== lang);
            if (el.dataset.langSection === lang) {
                el.classList.remove('hidden-by-default');
            }
        });

        // Update navigation links
        document.querySelectorAll('.nav-link').forEach(link => {
            const text = link.getAttribute(`data-${lang}`) || link.textContent;
            if (link.getAttribute('data-en')) {
                link.textContent = text;
            }
        });

        // Update navigation action buttons
        document.querySelectorAll('.nav-action-btn span').forEach(span => {
            const text = span.getAttribute(`data-${lang}`) || span.textContent;
            if (span.getAttribute('data-en')) {
                span.textContent = text;
            }
        });

        // Update search placeholder
        const searchInput = document.getElementById('main-search-input');
        if (searchInput) {
            searchInput.placeholder = lang === 'gr' ? 'Αναζήτηση στο διαδίκτυο...' : 'Search the Web...';
        }

        // Update useful info search placeholder if it exists
        const usefulInfoSearchInput = document.getElementById('useful-info-search-input');
        if (usefulInfoSearchInput) {
            if (!isUsefulInfoIndexBuilt) {
                usefulInfoSearchInput.placeholder = lang === 'gr' ? 'Πατήστε για φόρτωση αναζήτησης...' : 'Click to load search...';
            } else {
                usefulInfoSearchInput.placeholder = lang === 'gr' ? 'Αναζήτηση άρθρων...' : 'Search articles...';
            }
        }

        // Update useful info prompt
        const usefulInfoPrompt = document.getElementById('useful-info-prompt');
        if (usefulInfoPrompt) {
            const text = usefulInfoPrompt.getAttribute(`data-${lang}`) || usefulInfoPrompt.textContent;
            usefulInfoPrompt.textContent = text;
        }

        // Update disclaimer language button
        const disclaimerLangBtn = document.getElementById('disclaimer-lang-btn');
        if (disclaimerLangBtn) {
            const span = disclaimerLangBtn.querySelector('span');
            if (span) {
                const text = span.getAttribute(`data-${lang}`) || span.textContent;
                span.textContent = text;
            }
        }
    };

    // --- DISCLAIMER FUNCTIONALITY ---
    function initializeDisclaimer() {
        const disclaimerModal = document.getElementById('disclaimer-modal');
        const acceptBtn = document.getElementById('accept-disclaimer');
        const declineBtn = document.getElementById('decline-disclaimer');

        // Check if user has already accepted the disclaimer
        const disclaimerAccepted = localStorage.getItem('disclaimerAccepted');

        if (!disclaimerAccepted) {
            // Show disclaimer modal immediately on page load
            setTimeout(() => {
                if (disclaimerModal) {
                    disclaimerModal.classList.add('visible');
                }
            }, 500);
        }

        // Handle accept button
        acceptBtn?.addEventListener('click', () => {
            localStorage.setItem('disclaimerAccepted', 'true');
            if (disclaimerModal) {
                disclaimerModal.classList.remove('visible');
            }
            console.log('Disclaimer accepted');
        });

        // Handle decline button - redirect to Google homepage
        declineBtn?.addEventListener('click', () => {
            window.location.href = 'https://www.google.com';
        });

        // Prevent closing the disclaimer modal by clicking outside
        // This listener is still useful to stop propagation if needed,
        // but the main closing logic is now handled in initializeModals()
        disclaimerModal?.addEventListener('click', (e) => {
            if (e.target === disclaimerModal) {
                // Don't allow closing by clicking outside - force user to make a choice
                return;
            }
        });
    }
    
    // --- HELPER FUNCTIONS (Security & Performance) ---

    /**
     * 🔒 SECURITY: Sanitizes string inputs to prevent XSS.
     * Removes < and > characters.
     */
    function sanitizeInput(str) {
        if (!str) return '';
        return str.replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    /**
     * ⚡ PERFORMANCE: Asynchronously loads a script.
     * Returns a promise that resolves when the script is loaded.
     */
    function loadScript(src) {
        return new Promise((resolve, reject) => {
            if (document.querySelector(`script[src="${src}"]`)) {
                resolve(); // Already loaded or loading
                return;
            }
            const script = document.createElement('script');
            script.src = src;
            script.onload = () => resolve();
            script.onerror = () => reject(new Error(`Failed to load script: ${src}`));
            document.head.appendChild(script);
        });
    }

    // --- CERTIFICATE FUNCTIONALITY ---
    const certificateTranslations = {
        en: {
            title: 'Certificate of Participation',
            subtitle: 'DedSec Project - 1 Year Anniversary',
            certifies: 'This certifies that',
            participated: 'participated in the 1 Year Anniversary version of the DedSec Project website.',
            event: 'Event held October 20 - October 31, 2025.',
            issuedTo: 'Issued To',
            age: 'Age',
            location: 'Location',
            dateIssued: 'Date Issued',
            team: 'DedSec Project Team'
        },
        gr: {
            title: 'Πιστοποιητικό Συμμετοχής',
            subtitle: 'DedSec Project - 1η Επέτειος',
            certifies: 'Το παρόν πιστοποιεί ότι',
            participated: 'συμμετείχε στην έκδοση της 1ης επετείου της ιστοσελίδας του DedSec Project.',
            event: 'Η εκδήλωση πραγματοποιήθηκε από 20 Οκτωβρίου έως 31 Οκτωβρίου 2025.',
            issuedTo: 'Εκδόθηκε σε',
            age: 'Ηλικία',
            location: 'Τοποθεσία',
            dateIssued: 'Ημερομηνία Έκδοσης',
            team: 'Ομάδα DedSec Project'
        }
    };
    
    /**
     * ⚡ PERFORMANCE: Lazily loads certificate scripts and opens the modal.
     */
    async function openCertificateModal() {
        const certificateModal = document.getElementById('certificate-modal');
        const certificateBtn = document.getElementById('certificate-btn');
        if (!certificateModal || !certificateBtn) return;

        if (areCertificateScriptsLoaded) {
            certificateModal.classList.add('visible');
            return;
        }

        if (areCertificateScriptsLoading) {
            return; // Prevent double-clicks
        }

        areCertificateScriptsLoading = true;
        const btnSpan = certificateBtn.querySelector('span');
        const originalBtnText = btnSpan.textContent;
        btnSpan.textContent = currentLanguage === 'gr' ? 'Φόρτωση...' : 'Loading...';
        certificateBtn.disabled = true;

        try {
            await Promise.all([
                loadScript('https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js'),
                loadScript('https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js')
            ]);
            areCertificateScriptsLoaded = true;
            console.log('Certificate scripts loaded successfully.');
            certificateModal.classList.add('visible');
        } catch (error) {
            console.error('Failed to load certificate scripts:', error);
            alert(currentLanguage === 'gr' ? 'Σφάλμα φόρτωσης. Παρακαλώ δοκιμάστε ξανά.' : 'Error loading scripts. Please try again.');
        } finally {
            areCertificateScriptsLoading = false;
            btnSpan.textContent = originalBtnText;
            certificateBtn.disabled = false;
        }
    }

    function initializeCertificateFeature() {
        const certificateBtn = document.getElementById('certificate-btn');
        const generateCertificateBtn = document.getElementById('generate-certificate');
        const certificateForm = document.getElementById('certificate-form');
        const certificateModal = document.getElementById('certificate-modal');
        
        if (certificateBtn) {
            // Modified to use the new lazy-loading function
            certificateBtn.addEventListener('click', openCertificateModal);
        }

        if (generateCertificateBtn && certificateForm) {
            generateCertificateBtn.style.background = 'linear-gradient(135deg, var(--nm-accent), var(--nm-accent-hover))';
            generateCertificateBtn.style.borderColor = 'var(--nm-accent)';
            generateCertificateBtn.style.color = '#000000';

            generateCertificateBtn.addEventListener('mouseenter', () => {
                if (!generateCertificateBtn.querySelector('.fa-check')) {
                    generateCertificateBtn.style.background = 'linear-gradient(135deg, var(--nm-accent-hover), var(--nm-accent))';
                }
            });

            generateCertificateBtn.addEventListener('mouseleave', () => {
                if (!generateCertificateBtn.querySelector('.fa-check')) {
                    generateCertificateBtn.style.background = 'linear-gradient(135deg, var(--nm-accent), var(--nm-accent-hover))';
                }
            });

            generateCertificateBtn.addEventListener('click', generateCertificate);
        }

        // Close certificate modal
        if (certificateModal) {
            const closeModal = () => {
                certificateModal.classList.remove('visible');
                certificateForm?.reset();
            };
            
            certificateModal.addEventListener('click', e => {
                if (e.target === certificateModal) closeModal();
            });
            
            certificateModal.querySelector('.close-modal')?.addEventListener('click', closeModal);
        }
    }

    async function generateCertificate() {
        const form = document.getElementById('certificate-form');
        
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }

        // ⚡ PERFORMANCE: Ensure scripts are loaded before trying to use them
        if (!areCertificateScriptsLoaded) {
            alert(currentLanguage === 'gr' ? 'Οι βιβλιοθήκες πιστοποιητικού δεν έχουν φορτωθεί. Παρακαλώ κλείστε και ανοίξτε ξανά το παράθυρο.' : 'Certificate libraries not loaded. Please close and re-open the modal.');
            return;
        }

        // 🔒 SECURITY: Check if generator functions are available (post-load)
        if (typeof window.jspdf === 'undefined' || typeof window.jspdf.jsPDF === 'undefined' || typeof window.html2canvas === 'undefined') {
            alert('Error: Certificate generator failed to load. Please check your internet connection and try again.');
            return;
        }

        const formData = new FormData(form);
        
        // 🔒 SECURITY: Sanitize all string inputs
        const firstName = sanitizeInput(formData.get('firstName'));
        const lastName = sanitizeInput(formData.get('lastName'));
        const age = formData.get('age'); // Age is a number, no sanitization needed
        const country = sanitizeInput(formData.get('country'));
        const city = sanitizeInput(formData.get('city'));
        
        // Check if sanitization blocked a required field
        if (!firstName || !lastName || !country || !city) {
            alert(currentLanguage === 'gr' ? 'Τα πεδία δεν μπορούν να περιέχουν ειδικούς χαρακτήρες όπως < ή >.' : 'Fields cannot contain special characters like < or >.');
            form.reportValidity(); // This will highlight the empty (post-sanitization) fields
            return;
        }

        generateCertificateWithCanvas(firstName, lastName, age, country, city);
    }

    function generateCertificateWithCanvas(firstName, lastName, age, country, city) {
        try {
            const tempCertificate = createCertificateHTML(firstName, lastName, age, country, city);
            document.body.appendChild(tempCertificate);

            // Use the now-loaded html2canvas
            window.html2canvas(tempCertificate, {
                scale: 2,
                useCORS: true,
                backgroundColor: '#ffffff'
            }).then(canvas => {
                document.body.removeChild(tempCertificate);
                const imgData = canvas.toDataURL('image/png');
                
                // Use the now-loaded jspdf
                const { jsPDF } = window.jspdf;
                const doc = new jsPDF('landscape', 'mm', 'a4');
                
                const pageWidth = doc.internal.pageSize.getWidth();
                const pageHeight = doc.internal.pageSize.getHeight();
                
                doc.addImage(imgData, 'PNG', 0, 0, pageWidth, pageHeight);
                
                const fileName = currentLanguage === 'gr' 
                    ? `Πιστοποιητικό_Επετείου_DedSec_${firstName}_${lastName}.pdf`
                    : `DedSec_Anniversary_Certificate_${firstName}_${lastName}.pdf`;
                
                doc.save(fileName);
                showCertificateSuccess(firstName);
            }).catch(error => {
                console.error("Error generating certificate:", error);
                if (document.body.contains(tempCertificate)) {
                    document.body.removeChild(tempCertificate);
                }
                alert("An error occurred while generating the certificate. Please try again.");
            });

        } catch (error) {
            console.error("Error in certificate generation:", error);
            alert("An error occurred while generating the certificate. Please try again.");
        }
    }

    function createCertificateHTML(firstName, lastName, age, country, city) {
        const translations = certificateTranslations[currentLanguage];
        const fullName = `${firstName} ${lastName}`;
        const today = new Date().toLocaleDateString(currentLanguage === 'gr' ? 'el-GR' : 'en-US', { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
        });

        const certificateDiv = document.createElement('div');
        certificateDiv.style.cssText = `
            position: fixed;
            top: -10000px;
            left: -10000px;
            width: 1123px;
            height: 794px;
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            border: 4px solid #FFD700;
            border-radius: 15px;
            padding: 40px 30px;
            color: #ffffff;
            font-family: 'Noto Serif', serif;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
            box-sizing: border-box;
        `;

        certificateDiv.innerHTML = `
            <div style="margin-bottom: 30px;">
                <div style="font-size: 3rem; color: #FFD700; margin-bottom: 15px;">
                    <i class="fas fa-shield-alt"></i>
                </div>
                <h1 style="font-size: 2.2rem; color: #FFD700; margin: 0 0 10px 0; font-weight: bold; text-transform: uppercase; letter-spacing: 2px; font-family: 'Noto Serif', serif;">
                    ${translations.title}
                </h1>
                <h2 style="font-size: 1.5rem; color: #9966FF; margin: 0; font-weight: normal; font-style: italic; font-family: 'Noto Serif', serif;">
                    ${translations.subtitle}
                </h2>
            </div>
            
            <div style="margin: 30px 0;">
                <p style="font-size: 1.1rem; margin: 15px 0; line-height: 1.6; font-family: 'Noto Serif', serif;">
                    ${translations.certifies}
                </p>
                <div style="font-size: 2.5rem; font-weight: bold; color: #FFD700; margin: 20px 0; padding: 10px; border-bottom: 2px solid #FFD700; border-top: 2px solid #FFD700; font-family: 'Noto Serif', serif; text-transform: uppercase; letter-spacing: 1px;">
                    ${fullName}
                </div>
                <p style="font-size: 1.1rem; margin: 15px 0; line-height: 1.6; font-family: 'Noto Serif', serif;">
                    ${translations.participated}
                </p>
                <p style="font-size: 1.1rem; margin: 15px 0; line-height: 1.6; font-family: 'Noto Serif', serif;">
                    ${translations.event}
                </p>
            </div>
            
            <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-top: 40px; padding-top: 20px; border-top: 1px solid #3A4A5E;">
                <div style="text-align: left;">
                    <div style="margin: 8px 0; font-size: 0.9rem;">
                        <span style="font-weight: bold; color: #FFD700;">${translations.issuedTo}:</span> ${fullName}
                    </div>
                    <div style="margin: 8px 0; font-size: 0.9rem;">
                        <span style="font-weight: bold; color: #FFD700;">${translations.age}:</span> ${age}
                    </div>
                    <div style="margin: 8px 0; font-size: 0.9rem;">
                        <span style="font-weight: bold; color: #FFD700;">${translations.location}:</span> ${city}, ${country}
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="margin: 8px 0; font-size: 0.9rem;">
                        <span style="font-weight: bold; color: #FFD700;">${translations.dateIssued}:</span> ${today}
                    </div>
                    <div style="text-align: center; margin-top: 10px;">
                        <div style="width: 200px; height: 1px; background: #ffffff; margin: 0 auto 10px auto;"></div>
                        <span style="font-style: italic; color: #7A8899; font-family: 'Noto Serif', serif;">
                            ${translations.team}
                        </span>
                    </div>
                </div>
            </div>
        `;

        return certificateDiv;
    }

    function showCertificateSuccess(firstName) {
        const generateBtn = document.getElementById('generate-certificate');
        const originalHTML = generateBtn.innerHTML;
        
        generateBtn.innerHTML = `
            <i class="fas fa-check"></i>
            <span data-en="Certificate Downloaded!" data-gr="Το Πιστοποιητικό Λήφθηκε!">Certificate Downloaded!</span>
        `;
        generateBtn.style.background = '#FFFFFF';
        generateBtn.style.borderColor = 'var(--nm-accent)';
        generateBtn.style.color = 'var(--nm-accent)';
        
        changeLanguage(currentLanguage);
        
        setTimeout(() => {
            generateBtn.innerHTML = originalHTML;
            generateBtn.style.background = 'linear-gradient(135deg, var(--nm-accent), var(--nm-accent-hover))';
            generateBtn.style.borderColor = 'var(--nm-accent)';
            generateBtn.style.color = '#000000';
            changeLanguage(currentLanguage);
        }, 3000);
    }

    // --- SEARCH FUNCTIONALITY ---
    function initializeWebSearchSuggestions() {
        const searchInput = document.getElementById('main-search-input');
        const suggestionsContainer = document.getElementById('search-suggestions-container');
        const searchForm = document.getElementById('main-search-form');
        if (!searchInput || !suggestionsContainer || !searchForm) return;

        const debounce = (func, delay) => {
            let timeoutId;
            return (...args) => {
                clearTimeout(timeoutId);
                timeoutId = setTimeout(() => {
                    func.apply(this, args);
                }, delay);
            };
        };

        const fetchSuggestions = (query) => {
            const oldScript = document.getElementById('jsonp-script');
            if (oldScript) {
                oldScript.remove();
            }

            const script = document.createElement('script');
            script.id = 'jsonp-script';
            script.src = `https://suggestqueries.google.com/complete/search?client=chrome&q=${encodeURIComponent(query)}&hl=${currentLanguage}&callback=handleGoogleSuggestions`;
            
            script.onerror = () => {
                console.error("Error loading Google suggestions.");
                suggestionsContainer.classList.add('hidden');
                suggestionsContainer.innerHTML = '';
            };
            
            document.head.appendChild(script);
        };

        const debouncedFetchSuggestions = debounce(fetchSuggestions, 250);

        window.handleGoogleSuggestions = (data) => {
            suggestionsContainer.innerHTML = '';
            const suggestions = data[1];

            if (suggestions && Array.isArray(suggestions) && suggestions.length > 0) {
                suggestions.slice(0, 5).forEach(suggestion => {
                    const itemEl = document.createElement('div');
                    itemEl.classList.add('search-result-item');
                    itemEl.textContent = suggestion;
                    
                    itemEl.addEventListener('click', () => {
                        searchInput.value = suggestion;
                        suggestionsContainer.classList.add('hidden');
                        searchForm.submit();
                        setTimeout(() => { searchInput.value = ''; }, 100);
                    });
                    suggestionsContainer.appendChild(itemEl);
                });
                suggestionsContainer.classList.remove('hidden');
            } else {
                suggestionsContainer.classList.add('hidden');
            }
        };

        searchInput.addEventListener('input', () => {
            const query = searchInput.value.trim();
            if (query.length < 1) {
                suggestionsContainer.classList.add('hidden');
                suggestionsContainer.innerHTML = '';
                return;
            }
            debouncedFetchSuggestions(query);
        });

        document.addEventListener('click', (e) => {
            if (!searchForm.contains(e.target)) {
                suggestionsContainer.classList.add('hidden');
            }
        });

        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                suggestionsContainer.classList.add('hidden');
            }
        });
    }

    // --- MODAL MANAGEMENT ---
    function initializeModals() {
        document.querySelectorAll('.modal-overlay').forEach(modal => {
            const closeModalBtn = modal.querySelector('.close-modal');
            const closeModal = () => {
                modal.classList.remove('visible');
            };
            
            modal.addEventListener('click', e => {
                // Check if the target is the modal overlay itself
                // AND if the modal is NOT the disclaimer modal
                if (e.target === modal && modal.id !== 'disclaimer-modal') {
                    closeModal();
                }
            });
            
            closeModalBtn?.addEventListener('click', closeModal);
        });
    }

    // --- CAROUSEL FUNCTIONALITY ---
    function initializeCarousels() {
        const carousels = document.querySelectorAll('.gym-carousel');
        
        carousels.forEach(carousel => {
            const images = carousel.querySelectorAll('.gym-clothing-images img');
            const prevBtn = carousel.querySelector('.carousel-btn.prev');
            const nextBtn = carousel.querySelector('.carousel-btn.next');
            
            if (images.length > 0 && prevBtn && nextBtn) {
                let currentIndex = 0;
                
                const showImage = (index) => {
                    images.forEach((img, i) => {
                        img.classList.toggle('active', i === index);
                    });
                };
                
                prevBtn.addEventListener('click', () => {
                    currentIndex = (currentIndex > 0) ? currentIndex - 1 : images.length - 1;
                    showImage(currentIndex);
                });
                
                nextBtn.addEventListener('click', () => {
                    currentIndex = (currentIndex < images.length - 1) ? currentIndex + 1 : 0;
                    showImage(currentIndex);
                });
                
                showImage(0);
            }
        });
    }

    // --- COPY FUNCTIONALITY ---
    function initializeCopyButtons() {
        // Make copy function globally accessible
        window.copyToClipboard = (button, targetId) => {
            const codeElement = document.getElementById(targetId);
            if (!codeElement || !navigator.clipboard) {
                console.warn('Clipboard API not available or element not found.');
                button.textContent = 'Error';
                setTimeout(() => { 
                    button.textContent = (currentLanguage === 'gr') ? 'Αντιγραφή' : 'Copy'; 
                }, 1500);
                return;
            }
            
            const originalText = button.textContent;
            navigator.clipboard.writeText(codeElement.innerText).then(() => {
                button.textContent = (currentLanguage === 'gr') ? 'Αντιγράφηκε!' : 'Copied!';
                setTimeout(() => { button.textContent = originalText; }, 1500);
            }).catch(err => {
                console.error('Failed to copy text: ', err);
                button.textContent = 'Failed!';
                setTimeout(() => { button.textContent = originalText; }, 1500);
            });
        };

        // Attach copy functionality to existing buttons
        document.querySelectorAll('.copy-btn').forEach(btn => {
            const targetId = btn.getAttribute('onclick')?.match(/'(.*?)'/)?.[1];
            if (targetId) {
                btn.addEventListener('click', () => {
                    window.copyToClipboard(btn, targetId);
                });
            }
        });
    }

    // --- TOOL CATEGORIES FUNCTIONALITY ---
    function initializeToolCategories() {
        console.log('Initializing tool categories...');
        
        // Close all categories and tool items by default
        document.querySelectorAll('.category, .tool-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // Category toggle functionality
        document.querySelectorAll('.category-header').forEach(header => {
            header.addEventListener('click', function() {
                console.log('Category header clicked');
                const category = this.parentElement;
                const wasActive = category.classList.contains('active');
                
                // Close all categories first
                document.querySelectorAll('.category').forEach(otherCategory => {
                    otherCategory.classList.remove('active');
                });
                
                // Open the clicked category if it was not active
                if (!wasActive) {
                    category.classList.add('active');
                }
            });
        });
        
        // Tool item toggle functionality
        document.querySelectorAll('.tool-header').forEach(header => {
            header.addEventListener('click', function(e) {
                console.log('Tool header clicked');
                // Prevent the category from closing when clicking on a tool
                e.stopPropagation();
                
                const toolItem = this.parentElement;
                const wasActive = toolItem.classList.contains('active');
                
                // Close all other tool items in the same category
                const category = toolItem.closest('.category');
                if (category) {
                    category.querySelectorAll('.tool-item').forEach(otherTool => {
                        if (otherTool !== toolItem) {
                            otherTool.classList.remove('active');
                        }
                    });
                }
                
                // Toggle the clicked tool item
                if (!wasActive) {
                    toolItem.classList.add('active');
                } else {
                    toolItem.classList.remove('active');
                }
            });
        });
    }

    // --- USEFUL INFORMATION FUNCTIONALITY ---
    const SearchEngine = {
        idfMaps: {},

        tokenize(text, lang) {
            if (!text) return [];
            return text
                .toLowerCase()
                .replace(/[.,/#!$%\^&\*;:{}=\-_`~()]/g, "")
                .split(/\s+/)
                .filter(word => word.length > 1);
        },

        preprocessItem(item) {
            return {
                ...item,
                titleTokens: this.tokenize(item.title, item.lang),
                textTokens: this.tokenize(item.text, item.lang)
            };
        },

        calculateIdf(indexName, index) {
            const docFreq = new Map();
            const totalDocs = index.length;
            if (totalDocs === 0) return;

            index.forEach(item => {
                const seenTokens = new Set([...item.titleTokens, ...item.textTokens]);
                seenTokens.forEach(token => {
                    docFreq.set(token, (docFreq.get(token) || 0) + 1);
                });
            });

            const idfMap = new Map();
            for (const [token, freq] of docFreq.entries()) {
                idfMap.set(token, Math.log(totalDocs / (1 + freq)));
            }
            this.idfMaps[indexName] = idfMap;
        },

        _getNgrams(word, n = 2) {
            const ngrams = new Set();
            if (!word || word.length < n) return ngrams;
            for (let i = 0; i <= word.length - n; i++) {
                ngrams.add(word.substring(i, i + n));
            }
            return ngrams;
        },

        _calculateSimilarity(word1, word2) {
            if (!word1 || !word2) return 0;
            const ngrams1 = this._getNgrams(word1);
            const ngrams2 = this._getNgrams(word2);
            const intersection = new Set([...ngrams1].filter(x => ngrams2.has(x)));
            const union = ngrams1.size + ngrams2.size - intersection.size;
            return union === 0 ? 0 : intersection.size / union;
        },

        search(query, index, lang, indexName) {
            const queryTokens = this.tokenize(query, lang);
            if (queryTokens.length === 0) return [];
            const idfMap = this.idfMaps[indexName] || new Map();

            const scoredResults = index
                .filter(item => item.lang === lang)
                .map(item => {
                    let score = 0;
                    const foundTokens = new Set();

                    queryTokens.forEach(qToken => {
                        const idf = idfMap.get(qToken) || 0.5;
                        let tokenFound = false;

                        let exactTitleMatches = item.titleTokens.filter(t => t === qToken).length;
                        if (exactTitleMatches > 0) {
                            score += exactTitleMatches * 10 * idf;
                            tokenFound = true;
                        }
                        let exactTextMatches = item.textTokens.filter(t => t === qToken).length;
                        if (exactTextMatches > 0) {
                            score += exactTextMatches * 2 * idf;
                            tokenFound = true;
                        }
                        if(tokenFound) foundTokens.add(qToken);

                        if (!tokenFound) {
                            let bestSimilarity = 0;
                            const allItemTokens = [...item.titleTokens, ...item.textTokens];
                            allItemTokens.forEach(tToken => {
                                const similarity = this._calculateSimilarity(qToken, tToken);
                                if (similarity > bestSimilarity) bestSimilarity = similarity;
                            });
                            
                            if (bestSimilarity > 0.7) {
                               score += bestSimilarity * 5 * idf;
                               foundTokens.add(qToken);
                            }
                        }
                    });

                    if (foundTokens.size === queryTokens.length && queryTokens.length > 1) score *= 1.5;
                    if (item.text.toLowerCase().includes(query.toLowerCase().trim())) score *= 1.2;
                    score *= item.weight || 1;

                    return { ...item, score };
                });

            return scoredResults
                .filter(item => item.score > 0)
                .sort((a, b) => b.score - a.score);
        },
        
        generateSnippet(text, query, lang) {
            const queryTokens = this.tokenize(query, lang);
            if (queryTokens.length === 0) return text.substring(0, 120) + (text.length > 120 ? '...' : '');
    
            let bestIndex = -1;
            const lowerCaseText = text.toLowerCase();
    
            for (const token of queryTokens) {
                const index = lowerCaseText.indexOf(token);
                if (index !== -1) {
                    bestIndex = index;
                    break; 
                }
            }
            
            if (bestIndex === -1) {
                 return text.substring(0, 120) + (text.length > 120 ? '...' : '');
            }
    
            const snippetLength = 120;
            const start = Math.max(0, bestIndex - Math.round(snippetLength / 4));
            const end = Math.min(text.length, start + snippetLength);
            
            let snippet = text.substring(start, end);
            if (start > 0) snippet = '... ' + snippet;
            if (end < text.length) snippet = snippet + ' ...';
    
            return snippet;
        },

        highlight(snippet, query, lang) {
            const queryTokens = this.tokenize(query, lang);
            if (queryTokens.length === 0) return snippet;
            const regex = new RegExp(`(${queryTokens.join('|')})`, 'gi');
            return snippet.replace(regex, '<strong>$1</strong>');
        }
    };

    async function buildUsefulInfoSearchIndex(progressBar, progressText) {
        if (isUsefulInfoIndexBuilt || usefulInfoFiles.length === 0) return;

        let filesLoaded = 0;
        const totalFiles = usefulInfoFiles.length;

        const indexPromises = usefulInfoFiles.map(async (file) => {
            try {
                const response = await fetch(file.download_url);
                if (!response.ok) return;
                const htmlContent = await response.text();
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = htmlContent;

                let fallbackTitleEN = file.name.replace(/\.html$/, '').replace(/^\d+_/, '').replace(/_/g, ' ');
                let fallbackTitleGR = fallbackTitleEN;

                const titleRegex = /(.+?)_\((.+?)\)/;
                const match = file.name.match(titleRegex);

                if (match && match[1] && match[2]) {
                    fallbackTitleEN = match[1].replace(/_/g, ' ').trim();
                    fallbackTitleGR = match[2].replace(/_/g, ' ').trim();
                }

                const titlesContainer = tempDiv.querySelector('#article-titles');
                const titleEN = titlesContainer?.querySelector('[data-lang="en"]')?.textContent.trim() || fallbackTitleEN;
                const titleGR = titlesContainer?.querySelector('[data-lang="gr"]')?.textContent.trim() || fallbackTitleGR;

                tempDiv.querySelectorAll('[data-lang-section]').forEach(section => {
                    const lang = section.dataset.langSection;
                    const articleTitle = lang === 'gr' ? titleGR : titleEN;
                    section.querySelectorAll('h3, h4, p, li, b, code').forEach(el => {
                        const text = el.textContent.trim().replace(/\s\s+/g, ' ');
                        if (text.length > 5) {
                            const item = {
                                lang,
                                title: articleTitle,
                                text,
                                url: file.download_url,
                                weight: (el.tagName === 'H3' ? 5 : 1)
                            };
                            usefulInfoSearchIndex.push(SearchEngine.preprocessItem(item));
                        }
                    });
                });
            } catch (e) {
                console.error(`Failed to index file: ${file.name}`, e);
            } finally {
                filesLoaded++;
                const progress = (filesLoaded / totalFiles) * 100;
                if (progressBar) progressBar.style.width = `${progress}%`;
                if (progressText) progressText.textContent = `${Math.round(progress)}%`;
            }
        });

        await Promise.all(indexPromises);
        SearchEngine.calculateIdf('usefulInfo', usefulInfoSearchIndex);
        isUsefulInfoIndexBuilt = true;
    }

    function updateUsefulInfoButtonTitles() {
        const titleMap = new Map();

        usefulInfoSearchIndex.forEach(item => {
            if (!titleMap.has(item.url)) {
                titleMap.set(item.url, {});
            }
            const langTitles = titleMap.get(item.url);
            if (!langTitles[item.lang]) {
                langTitles[item.lang] = item.title;
            }
        });

        document.querySelectorAll('#useful-information-nav .app-icon[data-url]').forEach(button => {
            const url = button.dataset.url;
            const titles = titleMap.get(url);
            if (titles) {
                const buttonSpan = button.querySelector('span');
                if(buttonSpan) {
                   buttonSpan.setAttribute('data-en', titles.en || '');
                   buttonSpan.setAttribute('data-gr', titles.gr || titles.en || '');
                   buttonSpan.textContent = (currentLanguage === 'gr' ? titles.gr : titles.en) || titles.en || buttonSpan.textContent;
                }
            }
        });
    }

    function initializeUsefulInfoSearch() {
        const searchInput = document.getElementById('useful-info-search-input');
        const resultsContainer = document.getElementById('useful-info-results-container');
        const navContainer = document.getElementById('useful-information-nav');
        if (!searchInput || !resultsContainer || !navContainer) return;

        const progressBarContainer = document.createElement('div');
        progressBarContainer.className = 'progress-bar-container';
        
        const progressBar = document.createElement('div');
        progressBar.className = 'progress-bar';

        const progressText = document.createElement('span');
        progressText.className = 'progress-bar-text';
        progressText.textContent = '0%';

        progressBarContainer.appendChild(progressBar);
        progressBarContainer.appendChild(progressText);
        navContainer.parentNode.insertBefore(progressBarContainer, navContainer);

        const showNav = (shouldShow) => {
            navContainer.querySelectorAll('.app-icon').forEach(article => {
                article.style.display = shouldShow ? 'flex' : 'none';
            });
        };

        searchInput.addEventListener('focus', async () => {
            if (isUsefulInfoIndexBuilt) return;

            searchInput.placeholder = currentLanguage === 'gr' ? 'Ευρετηρίαση άρθρων...' : 'Indexing articles...';
            searchInput.disabled = true;

            progressBarContainer.style.display = 'block';
            progressBar.style.width = '0%';

            await buildUsefulInfoSearchIndex(progressBar, progressText);
            
            updateUsefulInfoButtonTitles();

            setTimeout(() => {
                progressBarContainer.style.display = 'none';
            }, 500);

            searchInput.disabled = false;
            searchInput.placeholder = currentLanguage === 'gr' ? 'Αναζήτηση άρθρων...' : 'Search articles...';
            searchInput.focus();
        }, { once: true });

        searchInput.addEventListener('input', () => {
            const query = searchInput.value.trim();
            resultsContainer.innerHTML = '';

            if (!isUsefulInfoIndexBuilt || query.length < 2) {
                resultsContainer.classList.add('hidden');
                showNav(true);
                return;
            }
            
            showNav(false);

            const results = SearchEngine.search(query, usefulInfoSearchIndex, currentLanguage, 'usefulInfo');

            if (results.length > 0) {
                results.slice(0, 7).forEach(result => {
                    const itemEl = document.createElement('div');
                    itemEl.classList.add('search-result-item');
                    const snippet = SearchEngine.generateSnippet(result.text, query, currentLanguage);
                    const highlightedSnippet = SearchEngine.highlight(snippet, query, currentLanguage);

                    itemEl.innerHTML = `${highlightedSnippet} <small>${result.title}</small>`;
                    itemEl.addEventListener('click', () => {
                        searchInput.value = '';
                        resultsContainer.classList.add('hidden');
                        loadInformationContent(result.url, result.title, result.text);
                    });
                    resultsContainer.appendChild(itemEl);
                });
                resultsContainer.classList.remove('hidden');
            } else {
                resultsContainer.classList.add('hidden');
                showNav(true);
            }
        });
    }

    async function fetchUsefulInformation() {
        if (usefulInformationLoaded || isFetchingUsefulInfo) return;
        isFetchingUsefulInfo = true;
        const navContainer = document.getElementById('useful-information-nav');
        const GITHUB_API_URL = 'https://api.github.com/repos/dedsec1121fk/dedsec1121fk.github.io/contents/Useful_Information';
        navContainer.innerHTML = `<p>${currentLanguage === 'gr' ? 'Φόρτωση...' : 'Loading...'}</p>`;
        
        try {
            const response = await fetch(GITHUB_API_URL);
            if (!response.ok) throw new Error(`GitHub API error: ${response.status}`);
            const files = await response.json();
            usefulInfoFiles = files.filter(file => file.type === 'file' && file.name.endsWith('.html'));
            
            navContainer.innerHTML = '';
            if (usefulInfoFiles.length === 0) {
                 navContainer.innerHTML = `<p>${currentLanguage === 'gr' ? 'Δεν βρέθηκαν πληροφορίες.' : 'No information found.'}</p>`;
                 return;
            }
            
            usefulInfoFiles.forEach(file => {
                let titleEN = file.name.replace(/\.html$/, '').replace(/^\d+_/, '').replace(/_/g, ' ');
                let titleGR = titleEN; 
    
                const titleRegex = /(.+?)_\((.+?)\)/;
                const match = file.name.match(titleRegex);
    
                if (match && match[1] && match[2]) {
                    titleEN = match[1].replace(/_/g, ' ').trim();
                    titleGR = match[2].replace(/_/g, ' ').trim();
                }
    
                const button = document.createElement('button');
                button.className = 'app-icon';
                button.dataset.url = file.download_url;
                
                const initialTitle = currentLanguage === 'gr' ? titleGR : titleEN;
                button.innerHTML = `<i class="fas fa-book-open"></i><span data-en="${titleEN}" data-gr="${titleGR}">${initialTitle}</span>`;
                
                button.addEventListener('click', () => {
                    const span = button.querySelector('span');
                    const modalTitle = (currentLanguage === 'gr' ? span.getAttribute('data-gr') : span.getAttribute('data-en')) || titleEN;
                    loadInformationContent(file.download_url, modalTitle);
                });
                navContainer.appendChild(button);
            });
            usefulInformationLoaded = true;
        } catch (error) {
            console.error('Failed to fetch useful information:', error);
            navContainer.innerHTML = `<p style="color: var(--nm-danger);">${currentLanguage === 'gr' ? 'Αποτυχία φόρτωσης.' : 'Failed to load.'}</p>`;
        } finally {
            isFetchingUsefulInfo = false;
        }
    }

    function createAndShowArticleModal(title, htmlContent, textToHighlight = null) {
        document.querySelectorAll('.article-modal-overlay').forEach(modal => modal.remove());
        const modalOverlay = document.createElement('div');
        modalOverlay.className = 'modal-overlay article-modal-overlay'; 
        modalOverlay.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>${title}</h2>
                    <button class="close-modal">&times;</button>
                </div>
                <div class="modal-body">${htmlContent}</div>
            </div>`;
        document.body.appendChild(modalOverlay);

        // Initialize copy buttons in the new modal
        let dynamicCodeIdCounter = 0;
        const codeContainers = modalOverlay.querySelectorAll('.code-container');
        codeContainers.forEach(container => {
            const copyBtn = container.querySelector('.copy-btn');
            const codeEl = container.querySelector('code');

            if (copyBtn && codeEl) {
                if (!codeEl.id) {
                    const uniqueId = `dynamic-code-${Date.now()}-${dynamicCodeIdCounter++}`;
                    codeEl.id = uniqueId;
                }
                
                copyBtn.addEventListener('click', () => {
                    window.copyToClipboard(copyBtn, codeEl.id);
                });
            }
        });
        
        setTimeout(() => modalOverlay.classList.add('visible'), 10);
        changeLanguage(currentLanguage);
    
        if (textToHighlight) {
            setTimeout(() => {
                const modalBody = modalOverlay.querySelector('.modal-body');
                const allElements = modalBody.querySelectorAll('p, li, h3, h4, b, code, .tip, .note');
                const targetElement = Array.from(allElements).find(el => el.textContent.trim().replace(/\s\s+/g, ' ') === textToHighlight.trim());
                if (targetElement) {
                    modalBody.scrollTo({ top: targetElement.offsetTop - 50, behavior: 'smooth' });
                    targetElement.classList.add('content-highlight');
                    setTimeout(() => targetElement.classList.remove('content-highlight'), 2500);
                }
            }, 150);
        }
        
        const closeModal = () => {
            modalOverlay.classList.remove('visible');
            modalOverlay.addEventListener('transitionend', () => modalOverlay.remove(), { once: true });
            
            const searchInput = document.getElementById('useful-info-search-input');
            if (searchInput) searchInput.value = '';
            
            const navContainer = document.getElementById('useful-information-nav');
            if (navContainer) {
                navContainer.querySelectorAll('.app-icon').forEach(article => {
                    article.style.display = 'flex';
                });
            }
        };

        modalOverlay.addEventListener('click', (e) => {
            if (e.target === modalOverlay) closeModal();
        });
        modalOverlay.querySelector('.close-modal').addEventListener('click', closeModal);
    }

    async function loadInformationContent(url, title, textToHighlight = null) {
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error(`Fetch failed: ${response.status}`);
            const htmlContent = await response.text();
            createAndShowArticleModal(title, htmlContent, textToHighlight);
        } catch (error) {
            console.error('Failed to load content:', error);
        }
    }

    // --- INITIALIZATION ---
    function initializePortfolio() {
        initializeNavigation();
        initializeThemeSwitcher();
        initializeLanguageSwitcher();
        initializeCertificateFeature(); // Now uses lazy loading
        initializeWebSearchSuggestions();
        initializeModals();
        initializeCarousels();
        initializeCopyButtons();
        initializeDisclaimer(); // Added disclaimer initialization (no cookie consent)

        // Initialize tool categories if on the tools page
        if (document.querySelector('.categories-container')) {
            console.log('Tools page detected, initializing tool categories...');
            initializeToolCategories();
        }

        // Initialize useful information if on that page
        if (document.getElementById('useful-information-nav')) {
            initializeUsefulInfoSearch();
            fetchUsefulInformation();
        }

        // Set initial language
        const savedLanguage = localStorage.getItem('language') || 'en';
        changeLanguage(savedLanguage);

        // Set initial theme
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'light') {
            document.body.classList.add('light-theme');
        }

        // Update active nav link based on current page
        const currentPage = window.location.pathname.split('/').pop() || 'index.html';
        document.querySelectorAll('.nav-link').forEach(link => {
            const linkPage = link.getAttribute('href');
            if ((currentPage === 'index.html' || currentPage === '') && linkPage === 'index.html') {
                link.classList.add('active');
            } else if (linkPage === currentPage) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
    }

    // Initialize the application
    initializePortfolio();
});