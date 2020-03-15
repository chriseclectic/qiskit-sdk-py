# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2020.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

# pylint: disable=invalid-name

"""Tests for clifford append gate functions."""

import unittest
from test import combine
from ddt import ddt

import numpy as np

from qiskit.test import QiskitTestCase
from qiskit.circuit import Gate, QuantumRegister, QuantumCircuit
from qiskit.extensions import UnitaryGate
from qiskit.extensions.standard import (IGate, XGate, YGate, ZGate,
                                        HGate, SGate, SdgGate,
                                        CXGate, CZGate, SwapGate)
from qiskit.quantum_info.operators import Clifford, Operator
from qiskit.quantum_info.operators.symplectic.clifford_append_gate import append_gate


class VGate(Gate):
    """V Gate used in Clifford synthesis."""

    def __init__(self):
        """Create new V Gate."""
        super().__init__('v', 1, [])

    def _define(self):
        """V Gate definition."""
        q = QuantumRegister(1, 'q')
        self.definition = [(SdgGate(), [q[0]], []), (HGate(), [q[0]], [])]


class WGate(Gate):
    """W Gate used in Clifford synthesis."""

    def __init__(self):
        """Create new W Gate."""
        super().__init__('w', 1, [])

    def _define(self):
        """W Gate definition."""
        q = QuantumRegister(1, 'q')
        self.definition = [(VGate(), [q[0]], []), (VGate(), [q[0]], [])]


def random_clifford_circuit(num_qubits, num_gates, gates='all', seed=None):
    """Generate a pseudo random Clifford circuit."""
    if gates == 'all':
        gates = ['i', 'x', 'y', 'z', 'h', 's', 'sdg', 'v', 'w', 'cx', 'cz', 'swap']
    if gates == '1-qubit':
        gates = ['i', 'x', 'y', 'z', 'h', 's', 'sdg', 'v', 'w']

    instructions = {
        'i': (IGate(), 1),
        'x': (XGate(), 1),
        'y': (YGate(), 1),
        'z': (ZGate(), 1),
        'h': (HGate(), 1),
        's': (SGate(), 1),
        'sdg': (SdgGate(), 1),
        'v': (VGate(), 1),
        'w': (WGate(), 1),
        'cx': (CXGate(), 2),
        'cz': (CZGate(), 2),
        'swap': (SwapGate(), 2)
    }

    rng = np.random.RandomState(seed=seed)
    samples = rng.choice(gates, num_gates)

    circ = QuantumCircuit(num_qubits)

    for name in samples:
        gate, nqargs = instructions[name]
        qargs = rng.choice(range(num_qubits), nqargs, replace=False).tolist()
        circ.append(gate, qargs)

    return circ


