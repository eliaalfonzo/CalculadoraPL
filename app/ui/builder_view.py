import customtkinter as ctk

from app.components.constraint_row import ConstraintRow
from app.core.model import LinearProgram, ObjectiveFunction, Constraint
from app.core.simplex import SimplexSolver
from app.utils.validators import clean_inputs
from app.ui.results_view import ResultsView


class BuilderView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)

        self.configure(fg_color="#0f172a")

        self.constraints = []
        self.variables = 0

        # ---------------- TITULO ----------------
        ctk.CTkLabel(
            self,
            text="Construcción del Modelo",
            font=("Arial", 22, "bold"),
            text_color="white"
        ).pack(pady=15)

        # ---------------- INPUT VARIABLES ----------------
        self.var_entry = ctk.CTkEntry(
            self,
            placeholder_text="Número de variables (ej: 2, 3)"
        )
        self.var_entry.pack(pady=10)

        # ---------------- BOTÓN GENERAR ----------------
        ctk.CTkButton(
            self,
            text="Generar estructura",
            command=self.generate_structure
        ).pack(pady=10)

        # ---------------- CONTENEDOR DINÁMICO ----------------
        self.container = ctk.CTkFrame(self)
        self.container.pack(pady=10, fill="both", expand=True)

        # ---------------- BOTONES ----------------
        self.add_btn = ctk.CTkButton(
            self,
            text="+ Agregar restricción",
            command=self.add_constraint
        )

        self.solve_btn = ctk.CTkButton(
            self,
            text="Resolver",
            command=self.solve
        )

    # ======================================================
    # GENERAR ESTRUCTURA
    # ======================================================
    def generate_structure(self):

        if not self.var_entry.get().isdigit():
            print("❌ Ingresa un número válido de variables")
            return

        self.variables = int(self.var_entry.get())

        # limpiar interfaz
        for widget in self.container.winfo_children():
            widget.destroy()

        self.constraints.clear()

        # ---------------- FUNCION OBJETIVO ----------------
        self.obj_entries = []

        obj_frame = ctk.CTkFrame(self.container)
        obj_frame.pack(pady=10)

        ctk.CTkLabel(obj_frame, text="Z =").pack(side="left")

        for i in range(self.variables):
            entry_frame = ctk.CTkFrame(obj_frame)
            entry_frame.pack(side="left")

            e = ctk.CTkEntry(entry_frame, width=60)
            e.pack(side="left")
            self.obj_entries.append(e)

            ctk.CTkLabel(
                entry_frame,
                text=f"x{i+1}",
                text_color="white"
            ).pack(side="left")

            if i < self.variables - 1:
                ctk.CTkLabel(obj_frame, text="+", text_color="white").pack(side="left")

        # ---------------- BOTONES ----------------
        self.add_btn.pack(pady=10)
        self.solve_btn.pack(pady=10)

    # ======================================================
    # AGREGAR RESTRICCIÓN
    # ======================================================
    def add_constraint(self):

        if self.variables == 0:
            print("❌ Primero define las variables")
            return

        row = ConstraintRow(self.container, self.variables)
        row.pack(pady=5)

        self.constraints.append(row)

    # ======================================================
    # RESOLVER (SIMPLEX + RESULTS VIEW)
    # ======================================================
    def solve(self):

        if not hasattr(self, "obj_entries"):
            print("❌ Genera primero la estructura")
            return

        if len(self.constraints) == 0:
            print("❌ Debes agregar al menos una restricción")
            return

        try:
            # ---------------- MODELO ----------------
            objective = clean_inputs([e.get() for e in self.obj_entries])

            constraints_data = [c.get_data() for c in self.constraints]

            model = LinearProgram(
                objective=ObjectiveFunction(
                    coefficients=objective,
                    mode="max"
                ),
                constraints=[
                    Constraint(
                        coefficients=clean_inputs(c["coefficients"]),
                        sign=c["sign"],
                        value=float(c["rhs"])
                    )
                    for c in constraints_data
                ],
                variables=self.variables
            )

            # ---------------- SIMPLEX ----------------
            solver = SimplexSolver(model)
            result = solver.solve()

            # ---------------- CAMBIO A RESULTS VIEW ----------------
            self.pack_forget()

            results_view = ResultsView(self.master, result)
            results_view.pack(fill="both", expand=True)

        except Exception as e:
            print("❌ Error al resolver:", e)