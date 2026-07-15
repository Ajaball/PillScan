/* ═══════════════════════════════════════════════════════════════════
   PillScan PWA — Internationalization (i18n)
   Arabic (RTL) + English translations for all screens
   ═══════════════════════════════════════════════════════════════════ */

const translations = {
  ar: {
    // ── App ────────────────────────────────────────────────────────
    app_name: 'بيل سكان',
    app_tagline: 'ماسح الأدوية الذكي',

    // ── Navigation ─────────────────────────────────────────────────
    nav_home: 'الرئيسية',
    nav_scan: 'فحص',
    nav_meds: 'أدويتي',
    nav_history: 'السجل',
    nav_profile: 'حسابي',

    // ── Common ─────────────────────────────────────────────────────
    save: 'حفظ',
    cancel: 'إلغاء',
    delete: 'حذف',
    edit: 'تعديل',
    add: 'إضافة',
    confirm: 'تأكيد',
    back: 'رجوع',
    next: 'التالي',
    skip: 'تخطي',
    done: 'تم',
    close: 'إغلاق',
    search: 'بحث',
    loading: 'جاري التحميل...',
    retry: 'إعادة المحاولة',
    no_data: 'لا توجد بيانات',
    error_generic: 'حدث خطأ، يرجى المحاولة لاحقاً',
    success: 'تمت العملية بنجاح',
    yes: 'نعم',
    no: 'لا',
    or: 'أو',
    required: 'مطلوب',
    optional: 'اختياري',

    // ── Onboarding ─────────────────────────────────────────────────
    onboarding_title_1: 'تعرّف على أدويتك',
    onboarding_desc_1: 'وجّه الكاميرا نحو أي حبة دواء واحصل على معلوماتها فوراً بدقة عالية',
    onboarding_title_2: 'إدارة أدويتك بذكاء',
    onboarding_desc_2: 'أضف أدويتك وحدد مواعيدها واحصل على تنبيهات لا تنسى',
    onboarding_title_3: 'تتبع التزامك',
    onboarding_desc_3: 'راقب مدى التزامك بأدويتك عبر إحصائيات مفصلة وتقويم بصري',
    onboarding_start: 'ابدأ الآن',

    // ── Auth ───────────────────────────────────────────────────────
    login: 'تسجيل الدخول',
    register: 'إنشاء حساب',
    logout: 'تسجيل الخروج',
    email: 'البريد الإلكتروني',
    password: 'كلمة المرور',
    confirm_password: 'تأكيد كلمة المرور',
    full_name: 'الاسم الكامل',
    phone: 'رقم الهاتف',
    forgot_password: 'نسيت كلمة المرور؟',
    no_account: 'ليس لديك حساب؟',
    have_account: 'لديك حساب بالفعل؟',
    create_account: 'إنشاء حساب جديد',
    login_welcome: 'مرحباً بك مجدداً',
    login_subtitle: 'سجّل دخولك للوصول إلى أدويتك',
    register_welcome: 'إنشاء حساب جديد',
    register_subtitle: 'انضم إلى بيل سكان لإدارة أدويتك',
    password_min: 'كلمة المرور يجب أن تكون 8 أحرف على الأقل',
    passwords_mismatch: 'كلمات المرور غير متطابقة',
    invalid_email: 'البريد الإلكتروني غير صالح',
    login_error: 'البريد الإلكتروني أو كلمة المرور غير صحيحة',
    register_success: 'تم إنشاء الحساب بنجاح',

    // ── Forgot Password ────────────────────────────────────────────
    forgot_title: 'استعادة كلمة المرور',
    forgot_subtitle: 'أدخل بريدك الإلكتروني لإرسال رمز التأكيد',
    send_code: 'إرسال الرمز',
    enter_otp: 'أدخل رمز التأكيد',
    new_password: 'كلمة المرور الجديدة',
    reset_password: 'إعادة تعيين',
    reset_success: 'تم إعادة تعيين كلمة المرور بنجاح',

    // ── Home ───────────────────────────────────────────────────────
    greeting_morning: 'صباح الخير',
    greeting_afternoon: 'مساء الخير',
    greeting_evening: 'مساء الخير',
    today_meds: 'أدوية اليوم',
    quick_scan: 'فحص سريع',
    weekly_adherence: 'الالتزام هذا الأسبوع',
    last_scan: 'آخر فحص',
    no_meds_today: 'لا توجد أدوية مجدولة لليوم',
    add_first_med: 'أضف دواءك الأول',
    taken: 'تم أخذه',
    pending: 'معلق',
    missed: 'فائت',
    skipped: 'تم تخطيه',

    // ── Scanner ────────────────────────────────────────────────────
    scanner_title: 'فحص الدواء',
    scanner_hint: 'ضع الحبة في المنتصف',
    capture: 'التقاط',
    upload_image: 'رفع صورة',
    camera_error: 'لا يمكن الوصول للكاميرا',
    camera_permission: 'يرجى السماح بالوصول للكاميرا',
    scanning: 'جاري الفحص...',
    retake: 'إعادة التقاط',

    // ── Scan Results ───────────────────────────────────────────────
    results_title: 'نتائج الفحص',
    top_match: 'أفضل تطابق',
    confidence: 'نسبة الثقة',
    other_matches: 'نتائج أخرى محتملة',
    add_to_meds: 'إضافة لأدويتي',
    new_scan: 'فحص جديد',
    no_results: 'لم يتم التعرف على الدواء',
    source_ai: 'ذكاء اصطناعي',
    ai_suggestion_note: 'اقتراح بالذكاء الاصطناعي — غير مسجّل في قاعدة البيانات. تحقّق من النشرة أو استشر الصيدلي.',

    // ── Leaflet Summary ────────────────────────────────────────────
    leaflet_card_title: 'تلخيص نشرة الدواء',
    leaflet_card_desc: 'صوّر النشرة أو الوصفة واحصل على ملخّص بالعربي',
    leaflet_title: 'مسح النشرة',
    leaflet_hint: 'ضع نشرة الدواء أو الوصفة داخل الإطار',
    leaflet_summarizing: 'جاري قراءة النشرة وتلخيصها...',
    leaflet_summary_title: 'ملخّص النشرة',
    leaflet_ai_summary: 'ملخّص بالذكاء الاصطناعي',
    leaflet_no_summary: 'لا يوجد ملخّص لعرضه',
    leaflet_new_scan: 'مسح نشرة جديدة',

    // ── Drug Details ───────────────────────────────────────────────
    drug_details: 'تفاصيل الدواء',
    generic_name: 'الاسم العلمي',
    dosage_form: 'الشكل الدوائي',
    strength: 'التركيز',
    manufacturer: 'الشركة المصنعة',
    description: 'الوصف',
    usage_instructions: 'تعليمات الاستخدام',
    side_effects: 'الآثار الجانبية',
    contraindications: 'موانع الاستعمال',
    storage: 'التخزين',
    requires_prescription: 'يحتاج وصفة طبية',
    otc: 'بدون وصفة',
    severity_mild: 'خفيف',
    severity_moderate: 'متوسط',
    severity_severe: 'شديد',
    pill_shape: 'الشكل',
    pill_color: 'اللون',

    // ── Drug Search ────────────────────────────────────────────────
    search_drugs: 'البحث عن دواء',
    search_placeholder: 'اكتب اسم الدواء...',
    filter_shape: 'الشكل',
    filter_color: 'اللون',
    filter_category: 'الفئة',
    no_results_found: 'لم يتم العثور على نتائج',

    // ── Medications ────────────────────────────────────────────────
    my_medications: 'أدويتي',
    add_medication: 'إضافة دواء',
    edit_medication: 'تعديل الدواء',
    medication_name: 'اسم الدواء',
    custom_name: 'اسم مخصص',
    dosage: 'الجرعة',
    frequency: 'التكرار',
    start_date: 'تاريخ البدء',
    end_date: 'تاريخ الانتهاء',
    notes: 'ملاحظات',
    active: 'نشط',
    inactive: 'غير نشط',
    no_medications: 'لم تضف أي أدوية بعد',
    delete_medication: 'هل تريد حذف هذا الدواء؟',
    frequency_daily: 'يومياً',
    frequency_twice: 'مرتين يومياً',
    frequency_three: 'ثلاث مرات يومياً',
    frequency_weekly: 'أسبوعياً',
    frequency_custom: 'مخصص',

    // ── Reminders ──────────────────────────────────────────────────
    reminders: 'التنبيهات',
    add_reminder: 'إضافة تنبيه',
    edit_reminder: 'تعديل التنبيه',
    reminder_time: 'وقت التنبيه',
    reminder_days: 'أيام التنبيه',
    no_reminders: 'لا توجد تنبيهات',
    reminder_enabled: 'التنبيه مفعّل',
    reminder_disabled: 'التنبيه معطّل',
    snooze: 'تأجيل',
    snooze_minutes: 'تأجيل لمدة {min} دقائق',
    day_sat: 'سبت',
    day_sun: 'أحد',
    day_mon: 'إثنين',
    day_tue: 'ثلاثاء',
    day_wed: 'أربعاء',
    day_thu: 'خميس',
    day_fri: 'جمعة',

    // ── Adherence ──────────────────────────────────────────────────
    adherence: 'الالتزام',
    adherence_rate: 'نسبة الالتزام',
    streak: 'سلسلة الأيام',
    streak_days: '{n} يوم متتالي',
    total_scheduled: 'إجمالي المجدول',
    period_week: 'أسبوع',
    period_month: 'شهر',
    period_year: 'سنة',
    calendar_view: 'عرض التقويم',
    stats_view: 'عرض الإحصائيات',
    great_job: 'أداء ممتاز! 🎉',
    keep_going: 'استمر في الالتزام 💪',
    needs_improvement: 'يمكنك تحسين التزامك',

    // ── Profile ────────────────────────────────────────────────────
    profile: 'الملف الشخصي',
    settings: 'الإعدادات',
    language: 'اللغة',
    dark_mode: 'الوضع المظلم',
    notifications: 'الإشعارات',
    font_size: 'حجم الخط',
    about: 'عن التطبيق',
    version: 'الإصدار',
    delete_account: 'حذف الحساب',
    delete_account_confirm: 'هل أنت متأكد من حذف حسابك؟ لا يمكن التراجع عن هذا الإجراء.',
    logout_confirm: 'هل تريد تسجيل الخروج؟',
    arabic: 'العربية',
    english: 'English',
    scan_history: 'سجل الفحوصات',

    // ── AI Settings ────────────────────────────────────────────────
    ai_settings: 'إعدادات الذكاء الاصطناعي',
    ai_settings_desc: 'أضف مفاتيح Gemini للتعرّف على الأدوية وتلخيص النشرات',
    ai_settings_intro: 'أضف مفاتيح Gemini الخاصة بك لتشغيل التعرّف على الأدوية وتلخيص النشرات. تُحفظ المفاتيح مشفّرة ولا تظهر مرة أخرى.',
    ai_failover_note: 'يمكنك إضافة حتى 5 مفاتيح Gemini. يجرّبها التطبيق بالترتيب — إذا انتهى رصيد المفتاح الأول أو فشل، ينتقل للمفتاح التالي تلقائيًا.',
    ai_gemini_key: 'مفتاح Gemini',
    ai_key_placeholder: 'الصق المفتاح هنا...',
    ai_key_configured: 'مُفعّل',
    ai_key_not_configured: 'غير مُضاف',
    ai_key_saved_hint: 'مفتاح محفوظ',
    ai_clear_key: 'حذف المفتاح',
    ai_get_gemini_key: 'احصل على مفتاح Gemini من Google AI Studio',
    ai_get_openai_key: 'احصل على مفتاح OpenAI من platform.openai.com',
    ai_settings_saved: 'تم حفظ الإعدادات',
    ai_key_cleared: 'تم حذف المفتاح',
    ai_no_changes: 'لا توجد تغييرات لحفظها',
    ai_model: 'الموديل',

    // ── Registration / Approval ────────────────────────────────────
    phone_required: 'رقم الجوال مطلوب',
    invalid_phone: 'رقم الجوال غير صالح',
    register_pending_title: 'تم استلام طلبك',
    register_pending: 'تم استلام طلبك، بانتظار موافقة المدير',
    account_pending: 'حسابك قيد المراجعة، انتظر موافقة المدير',
    account_rejected: 'تم رفض طلب حسابك',

    // ── Admin Panel ────────────────────────────────────────────────
    admin_panel: 'لوحة الإدارة',
    admin_panel_desc: 'إدارة طلبات التسجيل والمستخدمين',
    admin_pending_requests: 'طلبات معلّقة',
    admin_all_users: 'كل المستخدمين',
    admin_no_pending: 'لا توجد طلبات معلّقة',
    admin_no_users: 'لا يوجد مستخدمون',
    admin_approve: 'قبول',
    admin_reject: 'رفض',
    admin_request_date: 'تاريخ الطلب',
    admin_status_updated: 'تم تحديث الحالة',
    status_pending: 'قيد المراجعة',
    status_approved: 'مقبول',
    status_rejected: 'مرفوض',
    role_admin: 'مدير',
    role_user: 'مستخدم',

    // ── Pharmacist Assistant ───────────────────────────────────────
    assistant_title: 'المساعد الدوائي',
    assistant_card_title: 'المساعد الدوائي',
    assistant_card_desc: 'اكتب اسم الدواء واحصل على معلومات عامة موثوقة',
    assistant_placeholder: 'اكتب اسم الدواء...',
    assistant_loading: 'جاري جلب المعلومات الدوائية...',
    assistant_empty: 'اكتب اسم دواء لبدء البحث',
    assistant_disclaimer: 'هذه المعلومات للتوعية فقط ولا تغني عن استشارة الطبيب أو الصيدلي المختص.',
    assistant_not_recognized: 'لم يتم التعرف على هذا الدواء بشكل مؤكد',
    assistant_not_configured: 'خدمة المساعد غير مفعّلة بعد. أضف مفتاح Gemini من إعدادات الذكاء الاصطناعي.',
    assistant_uses: 'دواعي الاستعمال',
    assistant_interactions: 'تفاعلات دوائية مهمة',
    assistant_warnings: 'تحذيرات',
    assistant_ask_about: 'اسأل المساعد الدوائي',
    ai_test_keys: 'اختبار المفاتيح',
    ai_key_ok: 'يعمل ✓',
    ai_key_failed: 'فشل',
    ai_test_ok: 'المفاتيح تعمل ✅ — التعرّف والتلخيص جاهزان.',
    ai_test_fail: 'كل المفاتيح فشلت. تحقّق من صحة المفتاح، أو أن خدمة Generative Language مفعّلة في Google، أو أن الرصيد لم ينتهِ.',

    // ── Offline ────────────────────────────────────────────────────
    offline_title: 'لا يوجد اتصال',
    offline_message: 'يرجى التحقق من اتصالك بالإنترنت',

    // ── Install PWA ────────────────────────────────────────────────
    install_prompt: 'أضف بيل سكان إلى شاشتك الرئيسية',
    install_button: 'تثبيت',
    install_dismiss: 'لاحقاً',
  },

  en: {
    // ── App ────────────────────────────────────────────────────────
    app_name: 'PillScan',
    app_tagline: 'AI-Powered Pill Scanner',

    // ── Navigation ─────────────────────────────────────────────────
    nav_home: 'Home',
    nav_scan: 'Scan',
    nav_meds: 'My Meds',
    nav_history: 'History',
    nav_profile: 'Profile',

    // ── Common ─────────────────────────────────────────────────────
    save: 'Save',
    cancel: 'Cancel',
    delete: 'Delete',
    edit: 'Edit',
    add: 'Add',
    confirm: 'Confirm',
    back: 'Back',
    next: 'Next',
    skip: 'Skip',
    done: 'Done',
    close: 'Close',
    search: 'Search',
    loading: 'Loading...',
    retry: 'Retry',
    no_data: 'No data available',
    error_generic: 'Something went wrong, please try again',
    success: 'Operation completed successfully',
    yes: 'Yes',
    no: 'No',
    or: 'or',
    required: 'Required',
    optional: 'Optional',

    // ── Onboarding ─────────────────────────────────────────────────
    onboarding_title_1: 'Identify Your Pills',
    onboarding_desc_1: 'Point your camera at any pill and get instant AI-powered identification',
    onboarding_title_2: 'Manage Your Medications',
    onboarding_desc_2: 'Add your medications, set schedules, and never miss a dose',
    onboarding_title_3: 'Track Your Adherence',
    onboarding_desc_3: 'Monitor your medication compliance with detailed stats and calendar view',
    onboarding_start: 'Get Started',

    // ── Auth ───────────────────────────────────────────────────────
    login: 'Log In',
    register: 'Register',
    logout: 'Log Out',
    email: 'Email',
    password: 'Password',
    confirm_password: 'Confirm Password',
    full_name: 'Full Name',
    phone: 'Phone Number',
    forgot_password: 'Forgot Password?',
    no_account: "Don't have an account?",
    have_account: 'Already have an account?',
    create_account: 'Create Account',
    login_welcome: 'Welcome Back',
    login_subtitle: 'Log in to access your medications',
    register_welcome: 'Create Account',
    register_subtitle: 'Join PillScan to manage your meds',
    password_min: 'Password must be at least 8 characters',
    passwords_mismatch: 'Passwords do not match',
    invalid_email: 'Invalid email address',
    login_error: 'Incorrect email or password',
    register_success: 'Account created successfully',

    // ── Forgot Password ────────────────────────────────────────────
    forgot_title: 'Reset Password',
    forgot_subtitle: 'Enter your email to receive a reset code',
    send_code: 'Send Code',
    enter_otp: 'Enter verification code',
    new_password: 'New Password',
    reset_password: 'Reset Password',
    reset_success: 'Password reset successfully',

    // ── Home ───────────────────────────────────────────────────────
    greeting_morning: 'Good Morning',
    greeting_afternoon: 'Good Afternoon',
    greeting_evening: 'Good Evening',
    today_meds: "Today's Medications",
    quick_scan: 'Quick Scan',
    weekly_adherence: 'Weekly Adherence',
    last_scan: 'Last Scan',
    no_meds_today: 'No medications scheduled for today',
    add_first_med: 'Add your first medication',
    taken: 'Taken',
    pending: 'Pending',
    missed: 'Missed',
    skipped: 'Skipped',

    // ── Scanner ────────────────────────────────────────────────────
    scanner_title: 'Scan Pill',
    scanner_hint: 'Place the pill in the center',
    capture: 'Capture',
    upload_image: 'Upload Image',
    camera_error: 'Cannot access camera',
    camera_permission: 'Please allow camera access',
    scanning: 'Scanning...',
    retake: 'Retake',

    // ── Scan Results ───────────────────────────────────────────────
    results_title: 'Scan Results',
    top_match: 'Top Match',
    confidence: 'Confidence',
    other_matches: 'Other Possible Matches',
    add_to_meds: 'Add to My Medications',
    new_scan: 'New Scan',
    no_results: 'Could not identify the pill',
    source_ai: 'AI',
    ai_suggestion_note: 'AI suggestion — not in the database. Verify with the leaflet or ask a pharmacist.',

    // ── Leaflet Summary ────────────────────────────────────────────
    leaflet_card_title: 'Summarize Leaflet',
    leaflet_card_desc: 'Scan a leaflet or prescription for an Arabic summary',
    leaflet_title: 'Scan Leaflet',
    leaflet_hint: 'Place the leaflet or prescription inside the frame',
    leaflet_summarizing: 'Reading and summarizing the leaflet...',
    leaflet_summary_title: 'Leaflet Summary',
    leaflet_ai_summary: 'AI Summary',
    leaflet_no_summary: 'No summary to display',
    leaflet_new_scan: 'Scan New Leaflet',

    // ── Drug Details ───────────────────────────────────────────────
    drug_details: 'Drug Details',
    generic_name: 'Generic Name',
    dosage_form: 'Dosage Form',
    strength: 'Strength',
    manufacturer: 'Manufacturer',
    description: 'Description',
    usage_instructions: 'Usage Instructions',
    side_effects: 'Side Effects',
    contraindications: 'Contraindications',
    storage: 'Storage',
    requires_prescription: 'Prescription Required',
    otc: 'Over the Counter',
    severity_mild: 'Mild',
    severity_moderate: 'Moderate',
    severity_severe: 'Severe',
    pill_shape: 'Shape',
    pill_color: 'Color',

    // ── Drug Search ────────────────────────────────────────────────
    search_drugs: 'Search Drugs',
    search_placeholder: 'Type drug name...',
    filter_shape: 'Shape',
    filter_color: 'Color',
    filter_category: 'Category',
    no_results_found: 'No results found',

    // ── Medications ────────────────────────────────────────────────
    my_medications: 'My Medications',
    add_medication: 'Add Medication',
    edit_medication: 'Edit Medication',
    medication_name: 'Medication Name',
    custom_name: 'Custom Name',
    dosage: 'Dosage',
    frequency: 'Frequency',
    start_date: 'Start Date',
    end_date: 'End Date',
    notes: 'Notes',
    active: 'Active',
    inactive: 'Inactive',
    no_medications: "You haven't added any medications yet",
    delete_medication: 'Delete this medication?',
    frequency_daily: 'Daily',
    frequency_twice: 'Twice Daily',
    frequency_three: 'Three Times Daily',
    frequency_weekly: 'Weekly',
    frequency_custom: 'Custom',

    // ── Reminders ──────────────────────────────────────────────────
    reminders: 'Reminders',
    add_reminder: 'Add Reminder',
    edit_reminder: 'Edit Reminder',
    reminder_time: 'Reminder Time',
    reminder_days: 'Reminder Days',
    no_reminders: 'No reminders set',
    reminder_enabled: 'Reminder enabled',
    reminder_disabled: 'Reminder disabled',
    snooze: 'Snooze',
    snooze_minutes: 'Snoozed for {min} minutes',
    day_sat: 'Sat',
    day_sun: 'Sun',
    day_mon: 'Mon',
    day_tue: 'Tue',
    day_wed: 'Wed',
    day_thu: 'Thu',
    day_fri: 'Fri',

    // ── Adherence ──────────────────────────────────────────────────
    adherence: 'Adherence',
    adherence_rate: 'Adherence Rate',
    streak: 'Streak',
    streak_days: '{n} day streak',
    total_scheduled: 'Total Scheduled',
    period_week: 'Week',
    period_month: 'Month',
    period_year: 'Year',
    calendar_view: 'Calendar View',
    stats_view: 'Statistics View',
    great_job: 'Great job! 🎉',
    keep_going: 'Keep it up 💪',
    needs_improvement: 'Room for improvement',

    // ── Profile ────────────────────────────────────────────────────
    profile: 'Profile',
    settings: 'Settings',
    language: 'Language',
    dark_mode: 'Dark Mode',
    notifications: 'Notifications',
    font_size: 'Font Size',
    about: 'About',
    version: 'Version',
    delete_account: 'Delete Account',
    delete_account_confirm: 'Are you sure you want to delete your account? This action cannot be undone.',
    logout_confirm: 'Are you sure you want to log out?',
    arabic: 'العربية',
    english: 'English',
    scan_history: 'Scan History',

    // ── AI Settings ────────────────────────────────────────────────
    ai_settings: 'AI Settings',
    ai_settings_desc: 'Add Gemini keys for pill ID & leaflet summaries',
    ai_settings_intro: 'Add your own Gemini keys to enable pill identification and leaflet summaries. Keys are stored encrypted and never shown again.',
    ai_failover_note: 'You can add up to 5 Gemini keys. The app tries them in order — if the first is exhausted or fails, it moves to the next automatically.',
    ai_gemini_key: 'Gemini Key',
    ai_key_placeholder: 'Paste your key here...',
    ai_key_configured: 'Configured',
    ai_key_not_configured: 'Not set',
    ai_key_saved_hint: 'Key saved',
    ai_clear_key: 'Remove key',
    ai_get_gemini_key: 'Get a Gemini key from Google AI Studio',
    ai_get_openai_key: 'Get an OpenAI key from platform.openai.com',
    ai_settings_saved: 'Settings saved',
    ai_key_cleared: 'Key removed',
    ai_model: 'Model',
    ai_test_keys: 'Test keys',
    ai_key_ok: 'Works ✓',
    ai_key_failed: 'Failed',
    ai_test_ok: 'Keys work ✅ — identification and summaries are ready.',
    ai_test_fail: 'All keys failed. Check the key is correct, the Generative Language API is enabled in Google, and the quota is not exhausted.',
    ai_no_changes: 'No changes to save',

    // ── Registration / Approval ────────────────────────────────────
    phone_required: 'Phone number is required',
    invalid_phone: 'Invalid phone number',
    register_pending_title: 'Request received',
    register_pending: 'Your request has been received and is awaiting admin approval',
    account_pending: 'Your account is under review, please wait for admin approval',
    account_rejected: 'Your account request was rejected',

    // ── Admin Panel ────────────────────────────────────────────────
    admin_panel: 'Admin Panel',
    admin_panel_desc: 'Manage sign-up requests and users',
    admin_pending_requests: 'Pending Requests',
    admin_all_users: 'All Users',
    admin_no_pending: 'No pending requests',
    admin_no_users: 'No users',
    admin_approve: 'Approve',
    admin_reject: 'Reject',
    admin_request_date: 'Request date',
    admin_status_updated: 'Status updated',
    status_pending: 'Pending',
    status_approved: 'Approved',
    status_rejected: 'Rejected',
    role_admin: 'Admin',
    role_user: 'User',

    // ── Pharmacist Assistant ───────────────────────────────────────
    assistant_title: 'Drug Assistant',
    assistant_card_title: 'Drug Assistant',
    assistant_card_desc: 'Type a drug name for reliable general info',
    assistant_placeholder: 'Type drug name...',
    assistant_loading: 'Fetching drug information...',
    assistant_empty: 'Type a drug name to start',
    assistant_disclaimer: 'This information is for awareness only and is not a substitute for consulting a doctor or pharmacist.',
    assistant_not_recognized: 'This drug could not be confidently recognized',
    assistant_not_configured: 'The assistant is not enabled yet. Add a Gemini key in AI settings.',
    assistant_uses: 'Uses',
    assistant_interactions: 'Important Drug Interactions',
    assistant_warnings: 'Warnings',
    assistant_ask_about: 'Ask the Drug Assistant',

    // ── Offline ────────────────────────────────────────────────────
    offline_title: 'No Connection',
    offline_message: 'Please check your internet connection',

    // ── Install PWA ────────────────────────────────────────────────
    install_prompt: 'Add PillScan to your home screen',
    install_button: 'Install',
    install_dismiss: 'Later',
  }
};

