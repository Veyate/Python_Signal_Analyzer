import customtkinter as ctk

class StatusBarFrame(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, height=25, corner_radius=0, **kwargs)
        self.lbl_status = ctk.CTkLabel(self, text="Prêt", anchor="w", font=ctk.CTkFont(size=11))
        self.lbl_status.pack(side="left", padx=10, pady=2)

    def set_message(self, message):
        self.lbl_status.configure(text=message)
