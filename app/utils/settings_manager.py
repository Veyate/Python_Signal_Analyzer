"""
Gestionnaire des préférences utilisateur.
"""
import json
import os
import customtkinter as ctk

SETTINGS_FILE = "user_settings.json"

DEFAULT_SETTINGS = {
    "language": "fr",
    "appearance_mode": "Dark",
    "color_theme": "blue",
    "ui_scaling": 1.0,
    "panel_explorer_width": 180,
    "panel_properties_width": 230
}

class SettingsManager:
    def __init__(self):
        self.settings = DEFAULT_SETTINGS.copy()
        self.load_settings()

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    self.settings.update(json.load(f))
            except Exception:
                pass

    def save_settings(self):
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, indent=4)

    def apply_ui_settings(self):
        ctk.set_appearance_mode(self.settings.get("appearance_mode", "Dark"))
        ctk.set_default_color_theme(self.settings.get("color_theme", "blue"))
        ctk.set_widget_scaling(self.settings.get("ui_scaling", 1.0))
        ctk.set_window_scaling(self.settings.get("ui_scaling", 1.0))

settings = SettingsManager()
