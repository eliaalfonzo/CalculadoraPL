from fractions import Fraction
from copy import deepcopy


class SimplexSolver:
    def __init__(self, model):
        self.model = model
        self.tableaux = []
        self.steps = []
        self.status = {
            "tipo_solucion": "Indeterminado",
            "acotada": "Desconocido",
            "degeneracion": "No"
        }
        self.basis = []
        self.degenerate = False

    # ---------------------------
    # AUXILIAR DE FORMATO
    # ---------------------------
    @staticmethod
    def _format_term(coef, variable, is_first=False):
        """Formatea un término matemático respetando los signos visuales."""
        if coef == 0:
            return ""
        
        # Determinar el signo y formatear el coeficiente absoluto
        sign = "+ " if coef > 0 else "- "
        if is_first:
            sign = "" if coef > 0 else "-"
            
        return f"{sign}{abs(coef)}{variable}"

    # ---------------------------
    # ESTANDARIZACIÓN
    # ---------------------------
    def get_standardization(self):
        lines = []

        # Función objetivo (Moviendo variables al lado izquierdo junto a Z)
        mode = self.model.objective.mode.upper()
        obj_terms = []
        
        for i, coef in enumerate(self.model.objective.coefficients):
            # Al pasar al lado de Z, el signo se invierte formalmente en el formato clásico:
            # Si coef > 0 pasa como -coefX, si coef < 0 pasa como +coefX
            inverted_coef = -coef
            term = self._format_term(inverted_coef, f"X{i+1}", is_first=False)
            if term:
                obj_terms.append(term)

        # Unir los términos limpiando espacios redundantes
        obj_string = " ".join(obj_terms)
        if obj_string and not obj_string.startswith("-"):
            obj_string = "+ " + obj_string

        lines.append(f"{mode} Z {obj_string} = 0".replace("  ", " "))

        slack = 1

        # Restricciones
        for c in self.model.constraints:
            left_terms = []

            for i, coef in enumerate(c.coefficients):
                is_first = (len(left_terms) == 0)
                term = self._format_term(coef, f"X{i+1}", is_first=is_first)
                if term:
                    left_terms.append(term)

            relation = c.sign

            if relation == "<=":
                left_terms.append(f"+ S{slack}" if left_terms else f"S{slack}")
                slack += 1
            elif relation == ">=":
                left_terms.append(f"- S{slack}" if left_terms else f"-S{slack}")
                slack += 1

            equation = " ".join(left_terms) + f" = {c.value}"
            lines.append(equation.replace("  ", " "))

        variables = []

        for i in range(self.model.variables):
            variables.append(f"X{i+1}")

        for i in range(slack - 1):
            variables.append(f"S{i+1}")

        lines.append(",".join(variables) + " ≥ 0")

        return lines

    # ---------------------------
    # TABLA INICIAL
    # ---------------------------
    def build_initial_tableau(self):
        num_constraints = len(self.model.constraints)

        tableau = []

        for i, c in enumerate(self.model.constraints):
            row = [Fraction(x) for x in c.coefficients]

            # variables de holgura
            for j in range(num_constraints):
                row.append(Fraction(1) if i == j else Fraction(0))

            row.append(Fraction(c.value))
            tableau.append(row)

        # Z row
        z_row = [Fraction(-x) for x in self.model.objective.coefficients]

        for _ in range(num_constraints):
            z_row.append(Fraction(0))

        z_row.append(Fraction(0))

        tableau.append(z_row)

        # Variables básicas iniciales
        self.basis = [f"s{i+1}" for i in range(num_constraints)]

        self.tableaux.append(deepcopy(tableau))

        self.steps.append({
            "message": "Tabla inicial creada",
            "tableau": deepcopy(tableau),
            "basis": deepcopy(self.basis)
        })

    # ---------------------------
    # PIVOTE
    # ---------------------------
    def get_pivot(self, tableau):
        z_row = tableau[-1]

        pivot_col = min(range(len(z_row) - 1), key=lambda j: z_row[j])

        # óptimo
        if z_row[pivot_col] >= 0:
            return None, None, "OPTIMO"

        ratios = []

        for i in range(len(tableau) - 1):
            if tableau[i][pivot_col] > 0:
                ratios.append((tableau[i][-1] / tableau[i][pivot_col], i))

        # no acotado
        if not ratios:
            return None, None, "NO_ACOTADO"

        min_ratio = min(ratios)[0]
        pivot_row = min(ratios)[1]

        # ---------------------------
        # DETECCIÓN DE DEGENERACIÓN REAL
        # ---------------------------
        min_count = sum(1 for r, _ in ratios if r == min_ratio)

        if min_count > 1:
            self.degenerate = True
            self.steps.append({
                "message": "⚠️ Degeneración detectada (empate en razón mínima)",
                "tableau": deepcopy(tableau),
                "basis": deepcopy(self.basis)
            })

        return pivot_row, pivot_col, "OK"

    # ---------------------------
    # OPERACIÓN PIVOTE
    # ---------------------------
    def pivot(self, tableau, row, col):
        # La variable que entra a la base
        if col < self.model.variables:
            entering = f"x{col + 1}"
        else:
            entering = f"s{col - self.model.variables + 1}"

        # Actualizar la variable básica de la fila pivote
        self.basis[row] = entering

        pivot_value = tableau[row][col]

        tableau[row] = [x / pivot_value for x in tableau[row]]

        for i in range(len(tableau)):
            if i != row:
                factor = tableau[i][col]
                tableau[i] = [
                    tableau[i][j] - factor * tableau[row][j]
                    for j in range(len(tableau[i]))
                ]

    # ---------------------------
    # CLASIFICACIÓN DE SOLUCIÓN
    # ---------------------------
    def classify_solution(self, tableau):
        z_row = tableau[-1]
        
        # Por defecto asumimos Única y Sí acotada
        tipo_solucion = "Única"
        acotada = "Sí"
        
        # Revisar si existió degeneración por empate o si hay un lado derecho en 0
        degeneracion = "No"
        if self.degenerate:
            degeneracion = "Sí"
        else:
            for row in tableau[:-1]:
                if row[-1] == 0:
                    degeneracion = "Sí"
                    break

        # ---------------- ÓPTIMA MÚLTIPLE ----------------
        # Comprobamos variables no básicas con costo reducido igual a cero
        for j in range(len(z_row) - 1):
            # Identificar el nombre de la variable de la columna j
            if j < self.model.variables:
                var_name = f"x{j + 1}"
            else:
                var_name = f"s{j - self.model.variables + 1}"
            
            # Si el costo reducido es 0 y NO está en la base, hay soluciones múltiples
            if z_row[j] == 0 and var_name not in self.basis:
                tipo_solucion = "Múltiple"
                break

        return {
            "tipo_solucion": tipo_solucion,
            "acotada": acotada,
            "degeneracion": degeneracion
        }

    # ---------------------------
    # SOLVER
    # ---------------------------
    def solve(self):
        self.steps.append({
            "type": "standardization",
            "content": self.get_standardization()
        })

        self.build_initial_tableau()

        tableau = deepcopy(self.tableaux[0])
        iteration = 1

        while True:
            pivot_row, pivot_col, status_flag = self.get_pivot(tableau)

            # ---------------- NO ACOTADO ----------------
            if status_flag == "NO_ACOTADO":
                self.status = {
                    "tipo_solucion": "Óptima no acotada",
                    "acotada": "No",
                    "degeneracion": "Sí" if self.degenerate else "No"
                }

                self.steps.append({
                    "message": "❌ Problema no acotado",
                    "tableau": deepcopy(tableau),
                    "pivot_row": pivot_row,
                    "pivot_col": pivot_col,
                    "basis": deepcopy(self.basis)
                })
                break

            # ---------------- ÓPTIMO ----------------
            if status_flag == "OPTIMO":
                self.status = self.classify_solution(tableau)

                self.steps.append({
                    "message": f"✔ Óptimo alcanzado ({self.status['tipo_solucion']})",
                    "tableau": deepcopy(tableau),
                    "pivot_row": None,
                    "pivot_col": None,
                    "basis": deepcopy(self.basis)
                })
                break

            # ---------------- ITERACIÓN ----------------
            self.steps.append({
                "message": f"Iteración {iteration}",
                "tableau": deepcopy(tableau),
                "pivot_row": pivot_row,
                "pivot_col": pivot_col,
                "basis": deepcopy(self.basis)
            })

            self.pivot(tableau, pivot_row, pivot_col)

            self.tableaux.append(deepcopy(tableau))

            iteration += 1

        return {
            "tableaux": self.tableaux,
            "steps": self.steps,
            "solution": self.extract_solution(tableau),
            "status": self.status,
            "solution_type": self.status
        }

    # ---------------------------
    # SOLUCIÓN FINAL
    # ---------------------------
    def extract_solution(self, tableau):
        num_vars = self.model.variables
        solution = [Fraction(0) for _ in range(num_vars)]

        for j in range(num_vars):
            column = [tableau[i][j] for i in range(len(tableau) - 1)]

            if column.count(Fraction(0)) == len(column) - 1:
                try:
                    idx = column.index(Fraction(1))
                    solution[j] = tableau[idx][-1]
                except ValueError:
                    pass

        z_value = tableau[-1][-1]

        return {
            "variables": solution,
            "z": z_value
        }