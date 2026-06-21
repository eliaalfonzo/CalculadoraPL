# app/components/constraint_row.py
import customtkinter as ctk
from assets.styles import COLORS, FONTS, PADDING

class ConstraintRow(ctk.CTkFrame):
    def __init__(self, master, variables):
        # Usamos el color de fondo de las tarjetas para que combine con el contenedor
        super().__init__(master, fg_color="transparent")

        self.entries = []

        # Contenedor interno para dar un sutil margen y alineación limpia
        inner_frame = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=8)
        inner_frame.pack(fill="x", padx=PADDING["xs"], pady=PADDING["xs"])

        # Contenedor para la parte izquierda de la ecuación (coeficientes y variables)
        equation_frame = ctk.CTkFrame(inner_frame, fg_color="transparent")
        equation_frame.pack(side="left", padx=PADDING["md"], pady=PADDING["sm"])

        for i in range(variables):
            # Input para el coeficiente numérico
            entry = ctk.CTkEntry(
                equation_frame, 
                width=65,
                font=FONTS["body"],
                fg_color=COLORS["bg"],
                border_color=COLORS["border"],
                justify="center"
            )
            entry.pack(side="left", padx=PADDING["xs"])
            self.entries.append(entry)

            # Etiqueta de la variable (x1, x2, etc.) en Montserrat Bold
            ctk.CTkLabel(
                equation_frame,
                text=f"x{i+1}",
                font=FONTS["body_bold"],
                text_color=COLORS["muted"]
            ).pack(side="left", padx=2)

            # Signo "+" de separación entre variables
            if i < variables - 1:
                ctk.CTkLabel(
                    equation_frame, 
                    text="+", 
                    font=FONTS["body_bold"],
                    text_color=COLORS["muted"]
                ).pack(side="left", padx=PADDING["xs"])

        # Contenedor para el operador relacional y el lado derecho (RHS)
        right_side_frame = ctk.CTkFrame(inner_frame, fg_color="transparent")
        right_side_frame.pack(side="right", padx=PADDING["md"], pady=PADDING["sm"])

        # Selector de Signo (Estilizado con bordes suaves y fuente Montserrat)
        self.sign = ctk.CTkOptionMenu(
            right_side_frame, 
            values=["≤", "≥", "="],
            font=FONTS["body_bold"],
            width=75,
            height=30,
            fg_color=COLORS["border"],
            button_color=COLORS["border"],
            button_hover_color=COLORS["muted"],
            dropdown_fg_color=COLORS["card"],
            dropdown_text_color=COLORS["text"],
            dropdown_font=FONTS["body"]
        )
        self.sign.set("≤") # Valor inicial por defecto estético
        self.sign.pack(side="left", padx=PADDING["sm"])

        # Input para el Lado Derecho (RHS - Right Hand Side)
        self.rhs = ctk.CTkEntry(
            right_side_frame, 
            width=70,
            font=FONTS["body"],
            fg_color=COLORS["bg"],
            border_color=COLORS["border"],
            justify="center",
            placeholder_text="b"
        )
        self.rhs.pack(side="left", padx=PADDING["xs"])

    def get_data(self):
        # Mapeamos los caracteres matemáticos de vuelta a operadores estándar para tu backend si lo requiere
        sign_mapping = {
            "≤": "<=",
            "≥": ">=",
            "=": "="
        }
        
        return {
            "coefficients": [e.get() for e in self.entries],
            "sign": sign_mapping.get(self.sign.get(), self.sign.get()),
            "rhs": self.rhs.get()
        }