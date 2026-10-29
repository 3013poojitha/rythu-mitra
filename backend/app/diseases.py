"""Crop disease & pest library with spray recommendations (Crop Doctor).

Doses follow commonly published university/ICAR-style recommendations but this
is DEMO data: a real deployment must use the State's approved package of
practices and the product label. The AI model only *identifies* the problem;
doses always come from this table, so the model can never invent a dose.

Dose units:
  per="litre" -> amount of product per litre of water (sprayed or drenched)
  per="acre"  -> amount applied directly per acre (granules, traps, bio-agents)
"""
from .terms import medicine


SPRAYER_TANK_L = 16  # standard knapsack sprayer

SAFETY = {
    "en": [
        "Wear gloves, a mask, full-sleeve clothes and shoes while mixing and spraying.",
        "Spray in the early morning or evening. Do not spray in strong wind, rain or midday heat.",
        "Use only one product per spray unless a tank-mix is recommended. Never mix unknown chemicals.",
        "Measure doses with a measuring cup. Do not increase the dose - it harms crops and soil.",
        "Do not eat, drink or smoke while spraying. Wash hands and face with soap afterwards.",
        "Keep chemicals locked away from children and animals. Do not reuse empty containers; puncture and bury them.",
        "Respect the waiting period before harvest shown for each product.",
        "Confirm the diagnosis with your Agriculture Extension Officer (AEO) before buying chemicals.",
    ],
    "te": [
        "మందు కలిపేటప్పుడు, పిచికారీ చేసేటప్పుడు చేతి తొడుగులు, మాస్క్, పొడవు చేతుల బట్టలు, చెప్పులు ధరించండి.",
        "ఉదయం లేదా సాయంత్రం పిచికారీ చేయండి. గాలి, వర్షం, మధ్యాహ్నం ఎండలో చేయవద్దు.",
        "సిఫార్సు లేకుండా రెండు మందులు కలపవద్దు. తెలియని మందులు ఎప్పుడూ కలపవద్దు.",
        "కొలత కప్పుతో మోతాదు కొలవండి. మోతాదు పెంచవద్దు - పంటకు, నేలకు హాని.",
        "పిచికారీ సమయంలో తినడం, తాగడం, పొగ తాగడం చేయవద్దు. తర్వాత సబ్బుతో కడుక్కోండి.",
        "మందులను పిల్లలు, పశువులకు దూరంగా ఉంచండి. ఖాళీ డబ్బాలను మళ్లీ వాడవద్దు.",
        "ప్రతి మందుకు చూపిన పంట కోత ముందు నిరీక్షణ కాలాన్ని పాటించండి.",
        "మందులు కొనే ముందు మీ వ్యవసాయ విస్తరణ అధికారి (AEO) తో నిర్ధారించుకోండి.",
    ],
}


def T(kind, product, dose, unit, reason, when, repeat, phi=None, per="litre", water=200, method="Foliar spray"):
    return {"kind": kind, "product": product, "dose": dose, "unit": unit, "per": per,
            "water_l_per_acre": water if per == "litre" else None, "method": method,
            "reason": reason, "when": when, "repeat": repeat, "phi_days": phi}


