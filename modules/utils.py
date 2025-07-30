"""
Utility functions for the Layla Conversation Analyzer
"""
import re
from deep_translator import GoogleTranslator

def is_arabic(text):
    """Simple check for Arabic characters"""
    return bool(re.search(r'[\u0600-\u06FF]', str(text)))

def translate_text(text):
    """Translate text to English using GoogleTranslator"""
    try:
        return GoogleTranslator(source='auto', target='en').translate(text)
    except Exception:
        return "[Translation failed]"
