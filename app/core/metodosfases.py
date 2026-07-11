from fractions import Fraction
from copy import deepcopy
from typing import List, Dict, Any


class TwoPhaseSolver:
    def __init__(self, lp: Any):
        self.lp = lp
        self.num_vars = lp.variables
        self.mode = lp.objective.mode.lower()

        self.c_orig = [Fraction(c) for c in lp.objective.coefficients]
        if self.mode == "max":
            self.c_orig = [-c for c in self.c_orig]

        self.constraints = lp.constraints

        # CAMBIO 1: Agregar una bandera de degeneración
        self.degenerate = False

    def solve(self) -> Dict[str, Any]:
        steps = []

        num_slack = 0
        num_artificial = 0

        for c in self.constraints:
            if c.sign in ("<=", ">="):
                num_slack += 1
            if c.sign in (">=", "="):
                num_artificial += 1

        total_columns = self.num_vars + num_slack + num_artificial + 1
        num_constraints = len(self.constraints)

        # Matriz interna estándar
        matrix = [[Fraction(0) for _ in range(total_columns)]
                  for _ in range(num_constraints + 2)]

        # Encabezados matemáticos ordenados de forma secuencial estricta
        headers = []
        headers.extend([f"x{i+1}" for i in range(self.num_vars)])

        s_idx = 1
        for c in self.constraints:
            if c.sign in ("<=", ">="):
                headers.append(f"s{s_idx}")
                s_idx += 1

        r_idx = 1
        for c in self.constraints:
            if c.sign in (">=", "="):
                headers.append(f"r{r_idx}")
                r_idx += 1

        headers.append("sol")

        basis = []
        art_indices = []
        
        current_s = 1
        current_r = 1

        for i, c in enumerate(self.constraints):
            for j in range(self.num_vars):
                matrix[i][j] = Fraction(c.coefficients[j])

            rhs_val = Fraction(c.value)
            if rhs_val < 0:
                matrix[i] = [-x for x in matrix[i]]
                rhs_val = -rhs_val
            matrix[i][-1] = rhs_val

            if c.sign in ("<=", ">="):
                s_label = f"s{current_s}"
                col_s = headers.index(s_label)
                if c.sign == "<=":
                    matrix[i][col_s] = Fraction(1)
                    basis.append(s_label)
                else:
                    matrix[i][col_s] = Fraction(-1)
                    basis.append(s_label)
                current_s += 1

            if c.sign in (">=", "="):
                r_label = f"r{current_r}"
                col_a = headers.index(r_label)
                matrix[i][col_a] = Fraction(1)
                basis.pop() if c.sign == ">=" else None  # Ajuste si es necesario dependiendo de tu lógica de base anterior
                basis.append(r_label)
                art_indices.append(col_a)
                current_r += 1

        row_z = num_constraints
        for j in range(self.num_vars):
            matrix[row_z][j] = -self.c_orig[j]

        row_w = num_constraints + 1

        if num_artificial > 0:
            for idx in art_indices:
                matrix[row_w][idx] = Fraction(-1)

            for i, c in enumerate(self.constraints):
                if c.sign in (">=", "="):
                    for j in range(total_columns):
                        matrix[row_w][j] += matrix[i][j]

            steps.append(self._save_step(
                "Fase I - Inicial",
                matrix, basis, headers, row_w, num_constraints, 1, "R"
            ))

            matrix, basis, s1, ok = self._pivot_loop(
                matrix, basis, headers, row_w,
                total_columns, num_constraints, 1, "R"
            )
            steps += s1

            if not ok or matrix[row_w][-1] != 0:
                solution_type = {
                    "tipo_solucion": "Sin solución",
                    "acotada": "Sí",
                    "degeneracion": "Sí" if self.degenerate else "No"
                }
                return {
                    "status": "SIN SOLUCIÓN",
                    "solution_type": solution_type,
                    "steps": steps
                }

        # =========================================================
        # FASE II
        # =========================================================
        matrix2 = []
        for i in range(num_constraints + 1):
            row = []
            for j in range(total_columns):
                if j not in art_indices:
                    row.append(matrix[i][j])
            matrix2.append(row)

        headers2 = [h for h in headers if not h.startswith("r")]
        row_z2 = num_constraints

        steps.append(self._save_step(
            "Fase II - Inicial",
            matrix2, basis, headers2, row_z2, num_constraints, 2, "Z"
        ))

        matrix2, basis, s2, ok = self._pivot_loop(
            matrix2, basis, headers2, row_z2,
            len(headers2), num_constraints, 2, "Z"
        )
        steps += s2

        if not ok:
            # Retorno estructurado si el problema es no acotado
            solution_type = {
                "tipo_solucion": "Óptima no acotada",
                "acotada": "No",
                "degeneracion": "Sí" if self.degenerate else "No"
            }
            return {
                "status": "NO_ACOTADA",
                "solution_type": solution_type,
                "steps": steps
            }

        sol = {h: Fraction(0) for h in headers2[:-1]}
        for i in range(num_constraints):
            if basis[i] in sol:
                sol[basis[i]] = matrix2[i][-1]

        # Usar la propiedad self.degenerate directamente
        degenerate = self.degenerate

        z = matrix2[row_z2][-1]
        if self.mode == "max":
            z = -z

        multiple = False
        for j in range(len(headers2) - 1):
            if matrix2[row_z2][j] == 0 and headers2[j] not in basis:
                multiple = True

        if multiple:
            status = "ÓPTIMA MÚLTIPLE"
        elif degenerate:
            status = "DEGENERADA"
        else:
            status = "ÓPTIMA ÚNICA"

        # Construir el diccionario independiente para el óptimo
        solution_type = {
            "tipo_solucion": "Óptima múltiple" if multiple else "Óptima única",
            "acotada": "Sí",
            "degeneracion": "Sí" if degenerate else "No"
        }

        return {
            "status": status,  # Se mantiene por compatibilidad
            "solution_type": solution_type,
            "z": str(z),
            "variables": {k: str(v) for k, v in sol.items() if k.startswith("x")},
            "steps": steps
        }

    def _pivot_loop(self, matrix, basis, headers,
                    obj_row, total_cols, num_constraints,
                    phase, objective):
        steps = []
        while True:
            entering = -1
            best = Fraction(0)
            for j in range(total_cols - 1):
                if matrix[obj_row][j] > best:
                    best = matrix[obj_row][j]
                    entering = j

            if entering == -1:
                break

            leaving = -1
            ratio_min = None
            
            # Cambiar la detección de degeneración dentro del pivot
            ratios = []
            for i in range(num_constraints):
                if matrix[i][entering] > 0:
                    r = matrix[i][-1] / matrix[i][entering]
                    ratios.append((r, i))
                    if ratio_min is None or r < ratio_min:
                        ratio_min = r
                        leaving = i

            if leaving == -1:
                return matrix, basis, steps, False

            # Evaluar empate en la razón mínima antes del pivote
            min_count = sum(1 for r, _ in ratios if r == ratio_min)
            if min_count > 1:
                self.degenerate = True

            old = basis[leaving]
            basis[leaving] = headers[entering]

            pivot = matrix[leaving][entering]
            matrix[leaving] = [x / pivot for x in matrix[leaving]]

            for i in range(len(matrix)):
                if i != leaving:
                    f = matrix[i][entering]
                    matrix[i] = [
                        matrix[i][j] - f * matrix[leaving][j]
                        for j in range(total_cols)
                    ]

            step = self._save_step(
                f"Entra {headers[entering]} sale {old}",
                matrix,
                basis,
                headers,
                obj_row,
                num_constraints,
                phase,
                objective
            )
            steps.append(step)

        return matrix, basis, steps, True

    def _save_step(
        self,
        description,
        matrix,
        basis,
        headers,
        obj_row,
        num_constraints,
        phase,
        objective,
    ):
        """
        Construye una representación ordenada del tableau para la interfaz.
        """
        ordered_headers = [objective.upper()] + [h.upper() for h in headers]

        def build_row(source_row, is_objective=False):
            row = []
            row.append("1" if is_objective else "0")
            row.extend(str(v) for v in source_row)
            return row

        output_matrix = []
        output_matrix.append(build_row(matrix[obj_row], is_objective=True))

        for i in range(num_constraints):
            output_matrix.append(build_row(matrix[i], is_objective=False))

        return {
            "description": description,
            "phase": phase,
            "objective": objective,
            "headers": ordered_headers,
            "basis": [objective.upper()] + [b.upper() for b in basis],
            "matrix": output_matrix,
        }