# settings.py
import os
import json


class SettingsManager:
    """Gestionnaire de préférences utilisateur enregistrées dans user_settings.json."""

    SETTINGS_FILE = "user_settings.json"

    DEFAULT_SETTINGS = {
        "theme": "dark",
        "font_family": "Segoe UI",
        "font_size": 10,
        "language": "fr",
        "window_geometry": "",
        "dock_state": "",
        "recent_projects": [],
        "last_open_dir": ""
    }

    @classmethod
    def get_settings_path(cls):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), cls.SETTINGS_FILE)

    @classmethod
    def load_settings(cls) -> dict:
        path = cls.get_settings_path()
        settings = dict(cls.DEFAULT_SETTINGS)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    settings.update(data)
            except Exception as e:
                print(f"Erreur lors de la lecture de user_settings.json: {e}")
        return settings

    @classmethod
    def save_settings(cls, settings_dict: dict):
        path = cls.get_settings_path()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(settings_dict, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de user_settings.json: {e}")
