"""
Marathi Text Normalizer for TTS
Handles: numbers, dates, abbreviations, common English words in Marathi text

FIXED: Complete Marathi number lookup for 1-100 (each has a unique compound word)
FIXED: Proper हजार/लाख/कोटी handling for numbers 1000+
FIXED: Abbreviation expansion order (longest first)
NOTE: num2words does NOT support Marathi — a manual lookup is required.
"""
import re

# =============================================================================
# Marathi Number System — Complete lookup for 0-100
# Marathi has UNIQUE compound words for every number; simple tens+ones doesn't work.
# =============================================================================
MARATHI_NUMBERS = {
    0: 'शून्य',
    1: 'एक', 2: 'दोन', 3: 'तीन', 4: 'चार', 5: 'पाच',
    6: 'सहा', 7: 'सात', 8: 'आठ', 9: 'नऊ', 10: 'दहा',
    11: 'अकरा', 12: 'बारा', 13: 'तेरा', 14: 'चौदा', 15: 'पंधरा',
    16: 'सोळा', 17: 'सतरा', 18: 'अठरा', 19: 'एकोणीस', 20: 'वीस',
    21: 'एकवीस', 22: 'बावीस', 23: 'तेवीस', 24: 'चोवीस', 25: 'पंचवीस',
    26: 'सव्वीस', 27: 'सत्तावीस', 28: 'अठ्ठावीस', 29: 'एकोणतीस', 30: 'तीस',
    31: 'एकतीस', 32: 'बत्तीस', 33: 'तेहेतीस', 34: 'चौतीस', 35: 'पस्तीस',
    36: 'छत्तीस', 37: 'सदतीस', 38: 'अडतीस', 39: 'एकोणचाळीस', 40: 'चाळीस',
    41: 'एक्केचाळीस', 42: 'बेचाळीस', 43: 'त्रेचाळीस', 44: 'चव्वेचाळीस', 45: 'पंचेचाळीस',
    46: 'सेहेचाळीस', 47: 'सत्तेचाळीस', 48: 'अठ्ठेचाळीस', 49: 'एकोणपन्नास', 50: 'पन्नास',
    51: 'एक्कावन्न', 52: 'बावन्न', 53: 'त्रेपन्न', 54: 'चौपन्न', 55: 'पंचावन्न',
    56: 'छप्पन्न', 57: 'सत्तावन्न', 58: 'अठ्ठावन्न', 59: 'एकोणसाठ', 60: 'साठ',
    61: 'एकसष्ट', 62: 'बासष्ट', 63: 'त्रेसष्ट', 64: 'चौसष्ट', 65: 'पासष्ट',
    66: 'सहासष्ट', 67: 'सदुसष्ट', 68: 'अडुसष्ट', 69: 'एकोणसत्तर', 70: 'सत्तर',
    71: 'एकाहत्तर', 72: 'बाहत्तर', 73: 'त्र्याहत्तर', 74: 'चौऱ्याहत्तर', 75: 'पंच्याहत्तर',
    76: 'शहात्तर', 77: 'सत्याहत्तर', 78: 'अठ्ठ्याहत्तर', 79: 'एकोणऐंशी', 80: 'ऐंशी',
    81: 'एक्क्याऐंशी', 82: 'ब्याऐंशी', 83: 'त्र्याऐंशी', 84: 'चौऱ्याऐंशी', 85: 'पंच्याऐंशी',
    86: 'शहाऐंशी', 87: 'सत्त्याऐंशी', 88: 'अठ्ठ्याऐंशी', 89: 'एकोणनव्वद', 90: 'नव्वद',
    91: 'एक्क्याण्णव', 92: 'ब्याण्णव', 93: 'त्र्याण्णव', 94: 'चौऱ्याण्णव', 95: 'पंच्याण्णव',
    96: 'शहाण्णव', 97: 'सत्त्याण्णव', 98: 'अठ्ठ्याण्णव', 99: 'नव्व्याण्णव', 100: 'शंभर',
}

# Hundreds: 200-900
MARATHI_HUNDREDS = {
    1: 'शंभर', 2: 'दोनशे', 3: 'तीनशे', 4: 'चारशे', 5: 'पाचशे',
    6: 'सहाशे', 7: 'सातशे', 8: 'आठशे', 9: 'नऊशे',
}

# Common abbreviations in Marathi text
ABBREVIATIONS = {
    'अ.भा.': 'अखिल भारतीय',
    'इ.स.': 'ईसवी सन',
    'डॉ.': 'डॉक्टर',
    'श्री.': 'श्रीमान',
    'श्रीम.': 'श्रीमती',
    'सौ.': 'सौभाग्यवती',
    'कु.': 'कुमारी',
    'प्रा.': 'प्राध्यापक',
    'म.': 'महाराष्ट्र',
    'वि.': 'विद्यापीठ',
}


