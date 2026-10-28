"""Dummy data for the Telangana Bharat Vistaar prototype.

Everything here is fictional demo data. Numbers are realistic in shape but are
not official figures. A fixed random seed keeps the data identical on every run.
"""
import json
import os
import random
from datetime import date, datetime, timedelta

rng = random.Random(42)
TODAY = date.today()

DISTRICTS = {
    "Adilabad": "ఆదిలాబాద్", "Karimnagar": "కరీంనగర్", "Warangal": "వరంగల్",
    "Nizamabad": "నిజామాబాద్", "Khammam": "ఖమ్మం", "Nalgonda": "నల్గొండ",
    "Mahabubnagar": "మహబూబ్‌నగర్", "Medak": "మెదక్", "Rangareddy": "రంగారెడ్డి",
    "Siddipet": "సిద్దిపేట", "Jagtial": "జగిత్యాల", "Sangareddy": "సంగారెడ్డి",
}

CROPS = {
    "Paddy": "వరి", "Cotton": "పత్తి", "Maize": "మొక్కజొన్న", "Red gram": "కంది",
    "Chilli": "మిరప", "Turmeric": "పసుపు", "Soybean": "సోయాబీన్", "Groundnut": "వేరుశనగ",
}

# Words farmers might type for each crop (English + Telugu + common spellings)
CROP_ALIASES = {
    "Paddy": ["paddy", "rice", "vari", "వరి", "ధాన్యం"],
    "Cotton": ["cotton", "patti", "పత్తి"],
    "Maize": ["maize", "corn", "mokkajonna", "మొక్కజొన్న"],
    "Red gram": ["red gram", "redgram", "tur", "kandi", "కంది"],
    "Chilli": ["chilli", "chili", "mirchi", "mirapa", "మిరప", "మిర్చి"],
    "Turmeric": ["turmeric", "pasupu", "పసుపు"],
    "Soybean": ["soybean", "soya", "సోయా", "సోయాబీన్"],
    "Groundnut": ["groundnut", "peanut", "verusenaga", "వేరుశనగ"],
}

