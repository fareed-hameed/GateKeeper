const LANGS = {
    en: { dir: 'ltr', label: 'EN', name: 'English' },
    ar: { dir: 'rtl', label: 'ع', name: 'العربية' },
    ur: { dir: 'rtl', label: 'اُ', name: 'اردو' },
    hi: { dir: 'ltr', label: 'हि', name: 'हिन्दी' },
    bn: { dir: 'ltr', label: 'বা', name: 'বাংলা' },
};

const T = {
    en: {
        // Gate page
        enter_code: 'Enter your access code',
        trigger: 'Open Gate',
        authenticating: 'Authenticating...',
        access_granted: 'Access granted',
        access_denied: 'Access denied',
        invalid_code: 'Invalid code',
        daily_limit: 'Daily limit reached',
        window_expired: 'Access window has expired',
        network_error: 'Network error. Please try again.',
        trusted_device: 'Registered device detected',
        trusted: 'Trusted',
        command_center: 'Command Center',
        attempts_remaining: '{n} attempt{s} remaining',
        window_remaining: '{n} min window remaining',
        // Admin page
        admin_enrollment: 'Admin Enrollment',
        enter_master_pin: 'Enter the master PIN',
        master_pin: 'Master PIN',
        device_name: 'Device name (e.g. My Phone)',
        view_codes: 'View Codes',
        enroll_device: 'Enroll This Device',
        enroll_and_view: 'Enroll & View',
        todays_code: "Today's Access Code",
        upcoming_codes: 'Upcoming Codes (7 Days)',
        today: 'Today',
        sys_config: 'System Configuration',
        max_triggers: 'Max triggers/device/day',
        access_window: 'Access window',
        daily_reset: 'Daily reset',
        code_digits: 'Code digits',
        action: 'Action',
        enrolled_devices: 'Enrolled Devices',
        no_devices: 'No devices enrolled',
        super_admin: 'Super Admin',
        admin: 'Admin',
        you: 'You',
        remove: 'Remove',
        invite_links: 'Invite Links',
        invite_label: 'Label (e.g. Mom\'s Phone)',
        generate_invite: 'Generate Invite Link',
        share_link: 'Share this link:',
        copy_link: 'Copy Link',
        copied: 'Copied!',
        copy_code: 'Copy Code',
        no_invites: 'No invites created yet',
        revoke: 'Revoke',
        expired: 'Expired',
        used: 'Used',
        revoked: 'Revoked',
        activity_log: 'Activity Log',
        no_activity: 'No recent activity',
        time: 'Time',
        device: 'Device',
        result: 'Result',
        triggered: 'Triggered',
        identifying: 'Identifying device...',
        access_codes: 'Access Codes',
        invalid_pin: 'Invalid PIN',
        enrollment_failed: 'Enrollment failed',
        remove_confirm: 'Remove this device?',
        revoke_confirm: 'Revoke this invite?',
        // Enroll page
        device_enrollment: 'Device Enrollment',
        invited_to_join: "You've been invited to join AEGIS",
        your_name: 'Your name or device name',
        register_device: 'Register Device',
        registered_ok: 'Device registered successfully. You can now use the access code or bypass on the main page.',
        go_to_aegis: 'Go to AEGIS',
        invalid_invite: 'Invalid invite',
    },
    ar: {
        enter_code: 'أدخل رمز الوصول',
        trigger: 'فتح البوابة',
        authenticating: 'جاري التحقق...',
        access_granted: 'تم منح الوصول',
        access_denied: 'تم رفض الوصول',
        invalid_code: 'رمز غير صالح',
        daily_limit: 'تم بلوغ الحد اليومي',
        window_expired: 'انتهت نافذة الوصول',
        network_error: 'خطأ في الشبكة. حاول مرة أخرى.',
        trusted_device: 'تم اكتشاف جهاز مسجل',
        trusted: 'موثوق',
        command_center: 'مركز التحكم',
        attempts_remaining: '{n} محاولة متبقية',
        window_remaining: '{n} دقيقة متبقية',
        admin_enrollment: 'تسجيل المسؤول',
        enter_master_pin: 'أدخل رمز المسؤول',
        master_pin: 'رمز المسؤول',
        device_name: 'اسم الجهاز (مثال: هاتفي)',
        view_codes: 'عرض الرموز',
        enroll_device: 'تسجيل هذا الجهاز',
        enroll_and_view: 'تسجيل وعرض',
        todays_code: 'رمز اليوم',
        upcoming_codes: 'الرموز القادمة (٧ أيام)',
        today: 'اليوم',
        sys_config: 'إعدادات النظام',
        max_triggers: 'الحد الأقصى/جهاز/يوم',
        access_window: 'نافذة الوصول',
        daily_reset: 'إعادة التعيين اليومي',
        code_digits: 'عدد الأرقام',
        action: 'الإجراء',
        enrolled_devices: 'الأجهزة المسجلة',
        no_devices: 'لا توجد أجهزة مسجلة',
        super_admin: 'مسؤول أعلى',
        admin: 'مسؤول',
        you: 'أنت',
        remove: 'إزالة',
        invite_links: 'روابط الدعوة',
        invite_label: 'التسمية (مثال: هاتف أمي)',
        generate_invite: 'إنشاء رابط دعوة',
        share_link: 'شارك هذا الرابط:',
        copy_link: 'نسخ الرابط',
        copied: 'تم النسخ!',
        copy_code: 'نسخ الرمز',
        no_invites: 'لا توجد دعوات بعد',
        revoke: 'إلغاء',
        expired: 'منتهي',
        used: 'مستخدم',
        revoked: 'ملغى',
        activity_log: 'سجل النشاط',
        no_activity: 'لا يوجد نشاط حديث',
        time: 'الوقت',
        device: 'الجهاز',
        result: 'النتيجة',
        triggered: 'تم التنفيذ',
        identifying: 'جاري تحديد الجهاز...',
        access_codes: 'رموز الوصول',
        invalid_pin: 'رمز غير صالح',
        enrollment_failed: 'فشل التسجيل',
        remove_confirm: 'إزالة هذا الجهاز؟',
        revoke_confirm: 'إلغاء هذه الدعوة؟',
        device_enrollment: 'تسجيل الجهاز',
        invited_to_join: 'تمت دعوتك للانضمام إلى AEGIS',
        your_name: 'اسمك أو اسم الجهاز',
        register_device: 'تسجيل الجهاز',
        registered_ok: 'تم تسجيل الجهاز بنجاح. يمكنك الآن استخدام رمز الوصول.',
        go_to_aegis: 'الذهاب إلى AEGIS',
        invalid_invite: 'دعوة غير صالحة',
    },
    ur: {
        enter_code: 'رسائی کوڈ درج کریں',
        trigger: 'گیٹ کھولیں',
        authenticating: 'تصدیق ہو رہی ہے...',
        access_granted: 'رسائی دے دی گئی',
        access_denied: 'رسائی سے انکار',
        invalid_code: 'غلط کوڈ',
        daily_limit: 'روزانہ کی حد پوری ہو گئی',
        window_expired: 'رسائی کا وقت ختم ہو گیا',
        network_error: 'نیٹ ورک میں خرابی۔ دوبارہ کوشش کریں۔',
        trusted_device: 'رجسٹرڈ ڈیوائس کا پتا چلا',
        trusted: 'قابل اعتماد',
        command_center: 'کمانڈ سینٹر',
        attempts_remaining: '{n} کوششیں باقی',
        window_remaining: '{n} منٹ باقی',
        admin_enrollment: 'ایڈمن اندراج',
        enter_master_pin: 'ماسٹر پن درج کریں',
        master_pin: 'ماسٹر پن',
        device_name: 'ڈیوائس کا نام',
        view_codes: 'کوڈ دیکھیں',
        enroll_device: 'یہ ڈیوائس رجسٹر کریں',
        enroll_and_view: 'رجسٹر اور دیکھیں',
        todays_code: 'آج کا کوڈ',
        upcoming_codes: 'آنے والے کوڈ (۷ دن)',
        today: 'آج',
        access_codes: 'رسائی کوڈ',
        invalid_pin: 'غلط پن',
        copy_code: 'کوڈ کاپی کریں',
        copied: 'کاپی ہو گیا!',
        device_enrollment: 'ڈیوائس اندراج',
        invited_to_join: 'آپ کو AEGIS میں شامل ہونے کی دعوت دی گئی',
        your_name: 'آپ کا نام یا ڈیوائس کا نام',
        register_device: 'ڈیوائس رجسٹر کریں',
        registered_ok: 'ڈیوائس کامیابی سے رجسٹر ہو گئی۔',
        go_to_aegis: 'AEGIS پر جائیں',
        invalid_invite: 'غلط دعوت',
    },
    hi: {
        enter_code: 'अपना एक्सेस कोड दर्ज करें',
        trigger: 'गेट खोलें',
        authenticating: 'प्रमाणित हो रहा है...',
        access_granted: 'पहुंच प्रदान की गई',
        access_denied: 'पहुंच अस्वीकृत',
        invalid_code: 'अमान्य कोड',
        daily_limit: 'दैनिक सीमा पूरी हो गई',
        window_expired: 'एक्सेस विंडो समाप्त हो गई',
        network_error: 'नेटवर्क त्रुटि। कृपया पुनः प्रयास करें।',
        trusted_device: 'पंजीकृत डिवाइस मिला',
        trusted: 'विश्वसनीय',
        command_center: 'कमांड सेंटर',
        attempts_remaining: '{n} प्रयास शेष',
        window_remaining: '{n} मिनट शेष',
        access_codes: 'एक्सेस कोड',
        invalid_pin: 'अमान्य पिन',
        copy_code: 'कोड कॉपी करें',
        copied: 'कॉपी हो गया!',
        device_enrollment: 'डिवाइस पंजीकरण',
        invited_to_join: 'आपको AEGIS में शामिल होने के लिए आमंत्रित किया गया है',
        your_name: 'आपका नाम या डिवाइस का नाम',
        register_device: 'डिवाइस पंजीकृत करें',
        registered_ok: 'डिवाइस सफलतापूर्वक पंजीकृत हो गई।',
        go_to_aegis: 'AEGIS पर जाएं',
        invalid_invite: 'अमान्य आमंत्रण',
    },
    bn: {
        enter_code: 'আপনার অ্যাক্সেস কোড লিখুন',
        trigger: 'গেট খুলুন',
        authenticating: 'যাচাই হচ্ছে...',
        access_granted: 'অ্যাক্সেস দেওয়া হয়েছে',
        access_denied: 'অ্যাক্সেস প্রত্যাখ্যাত',
        invalid_code: 'অবৈধ কোড',
        daily_limit: 'দৈনিক সীমা পূর্ণ',
        window_expired: 'অ্যাক্সেস উইন্ডো শেষ',
        network_error: 'নেটওয়ার্ক ত্রুটি। আবার চেষ্টা করুন।',
        trusted_device: 'নিবন্ধিত ডিভাইস সনাক্ত হয়েছে',
        trusted: 'বিশ্বস্ত',
        command_center: 'কমান্ড সেন্টার',
        attempts_remaining: '{n}টি প্রচেষ্টা বাকি',
        window_remaining: '{n} মিনিট বাকি',
        access_codes: 'অ্যাক্সেস কোড',
        invalid_pin: 'অবৈধ পিন',
        copy_code: 'কোড কপি করুন',
        copied: 'কপি হয়েছে!',
        device_enrollment: 'ডিভাইস নিবন্ধন',
        invited_to_join: 'আপনাকে AEGIS-এ যোগ দিতে আমন্ত্রণ জানানো হয়েছে',
        your_name: 'আপনার নাম বা ডিভাইস নাম',
        register_device: 'ডিভাইস নিবন্ধন করুন',
        registered_ok: 'ডিভাইস সফলভাবে নিবন্ধিত হয়েছে।',
        go_to_aegis: 'AEGIS-এ যান',
        invalid_invite: 'অবৈধ আমন্ত্রণ',
    },
};

