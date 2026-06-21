# main.py
import customtkinter as ctk
from app.ui.home_view import HomeView

# Configuración base de la app
ctk.set_appearance_mode("dark")  # dark / light
ctk.set_default_color_theme("green")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Programación Lineal App")
        
        # 1. Definimos las dimensiones deseadas de la ventana
        window_width = 1020
        window_height = 680

        # 2. Obtenemos el ancho y alto del monitor del usuario
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # 3. Calculamos la coordenada (X, Y) exacta para el centro de la pantalla
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)

        # 4. Establecemos el tamaño y la ubicación inicial centrada
        self.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        
        # 5. Habilitamos la expansión y maximización de la pantalla (Ancho=True, Alto=True)
        self.resizable(True, True)

        # Cargar pantalla principal
        self.home = HomeView(self)
        self.home.pack(fill="both", expand=True)


if __name__ == "__main__":
    app = App()
    app.mainloop()