# Every crop a farmer can pick for a land plot: (English, Telugu, icon, group).
# The first 8 are the crops above, which also have prices and advisories.
CROP_CATALOG = [
    ("Paddy", "వరి", "🌾", "Cereals"), ("Cotton", "పత్తి", "☁️", "Commercial"), ("Maize", "మొక్కజొన్న", "🌽", "Cereals"),
    ("Red gram", "కంది", "🫘", "Pulses"), ("Chilli", "మిరప", "🌶️", "Spices"), ("Turmeric", "పసుపు", "🟡", "Spices"),
    ("Soybean", "సోయాబీన్", "🫛", "Oilseeds"), ("Groundnut", "వేరుశనగ", "🥜", "Oilseeds"),
    # Cereals and millets
    ("Jowar (Sorghum)", "జొన్న", "🌾", "Cereals"), ("Bajra (Pearl millet)", "సజ్జ", "🌾", "Cereals"),
    ("Ragi (Finger millet)", "రాగి", "🌾", "Cereals"), ("Wheat", "గోధుమ", "🌾", "Cereals"),
    ("Foxtail millet", "కొర్ర", "🌾", "Cereals"), ("Little millet", "సామ", "🌾", "Cereals"),
    ("Kodo millet", "అరిక", "🌾", "Cereals"),
    # Pulses
    ("Bengal gram (Chickpea)", "శనగ", "🫘", "Pulses"), ("Green gram (Moong)", "పెసర", "🫘", "Pulses"),
    ("Black gram (Urad)", "మినుము", "🫘", "Pulses"), ("Horse gram", "ఉలవ", "🫘", "Pulses"),
    ("Cowpea", "అలసంద", "🫘", "Pulses"), ("Field bean (Lablab)", "చిక్కుడు", "🫛", "Pulses"),
    # Oilseeds
    ("Sunflower", "పొద్దుతిరుగుడు", "🌻", "Oilseeds"), ("Sesame (Gingelly)", "నువ్వులు", "🌱", "Oilseeds"),
    ("Castor", "ఆముదం", "🌱", "Oilseeds"), ("Mustard", "ఆవాలు", "🌼", "Oilseeds"),
    ("Safflower", "కుసుమ", "🌼", "Oilseeds"), ("Oil palm", "ఆయిల్ పామ్", "🌴", "Oilseeds"),
    # Commercial
    ("Sugarcane", "చెరకు", "🎋", "Commercial"), ("Tobacco", "పొగాకు", "🍃", "Commercial"),
    ("Mulberry (Sericulture)", "మల్బరీ", "🌳", "Commercial"),
    # Spices
    ("Coriander", "ధనియాలు", "🌿", "Spices"), ("Ginger", "అల్లం", "🫚", "Spices"), ("Garlic", "వెల్లుల్లి", "🧄", "Spices"),
    ("Fenugreek", "మెంతులు", "🌿", "Spices"),
    # Vegetables
    ("Onion", "ఉల్లి", "🧅", "Vegetables"), ("Tomato", "టమాట", "🍅", "Vegetables"), ("Brinjal", "వంకాయ", "🍆", "Vegetables"),
    ("Okra (Bhendi)", "బెండ", "🥬", "Vegetables"), ("Potato", "బంగాళదుంప", "🥔", "Vegetables"),
    ("Cabbage", "క్యాబేజీ", "🥬", "Vegetables"), ("Cauliflower", "కాలీఫ్లవర్", "🥦", "Vegetables"),
    ("Carrot", "క్యారెట్", "🥕", "Vegetables"), ("Cucumber", "దోసకాయ", "🥒", "Vegetables"),
    ("Bottle gourd", "సొరకాయ", "🥒", "Vegetables"), ("Bitter gourd", "కాకరకాయ", "🥒", "Vegetables"),
    ("Ridge gourd", "బీరకాయ", "🥒", "Vegetables"), ("Drumstick (Moringa)", "మునగ", "🌿", "Vegetables"),
    ("Beans", "బీన్స్", "🫛", "Vegetables"), ("Capsicum", "క్యాప్సికం", "🫑", "Vegetables"),
    ("Leafy vegetables", "ఆకుకూరలు", "🥬", "Vegetables"), ("Sweet potato", "చిలగడదుంప", "🍠", "Vegetables"),
    # Fruits
    ("Mango", "మామిడి", "🥭", "Fruits"), ("Banana", "అరటి", "🍌", "Fruits"), ("Papaya", "బొప్పాయి", "🍈", "Fruits"),
    ("Guava", "జామ", "🍐", "Fruits"), ("Sweet orange (Mosambi)", "బత్తాయి", "🍊", "Fruits"), ("Lemon", "నిమ్మ", "🍋", "Fruits"),
    ("Pomegranate", "దానిమ్మ", "🍎", "Fruits"), ("Grapes", "ద్రాక్ష", "🍇", "Fruits"), ("Watermelon", "పుచ్చకాయ", "🍉", "Fruits"),
    ("Muskmelon", "కర్బూజ", "🍈", "Fruits"), ("Coconut", "కొబ్బరి", "🥥", "Fruits"), ("Sapota", "సపోటా", "🟤", "Fruits"),
    ("Custard apple", "సీతాఫలం", "🍏", "Fruits"), ("Cashew", "జీడిమామిడి", "🌰", "Fruits"),
    # Others
    ("Marigold (Flowers)", "బంతి", "🌼", "Flowers"), ("Rose (Flowers)", "గులాబీ", "🌹", "Flowers"),
    ("Fodder grass", "పశుగ్రాసం", "🌿", "Fodder"),
]
ALL_CROPS = {name: te for name, te, _, _ in CROP_CATALOG}


def crop_te(crop):
    """Telugu name of any crop; a crop typed in by the farmer keeps its own name."""
    return ALL_CROPS.get(crop, crop)


def crop_icon(crop):
    return next((icon for name, _, icon, _ in CROP_CATALOG if name == crop), "🌱")


MARKETS = ["Warangal (Enumamula)", "Nizamabad", "Khammam", "Hyderabad (Bowenpally)", "Karimnagar", "Siddipet"]

# Base modal prices in Rs per quintal (dummy)
BASE_PRICE = {
    "Paddy": 2300, "Cotton": 7200, "Maize": 2150, "Red gram": 7400,
    "Chilli": 14500, "Turmeric": 13200, "Soybean": 4700, "Groundnut": 6300,
}
MSP = {"Paddy": 2369, "Cotton": 7710, "Maize": 2400, "Red gram": 8000, "Soybean": 5328, "Groundnut": 7263}


def _mandi_prices():
    rows = []
    for crop, base in BASE_PRICE.items():
        for market in rng.sample(MARKETS, 3):
            modal = int(base * rng.uniform(0.92, 1.08))
            rows.append({
                "crop": crop, "crop_te": CROPS[crop], "market": market,
                "min": int(modal * 0.93), "max": int(modal * 1.06), "modal": modal,
                "msp": MSP.get(crop), "arrivals_qtl": rng.randint(150, 4200),
                "date": TODAY.isoformat(),
            })
    return rows


MANDI_PRICES = _mandi_prices()

