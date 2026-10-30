/* ============================================
   KAVACH – Internationalization (i18n)
   Client-side translation engine
   ============================================ */

const I18n = {
    currentLang: 'en',
    translations: {},

    init() {
        const btn = document.getElementById('lang-menu-button');
        const menu = document.getElementById('lang-dropdown-menu');
        const chevron = document.getElementById('lang-chevron');
        const options = document.querySelectorAll('#lang-options button');

        if (btn && menu) {
            // Restore saved language
            const saved = localStorage.getItem('kavach-lang') || 'en';
            this.setLanguage(saved);

            // Toggle menu
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                menu.classList.toggle('hidden');
                chevron.classList.toggle('rotate-180');
            });

            // Close when clicking outside
            document.addEventListener('click', () => {
                menu.classList.add('hidden');
                chevron.classList.remove('rotate-180');
            });

            // Language selection
            options.forEach(opt => {
                opt.addEventListener('click', () => {
                    const lang = opt.getAttribute('data-lang');
                    this.setLanguage(lang);
                    menu.classList.add('hidden');
                    chevron.classList.remove('rotate-180');
                });
            });
        }
    },

    async setLanguage(lang) {
        this.currentLang = lang;
        localStorage.setItem('kavach-lang', lang);

        // Update UI dropdown button text
        const langText = document.getElementById('current-lang-text');
        if (langText) {
            const langNames = {
                'en': 'English',
                'hi': 'हिंदी',
                'kn': 'ಕನ್ನಡ',
                'mr': 'मराठी'
            };
            langText.textContent = langNames[lang] || 'English';
        }

        // Update active class in menu
        document.querySelectorAll('#lang-options button').forEach(btn => {
            if (btn.getAttribute('data-lang') === lang) {
                btn.classList.add('active-lang');
            } else {
                btn.classList.remove('active-lang');
            }
        });

        // Try fetching from backend; fall back to embedded strings
        if (!this.translations[lang]) {
            try {
                const res = await fetch(`/api/translations/${lang}`);
                if (res.ok) {
                    this.translations[lang] = await res.json();
                }
            } catch {
                // Fallback inline
            }
        }

        // If still no translations, use embedded fallback
        if (!this.translations[lang]) {
            this.translations[lang] = FALLBACK_TRANSLATIONS[lang] || FALLBACK_TRANSLATIONS['en'];
        }

        this.applyAll();
    },

    t(key) {
        const strings = this.translations[this.currentLang] || FALLBACK_TRANSLATIONS['en'];
        return strings[key] || FALLBACK_TRANSLATIONS['en'][key] || key;
    },

    applyAll() {
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            el.textContent = this.t(key);
        });
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            el.placeholder = this.t(key);
        });
    },

    applyToElement(el) {
        el.querySelectorAll('[data-i18n]').forEach(child => {
            const key = child.getAttribute('data-i18n');
            child.textContent = this.t(key);
        });
    },
};