DISEASES = [
    {
        "id": "paddy-blast", "crop": "Paddy", "name": "Rice Blast", "name_te": "వరి అగ్గి తెగులు", "type": "Fungal disease",
        "cause": "Fungus Magnaporthe oryzae. Spreads in cool nights, high humidity, dew, and when too much nitrogen (urea) is applied.",
        "cause_te": "శిలీంధ్రం వల్ల వస్తుంది. చల్లని రాత్రులు, ఎక్కువ తేమ, మంచు, యూరియా ఎక్కువగా వేసినప్పుడు వ్యాపిస్తుంది.",
        "symptoms": "Spindle / eye-shaped spots with grey centres and brown edges on leaves; neck turns black and panicles break (neck blast).",
        "symptoms_te": "ఆకులపై బూడిద మధ్యభాగం, గోధుమ అంచులతో కన్ను ఆకారపు మచ్చలు; వెన్ను మెడ నల్లబడి విరుగుతుంది.",
        "treatments": [
            T("Chemical", "Tricyclazole 75 WP", 0.6, "g", "Systemic fungicide that stops the blast fungus from entering leaves.", "At first spots on leaves, and again at panicle emergence to protect the neck.", "Repeat after 10-15 days if spots continue", 30),
            T("Chemical", "Isoprothiolane 40 EC", 1.5, "ml", "Alternative fungicide - use if Tricyclazole was already sprayed twice.", "When leaf spots are spreading quickly.", "Once more after 12-15 days if needed", 30),
            T("Organic", "Pseudomonas fluorescens 1.5% WP", 5, "g", "Beneficial bacteria that suppress the fungus; safe for the environment.", "As prevention from tillering stage, or at very first spots.", "Every 10 days, 2-3 times"),
        ],
        "prevention": ["Use resistant varieties.", "Split urea into 3 doses; avoid excess nitrogen.", "Remove grassy weeds on bunds that host the fungus."],
        "prevention_te": ["నిరోధక రకాలు వాడండి.", "యూరియాను 3 విడతలుగా వేయండి; ఎక్కువ వేయవద్దు.", "గట్లపై గడ్డి కలుపు తీసివేయండి."],
    },
    {
        "id": "paddy-bph", "crop": "Paddy", "name": "Brown Planthopper", "name_te": "సుడిదోమ", "type": "Insect pest",
        "cause": "Small brown insects that suck sap at the base of the plant. Increase with dense planting, standing water and excess urea.",
        "cause_te": "మొక్క అడుగున రసం పీల్చే చిన్న గోధుమ పురుగులు. దగ్గరగా నాటడం, నిలువ నీరు, ఎక్కువ యూరియాతో పెరుగుతాయి.",
        "symptoms": "Round patches of yellow then dried plants ('hopper burn'); many insects at the base of stems when you part the plants.",
        "symptoms_te": "గుండ్రని మడుల్లో మొక్కలు పసుపు రంగుకు మారి ఎండిపోవడం; మొక్క అడుగున ఎక్కువ పురుగులు.",
        "treatments": [
            T("Chemical", "Pymetrozine 50 WG", 0.6, "g", "Stops the insects from feeding; gentle on natural enemies like spiders.", "When 10 or more hoppers are seen per hill. Drain water first.", "Once more after 15 days if hoppers return", 14, method="Spray directed at the base of plants"),
            T("Chemical", "Dinotefuran 20 SG", 0.4, "g", "Fast-acting alternative for heavy attack.", "Heavy infestation or hopper burn patches appearing.", "Do not repeat the same product - rotate", 21, method="Spray directed at the base of plants"),
            T("Organic", "Neem oil 1500 ppm", 5, "ml", "Repels and reduces egg laying; best in early stage.", "At the first sighting of hoppers.", "Every 7-10 days"),
        ],
        "prevention": ["Leave a 20 cm walking alley every 2 m for air and light.", "Alternate wetting and drying instead of continuous standing water.", "Avoid synthetic pyrethroids - they cause BPH resurgence."],
        "prevention_te": ["ప్రతి 2 మీటర్లకు 20 సెం.మీ. కాలిబాట వదలండి.", "నిరంతరం నీరు నిలువ ఉంచకుండా ఆరబెట్టి తడి పెట్టండి.", "సింథటిక్ పైరిథ్రాయిడ్లు వాడవద్దు."],
    },
    {
        "id": "paddy-stemborer", "crop": "Paddy", "name": "Yellow Stem Borer", "name_te": "కాండం తొలుచు పురుగు", "type": "Insect pest",
        "cause": "Caterpillars bore into the stem and eat the inside. Moths lay eggs on leaf tips.",
        "cause_te": "పురుగు కాండంలోకి తొలుచుకుని లోపలి భాగం తింటుంది. రెక్కల పురుగు ఆకు చివర్లలో గుడ్లు పెడుతుంది.",
        "symptoms": "Central shoot dries ('dead heart') in young crop; white empty panicles ('white ear') at flowering.",
        "symptoms_te": "పిలక దశలో మధ్య ఆకు ఎండిపోవడం (డెడ్ హార్ట్); వెన్ను దశలో తెల్ల కంకులు.",
        "treatments": [
            T("Chemical", "Chlorantraniliprole 18.5 SC", 0.3, "ml", "Kills caterpillars inside the stem; long protection.", "When 5% dead hearts or egg masses are seen.", "Once more after 20 days if needed", 40),
            T("Chemical", "Cartap hydrochloride 4G (granules)", 8, "kg", "Granules release slowly into water and reach the borer inside the stem.", "At 30-35 days after transplanting with 2-3 cm water in the field.", "Single application", 30, per="acre", method="Broadcast granules in standing water"),
            T("Organic", "Pheromone traps (Scirpophaga lure)", 8, "traps", "Catch male moths and reduce mating; also shows when to act.", "From 15 days after transplanting.", "Change lure every 25-30 days", per="acre", method="Install traps above crop height"),
        ],
        "prevention": ["Clip leaf tips with egg masses before transplanting.", "Plough stubbles after harvest.", "Use pheromone traps for monitoring."],
        "prevention_te": ["నాటే ముందు గుడ్లు ఉన్న ఆకు చివర్లు కత్తిరించండి.", "కోత తర్వాత మొదళ్లను దున్నేయండి.", "లింగాకర్షక బుట్టలతో పర్యవేక్షించండి."],
    },
    {
        "id": "cotton-pbw", "crop": "Cotton", "name": "Pink Bollworm", "name_te": "గులాబీ రంగు పురుగు", "type": "Insect pest",
        "cause": "Pink caterpillars that live inside flowers and bolls. Survive in stored seed cotton and late-season crop.",
        "cause_te": "పూలు, కాయల లోపల ఉండే గులాబీ రంగు పురుగులు. నిల్వ పత్తి, ఆలస్య పంటలో బతుకుతాయి.",
        "symptoms": "Flowers stay closed like a rosette; small holes on bolls; stained, poor-quality lint and damaged seeds.",
        "symptoms_te": "పూలు గులాబీ పువ్వులా ముడుచుకుని ఉంటాయి (గుడ్డి పూలు); కాయలపై చిన్న రంధ్రాలు; దూది రంగు మారడం.",
        "treatments": [
            T("Chemical", "Profenofos 50 EC", 2, "ml", "Contact and stomach poison for young larvae before they enter bolls.", "When 8 moths/trap/night for 3 nights or 10% damaged flowers/bolls.", "Rotate with another product after 10-15 days", 20),
            T("Chemical", "Emamectin benzoate 5 SG", 0.4, "g", "Strong larvicide; use as rotation partner.", "At second spray if attack continues.", "Do not use more than twice a season", 10),
            T("Organic", "Neem oil 1500 ppm", 5, "ml", "Reduces egg laying from early flowering.", "From 45-50 days after sowing.", "Every 10 days"),
            T("Organic", "Pheromone traps (Gossyplure)", 8, "traps", "Trap male moths and tell you when numbers cross the danger level.", "From 40 days after sowing.", "Change lure every 3 weeks", per="acre", method="Install traps at crop height"),
        ],
        "prevention": ["Pick and destroy rosette flowers.", "Terminate the crop by December; do not keep ratoon cotton.", "Do not store seed cotton in the house."],
        "prevention_te": ["గుడ్డి పూలను తీసి నాశనం చేయండి.", "డిసెంబర్ నాటికి పంట ముగించండి; కార్శి పత్తి ఉంచవద్దు.", "పత్తిని ఇంట్లో నిల్వ చేయవద్దు."],
    },
    {
        "id": "cotton-whitefly", "crop": "Cotton", "name": "Whitefly", "name_te": "తెల్లదోమ", "type": "Insect pest",
        "cause": "Tiny white flies that suck sap from the underside of leaves and spread leaf-curl virus. Increase in hot, dry weather and after pyrethroid sprays.",
        "cause_te": "ఆకుల అడుగున రసం పీల్చే చిన్న తెల్ల దోమలు; ఆకుముడత వైరస్ వ్యాపింపజేస్తాయి. వేడి, పొడి వాతావరణంలో పెరుగుతాయి.",
        "symptoms": "Many white flies fly up when plants are shaken; sticky leaves with black sooty mould; leaves curl and yellow.",
        "symptoms_te": "మొక్క కదిలిస్తే తెల్ల దోమలు ఎగురుతాయి; ఆకులు జిగటగా, నల్లని బూజు; ఆకులు ముడుచుకుని పసుపు రంగు.",
        "treatments": [
            T("Chemical", "Diafenthiuron 50 WP", 1.25, "g", "Kills adults and nymphs on leaf undersides.", "When 6-8 adults per leaf on top leaves.", "Rotate after 10-12 days", 21, method="Spray covering the underside of leaves"),
            T("Chemical", "Flonicamid 50 WG", 0.3, "g", "Stops feeding quickly; safe for bees when used correctly.", "If whitefly continues after first spray.", "Once more after 15 days if needed", 30, method="Spray covering the underside of leaves"),
            T("Organic", "Neem oil 1500 ppm", 5, "ml", "Reduces egg laying and repels adults.", "Early stage, low numbers.", "Every 7 days"),
            T("Organic", "Yellow sticky traps", 10, "traps", "Attract and trap adult whiteflies.", "From early crop stage.", "Replace when full", per="acre", method="Hang just above crop canopy"),
        ],
        "prevention": ["Avoid synthetic pyrethroids before 90 days.", "Remove weed hosts like Abutilon and Parthenium.", "Do not grow okra or brinjal next to cotton."],
        "prevention_te": ["90 రోజుల ముందు పైరిథ్రాయిడ్లు వాడవద్దు.", "కలుపు మొక్కలను తీసివేయండి.", "పత్తి పక్కన బెండ, వంకాయ వేయవద్దు."],
    },
    {
        "id": "maize-faw", "crop": "Maize", "name": "Fall Armyworm", "name_te": "కత్తెర పురుగు", "type": "Insect pest",
        "cause": "Caterpillars (with an inverted 'Y' on the head) that feed inside the whorl. Moths fly long distances.",
        "cause_te": "తలపై తిరగబడిన 'Y' గుర్తు ఉన్న లద్దె పురుగులు సుడిలో తింటాయి. రెక్కల పురుగులు దూరం ఎగురుతాయి.",
        "symptoms": "Ragged holes and 'window panes' on leaves; wet sawdust-like droppings in the whorl; cobs bored at later stage.",
        "symptoms_te": "ఆకులపై చిరిగిన రంధ్రాలు; సుడిలో తడి రంపపు పొట్టు లాంటి విసర్జన; తర్వాత కంకులకు రంధ్రాలు.",
        "treatments": [
            T("Chemical", "Emamectin benzoate 5 SG", 0.4, "g", "Kills larvae hidden in the whorl.", "When 10% plants show fresh damage (first 30 days) or 20% later.", "Rotate after 10 days", 14, method="Spray directed into the whorl"),
            T("Chemical", "Chlorantraniliprole 18.5 SC", 0.4, "ml", "Long-lasting control; rotation partner.", "Second spray if damage continues.", "Maximum 2 sprays per season", 21, method="Spray directed into the whorl"),
            T("Organic", "Neem Seed Kernel Extract (NSKE) 5%", 50, "g", "Stops young larvae from feeding; low cost.", "At egg and early larva stage (first 2 weeks).", "Every 7 days"),
            T("Organic", "Sand + lime mixture (9:1)", 10, "kg", "Abrasive mixture placed in the whorl damages young larvae.", "Early whorl stage, low infestation.", "Once a week", per="acre", method="Apply a pinch into each whorl"),
        ],
        "prevention": ["Sow at the same time as neighbours.", "Intercrop with red gram or cowpea.", "Check 20 plants per acre every week."],
        "prevention_te": ["పక్కవారితో ఒకేసారి విత్తండి.", "కంది లేదా అలసందతో అంతర పంట వేయండి.", "ప్రతి వారం ఎకరానికి 20 మొక్కలు పరిశీలించండి."],
    },
    {
        "id": "maize-tlb", "crop": "Maize", "name": "Turcicum Leaf Blight", "name_te": "ఆకు ఎండు తెగులు", "type": "Fungal disease",
        "cause": "Fungus Exserohilum turcicum; spreads in cool, wet and humid weather.",
        "cause_te": "శిలీంధ్రం వల్ల వస్తుంది; చల్లని, తడి, తేమ వాతావరణంలో వ్యాపిస్తుంది.",
        "symptoms": "Long cigar-shaped grey-green to tan spots on leaves, starting from lower leaves.",
        "symptoms_te": "కింది ఆకుల నుండి మొదలై పొడవైన సిగార్ ఆకారపు బూడిద-గోధుమ మచ్చలు.",
        "treatments": [
            T("Chemical", "Mancozeb 75 WP", 2.5, "g", "Protective fungicide that stops new infections.", "At first symptoms on lower leaves.", "Repeat after 10-12 days", 15),
            T("Chemical", "Propiconazole 25 EC", 1, "ml", "Systemic fungicide for spreading infection.", "If spots reach the leaves above the cob.", "Once more after 15 days if needed", 30),
        ],
        "prevention": ["Grow resistant hybrids.", "Remove and burn infected crop residue."],
        "prevention_te": ["నిరోధక హైబ్రిడ్లు వాడండి.", "తెగులు సోకిన పంట అవశేషాలు కాల్చివేయండి."],
    },
    {
        "id": "chilli-thrips", "crop": "Chilli", "name": "Thrips & Leaf Curl", "name_te": "తామర పురుగు & ఆకుముడత", "type": "Insect pest / viral",
        "cause": "Thrips and mites suck sap from young leaves; thrips also spread viruses. Worse in dry weather.",
        "cause_te": "తామర పురుగులు, నల్లి లేత ఆకుల రసం పీలుస్తాయి; వైరస్ కూడా వ్యాపింపజేస్తాయి. పొడి వాతావరణంలో ఎక్కువ.",
        "symptoms": "Leaves curl upwards (thrips) or downwards (mites); silvery streaks; plants stunted; flowers drop.",
        "symptoms_te": "ఆకులు పైకి (తామర) లేదా కిందకు (నల్లి) ముడుచుకోవడం; వెండి చారలు; మొక్క ఎదగకపోవడం; పూత రాలడం.",
        "treatments": [
            T("Chemical", "Fipronil 5 SC", 2, "ml", "Controls thrips feeding on new leaves.", "When 2 or more thrips per leaf or first curling.", "Rotate after 10 days", 7),
            T("Chemical", "Spinetoram 11.7 SC", 0.9, "ml", "Rotation partner with a different mode of action.", "If thrips continue after first spray.", "Maximum 2 sprays per season", 5),
            T("Organic", "Neem oil 1500 ppm", 5, "ml", "Repels thrips and mites; safe near harvest.", "Early stage or between chemical sprays.", "Every 7 days"),
            T("Organic", "Blue sticky traps", 10, "traps", "Attract and catch adult thrips.", "From transplanting.", "Replace when full", per="acre", method="Hang just above crop canopy"),
        ],
        "prevention": ["Raise nursery under insect-proof net.", "Remove and destroy virus-infected plants early.", "Grow 2 rows of maize around the field as a barrier."],
        "prevention_te": ["నారును పురుగు నిరోధక వలలో పెంచండి.", "వైరస్ సోకిన మొక్కలను వెంటనే తీసివేయండి.", "పొలం చుట్టూ 2 వరుసల మొక్కజొన్న వేయండి."],
    },
    {
        "id": "chilli-anthracnose", "crop": "Chilli", "name": "Fruit Rot & Die-back (Anthracnose)", "name_te": "కాయ కుళ్లు & కొమ్మ ఎండు తెగులు", "type": "Fungal disease",
        "cause": "Fungus Colletotrichum; spreads with rain splash and high humidity during fruiting.",
        "cause_te": "శిలీంధ్రం వల్ల వస్తుంది; కాయ దశలో వర్షం, ఎక్కువ తేమతో వ్యాపిస్తుంది.",
        "symptoms": "Sunken dark spots with rings on ripe fruits; branch tips dry from the top downwards.",
        "symptoms_te": "పండిన కాయలపై వలయాలతో లోతైన నల్ల మచ్చలు; కొమ్మల చివర్లు పై నుండి కిందకు ఎండిపోవడం.",
        "treatments": [
            T("Chemical", "Propiconazole 25 EC", 1, "ml", "Systemic fungicide that stops the fruit rot fungus.", "At first fruit spots or tip drying.", "Repeat after 15 days", 7),
            T("Chemical", "Azoxystrobin 23 SC", 1, "ml", "Rotation partner with long protection.", "During rainy spells at fruiting.", "Maximum 2 sprays per season", 5),
            T("Chemical", "Mancozeb 75 WP", 2.5, "g", "Protective cover spray before rains.", "Before forecast rain at fruiting stage.", "Every 10-12 days", 10),
        ],
        "prevention": ["Use disease-free seed treated with Trichoderma.", "Remove and destroy infected fruits.", "Avoid water stagnation."],
        "prevention_te": ["ట్రైకోడెర్మాతో శుద్ధి చేసిన విత్తనం వాడండి.", "తెగులు సోకిన కాయలు తీసివేయండి.", "నీరు నిలవకుండా చూడండి."],
    },
    {
        "id": "redgram-podborer", "crop": "Red gram", "name": "Gram Pod Borer", "name_te": "కాయతొలుచు పురుగు", "type": "Insect pest",
        "cause": "Helicoverpa caterpillars that feed on flowers and bore into pods. Peak during flowering in cloudy weather.",
        "cause_te": "పూలు తిని కాయలను తొలిచే లద్దె పురుగులు. మేఘావృత వాతావరణంలో పూత దశలో ఎక్కువ.",
        "symptoms": "Round holes in pods with the caterpillar half inside; damaged flowers and buds.",
        "symptoms_te": "కాయలపై గుండ్రని రంధ్రాలు, పురుగు సగం లోపల; పూలు, మొగ్గలు దెబ్బతినడం.",
        "treatments": [
            T("Chemical", "Chlorantraniliprole 18.5 SC", 0.3, "ml", "Kills larvae with long residual effect.", "At 50% flowering or when 1 larva per plant.", "Once more after 15 days if needed", 30),
            T("Chemical", "Indoxacarb 14.5 SC", 1, "ml", "Rotation partner for heavy attack.", "Second spray at pod formation.", "Do not repeat the same product", 15),
            T("Organic", "Neem Seed Kernel Extract (NSKE) 5%", 50, "g", "Prevents egg laying and young larva feeding.", "At flower initiation.", "Every 7-10 days"),
        ],
        "prevention": ["Install 20 bird perches per acre.", "Use pheromone traps (5 per acre).", "Shake plants over a sheet to collect larvae in small plots."],
        "prevention_te": ["ఎకరానికి 20 పక్షి స్థావరాలు పెట్టండి.", "ఎకరానికి 5 లింగాకర్షక బుట్టలు పెట్టండి.", "చిన్న పొలాల్లో మొక్కలు దులిపి పురుగులు ఏరండి."],
    },
    {
        "id": "groundnut-tikka", "crop": "Groundnut", "name": "Tikka Leaf Spot", "name_te": "టిక్కా ఆకుమచ్చ తెగులు", "type": "Fungal disease",
        "cause": "Fungi Cercospora and Phaeoisariopsis; spread in humid weather from 30 days after sowing.",
        "cause_te": "శిలీంధ్రాల వల్ల వస్తుంది; విత్తిన 30 రోజుల తర్వాత తేమ వాతావరణంలో వ్యాపిస్తుంది.",
        "symptoms": "Brown to black round spots, sometimes with a yellow halo; leaves fall early.",
        "symptoms_te": "గోధుమ నుండి నల్ల రంగు గుండ్రని మచ్చలు, చుట్టూ పసుపు వలయం; ఆకులు ముందుగా రాలిపోవడం.",
        "treatments": [
            T("Chemical", "Hexaconazole 5 EC", 2, "ml", "Systemic fungicide that controls both leaf spots.", "At first spots (around 30-35 days).", "Repeat after 15 days", 15),
            T("Chemical", "Tebuconazole 25.9 EC", 1, "ml", "Rotation partner; also controls rust.", "Second spray if spots continue.", "Maximum 2 sprays", 20),
            T("Chemical", "Mancozeb 75 WP", 2.5, "g", "Low-cost protective spray.", "Before humid spells.", "Every 10-12 days", 15),
        ],
        "prevention": ["Remove and destroy volunteer groundnut plants.", "Rotate with cereals.", "Intercrop with pearl millet (1:3)."],
        "prevention_te": ["పొలంలో అనవసర వేరుశనగ మొక్కలు తీసివేయండి.", "ధాన్యపు పంటలతో మార్పిడి చేయండి.", "సజ్జతో అంతర పంట (1:3)."],
    },
    {
        "id": "turmeric-rhizomerot", "crop": "Turmeric", "name": "Rhizome Rot", "name_te": "దుంప కుళ్లు తెగులు", "type": "Fungal disease",
        "cause": "Soil fungus Pythium; spreads in waterlogged soil and through infected seed rhizomes.",
        "cause_te": "నేలలోని శిలీంధ్రం వల్ల వస్తుంది; నీరు నిలిచిన నేలలో, తెగులు సోకిన విత్తన దుంపల ద్వారా వ్యాపిస్తుంది.",
        "symptoms": "Leaves yellow from the edges and dry; the collar becomes soft and rotten; rhizomes rot with a bad smell.",
        "symptoms_te": "ఆకులు అంచుల నుండి పసుపు రంగుకు మారి ఎండిపోవడం; మొదలు మెత్తబడి కుళ్లడం; దుంపలు దుర్వాసనతో కుళ్లడం.",
        "treatments": [
            T("Chemical", "Copper oxychloride 50 WP", 3, "g", "Kills the rot fungus in the root zone.", "As soon as yellowing plants are seen; drench affected and nearby plants.", "Repeat after 15 days", 30, water=400, method="Soil drench around the plant base"),
            T("Chemical", "Metalaxyl 8% + Mancozeb 64% WP", 2.5, "g", "Systemic fungicide specific to Pythium rot.", "If rot spreads after the first drench.", "Once more after 15-20 days", 30, water=400, method="Soil drench around the plant base"),
            T("Organic", "Trichoderma viride (mixed with 100 kg farmyard manure)", 2, "kg", "Beneficial fungus that protects roots from rot.", "At planting and again at 60 days.", "Twice a season", per="acre", method="Mix with manure and apply to soil"),
        ],
        "prevention": ["Plant on raised beds with good drainage.", "Treat seed rhizomes before planting.", "Remove and burn rotten clumps."],
        "prevention_te": ["మంచి మురుగు నీటి పారుదల ఉన్న ఎత్తు మడులపై నాటండి.", "నాటే ముందు విత్తన దుంపలు శుద్ధి చేయండి.", "కుళ్లిన మొక్కలు తీసి కాల్చివేయండి."],
    },
    {
        "id": "soybean-spodoptera", "crop": "Soybean", "name": "Tobacco Caterpillar", "name_te": "పొగాకు లద్దె పురుగు", "type": "Insect pest",
        "cause": "Spodoptera litura caterpillars feed in groups at night, then spread across the field.",
        "cause_te": "లద్దె పురుగులు రాత్రి గుంపులుగా తిని తర్వాత పొలమంతా వ్యాపిస్తాయి.",
        "symptoms": "Leaves eaten in patches leaving only veins (skeletonised); egg masses covered with brown hair under leaves.",
        "symptoms_te": "ఆకులు ఈనెలు మాత్రమే మిగిలేలా తినేయడం; ఆకుల అడుగున గోధుమ వెంట్రుకలతో గుడ్ల సముదాయాలు.",
        "treatments": [
            T("Chemical", "Chlorantraniliprole 18.5 SC", 0.3, "ml", "Kills caterpillars of all sizes.", "When young larvae are seen in groups.", "Once more after 15 days if needed", 30),
            T("Chemical", "Emamectin benzoate 5 SG", 0.4, "g", "Rotation partner for older larvae.", "Second spray if damage continues.", "Maximum 2 sprays", 10),
            T("Organic", "Neem Seed Kernel Extract (NSKE) 5%", 50, "g", "Stops young larvae from feeding.", "At egg and first larva stage.", "Every 7 days"),
        ],
        "prevention": ["Collect and destroy egg masses and leaves with groups of larvae.", "Grow castor as a trap crop around the field."],
        "prevention_te": ["గుడ్ల సముదాయాలు, పురుగులు ఉన్న ఆకులు ఏరి నాశనం చేయండి.", "పొలం చుట్టూ ఆముదం ఎర పంటగా వేయండి."],
    },
]

