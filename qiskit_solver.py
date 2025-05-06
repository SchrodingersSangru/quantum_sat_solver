# quantum_solver.py

import math
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
from qiskit.circuit.library import MCXGate
from qiskit_aer import AerSimulator

class QiskitSolver:
    def __init__(self, dimacs_cnf: str, shots: int = 1024):
        self.dimacs = dimacs_cnf
        self.shots = shots
        self.num_vars, self.clauses = self._parse_dimacs(dimacs_cnf)
        self.simulator = AerSimulator()

    def _parse_dimacs(self, dimacs: str):
        lines = [line.strip() for line in dimacs.split('\n') if line]
        clauses = []
        num_vars = 0

        for line in lines:
            if line.startswith('p cnf'):
                _, _, num_vars, _ = line.split()
                num_vars = int(num_vars)
            elif not line.startswith('c') and not line.startswith('p'):
                clause = [int(x) for x in line[:-2].split()]
                clauses.append(clause)

        return num_vars, clauses

    def _build_oracle(self):
        qr = QuantumRegister(self.num_vars, 'var')
        clause_ancillas = QuantumRegister(len(self.clauses), 'clause')
        output_ancilla = QuantumRegister(1, 'out')
        qc = QuantumCircuit(qr, clause_ancillas, output_ancilla, name="Oracle")

        for i, clause in enumerate(self.clauses):
            for x in clause:
                if x < 0:
                    qc.x(qr[abs(x) - 1])

            controls = [qr[abs(x) - 1] for x in clause]
            if len(controls) > 1:
                qc.append(MCXGate(len(controls)), controls + [clause_ancillas[i]])
            else:
                qc.cx(controls[0], clause_ancillas[i])

            for x in clause:
                if x < 0:
                    qc.x(qr[abs(x) - 1])

            qc.x(clause_ancillas[i])

        if len(self.clauses) > 1:
            qc.append(MCXGate(len(self.clauses)), clause_ancillas[:] + [output_ancilla[0]])
        else:
            qc.cx(clause_ancillas[0], output_ancilla[0])

        qc.z(output_ancilla[0])
        qc.append(MCXGate(len(self.clauses)).inverse(), clause_ancillas[:] + [output_ancilla[0]])

        for i, clause in reversed(list(enumerate(self.clauses))):
            qc.x(clause_ancillas[i])
            for x in reversed(clause):
                if x < 0:
                    qc.x(qr[abs(x) - 1])

            controls = [qr[abs(x) - 1] for x in clause]
            if len(controls) > 1:
                qc.append(MCXGate(len(controls)).inverse(), controls + [clause_ancillas[i]])
            else:
                qc.cx(controls[0], clause_ancillas[i])

            for x in clause:
                if x < 0:
                    qc.x(qr[abs(x) - 1])

        return qc

    def _grover_diffuser(self):
        qc = QuantumCircuit(self.num_vars, name="Diffuser")
        qc.h(range(self.num_vars))
        qc.x(range(self.num_vars))
        qc.append(MCXGate(self.num_vars - 1), list(range(self.num_vars - 1)) + [self.num_vars - 1])
        qc.x(range(self.num_vars))
        qc.h(range(self.num_vars))
        return qc

    def solve(self):
        N = 2 ** self.num_vars
        iterations = math.floor(math.pi / 4 * math.sqrt(N))

        var_reg = QuantumRegister(self.num_vars, 'var')
        clause_reg = QuantumRegister(len(self.clauses), 'clause')
        out_reg = QuantumRegister(1, 'out')
        creg = ClassicalRegister(self.num_vars, 'meas')

        qc = QuantumCircuit(var_reg, clause_reg, out_reg, creg)
        qc.h(var_reg)

        oracle = self._build_oracle()
        diffuser = self._grover_diffuser()

        for _ in range(iterations):
            qc.append(oracle, var_reg[:] + clause_reg[:] + out_reg[:])
            qc.append(diffuser, var_reg[:])

        qc.measure(var_reg, creg)

        transpiled = transpile(qc, self.simulator)
        print(transpiled.draw())
        result = self.simulator.run(transpiled, shots=self.shots).result()
        return result.get_counts(qc)
