from fractions import Fraction
from copy import deepcopy


class SimplexSolver:
    def __init__(self, model):
        self.model = model
        self.tableaux = []
        self.steps = []

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

        self.tableaux.append(deepcopy(tableau))

        self.steps.append({
            "message": "Tabla inicial creada",
            "tableau": deepcopy(tableau)
        })

    # ---------------------------
    # PIVOTE
    # ---------------------------
    def get_pivot(self, tableau):
        z_row = tableau[-1]

        pivot_col = min(range(len(z_row) - 1), key=lambda j: z_row[j])

        if z_row[pivot_col] >= 0:
            return None, None

        ratios = []

        for i in range(len(tableau) - 1):
            if tableau[i][pivot_col] > 0:
                ratios.append((tableau[i][-1] / tableau[i][pivot_col], i))

        if not ratios:
            raise Exception("Problema no acotado")

        _, pivot_row = min(ratios)

        return pivot_row, pivot_col

    # ---------------------------
    # OPERACIÓN PIVOTE
    # ---------------------------
    def pivot(self, tableau, row, col):
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
    # SOLVER
    # ---------------------------
    def solve(self):
        self.build_initial_tableau()

        tableau = deepcopy(self.tableaux[0])
        iteration = 0

        while True:
            pivot_row, pivot_col = self.get_pivot(tableau)

            if pivot_row is None:
                self.steps.append({
                    "message": "Óptimo alcanzado",
                    "tableau": deepcopy(tableau)
                })
                break

            self.steps.append({
                "message": f"Iteración {iteration} - pivote ({pivot_row},{pivot_col})",
                "tableau": deepcopy(tableau)
            })

            self.pivot(tableau, pivot_row, pivot_col)

            self.tableaux.append(deepcopy(tableau))

            iteration += 1

        return {
            "tableaux": self.tableaux,
            "steps": self.steps,
            "solution": self.extract_solution(tableau)
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
                idx = column.index(Fraction(1))
                solution[j] = tableau[idx][-1]

        z_value = tableau[-1][-1]

        return {
            "variables": solution,
            "z": z_value
        }