"""Telugu words shared by the React and Streamlit apps.

The app starts in Telugu (most farmers read Telugu, not English) and has a
తెలుగు | English switch. Two kinds of words live here:

* VALUES - data values stored in English (soil, season, status, ...) and the
  Telugu shown for them. Use te(value) to translate one; unknown values come
  back unchanged.
* UI - common screen words, so both apps say the same thing in Telugu.

React gets both from GET /api/terms; Streamlit imports this module.
Crop, district, scheme, weather and disease names already have their own
Telugu fields in data.py / diseases.py.
"""

VALUES = {
    # Seasons
    "Kharif": "ఖరీఫ్", "Rabi": "రబీ", "Summer": "వేసవి", "Both": "రెండు సీజన్లు",
    # Soil
    "Black cotton": "నల్ల రేగడి నేల", "Red sandy loam": "ఎర్ర ఇసుక నేల", "Alluvial": "ఒండ్రు నేల",
    "Red loam": "ఎర్ర నేల", "Clay": "బంకమట్టి నేల", "Sandy": "ఇసుక నేల",
    # Water source
    "Borewell": "బోరుబావి", "Canal": "కాలువ", "Tank": "చెరువు", "Rainfed": "వర్షాధారం",
    "Drip": "బిందు సేద్యం", "Sprinkler": "తుంపర సేద్యం",
    # Gender
    "Male": "పురుషుడు", "Female": "స్త్రీ", "Other": "ఇతర",
    # Scheme application / grievance status
    "Approved": "ఆమోదించబడింది", "Credited": "డబ్బు జమ అయింది", "Pending verification": "పరిశీలనలో ఉంది",
    "Rejected - land record mismatch": "తిరస్కరించబడింది - భూ రికార్డు సరిపోలలేదు", "Under review": "సమీక్షలో ఉంది",
    "Open": "నమోదైంది", "In progress": "పని జరుగుతోంది", "Resolved": "పరిష్కరించబడింది",
    "Escalated": "పై అధికారులకు పంపబడింది",
    # Grievance categories
    "Payment not received": "డబ్బు జమ కాలేదు", "Land record correction": "భూ రికార్డు సవరణ",
    "Seed quality": "విత్తన నాణ్యత", "Fertilizer shortage": "ఎరువుల కొరత",
    "Crop insurance claim": "పంట బీమా క్లెయిమ్", "Name mismatch in Aadhaar": "ఆధార్‌లో పేరు తేడా",
    # Channels
    "Web chatbot": "వెబ్ చాట్", "WhatsApp": "వాట్సాప్", "Voice bot": "వాయిస్ బాట్", "Rythu Vedika": "రైతు వేదిక",
    # Disease types and remedy kinds
    "Fungal disease": "శిలీంధ్ర తెగులు", "Insect pest": "పురుగు", "Insect pest / viral": "పురుగు / వైరస్ తెగులు",
    "Chemical": "రసాయన మందు", "Organic": "సేంద్రియ / తక్కువ ఖర్చు",
    # Crop Doctor follow-up
    "yes": "వాడాను", "partly": "కొంత వాడాను", "no": "వాడలేదు",
    "Used it": "వాడాను", "Used partly": "కొంత వాడాను", "Did not use": "వాడలేదు",
    "cured": "పూర్తిగా తగ్గింది", "improved": "మెరుగుపడింది", "no_change": "మార్పు లేదు", "worse": "ఎక్కువైంది",
    "Cured": "పూర్తిగా తగ్గింది", "Improved": "మెరుగుపడింది", "No change": "మార్పు లేదు", "Got worse": "ఎక్కువైంది",
    "Could not afford it": "కొనలేకపోయాను", "Not available in the shop": "దుకాణంలో దొరకలేదు",
    "Used something else": "వేరే మందు వాడాను", "Problem went away on its own": "దానంతట అదే తగ్గింది",
    "Waiting to confirm with AEO": "AEO తో నిర్ధారించాలి", "Something else": "వేరే మందు",
    # Where an entry came from
    "Crop Doctor": "పంట వైద్యుడు", "Chat photo": "చాట్ ఫోటో", "My Details": "నా వివరాలు",
    "Department records (demo)": "శాఖ రికార్డులు (డెమో)", "Added by farmer": "రైతు జోడించారు",
    # Roles
    "Farmer": "రైతు", "Department Admin": "శాఖ అడ్మిన్", "NISG Contributor": "NISG కంట్రిబ్యూటర్",
    "Department Reviewer": "శాఖ సమీక్షకులు", "Bharat Vistaar Central Team": "భారత్ విస్తార్ కేంద్ర బృందం",
}

