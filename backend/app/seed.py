"""
Database Seed Script
Populates the drug database with common medications found in Saudi Arabia.
Run: python -m app.seed
"""

import asyncio
from app.database import AsyncSessionLocal, create_tables
from app.models.drug import Drug, DrugSideEffect, DrugContraindication, DrugImage

# Common medications available in Saudi Arabia (SFDA registered)
SEED_DRUGS = [
    {
        "name_en": "Panadol Extra",
        "name_ar": "بانادول إكسترا",
        "generic_name_en": "Paracetamol + Caffeine",
        "generic_name_ar": "باراسيتامول + كافيين",
        "manufacturer": "GlaxoSmithKline",
        "shape": "oval",
        "color": "white",
        "imprint": "PANADOL",
        "dosage_form": "Film-coated tablet",
        "strength": "500mg/65mg",
        "description_en": "Panadol Extra is used for the relief of mild to moderate pain including headache, migraine, toothache, sore throat, period pain, and fever.",
        "description_ar": "بانادول إكسترا يُستخدم لتخفيف الألم الخفيف إلى المعتدل بما في ذلك الصداع والشقيقة وألم الأسنان والتهاب الحلق وآلام الدورة الشهرية والحمى.",
        "usage_instructions_en": "Adults: 1-2 tablets every 4-6 hours. Maximum 8 tablets in 24 hours.",
        "usage_instructions_ar": "البالغون: 1-2 قرص كل 4-6 ساعات. الحد الأقصى 8 أقراص في 24 ساعة.",
        "storage_instructions": "Store below 25°C. Keep out of reach of children.",
        "category": "Analgesic",
        "requires_prescription": False,
        "model_class_id": 0,
        "side_effects": [
            {"effect_en": "Nausea", "effect_ar": "غثيان", "severity": "mild"},
            {"effect_en": "Allergic skin reaction", "effect_ar": "تفاعل جلدي تحسسي", "severity": "moderate"},
            {"effect_en": "Liver damage (overdose)", "effect_ar": "تلف الكبد (جرعة زائدة)", "severity": "severe"},
        ],
        "contraindications": [
            {"contraindication_en": "Severe liver disease", "contraindication_ar": "أمراض الكبد الحادة"},
            {"contraindication_en": "Allergy to paracetamol", "contraindication_ar": "حساسية من الباراسيتامول"},
        ],
    },
    {
        "name_en": "Amoxil",
        "name_ar": "أموكسيل",
        "generic_name_en": "Amoxicillin",
        "generic_name_ar": "أموكسيسيلين",
        "manufacturer": "GlaxoSmithKline",
        "shape": "capsule",
        "color": "red/yellow",
        "imprint": "AMOXIL 500",
        "dosage_form": "Capsule",
        "strength": "500mg",
        "description_en": "Amoxil is a penicillin antibiotic used to treat bacterial infections of the ear, nose, throat, urinary tract, and skin.",
        "description_ar": "أموكسيل هو مضاد حيوي من البنسلين يُستخدم لعلاج العدوى البكتيرية في الأذن والأنف والحلق والمسالك البولية والجلد.",
        "usage_instructions_en": "Adults: 250-500mg every 8 hours. Complete the full course as prescribed.",
        "usage_instructions_ar": "البالغون: 250-500 ملجم كل 8 ساعات. أكمل الجرعة الكاملة كما وصفها الطبيب.",
        "storage_instructions": "Store below 25°C. Keep dry.",
        "category": "Antibiotic",
        "requires_prescription": True,
        "model_class_id": 1,
        "side_effects": [
            {"effect_en": "Diarrhea", "effect_ar": "إسهال", "severity": "mild"},
            {"effect_en": "Nausea and vomiting", "effect_ar": "غثيان وقيء", "severity": "mild"},
            {"effect_en": "Skin rash", "effect_ar": "طفح جلدي", "severity": "moderate"},
            {"effect_en": "Anaphylaxis (rare)", "effect_ar": "صدمة تحسسية (نادرة)", "severity": "severe"},
        ],
        "contraindications": [
            {"contraindication_en": "Penicillin allergy", "contraindication_ar": "حساسية من البنسلين"},
            {"contraindication_en": "Infectious mononucleosis", "contraindication_ar": "داء كثرة الوحيدات العدوائية"},
        ],
    },
    {
        "name_en": "Glucophage",
        "name_ar": "جلوكوفاج",
        "generic_name_en": "Metformin",
        "generic_name_ar": "ميتفورمين",
        "manufacturer": "Merck",
        "shape": "round",
        "color": "white",
        "imprint": "500",
        "dosage_form": "Film-coated tablet",
        "strength": "500mg",
        "description_en": "Glucophage is used to treat type 2 diabetes. It helps control blood sugar levels.",
        "description_ar": "جلوكوفاج يُستخدم لعلاج مرض السكري من النوع الثاني. يساعد على التحكم في مستويات السكر في الدم.",
        "usage_instructions_en": "Adults: Start with 500mg once or twice daily with meals. Maximum 2550mg/day.",
        "usage_instructions_ar": "البالغون: ابدأ بـ 500 ملجم مرة أو مرتين يومياً مع الوجبات. الحد الأقصى 2550 ملجم يومياً.",
        "storage_instructions": "Store below 30°C.",
        "category": "Antidiabetic",
        "requires_prescription": True,
        "model_class_id": 2,
        "side_effects": [
            {"effect_en": "Nausea", "effect_ar": "غثيان", "severity": "mild"},
            {"effect_en": "Diarrhea", "effect_ar": "إسهال", "severity": "mild"},
            {"effect_en": "Abdominal pain", "effect_ar": "ألم في البطن", "severity": "mild"},
            {"effect_en": "Lactic acidosis (rare)", "effect_ar": "حماض لبني (نادر)", "severity": "severe"},
        ],
        "contraindications": [
            {"contraindication_en": "Severe renal impairment", "contraindication_ar": "قصور كلوي حاد"},
            {"contraindication_en": "Diabetic ketoacidosis", "contraindication_ar": "الحماض الكيتوني السكري"},
        ],
    },
    {
        "name_en": "Lipitor",
        "name_ar": "ليبيتور",
        "generic_name_en": "Atorvastatin",
        "generic_name_ar": "أتورفاستاتين",
        "manufacturer": "Pfizer",
        "shape": "oval",
        "color": "white",
        "imprint": "PD 155",
        "dosage_form": "Film-coated tablet",
        "strength": "10mg",
        "description_en": "Lipitor is used to lower cholesterol and reduce the risk of cardiovascular disease.",
        "description_ar": "ليبيتور يُستخدم لخفض الكوليسترول وتقليل خطر الإصابة بأمراض القلب والأوعية الدموية.",
        "usage_instructions_en": "Adults: 10-80mg once daily. Can be taken at any time of day with or without food.",
        "usage_instructions_ar": "البالغون: 10-80 ملجم مرة واحدة يومياً. يمكن تناوله في أي وقت من اليوم مع أو بدون طعام.",
        "storage_instructions": "Store below 30°C. Protect from moisture.",
        "category": "Statin",
        "requires_prescription": True,
        "model_class_id": 3,
        "side_effects": [
            {"effect_en": "Muscle pain", "effect_ar": "ألم في العضلات", "severity": "mild"},
            {"effect_en": "Joint pain", "effect_ar": "ألم في المفاصل", "severity": "mild"},
            {"effect_en": "Liver enzyme elevation", "effect_ar": "ارتفاع إنزيمات الكبد", "severity": "moderate"},
            {"effect_en": "Rhabdomyolysis (rare)", "effect_ar": "انحلال الربيدات (نادر)", "severity": "severe"},
        ],
        "contraindications": [
            {"contraindication_en": "Active liver disease", "contraindication_ar": "أمراض الكبد النشطة"},
            {"contraindication_en": "Pregnancy and breastfeeding", "contraindication_ar": "الحمل والرضاعة"},
        ],
    },
    {
        "name_en": "Zestril",
        "name_ar": "زيستريل",
        "generic_name_en": "Lisinopril",
        "generic_name_ar": "ليسينوبريل",
        "manufacturer": "AstraZeneca",
        "shape": "round",
        "color": "pink",
        "imprint": "ZESTRIL 10",
        "dosage_form": "Tablet",
        "strength": "10mg",
        "description_en": "Zestril is used to treat high blood pressure (hypertension) and heart failure.",
        "description_ar": "زيستريل يُستخدم لعلاج ارتفاع ضغط الدم وفشل القلب.",
        "usage_instructions_en": "Adults: Start with 10mg once daily. Maximum 80mg/day.",
        "usage_instructions_ar": "البالغون: ابدأ بـ 10 ملجم مرة واحدة يومياً. الحد الأقصى 80 ملجم يومياً.",
        "storage_instructions": "Store below 25°C. Protect from light.",
        "category": "ACE Inhibitor",
        "requires_prescription": True,
        "model_class_id": 4,
        "side_effects": [
            {"effect_en": "Dry cough", "effect_ar": "سعال جاف", "severity": "mild"},
            {"effect_en": "Dizziness", "effect_ar": "دوخة", "severity": "mild"},
            {"effect_en": "Hyperkalemia", "effect_ar": "ارتفاع البوتاسيوم", "severity": "moderate"},
            {"effect_en": "Angioedema (rare)", "effect_ar": "وذمة وعائية (نادرة)", "severity": "severe"},
        ],
        "contraindications": [
            {"contraindication_en": "History of angioedema", "contraindication_ar": "تاريخ وذمة وعائية"},
            {"contraindication_en": "Pregnancy", "contraindication_ar": "الحمل"},
            {"contraindication_en": "Bilateral renal artery stenosis", "contraindication_ar": "تضيق الشريان الكلوي الثنائي"},
        ],
    },
    {
        "name_en": "Augmentin",
        "name_ar": "أوجمنتين",
        "generic_name_en": "Amoxicillin + Clavulanate",
        "generic_name_ar": "أموكسيسيلين + كلافيولانات",
        "manufacturer": "GlaxoSmithKline",
        "shape": "oval",
        "color": "white",
        "imprint": "AC 625",
        "dosage_form": "Film-coated tablet",
        "strength": "625mg",
        "description_en": "Augmentin is a broad-spectrum antibiotic used to treat various bacterial infections resistant to amoxicillin alone.",
        "description_ar": "أوجمنتين هو مضاد حيوي واسع الطيف يُستخدم لعلاج العدوى البكتيرية المختلفة المقاومة للأموكسيسيلين وحده.",
        "usage_instructions_en": "Adults: 1 tablet (625mg) every 8 hours. Take at the start of a meal.",
        "usage_instructions_ar": "البالغون: قرص واحد (625 ملجم) كل 8 ساعات. يؤخذ في بداية الوجبة.",
        "storage_instructions": "Store below 25°C.",
        "category": "Antibiotic",
        "requires_prescription": True,
        "model_class_id": 5,
        "side_effects": [
            {"effect_en": "Diarrhea", "effect_ar": "إسهال", "severity": "mild"},
            {"effect_en": "Nausea", "effect_ar": "غثيان", "severity": "mild"},
            {"effect_en": "Skin rash", "effect_ar": "طفح جلدي", "severity": "moderate"},
        ],
        "contraindications": [
            {"contraindication_en": "Penicillin allergy", "contraindication_ar": "حساسية من البنسلين"},
            {"contraindication_en": "History of liver problems with this drug", "contraindication_ar": "تاريخ مشاكل الكبد مع هذا الدواء"},
        ],
    },
    {
        "name_en": "Ventolin",
        "name_ar": "فنتولين",
        "generic_name_en": "Salbutamol",
        "generic_name_ar": "سالبوتامول",
        "manufacturer": "GlaxoSmithKline",
        "shape": "round",
        "color": "white",
        "imprint": "V2",
        "dosage_form": "Tablet",
        "strength": "2mg",
        "description_en": "Ventolin is a bronchodilator used to treat bronchospasm in asthma and COPD.",
        "description_ar": "فنتولين هو موسع للقصبات يُستخدم لعلاج التشنج القصبي في الربو ومرض الانسداد الرئوي المزمن.",
        "usage_instructions_en": "Adults: 2-4mg 3-4 times daily. Maximum 32mg/day.",
        "usage_instructions_ar": "البالغون: 2-4 ملجم 3-4 مرات يومياً. الحد الأقصى 32 ملجم يومياً.",
        "storage_instructions": "Store below 30°C. Protect from light.",
        "category": "Bronchodilator",
        "requires_prescription": True,
        "model_class_id": 6,
        "side_effects": [
            {"effect_en": "Tremor", "effect_ar": "رعاش", "severity": "mild"},
            {"effect_en": "Headache", "effect_ar": "صداع", "severity": "mild"},
            {"effect_en": "Rapid heartbeat", "effect_ar": "تسارع ضربات القلب", "severity": "moderate"},
        ],
        "contraindications": [
            {"contraindication_en": "Allergy to salbutamol", "contraindication_ar": "حساسية من السالبوتامول"},
        ],
    },
    {
        "name_en": "Nexium",
        "name_ar": "نيكسيوم",
        "generic_name_en": "Esomeprazole",
        "generic_name_ar": "إيسوميبرازول",
        "manufacturer": "AstraZeneca",
        "shape": "oval",
        "color": "purple",
        "imprint": "20mg",
        "dosage_form": "Delayed-release capsule",
        "strength": "20mg",
        "description_en": "Nexium is a proton pump inhibitor used to treat gastroesophageal reflux disease (GERD) and stomach ulcers.",
        "description_ar": "نيكسيوم هو مثبط لمضخة البروتون يُستخدم لعلاج ارتجاع المريء وقرحة المعدة.",
        "usage_instructions_en": "Adults: 20-40mg once daily, 30 minutes before a meal. Duration: 4-8 weeks.",
        "usage_instructions_ar": "البالغون: 20-40 ملجم مرة واحدة يومياً، قبل الوجبة بـ 30 دقيقة. المدة: 4-8 أسابيع.",
        "storage_instructions": "Store below 30°C. Keep in original packaging.",
        "category": "Proton Pump Inhibitor",
        "requires_prescription": True,
        "model_class_id": 7,
        "side_effects": [
            {"effect_en": "Headache", "effect_ar": "صداع", "severity": "mild"},
            {"effect_en": "Abdominal pain", "effect_ar": "ألم في البطن", "severity": "mild"},
            {"effect_en": "Vitamin B12 deficiency (long-term)", "effect_ar": "نقص فيتامين ب12 (طويل المدى)", "severity": "moderate"},
        ],
        "contraindications": [
            {"contraindication_en": "Known hypersensitivity to PPIs", "contraindication_ar": "فرط حساسية معروف لمثبطات مضخة البروتون"},
        ],
    },
    {
        "name_en": "Concor",
        "name_ar": "كونكور",
        "generic_name_en": "Bisoprolol",
        "generic_name_ar": "بيسوبرولول",
        "manufacturer": "Merck",
        "shape": "heart",
        "color": "yellow",
        "imprint": "BIS 5",
        "dosage_form": "Film-coated tablet",
        "strength": "5mg",
        "description_en": "Concor is a beta-blocker used to treat hypertension, angina, and heart failure.",
        "description_ar": "كونكور هو حاصر للبيتا يُستخدم لعلاج ارتفاع ضغط الدم والذبحة الصدرية وفشل القلب.",
        "usage_instructions_en": "Adults: 5-10mg once daily in the morning.",
        "usage_instructions_ar": "البالغون: 5-10 ملجم مرة واحدة يومياً في الصباح.",
        "storage_instructions": "Store below 30°C.",
        "category": "Beta-Blocker",
        "requires_prescription": True,
        "model_class_id": 8,
        "side_effects": [
            {"effect_en": "Fatigue", "effect_ar": "إرهاق", "severity": "mild"},
            {"effect_en": "Cold hands and feet", "effect_ar": "برودة اليدين والقدمين", "severity": "mild"},
            {"effect_en": "Bradycardia", "effect_ar": "بطء ضربات القلب", "severity": "moderate"},
        ],
        "contraindications": [
            {"contraindication_en": "Severe asthma", "contraindication_ar": "ربو حاد"},
            {"contraindication_en": "Severe bradycardia", "contraindication_ar": "بطء شديد في ضربات القلب"},
            {"contraindication_en": "Uncontrolled heart failure", "contraindication_ar": "فشل قلبي غير متحكم فيه"},
        ],
    },
    {
        "name_en": "Brufen",
        "name_ar": "بروفين",
        "generic_name_en": "Ibuprofen",
        "generic_name_ar": "إيبوبروفين",
        "manufacturer": "Abbott",
        "shape": "round",
        "color": "pink",
        "imprint": "BRUFEN 400",
        "dosage_form": "Film-coated tablet",
        "strength": "400mg",
        "description_en": "Brufen is a non-steroidal anti-inflammatory drug (NSAID) used for pain relief, fever reduction, and inflammation.",
        "description_ar": "بروفين هو مضاد للالتهاب غير الستيرويدي يُستخدم لتخفيف الألم وخفض الحرارة والالتهاب.",
        "usage_instructions_en": "Adults: 200-400mg every 4-6 hours. Maximum 1200mg/day (OTC).",
        "usage_instructions_ar": "البالغون: 200-400 ملجم كل 4-6 ساعات. الحد الأقصى 1200 ملجم يومياً.",
        "storage_instructions": "Store below 25°C.",
        "category": "NSAID",
        "requires_prescription": False,
        "model_class_id": 9,
        "side_effects": [
            {"effect_en": "Stomach upset", "effect_ar": "اضطراب المعدة", "severity": "mild"},
            {"effect_en": "Heartburn", "effect_ar": "حرقة المعدة", "severity": "mild"},
            {"effect_en": "Stomach ulcers (long-term)", "effect_ar": "قرحة المعدة (طويل المدى)", "severity": "severe"},
        ],
        "contraindications": [
            {"contraindication_en": "Active GI bleeding", "contraindication_ar": "نزيف نشط في الجهاز الهضمي"},
            {"contraindication_en": "Severe renal impairment", "contraindication_ar": "قصور كلوي حاد"},
            {"contraindication_en": "Third trimester of pregnancy", "contraindication_ar": "الثلث الأخير من الحمل"},
        ],
    },
    {
        "name_en": "Claritine",
        "name_ar": "كلاريتين",
        "generic_name_en": "Loratadine / Antihistamine",
        "generic_name_ar": "لوراتادين / مضاد هيستامين",
        "manufacturer": "Bayer",
        "shape": "oval",
        "color": "white",
        "imprint": "10",
        "dosage_form": "Tablet",
        "strength": "10mg",
        "description_en": "Claritine is an antihistamine used to treat allergies, runny nose, and itchy eyes.",
        "description_ar": "كلاريتين هو مضاد للهيستامين يُسخدم لعلاج الحساسية وسيلان الأنف وحكة العين.",
        "usage_instructions_en": "Adults: 1 tablet (10mg) once daily.",
        "usage_instructions_ar": "البالغون: قرص واحد (10 ملجم) مرة واحدة يومياً.",
        "storage_instructions": "Store below 25°C.",
        "category": "Antihistamine",
        "requires_prescription": False,
        "model_class_id": 10,
        "side_effects": [
            {"effect_en": "Drowsiness (rare)", "effect_ar": "نعاس (نادر)", "severity": "mild"},
            {"effect_en": "Dry mouth", "effect_ar": "جفاف الفم", "severity": "mild"},
            {"effect_en": "Headache", "effect_ar": "صداع", "severity": "mild"},
        ],
        "contraindications": [
            {"contraindication_en": "Severe liver disease", "contraindication_ar": "أمراض الكبد الحادة"},
        ],
    },
]