CONDITIONS = [
    ("Sunny", "ఎండ"), ("Partly cloudy", "పాక్షికంగా మేఘావృతం"),
    ("Light rain", "తేలికపాటి వర్షం"), ("Thunderstorm", "ఉరుములతో వర్షం"), ("Cloudy", "మేఘావృతం"),
]


def _weather():
    out = {}
    for d in DISTRICTS:
        days = []
        for i in range(5):
            cond, cond_te = rng.choice(CONDITIONS)
            rain = 0 if cond in ("Sunny", "Partly cloudy") else rng.randint(2, 38)
            days.append({
                "date": (TODAY + timedelta(days=i)).isoformat(),
                "condition": cond, "condition_te": cond_te,
                "max_c": rng.randint(29, 36), "min_c": rng.randint(19, 24),
                "rain_mm": rain, "humidity": rng.randint(55, 90),
            })
        out[d] = days
    return out


WEATHER = _weather()

SCHEMES = [
    {
        "id": "rythu-bharosa", "name": "Rythu Bharosa", "name_te": "రైతు భరోసా", "level": "State",
        "aliases": ["rythu bharosa", "raithu bharosa", "bharosa", "రైతు భరోసా", "భరోసా", "rythu bandhu", "రైతు బంధు"],
        "benefit": "Investment support of Rs 6,000 per acre per season (Rs 12,000 per acre per year) credited to the farmer's bank account.",
        "benefit_te": "ప్రతి సీజన్‌కు ఎకరానికి రూ.6,000 (సంవత్సరానికి ఎకరానికి రూ.12,000) పెట్టుబడి సహాయం నేరుగా రైతు బ్యాంకు ఖాతాలో జమ.",
        "eligibility": "Pattadar farmers with land records in Dharani/Bhu Bharathi portal.",
        "eligibility_te": "భూ భారతి పోర్టల్‌లో భూమి రికార్డులు ఉన్న పట్టాదారు రైతులు.",
        "apply": "Contact your Agriculture Extension Officer (AEO) at the Rythu Vedika with pattadar passbook and Aadhaar.",
        "apply_te": "పట్టాదారు పాస్‌బుక్ మరియు ఆధార్‌తో రైతు వేదికలో మీ వ్యవసాయ విస్తరణ అధికారి (AEO)ని సంప్రదించండి.",
    },
    {
        "id": "rythu-bima", "name": "Rythu Bima", "name_te": "రైతు బీమా", "level": "State",
        "aliases": ["rythu bima", "bima", "life insurance", "రైతు బీమా", "బీమా"],
        "benefit": "Rs 5 lakh group life insurance cover for farmers aged 18-59; premium paid by the State.",
        "benefit_te": "18-59 సంవత్సరాల రైతులకు రూ.5 లక్షల జీవిత బీమా; ప్రీమియం ప్రభుత్వమే చెల్లిస్తుంది.",
        "eligibility": "Pattadar farmers aged 18 to 59 years.",
        "eligibility_te": "18 నుండి 59 సంవత్సరాల వయస్సు గల పట్టాదారు రైతులు.",
        "apply": "Enrol through the AEO; nominee details are mandatory.",
        "apply_te": "AEO ద్వారా నమోదు చేసుకోండి; నామినీ వివరాలు తప్పనిసరి.",
    },
    {
        "id": "pm-kisan", "name": "PM-KISAN", "name_te": "పీఎం-కిసాన్", "level": "Central",
        "aliases": ["pm kisan", "pm-kisan", "pmkisan", "kisan samman", "పీఎం కిసాన్", "కిసాన్"],
        "benefit": "Rs 6,000 per year in three instalments of Rs 2,000 via Direct Benefit Transfer.",
        "benefit_te": "సంవత్సరానికి రూ.6,000 — మూడు విడతల్లో రూ.2,000 చొప్పున నేరుగా బ్యాంకు ఖాతాలో.",
        "eligibility": "Landholding farmer families (exclusions apply for income-tax payers, pensioners above limit, etc.).",
        "eligibility_te": "భూమి కలిగిన రైతు కుటుంబాలు (ఆదాయపు పన్ను చెల్లించేవారు మొదలైనవారికి మినహాయింపు).",
        "apply": "Register on pmkisan.gov.in or at a Common Service Centre; e-KYC is mandatory.",
        "apply_te": "pmkisan.gov.in లో లేదా మీసేవ / CSC కేంద్రంలో నమోదు చేయండి; e-KYC తప్పనిసరి.",
    },
    {
        "id": "pmfby", "name": "PM Fasal Bima Yojana", "name_te": "ప్రధాన మంత్రి ఫసల్ బీమా యోజన", "level": "Central",
        "aliases": ["fasal bima", "pmfby", "crop insurance", "పంట బీమా", "ఫసల్ బీమా"],
        "benefit": "Crop insurance against natural calamities, pests and diseases. Farmer premium: 2% Kharif, 1.5% Rabi, 5% commercial crops.",
        "benefit_te": "ప్రకృతి వైపరీత్యాలు, తెగుళ్ల వల్ల పంట నష్టానికి బీమా. ప్రీమియం: ఖరీఫ్ 2%, రబీ 1.5%, వాణిజ్య పంటలు 5%.",
        "eligibility": "All farmers growing notified crops in notified areas, including tenant farmers.",
        "eligibility_te": "నోటిఫై చేసిన ప్రాంతాల్లో నోటిఫై చేసిన పంటలు పండించే రైతులందరూ (కౌలు రైతులతో సహా).",
        "apply": "Through your bank, CSC or pmfby.gov.in before the season cut-off date.",
        "apply_te": "సీజన్ గడువు తేదీకి ముందు బ్యాంకు, CSC లేదా pmfby.gov.in ద్వారా.",
    },
    {
        "id": "soil-health", "name": "Soil Health Card", "name_te": "సాయిల్ హెల్త్ కార్డు", "level": "Central",
        "aliases": ["soil health", "soil test", "soil card", "నేల పరీక్ష", "భూసార"],
        "benefit": "Free soil testing with crop-wise fertilizer recommendations every 2 years.",
        "benefit_te": "ప్రతి 2 సంవత్సరాలకు ఉచిత భూసార పరీక్ష మరియు పంటల వారీగా ఎరువుల సిఫార్సులు.",
        "eligibility": "All farmers.", "eligibility_te": "రైతులందరూ.",
        "apply": "Give a soil sample to the AEO at your Rythu Vedika.",
        "apply_te": "మీ రైతు వేదికలో AEO కి మట్టి నమూనా ఇవ్వండి.",
    },
    {
        "id": "farm-mech", "name": "Farm Mechanisation Subsidy", "name_te": "వ్యవసాయ యాంత్రీకరణ సబ్సిడీ", "level": "State",
        "aliases": ["mechanisation", "mechanization", "tractor", "subsidy", "యంత్ర", "సబ్సిడీ", "ట్రాక్టర్"],
        "benefit": "40-50% subsidy on sprayers, rotavators, drones and other farm equipment (higher for SC/ST and women farmers).",
        "benefit_te": "స్ప్రేయర్లు, రోటావేటర్లు, డ్రోన్లు మొదలైన పరికరాలపై 40-50% సబ్సిడీ (SC/ST, మహిళా రైతులకు ఎక్కువ).",
        "eligibility": "Farmers with land records; one benefit per item per 5 years.",
        "eligibility_te": "భూమి రికార్డులు ఉన్న రైతులు; 5 సంవత్సరాలకు ఒక్కో పరికరానికి ఒకసారి.",
        "apply": "Apply through the Mandal Agriculture Officer.",
        "apply_te": "మండల వ్యవసాయ అధికారి ద్వారా దరఖాస్తు చేయండి.",
    },
]

