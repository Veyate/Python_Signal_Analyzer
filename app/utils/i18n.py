"""
Moteur de traduction (i18n).
"""
import json
import os

class I18nManager:
    def __init__(self, default_lang="fr"):
        self.current_lang = default_lang
        self.translations = {}
        self.i18n_dir = os.path.join(os.path.dirname(__file__), "..", "i18n")
        self.load_language(default_lang)

    def load_language(self, lang_code):
        file_path = os.path.join(self.i18n_dir, f"{lang_code}.json")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                self.translations = json.load(f)
            self.current_lang = lang_code

    def get(self, key, *args):
        text = self.translations.get(key, key)
        if args:
            return text.format(*args)
        return text

i18n = I18nManager()
def _(key, *args):
    return i18n.get(key, *args)
