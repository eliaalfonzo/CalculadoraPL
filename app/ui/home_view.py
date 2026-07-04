import customtkinter as ctk 
from app.ui.builder_view import BuilderView
from assets.styles import COLORS, FONTS, PADDING

class HomeView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.configure(fg_color=COLORS["bg"])

        # Contenedor central (Card) con bordes más redondeados y limpios
        self.menu_card = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=20)
        self.menu_card.pack(expand=True, padx=PADDING["xl"], pady=(PADDING["xl"], 10))

        # ==========================
        # TÍTULO Y SUBTÍTULO
        # ==========================
        title = ctk.CTkLabel(
            self.menu_card,
            text="Calculadora de Programación Lineal",
            font=FONTS["title"],
            text_color=COLORS["text"]
        )
        title.pack(pady=(PADDING["xl"], PADDING["sm"]), padx=PADDING["xl"])

        subtitle = ctk.CTkLabel(
            self.menu_card,
            text="Selecciona el método matemático que deseas ejecutar",
            font=FONTS["subtitle"],
            text_color=COLORS["muted"]
        )
        subtitle.pack(pady=(0, PADDING["xl"]), padx=PADDING["xl"])

        # ==========================
        # BOTONES DE SELECCIÓN (Rediseñados)
        # ==========================
        methods = [
            ("Método Gráfico", "graphical"),
            ("Método Simplex", "simplex"),
            ("Método Dos Fases", "two_phase")
        ]

        for text, method_key in methods:
            btn = ctk.CTkButton(
                self.menu_card,
                text=text,
                width=320,         # Un poquito más ancho para mejor balance visual
                height=48,         # Más alto para que se vea premium
                font=FONTS["body_bold"],
                fg_color=COLORS["primary"],
                hover_color=COLORS["primary_hover"],
                text_color="#000000", # Texto blanco sobre el botón rosa pastel
                corner_radius=20,     # Bordes redondeados tipo píldora (muy aesthetic)
                cursor="hand2",       # Cambia el cursor al pasar por encima
                command=lambda m=method_key: self.open_builder(m)
            )
            btn.pack(pady=PADDING["sm"])
            
        # Espacio estético inferior dentro de la card
        ctk.CTkLabel(self.menu_card, text="", height=15).pack()

        # ==========================
        # FOOTER / CRÉDITOS (Integrantes)
        # ==========================
        credits_text = "Desarrollado por: Elia Alfonzo (C.I: 32.495.353)  •  Valeria García (C.I: 31.649.272)"
        
        footer = ctk.CTkLabel(
            self,
            text=credits_text,
            font=FONTS["footer"],
            text_color=COLORS["footer_text"]
        )
        footer.pack(side="bottom", pady=PADDING["md"])

    def open_builder(self, method):
        self.pack_forget()
        builder = BuilderView(self.master, method)
        builder.pack(fill="both", expand=True)