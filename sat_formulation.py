# sat_formulation.py

from pysat.formula import CNF
import tempfile

class SATFormulation:
    def __init__(self):
        self.cnf = CNF()
        self._define_constraints()

    def _define_constraints(self):
        # Example business logic constraints:
        self.cnf.append([1, 2])      # Supplier_A OR Supplier_B
        self.cnf.append([-3, -4])    # ¬Overseas OR ¬Customs_Agent
        self.cnf.append([-5, 1])     # ¬Insurance OR Supplier_A

    def get_cnf(self):
        return self.cnf

    def to_dimacs(self):
        with tempfile.NamedTemporaryFile(mode='w+t') as temp_file:
            self.cnf.to_file(temp_file.name)
            temp_file.seek(0)
            return temp_file.read()

    def interpret_solution(self, counts: dict):
        solution_str = max(counts, key=counts.get)[::-1]
        solution = {
            var: int(solution_str[var - 1])
            for var in range(1, self.cnf.nv + 1)
        }

        var_names = {
            1: 'Supplier_A',
            2: 'Supplier_B',
            3: 'Overseas',
            4: 'Customs_Agent',
            5: 'Premium_Shipping',
            6: 'Insurance'
        }

        valid = all(
            any(solution[abs(lit)] == (1 if lit > 0 else 0)
                for lit in clause)
            for clause in self.cnf.clauses
        )

        return {
            'valid': valid,
            'decisions': {var_names.get(k, f"Var_{k}"): bool(v) for k, v in solution.items()},
            'raw_solution': solution
        }
