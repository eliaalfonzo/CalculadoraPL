import customtkinter as ctk
from fractions import Fraction
from assets.styles import COLORS, FONTS, PADDING


class ResultsView(ctk.CTkFrame):
    def __init__(self, master, result):
        super().__init__(master)

        self.configure(fg_color=COLORS["bg"])
        self.result = result

        # ---------------- TITULO ----------------
        ctk.CTkLabel(
            self,
            text="Iteraciones Método Simplex",
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
            padx=PADDING["xl"],
            fill="both",
            expand=True
        )

        # =========================================================
        # ITERACIONES
        # =========================================================
        for step in result.get("steps", []):

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
            msg = step.get("message", "")

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

            tableau = step.get("tableau")
            if not tableau:
                continue

            table_frame = ctk.CTkFrame(frame, fg_color="transparent")
            table_frame.pack(pady=(0, PADDING["md"]), padx=PADDING["md"])

            num_rows = len(tableau)
            num_cols = len(tableau[0])

            # =========================================================
            # ENCABEZADOS TIPO LIBRO: BV | Z | X1.. | RHS
            # =========================================================
            headers = ["BV", "Z"]

            for i in range(num_cols - 2):
                headers.append(f"X{i+1}")

            headers.append("RHS")

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

            # =========================================================
            # TABLA
            # =========================================================
            for r in range(num_rows):

                row_frame = ctk.CTkFrame(table_frame, fg_color="transparent")
                row_frame.pack(side="top", fill="x")

                # BV (base variable visual)
                base_label = "S" + str(r + 1) if r < num_rows - 1 else "Z"

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

                for c in range(num_cols):

                    value = tableau[r][c]

                    # ---------------- FRACTION CLEAN ----------------
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
        # SOLUCIÓN FINAL
        # =========================================================
        sol = result.get("solution", {})

        final_card = ctk.CTkFrame(
            self,
            fg_color=COLORS["card"],
            corner_radius=12,
            border_color=COLORS["primary"],
            border_width=1
        )
        final_card.pack(
            pady=PADDING["md"],
            padx=PADDING["xl"],
            fill="x"
        )

        ctk.CTkLabel(
            final_card,
            text="✨ Solución Óptima Encontrada",
            font=FONTS["section"],
            text_color=COLORS["primary"]
        ).pack(pady=(PADDING["sm"], PADDING["xs"]))

        ctk.CTkLabel(
            final_card,
            text=f"Z = {sol.get('z', 'N/A')}",
            font=FONTS["title"],
            text_color=COLORS["text"]
        ).pack(pady=5)

        ctk.CTkLabel(
            final_card,
            text=f"Variables: {sol.get('variables', [])}",
            font=FONTS["body_bold"],
            text_color=COLORS["muted"]
        ).pack(pady=(0, PADDING["sm"]))

        # ---------------- BOTÓN VOLVER ----------------
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

    def go_home(self):
        self.pack_forget()
        from app.ui.home_view import HomeView
        HomeView(self.master).pack(fill="both", expand=True)