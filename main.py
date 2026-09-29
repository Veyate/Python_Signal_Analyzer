import customtkinter as ctk
from app.ui.main_window import MainWindow
from app.utils.settings_manager import settings

def main():
    settings.apply_ui_settings()
    app = MainWindow()
    app.mainloop()

if __name__ == "__main__":
    main()
