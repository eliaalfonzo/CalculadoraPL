import customtkinter as ctk
from app.ui.builder_view import BuilderView


class HomeView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)

        self.master = master
        self.configure(fg_color="#0f172a")

        # ---------------- TITULO ----------------
        title = ctk.CTkLabel(
            self,
            text="Calculadora de Programación Lineal",
            font=("Arial", 24, "bold"),
            text_color="white"
        )
        title.pack(pady=40)

        subtitle = ctk.CTkLabel(
            self,
            text="Selecciona el método que deseas usar",
            font=("Arial", 16),
            text_color="#94a3b8"
        )
        subtitle.pack(pady=10)

        # ---------------- BOTONES ----------------
        btn1 = ctk.CTkButton(
            self,
            text="Método Gráfico",
            width=250,
            command=self.open_builder
        )
        btn1.pack(pady=10)

        btn2 = ctk.CTkButton(
            self,
            text="Método Simplex",
            width=250,
            command=self.open_builder
        )
        btn2.pack(pady=10)

        btn3 = ctk.CTkButton(
            self,
            text="Método Dos Fases",
            width=250,
            command=self.open_builder
        )
        btn3.pack(pady=10)

    # ---------------- CAMBIO DE PANTALLA ----------------
    def open_builder(self):
        self.pack_forget()
        builder = BuilderView(self.master)
        builder.pack(fill="both", expand=True)