class TestCliffordGates(QiskitTestCase):
    """Tests for clifford append gate functions."""

    def test_append_1_qubit_gate(self):
        "Tests for append of 1-qubit gates"

        target_table = {
            "i": np.array([[[True, False], [False, True]]], dtype=np.bool),
            "id": np.array([[[True, False], [False, True]]], dtype=np.bool),
            "iden": np.array([[[True, False], [False, True]]], dtype=np.bool),
            "x": np.array([[[True, False], [False, True]]], dtype=np.bool),
            "y": np.array([[[True, False], [False, True]]], dtype=np.bool),
            "z": np.array([[[True, False], [False, True]]], dtype=np.bool),
            "h": np.array([[[False, True], [True, False]]], dtype=np.bool),
            "s": np.array([[[True, True], [False, True]]], dtype=np.bool),
            "sdg": np.array([[[True, True], [False, True]]], dtype=np.bool),
            "sinv": np.array([[[True, True], [False, True]]], dtype=np.bool),
            "v": np.array([[[True, True], [True, False]]], dtype=np.bool),
            "w": np.array([[[False, True], [True, True]]], dtype=np.bool),

        }

        target_phase = {
            "i": np.array([[False, False]], dtype=np.bool),
            "id": np.array([[False, False]], dtype=np.bool),
            "iden": np.array([[False, False]], dtype=np.bool),
            "x": np.array([[False, True]], dtype=np.bool),
            "y": np.array([[True, True]], dtype=np.bool),
            "z": np.array([[True, False]], dtype=np.bool),
            "h": np.array([[False, False]], dtype=np.bool),
            "s": np.array([[False, False]], dtype=np.bool),
            "sdg": np.array([[True, False]], dtype=np.bool),
            "sinv": np.array([[True, False]], dtype=np.bool),
            "v": np.array([[False, False]], dtype=np.bool),
            "w": np.array([[False, False]], dtype=np.bool)
        }

        target_stabilizer = {
            "i": "+Z",
            "id": "+Z",
            "iden": "+Z",
            "x": "-Z",
            "y": "-Z",
            "z": "+Z",
            "h": "+X",
            "s": "+Z",
            "sdg": "+Z",
            "sinv": "+Z",
            "v": "+X",
            "w": "+Y",
        }

        target_destabilizer = {
            "i": "+X",
            "id": "+X",
            "iden": "+X",
            "x": "+X",
            "y": "-X",
            "z": "-X",
            "h": "+Z",
            "s": "+Y",
            "sdg": "-Y",
            "sinv": "-Y",
            "v": "+Y",
            "w": "+Z",
        }

        for gate_name in ("i", "id", "iden", "x", "y", "z", "h",
                          "s", "sdg", "v", "w"):
            with self.subTest(msg='append gate %s' % gate_name):
                cliff = Clifford([[1, 0], [0, 1]])
                cliff = append_gate(cliff, gate_name, [0])
                value_table = cliff.table._array
                value_phase = cliff.table._phase
                value_stabilizer = cliff.stabilizer.to_labels()
                value_destabilizer = cliff.destabilizer.to_labels()
                self.assertTrue(np.all(np.array(value_table ==
                                                target_table[gate_name])))
                self.assertTrue(np.all(np.array(value_phase ==
                                                target_phase[gate_name])))
                self.assertTrue(np.all(np.array(value_stabilizer ==
                                                [target_stabilizer[gate_name]])))
                self.assertTrue(np.all(np.array(value_destabilizer ==
                                                [target_destabilizer[gate_name]])))

    def test_1_qubit_identity_relations(self):
        "Tests identity relations for 1-qubit gates"

        for gate_name in ("x", "y", "z", "h"):
            with self.subTest(msg='identity for gate %s' % gate_name):
                cliff = Clifford([[1, 0], [0, 1]])
                cliff1 = cliff.copy()
                cliff = append_gate(cliff, gate_name, [0])
                cliff = append_gate(cliff, gate_name, [0])
                self.assertEqual(cliff, cliff1)

        gates = ['s', 's', 'v']
        inv_gates = ['sdg', 'sinv', 'w']

        for gate_name, inv_gate in zip(gates, inv_gates):
            with self.subTest(msg='identity for gate %s' % gate_name):
                cliff = Clifford([[1, 0], [0, 1]])
                cliff1 = cliff.copy()
                cliff = append_gate(cliff, gate_name, [0])
                cliff = append_gate(cliff, inv_gate, [0])
                self.assertEqual(cliff, cliff1)

    def test_1_qubit_mult_relations(self):
        "Tests multiplicity relations for 1-qubit gates"

        rels = ['x * y = z', 'x * z = y', 'y * z = x',
                's * s = z', 'sdg * sdg = z', 'sinv * sinv = z',
                'sdg * h = v', 'h * s = w']

        for rel in rels:
            with self.subTest(msg='relation %s' % rel):
                split_rel = rel.split()
                cliff = Clifford([[1, 0], [0, 1]])
                cliff1 = cliff.copy()
                cliff = append_gate(cliff, split_rel[0], [0])
                cliff = append_gate(cliff, split_rel[2], [0])
                cliff1 = append_gate(cliff1, split_rel[4], [0])
                self.assertEqual(cliff, cliff1)

    def test_1_qubit_conj_relations(self):
        "Tests conjugation relations for 1-qubit gates"

        rels = ['h * x * h = z', 'h * y * h = y',
                's * x * sdg = y', 'w * x * v = y',
                'w * y * v = z', 'w * z * v = x']

        for rel in rels:
            with self.subTest(msg='relation %s' % rel):
                split_rel = rel.split()
                cliff = Clifford([[1, 0], [0, 1]])
                cliff1 = cliff.copy()
                cliff = append_gate(cliff, split_rel[0], [0])
                cliff = append_gate(cliff, split_rel[2], [0])
                cliff = append_gate(cliff, split_rel[4], [0])
                cliff1 = append_gate(cliff1, split_rel[6], [0])
                self.assertEqual(cliff, cliff1)

    def test_append_2_qubit_gate(self):
        "Tests for append of 2-qubit gates"

        target_table = {
            "cx [0, 1]": np.array([[True, True, False, False],
                                   [False, True, False, False],
                                   [False, False, True, False],
                                   [False, False, True, True]]),

            "cx [1, 0]": np.array([[True, False, False, False],
                                   [True, True, False, False],
                                   [False, False, True, True],
                                   [False, False, False, True]]),

            "cz [0, 1]": np.array([[True, False, False, True],
                                   [False, True, True, False],
                                   [False, False, True, False],
                                   [False, False, False, True]]),

            "cz [1, 0]": np.array([[True, False, False, True],
                                   [False, True, True, False],
                                   [False, False, True, False],
                                   [False, False, False, True]]),

            "swap [0, 1]": np.array([[False, True, False, False],
                                    [True, False, False, False],
                                    [False, False, False, True],
                                    [False, False, True, False]]),

            "swap [1, 0]": np.array([[False, True, False, False],
                                     [True, False, False, False],
                                     [False, False, False, True],
                                     [False, False, True, False]])
        }

        target_phase = np.array([False, False, False, False])

        target_stabilizer = {
            "cx [0, 1]": ['+ZI', '+ZZ'],
            "cx [1, 0]": ['+ZZ', '+IZ'],
            "cz [0, 1]": ['+ZI', '+IZ'],
            "cz [1, 0]": ['+ZI', '+IZ'],
            "swap [0, 1]": ['+IZ', '+ZI'],
            "swap [1, 0]": ['+IZ', '+ZI']
        }

        target_destabilizer = {
            "cx [0, 1]": ['+XX', '+IX'],
            "cx [1, 0]": ['+XI', '+XX'],
            "cz [0, 1]": ['+XZ', '+ZX'],
            "cz [1, 0]": ['+XZ', '+ZX'],
            "swap [0, 1]": ['+IX', '+XI'],
            "swap [1, 0]": ['+IX', '+XI']
        }

        for gate_name in ("cx", "cz", "swap"):
            for qubits in ([0, 1], [1, 0]):
                with self.subTest(msg='append gate %s %s' % (
                        gate_name, qubits)):
                    gate_qubits = gate_name + " " + str(qubits)
                    cliff = Clifford(np.eye(4))
                    cliff = append_gate(cliff, gate_name, qubits)
                    value_table = cliff.table._array
                    value_phase = cliff.table._phase
                    value_stabilizer = cliff.stabilizer.to_labels()
                    value_destabilizer = cliff.destabilizer.to_labels()
                    self.assertTrue(np.all(np.array(value_table ==
                                                    target_table[gate_qubits])))
                    self.assertTrue(np.all(np.array(value_phase ==
                                                    target_phase)))
                    self.assertTrue(np.all(np.array(value_stabilizer ==
                                                    target_stabilizer[gate_qubits])))
                    self.assertTrue(np.all(np.array(value_destabilizer ==
                                                    target_destabilizer[gate_qubits])))

    def test_2_qubit_identity_relations(self):
        "Tests identity relations for 2-qubit gates"

        for gate_name in ("cx", "cz", "swap"):
            for qubits in ([0, 1], [1, 0]):
                with self.subTest(msg='append gate %s %s' % (
                        gate_name, qubits)):
                    cliff = Clifford(np.eye(4))
                    cliff1 = cliff.copy()
                    cliff = append_gate(cliff, gate_name, qubits)
                    cliff = append_gate(cliff, gate_name, qubits)
                    self.assertEqual(cliff, cliff1)

    def test_2_qubit_relations(self):
        "Tests relations for 2-qubit gates"

        with self.subTest(msg='relation between cx, h and cz'):
            cliff = Clifford(np.eye(4))
            cliff1 = cliff.copy()
            cliff = append_gate(cliff, 'h', [1])
            cliff = append_gate(cliff, 'cx', [0, 1])
            cliff = append_gate(cliff, 'h', [1])
            cliff = append_gate(cliff, 'cz', [0, 1])
            self.assertEqual(cliff, cliff1)

        with self.subTest(msg='relation between cx and swap'):
            cliff = Clifford(np.eye(4))
            cliff1 = cliff.copy()
            cliff = append_gate(cliff, 'cx', [0, 1])
            cliff = append_gate(cliff, 'cx', [1, 0])
            cliff = append_gate(cliff, 'cx', [0, 1])
            cliff = append_gate(cliff, 'swap', [0, 1])
            self.assertEqual(cliff, cliff1)

        with self.subTest(msg='relation between cx and x'):
            cliff = Clifford(np.eye(4))
            cliff1 = cliff.copy()
            cliff = append_gate(cliff, 'cx', [0, 1])
            cliff = append_gate(cliff, 'x', [0])
            cliff = append_gate(cliff, 'cx', [0, 1])
            cliff = append_gate(cliff, 'x', [0])
            cliff = append_gate(cliff, 'x', [1])
            self.assertEqual(cliff, cliff1)

        with self.subTest(msg='relation between cx and z'):
            cliff = Clifford(np.eye(4))
            cliff1 = cliff.copy()
            cliff = append_gate(cliff, 'cx', [0, 1])
            cliff = append_gate(cliff, 'z', [1])
            cliff = append_gate(cliff, 'cx', [0, 1])
            cliff = append_gate(cliff, 'z', [0])
            cliff = append_gate(cliff, 'z', [1])
            self.assertEqual(cliff, cliff1)

        with self.subTest(msg='relation between cx and s'):
            cliff = Clifford(np.eye(4))
            cliff1 = cliff.copy()
            cliff = append_gate(cliff, 'cx', [1, 0])
            cliff = append_gate(cliff, 'cx', [0, 1])
            cliff = append_gate(cliff, 's', [1])
            cliff = append_gate(cliff, 'cx', [0, 1])
            cliff = append_gate(cliff, 'cx', [1, 0])
            cliff = append_gate(cliff, 'sdg', [0])
            self.assertEqual(cliff, cliff1)


