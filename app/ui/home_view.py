import customtkinter as ctk
from app.ui.builder_view import BuilderView
from assets.styles import COLORS, FONTS, PADDING

class HomeView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.configure(fg_color=COLORS["bg"])

        # Contenedor central (Card) para agrupar el contenido
        self.menu_card = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=12)
        self.menu_card.pack(expand=True, padx=PADDING["xl"], pady=PADDING["xl"])

        # ==========================
        # TITULO Y SUBTITULO
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
        # BOTONES DE SELECCIÓN
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
                width=280,
                height=45,
                font=FONTS["body_bold"],
                fg_color=COLORS["secondary"],
                hover_color=COLORS["secondary_hover"],
                text_color=COLORS["bg"],  # Contraste oscuro en botón claro
                corner_radius=8,
                command=lambda m=method_key: self.open_builder(m)
            )
            btn.pack(pady=PADDING["sm"])
            
        # Espacio estético inferior
        ctk.CTkLabel(self.menu_card, text="", height=10).pack()

    def open_builder(self, method):
        self.pack_forget()
        builder = BuilderView(self.master, method)
        builder.pack(fill="both", expand=True)