def number_to_marathi(num_str):
    """
    Convert a number string to Marathi words.
    Uses a complete lookup table for 0-100 and recursive decomposition for larger numbers.
    Follows the Indian numbering system: हजार (1,000), लाख (1,00,000), कोटी (1,00,00,000).
    """
    try:
        num = int(num_str)
    except ValueError:
        return num_str

    if num < 0:
        return 'उणे ' + number_to_marathi(str(-num))

    # Direct lookup: 0-100
    if num <= 100:
        return MARATHI_NUMBERS.get(num, num_str)

    # 101-999
    if num < 1000:
        hundreds = num // 100
        remainder = num % 100
        result = MARATHI_HUNDREDS.get(hundreds, MARATHI_NUMBERS.get(hundreds, '') + 'शे')
        if remainder:
            result += ' ' + number_to_marathi(str(remainder))
        return result

    # 1,000 - 99,999 (हजार)
    if num < 100000:
        thousands = num // 1000
        remainder = num % 1000
        if thousands == 1:
            result = 'एक हजार'
        else:
            result = number_to_marathi(str(thousands)) + ' हजार'
        if remainder:
            result += ' ' + number_to_marathi(str(remainder))
        return result

    # 1,00,000 - 99,99,999 (लाख)
    if num < 10000000:
        lakhs = num // 100000
        remainder = num % 100000
        if lakhs == 1:
            result = 'एक लाख'
        else:
            result = number_to_marathi(str(lakhs)) + ' लाख'
        if remainder:
            result += ' ' + number_to_marathi(str(remainder))
        return result

    # 1,00,00,000+ (कोटी)
    if num < 10000000000:
        crores = num // 10000000
        remainder = num % 10000000
        if crores == 1:
            result = 'एक कोटी'
        else:
            result = number_to_marathi(str(crores)) + ' कोटी'
        if remainder:
            result += ' ' + number_to_marathi(str(remainder))
        return result

    # Very large numbers: spell digit by digit
    return ' '.join(MARATHI_NUMBERS.get(int(d), d) for d in str(num))


def normalize_text(text):
    """Full Marathi text normalization pipeline."""

    # Step 1: Expand abbreviations (longest first to avoid partial matches)
    for abbr, expansion in sorted(ABBREVIATIONS.items(), key=lambda x: -len(x[0])):
        text = text.replace(abbr, expansion)

    # Step 2: Convert numbers to words
    text = re.sub(r'\d+', lambda m: number_to_marathi(m.group()), text)

    # Step 3: Remove unwanted characters
    # Keep Devanagari, spaces, and basic punctuation
    text = re.sub(r'[^\u0900-\u097F\s।,!?.\-:;]', '', text)

    # Step 4: Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # Step 5: Clean punctuation spacing
    text = re.sub(r'\s+([।,!?;:])', r'\1', text)

    return text


if __name__ == "__main__":
    tests = [
        ("आज तापमान 25 अंश आहे.", "Basic compound number"),
        ("डॉ. पाटील यांनी 100 रुपये दिले", "Abbreviation + 100"),
        ("इ.स. 2024 मध्ये", "Year 2024"),
        ("म. राज्यात 50 लाख लोक", "Short abbreviation"),
        ("21 जानेवारी 2025", "21 + year"),
        ("42 वे वर्ष", "Compound number 42"),
        ("999 लोक आले", "Hundreds"),
        ("10000 रुपये", "Ten thousand"),
        ("150000 लोक", "1.5 lakh"),
        ("0 ते 100", "Zero to hundred"),
    ]

    print("=== Marathi Text Normalizer Tests ===\n")
    for text, label in tests:
        result = normalize_text(text)
        print(f"[{label}]")
        print(f"  IN:  {text}")
        print(f"  OUT: {result}")
        print()

    # Verify specific compound numbers
    print("=== Number Verification ===\n")
    check = [
        (21, 'एकवीस'), (25, 'पंचवीस'), (42, 'बेचाळीस'),
        (99, 'नव्व्याण्णव'), (100, 'शंभर'), (1000, 'एक हजार'),
        (2024, 'दोन हजार चोवीस'), (100000, 'एक लाख'),
    ]
    for num, expected in check:
        got = number_to_marathi(str(num))
        status = "✓" if got == expected else "✗"
        print(f"  {status} {num:>8} -> {got:30s} (expected: {expected})")