# ICAR-style crop advisories (dummy, simplified)
ADVISORIES = {
    "Paddy": {
        "en": ["Maintain 2-5 cm standing water during tillering.",
               "Apply nitrogen in 3 splits: basal, tillering and panicle initiation.",
               "Watch for brown planthopper at the base of the plant; avoid excess urea.",
               "For leaf blast, spray Tricyclazole 75 WP @ 0.6 g per litre."],
        "te": ["పిలకల దశలో 2-5 సెం.మీ. నీరు నిలువ ఉంచండి.",
               "నత్రజనిని 3 విడతల్లో వేయండి: దుక్కిలో, పిలకల దశలో, అంకురం దశలో.",
               "మొక్క అడుగున సుడిదోమ కోసం గమనించండి; యూరియా ఎక్కువగా వాడవద్దు.",
               "అగ్గి తెగులుకు ట్రైసైక్లాజోల్ 75 WP లీటరుకు 0.6 గ్రా. పిచికారీ చేయండి."],
    },
    "Cotton": {
        "en": ["Install pheromone traps (5 per acre) to monitor pink bollworm.",
               "Remove and destroy rosette flowers.",
               "Apply potash at square formation to improve boll weight.",
               "Avoid synthetic pyrethroids before 90 days to prevent whitefly outbreak."],
        "te": ["గులాబీ రంగు పురుగు గమనించడానికి ఎకరానికి 5 లింగాకర్షక బుట్టలు పెట్టండి.",
               "గుడ్డి పూలను తీసి నాశనం చేయండి.",
               "కాయ బరువు పెరగడానికి మొగ్గ దశలో పొటాష్ వేయండి.",
               "తెల్లదోమ రాకుండా 90 రోజుల ముందు సింథటిక్ పైరిథ్రాయిడ్లు వాడవద్దు."],
    },
    "Maize": {
        "en": ["Scout for fall armyworm in the whorl every week.",
               "Spray Emamectin benzoate 5 SG @ 0.4 g per litre if damage exceeds 10%.",
               "Apply sand + lime (9:1) into the whorl as a low-cost control.",
               "Ensure irrigation at tasselling and silking stages."],
        "te": ["ప్రతి వారం సుడిలో కత్తెర పురుగు కోసం పరిశీలించండి.",
               "నష్టం 10% మించితే ఎమామెక్టిన్ బెంజోయేట్ 5 SG లీటరుకు 0.4 గ్రా. పిచికారీ చేయండి.",
               "తక్కువ ఖర్చు నివారణకు ఇసుక + సున్నం (9:1) సుడిలో వేయండి.",
               "పూత, పీచు దశల్లో తప్పనిసరిగా నీరు పెట్టండి."],
    },
    "Red gram": {
        "en": ["Nip the terminal bud at 45-50 days to increase branching.",
               "Monitor for pod borer at flowering; use bird perches (20 per acre).",
               "Spray NSKE 5% at flower initiation."],
        "te": ["కొమ్మలు ఎక్కువగా రావడానికి 45-50 రోజుల్లో తలలు తుంచండి.",
               "పూత దశలో కాయతొలుచు పురుగు గమనించండి; ఎకరానికి 20 పక్షి స్థావరాలు పెట్టండి.",
               "పూత మొదలయ్యే సమయంలో వేప గింజల కషాయం 5% పిచికారీ చేయండి."],
    },
    "Chilli": {
        "en": ["Control thrips and mites early to prevent leaf curl.",
               "Use yellow and blue sticky traps (10 per acre).",
               "Spray Fipronil 5 SC @ 2 ml per litre for thrips.",
               "Avoid water stagnation to prevent fruit rot."],
        "te": ["ఆకుముడత రాకుండా తామర పురుగులు, నల్లిని ముందుగానే నియంత్రించండి.",
               "ఎకరానికి 10 పసుపు, నీలం జిగురు అట్టలు పెట్టండి.",
               "తామర పురుగులకు ఫిప్రోనిల్ 5 SC లీటరుకు 2 మి.లీ. పిచికారీ చేయండి.",
               "కాయ కుళ్లు రాకుండా నీరు నిలవకుండా చూడండి."],
    },
    "Turmeric": {
        "en": ["Mulch with green leaves after planting to conserve moisture.",
               "Earth up at 60 and 90 days.",
               "Drench Copper oxychloride 3 g per litre for rhizome rot."],
        "te": ["నాటిన తర్వాత తేమ నిలవడానికి పచ్చి ఆకులతో మల్చింగ్ చేయండి.",
               "60 మరియు 90 రోజుల్లో మట్టిని ఎగదోయండి.",
               "దుంప కుళ్లుకు కాపర్ ఆక్సీక్లోరైడ్ లీటరుకు 3 గ్రా. మొదళ్లలో పోయండి."],
    },
    "Soybean": {
        "en": ["Treat seed with Rhizobium culture before sowing.",
               "Keep the field weed-free for the first 45 days.",
               "Watch for girdle beetle and tobacco caterpillar."],
        "te": ["విత్తే ముందు రైజోబియం కల్చర్‌తో విత్తన శుద్ధి చేయండి.",
               "మొదటి 45 రోజులు కలుపు లేకుండా చూడండి.",
               "కాండం తొలుచు పురుగు, పొగాకు లద్దె పురుగు కోసం గమనించండి."],
    },
    "Groundnut": {
        "en": ["Apply gypsum @ 200 kg per acre at pegging.",
               "Monitor for leaf miner and tikka leaf spot.",
               "Avoid moisture stress at pod development."],
        "te": ["ఊడల దశలో ఎకరానికి 200 కిలోల జిప్సం వేయండి.",
               "ఆకు తొలుచు పురుగు, టిక్కా ఆకుమచ్చ తెగులు కోసం గమనించండి.",
               "కాయ ఏర్పడే దశలో నీటి ఎద్దడి లేకుండా చూడండి."],
    },
}

