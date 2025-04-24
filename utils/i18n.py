# utils/i18n.py
import os
import json
from flask import request, g

SUPPORTED_LANGS = ['zh-TW', 'ja', 'en']
DEFAULT_LANG = 'en'
LOCALE_DIR = os.path.join(os.path.dirname(__file__), '../lang')

def get_locale():
    if hasattr(g, 'lang'):
        return g.lang
    # 自 Accept-Language 偵測使用語系
    accept_langs = request.accept_languages.values()
    for lang in accept_langs:
        lang = lang.lower()
        if 'zh-tw' in lang:
            g.lang = 'zh-TW'
            break
        elif 'ja' in lang:
            g.lang = 'ja'
            break
        elif 'en' in lang:
            g.lang = 'en'
            break
    else:
        g.lang = DEFAULT_LANG
    return g.lang

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
