"""
Utility functions for the Layla Conversation Analyzer
"""
import re
import pandas as pd
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

def categorize_opening_message(message):
    """
    Categorize conversation opening messages into predefined categories.
    
    Categories:
    1. Fragrance Help - Help finding perfumes
    2. Skincare Routine - Creating skincare routines  
    3. Product Summarization - Summarizing product details
    4. Others - All other conversation openings
    
    Args:
        message (str): The opening message of a conversation
        
    Returns:
        str: Category name
    """
    if not message or pd.isna(message):
        return "Others"
    
    # Clean the message for comparison
    clean_message = str(message).strip().lower()
    
    # Define categorization patterns (English and Arabic)
    fragrance_patterns = [
        # English patterns
        r"can you help me find the perfect fragrance",
        r"help me find.*fragrance",
        r"help me find.*perfume", 
        r"find.*perfect fragrance",
        r"find.*perfect perfume",
        # Arabic patterns  
        r"هل يمكنك مساعدتي في العثور على العطر المثالي",
        r"مساعدتي.*العطر",
        r"العثور على.*العطر",
        r"ترشيح.*عطر",
        r"اختيار.*عطر",  
        r"برفيوم", 
        r"عطر ثابت", 
        r"اختيار عطر",
    ]
    
    skincare_patterns = [
        # English patterns
        r"define a 7-step skincare routine",
        r"define.*skincare routine",
        r"7-step skincare routine",
        r"skincare routine.*7.*step",
        r"create.*skincare routine",
        r"routine.*skin",
        # Arabic patterns
        r"حدد روتينًا مكونًا من 7 خطوات للعناية بالبشرة",
        r"حدد روتين.*للعناية بالبشرة.*7.*خطوات",
        r"حدد.*روتين.*العناية بالبشرة",
        r"روتين.*العناية بالبشرة.*7.*خطوات",
        r"روتين.*بشرة",
        r"العناية بالبشرة.*روتين",
        r"روتين بشرة", 
        r"نصائح بشرة"
    ]
    
    summarization_patterns = [
        # English patterns
        r"summarize the product details",
        r"summarize.*product.*details",
        r"summarize.*key details.*product",
        r"summarize.*following product",
        r"summarize.*product.*using.*name.*description",
        r"summarize.*key details.*following product",
        r"product details.*name and description",
        r"write.*customer questions.*answers",
        r"product.*name.*description.*questions",
        r"key details.*product.*name.*description",
        r"details.*product.*provided name",
        r"details.*following product.*name.*description",
        r"customer questions",
        # Arabic patterns
        r"اذكر تفاصيل المنتج التالي",
        r"تفاصيل المنتج.*الاسم والوصف", 
        r"أنشئ.*أسئلة.*للعملاء",
        r"المنتج.*الاسم.*الوصف.*أسئلة",
        r"تفاصيل.*المنتج.*المُقدّمين",
        r"لخص.*تفاصيل.*المنتج",
        r"تفاصيل.*المنتج التالي.*الاسم.*الوصف",
        r"معلومات المنتج.*اسم.*وصف",
        r"كتابة.*أسئلة.*عن المنتج",
        r"اعطني تفاصيل المنتج", 
        r"معلومات عن المنتج"
    ]
    
    # Check each category
    for pattern in fragrance_patterns:
        if re.search(pattern, clean_message, re.IGNORECASE):
            return "Fragrance Help"
            
    for pattern in skincare_patterns:
        if re.search(pattern, clean_message, re.IGNORECASE):
            return "Skincare Routine"
            
    for pattern in summarization_patterns:
        if re.search(pattern, clean_message, re.IGNORECASE):
            return "Product Summarization"
    
    return "Others"