INDEX = {d["id"]: d for d in DISEASES}


def plan_for(disease, acres):
    """Work out how much of each product to buy and mix for the given area."""
    out = []
    for t in disease["treatments"]:
        row = dict(t)
        if t["per"] == "litre":
            water = t["water_l_per_acre"] * acres
            row["water_total_l"] = round(water)
            row["per_tank"] = round(t["dose"] * SPRAYER_TANK_L, 1)
            row["tanks"] = round(water / SPRAYER_TANK_L, 1)
            row["total"] = round(t["dose"] * water, 1)
        else:
            row["total"] = round(t["dose"] * acres, 1)
        out.append(row)
    return out


def short_remedy(disease, te=False):
    t = disease["treatments"][0]
    if te:
        # Telugu: the treatment lines have Telugu (see TREATMENT_TE at the end of this file)
        if t["per"] == "litre":
            return (f"{medicine(t['product'])}: లీటరు నీటికి {t['dose']} {t['unit']} "
                    f"({SPRAYER_TANK_L} లీటర్ల ట్యాంకుకు {round(t['dose'] * SPRAYER_TANK_L, 1)} {t['unit']}). {t['when_te']}")
        return f"{medicine(t['product'])}: ఎకరానికి {t['dose']} {t['unit']}. {t['when_te']}"
    if t["per"] == "litre":
        return (f"{t['product']}: {t['dose']} {t['unit']} per litre of water "
                f"({round(t['dose'] * SPRAYER_TANK_L, 1)} {t['unit']} per {SPRAYER_TANK_L}-litre tank). {t['when']}")
    return f"{t['product']}: {t['dose']} {t['unit']} per acre. {t['when']}"