@ddt
class TestCliffordCircuits(QiskitTestCase):
    """Stress tests for random clifford circuits."""

    @combine(gates=[['h', 's'],
                    ['h', 's', 'i', 'x', 'y', 'z'],
                    ['h', 's', 'sdg'],
                    ['h', 's', 'v'],
                    ['h', 's', 'w'],
                    ['h', 's', 'sdg', 'i', 'x', 'y', 'z', 'v', 'w']])
    def test_to_operator_1qubit_gates(self, gates):
        """Test 1-qubit circuit with gates {gates}"""
        samples = 10
        num_gates = 10
        seed = 100
        for i in range(samples):
            circ = random_clifford_circuit(1, num_gates, gates=gates, seed=seed + i)
            value = Clifford(circ).to_operator()
            target = Operator(circ)
            self.assertTrue(target.equiv(value))

    @combine(gates=[['cx'], ['cz'], ['swap'], ['cx', 'cz'],
                    ['cx', 'swap'], ['cz', 'swap'], ['cx', 'cz', 'swap']])
    def test_to_operator_2qubit_gates(self, gates):
        """Test 2-qubit circuit with gates {gates}"""
        samples = 10
        num_gates = 10
        seed = 200
        for i in range(samples):
            circ = random_clifford_circuit(2, num_gates, gates=gates, seed=seed + i)
            value = Clifford(circ).to_operator()
            target = Operator(circ)
            self.assertTrue(target.equiv(value))

    @combine(gates=[['h', 's', 'cx'], ['h', 's', 'cz'], ['h', 's', 'swap'], 'all'],
             num_qubits=[2, 3, 4])
    def test_to_operator_nqubit_gates(self, gates, num_qubits):
        """Test {num_qubits}-qubit circuit with gates {gates}"""
        samples = 10
        num_gates = 20
        seed = 300
        for i in range(samples):
            circ = random_clifford_circuit(num_qubits, num_gates, gates=gates, seed=seed + i)
            value = Clifford(circ).to_operator()
            target = Operator(circ)
            self.assertTrue(target.equiv(value))


