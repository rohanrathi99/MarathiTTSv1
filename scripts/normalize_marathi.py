"""
Marathi Text Normalizer for TTS  — v2 (Fixed & Enhanced)
=========================================================
Changes from v1:
  FIX  : Complete Marathi number lookup for 1-100 retained (unique compound words)
  FIX  : Proper हजार/लाख/कोटी handling retained
  FIX  : Abbreviation expansion order (longest first) retained
  NEW  : Decimal number support  (3.14 → तीन दशांश एक चार)
  NEW  : Ordinal number support  (1ला, 2रा, 3रा … → पहिला, दुसरा, तिसरा …)
  NEW  : DD/MM/YYYY and DD-MM-YYYY date expansion
  NEW  : Currency symbols  (₹, $, €) → spoken form
  NEW  : Percentage  (25%) → पंचवीस टक्के
  NEW  : Time  (10:30) → दहा वाजून तीस मिनिटे
  NEW  : Extended abbreviation dictionary (25 entries)
  NOTE : num2words does NOT support Marathi — manual lookup is required.
"""
import re

# =============================================================================
# Marathi Number System — Complete lookup 0-100
# Marathi has UNIQUE compound words for every number; simple tens+ones won't work.
# =============================================================================
MARATHI_NUMBERS = {
    0: 'शून्य',
    1: 'एक',    2: 'दोन',    3: 'तीन',    4: 'चार',    5: 'पाच',
    6: 'सहा',   7: 'सात',    8: 'आठ',     9: 'नऊ',     10: 'दहा',
    11: 'अकरा', 12: 'बारा',  13: 'तेरा',  14: 'चौदा',  15: 'पंधरा',
    16: 'सोळा', 17: 'सतरा',  18: 'अठरा',  19: 'एकोणीस',20: 'वीस',
    21: 'एकवीस',    22: 'बावीस',     23: 'तेवीस',     24: 'चोवीस',     25: 'पंचवीस',
    26: 'सव्वीस',   27: 'सत्तावीस',  28: 'अठ्ठावीस',  29: 'एकोणतीस',   30: 'तीस',
    31: 'एकतीस',    32: 'बत्तीस',    33: 'तेहेतीस',   34: 'चौतीस',     35: 'पस्तीस',
    36: 'छत्तीस',   37: 'सदतीस',    38: 'अडतीस',     39: 'एकोणचाळीस', 40: 'चाळीस',
    41: 'एक्केचाळीस',42: 'बेचाळीस', 43: 'त्रेचाळीस', 44: 'चव्वेचाळीस', 45: 'पंचेचाळीस',
    46: 'सेहेचाळीस', 47: 'सत्तेचाळीस',48: 'अठ्ठेचाळीस',49: 'एकोणपन्नास', 50: 'पन्नास',
    51: 'एक्कावन्न', 52: 'बावन्न',   53: 'त्रेपन्न',  54: 'चौपन्न',    55: 'पंचावन्न',
    56: 'छप्पन्न',   57: 'सत्तावन्न', 58: 'अठ्ठावन्न', 59: 'एकोणसाठ',   60: 'साठ',
    61: 'एकसष्ट',   62: 'बासष्ट',    63: 'त्रेसष्ट',  64: 'चौसष्ट',    65: 'पासष्ट',
    66: 'सहासष्ट',  67: 'सदुसष्ट',   68: 'अडुसष्ट',   69: 'एकोणसत्तर', 70: 'सत्तर',
    71: 'एकाहत्तर', 72: 'बाहत्तर',   73: 'त्र्याहत्तर',74: 'चौऱ्याहत्तर',75: 'पंच्याहत्तर',
    76: 'शहात्तर',  77: 'सत्याहत्तर', 78: 'अठ्ठ्याहत्तर',79: 'एकोणऐंशी', 80: 'ऐंशी',
    81: 'एक्क्याऐंशी',82: 'ब्याऐंशी', 83: 'त्र्याऐंशी', 84: 'चौऱ्याऐंशी',85: 'पंच्याऐंशी',
    86: 'शहाऐंशी',  87: 'सत्त्याऐंशी',88: 'अठ्ठ्याऐंशी',89: 'एकोणनव्वद', 90: 'नव्वद',
    91: 'एक्क्याण्णव',92: 'ब्याण्णव', 93: 'त्र्याण्णव', 94: 'चौऱ्याण्णव',95: 'पंच्याण्णव',
    96: 'शहाण्णव',  97: 'सत्त्याण्णव',98: 'अठ्ठ्याण्णव',99: 'नव्व्याण्णव', 100: 'शंभर',
}