# Medicine names (Crop Doctor remedies) as shown in Telugu. Bottle and packet labels are
# printed in English, so the English name stays in brackets for anything bought in a shop.
_MEDICINES_TE = {
    "Azoxystrobin 23 SC": "అజాక్సిస్ట్రోబిన్ 23 SC",
    "Cartap hydrochloride 4G (granules)": "కార్టాప్ హైడ్రోక్లోరైడ్ 4G (గుళికలు)",
    "Chlorantraniliprole 18.5 SC": "క్లోరాంట్రానిలిప్రోల్ 18.5 SC",
    "Copper oxychloride 50 WP": "కాపర్ ఆక్సీక్లోరైడ్ 50 WP",
    "Diafenthiuron 50 WP": "డయాఫెంథియురాన్ 50 WP",
    "Dinotefuran 20 SG": "డైనోటెఫ్యూరాన్ 20 SG",
    "Emamectin benzoate 5 SG": "ఇమామెక్టిన్ బెంజోయేట్ 5 SG",
    "Fipronil 5 SC": "ఫిప్రోనిల్ 5 SC",
    "Flonicamid 50 WG": "ఫ్లోనికామిడ్ 50 WG",
    "Hexaconazole 5 EC": "హెక్సాకోనజోల్ 5 EC",
    "Indoxacarb 14.5 SC": "ఇండాక్సాకార్బ్ 14.5 SC",
    "Isoprothiolane 40 EC": "ఐసోప్రోథయోలేన్ 40 EC",
    "Mancozeb 75 WP": "మాంకోజెబ్ 75 WP",
    "Metalaxyl 8% + Mancozeb 64% WP": "మెటాలాక్సిల్ 8% + మాంకోజెబ్ 64% WP",
    "Neem Seed Kernel Extract (NSKE) 5%": "వేప గింజల కషాయం (NSKE) 5%",
    "Neem oil 1500 ppm": "వేప నూనె 1500 ppm",
    "Profenofos 50 EC": "ప్రొఫెనోఫాస్ 50 EC",
    "Propiconazole 25 EC": "ప్రొపికోనజోల్ 25 EC",
    "Pseudomonas fluorescens 1.5% WP": "సూడోమోనాస్ ఫ్లోరెసెన్స్ 1.5% WP",
    "Pymetrozine 50 WG": "పైమెట్రోజిన్ 50 WG",
    "Spinetoram 11.7 SC": "స్పైనెటోరామ్ 11.7 SC",
    "Tebuconazole 25.9 EC": "టెబుకోనజోల్ 25.9 EC",
    "Trichoderma viride (mixed with 100 kg farmyard manure)": "ట్రైకోడెర్మా విరిడి (100 కిలోల పశువుల ఎరువులో కలిపి)",
    "Tricyclazole 75 WP": "ట్రైసైక్లజోల్ 75 WP",
    "Pheromone traps (Gossyplure)": "లింగాకర్షక బుట్టలు (గాసిప్లూర్)",
    "Pheromone traps (Scirpophaga lure)": "లింగాకర్షక బుట్టలు (కాండం తొలిచే పురుగు ఎర)",
}
# Made at home or plain things - no shop label to match, so Telugu only
_PLAIN_TE = {
    "Blue sticky traps": "నీలం జిగురు అట్టలు",
    "Yellow sticky traps": "పసుపు జిగురు అట్టలు",
    "Sand + lime mixture (9:1)": "ఇసుక + సున్నం మిశ్రమం (9:1)",
    "Something else": "వేరే మందు",
}
MEDICINES = {**{en: f"{te_name} ({en})" for en, te_name in _MEDICINES_TE.items()}, **_PLAIN_TE}


def medicine(name, te=True):
    """A medicine name for the screen: Telugu with the English label in brackets, or English."""
    return MEDICINES.get(name, name) if te else name