class TestCliffordOperators(QiskitTestCase):

    def test_conjugate(self):
        "Test conjugate method"
        samples = 10
        num_gates = 10
        seed = 400
        for num_qubits in [1, 2, 3]:
            if num_qubits == 1:
                gates = '1-qubit'
            else:
                gates = 'all'
            for i in range(samples):
                circ = random_clifford_circuit(num_qubits, num_gates, gates=gates, seed=seed + i)
                value = np.array(Clifford(circ).conjugate().to_matrix()).flatten()
                target = np.array(UnitaryGate(Clifford(circ).to_operator()).conjugate()
                                  .to_matrix()).flatten()
                ratio = target[np.nonzero(target)] / value[np.nonzero(value)]
                self.assertTrue(np.all(ratio == ratio[0]))

    def test_transpose(self):
        "Test transpose method"
        samples = 10
        num_gates = 1
        seed = 400
        for num_qubits in [1, 2, 3]:
            if num_qubits == 1:
                gates = '1-qubit'
            else:
                gates = 'all'
            for i in range(samples):
                circ = random_clifford_circuit(num_qubits, num_gates, gates=gates, seed=seed + i)
                value = np.array(Clifford(circ).transpose().to_matrix()).flatten()
                target = np.array(UnitaryGate(Clifford(circ).to_operator()).transpose()
                                  .to_matrix()).flatten()
                ratio = target[np.nonzero(target)] / value[np.nonzero(value)]
                print(circ)
                print(value)
                print(target)
                print(ratio)
                self.assertTrue(np.all(ratio == ratio[0]))

if __name__ == '__main__':
    unittest.main()
