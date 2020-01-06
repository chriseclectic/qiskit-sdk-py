# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2019.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""
Two-qubit XX-rotation gate.
"""
import numpy as np
from qiskit.circuit import Gate
from qiskit.circuit import QuantumCircuit
from qiskit.circuit import QuantumRegister
from qiskit.extensions.standard.cx import CnotGate
from qiskit.extensions.standard.rz import RZGate
from qiskit.extensions.standard.u2 import U2Gate
from qiskit.extensions.standard.u3 import U3Gate
from qiskit.extensions.standard.h import HGate


class RXXGate(Gate):
    r"""Two-qubit XX-rotation gate.

    **Matrix Definition**

    The matrix for this gate is given by:

    .. math::

        U_{\text{RZ}}(\theta)
            = \exp\left(-i \frac{\theta}{2}
                        (\sigma_X\otimes\sigma_X) \right)
            = \begin{bmatrix}
                \cos(\theta / 2) & 0 & 0 & -i \sin(\theta / 2) \\
                0 & \cos(\theta / 2) & -i \sin(\theta / 2) & 0 \\
                0 & -i \sin(\theta / 2) & \cos(\theta / 2) & 0 \\
                -i \sin(\theta / 2) & 0 & 0 & \cos(\theta / 2)
            \end{bmatrix}
    """

    def __init__(self, theta, phase=0, label=None):
        """Create new rxx gate."""
        super().__init__("rxx", 2, [theta],
                         phase=phase, label=label)

    def _define(self):
        """Calculate a subcircuit that implements this unitary."""
        definition = []
        q = QuantumRegister(2, "q")
        theta = self.params[0]
        rule = [
            (U3Gate(np.pi / 2, theta, 0), [q[0]], []),
            (HGate(), [q[1]], []),
            (CnotGate(), [q[0], q[1]], []),
            (RZGate(-theta, phase=self.phase), [q[1]], []),
            (CnotGate(), [q[0], q[1]], []),
            (HGate(), [q[1]], []),
            (U2Gate(-np.pi, np.pi - theta), [q[0]], []),
        ]
        for inst in rule:
            definition.append(inst)
        self.definition = definition

    def inverse(self):
        """Invert this gate."""
        return RXXGate(-self.params[0], phase=-self.phase)

    def _matrix_definition(self):
        """Return a Numpy.array for the RXX gate."""
        theta = float(self.params[0])
        return np.array([
            [np.cos(theta / 2), 0, 0, -1j * np.sin(theta / 2)],
            [0, np.cos(theta / 2), -1j * np.sin(theta / 2), 0],
            [0, -1j * np.sin(theta / 2), np.cos(theta / 2), 0],
            [-1j * np.sin(theta / 2), 0, 0, np.cos(theta / 2)]], dtype=complex)


def rxx(self, theta, qubit1, qubit2):
    """Apply RXX to circuit."""
    return self.append(RXXGate(theta), [qubit1, qubit2], [])


# Add to QuantumCircuit class
QuantumCircuit.rxx = rxx
