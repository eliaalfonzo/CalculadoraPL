import customtkinter as ctk


class ConstraintRow(ctk.CTkFrame):
    def __init__(self, master, variables):
        super().__init__(master)

        self.entries = []

        for i in range(variables):
            entry = ctk.CTkEntry(self, width=60)
            entry.pack(side="left", padx=5)
            self.entries.append(entry)

            # etiqueta de variable BIEN formada
            ctk.CTkLabel(
                self,
                text=f"x{i+1}",
                text_color="white"
            ).pack(side="left")

            if i < variables - 1:
                ctk.CTkLabel(self, text="+", text_color="white").pack(side="left")

        # signo
        self.sign = ctk.CTkOptionMenu(self, values=["<=", ">=", "="])
        self.sign.pack(side="left", padx=10)

        # RHS
        self.rhs = ctk.CTkEntry(self, width=60)
        self.rhs.pack(side="left")

    def get_data(self):
        return {
            "coefficients": [e.get() for e in self.entries],
            "sign": self.sign.get(),
            "rhs": self.rhs.get()
        }