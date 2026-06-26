# Contenido de prueba.py
from app.core.model import LinearProgram, Constraint, ObjectiveFunction
from app.core.metodosfases import TwoPhaseSolver

# 1. Definimos la función objetivo con sus coeficientes reales [4.0, 1.0]
funcion_objetivo = ObjectiveFunction(coefficients=[4.0, 1.0], mode="min")

# 2. Definimos la lista de restricciones con sus coeficientes, signo y valor RHS
restricciones = [
    Constraint(coefficients=[3.0, 1.0], sign="=", value=3.0),
    Constraint(coefficients=[4.0, 3.0], sign=">=", value=6.0),
    Constraint(coefficients=[1.0, 2.0], sign="<=", value=4.0)
]

# 3. Armamos el Programa Lineal completo (son 2 variables de decisión)
problema = LinearProgram(
    objective=funcion_objetivo,
    constraints=restricciones,
    variables=2
)

# 4. Pasamos el problema al cerebro matemático y lo ejecutamos
solver = TwoPhaseSolver(problema)
resultado = solver.solve()

# 5. Imprimimos los resultados en la terminal
print("=========================================")
print("       RESULTADOS DEL EJERCICIO          ")
print("=========================================")
print(f"Estado de la solución: {resultado['status']}")
print(f"Valor óptimo de Z:     {resultado['z']}")
print(f"Valores de las variables:")
for var, valor in resultado['variables'].items():
    print(f"  - {var} = {valor}")
print("=========================================")
print(f"Se generaron {len(resultado['steps'])} tablas/pasos iterativos.")