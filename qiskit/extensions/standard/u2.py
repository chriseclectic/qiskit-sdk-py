# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""
One-pulse single-qubit gate.
"""
import numpy
from qiskit.circuit import Gate
from qiskit.circuit import QuantumCircuit
from qiskit.circuit import QuantumRegister
from qiskit.qasm import pi
from qiskit.extensions.standard.u3 import U3Gate


class U2Gate(Gate):
    r"""One-pulse single-qubit gate.

    **Matrix Definition**

    The matrix for this gate is given by:

    .. math::

        U_2(\phi, lambda) = \frac{1}{\sqrt{2}}\begin{bmatrix}
            1 & -e^{i \lambda} \\
            e^{i \phi} & e^{i (phi+\lambda)}
            \end{bmatrix}
    """

    def __init__(self, phi, lam, phase_angle=0, label=None):
        """Create new one-pulse single-qubit gate."""
        super().__init__("u2", 1, [phi, lam],
                         phase_angle=phase_angle, label=label)

    def _define(self):
        q = QuantumRegister(1, "q")
        self.definition = [
            (U3Gate(pi / 2, self.params[0], self.params[1],
             phase_angle=self.phase_angle), [q[0]], [])
        ]

    def inverse(self):
        """Invert this gate.

        u2(phi,lamb)^dagger = u2(-lamb-pi,-phi+pi)
        """
        return U2Gate(-self.params[1] - pi, -self.params[0] + pi,
                      phase_angle=-self.phase_angle)

    def _matrix_definition(self):
        """Return a Numpy.array for the U3 gate."""
        isqrt2 = 1 / numpy.sqrt(2)
        phi, lam = self.params
        phi, lam = float(phi), float(lam)
        return numpy.array([[isqrt2, -numpy.exp(1j * lam) * isqrt2],
                            [
                                numpy.exp(1j * phi) * isqrt2,
                                numpy.exp(1j * (phi + lam)) * isqrt2
                            ]],
                           dtype=complex)


def u2(self, phi, lam, q):  # pylint: disable=invalid-name
    """Apply u2 to q."""
    return self.append(U2Gate(phi, lam), [q], [])


QuantumCircuit.u2 = u2
