"""
Point d'entrée principal.
"""
import customtkinter as ctk
import config
from app.utils.settings_manager import settings
from app.utils.i18n import i18n
from app.ui.main_window import MainWindow

def main():
    settings.apply_ui_settings()
    i18n.load_language(settings.settings["language"])

    app = MainWindow()
    app.mainloop()

if __name__ == "__main__":
    main()