# Hundreds: 200–900
MARATHI_HUNDREDS = {
    1: 'शंभर', 2: 'दोनशे', 3: 'तीनशे', 4: 'चारशे', 5: 'पाचशे',
    6: 'सहाशे', 7: 'सातशे', 8: 'आठशे', 9: 'नऊशे',
}

# Ordinals 1–20 (unique forms; higher are handled generically)
MARATHI_ORDINALS = {
    1: 'पहिला',    2: 'दुसरा',    3: 'तिसरा',    4: 'चौथा',
    5: 'पाचवा',    6: 'सहावा',    7: 'सातवा',    8: 'आठवा',
    9: 'नववा',     10: 'दहावा',   11: 'अकरावा',  12: 'बारावा',
    13: 'तेरावा',  14: 'चौदावा',  15: 'पंधरावा', 16: 'सोळावा',
    17: 'सतरावा',  18: 'अठरावा',  19: 'एकोणिसावा',20: 'विसावा',
}

# Month names in Marathi
MARATHI_MONTHS = {
    1: 'जानेवारी', 2: 'फेब्रुवारी', 3: 'मार्च',    4: 'एप्रिल',
    5: 'मे',       6: 'जून',         7: 'जुलै',     8: 'ऑगस्ट',
    9: 'सप्टेंबर', 10: 'ऑक्टोबर',  11: 'नोव्हेंबर', 12: 'डिसेंबर',
}

# Digit-by-digit pronunciation (for decimals after decimal point)
MARATHI_DIGITS = {str(i): MARATHI_NUMBERS[i] for i in range(10)}

# =============================================================================
# Abbreviations — expanded dictionary (25 entries, longest-first safe)
# =============================================================================
ABBREVIATIONS = {
    # Titles
    'डॉ.': 'डॉक्टर',
    'श्रीम.': 'श्रीमती',
    'श्री.': 'श्रीमान',
    'सौ.': 'सौभाग्यवती',
    'कु.': 'कुमारी',
    'प्रा.': 'प्राध्यापक',
    'प्रो.': 'प्रोफेसर',
    'न्या.': 'न्यायमूर्ती',
    'आ.': 'आमदार',
    'खा.': 'खासदार',
    # Organisations / places
    'अ.भा.': 'अखिल भारतीय',
    'म.रा.': 'महाराष्ट्र राज्य',
    'म.': 'महाराष्ट्र',
    'वि.': 'विद्यापीठ',
    'म.न.पा.': 'महानगरपालिका',
    'ग्रा.पं.': 'ग्रामपंचायत',
    # Date / time
    'इ.स.पू.': 'ईसवी सनापूर्वी',
    'इ.स.': 'ईसवी सन',
    # Misc
    'इ.': 'इत्यादी',
    'व.': 'वगैरे',
    'नं.': 'नंबर',
    'पृ.': 'पृष्ठ',
    'क्र.': 'क्रमांक',
    'रु.': 'रुपये',
    'कि.मी.': 'किलोमीटर',
}

# =============================================================================
# Number-to-words conversion
# =============================================================================

def _digits_to_marathi(digits_str):
    """Convert a string of digit characters to individual Marathi words."""
    return ' '.join(MARATHI_DIGITS.get(d, d) for d in digits_str)


def number_to_marathi(num_str):
    """
    Convert an integer string to Marathi words.
    Follows the Indian numbering system: हजार, लाख, कोटी.
    """
    try:
        num = int(num_str)
    except ValueError:
        return num_str

    if num < 0:
        return 'उणे ' + number_to_marathi(str(-num))

    if num <= 100:
        return MARATHI_NUMBERS.get(num, num_str)

    if num < 1000:
        hundreds = num // 100
        remainder = num % 100
        result = MARATHI_HUNDREDS.get(hundreds, MARATHI_NUMBERS.get(hundreds, '') + 'शे')
        if remainder:
            result += ' ' + number_to_marathi(str(remainder))
        return result

    if num < 100_000:          # हजार
        thousands = num // 1000
        remainder = num % 1000
        result = ('एक हजार' if thousands == 1
                  else number_to_marathi(str(thousands)) + ' हजार')
        if remainder:
            result += ' ' + number_to_marathi(str(remainder))
        return result

    if num < 10_000_000:       # लाख
        lakhs = num // 100_000
        remainder = num % 100_000
        result = ('एक लाख' if lakhs == 1
                  else number_to_marathi(str(lakhs)) + ' लाख')
        if remainder:
            result += ' ' + number_to_marathi(str(remainder))
        return result

    if num < 10_000_000_000:   # कोटी
        crores = num // 10_000_000
        remainder = num % 10_000_000
        result = ('एक कोटी' if crores == 1
                  else number_to_marathi(str(crores)) + ' कोटी')
        if remainder:
            result += ' ' + number_to_marathi(str(remainder))
        return result

    # Very large: digit-by-digit
    return _digits_to_marathi(str(num))


