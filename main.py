import customtkinter as ctk
from app.ui.home_view import HomeView

# Configuración base de la app
ctk.set_appearance_mode("dark")  # dark / light
ctk.set_default_color_theme("green")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Programación Lineal App")
        self.geometry("900x600")
        self.resizable(False, False)

        # Cargar pantalla principal
        self.home = HomeView(self)
        self.home.pack(fill="both", expand=True)


if __name__ == "__main__":
    app = App()
    app.mainloop()