from fractions import Fraction
from copy import deepcopy
from typing import List, Dict, Any, Tuple
# Importamos las estructuras desde tu archivo model.py
from app.core.model import LinearProgram, Constraint

class TwoPhaseSolver:
    def __init__(self, lp: LinearProgram):
        self.lp = lp
        self.num_vars = lp.variables
        self.mode = lp.objective.mode.lower() # "max" o "min"
        
        # Convertimos los coeficientes de la función objetivo a fracciones
        # Si es Maximizar, multiplicamos por -1 internamente para usar el estándar de minimización
        self.c_orig = [Fraction(c) for c in lp.objective.coefficients]
        if self.mode == "max":
            self.c_orig = [-c for c in self.c_orig]
            
        self.constraints = lp.constraints

    def solve(self) -> Dict[str, Any]:
        """
        Resuelve el problema usando el Método de las Dos Fases.
        Retorna un diccionario con el historial de pasos, tablas y la solución final.
        """
        steps = []
        
        # 1. Determinar cuántas variables de holgura, exceso y artificiales se necesitan
        num_slack = 0
        num_artificial = 0
        
        for c in self.constraints:
            if c.sign == "<=":
                num_slack += 1
            elif c.sign == ">=":
                num_slack += 1
                num_artificial += 1
            elif c.sign == "=":
                num_artificial += 1

        total_columns = self.num_vars + num_slack + num_artificial + 1  # +1 para la columna RHS
        num_constraints = len(self.constraints)
        
        # Construir la matriz inicial (Tablero)
        # Filas: num_constraints (para restricciones) + 1 (Fila Z) + 1 (Fila W de Fase I si aplica)
        matrix = [[Fraction(0) for _ in range(total_columns)] for _ in range(num_constraints + 2)]
        
        # Nombres de las variables para el reporte de la UI
        headers = [f"x{i+1}" for i in range(self.num_vars)]
        slack_counter = 1
        art_counter = 1
        slack_indices = []
        art_indices = []
        
        for c in self.constraints:
            if c.sign == "<=":
                headers.append(f"s{slack_counter}")
                slack_counter += 1
            elif c.sign == ">=":
                headers.append(f"e{slack_counter}")  # Exceso
                slack_counter += 1
                headers.append(f"a{art_counter}")
                art_counter += 1
            elif c.sign == "=":
                headers.append(f"a{art_counter}")
                art_counter += 1
        headers.append("RHS")

        # Rellenar restricciones en la matriz y definir la Base Inicial
        current_slack = self.num_vars
        current_art = self.num_vars + num_slack
        basis = []
        
        for i, c in enumerate(self.constraints):
            # Coeficientes de variables de decisión
            for j in range(self.num_vars):
                matrix[i][j] = Fraction(c.coefficients[j])
            
            # Lado derecho (RHS)
            rhs_val = Fraction(c.value)
            # Si el RHS es negativo, multiplicamos la fila por -1 para normalizarlo
            if rhs_val < 0:
                matrix[i] = [-x for x in matrix[i]]
                rhs_val = -rhs_val
                # Nota: Los signos de restricción invertirían, pero asumimos entrada estandarizada en UI
            matrix[i][-1] = rhs_val
            
            # Asignar holguras, excesos y artificiales
            if c.sign == "<=":
                matrix[i][current_slack] = Fraction(1)
                basis.append(headers[current_slack])
                current_slack += 1
            elif c.sign == ">=":
                matrix[i][current_slack] = Fraction(-1) # Exceso
                current_slack += 1
                matrix[i][current_art] = Fraction(1)    # Artificial
                basis.append(headers[current_art])
                art_indices.append(current_art)
                current_art += 1
            elif c.sign == "=":
                matrix[i][current_art] = Fraction(1)    # Artificial
                basis.append(headers[current_art])
                art_indices.append(current_art)
                current_art += 1

        # Fila Z (Función objetivo real) -> Penúltima fila de la matriz
        row_z = num_constraints
        for j in range(self.num_vars):
            matrix[row_z][j] = -self.c_orig[j]

        # Fila W (Función objetivo de la Fase I: Minimizar la suma de las variables artificiales)
        # W = sum(a_i) -> En forma estándar: W - sum(a_i) = 0
        row_w = num_constraints + 1
        if num_artificial > 0:
            for idx in art_indices:
                matrix[row_w][idx] = Fraction(-1)
            
            # Hacer operaciones de fila para que los coeficientes de las variables artificiales en la fila W sean 0
            for i, c in enumerate(self.constraints):
                if c.sign == ">=" or c.sign == "=":
                    for j in range(total_columns):
                        matrix[row_w][j] += matrix[i][j]
            
            steps.append(self._save_step("Matriz Inicial - Inicialización Fase I", matrix, basis, headers, row_w))
            
            # --- ITERACIONES FASE I ---
            matrix, basis, phase1_steps, success = self._pivot_loop(matrix, basis, headers, row_w, total_columns, num_constraints)
            steps.extend(phase1_steps)
            
            if not success:
                return {"status": "NO_FEASIBLE", "message": "El problema no tiene solución factible.", "steps": steps}
            
            # Verificar si el valor de W es cero al final de la Fase I
            if matrix[row_w][-1] != 0:
                return {"status": "NO_FEASIBLE", "message": "El problema no tiene solución factible (W > 0).", "steps": steps}
        
        # --- PREPARACIÓN FASE II ---
        # Eliminamos la fila W y removemos las columnas de las variables artificiales
        matrix_phase2 = []
        for i in range(num_constraints + 1): # Dejamos fuera la fila W
            new_row = []
            for j in range(total_columns):
                if j not in art_indices:
                    new_row.append(matrix[i][j])
            matrix_phase2.append(new_row)
            
        headers_phase2 = [h for j, h in enumerate(headers) if j not in art_indices]
        row_z_p2 = num_constraints
        total_cols_p2 = len(headers_phase2)

        steps.append(self._save_step("Inicio de la Fase II (Removiendo Artificiales)", matrix_phase2, basis, headers_phase2, row_z_p2))

        # --- ITERACIONES FASE II ---
        matrix_phase2, basis, phase2_steps, success = self._pivot_loop(matrix_phase2, basis, headers_phase2, row_z_p2, total_cols_p2, num_constraints)
        steps.extend(phase2_steps)

        if not success:
            return {"status": "UNBOUNDED", "message": "El problema no está acotado.", "steps": steps}

        # --- EXTRACCIÓN DE RESULTADOS ---
        sol_dict = {h: Fraction(0) for h in headers_phase2[:-1]}
        for i in range(num_constraints):
            if basis[i] in sol_dict:
                sol_dict[basis[i]] = matrix_phase2[i][-1]

        # El valor final de Z exacto
        z_value = matrix_phase2[row_z_p2][-1]
        if self.mode == "max":
            z_value = -z_value # Revertimos el cambio de signo inicial de maximización

        # Formatear la solución final en strings legibles (como fracciones)
        solution_formatted = {k: str(v) for k, v in sol_dict.items() if k.startswith('x')}
        
        return {
            "status": "OPTIMAL",
            "z": str(z_value),
            "variables": solution_formatted,
            "steps": steps
        }

    def _pivot_loop(self, matrix: List[List[Fraction]], basis: List[str], headers: List[str], 
                    obj_row: int, total_cols: int, num_constraints: int) -> Tuple[List[List[Fraction]], List[str], List[Dict], bool]:
        """Ejecuta el bucle de pivoteo clásico del algoritmo Simplex."""
        loop_steps = []
        
        while True:
            # Buscar columna pivote (Criterio de entrada: indicador más positivo en la fila objetivo)
            # Nota: Al estar bajo formato de minimización estricta de costos, buscamos coeficientes positivos.
            entering_col = -1
            max_val = Fraction(0)
            for j in range(total_cols - 1):
                if matrix[obj_row][j] > max_val:
                    max_val = matrix[obj_row][j]
                    entering_col = j
            
            # Si no hay indicadores positivos, se llegó al óptimo de esta fase
            if entering_col == -1:
                break
                
            # Buscar fila pivote (Criterio de salida: Razón mínima RHS / Coeficiente)
            leaving_row = -1
            min_ratio = None
            
            for i in range(num_constraints):
                if matrix[i][entering_col] > 0:
                    ratio = matrix[i][-1] / matrix[i][entering_col]
                    if min_ratio is None or ratio < min_ratio:
                        min_ratio = ratio
                        leaving_row = i
                        
            # Si ninguna variable restringe (no hay coeficientes > 0), no está acotado
            if leaving_row == -1:
                return matrix, basis, loop_steps, False

            # Intercambiar variable en la base
            old_basis = basis[leaving_row]
            basis[leaving_row] = headers[entering_col]

            # Operación de pivoteo: Hacer que el elemento pivote sea 1
            pivot_val = matrix[leaving_row][entering_col]
            matrix[leaving_row] = [x / pivot_val for x in matrix[leaving_row]]

            # Hacer cero el resto de elementos de la columna pivote
            for i in range(len(matrix)):
                if i != leaving_row:
                    factor = matrix[i][entering_col]
                    matrix[i] = [matrix[i][j] - factor * matrix[leaving_row][j] for j in range(total_cols)]

            loop_steps.append(self._save_step(
                f"Iteración: Entra {headers[entering_col]} por {old_basis}", 
                matrix, basis, headers, obj_row
            ))

        return matrix, basis, loop_steps, True

    def _save_step(self, description: str, matrix: List[List[Fraction]], basis: List[str], headers: List[str], obj_row: int) -> Dict[str, Any]:
        """Copia el estado actual de la matriz y lo convierte a strings de fracciones para renderizar en la interfaz."""
        matrix_str = []
        for i in range(len(matrix)):
            row_str = []
            for j in range(len(matrix[i])):
                # Guardamos como string en formato de fracción legible (ej: "3/4")
                row_str.append(str(matrix[i][j]))
            matrix_str.append(row_str)
            
        return {
            "description": description,
            "headers": deepcopy(headers),
            "basis": deepcopy(basis),
            "matrix": matrix_str
        }