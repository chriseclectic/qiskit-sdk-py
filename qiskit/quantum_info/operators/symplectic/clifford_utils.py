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

from random import Random
import numpy as np

from .clifford import Clifford
from .clifford_circuits import append_gate
from .stabilizer_table import StabilizerTable
from .symplectic_utils import symplectic


def random_clifford(num_qubits, seed=None):
    """Return a random N-qubit Clifford operator.

    Args:
        num_qubits (int): the numbe of qubits for the Clifford.
        seed (int): Optional. To set a random seed.

    Returns:
        Clifford: the generated N-qubit clifford operator.

    Reference:
        1. R. Koenig, J.A. Smolin. *How to efficiently select an arbitrary
           Clifford group element*. J. Math. Phys. 55, 122202 (2014).
           `arXiv:1406.2170 [quant-ph] <https://arxiv.org/abs/1406.2170>`_
    """
    # Random number generator
    # We need to use Python random module instead of Numpy.random
    # as we are generating bigints
    rng = Random()
    rng.seed(seed)

    # The algorithm from Ref 1. generates a random Clifford by generating
    # a random symplectic matrix for the Clifford array, and a random
    # symplectic Pauli vector for the Phase.

    # Geneate random phase vector
    phase = np.array(
        [rng.randint(0, 1) for _ in range(2 * num_qubits)], dtype=np.bool)

    # Compute size of N-qubit sympletic group
    # this number will be a bigint if num_qubits > 5
    size = pow(2, num_qubits ** 2)
    for i in range(1, num_qubits+1):
        size *= pow(4, i) - 1

    # Sample a group element by index
    rint = rng.randrange(size)

    # Generate random element of symplectic group
    # TODO: Code needs to be optimized

    symp = symplectic(rint, num_qubits)
    symp2 = np.zeros([2 * num_qubits, 2 * num_qubits], dtype=np.uint8)
    symp3 = np.zeros([2 * num_qubits, 2 * num_qubits], dtype=np.uint8)

    # these interchange rows and columns because the random symplectic code
    #  uses a different convention
    for i in range(num_qubits):
        symp2[i] = symp[2 * i]
        symp2[i + num_qubits] = symp[2 * i + 1]
    for i in range(num_qubits):
        symp3[:, i] = symp2[:, 2 * i]
        symp3[:, i + num_qubits] = symp2[:, 2 * i + 1]

    return Clifford(StabilizerTable(symp3, phase))


def append_gate_list(gate_type, qubits, gate_index, gatelist):
    if gate_type == 'pauli':
        if gate_index == 1:
            gatelist.append('z ' + str(qubits[0]))
        if gate_index == 2:
            gatelist.append('x ' + str(qubits[0]))
        if gate_index == 3:
            gatelist.append('y ' + str(qubits[0]))
    if gate_type == 'hadamard':
        if gate_index == 1:
            gatelist.append('h ' + str(qubits[0]))
    if gate_type == 'rotation':
        if gate_index == 1:
            gatelist.append('v ' + str(qubits[0]))
        if gate_index == 2:
            gatelist.append('w ' + str(qubits[0]))
    if gate_type == 'cnot':
        gatelist.append('cx ' + str(qubits[0]) + ' ' + str(qubits[1]))

def clifford1_gates(idx: int):
    """
    Make a single qubit Clifford gate.
    Args:
        idx: the index (modulo 24) of a single qubit
                Clifford.
    Returns:
        A single qubit Clifford gate
    """

    gatelist = []
    # Cannonical Ordering of Cliffords 0,...,23
    cannonicalorder = idx % 24
    pauli = np.mod(cannonicalorder, 4)
    rotation = np.mod(cannonicalorder // 4, 3)
    hadamard = np.mod(cannonicalorder // 12, 2)

    append_gate_list("hadamard", [0], hadamard, gatelist)
    append_gate_list("rotation", [0], rotation, gatelist)
    append_gate_list("pauli", [0], pauli, gatelist)

    return gatelist


def clifford2_gates(idx: int):
    """
    Make a 2-qubit Clifford gate.
    Args:
        idx: the index (modulo 11520) of a two-qubit
            Clifford.
    Returns:
        A 2-qubit Clifford gate.
    """

    gatelist = []
    cannon = idx % 11520

    pauli = np.mod(cannon, 16)
    symp = cannon // 16

    if symp < 36:  # 1-qubit Cliffords Class
        r0 = np.mod(symp, 3)
        r1 = np.mod(symp // 3, 3)
        h0 = np.mod(symp // 9, 2)
        h1 = np.mod(symp // 18, 2)

        append_gate_list("hadamard", [0], h0, gatelist)
        append_gate_list("hadamard", [1], h1, gatelist)
        append_gate_list("rotation", [0], r0, gatelist)
        append_gate_list("rotation", [1], r1, gatelist)

    elif symp < 360:  # CNOT-like Class
        symp = symp - 36
        r0 = np.mod(symp, 3)
        r1 = np.mod(symp // 3, 3)
        r2 = np.mod(symp // 9, 3)
        r3 = np.mod(symp // 27, 3)
        h0 = np.mod(symp // 81, 2)
        h1 = np.mod(symp // 162, 2)

        append_gate_list("hadamard", [0], h0, gatelist)
        append_gate_list("hadamard", [1], h1, gatelist)
        append_gate_list("rotation", [0], r0, gatelist)
        append_gate_list("rotation", [1], r1, gatelist)
        append_gate_list("cnot", [0, 1], None, gatelist)
        append_gate_list("rotation", [0], r2, gatelist)
        append_gate_list("rotation", [1], r3, gatelist)

    elif symp < 684:  # iSWAP-like Class
        symp = symp - 360
        r0 = np.mod(symp, 3)
        r1 = np.mod(symp // 3, 3)
        r2 = np.mod(symp // 9, 3)
        r3 = np.mod(symp // 27, 3)
        h0 = np.mod(symp // 81, 2)
        h1 = np.mod(symp // 162, 2)

        append_gate_list("hadamard", [0], h0, gatelist)
        append_gate_list("hadamard", [1], h1, gatelist)
        append_gate_list("rotation", [0], r0, gatelist)
        append_gate_list("rotation", [1], r1, gatelist)
        append_gate_list("cnot", [0, 1], None, gatelist)
        append_gate_list("cnot", [1, 0], None, gatelist)
        append_gate_list("rotation", [0], r2, gatelist)
        append_gate_list("rotation", [1], r3, gatelist)

    else:  # SWAP Class
        symp = symp - 684
        r0 = np.mod(symp, 3)
        r1 = np.mod(symp // 3, 3)
        h0 = np.mod(symp // 9, 2)
        h1 = np.mod(symp // 18, 2)

        append_gate_list("hadamard", [0], h0, gatelist)
        append_gate_list("hadamard", [1], h1, gatelist)
        append_gate_list("rotation", [0], r0, gatelist)
        append_gate_list("rotation", [1], r1, gatelist)
        append_gate_list("cnot", [0, 1], None, gatelist)
        append_gate_list("cnot", [1, 0], None, gatelist)
        append_gate_list("cnot", [0, 1], None, gatelist)

    append_gate_list("pauli", [0],  np.mod(pauli, 4), gatelist)
    append_gate_list("pauli", [1], pauli // 4, gatelist)

    return gatelist

