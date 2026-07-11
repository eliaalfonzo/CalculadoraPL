import customtkinter as ctk
from tkinter import messagebox  # Para lanzar alertas visuales limpias sin romper la app

from app.components.constraint_row import ConstraintRow
from app.core.model import LinearProgram, ObjectiveFunction, Constraint
from app.core.simplex import SimplexSolver
from app.core.graphical import GraphicalSolver
# Importamos tu nuevo solver matemático del método de las dos fases
from app.core.metodosfases import TwoPhaseSolver
from app.utils.validators import clean_inputs
from app.ui.results_view import ResultsView

from assets.styles import COLORS, FONTS, PADDING

class BuilderView(ctk.CTkFrame):
    def __init__(self, master, method):
        super().__init__(master)
        self.master = master
        self.method = method
        self.configure(fg_color=COLORS["bg"])

        self.constraints = []
        self.variables = 0

        # ==========================
        # HEADER DE LA PANTALLA
        # ==========================
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(pady=(PADDING["lg"], PADDING["md"]), fill="x")

        ctk.CTkLabel(
            header_frame,
            text="Construcción del Modelo",
            font=FONTS["title"],
            text_color=COLORS["text"]
        ).pack()

        method_names = {
            "simplex": "Método Simplex",
            "graphical": "Método Gráfico",
            "two_phase": "Método Dos Fases"
        }

        ctk.CTkLabel(
            header_frame,
            text=f"Configuración activa: {method_names.get(method, method)}",
            text_color=COLORS["secondary"],
            font=FONTS["subtitle"]
        ).pack(pady=(5, 0))

        # ==========================
        # PANEL CONFIGURACIÓN INICIAL (Card)
        # ==========================
        self.config_card = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=12)
        self.config_card.pack(pady=PADDING["md"], padx=PADDING["xl"], fill="x")

        controls_inner = ctk.CTkFrame(self.config_card, fg_color="transparent")
        controls_inner.pack(pady=PADDING["md"], padx=PADDING["md"])

        # Optimizacion Dropdown
        opt_label = ctk.CTkLabel(controls_inner, text="Optimizar:", font=FONTS["body_bold"], text_color=COLORS["text"])
        opt_label.pack(side="left", padx=PADDING["sm"])
        
        self.optimization_type = ctk.CTkOptionMenu(
            controls_inner,
            values=["max", "min"],
            font=FONTS["body"],
            width=90,
            fg_color=COLORS["border"],
            button_color=COLORS["border"],
            button_hover_color=COLORS["muted"],
            dropdown_fg_color=COLORS["card"],
            dropdown_text_color=COLORS["text"]
        )
        self.optimization_type.set("max")
        self.optimization_type.pack(side="left", padx=PADDING["md"])

        # Variables Input
        var_label = ctk.CTkLabel(controls_inner, text="Variables:", font=FONTS["body_bold"], text_color=COLORS["text"])
        var_label.pack(side="left", padx=PADDING["sm"])

        self.var_entry = ctk.CTkEntry(
            controls_inner,
            placeholder_text="Ej: 2 o 3",
            width=100,
            font=FONTS["body"],
            fg_color=COLORS["bg"],
            border_color=COLORS["border"]
        )
        self.var_entry.pack(side="left", padx=PADDING["sm"])

        # Botón Generar Estructura
        gen_btn = ctk.CTkButton(
            controls_inner,
            text="Inicializar Matriz",
            font=FONTS["body_bold"],
            fg_color=COLORS["secondary"],
            hover_color=COLORS["secondary_hover"],
            text_color=COLORS["bg"],
            command=self.generate_structure
        )
        gen_btn.pack(side="left", padx=PADDING["md"])

        # ==========================
        # CONTENEDOR DINÁMICO (Scrollable)
        # ==========================
        self.container = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg"], label_text="Estructura del Modelo Matemático", label_font=FONTS["section"], label_text_color=COLORS["muted"])
        self.container.pack(pady=PADDING["md"], padx=PADDING["xl"], fill="both", expand=True)

        # Panel de Acciones Inferiores
        self.actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.actions_frame.pack(pady=PADDING["lg"])

        self.add_btn = ctk.CTkButton(
            self.actions_frame,
            text="+ Agregar restricción",
            font=FONTS["body_bold"],
            fg_color=COLORS["card"],
            border_color=COLORS["border"],
            border_width=1,
            text_color=COLORS["text"],
            command=self.add_constraint
        )

        self.solve_btn = ctk.CTkButton(
            self.actions_frame,
            text="Resolver Modelo →",
            font=FONTS["body_bold"],
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            text_color=COLORS["bg"],
            command=self.solve
        )

    def generate_structure(self):
        if not self.var_entry.get().isdigit():
            messagebox.showwarning("Atención", "Por favor, ingresa un número entero válido de variables.")
            return

        self.variables = int(self.var_entry.get())

        for widget in self.container.winfo_children():
            widget.destroy()

        self.constraints.clear()

        # ==========================
        # DISEÑO DINÁMICO DE FUNCIÓN OBJETIVO
        # ==========================
        obj_card = ctk.CTkFrame(self.container, fg_color=COLORS["card"], corner_radius=8)
        obj_card.pack(pady=PADDING["sm"], fill="x", padx=PADDING["sm"])

        ctk.CTkLabel(
            obj_card,
            text="Función Objetivo Max/Min Z:",
            font=FONTS["body_bold"],
            text_color=COLORS["secondary"]
        ).pack(anchor="w", padx=PADDING["md"], pady=(PADDING["sm"], 0))

        obj_frame = ctk.CTkFrame(obj_card, fg_color="transparent")
        obj_frame.pack(pady=PADDING["md"], padx=PADDING["md"])

        ctk.CTkLabel(
            obj_frame,
            text="Z =",
            font=FONTS["section"],
            text_color=COLORS["text"]
        ).pack(side="left", padx=PADDING["xs"])

        self.obj_entries = []

        for i in range(self.variables):
            entry_frame = ctk.CTkFrame(obj_frame, fg_color="transparent")
            entry_frame.pack(side="left", padx=PADDING["xs"])

            entry = ctk.CTkEntry(
                entry_frame,
                width=65,
                font=FONTS["body"],
                fg_color=COLORS["bg"],
                border_color=COLORS["border"],
                justify="center"
            )
            entry.pack(side="left")
            self.obj_entries.append(entry)

            ctk.CTkLabel(
                entry_frame,
                text=f"x{i+1}",
                font=FONTS["body_bold"],
                text_color=COLORS["muted"]
            ).pack(side="left", padx=2)

            if i < self.variables - 1:
                ctk.CTkLabel(
                    obj_frame,
                    text="+",
                    font=FONTS["body_bold"],
                    text_color=COLORS["muted"]
                ).pack(side="left", padx=PADDING["xs"])

        # ==========================
        # CONDICIÓN DE NO NEGATIVIDAD
        # ==========================
        non_negative_card = ctk.CTkFrame(
            self.container,
            fg_color=COLORS["card"],
            corner_radius=8
        )
        non_negative_card.pack(
            pady=PADDING["sm"],
            fill="x",
            padx=PADDING["sm"]
        )

        ctk.CTkLabel(
            non_negative_card,
            text="Condición de no negatividad:",
            font=FONTS["body_bold"],
            text_color=COLORS["secondary"]
        ).pack(anchor="w", padx=PADDING["md"], pady=(PADDING["sm"], 0))

        variables_text = ", ".join(
            [f"X{i+1}" for i in range(self.variables)]
        )

        ctk.CTkLabel(
            non_negative_card,
            text=f"{variables_text} ≥ 0",
            font=FONTS["body"],
            text_color=COLORS["text"]
        ).pack(anchor="w", padx=PADDING["md"], pady=(0, PADDING["sm"]))

        self.add_btn.pack(side="left", padx=PADDING["sm"])
        self.solve_btn.pack(side="left", padx=PADDING["sm"])

    def add_constraint(self):
        if self.variables == 0:
            return
        row = ConstraintRow(self.container, self.variables)
        row.pack(pady=PADDING["xs"], fill="x", padx=PADDING["sm"])
        self.constraints.append(row)

    def solve(self):
        if not hasattr(self, "obj_entries"):
            messagebox.showwarning("Atención", "Genera primero la estructura inicializando la matriz.")
            return

        if len(self.constraints) == 0:
            messagebox.showwarning("Atención", "Debes agregar al menos una restricción al modelo.")
            return

        try:
            # Captura y limpieza de entradas
            objective = clean_inputs([e.get() for e in self.obj_entries])
            constraints_data = [c.get_data() for c in self.constraints]

            # Construcción segura de las restricciones del modelo
            parsed_constraints = []
            for idx, c in enumerate(constraints_data):
                # Validación manual preventiva por si se quedó un string/vacío en el RHS
                try:
                    rhs_val = float(c["rhs"])
                except ValueError:
                    raise ValueError(f"El valor del lado derecho (RHS) en la restricción {idx+1} debe ser un número numérico válido.")

                parsed_constraints.append(
                    Constraint(
                        coefficients=clean_inputs(c["coefficients"]),
                        sign=c["sign"],
                        value=rhs_val
                    )
                )

            model = LinearProgram(
                objective=ObjectiveFunction(
                    coefficients=objective,
                    mode=self.optimization_type.get()
                ),
                constraints=parsed_constraints,
                variables=self.variables
            )

            # ======================================
            # SELECCIÓN DEL MÉTODO
            # ======================================
            if self.method == "simplex":
                solver = SimplexSolver(model)
                result = solver.solve()
            elif self.method == "graphical":
                solver = GraphicalSolver(model)
                result = solver.solve()
            elif self.method == "two_phase":
                # Instanciamos tu solucionador matemático pasándole el modelo estructurado
                solver = TwoPhaseSolver(model)
                # Ejecutamos el algoritmo que retorna las iteraciones y el diccionario de respuestas
                result = solver.solve()
            else:
                raise Exception("Método no reconocido")

            # ======================================
            # CAMBIO A RESULTS VIEW
            # ======================================
            self.pack_forget()
            results_view = ResultsView(self.master, result)
            results_view.pack(fill="both", expand=True)

        except ValueError as ve:
            # Captura controlada de errores de formato o campos vacíos ('x', '', etc.)
            messagebox.showerror("Error en los datos", f"Entrada inválida:\n{str(ve)}\n\nAsegúrate de no usar letras o dejar celdas vacías.")
        except Exception as e:
            # Captura de cualquier fallo algorítmico inesperado del solver
            messagebox.showerror("Error al resolver", f"Ocurrió un problema inesperado:\n{str(e)}")
