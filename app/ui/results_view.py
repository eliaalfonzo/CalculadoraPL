import customtkinter as ctk
from fractions import Fraction
from assets.styles import COLORS, FONTS, PADDING

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

        # ---------------- TÍTULO DINÁMICO (SIMPLEX O DOS FASES) ----------------
        title_text = "Iteraciones Método de las Dos Fases" if method == "two_phase" or "steps" in result and len(result["steps"]) > 0 and "headers" in result["steps"][0] else "Iteraciones Método Simplex"
        
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
        # DICCIONARIO DE TRADUCCIÓN DE VARIABLES SOLICITADO
        # =========================================================
        var_translation = {
            "a1": "s1",
            "e1": "s2",
            "a2": "r1",
            "s2": "r2",
            "rhs": "Sol"
        }

        # =========================================================
        # ITERACIONES SIMPLEX / DOS FASES
        # =========================================================
        for step_idx, step in enumerate(result.get("steps", [])):
            frame = ctk.CTkFrame(
                scroll,
                fg_color=COLORS["card"],
                corner_radius=10
            )
            frame.pack(
                pady=PADDING["sm"],
                fill="x",
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

            # ---------------- CONSTRUIR ENCABEZADOS DE COLUMNAS ----------------
            if is_two_phase:
                raw_headers = step.get("headers", [])
                headers = ["BV"] + [var_translation.get(h.lower(), h.lower()) for h in raw_headers]
            else:
                headers = ["BV", "Z"]
                for i in range(num_cols - 2):
                    headers.append(f"x{i+1}")
                headers.append("Sol")

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
            for r in range(num_rows):
                row_frame = ctk.CTkFrame(table_frame, fg_color="transparent")
                row_frame.pack(side="top", fill="x")

                # Determinar la variable básica (BV) para la fila actual
                if is_two_phase:
                    basis_list = step.get("basis", [])
                    if r < len(basis_list):
                        raw_label = str(basis_list[r]).lower()
                        base_label = var_translation.get(raw_label, raw_label)
                    elif r == num_rows - 2:
                        base_label = "Z"
                    else:
                        base_label = "W"
                else:
                    base_label = "s" + str(r + 1) if r < num_rows - 1 else "Z"

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

                # Rellenar los valores numéricos
                for c in range(num_cols):
                    value = tableau[r][c]
                    if isinstance(value, Fraction):
                        if value.denominator == 1:
                            value = str(value.numerator)
                        else:
                            value = f"{value.numerator}/{value.denominator}"
                    else:
                        value = str(value)

                    is_pivot = (r == pivot_row and c == pivot_col)
                    bg = COLORS["primary"] if is_pivot else (
                        COLORS["bg"] if r % 2 == 0 else COLORS["border"]
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
            # También normalizamos la tarjeta final de resultados
            sol_vars = ", ".join([f"{var_translation.get(k.lower(), k.lower())} = {v}" for k, v in variables_dict.items()])
        else:
            sol_vars = str(result.get("solution", {}).get("variables", []))

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

        ctk.CTkButton(self, text="← Volver al Menú Principal", font=FONTS["body_bold"], fg_color=COLORS["border"], hover_color=COLORS["muted"], text_color=COLORS["text"], width=220, height=40, command=self.go_home).pack(pady=(PADDING["sm"], PADDING["lg"]))

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
        plt.close('all')  # Liberar memoria latente de gráficos
        self.destroy()   # Eliminar bucles gráficos concurrentes
        from app.ui.home_view import HomeView
        HomeView(self.master).pack(fill="both", expand=True)