// Fill missing keys with English fallback
for (const lang of Object.keys(T)) {
    if (lang === 'en') continue;
    for (const key of Object.keys(T.en)) {
        if (!T[lang][key]) T[lang][key] = T.en[key];
    }
}

// --- i18n Engine ---
let currentLang = localStorage.getItem('aegis_lang') || detectLang();

function detectLang() {
    const nav = (navigator.language || '').slice(0, 2).toLowerCase();
    return LANGS[nav] ? nav : 'en';
}

function t(key, vars) {
    let str = (T[currentLang] && T[currentLang][key]) || T.en[key] || key;
    if (vars) {
        for (const [k, v] of Object.entries(vars)) {
            str = str.replace(new RegExp(`\\{${k}\\}`, 'g'), v);
        }
    }
    return str;
}

function setLang(lang) {
    currentLang = lang;
    localStorage.setItem('aegis_lang', lang);
    document.documentElement.dir = LANGS[lang].dir;
    document.documentElement.lang = lang;
    if (typeof applyTranslations === 'function') applyTranslations();
}

function renderLangSelector(containerId, allowedLangs) {
    const el = document.getElementById(containerId);
    if (!el) return;
    const langs = allowedLangs || Object.keys(LANGS);

    // Globe button + dropdown
    const currentName = LANGS[currentLang]?.name || 'English';
    el.innerHTML = `
        <button class="lang-globe" onclick="this.parentElement.classList.toggle('lang-open')" title="Language">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <path d="M2 12h20M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10A15.3 15.3 0 0112 2z"/>
            </svg>
        </button>
        <div class="lang-dropdown">
            ${langs.map(l => `
                <button class="lang-option ${l === currentLang ? 'lang-selected' : ''}"
                        onclick="setLang('${l}'); this.closest('.lang-bar').classList.remove('lang-open');">
                    <span class="lang-option-label">${LANGS[l].label}</span>
                    <span class="lang-option-name">${LANGS[l].name}</span>
                </button>
            `).join('')}
        </div>`;
}

// Close dropdown on outside click
document.addEventListener('click', (e) => {
    const bar = document.getElementById('langBar');
    if (bar && !bar.contains(e.target)) bar.classList.remove('lang-open');
});

// Apply direction on load
document.documentElement.dir = LANGS[currentLang]?.dir || 'ltr';
document.documentElement.lang = currentLang;