# Common screen words - use these exact Telugu words in both apps
UI = {
    "Rythu Mitra": "రైతు మిత్ర",
    "Telangana Agriculture Dept × Bharat Vistaar": "తెలంగాణ వ్యవసాయ శాఖ × భారత్ విస్తార్",
    "Prototype with dummy data": "నమూనా సమాచారంతో ప్రయోగాత్మక యాప్",
    "My Details": "నా వివరాలు", "Farmer Chat": "రైతు చాట్", "Crop Doctor": "పంట వైద్యుడు",
    "Farmer Services": "రైతు సేవలు", "My history": "నా చరిత్ర", "How the app works": "యాప్ ఎలా పనిచేస్తుంది",
    "Change password": "పాస్‌వర్డ్ మార్చండి", "Log out": "లాగ్ అవుట్", "Log in": "లాగిన్",
    "User ID": "యూజర్ ID", "Farmer ID": "రైతు ID", "Password": "పాస్‌వర్డ్", "Forgot password?": "పాస్‌వర్డ్ మర్చిపోయారా?",
    "Remember me": "నన్ను గుర్తుంచుకో", "Mobile": "మొబైల్", "Bank": "బ్యాంక్",
    "Full name": "పూర్తి పేరు", "Village": "గ్రామం", "District": "జిల్లా", "Age": "వయస్సు", "Gender": "లింగం",
    "Total land": "మొత్తం భూమి", "acres": "ఎకరాలు", "Land plots": "భూమి ముక్కలు", "Plot": "భూమి ముక్క",
    "Survey no.": "సర్వే నం.", "Crop": "పంట", "Crops": "పంటలు", "Season": "సీజన్", "Soil": "నేల",
    "Water source": "నీటి వనరు", "Area (acres)": "విస్తీర్ణం (ఎకరాలు)",
    "Edit details": "వివరాలు మార్చండి", "Save changes": "మార్పులు సేవ్ చేయండి", "Save": "సేవ్ చేయండి",
    "Cancel": "రద్దు చేయండి", "Back": "వెనక్కి", "Delete": "తొలగించండి", "Edit": "మార్చండి",
    "Saved to your account": "మీ ఖాతాలో సేవ్ అయింది",
    "Crops grown": "సాగు చేసిన పంటలు", "Problems & remedies": "సమస్యలు & నివారణలు",
    "Growing now": "ఇప్పుడు సాగులో ఉంది", "Harvested": "కోత పూర్తయింది", "Mark harvested": "కోత పూర్తయింది",
    "Add a past crop": "పాత పంట జోడించండి", "Sown in": "విత్తిన నెల", "Harvested in": "కోసిన నెల",
    "Still growing": "ఇంకా సాగులో ఉంది", "Harvest": "దిగుబడి", "quintals": "క్వింటాళ్లు", "qtl": "క్వి.",
    "From": "నుండి", "To": "వరకు", "All plots": "అన్ని భూమి ముక్కలు", "Timeline": "కాలక్రమం",
    "Scheme applications": "పథకాల దరఖాస్తులు", "Grievances": "ఫిర్యాదులు", "Weather": "వాతావరణం",
    "Advisory": "సలహాలు", "Status": "స్థితి", "Amount": "మొత్తం", "Date": "తేదీ",
    "Waiting for feedback": "మీ సమాధానం కోసం ఎదురుచూస్తోంది", "Tell us if it worked": "మందు పనిచేసిందో చెప్పండి",
    "Mock AI mode": "మాక్ AI మోడ్",
}