# Pest / disease library used by the image diagnosis feature
PESTS = [
    {"name": "Fall Armyworm", "name_te": "కత్తెర పురుగు", "crop": "Maize",
     "symptoms": "Ragged holes in leaves and sawdust-like frass in the whorl.",
     "symptoms_te": "ఆకులపై చిరిగిన రంధ్రాలు, సుడిలో రంపపు పొట్టు లాంటి విసర్జన.",
     "remedy": "Spray Emamectin benzoate 5 SG @ 0.4 g/L into the whorl; apply sand + lime.",
     "remedy_te": "సుడిలో ఎమామెక్టిన్ బెంజోయేట్ 5 SG లీటరుకు 0.4 గ్రా. పిచికారీ చేయండి; ఇసుక + సున్నం వేయండి."},
    {"name": "Pink Bollworm", "name_te": "గులాబీ రంగు పురుగు", "crop": "Cotton",
     "symptoms": "Rosette flowers, bored bolls and stained lint.",
     "symptoms_te": "గుడ్డి పూలు, రంధ్రాలు పడిన కాయలు, రంగు మారిన దూది.",
     "remedy": "Pheromone traps, destroy rosette flowers; spray Profenophos 50 EC @ 2 ml/L if above ETL.",
     "remedy_te": "లింగాకర్షక బుట్టలు పెట్టండి, గుడ్డి పూలు తీసివేయండి; ఆర్థిక నష్ట పరిమితి దాటితే ప్రొఫెనోఫాస్ 50 EC లీటరుకు 2 మి.లీ."},
    {"name": "Rice Blast", "name_te": "వరి అగ్గి తెగులు", "crop": "Paddy",
     "symptoms": "Spindle-shaped grey lesions with brown margins on leaves.",
     "symptoms_te": "ఆకులపై గోధుమ అంచులతో కదురు ఆకారపు బూడిద రంగు మచ్చలు.",
     "remedy": "Spray Tricyclazole 75 WP @ 0.6 g/L; avoid excess nitrogen.",
     "remedy_te": "ట్రైసైక్లాజోల్ 75 WP లీటరుకు 0.6 గ్రా. పిచికారీ చేయండి; నత్రజని ఎక్కువగా వేయవద్దు."},
    {"name": "Brown Planthopper", "name_te": "సుడిదోమ", "crop": "Paddy",
     "symptoms": "Circular patches of dried plants ('hopper burn'); insects at plant base.",
     "symptoms_te": "గుండ్రని మచ్చల్లో మొక్కలు ఎండిపోవడం; మొక్క అడుగున పురుగులు.",
     "remedy": "Drain water, make 20 cm alleys; spray Pymetrozine 50 WG @ 0.6 g/L at the base.",
     "remedy_te": "నీరు తీసివేసి, 20 సెం.మీ. కాలిబాటలు చేయండి; మొక్క అడుగున పైమెట్రోజిన్ 50 WG లీటరుకు 0.6 గ్రా."},
    {"name": "Chilli Leaf Curl (Thrips)", "name_te": "మిరప ఆకుముడత (తామర పురుగు)", "crop": "Chilli",
     "symptoms": "Upward curling of leaves, stunted plants, silvery streaks.",
     "symptoms_te": "ఆకులు పైకి ముడుచుకోవడం, మొక్క ఎదుగుదల తగ్గడం, వెండి రంగు చారలు.",
     "remedy": "Blue sticky traps; spray Fipronil 5 SC @ 2 ml/L; remove infected plants.",
     "remedy_te": "నీలం జిగురు అట్టలు; ఫిప్రోనిల్ 5 SC లీటరుకు 2 మి.లీ. పిచికారీ; సోకిన మొక్కలు తీసివేయండి."},
]

