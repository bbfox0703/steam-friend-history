# utils/i18n.py
import os
import json
from flask import request, g

SUPPORTED_LANGS = ['zh-TW', 'ja', 'en']
DEFAULT_LANG = 'en'
LOCALE_DIR = os.path.join(os.path.dirname(__file__), '../lang')

def get_locale():
    # 每次重新評估，不使用 g.lang 快取（避免卡住）
    # 因為在同一個 request 中語言設定可能會改變

    # 優先檢查 Cookie 中的語言設定
    lang_override = request.cookies.get('lang_override')
    if lang_override and lang_override in SUPPORTED_LANGS:
        g.lang = lang_override
        return lang_override

    # 自 Accept-Language 偵測使用語系
    accept_langs = request.accept_languages.values()
    for lang in accept_langs:
        lang = lang.lower()
        if 'zh-tw' in lang or 'zh' in lang:
            detected_lang = 'zh-TW'
            g.lang = detected_lang
            return detected_lang
        elif 'ja' in lang:
            detected_lang = 'ja'
            g.lang = detected_lang
            return detected_lang
        elif 'en' in lang:
            detected_lang = 'en'
            g.lang = detected_lang
            return detected_lang

    # 預設語言
    g.lang = DEFAULT_LANG
    return DEFAULT_LANG

TRANSLATIONS = {}

def load_translations():
    for lang in SUPPORTED_LANGS:
        path = os.path.join(LOCALE_DIR, f'{lang}.json')
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                TRANSLATIONS[lang] = json.load(f)

def _(text):
    lang = get_locale()
    return TRANSLATIONS.get(lang, {}).get(text, text)

# 初始化時預載語言包
load_translations()