def decimal_to_marathi(match):
    """
    Convert a decimal number match to Marathi.
    E.g. '3.14'  → 'तीन दशांश एक चार'
         '0.5'   → 'शून्य दशांश पाच'
    """
    integer_part = match.group(1)
    decimal_part  = match.group(2)
    left  = number_to_marathi(integer_part)
    right = _digits_to_marathi(decimal_part)   # each digit read individually
    return left + ' दशांश ' + right


def ordinal_to_marathi(match):
    """
    Convert ordinal suffixes written after digits.
    Handles: 1ला, 2रा, 3रा, 4था, 5वा … or 1st/2nd style (ignored — Marathi only)
    Also handles feminine forms: 1ली, 2री etc.
    """
    num  = int(match.group(1))
    # suffix = match.group(2)  # e.g. 'ला', 'रा', 'ली', 'री', 'वा', 'था'
    if num in MARATHI_ORDINALS:
        return MARATHI_ORDINALS[num]
    # Fallback: number + वा
    return number_to_marathi(str(num)) + 'वा'


def date_to_marathi(match):
    """
    Convert DD/MM/YYYY or DD-MM-YYYY to spoken Marathi.
    E.g. 15/08/1947 → 'पंधरा ऑगस्ट एक हजार नऊशे सत्तेचाळीस'
    """
    day   = int(match.group(1))
    month = int(match.group(2))
    year  = match.group(3)
    day_str   = number_to_marathi(str(day))
    month_str = MARATHI_MONTHS.get(month, number_to_marathi(str(month)))
    year_str  = number_to_marathi(year)
    return f'{day_str} {month_str} {year_str}'


def time_to_marathi(match):
    """
    Convert HH:MM to spoken Marathi.
    E.g. '10:30' → 'दहा वाजून तीस मिनिटे'
         '9:00'  → 'नऊ वाजले'
    """
    hour   = int(match.group(1))
    minute = int(match.group(2))
    hour_str = number_to_marathi(str(hour))
    if minute == 0:
        return f'{hour_str} वाजले'
    minute_str = number_to_marathi(str(minute))
    return f'{hour_str} वाजून {minute_str} मिनिटे'


def percentage_to_marathi(match):
    """25%  →  पंचवीस टक्के"""
    return number_to_marathi(match.group(1)) + ' टक्के'


def currency_to_marathi(match):
    """
    ₹500  → पाचशे रुपये
    $100  → शंभर डॉलर
    €50   → पन्नास युरो
    """
    symbol  = match.group(1)
    amount  = match.group(2)
    # Handle decimal amounts  (₹1.50)
    if '.' in amount:
        parts = amount.split('.')
        word  = number_to_marathi(parts[0])
    else:
        word = number_to_marathi(amount)
    currency_map = {'₹': 'रुपये', '$': 'डॉलर', '€': 'युरो', '£': 'पाउंड'}
    return word + ' ' + currency_map.get(symbol, '')


# =============================================================================
# Main normalisation pipeline
# =============================================================================