FIRST = ["Ramesh", "Lakshmi", "Srinivas", "Padma", "Venkatesh", "Saritha", "Raju", "Anitha", "Mallesh",
         "Swapna", "Narsimha", "Kavitha", "Yadagiri", "Sujatha", "Krishna", "Manjula", "Bhaskar", "Renuka",
         "Anjaiah", "Shobha", "Ravinder", "Jyothi", "Sathaiah", "Vani", "Komuraiah"]
LAST = ["Reddy", "Goud", "Rao", "Naik", "Yadav", "Chary", "Mudiraj", "Patel", "Varma", "Kumar"]
VILLAGES = ["Peddapalli", "Jangaon", "Bhongir", "Huzurabad", "Kamareddy", "Narsampet", "Madhira",
            "Gajwel", "Zaheerabad", "Armoor", "Mulugu", "Kodad", "Wanaparthy", "Utnoor", "Sircilla"]

STATUSES = ["Approved", "Credited", "Pending verification", "Rejected - land record mismatch", "Under review"]


def _farmers():
    farmers = []
    for i in range(50):
        fid = f"TS{1001 + i}"
        district = rng.choice(list(DISTRICTS))
        crops = rng.sample(list(CROPS), rng.randint(1, 2))
        acres = round(rng.uniform(0.8, 9.5), 1)
        plots = []
        remaining = acres
        for p in range(rng.randint(1, 2)):
            area = remaining if p else round(remaining * rng.uniform(0.4, 1.0), 1)
            remaining = round(remaining - area, 1)
            plots.append({
                "survey_no": f"{rng.randint(10, 480)}/{rng.choice('ABCD')}",
                "area_acres": area, "soil": rng.choice(["Black cotton", "Red sandy loam", "Alluvial", "Red loam"]),
                "irrigation": rng.choice(["Borewell", "Canal", "Tank", "Rainfed"]),
                "crop": crops[p % len(crops)],
            })
            if remaining <= 0:
                break
        applications = []
        for scheme in rng.sample(["rythu-bharosa", "pm-kisan", "pmfby", "farm-mech", "rythu-bima"], 3):
            status = rng.choice(STATUSES)
            amount = {"rythu-bharosa": int(acres * 6000), "pm-kisan": 2000, "pmfby": rng.randint(4, 18) * 1000,
                      "farm-mech": rng.randint(8, 60) * 1000, "rythu-bima": 0}[scheme]
            applications.append({
                "app_id": f"APP-{rng.randint(100000, 999999)}", "scheme_id": scheme,
                "applied_on": (TODAY - timedelta(days=rng.randint(10, 160))).isoformat(),
                "status": status, "amount": amount,
                "credited_on": (TODAY - timedelta(days=rng.randint(1, 9))).isoformat() if status == "Credited" else None,
            })
        name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
        farmers.append({
            "farmer_id": fid, "name": name, "mobile": f"9{rng.randint(100000000, 999999999)}",
            "district": district, "district_te": DISTRICTS[district], "village": rng.choice(VILLAGES),
            "age": rng.randint(24, 66), "gender": rng.choice(["Male", "Female"]),
            "total_acres": acres, "plots": plots, "crops": crops,
            "bank": f"{rng.choice(['SBI', 'APGVB', 'Union Bank', 'Canara Bank'])} xxxx{rng.randint(1000, 9999)}",
            "applications": applications,
        })
    return farmers


