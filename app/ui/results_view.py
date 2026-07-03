import customtkinter as ctk
from fractions import Fraction
from assets.styles import COLORS, FONTS, PADDING
import re

# Imports de Matplotlib para integración interactiva y matemática seria
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import numpy as np


class ResultsView(ctk.CTkFrame):
    def __init__(self, master, result):
        super().__init__(master)

        self.configure(fg_color=COLORS["bg"])
        self.result = result

        # Validar el método para derivar la renderización de la UI
        method = result.get("method", "simplex")

        if method == "graphical":
            self.build_graphical_view()
            return

        # ---------------- TÍTULO DINÁMICO ----------------
        if method == "two_phase":
            title_text = "Iteraciones del Método de las Dos Fases"
        elif method == "simplex":
            title_text = "Iteraciones del Método Simplex"
        else:
            title_text = "Resultados"
        
        ctk.CTkLabel(
            self,
            text=title_text,
            font=FONTS["title"],
            text_color=COLORS["text"]
        ).pack(pady=(PADDING["lg"], PADDING["sm"]))

        # ---------------- TIPO SOLUCIÓN ----------------
        status = result.get("status", "DESCONOCIDO")

        ctk.CTkLabel(
            self,
            text=f"Tipo de solución: {status}",
            font=FONTS["section"],
            text_color=COLORS["primary"]
        ).pack(pady=(0, PADDING["sm"]))

        # ---------------- SCROLL ----------------
        scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=COLORS["bg"],
            border_color=COLORS["border"]
        )
        scroll.pack(
            pady=PADDING["md"],
            fill="both",
            expand=True
        )

        # =========================================================
        # ITERACIONES SIMPLEX / DOS FASES
        # =========================================================
        current_phase = None

        for step_idx, step in enumerate(result.get("steps", [])):
            
            # Inyección dinámica de títulos de fase (Fase I / Fase II)
            phase = step.get("phase")
            if phase != current_phase:
                current_phase = phase
                phase_title = "FASE I" if phase == 1 else "FASE II"
                
                ctk.CTkLabel(
                    scroll,
                    text=phase_title,
                    font=FONTS["title"],
                    text_color=COLORS["primary"]
                ).pack(pady=(20, 10))

            frame = ctk.CTkFrame(
                scroll,
                fg_color=COLORS["card"],
                corner_radius=10
            )
            frame.pack(
                pady=PADDING["sm"],
                fill="x",
                anchor="n",
                padx=PADDING["sm"]
            )

            # ---------------- HEADER ----------------
            msg = step.get("description", step.get("message", f"Iteración {step_idx + 1}"))
            pivot_row = step.get("pivot_row")
            pivot_col = step.get("pivot_col")

            if pivot_row is not None and pivot_col is not None:
                msg += f" | pivote ({pivot_row}, {pivot_col})"

            ctk.CTkLabel(
                frame,
                text=msg,
                font=FONTS["section"],
                text_color=COLORS["secondary"]
            ).pack(anchor="w", padx=PADDING["md"], pady=PADDING["sm"])

            # Detectamos si la matriz viene de metodosfases ("matrix") o de simplex ("tableau")
            is_two_phase = "matrix" in step
            tableau = step.get("matrix" if is_two_phase else "tableau")
            
            if not tableau:
                continue

            table_frame = ctk.CTkFrame(frame, fg_color="transparent")
            table_frame.pack(pady=(0, PADDING["md"]), padx=PADDING["md"])

            num_rows = len(tableau)
            num_cols = len(tableau[0])

            # ---------------- CONSTRUIR ENCABEZADOS REORDENADOS Y MAPA DE COLUMNAS ----------------
            if is_two_phase:
                objective = step.get("objective", "Z")
                raw_headers = step.get("headers", [])
                
                # Guardar el índice original de cada columna y tipificar
                header_info = []
                for idx, h in enumerate(raw_headers):
                    h = h.lower()
                    if h == "rhs":
                        tipo = 3
                    elif h.startswith("x"):
                        tipo = 0
                    elif h.startswith("s") or h.startswith("e"):
                        tipo = 1
                    elif h.startswith("a"):
                        tipo = 2
                    else:
                        tipo = 99
                    header_info.append((tipo, idx, h))

                # Ordenar por tipo e índice original
                header_info.sort(key=lambda x: (x[0], x[1]))

                # Crear el mapa de orden de columnas real de la matriz
                column_order = [x[1] for x in header_info]

                # Traducir y formatear las etiquetas de los encabezados
                translated_headers = []
                for _, _, h in header_info:
                    if h.startswith("a"):
                        translated_headers.append(h.replace("a", "R").upper())
                    elif h.startswith("e"):
                        translated_headers.append(h.replace("e", "S").upper())
                    elif h == "rhs":
                        translated_headers.append("SOL")
                    else:
                        translated_headers.append(h.upper())

                headers = ["VB", objective] + translated_headers
            else:
                headers = ["VB", "Z"]
                num_vars = len(result.get("solution", {}).get("variables", []))
                num_slack = num_cols - num_vars - 1

                for i in range(num_vars):
                    headers.append(f"X{i+1}")

                for i in range(num_slack):
                    headers.append(f"S{i+1}")

                headers.append("SOL")
                column_order = list(range(num_cols))

            header_row = ctk.CTkFrame(table_frame, fg_color="transparent")
            header_row.pack(fill="x", pady=(0, 5))

            for h in headers:
                ctk.CTkLabel(
                    header_row,
                    text=h,
                    width=75,
                    height=30,
                    font=FONTS["body_bold"],
                    fg_color=COLORS["border"],
                    text_color=COLORS["text"],
                    corner_radius=4
                ).pack(side="left", padx=2)

            # ---------------- PINTAR LAS FILAS DE LA TABLA ----------------
            row_order = [num_rows - 1] + list(range(num_rows - 1))

            for display_row, real_row in enumerate(row_order):
                row_frame = ctk.CTkFrame(table_frame, fg_color="transparent")
                row_frame.pack(side="top", fill="x")

                # ---------------- VB ----------------
                basis_list = step.get("basis", [])

                if real_row == num_rows - 1:
                    if is_two_phase:
                        base_label = step.get("objective", "Z")
                    else:
                        base_label = "Z"
                elif real_row < len(basis_list):
                    raw_label = str(basis_list[real_row]).lower().strip()
                    if raw_label == "rhs":
                        base_label = "SOL"
                    elif raw_label.startswith("a"):
                        base_label = raw_label.replace("a", "R").upper()
                    elif raw_label.startswith("e"):
                        base_label = raw_label.replace("e", "S").upper()
                    else:
                        base_label = raw_label.upper()
                else:
                    base_label = ""

                ctk.CTkLabel(
                    row_frame,
                    text=base_label,
                    width=75,
                    height=32,
                    font=FONTS["table"],
                    fg_color=COLORS["border"],
                    text_color=COLORS["text"],
                    corner_radius=4
                ).pack(side="left", padx=2, pady=2)

                # ---------------- COLUMNA DE LA FUNCIÓN OBJETIVO ----------------
                if real_row == num_rows - 1:
                    obj_value = "1"
                else:
                    obj_value = "0"

                ctk.CTkLabel(
                    row_frame,
                    text=obj_value,
                    width=75,
                    height=32,
                    font=FONTS["table"],
                    fg_color=COLORS["border"],
                    text_color=COLORS["text"],
                    corner_radius=4
                ).pack(side="left", padx=2, pady=2)

                # ---------------- VALORES NUMÉRICOS REORDENADOS ----------------
                for c in column_order:
                    value = tableau[real_row][c]
                    if isinstance(value, Fraction):
                        if value.denominator == 1:
                            value = str(value.numerator)
                        else:
                            value = f"{value.numerator}/{value.denominator}"
                    else:
                        value = str(value)

                    is_pivot = (real_row == pivot_row and c == pivot_col)
                    bg = COLORS["primary"] if is_pivot else (
                        COLORS["bg"] if display_row % 2 == 0 else COLORS["border"]
                    )
                    text_color = "black" if is_pivot else COLORS["text"]

                    ctk.CTkLabel(
                        row_frame,
                        text=value,
                        width=75,
                        height=32,
                        font=FONTS["table"],
                        fg_color=bg,
                        text_color=text_color,
                        corner_radius=4
                    ).pack(side="left", padx=2, pady=2)

        # =========================================================
        # SOLUCIÓN FINAL (COMPATIBLE SIMPLEX Y DOS FASES)
        # =========================================================
        sol_z = result.get("z", result.get("solution", {}).get("z", "N/A"))
        
        if "variables" in result and isinstance(result["variables"], dict):
            variables_dict = result["variables"]
            formatted_vars = []
            for k, v in variables_dict.items():
                lbl = k.lower().strip()
                if lbl.startswith("a"):
                    lbl = lbl.replace("a", "R")
                elif lbl.startswith("e"):
                    lbl = lbl.replace("e", "S")
                formatted_vars.append(f"{lbl.upper()} = {v}")
            sol_vars = ", ".join(formatted_vars)
        else:
            solution = result.get("solution", {})
            variables = solution.get("variables", [])

            formatted_vars = []
            for i, value in enumerate(variables):
                if isinstance(value, Fraction):
                    if value.denominator == 1:
                        txt = str(value.numerator)
                    else:
                        txt = f"{value.numerator}/{value.denominator}"
                else:
                    txt = str(value)
                formatted_vars.append(f"X{i+1} = {txt}")

            sol_vars = ", ".join(formatted_vars)

        final_card = ctk.CTkFrame(
            self,
            fg_color=COLORS["card"],
            corner_radius=12,
            border_color=COLORS["primary"],
            border_width=1
        )
        final_card.pack(pady=PADDING["md"], padx=PADDING["xl"], fill="x")

        ctk.CTkLabel(final_card, text=" Solución Óptima Encontrada", font=FONTS["section"], text_color=COLORS["primary"]).pack(pady=(PADDING["sm"], PADDING["xs"]))
        ctk.CTkLabel(final_card, text=f"Z = {sol_z}", font=FONTS["title"], text_color=COLORS["text"]).pack(pady=5)
        ctk.CTkLabel(final_card, text=f"Variables: {sol_vars}", font=FONTS["body_bold"], text_color=COLORS["muted"]).pack(pady=(0, PADDING["sm"]))

        ctk.CTkButton(
            self, 
            text="← Volver al Menú Principal", 
            font=FONTS["body_bold"], 
            fg_color=COLORS["border"], 
            hover_color=COLORS["muted"], 
            text_color=COLORS["text"], 
            width=220, 
            height=40, 
            command=self.go_home
        ).pack(pady=(PADDING["sm"], PADDING["lg"]))

    # =========================================================
    #  VISTA MÉTODO GRÁFICO CORREGIDA SIN DESBORDAMIENTOS
    # =========================================================
    def build_graphical_view(self):
        ctk.CTkLabel(
            self,
            text="Optimización por Método Gráfico",
            font=FONTS["title"],
            text_color=COLORS["text"]
        ).pack(pady=(PADDING["md"], PADDING["xs"]))

        status = self.result.get("status", "DESCONOCIDO")
        ctk.CTkLabel(
            self,
            text=f"Estado del Modelo: {status}",
            font=FONTS["section"],
            text_color=COLORS["primary"]
        ).pack(pady=(0, PADDING["xs"]))

        main_split = ctk.CTkFrame(self, fg_color="transparent")
        main_split.pack(fill="both", expand=True, padx=PADDING["xl"], pady=PADDING["xs"])

        # ---- PANEL IZQUIERDO: GRÁFICO INTERACTIVO ----
        graph_frame = ctk.CTkFrame(main_split, fg_color=COLORS["card"], corner_radius=12)
        graph_frame.pack(side="left", fill="both", expand=True, padx=(0, PADDING["md"]))

        fig, ax = plt.subplots(figsize=(4.2, 3.4), dpi=100)
        fig.patch.set_facecolor(COLORS["card"])
        ax.set_facecolor(COLORS["bg"])
        
        ax.spines['bottom'].set_color(COLORS["text"])
        ax.spines['top'].set_color(COLORS["border"])
        ax.spines['left'].set_color(COLORS["text"])
        ax.spines['right'].set_color(COLORS["border"])
        ax.xaxis.label.set_color(COLORS["text"])
        ax.yaxis.label.set_color(COLORS["text"])
        ax.tick_params(colors=COLORS["muted"], labelsize=9)
        ax.grid(True, color=COLORS["border"], linestyle="--", alpha=0.5)

        graph_data = self.result.get("graph_data", {})
        constraints = graph_data.get("constraints", [])
        
        max_val = 10
        for c in constraints:
            coefs = c.get("coefficients", [1, 1])
            rhs = c.get("rhs", 10)
            if coefs[0] > 0: max_val = max(max_val, rhs / coefs[0])
            if coefs[1] > 0: max_val = max(max_val, rhs / coefs[1])
        
        upper_bound = max_val * 1.3
        x_vals = np.linspace(0, upper_bound, 400)
        ax.set_xlim(0, upper_bound)
        ax.set_ylim(0, upper_bound)
        ax.set_xlabel("Variable X1")
        ax.set_ylabel("Variable X2")

        for idx, c in enumerate(constraints):
            coefs = c.get("coefficients", [0, 0])
            rhs = c.get("rhs", 0)
            sign = c.get("sign", "<=")
            
            if coefs[1] != 0:
                y_line = (rhs - coefs[0] * x_vals) / coefs[1]
                ax.plot(x_vals, y_line, label=f"R{idx+1}: {coefs[0]}x1 + {coefs[1]}x2 {sign} {rhs}", linewidth=2)
            else:
                ax.axvline(x=rhs/coefs[0], label=f"R{idx+1}: {coefs[0]}x1 {sign} {rhs}", linewidth=2)

        resolution = 300
        grid_x = np.linspace(0, upper_bound, resolution)
        grid_y = np.linspace(0, upper_bound, resolution)

        X, Y = np.meshgrid(grid_x, grid_y)
        feasible_mask = np.ones_like(X, dtype=bool)

        for c in constraints:
            a, b = c.get("coefficients", [0, 0])
            rhs = c.get("rhs", 0)
            sign = c.get("sign", "<=")

            if sign == "<=":
                feasible_mask &= (a * X + b * Y <= rhs)
            elif sign == ">=":
                feasible_mask &= (a * X + b * Y >= rhs)
            else:
                feasible_mask &= (np.abs(a * X + b * Y - rhs) < 1e-9)

        ax.contourf(X, Y, feasible_mask, levels=[0.5, 1], colors=[COLORS["primary"]], alpha=0.18, zorder=0)

        feasible_vertex_list = graph_data.get("feasible_points", [])
        for pt in feasible_vertex_list:
            ax.scatter(pt[0], pt[1], s=40, color=COLORS["secondary"], edgecolor="black", zorder=3)

        solution = self.result.get("solution", {})
        opt_vars = solution.get("variables", [])
        if len(opt_vars) >= 2:
            ax.plot(opt_vars[0], opt_vars[1], marker="*", color=COLORS["primary"], markersize=14, zorder=4, label="Óptimo")

        ax.legend(loc="upper right", fontsize=8, facecolor=COLORS["card"], labelcolor=COLORS["text"])

        canvas = FigureCanvasTkAgg(fig, master=graph_frame)
        canvas.draw()
        
        toolbar = NavigationToolbar2Tk(canvas, graph_frame)
        toolbar.update()
        toolbar.pack(side="top", fill="x")
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=PADDING["sm"], pady=PADDING["sm"])

        # ---- PANEL DERECHO: DETALLES MATEMÁTICOS DE LOS VÉRTICES ----
        right_panel = ctk.CTkFrame(main_split, fg_color="transparent")
        right_panel.pack(side="right", fill="both", expand=True)

        scroll_right = ctk.CTkScrollableFrame(right_panel, fg_color=COLORS["bg"], label_text="Ecuaciones Analizadas", label_font=FONTS["section"], label_text_color=COLORS["muted"])
        scroll_right.pack(fill="both", expand=True)

        for step in self.result.get("steps", []):
            if isinstance(step, str) and step.strip():
                lbl_color = COLORS["secondary"] if "✓" in step or "" in step else COLORS["text"]
                lbl_font = FONTS["body_bold"] if "PASO" in step or "" in step else FONTS["body"]
                
                lbl = ctk.CTkLabel(
                    scroll_right,
                    text=str(step),
                    font=lbl_font,
                    text_color=lbl_color,
                    justify="left",
                    anchor="w"
                )
                lbl.pack(fill="x", padx=PADDING["sm"], pady=2)

        # ---- CARD INFERIOR COMPLETAMENTE VISIBLE ----
        opt_card = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=12, border_color=COLORS["primary"], border_width=1)
        opt_card.pack(fill="x", padx=PADDING["xl"], pady=(PADDING["xs"], PADDING["sm"]))

        ctk.CTkLabel(opt_card, text=" Vértice Óptimo Seleccionado", font=FONTS["section"], text_color=COLORS["primary"]).pack(pady=(4, 0))
        
        coord_txt = f"X1 = {opt_vars[0]:.2f}, X2 = {opt_vars[1]:.2f}" if len(opt_vars) == 2 else "No calculadas"
        ctk.CTkLabel(opt_card, text=f"Coordenadas óptimas: [ {coord_txt} ]", font=FONTS["body_bold"], text_color=COLORS["text"]).pack(pady=2)
        
        try:
            z_formatted = f"{float(solution.get('z', 0)):.4f}" if solution.get('z') is not None else "N/A"
        except ValueError:
            z_formatted = str(solution.get('z', 'N/A'))
            
        ctk.CTkLabel(opt_card, text=f"Z = {z_formatted}", font=FONTS["title"], text_color=COLORS["secondary"]).pack(pady=(0, 4))

        # Botón para regresar fijado al fondo sin recortarse
        ctk.CTkButton(
            self,
            text="← Volver al Menú Principal",
            font=FONTS["body_bold"],
            fg_color=COLORS["border"],
            hover_color=COLORS["muted"],
            text_color=COLORS["text"],
            width=220,
            height=35,
            command=self.go_home
        ).pack(pady=(0, PADDING["md"]))

    def go_home(self):
        plt.close('all')  # Liberar memoria latente de gráficos e hilos de Matplotlib
        self.destroy()   # Destruir el contenedor actual de la UI
        from app.ui.home_view import HomeView
        HomeView(self.master).pack(fill="both", expand=True)