def normalize_text(text):
    """
    Full Marathi text normalisation pipeline (v2).

    Order matters — each step assumes the previous one has run:
      1. Abbreviation expansion
      2. Date patterns   (before plain number replacement)
      3. Time patterns   (before plain number replacement)
      4. Currency        (before plain number replacement)
      5. Percentage      (before plain number replacement)
      6. Ordinals        (before plain number replacement)
      7. Decimal numbers (before plain integer replacement)
      8. Plain integers
      9. Character filtering (keep only Devanagari + punctuation)
     10. Whitespace normalisation
    """
    # Step 1 — Abbreviations (longest-first to avoid partial matches)
    for abbr, expansion in sorted(ABBREVIATIONS.items(), key=lambda x: -len(x[0])):
        text = text.replace(abbr, expansion)

    # Step 2 — Dates: DD/MM/YYYY or DD-MM-YYYY
    text = re.sub(
        r'\b(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})\b',
        date_to_marathi, text
    )

    # Step 3 — Time: H:MM or HH:MM  (must come before plain integers)
    text = re.sub(
        r'\b(\d{1,2}):(\d{2})\b',
        time_to_marathi, text
    )

    # Step 4 — Currency: ₹/$/€/£ followed by digits (optional decimal)
    text = re.sub(
        r'([₹$€£])(\d+(?:\.\d{1,2})?)',
        currency_to_marathi, text
    )

    # Step 5 — Percentage: digits followed by %
    text = re.sub(
        r'(\d+)\s*%',
        percentage_to_marathi, text
    )

    # Step 6 — Ordinals: digits followed by Marathi ordinal suffix letters
    # Matches: 1ला, 2रा, 3री, 4था, 5वा, etc.
    text = re.sub(
        r'(\d+)(ला|ली|रा|री|था|थी|वा|वी|वे)',
        ordinal_to_marathi, text
    )

    # Step 7 — Decimal numbers: integer.fractional
    text = re.sub(
        r'\b(\d+)\.(\d+)\b',
        decimal_to_marathi, text
    )

    # Step 8 — Plain integers
    text = re.sub(r'\d+', lambda m: number_to_marathi(m.group()), text)

    # Step 9 — Remove unwanted characters
    # Keep: Devanagari block, whitespace, Devanagari danda (।), basic punctuation
    text = re.sub(r'[^\u0900-\u097F\s।,!?.\-:;]', '', text)

    # Step 10 — Normalise whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # Step 11 — Clean punctuation spacing
    text = re.sub(r'\s+([।,!?;:])', r'\1', text)

    return text


# =============================================================================
# Self-test
# =============================================================================

if __name__ == '__main__':
    tests = [
        # Original v1 tests
        ("आज तापमान 25 अंश आहे.",              "Basic number 25"),
        ("डॉ. पाटील यांनी 100 रुपये दिले",      "Abbreviation + 100"),
        ("इ.स. 2024 मध्ये",                     "Year 2024"),
        ("म. राज्यात 50 लाख लोक",              "Short abbreviation"),
        ("21 जानेवारी 2025",                    "21 + year"),
        ("42 वे वर्ष",                          "Compound number 42"),
        ("999 लोक आले",                         "Hundreds"),
        ("10000 रुपये",                          "Ten thousand"),
        ("150000 लोक",                           "1.5 lakh"),
        ("0 ते 100",                             "Zero to hundred"),
        # New v2 tests
        ("किंमत 3.14 रुपये आहे",                "Decimal 3.14"),
        ("तो 1ला आला",                           "Ordinal 1ला"),
        ("आज 4था दिवस आहे",                     "Ordinal 4था"),
        ("स्वातंत्र्य दिन 15/08/1947",           "Date DD/MM/YYYY"),
        ("सकाळी 10:30 वाजता",                   "Time 10:30"),
        ("₹500 खर्च केले",                      "Currency ₹"),
        ("मतदान 68% झाले",                      "Percentage"),
        ("श्रीम. देशपांडे आल्या",               "New abbreviation श्रीम."),
        ("कि.मी. 12 अंतर",                       "Abbreviation कि.मी."),
        ("$50 डॉलर दिले",                        "Currency $"),
    ]

    print("=== Marathi Text Normalizer v2 Tests ===\n")
    for text, label in tests:
        result = normalize_text(text)
        print(f"[{label}]")
        print(f"  IN : {text}")
        print(f"  OUT: {result}")
        print()

    print("=== Number Verification ===\n")
    checks = [
        (21, 'एकवीस'), (25, 'पंचवीस'), (42, 'बेचाळीस'),
        (99, 'नव्व्याण्णव'), (100, 'शंभर'), (1000, 'एक हजार'),
        (2024, 'दोन हजार चोवीस'), (100000, 'एक लाख'),
    ]
    for num, expected in checks:
        got = number_to_marathi(str(num))
        status = "✓" if got == expected else "✗"
        print(f"  {status} {num:>8} -> {got:35s} (expected: {expected})")
