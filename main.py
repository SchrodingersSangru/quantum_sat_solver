# main.py

from sat_formulation import SATFormulation
from qiskit_solver import QiskitSolver

# Create business logic constraints
formulation = SATFormulation()
dimacs = formulation.to_dimacs()

# Run quantum solver with custom number of shots
solver = QiskitSolver(dimacs, shots=2048)
result_counts = solver.solve()

# Interpret the result
solution = formulation.interpret_solution(result_counts)

# Output
print(f"Solution Valid: {solution['valid']}")
print("Business Decisions:")
for k, v in solution['decisions'].items():
    print(f"- {k}: {'✅' if v else '❌'}")