/* Fallback translations (embedded for offline PWA support) */
const FALLBACK_TRANSLATIONS = {
    en: {
        app_name: "SignalSafe Campus – Cybersecurity Portal",
        tagline: "JCER Campus Cybersecurity Portal",
        dashboard: "Dashboard",
        tools: "Tools",
        alerts: "Alerts",
        settings: "Settings",
        support: "Support",
        security_score: "Security Score",
        monthly_avg: "Monthly Average",
        view_history: "View History",
        security_tools: "Security Tools",
        view_all: "View All",
        screenshot_tab: "Screenshot",
        qrcode_tab: "QR Code",
        url_tab: "Website URL",
        upload_image: "Upload Image",
        capture_camera: "Capture from Camera",
        paste_url: "Paste URL here",
        analyze: "Analyze",
        analyzing: "Analyzing...",
        risk_score: "Risk Score",
        status_safe: "Safe Transaction",
        status_suspicious: "Suspicious – Verify Manually",
        status_blocked: "Blocked – Fake Detected",
        safe_msg: "This appears to be a genuine transaction.",
        suspicious_msg: "Some anomalies detected. Please verify manually.",
        blocked_msg: "High risk of fraud detected. Do not proceed!",
        extracted_fields: "Extracted Information",
        reasons: "Detection Reasons",
        screenshot_hero_title: "Screenshot Scam Detector",
        screenshot_hero_desc: "Verify payment receipts instantly to protect your business.",
        qrcode_hero_title: "QR Code Security Scanner",
        qrcode_hero_desc: "Scan or upload a QR code to verify its payment destination.",
        url_hero_title: "Deep URL Phishing Scan",
        url_hero_desc: "Instant deep-scan analysis for malicious or suspicious URLs.",
        evidence_summary_default: "Automated SignalSafe verification based on visual and textual patterns.",
        scan_now: "Scan Now",
        open_camera: "Open Camera",
        camera_btn: "Camera",
        browse_files: "Browse Files",
        paste_link: "Paste Link",
        screenshot_card_desc: "Found a suspicious message? Take a screenshot and we'll check it.",
        qrcode_card_desc: "Never pay before checking. Scan QR codes at shops to verify safety.",
        url_card_desc: "Check if a link is real or a fake lottery scam before you click.",
        live_threats: "Live Threats in Your Area",
        bank_scam_title: "HIGH ALERT: VILLAGE BANK SCAM",
        bank_scam_desc: "A fake SMS about PM Kisan Yojana KYC is circulating in Shivpuri. Do not click links!",
        two_hours_ago: "2 hours ago",
        job_scam_title: "Fake Job Offer via WhatsApp",
        job_scam_desc: "Alert for local youth: Agencies promising railway jobs for ₹5000 are fraudulent.",
        yesterday: "Yesterday",
        cyber_safety_tips: "Cyber Safety Tips",
        upi_safety_guide: "UPI Safety Guide",
        upi_safety_desc: "Never enter PIN to 'receive' cash.",
        password_protection: "Password Protection",
        password_desc: "Don't use phone no. as password.",
        os_update_helper: "OS Update Helper",
        os_update_desc: "Learn how to update smartphone.",
        verification_tips_title: "Verification Tips",
        tip_ml_fraud: "High risk scores indicate ML-confirmed patterns of fraud.",
        tip_manual_check: "Always check your bank manually regardless of the scan output.",
        tip_reporting: "Use the reporting feature in your bank app if you encounter domains mimicking banking layouts.",
    },
    hi: {
        app_name: "कवच – स्कैम शील्ड",
        tagline: "ग्रामीण भारत के लिए रियल-टाइम स्कैम शील्ड",
        dashboard: "डैशबोर्ड",
        tools: "उपकरण",
        alerts: "अलर्ट",
        settings: "सेटिंग्स",
        support: "सहायता",
        security_score: "सुरक्षा स्कोर",
        monthly_avg: "मासिक औसत",
        view_history: "इतिहास देखें",
        security_tools: "सुरक्षा उपकरण",
        view_all: "सभी देखें",
        screenshot_tab: "स्क्रीनशॉट",
        qrcode_tab: "QR कोड",
        url_tab: "वेबसाइट URL",
        upload_image: "छवि अपलोड करें",
        capture_camera: "कैमरे से कैप्चर करें",
        paste_url: "यहाँ URL पेस्ट करें",
        analyze: "विश्लेषण करें",
        analyzing: "विश्लेषण हो रहा है...",
        risk_score: "जोखिम स्कोर",
        status_safe: "सुरक्षित लेनदेन",
        status_suspicious: "संदिग्ध – मैन्युअल रूप से सत्यापित करें",
        status_blocked: "अवरुद्ध – नकली पता चला",
        safe_msg: "यह एक वास्तविक लेनदेन प्रतीत होता है।",
        suspicious_msg: "कुछ असामान्यताएं पाई गईं। कृपया सत्यापित करें।",
        blocked_msg: "धोखाधड़ी का उच्च जोखिम। आगे न बढ़ें!",
        extracted_fields: "निकाली गई जानकारी",
        reasons: "पहचान के कारण",
        screenshot_hero_title: "स्क्रीनशॉट स्कैम डिटेक्टर",
        screenshot_hero_desc: "अपने व्यवसाय की सुरक्षा के लिए भुगतान रसीदों को तुरंत सत्यापित करें।",
        qrcode_hero_title: "QR कोड सुरक्षा स्कैनर",
        qrcode_hero_desc: "भुगतान गंतव्य को सत्यापित करने के लिए QR कोड स्कैन या अपलोड करें।",
        url_hero_title: "डीप URL फिशिंग स्कैन",
        url_hero_desc: "दुर्भावनापूर्ण या संदिग्ध URL के लिए त्वरित डीप-स्कैन विश्लेषण।",
        evidence_summary_default: "दृश्य और पाठ्य पैटर्न के आधार पर स्वचालित कवच सत्यापन।",
        scan_now: "अभी स्कैन करें",
        open_camera: "कैमरा खोलें",
        camera_btn: "कैमरा",
        browse_files: "फाइलें ब्राउज़ करें",
        paste_link: "लिंक पेस्ट करें",
        screenshot_card_desc: "कोई संदिग्ध संदेश मिला? स्क्रीनशॉट लें और हम इसकी जांच करेंगे।",
        qrcode_card_desc: "पेमेंट से पहले जांचें। सुरक्षा के लिए दुकानों पर QR कोड स्कैन करें।",
        url_card_desc: "क्लिक करने से पहले जांचें कि लिंक असली है या नकली लॉटरी घोटाला।",
        live_threats: "आपके क्षेत्र में लाइव खतरे",
        bank_scam_title: "हाई अलर्ट: ग्राम बैंक घोटाला",
        bank_scam_desc: "शिवपुरी में पीएम किसान योजना केवाईसी के बारे में फर्जी एसएमएस फैल रहा है।",
        two_hours_ago: "2 घंटे पहले",
        job_scam_title: "व्हाट्सएप के जरिए फर्जी नौकरी का ऑफर",
        job_scam_desc: "युवाओं के लिए अलर्ट: रेलवे की नौकरी दिलाने का वादा करने वाली एजेंसियां फर्जी हैं।",
        yesterday: "कल",
        cyber_safety_tips: "साइबर सुरक्षा टिप्स",
        upi_safety_guide: "यूपीआई सुरक्षा गाइड",
        upi_safety_desc: "पैसे 'प्राप्त' करने के लिए कभी भी पिन दर्ज न करें।",
        password_protection: "पासवर्ड सुरक्षा",
        password_desc: "पासवर्ड के रूप में फोन नंबर का उपयोग न करें।",
        os_update_helper: "ओएस अपडेट हेल्पर",
        os_update_desc: "स्मार्टफोन को अपडेट करने का तरीका जानें।",
        verification_tips_title: "सत्यापन टिप्स",
        tip_ml_fraud: "उच्च जोखिम स्कोर एमएल-पुष्टि धोखाधड़ी पैटर्न की ओर इशारा करते हैं।",
        tip_manual_check: "स्कैन परिणाम के बावजूद हमेशा अपने बैंक से मैन्युअल रूप से जांच करें।",
        tip_reporting: "यदि आपको बैंकिंग लेआउट की नकल करने वाले डोमेन मिलते हैं तो अपने बैंक ऐप में रिपोर्टिंग सुविधा का उपयोग करें।",
    },
    kn: {
        app_name: "ಕವಚ – ಸ್ಕ್ಯಾಮ್ ಶೀಲ್ಡ್",
        tagline: "ಗ್ರಾಮೀಣ ಭಾರತಕ್ಕೆ ರಿಯಲ್-ಟೈಮ್ ಸ್ಕ್ಯಾಮ್ ಶೀಲ್ಡ್",
        dashboard: "ಡ್ಯಾಶ್‌ಬೋರ್ಡ್",
        tools: "ಉಪಕರಣಗಳು",
        alerts: "ಎಚ್ಚರಿಕೆಗಳು",
        settings: "ಸೆಟ್ಟಿಂಗ್‌ಗಳು",
        support: "ಬೆಂಬಲ",
        security_score: "ಭದ್ರತಾ ಸ್ಕೋರ್",
        monthly_avg: "ಮಾಸಿಕ ಸರಾಸರಿ",
        view_history: "ಇತಿಹಾಸ ನೋಡಿ",
        security_tools: "ಭದ್ರತಾ ಪರಿಕರಗಳು",
        view_all: "ಎಲ್ಲವನ್ನೂ ನೋಡಿ",
        screenshot_tab: "ಸ್ಕ್ರೀನ್‌ಶಾಟ್",
        qrcode_tab: "QR ಕೋಡ್",
        url_tab: "ವೆಬ್‌ಸೈಟ್ URL",
        upload_image: "ಚಿತ್ರ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ",
        capture_camera: "ಕ್ಯಾಮೆರಾದಿಂದ ಕ್ಯಾಪ್ಚರ್ ಮಾಡಿ",
        paste_url: "ಇಲ್ಲಿ URL ಅಂಟಿಸಿ",
        analyze: "ವಿಶ್ಲೇಷಿಸಿ",
        analyzing: "ವಿಶ್ಲೇಷಿಸಲಾಗುತ್ತಿದೆ...",
        risk_score: "ಅಪಾಯ ಸ್ಕೋರ್",
        status_safe: "ಸುರಕ್ಷಿತ ವಹಿವಾಟು",
        status_suspicious: "ಅನುಮಾನಾಸ್ಪದ – ಹಸ್ತಚಾಲಿತವಾಗಿ ಪರಿಶೀಲಿಸಿ",
        status_blocked: "ನಿರ್ಬಂಧಿಸಲಾಗಿದೆ – ನಕಲಿ ಪತ್ತೆಯಾಗಿದೆ",
        safe_msg: "ಇದು ನಿಜವಾದ ವಹಿವಾಟು ಎಂದು ಕಾಣುತ್ತದೆ.",
        suspicious_msg: "ಕೆಲವು ಅಸಹಜತೆಗಳು ಕಂಡುಬಂದಿವೆ.",
        blocked_msg: "ವಂಚನೆಯ ಹೆಚ್ಚಿನ ಅಪಾಯ. ಮುಂದುವರಿಸಬೇಡಿ!",
        extracted_fields: "ಹೊರತೆಗೆದ ಮಾಹಿತಿ",
        reasons: "ಪತ್ತೆ ಕಾರಣಗಳು",
        screenshot_hero_title: "ಸ್ಕ್ರೀನ್‌ಶಾಟ್ ಸ್ಕ್ಯಾಮ್ ಡಿಟೆಕ್ಟರ್",
        screenshot_hero_desc: "ನಿಮ್ಮ ವ್ಯಾಪಾರವನ್ನು ರಕ್ಷಿಸಲು ಪಾವತಿ ರಸೀದಿಗಳನ್ನು ತಕ್ಷಣ ಪರಿಶೀಲಿಸಿ.",
        qrcode_hero_title: "QR ಕೋಡ್ ಭದ್ರತಾ ಸ್ಕ್ಯಾನರ್",
        qrcode_hero_desc: "ಪಾವತಿ ಗಮ್ಯಸ್ಥಾನವನ್ನು ಪರಿಶೀಲಿಸಲು QR ಕೋಡ್ ಅನ್ನು ಸ್ಕ್ಯಾನ್ ಮಾಡಿ ಅಥವಾ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ.",
        url_hero_title: "ಡೀಪ್ URL ಫಿಶಿಂಗ್ ಸ್ಕ್ಯಾನ್",
        url_hero_desc: "ದುರುದ್ದೇಶಪೂರಿತ ಅಥವಾ ಅನುಮಾನಾಸ್ಪದ URL ಗಳಿಗಾಗಿ ತ್ವರಿತ ಡೀಪ್-ಸ್ಕ್ಯಾನ್ ವಿಶ್ಲೇಷಣೆ.",
        evidence_summary_default: "ದೃಶ್ಯ ಮತ್ತು ಪಠ್ಯ ಮಾದರಿಗಳ ಆಧಾರದ ಮೇಲೆ ಸ್ವಯಂಚಾಲಿತ ಕವಚ ಪರಿಶೀಲನೆ.",
        scan_now: "ಈಗ ಸ್ಕ್ಯಾನ್ ಮಾಡಿ",
        open_camera: "ಕ್ಯಾಮೆರಾ ತೆರೆಯಿರಿ",
        camera_btn: "ಕ್ಯಾಮೆರಾ",
        browse_files: "ಫೈಲ್‌ಗಳನ್ನು ಬ್ರೌಸ್ ಮಾಡಿ",
        paste_link: "ಲಿಂಕ್ ಅಂಟಿಸಿ",
        screenshot_card_desc: "ಅನುಮಾನಾಸ್ಪದ ಸಂದೇಶವು ಕಂಡರೆ? ಸ್ಕ್ರೀನ್‌ಶಾಟ್ ತೆಗೆದುಕೊಳ್ಳಿ ಮತ್ತು ನಾವು ಪರೀಕ್ಷಿಸುತ್ತೇವೆ.",
        qrcode_card_desc: "ಪಾವತಿಸುವ ಮೊದಲು ಪರಿಶೀಲಿಸಿ. ಸುರಕ್ಷತೆಗಾಗಿ ಅಂಗಡಿಗಳಲ್ಲಿ QR ಸ್ಕ್ಯಾನ್ ಮಾಡಿ.",
        url_card_desc: "ನಿವು ಕಿಕ್ ಮಾಡುವ ಮೊದಲು ಲಿಂಕ್ ಅಸಲಿ ಅಥವಾ ನಕಲಿ ಲಾಟರಿ ಹಗರಣವೇ ಎಂದು ಪರಿಶೀಲಿಸಿ.",
        live_threats: "ನಿಮ್ಮ ಪ್ರದೇಶದಲ್ಲಿನ ಅಪಾಯಗಳು",
        bank_scam_title: "ಹೈ ಅಲರ್ಟ್: ಗ್ರಾಮ ಬ್ಯಾಂಕ್ ಹಗರಣ",
        bank_scam_desc: "ಪಿಎಂ ಕಿಸಾನ್ ಯೋಜನೆಯ ಕೆವೈಸಿ ಬಗ್ಗೆ ನಕಲಿ SMS ಹರಿದಾಡುತ್ತಿದೆ. ಲಿಂಕ್ ಕ್ಲಿಕ್ ಮಾಡಬೇಡಿ!",
        two_hours_ago: "2 ಗಂಟೆಗಳ ಹಿಂದೆ",
        job_scam_title: "ವಾಟ್ಸಾಪ್ ಮೂಲಕ ನಕಲಿ ಉದ್ಯೋಗ ಸಮಾಚಾರ",
        job_scam_desc: "ಯುವಕರಿಗೆ ಎಚ್ಚರಿಕೆ: ರೈಲ್ವೆ ಉದ್ಯೋಗಗಳನ್ನು ನಂಬಬೇಡಿ, ಹಣ ನೀಡಬೇಡಿ.",
        yesterday: "ನಿನ್ನೆ",
        cyber_safety_tips: "ಸೈಬರ್ ಸುರಕ್ಷತಾ ಸಲಹೆಗಳು",
        upi_safety_guide: "UPI ಸುರಕ್ಷತಾ ಮಾರ್ಗದರ್ಶಿ",
        upi_safety_desc: "ಹಣವನ್ನು ಸ್ವೀಕರಿಸಲು ಎಂದಿಗೂ ಪಿನ್ ನಮೂದಿಸಬೇಡಿ.",
        password_protection: "ಪಾಸ್ವರ್ಡ್ ರಕ್ಷಣೆ",
        password_desc: "ಫೋನ್ ಸಂಖ್ಯೆಯನ್ನು ಪಾಸ್ವರ್ಡ್ ಆಗಿ ಬಳಸಬೇಡಿ.",
        os_update_helper: "ಓಎಸ್ ಅಪ್‌ಡೇಟ್ ಸಹಾಯ",
        os_update_desc: "ಸ್ಮಾರ್ಟ್‌ಫೋನ್ ಅನ್ನು ಹೇಗೆ ಅಪ್‌ಡೇಟ್ ಮಾಡುವುದು ಎಂದು ತಿಳಿಯಿರಿ.",
        verification_tips_title: "ಪರಿಶೀಲನಾ ಸಲಹೆಗಳು",
        tip_ml_fraud: "ಹೆಚ್ಚಿನ ಅಪಾಯದ ಅಂಕಗಳು ಎಂಎಲ್-ದೃಢಪಡಿಸಿದ ವಂಚನೆಯ ಮಾದರಿಗಳನ್ನು ಸೂಚಿಸುತ್ತವೆ.",
        tip_manual_check: "ಸ್ಕ್ಯಾನ್ ಫಲಿತಾಂಶವನ್ನು ಲೆಕ್ಕಿಸದೆ ಯಾವಾಗಲೂ ನಿಮ್ಮ ಬ್ಯಾಂಕ್ ಅನ್ನು ಹಸ್ತಚಾಲಿತವಾಗಿ ಪರಿಶೀಲಿಸಿ.",
        tip_reporting: "ನೀವು ಬ್ಯಾಂಕಿಂಗ್ ವಿನ್ಯಾಸಗಳನ್ನು ಅನುಕರಿಸುವ ಡೊಮೇನ್‌ಗಳನ್ನು ಎದುರಿಸಿದರೆ ನಿಮ್ಮ ಬ್ಯಾಂಕ್ ಆಪ್‌ನಲ್ಲಿ ವರದಿ ಮಾಡುವ ವೈಶಿಷ್ಟ್ಯವನ್ನು ಬಳಸಿ.",
    },
    mr: {
        app_name: "कवच – स्कॅम शिल्ड",
        tagline: "ग्रामीण भारतासाठी रिअल-टाइम स्कॅम शिल्ड",
        dashboard: "डॅशबोर्ड",
        tools: "उपकरणे",
        alerts: "अलर्ट",
        settings: "सेटिंग्ज",
        support: "मदत",
        security_score: "सुरक्षा स्कोअर",
        monthly_avg: "मासिक सरासरी",
        view_history: "इतिहास पहा",
        security_tools: "सुरक्षा साधने",
        view_all: "सर्व पहा",
        screenshot_tab: "स्क्रीनशॉट",
        qrcode_tab: "QR कोड",
        url_tab: "वेबसाइट URL",
        upload_image: "प्रतिमा अपलोड करा",
        capture_camera: "कॅमेऱ्याने कॅप्चर करा",
        paste_url: "येथे URL पेस्ट करा",
        analyze: "विश्लेषण करा",
        analyzing: "विश्लेषण होत आहे...",
        risk_score: "जोखीम स्कोअर",
        status_safe: "सुरक्षित व्यवहार",
        status_suspicious: "संशयास्पद – व्यक्तिचलितपणे सत्यापित करा",
        status_blocked: "अवरोधित – बनावट आढळले",
        safe_msg: "हा एक खरा व्यवहार दिसतो.",
        suspicious_msg: "काही विसंगती आढळल्या. कृपया सत्यापित करा.",
        blocked_msg: "फसवणुकीचा उच्च धोका. पुढे जाऊ नका!",
        extracted_fields: "काढलेली माहिती",
        reasons: "शोध कारणे",
        screenshot_hero_title: "स्क्रीनशॉट स्कॅम डिटेक्टर",
        screenshot_hero_desc: "तुमच्या व्यवसायाचे रक्षण करण्यासाठी पेमेंट पावत्या त्वरित सत्यापित करा.",
        qrcode_hero_title: "QR कोड सुरक्षा स्कॅनर",
        qrcode_hero_desc: "पेमेंट गंतव्य सत्यापित करण्यासाठी QR कोड स्कॅन किंवा अपलोड करा.",
        url_hero_title: "डीप URL फिशिंग स्कॅन",
        url_hero_desc: "धोकादायक किंवा संशयास्पद URL साठी त्वरित डीप-स्कॅन विश्लेषण.",
        evidence_summary_default: "दृश्य आणि मजकूर पॅटर्नवर आधारित स्वयंचलित कवच सत्यापन.",
        scan_now: "आता स्कॅन करा",
        open_camera: "कॅमेरा उघडा",
        camera_btn: "कॅमेरा",
        browse_files: "फायली ब्राउझ करा",
        paste_link: "दुवा पेस्ट करा",
        screenshot_card_desc: "काही संशयास्पद संदेश आढळला? स्क्रीनशॉट घ्या आणि आम्ही तो तपासू.",
        qrcode_card_desc: "पेमेंट करण्यापूर्वी तपासा. सुरक्षेसाठी दुकानांमध्ये QR कोड स्कॅन करा.",
        url_card_desc: "क्लिक करण्यापूर्वी तपासा की लिंक खरी आहे की बनावट लॉटरी घोटाळा.",
        live_threats: "तुमच्या क्षेत्रातील धोके",
        bank_scam_title: "हाय अलर्ट: गाव बँक घोटाळा",
        bank_scam_desc: "शिवपुरीमध्ये पीएम किसान योजना केवायसीबद्दल बनावट एसएमएस पसरत आहे.",
        two_hours_ago: "२ तासांपूर्वी",
        job_scam_title: "व्हॉट्सॲपद्वारे बनावट नोकरीची ऑफर",
        job_scam_desc: "तरुणांसाठी अलर्ट: रेल्वे नोकरीचे आश्वासन देणाऱ्या संस्था बनावट आहेत.",
        yesterday: "काल",
        cyber_safety_tips: "सायಬರ್ ಸುರಕ್ಷತಾ ಟಿಪ್ಸ್",
        upi_safety_guide: "यूपीआई सुरक्षा मार्गदर्शक",
        upi_safety_desc: "पैसे 'मिळवण्यासाठी' कधीही पिन टाकू नका.",
        password_protection: "पासवर्ड संरक्षण",
        password_desc: "पासवर्ड म्हणून फोन नंबर वापरू नका.",
        os_update_helper: "ओएस अपडेट हेल्पर",
        os_update_desc: "स्मार्टफोन कसा अपडेट करायचा ते शिका.",
        verification_tips_title: "पडताळणी टिप्स",
        tip_ml_fraud: "उच्च जोखीम स्कोअर एमएल-पुष्टी केलेल्या फसवणुकीच्या पॅटर्न दर्शवतात.",
        tip_manual_check: "स्कॅन आउटपुट काहीही असले तरी नेहमी तुमच्या बँकेची स्वतः खात्री करा.",
        tip_reporting: "बँकिंग लेआउटची नक्कल करणारी डोमेन आढळल्यास तुमच्या बँक ॲपमधील रिपोर्टिंग वैशिष्ट्य वापरा.",
    },
};
