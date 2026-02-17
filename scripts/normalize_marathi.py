import re
try:
    from num2words import num2words
except ImportError:
    num2words = None

def normalize_text(text):
    """
    Basic normalization for Marathi text.
    1. Expand numbers to words (if num2words is available and supports 'mr' or 'hi' as fallback).
    2. Remove extensive punctuation if needed, but keeping basic punctuation is good for TTS prosody.
    3. Collapse whitespace.
    """
    
    # 1. Expand numbers
    # Regex to find numbers
    text = re.sub(r'\d+', lambda m: expand_number(m.group(0)), text)
    
    # 2. Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def expand_number(num_str):
    if num2words:
        try:
            # Try Marathi
            return num2words(int(num_str), lang='mr')
        except NotImplementedError:
             try:
                # Fallback to Hindi (often similar for numbers 0-9, but grammar differs)
                # Or just return mapped digits if simple
                return num2words(int(num_str), lang='hi')
             except:
                return num_str
    return num_str

if __name__ == "__main__":
    # Test
    sample = "आज तापमान 25 अंश आहे."
    print("Original:", sample)
    print("Normalized:", normalize_text(sample))
