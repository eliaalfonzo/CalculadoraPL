import customtkinter as ctk


class ResultsView(ctk.CTkFrame):
    def __init__(self, master, result):
        super().__init__(master)

        self.configure(fg_color="#0f172a")

        self.result = result

        # ---------------- TITULO ----------------
        ctk.CTkLabel(
            self,
            text="Método Simplex - Iteraciones",
            font=("Arial", 22, "bold"),
            text_color="white"
        ).pack(pady=15)

        # ---------------- SCROLL ----------------
        scroll = ctk.CTkScrollableFrame(self, width=900, height=500)
        scroll.pack(pady=10, fill="both", expand=True)

        # ---------------- ITERACIONES ----------------
        for i, step in enumerate(result["steps"]):

            frame = ctk.CTkFrame(scroll)
            frame.pack(pady=15, fill="x")

            # título iteración
            ctk.CTkLabel(
                frame,
                text=step["message"],
                font=("Arial", 16, "bold"),
                text_color="#38bdf8"
            ).pack(anchor="w", pady=5)

            # ---------------- TABLA ----------------
            table_frame = ctk.CTkFrame(frame)
            table_frame.pack(pady=5)

            tableau = step["tableau"]

            for r in range(len(tableau)):
                row_frame = ctk.CTkFrame(table_frame)
                row_frame.pack(side="top")

                for c in range(len(tableau[r])):
                    ctk.CTkLabel(
                        row_frame,
                        text=str(tableau[r][c]),
                        width=60,
                        height=25,
                        fg_color="#1e293b",
                        text_color="white",
                        corner_radius=5
                    ).pack(side="left", padx=2, pady=2)

        # ---------------- SOLUCIÓN FINAL ----------------
        sol = result["solution"]

        final_frame = ctk.CTkFrame(self)
        final_frame.pack(pady=20)

        ctk.CTkLabel(
            final_frame,
            text="Solución Óptima",
            font=("Arial", 18, "bold"),
            text_color="white"
        ).pack(pady=10)

        ctk.CTkLabel(
            final_frame,
            text=f"Z = {sol['z']}",
            text_color="#22c55e",
            font=("Arial", 16)
        ).pack(pady=5)

        ctk.CTkLabel(
            final_frame,
            text=f"Variables = {sol['variables']}",
            text_color="#38bdf8"
        ).pack(pady=5)

        # ---------------- BOTÓN ----------------
        ctk.CTkButton(
            self,
            text="Volver",
            command=self.go_home
        ).pack(pady=10)

    def go_home(self):
        self.pack_forget()