# Error messages the backend sends, as (regular expression, Telugu). {1}, {2} are the
# numbers/words captured by the brackets in the pattern. Use te_error(message).
ERRORS = [
    (r"You have already applied for this scheme\.", "ఈ పథకానికి మీరు ఇప్పటికే దరఖాస్తు చేశారు."),
    (r"Please choose a scheme\.", "దయచేసి ఒక పథకాన్ని ఎంచుకోండి."),
    (r"Incorrect user ID or password\. (\d+) attempt\(s\) left\.", "యూజర్ ID లేదా పాస్‌వర్డ్ తప్పు. ఇంకా {1} ప్రయత్నాలు మిగిలాయి."),
    (r"Incorrect user ID or password\.", "యూజర్ ID లేదా పాస్‌వర్డ్ తప్పు."),
    (r"Account locked after too many failed attempts\. Try again in (\d+) min or reset your password\.",
     "చాలాసార్లు తప్పు పాస్‌వర్డ్ వేశారు. {1} నిమిషాల తర్వాత ప్రయత్నించండి లేదా పాస్‌వర్డ్ మార్చండి."),
    (r"Account locked for (\d+) minutes after (\d+) failed attempts\.",
     "{2} సార్లు తప్పు పాస్‌వర్డ్ వేశారు. ఖాతా {1} నిమిషాలు ఆపివేయబడింది."),
    (r"User ID not found\.", "ఈ యూజర్ ID కనబడలేదు."),
    (r"Farmer ID not found in department records\.", "ఈ రైతు ID శాఖ రికార్డులలో లేదు."),
    (r"Mobile number does not match the one registered with the department\.", "మొబైల్ నంబర్ శాఖ రికార్డులోని నంబర్‌తో సరిపోలలేదు."),
    (r"An account already exists for this Farmer ID\. Use Login or Forgot password\.",
     "ఈ రైతు ID కి ఇప్పటికే ఖాతా ఉంది. లాగిన్ చేయండి లేదా 'పాస్‌వర్డ్ మర్చిపోయారా?' వాడండి."),
    (r"Passwords do not match\.", "రెండు పాస్‌వర్డ్‌లు ఒకేలా లేవు."),
    (r"Password must be at least 8 characters and contain letters and numbers\.",
     "పాస్‌వర్డ్‌లో కనీసం 8 అక్షరాలు ఉండాలి - అక్షరాలు, అంకెలు రెండూ ఉండాలి."),
    (r"Current password is incorrect\.", "ప్రస్తుత పాస్‌వర్డ్ తప్పు."),
    (r"New password must be different from the current one\.", "కొత్త పాస్‌వర్డ్ పాతదానికి భిన్నంగా ఉండాలి."),
    (r"The code has expired or was not requested\. Request a new one\.", "కోడ్ గడువు ముగిసింది. కొత్త కోడ్ అడగండి."),
    (r"Too many wrong codes\. Request a new one\.", "చాలాసార్లు తప్పు కోడ్ వేశారు. కొత్త కోడ్ అడగండి."),
    (r"Incorrect code\.", "కోడ్ తప్పు."),
    (r"Please log in again\.", "దయచేసి మళ్లీ లాగిన్ చేయండి."),
    (r"Please enter your full name \(2 to 60 letters\)\.", "మీ పూర్తి పేరు రాయండి."),
    (r"Please enter your village name\.", "మీ గ్రామం పేరు రాయండి."),
    (r"Please choose a district from the list\.", "జాబితా నుండి జిల్లా ఎంచుకోండి."),
    (r"Age must be a number\.", "వయస్సు అంకెలలో రాయండి."),
    (r"Age must be between 18 and 100\.", "వయస్సు 18 నుండి 100 మధ్య ఉండాలి."),
    (r"Please choose a gender\.", "లింగం ఎంచుకోండి."),
    (r"Add at least one land plot\.", "కనీసం ఒక భూమి ముక్క జోడించండి."),
    (r"You can add up to (\d+) plots\.", "{1} భూమి ముక్కల వరకు మాత్రమే జోడించవచ్చు."),
    (r"Plot (\d+): enter the survey number\.", "భూమి ముక్క {1}: సర్వే నంబర్ రాయండి."),
    (r"Plot (\d+): survey number (.+) is entered twice\.", "భూమి ముక్క {1}: సర్వే నంబర్ {2} రెండుసార్లు వచ్చింది."),
    (r"Plot (\d+): area must be a number\.", "భూమి ముక్క {1}: విస్తీర్ణం అంకెలలో రాయండి."),
    (r"Plot (\d+): area must be between 0\.1 and 100 acres\.", "భూమి ముక్క {1}: విస్తీర్ణం 0.1 నుండి 100 ఎకరాల మధ్య ఉండాలి."),
    (r"Plot (\d+): enter a crop name \(letters only\)\.", "భూమి ముక్క {1}: పంట పేరు రాయండి."),
    (r"Plot (\d+): choose a soil type\.", "భూమి ముక్క {1}: నేల రకం ఎంచుకోండి."),
    (r"Plot (\d+): choose a water source\.", "భూమి ముక్క {1}: నీటి వనరు ఎంచుకోండి."),
    (r"Plot (\d+): choose a season\.", "భూమి ముక్క {1}: సీజన్ ఎంచుకోండి."),
    (r"Enter the crop name\.", "పంట పేరు రాయండి."),
    (r"Choose a season\.", "సీజన్ ఎంచుకోండి."),
    (r"Sowing month: choose a month\.", "విత్తిన నెల ఎంచుకోండి."),
    (r"Harvest month: choose a month\.", "కోసిన నెల ఎంచుకోండి."),
    (r"Sowing month cannot be in the future\.", "విత్తిన నెల రాబోయే నెల కాకూడదు."),
    (r"Harvest month cannot be in the future\.", "కోసిన నెల రాబోయే నెల కాకూడదు."),
    (r"(Sowing|Harvest) month is too far in the past\.", "ఈ నెల చాలా పాతది."),
    (r"Harvest month cannot be before the sowing month\.", "కోసిన నెల విత్తిన నెల కంటే ముందు ఉండకూడదు."),
    (r"Area must be a number\.", "విస్తీర్ణం అంకెలలో రాయండి."),
    (r"Area must be between 0\.1 and 100 acres\.", "విస్తీర్ణం 0.1 నుండి 100 ఎకరాల మధ్య ఉండాలి."),
    (r"Yield must be a number \(quintals\)\.", "దిగుబడి క్వింటాళ్లలో అంకెలుగా రాయండి."),
    (r"Yield looks wrong - enter quintals for the whole area\.", "దిగుబడి సరిగా లేదు - మొత్తం భూమికి క్వింటాళ్లు రాయండి."),
    (r"Crop entry not found\.", "ఈ పంట వివరం కనబడలేదు."),
    (r"Please tell us if you used the remedy\.", "మందు వాడారో లేదో చెప్పండి."),
    (r"Please tell us how it worked\.", "ఫలితం ఎలా ఉందో చెప్పండి."),
    (r"Please choose why the remedy was not used\.", "మందు ఎందుకు వాడలేదో ఎంచుకోండి."),
    (r"Spray date is not a valid date\.", "పిచికారీ తేదీ సరిగా లేదు."),
    (r"Spray date cannot be in the future\.", "పిచికారీ తేదీ రాబోయే తేదీ కాకూడదు."),
    (r"Spray date cannot be before the disease was spotted\.", "పిచికారీ తేదీ తెగులు కనిపించిన తేదీ కంటే ముందు ఉండకూడదు."),
    (r"History entry not found\.", "ఈ చరిత్ర వివరం కనబడలేదు."),
    (r"Plot (\d+): sowing date is not a valid date\.", "భూమి ముక్క {1}: విత్తిన తేదీ సరిగా లేదు."),
    (r"Plot (\d+): harvest date is not a valid date\.", "భూమి ముక్క {1}: కోత తేదీ సరిగా లేదు."),
    (r"Plot (\d+): sowing date must be within the last 2 years or the next 6 months\.",
     "భూమి ముక్క {1}: విత్తిన తేదీ గత 2 సంవత్సరాలు లేదా రాబోయే 6 నెలల లోపు ఉండాలి."),
    (r"Plot (\d+): harvest date must be after the sowing date\.", "భూమి ముక్క {1}: కోత తేదీ విత్తిన తేదీ తర్వాత ఉండాలి."),
    (r"Plot (\d+): harvest date must be within 2 years of sowing\.", "భూమి ముక్క {1}: కోత తేదీ విత్తిన 2 సంవత్సరాల లోపు ఉండాలి."),
    (r"You can only update your own history\.", "మీ చరిత్రను మాత్రమే మార్చగలరు."),
    (r"Could not read the photo\. Please send a JPG or PNG picture\.", "ఫోటో చదవలేకపోయాం. JPG లేదా PNG ఫోటో పంపండి."),
    (r"Unknown photo type\.", "ఈ రకం ఫోటో తెలియదు."),
    (r"Farmer not found\.?", "రైతు వివరాలు కనబడలేదు."),
    (r"Image too large \(max 8 MB\)", "ఫోటో చాలా పెద్దది (8 MB వరకు మాత్రమే)."),
    (r"Video too large \(max 50 MB\)", "వీడియో చాలా పెద్దది (50 MB వరకు మాత్రమే)."),
    (r"Could not read the video\. Please send an MP4 video or photos\.", "వీడియో చదవలేకపోయాం. MP4 వీడియో లేదా ఫోటోలు పంపండి."),
    (r"Please add at least one photo or video\.", "కనీసం ఒక ఫోటో లేదా వీడియో పెట్టండి."),
]


def te_error(message):
    """Telugu for a backend error message (English is returned if there is no match)."""
    import re
    for pattern, telugu in ERRORS:
        m = re.fullmatch(pattern, (message or "").strip())
        if m:
            return telugu.format(None, *m.groups())
    return message


def te(value):
    """Telugu for a data value or screen word; anything unknown is returned as is."""
    return VALUES.get(value) or UI.get(value) or value