FARMERS = _farmers()
FARMER_INDEX = {f["farmer_id"]: f for f in FARMERS}

GRIEVANCE_CATEGORIES = ["Payment not received", "Land record correction", "Seed quality", "Fertilizer shortage",
                        "Crop insurance claim", "Name mismatch in Aadhaar"]


def _grievances():
    rows = []
    for i in range(18):
        f = rng.choice(FARMERS)
        status = rng.choice(["Open", "In progress", "Resolved", "Resolved", "Escalated"])
        rows.append({
            "grievance_id": f"GRV-{2401 + i}", "farmer_id": f["farmer_id"], "farmer_name": f["name"],
            "district": f["district"], "category": rng.choice(GRIEVANCE_CATEGORIES),
            "description": "Filed via Rythu Vedika (dummy record).", "status": status,
            "created_on": (TODAY - timedelta(days=rng.randint(1, 45))).isoformat(),
            "channel": rng.choice(["Web chatbot", "WhatsApp", "Voice bot", "Rythu Vedika"]),
        })
    return rows


GRIEVANCES = _grievances()

# Integration tracker (governance view from section 2.9 of the proposal)
TRACKER = [
    {"id": "T1", "stage": "Stage 1", "item": "Onboard core chatbot (Telugu)", "owner": "NISG / BV IT Team", "status": "Done", "due": "2026-08-15"},
    {"id": "T2", "stage": "Stage 1", "item": "Voice bot Telugu testing - 120 scenarios", "owner": "NISG", "status": "In progress", "due": "2026-10-30"},
    {"id": "T3", "stage": "Stage 1", "item": "Regional agriculture glossary (2,400 terms)", "owner": "Agri Dept", "status": "Done", "due": "2026-09-01"},
    {"id": "T4", "stage": "Stage 2", "item": "Publish Rythu Bharosa guidelines", "owner": "NISG (Contributor)", "status": "Done", "due": "2026-09-20"},
    {"id": "T5", "stage": "Stage 2", "item": "Publish Rabi 2026 seasonal advisory", "owner": "NISG (Contributor)", "status": "In progress", "due": "2026-11-05"},
    {"id": "T6", "stage": "Stage 3", "item": "Application status API (Rythu Bharosa)", "owner": "Scheme IT team", "status": "In progress", "due": "2026-11-20"},
    {"id": "T7", "stage": "Stage 3", "item": "Grievance redressal API", "owner": "Agri Dept IT", "status": "Blocked", "due": "2026-11-30"},
    {"id": "T8", "stage": "Stage 4", "item": "Land records integration (Bhu Bharathi)", "owner": "CCLA / NISG", "status": "Not started", "due": "2027-02-15"},
    {"id": "T9", "stage": "Stage 4", "item": "Crop booking data integration", "owner": "Agri Dept IT", "status": "Not started", "due": "2027-03-01"},
    {"id": "T10", "stage": "Channels", "item": "Embed chatbot on agri.telangana.gov.in", "owner": "Website team", "status": "In progress", "due": "2026-11-10"},
    {"id": "T11", "stage": "Channels", "item": "WhatsApp Business account verification (Meta)", "owner": "Agri Dept / Meta", "status": "Blocked", "due": "2026-11-25"},
    {"id": "T12", "stage": "Channels", "item": "Crop/pest image diagnosis enablement", "owner": "BV IT Team", "status": "Not started", "due": "2027-01-10"},
]

