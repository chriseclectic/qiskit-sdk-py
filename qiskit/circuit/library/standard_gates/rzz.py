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

"""Two-qubit ZZ-rotation gate."""

import numpy as np

from qiskit.circuit.gate import Gate
from qiskit.circuit.quantumregister import QuantumRegister


class RZZGate(Gate):
    r"""A parameteric 2-qubit :math:`Z \otimes Z` interaction (rotation about ZZ).

    This gate is symmetric, and is maximally entangling at :math:`\theta = \pi/2`.

    **Circuit Symbol:**

    .. parsed-literal::

        q_0: ───■────
                │zz(θ)
        q_1: ───■────

    **Matrix Representation:**

    .. math::

        \newcommand{\th}{\frac{\theta}{2}}

        R_{ZZ}(\theta) = exp(-i \th Z{\otimes}Z) =
            \begin{pmatrix}
                e^{-i \th} & 0 & 0 & 0 \\
                0 & e^{i \th} & 0 & 0 \\
                0 & 0 & e^{i \th} & 0 \\
                0 & 0 & 0 & e^{-i \th}
            \end{pmatrix}

    This is a direct sum of RZ rotations, so this gate is equivalent to a
    uniformly controlled (multiplexed) RZ gate:

    .. math::

        R_{ZZ}(\theta) =
            \begin{pmatrix}
                RZ(\theta) & 0 \\
                0 & RZ(-\theta)
            \end{pmatrix}

    **Examples:**

        .. math::

            R_{ZZ}(\theta = 0) = I

        .. math::

            R_{ZZ}(\theta = 2\pi) = -I

        .. math::

            R_{ZZ}(\theta = \pi) = - Z \otimes Z

        .. math::

            R_{ZZ}(\theta = \frac{\pi}{2}) = \frac{1}{\sqrt{2}}
                                    \begin{pmatrix}
                                        1-i & 0 & 0 & 0 \\
                                        0 & 1+i & 0 & 0 \\
                                        0 & 0 & 1+i & 0 \\
                                        0 & 0 & 0 & 1-i
                                    \end{pmatrix}
    """

    def __init__(self, theta, phase=0):
        """Create new RZZ gate."""
        super().__init__('rzz', 2, [theta], phase=phase)

    def _define(self):
        """
        gate rzz(theta) a, b { cx a, b; u1(theta) b; cx a, b; }
        """
        from .rz import RZGate
        from .x import CXGate
        q = QuantumRegister(2, 'q')
        self.definition = [
            (CXGate(), [q[0], q[1]], []),
            (RZGate(self.params[0], phase=self.phase), [q[1]], []),
            (CXGate(), [q[0], q[1]], [])
        ]

    def inverse(self):
        """Return inverse RZZ gate (i.e. with the negative rotation angle)."""
        return RZZGate(-self.params[0], phase=-self.phase)

    def _matrix_definition(self):
        """Return a numpy.array for the RZZ gate."""
        theta = float(self.params[0])
        return np.array([[np.exp(-1j*theta/2), 0, 0, 0],
                         [0, np.exp(1j*theta/2), 0, 0],
                         [0, 0, np.exp(1j*theta/2), 0],
                         [0, 0, 0, np.exp(-1j*theta/2)]], dtype=complex)
