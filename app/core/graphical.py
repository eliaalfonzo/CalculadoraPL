from fractions import Fraction
import itertools


class GraphicalSolver:
    def __init__(self, model):
        self.model = model
        self.steps = []

    # ==============================
    # VALIDACIÓN
    # ==============================
    def validate(self):
        if self.model.variables != 2:
            raise Exception("El Método Gráfico solo admite 2 variables.")

    # ==============================
    # INTERSECCIÓN ENTRE 2 RECTAS
    # ==============================
    def intersection(self, c1, c2):
        a1, b1, r1 = map(Fraction, c1.coefficients + [c1.value])
        a2, b2, r2 = map(Fraction, c2.coefficients + [c2.value])

        det = a1 * b2 - a2 * b1

        if det == 0:
            return None

        x = (r1 * b2 - r2 * b1) / det
        y = (a1 * r2 - a2 * r1) / det

        return (x, y)

    # ==============================
    # VERIFICAR FACTIBILIDAD
    # ==============================
    def is_feasible(self, x, y):
        for c in self.model.constraints:
            a, b = map(Fraction, c.coefficients)
            rhs = Fraction(c.value)

            lhs = a * x + b * y

            if c.sign == "<=" and lhs > rhs:
                return False
            if c.sign == ">=" and lhs < rhs:
                return False
            if c.sign == "=" and lhs != rhs:
                return False

        return True

    # ==============================
    # FUNCIÓN OBJETIVO
    # ==============================
    def evaluate(self, x, y):
        c1, c2 = map(Fraction, self.model.objective.coefficients)
        return c1 * x + c2 * y

    # ==============================
    # CONVEX HULL (MONOTONE CHAIN)
    # ==============================
    def convex_hull(self, points):
        if len(points) <= 1:
            return points

        points = sorted(set(points))

        def cross(o, a, b):
            return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

        lower = []
        for p in points:
            while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
                lower.pop()
            lower.append(p)

        upper = []
        for p in reversed(points):
            while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
                upper.pop()
            upper.append(p)

        return lower[:-1] + upper[:-1]

    # ==============================
    # CAMBIO 1: DETECTAR REGIÓN ACOTADA
    # ==============================
    def is_bounded_region(self, feasible, hull):
        # Si la envolvente convexa tiene suficientes vértices
        # y todos los puntos están contenidos en ella,
        # asumimos región cerrada y acotada.
        if len(hull) >= 3:
            return True
        return False

    # ==============================
    # CAMBIO 2: DETECTAR DEGENERACIÓN
    # ==============================
    def is_degenerate_vertex(self, point):
        if point is None:
            return False

        x, y = point
        active_constraints = 0

        for c in self.model.constraints:
            a, b = map(Fraction, c.coefficients)
            rhs = Fraction(c.value)

            lhs = a * x + b * y

            if lhs == rhs:
                active_constraints += 1

        # En dos variables normalmente convergen 2 restricciones.
        # Si hay más, es degenerado.
        return active_constraints > 2

    # ==============================
    # SOLVER PRINCIPAL
    # ==============================
    def solve(self):
        self.validate()

        self.steps.append("📌 PASO 1: Identificación de restricciones lineales del modelo.")
        
        # El origen (0,0) siempre es un punto de cruce candidato por defecto
        points = [(Fraction(0), Fraction(0))]

        # ==============================
        # 1. INTERSECCIONES ENTRE RESTRICCIONES
        # ==============================
        for c1, c2 in itertools.combinations(self.model.constraints, 2):
            pt = self.intersection(c1, c2)
            if pt:
                points.append(pt)

        # ==============================
        # 2. INTERSECCIONES CON EJES
        # ==============================
        for c in self.model.constraints:
            a, b, r = map(Fraction, c.coefficients + [c.value])

            if a != 0:
                points.append((r / a, Fraction(0)))
            if b != 0:
                points.append((Fraction(0), r / b))

        # Filtrar puntos duplicados
        unique_points = []
        for p in points:
            if p not in unique_points:
                unique_points.append(p)

        self.steps.append(f"📌 PASO 2: Se calcularon {len(unique_points)} intersecciones en las fronteras.")
        self.steps.append("\n📈 PASO 3: Análisis de Vértices Candidatos:")

        # ==============================
        # 3. FILTRAR PUNTOS FACTIBLES
        # ==============================
        feasible = []

        for p in unique_points:
            x, y = p[0], p[1]
            
            # Formateador visual para la consola/interfaz
            coord_str = f"({x}, {y})"
            
            # Debe cumplir las restricciones y las condiciones de no negatividad estándar (x >= 0, y >= 0)
            if x >= 0 and y >= 0 and self.is_feasible(x, y):
                feasible.append((x, y))
                z_val = self.evaluate(x, y)
                self.steps.append(f"  ✓ Vértice Factible: {coord_str} -> Evaluando Z = {z_val}")
            else:
                self.steps.append(f"  ❌ Vértice No Factible: {coord_str} fuera de región.")

        if not feasible:
            self.steps.append("\n❌ Conclusión: No se encontró un espacio común. El modelo es Infactible.")
            return {
                "method": "graphical",
                "status": "SIN_SOLUCION",
                "steps": self.steps,
                "graph_data": {
                    "constraints": [],
                    "feasible_points": []
                },
                "solution": {
                    "variables": [],
                    "z": None
                }
            }

        self.steps.append(f"\n🗺️ Región factible delimitada con {len(feasible)} vértices válidos.")

        # ==============================
        # 4. CONVEX HULL (REGIÓN REAL)
        # ==============================
        hull = self.convex_hull(feasible)

        # ==============================
        # 5. CAMBIO 3: OPTIMIZAR FUNCIÓN OBJETIVO
        # ==============================
        best_point = None
        best_value = None
        optimal_points = []

        for x, y in feasible:
            z = self.evaluate(x, y)

            if best_value is None:
                best_value = z
                best_point = (x, y)
                optimal_points.append((x, y))
                continue

            if self.model.objective.mode == "max":
                if z > best_value:
                    best_value = z
                    best_point = (x, y)
                    optimal_points = [(x, y)]
                elif z == best_value:
                    optimal_points.append((x, y))
            else:
                if z < best_value:
                    best_value = z
                    best_point = (x, y)
                    optimal_points = [(x, y)]
                elif z == best_value:
                    optimal_points.append((x, y))

        # Convertimos los puntos a floats exclusivamente para Matplotlib en el front
        feasible_floats = [(float(x), float(y)) for x, y in feasible]
        hull_floats = [(float(x), float(y)) for x, y in hull]

        self.steps.append(f"\n🎯 PASO 4: Vértice óptimo encontrado en: ({best_point[0]}, {best_point[1]})")

        # ==============================
        # CAMBIO 4: CLASIFICACIÓN FINAL ANTES DEL RETURN
        # ==============================
        bounded = self.is_bounded_region(feasible, hull)
        degenerate = self.is_degenerate_vertex(best_point)

        if len(optimal_points) > 1:
            solution_kind = "Múltiple"
        else:
            solution_kind = "Única"

        solution_type = {
            "tipo_solucion": solution_kind,
            "region": "Acotada" if bounded else "No Acotada",
            "degeneracion": "Sí" if degenerate else "No",
            "region_factible": "Sí"
        }

        # ==============================
        # 6. RESULTADO FINAL
        # ==============================
        return {
            "method": "graphical",
            "status": "OPTIMA_UNICA",
            "solution_type": solution_type,
            "steps": self.steps,
            "graph_data": {
                "constraints": [
                    {
                        "coefficients": c.coefficients,
                        "rhs": c.value,
                        "sign": c.sign
                    }
                    for c in self.model.constraints
                ],
                "feasible_points": feasible_floats,
                "hull": hull_floats
            },
            "solution": {
                "variables": [float(best_point[0]), float(best_point[1])],
                "z": str(best_value)
            }
        }