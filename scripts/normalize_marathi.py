"""
Marathi Text Normalizer for TTS
Handles: numbers, dates, abbreviations, common English words in Marathi text
"""
import re

# Marathi number words
MARATHI_DIGITS = {
    '0': 'शून्य', '1': 'एक', '2': 'दोन', '3': 'तीन', '4': 'चार',
    '5': 'पाच', '6': 'सहा', '7': 'सात', '8': 'आठ', '9': 'नऊ'
}

MARATHI_TEENS = {
    '10': 'दहा', '11': 'अकरा', '12': 'बारा', '13': 'तेरा', '14': 'चौदा',
    '15': 'पंधरा', '16': 'सोळा', '17': 'सतरा', '18': 'अठरा', '19': 'एकोणीस'
}

MARATHI_TENS = {
    '20': 'वीस', '30': 'तीस', '40': 'चाळीस', '50': 'पन्नास',
    '60': 'साठ', '70': 'सत्तर', '80': 'ऐंशी', '90': 'नव्वद'
}

MARATHI_POWERS = {
    100: 'शंभर', 1000: 'हजार', 100000: 'लाख', 10000000: 'कोटी'
}

# Common abbreviations in Marathi text
ABBREVIATIONS = {
    'डॉ.': 'डॉक्टर',
    'श्री.': 'श्रीमान',
    'सौ.': 'सौभाग्यवती',
    'कु.': 'कुमारी',
    'प्रा.': 'प्राध्यापक',
    'अ.भा.': 'अखिल भारतीय',
    'इ.स.': 'ईसवी सन',
    'म.': 'महाराष्ट्र',
}

def number_to_marathi(num_str):
    """Convert a number string to Marathi words (basic implementation)."""
    try:
        num = int(num_str)
    except ValueError:
        return num_str

    if num == 0:
        return 'शून्य'
    if num < 0:
        return 'उणे ' + number_to_marathi(str(-num))
    if num < 10:
        return MARATHI_DIGITS[str(num)]
    if num < 20:
        return MARATHI_TEENS.get(str(num), num_str)
    if num < 100:
        tens = (num // 10) * 10
        ones = num % 10
        result = MARATHI_TENS.get(str(tens), '')
        if ones:
            result += ' ' + MARATHI_DIGITS[str(ones)]
        return result
    if num < 1000:
        hundreds = num // 100
        remainder = num % 100
        if hundreds == 1:
            result = 'शंभर'
        else:
            result = MARATHI_DIGITS[str(hundreds)] + 'शे'
        if remainder:
            result += ' ' + number_to_marathi(str(remainder))
        return result

    # For larger numbers, spell out digit by digit
    return ' '.join(MARATHI_DIGITS.get(d, d) for d in num_str)


def normalize_text(text):
    """Full Marathi text normalization pipeline."""

    # Step 1: Expand abbreviations
    for abbr, expansion in ABBREVIATIONS.items():
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
    # Test
    sample = "आज तापमान 25 अंश आहे."
    print("Original:", sample)
    print("Normalized:", normalize_text(sample))