# Telugu for the treatment lines (why / when / repeat), so a farmer reading Telugu
# gets the full spray instructions. Added to each treatment as reason_te, when_te, repeat_te.
TREATMENT_TE = {
    # Why this product
    "Systemic fungicide that stops the blast fungus from entering leaves.": "అగ్గి తెగులు శిలీంధ్రం ఆకులలోకి చేరకుండా ఆపే లోపలికి వెళ్లే (సిస్టమిక్) మందు.",
    "Alternative fungicide - use if Tricyclazole was already sprayed twice.": "ప్రత్యామ్నాయ మందు - ట్రైసైక్లాజోల్ ఇప్పటికే రెండుసార్లు కొట్టి ఉంటే ఇది వాడండి.",
    "Beneficial bacteria that suppress the fungus; safe for the environment.": "శిలీంధ్రాన్ని అణిచే మంచి బ్యాక్టీరియా; పర్యావరణానికి సురక్షితం.",
    "Stops the insects from feeding; gentle on natural enemies like spiders.": "పురుగులు రసం పీల్చకుండా ఆపుతుంది; సాలీడు వంటి మిత్ర పురుగులకు హాని తక్కువ.",
    "Fast-acting alternative for heavy attack.": "ఎక్కువ దాడి ఉన్నప్పుడు త్వరగా పనిచేసే ప్రత్యామ్నాయ మందు.",
    "Repels and reduces egg laying; best in early stage.": "పురుగులను దూరం చేసి గుడ్లు పెట్టడం తగ్గిస్తుంది; మొదట్లోనే బాగా పనిచేస్తుంది.",
    "Kills caterpillars inside the stem; long protection.": "కాండం లోపలి పురుగులను చంపుతుంది; ఎక్కువ రోజులు రక్షణ ఇస్తుంది.",
    "Granules release slowly into water and reach the borer inside the stem.": "గుళికలు నీటిలో నెమ్మదిగా కరిగి కాండం లోపలి పురుగును చేరతాయి.",
    "Catch male moths and reduce mating; also shows when to act.": "మగ రెక్కల పురుగులను పట్టి సంతానం తగ్గిస్తాయి; మందు ఎప్పుడు కొట్టాలో కూడా తెలుపుతాయి.",
    "Contact and stomach poison for young larvae before they enter bolls.": "చిన్న పురుగులు కాయలలోకి చేరకముందే వాటిని చంపే మందు.",
    "Strong larvicide; use as rotation partner.": "పురుగులను బలంగా చంపే మందు; మార్చి మార్చి వాడండి.",
    "Reduces egg laying from early flowering.": "పూత మొదలైనప్పటి నుండి గుడ్లు పెట్టడం తగ్గిస్తుంది.",
    "Trap male moths and tell you when numbers cross the danger level.": "మగ రెక్కల పురుగులను పట్టి, ప్రమాద స్థాయి దాటినప్పుడు తెలుపుతాయి.",
    "Kills adults and nymphs on leaf undersides.": "ఆకుల అడుగున ఉన్న పెద్ద, చిన్న తెల్లదోమలను చంపుతుంది.",
    "Stops feeding quickly; safe for bees when used correctly.": "రసం పీల్చడం త్వరగా ఆపుతుంది; సరిగా వాడితే తేనెటీగలకు సురక్షితం.",
    "Reduces egg laying and repels adults.": "గుడ్లు పెట్టడం తగ్గించి పెద్ద పురుగులను దూరం చేస్తుంది.",
    "Attract and trap adult whiteflies.": "పెద్ద తెల్లదోమలను ఆకర్షించి పట్టుకుంటాయి.",
    "Kills larvae hidden in the whorl.": "సుడిలో దాగిన పురుగులను చంపుతుంది.",
    "Long-lasting control; rotation partner.": "ఎక్కువ రోజులు పనిచేస్తుంది; మార్చి మార్చి వాడే మందు.",
    "Stops young larvae from feeding; low cost.": "చిన్న పురుగులు తినకుండా ఆపుతుంది; తక్కువ ఖర్చు.",
    "Abrasive mixture placed in the whorl damages young larvae.": "సుడిలో వేసే ఈ మిశ్రమం చిన్న పురుగులను దెబ్బతీస్తుంది.",
    "Protective fungicide that stops new infections.": "కొత్తగా తెగులు సోకకుండా కాపాడే మందు.",
    "Systemic fungicide for spreading infection.": "వ్యాపిస్తున్న తెగులుకు లోపలికి వెళ్లే (సిస్టమిక్) మందు.",
    "Controls thrips feeding on new leaves.": "కొత్త ఆకులను పీల్చే తామర పురుగులను అదుపు చేస్తుంది.",
    "Rotation partner with a different mode of action.": "వేరే విధంగా పనిచేసే మందు; మార్చి మార్చి వాడండి.",
    "Repels thrips and mites; safe near harvest.": "తామర పురుగులు, నల్లిని దూరం చేస్తుంది; కోత దగ్గరలో కూడా సురక్షితం.",
    "Attract and catch adult thrips.": "పెద్ద తామర పురుగులను ఆకర్షించి పట్టుకుంటాయి.",
    "Systemic fungicide that stops the fruit rot fungus.": "కాయ కుళ్లు శిలీంధ్రాన్ని ఆపే లోపలికి వెళ్లే (సిస్టమిక్) మందు.",
    "Rotation partner with long protection.": "ఎక్కువ రోజులు రక్షణ ఇచ్చే మందు; మార్చి మార్చి వాడండి.",
    "Protective cover spray before rains.": "వర్షాలకు ముందు కాపాడే పిచికారీ.",
    "Kills larvae with long residual effect.": "పురుగులను చంపి ఎక్కువ రోజులు పనిచేస్తుంది.",
    "Rotation partner for heavy attack.": "ఎక్కువ దాడి ఉన్నప్పుడు మార్చి వాడే మందు.",
    "Prevents egg laying and young larva feeding.": "గుడ్లు పెట్టడం, చిన్న పురుగులు తినడం ఆపుతుంది.",
    "Systemic fungicide that controls both leaf spots.": "రెండు రకాల ఆకు మచ్చలను అదుపు చేసే లోపలికి వెళ్లే (సిస్టమిక్) మందు.",
    "Rotation partner; also controls rust.": "మార్చి వాడే మందు; తుప్పు తెగులును కూడా అదుపు చేస్తుంది.",
    "Low-cost protective spray.": "తక్కువ ఖర్చుతో కాపాడే పిచికారీ.",
    "Kills the rot fungus in the root zone.": "వేర్ల దగ్గర ఉన్న కుళ్లు శిలీంధ్రాన్ని చంపుతుంది.",
    "Systemic fungicide specific to Pythium rot.": "పిథియం దుంప కుళ్లుకు ప్రత్యేకమైన లోపలికి వెళ్లే (సిస్టమిక్) మందు.",
    "Beneficial fungus that protects roots from rot.": "వేర్లను కుళ్లు నుండి కాపాడే మంచి శిలీంధ్రం.",
    "Kills caterpillars of all sizes.": "అన్ని సైజుల పురుగులను చంపుతుంది.",
    "Rotation partner for older larvae.": "పెద్ద పురుగులకు మార్చి వాడే మందు.",
    "Stops young larvae from feeding.": "చిన్న పురుగులు తినకుండా ఆపుతుంది.",
    # When to apply
    "At first spots on leaves, and again at panicle emergence to protect the neck.": "ఆకులపై మొదటి మచ్చలు కనిపించగానే, మళ్లీ వెన్ను బయటకు వచ్చేటప్పుడు మెడను కాపాడటానికి.",
    "When leaf spots are spreading quickly.": "ఆకు మచ్చలు వేగంగా వ్యాపిస్తున్నప్పుడు.",
    "As prevention from tillering stage, or at very first spots.": "పిలకల దశ నుండి ముందు జాగ్రత్తగా, లేదా మొదటి మచ్చలు కనిపించగానే.",
    "When 10 or more hoppers are seen per hill. Drain water first.": "ఒక్కో దుబ్బుకు 10 లేదా ఎక్కువ దోమలు కనిపించినప్పుడు. ముందు నీరు తీసివేయండి.",
    "Heavy infestation or hopper burn patches appearing.": "దాడి ఎక్కువగా ఉన్నప్పుడు లేదా పొలంలో ఎండిన మచ్చలు కనిపించినప్పుడు.",
    "At the first sighting of hoppers.": "దోమలు మొదట కనిపించగానే.",
    "When 5% dead hearts or egg masses are seen.": "5% మొవ్వలు ఎండినప్పుడు లేదా గుడ్ల సముదాయాలు కనిపించినప్పుడు.",
    "At 30-35 days after transplanting with 2-3 cm water in the field.": "నాటిన 30-35 రోజులకు, పొలంలో 2-3 సెం.మీ. నీరు ఉండగా.",
    "From 15 days after transplanting.": "నాటిన 15 రోజుల నుండి.",
    "When 8 moths/trap/night for 3 nights or 10% damaged flowers/bolls.": "ఒక బుట్టలో రాత్రికి 8 రెక్కల పురుగులు 3 రాత్రులు పడినప్పుడు, లేదా 10% పూలు/కాయలు దెబ్బతిన్నప్పుడు.",
    "At second spray if attack continues.": "దాడి కొనసాగితే రెండో పిచికారీగా.",
    "From 45-50 days after sowing.": "విత్తిన 45-50 రోజుల నుండి.",
    "From 40 days after sowing.": "విత్తిన 40 రోజుల నుండి.",
    "When 6-8 adults per leaf on top leaves.": "పై ఆకులపై ఒక్కో ఆకుకు 6-8 తెల్లదోమలు కనిపించినప్పుడు.",
    "If whitefly continues after first spray.": "మొదటి పిచికారీ తర్వాత కూడా తెల్లదోమ ఉంటే.",
    "Early stage, low numbers.": "మొదటి దశలో, పురుగులు తక్కువగా ఉన్నప్పుడు.",
    "From early crop stage.": "పంట మొదటి దశ నుండి.",
    "When 10% plants show fresh damage (first 30 days) or 20% later.": "మొదటి 30 రోజుల్లో 10% మొక్కలకు, తర్వాత 20% మొక్కలకు కొత్త నష్టం కనిపించినప్పుడు.",
    "Second spray if damage continues.": "నష్టం కొనసాగితే రెండో పిచికారీ.",
    "At egg and early larva stage (first 2 weeks).": "గుడ్లు, చిన్న పురుగుల దశలో (మొదటి 2 వారాలు).",
    "Early whorl stage, low infestation.": "సుడి మొదటి దశలో, దాడి తక్కువగా ఉన్నప్పుడు.",
    "At first symptoms on lower leaves.": "కింది ఆకులపై మొదటి లక్షణాలు కనిపించగానే.",
    "If spots reach the leaves above the cob.": "మచ్చలు కంకి పై ఆకులకు చేరితే.",
    "When 2 or more thrips per leaf or first curling.": "ఒక్కో ఆకుకు 2 లేదా ఎక్కువ తామర పురుగులు ఉన్నప్పుడు, లేదా ఆకు ముడత మొదలవగానే.",
    "If thrips continue after first spray.": "మొదటి పిచికారీ తర్వాత కూడా తామర పురుగులు ఉంటే.",
    "Early stage or between chemical sprays.": "మొదటి దశలో లేదా రసాయన పిచికారీల మధ్యలో.",
    "From transplanting.": "నాటినప్పటి నుండి.",
    "At first fruit spots or tip drying.": "కాయలపై మొదటి మచ్చలు లేదా కొనలు ఎండటం కనిపించగానే.",
    "During rainy spells at fruiting.": "కాయ దశలో వర్షాలు కురుస్తున్నప్పుడు.",
    "Before forecast rain at fruiting stage.": "కాయ దశలో వర్షం సూచన ఉన్నప్పుడు ముందుగానే.",
    "At 50% flowering or when 1 larva per plant.": "50% పూత దశలో, లేదా ఒక్కో మొక్కకు 1 పురుగు కనిపించినప్పుడు.",
    "Second spray at pod formation.": "కాయ ఏర్పడేటప్పుడు రెండో పిచికారీ.",
    "At flower initiation.": "పూత మొదలయ్యేటప్పుడు.",
    "At first spots (around 30-35 days).": "మొదటి మచ్చలు కనిపించగానే (సుమారు 30-35 రోజులకు).",
    "Second spray if spots continue.": "మచ్చలు కొనసాగితే రెండో పిచికారీ.",
    "Before humid spells.": "తేమ ఎక్కువగా ఉండే రోజులకు ముందు.",
    "As soon as yellowing plants are seen; drench affected and nearby plants.": "మొక్కలు పసుపు రంగుకు మారడం కనిపించగానే; తెగులు సోకిన, చుట్టుపక్కల మొక్కల మొదళ్లలో పోయండి.",
    "If rot spreads after the first drench.": "మొదటిసారి పోసిన తర్వాత కూడా కుళ్లు వ్యాపిస్తే.",
    "At planting and again at 60 days.": "నాటేటప్పుడు, మళ్లీ 60 రోజులకు.",
    "When young larvae are seen in groups.": "చిన్న పురుగులు గుంపులుగా కనిపించినప్పుడు.",
    "At egg and first larva stage.": "గుడ్లు, మొదటి పురుగుల దశలో.",
    # Repeat
    "Repeat after 10-15 days if spots continue": "మచ్చలు కొనసాగితే 10-15 రోజుల తర్వాత మళ్లీ కొట్టండి",
    "Once more after 12-15 days if needed": "అవసరమైతే 12-15 రోజుల తర్వాత మరోసారి",
    "Every 10 days, 2-3 times": "ప్రతి 10 రోజులకు, 2-3 సార్లు",
    "Once more after 15 days if hoppers return": "దోమలు మళ్లీ వస్తే 15 రోజుల తర్వాత మరోసారి",
    "Do not repeat the same product - rotate": "అదే మందు మళ్లీ వాడవద్దు - వేరే మందుకు మార్చండి",
    "Every 7-10 days": "ప్రతి 7-10 రోజులకు",
    "Once more after 20 days if needed": "అవసరమైతే 20 రోజుల తర్వాత మరోసారి",
    "Single application": "ఒక్కసారి వేస్తే చాలు",
    "Change lure every 25-30 days": "ప్రతి 25-30 రోజులకు ఎర (ల్యూర్) మార్చండి",
    "Rotate with another product after 10-15 days": "10-15 రోజుల తర్వాత వేరే మందుకు మార్చండి",
    "Do not use more than twice a season": "ఒక సీజన్‌లో రెండుసార్ల కంటే ఎక్కువ వాడవద్దు",
    "Every 10 days": "ప్రతి 10 రోజులకు",
    "Change lure every 3 weeks": "ప్రతి 3 వారాలకు ఎర (ల్యూర్) మార్చండి",
    "Rotate after 10-12 days": "10-12 రోజుల తర్వాత వేరే మందుకు మార్చండి",
    "Once more after 15 days if needed": "అవసరమైతే 15 రోజుల తర్వాత మరోసారి",
    "Every 7 days": "ప్రతి 7 రోజులకు",
    "Replace when full": "అట్టలు నిండగానే మార్చండి",
    "Rotate after 10 days": "10 రోజుల తర్వాత వేరే మందుకు మార్చండి",
    "Maximum 2 sprays per season": "ఒక సీజన్‌లో గరిష్టంగా 2 పిచికారీలు",
    "Once a week": "వారానికి ఒకసారి",
    "Repeat after 10-12 days": "10-12 రోజుల తర్వాత మళ్లీ కొట్టండి",
    "Repeat after 15 days": "15 రోజుల తర్వాత మళ్లీ కొట్టండి",
    "Every 10-12 days": "ప్రతి 10-12 రోజులకు",
    "Do not repeat the same product": "అదే మందు మళ్లీ వాడవద్దు",
    "Maximum 2 sprays": "గరిష్టంగా 2 పిచికారీలు",
    "Once more after 15-20 days": "15-20 రోజుల తర్వాత మరోసారి",
    "Twice a season": "సీజన్‌కు రెండుసార్లు",
}

for _d in DISEASES:
    for _t in _d["treatments"]:
        for _k in ("reason", "when", "repeat"):
            _t[f"{_k}_te"] = TREATMENT_TE.get(_t[_k], _t[_k])


def search(query):
    """Disease library search: problems whose crop or name matches the typed text
    (English or Telugu, any case). Returns (matching diseases, catalogue crop name or None)."""
    from . import data
    q = " ".join(str(query or "").split()).lower()
    if not q:
        return DISEASES, None
    found = [d for d in DISEASES
             if q in d["crop"].lower() or q in data.crop_te(d["crop"]) or q in d["name"].lower() or q in d["name_te"]]
    # Which crop was typed (to name it in the "nothing yet" message); spellings vary a little, e.g. టమాట / టమాటా
    crop = next((name for name, te, _, _ in data.CROP_CATALOG
                 if q in (name.lower(), te) or q in name.lower().split(" (")[0] or te in q or q in te), None)
    return found, crop