/* ── i18n Engine ──────────────────────────────────────────────────── */

class I18n {
  constructor() {
    this.currentLang = localStorage.getItem('pillscan_lang') || 'ar';
    this.listeners = [];
  }

  /** Get translated string by key */
  t(key, params = {}) {
    const lang = translations[this.currentLang] || translations.ar;
    let text = lang[key] || translations.ar[key] || key;
    // Replace params like {n} or {min}
    Object.entries(params).forEach(([k, v]) => {
      text = text.replace(`{${k}}`, v);
    });
    return text;
  }

  /** Get current language */
  get lang() {
    return this.currentLang;
  }

  /** Check if current language is RTL */
  get isRTL() {
    return this.currentLang === 'ar';
  }

  /** Get text direction */
  get dir() {
    return this.isRTL ? 'rtl' : 'ltr';
  }

  /** Switch language */
  setLang(lang) {
    if (lang !== 'ar' && lang !== 'en') return;
    this.currentLang = lang;
    localStorage.setItem('pillscan_lang', lang);

    // Update document attributes
    document.documentElement.lang = lang;
    document.documentElement.dir = this.dir;
    document.documentElement.setAttribute('data-lang', lang);

    // Notify listeners
    this.listeners.forEach(fn => fn(lang));
  }

  /** Toggle language */
  toggleLang() {
    this.setLang(this.currentLang === 'ar' ? 'en' : 'ar');
  }

  /** Register change listener */
  onChange(fn) {
    this.listeners.push(fn);
    return () => {
      this.listeners = this.listeners.filter(l => l !== fn);
    };
  }

  /** Initialize — apply language to document */
  init() {
    document.documentElement.lang = this.currentLang;
    document.documentElement.dir = this.dir;
    document.documentElement.setAttribute('data-lang', this.currentLang);
  }
}

// Singleton
const i18n = new I18n();

export default i18n;
export { translations };