async def seed_database():
    """Populate the database with seed drug data."""
    # Ensure tables exist
    await create_tables()

    async with AsyncSessionLocal() as session:
        # Check if drugs already exist
        from sqlalchemy import select, func
        result = await session.execute(select(func.count()).select_from(Drug))
        count = result.scalar()

        # Seed default user if none exists
        from app.models.user import User
        user_result = await session.execute(select(func.count()).select_from(User))
        user_count = user_result.scalar()

        if user_count == 0:
            print("   [INFO] Seeding default demo user...")
            from app.services.auth_service import hash_password
            from app.config import get_settings
            _s = get_settings()
            demo_user = User(
                email=_s.ADMIN_EMAIL,
                password_hash=hash_password(_s.ADMIN_PASSWORD),
                full_name="PillScan Admin",
                language="ar",
                is_admin=True
            )
            session.add(demo_user)
            await session.flush()
            print(f"   [SUCCESS] Seeded default admin user: {_s.ADMIN_EMAIL}")

        if count > 0:
            print(f"   [INFO] Database already has {count} drugs. Skipping seed.")
            await session.commit()
            return

        print("   [INFO] Seeding drug database...")

        for drug_data in SEED_DRUGS:
            side_effects_data = drug_data.pop("side_effects", [])
            contraindications_data = drug_data.pop("contraindications", [])

            drug = Drug(**drug_data)
            session.add(drug)
            await session.flush()

            for se in side_effects_data:
                session.add(DrugSideEffect(drug_id=drug.id, **se))

            for ci in contraindications_data:
                session.add(DrugContraindication(drug_id=drug.id, **ci))

        await session.commit()
        print(f"   [SUCCESS] Seeded {len(SEED_DRUGS)} drugs with side effects and contraindications")


if __name__ == "__main__":
    asyncio.run(seed_database())