ISSUES = [
    {"id": "R1", "type": "Risk", "title": "Meta business verification may delay WhatsApp go-live", "severity": "High", "owner": "Agri Dept", "status": "Open"},
    {"id": "R2", "type": "Issue", "title": "Grievance API lacks OAuth - fails BV security review", "severity": "High", "owner": "Agri Dept IT", "status": "Open"},
    {"id": "R3", "type": "Issue", "title": "Voice bot mispronounces 'Rythu Bharosa'", "severity": "Medium", "owner": "BV IT Team", "status": "In progress"},
    {"id": "R4", "type": "Risk", "title": "Consent framework for land data not yet approved", "severity": "High", "owner": "Agri Dept", "status": "Open"},
    {"id": "R5", "type": "Action", "title": "Nominate Reviewer officer with .gov.in email", "severity": "Medium", "owner": "Agri Dept", "status": "Closed"},
    {"id": "R6", "type": "Issue", "title": "OCR misreads Telugu numerals in scanned circulars", "severity": "Low", "owner": "NISG", "status": "In progress"},
]

# Agreed test scenarios used for Claude vs GPT evaluation (section 2.9)
TEST_SCENARIOS = [
    {"id": "Q1", "lang": "en", "question": "What is the price of cotton today?", "expect": ["cotton", "quintal"]},
    {"id": "Q2", "lang": "te", "question": "వరంగల్ లో వాతావరణం ఎలా ఉంది?", "expect": ["వరంగల్"]},
    {"id": "Q3", "lang": "en", "question": "How do I apply for PM-KISAN?", "expect": ["pmkisan", "e-kyc"]},
    {"id": "Q4", "lang": "te", "question": "రైతు భరోసా పథకం గురించి చెప్పండి", "expect": ["6,000"]},
    {"id": "Q5", "lang": "en", "question": "My maize has holes in the leaves, what should I spray?", "expect": ["emamectin"]},
    {"id": "Q6", "lang": "en", "question": "Will it rain in Khammam this week?", "expect": ["khammam", "rain"]},
    {"id": "Q7", "lang": "te", "question": "మిరప ధర ఎంత?", "expect": ["మిరప"]},
    {"id": "Q8", "lang": "en", "question": "What is crop insurance premium for Kharif?", "expect": ["2%"]},
]


def _query_history():
    """30 days of fake usage logs for the PMU dashboard."""
    intents = ["mandi_price", "weather", "scheme_info", "crop_advisory", "application_status",
               "benefit_status", "grievance", "pest_diagnosis", "land_records"]
    weights = [24, 18, 20, 16, 8, 6, 4, 3, 1]
    rows = []
    for d in range(30, 0, -1):
        day = TODAY - timedelta(days=d)
        for _ in range(rng.randint(140, 320)):
            rows.append({
                "date": day.isoformat(), "intent": rng.choices(intents, weights)[0],
                "lang": rng.choices(["te", "en"], [72, 28])[0],
                "channel": rng.choices(["Web chatbot", "Voice bot", "WhatsApp", "BV App"], [40, 25, 15, 20])[0],
                "model": rng.choice(["claude", "gpt"]),
                "district": rng.choice(list(DISTRICTS)),
                "helpful": rng.random() < 0.86,
            })
    return rows


QUERY_HISTORY = _query_history()


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


def write_json(path, obj):
    """Save to a temporary file first, then swap it in, so a crash or a second
    process can never leave a half-written (empty) save file behind."""
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(obj, indent=1, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


def read_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return default


# Apply farmers' saved edits on top of the demo data whenever this module is used
from . import profiles  # noqa: E402,F401
