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
Identity gate.
"""
import warnings
# pylint: disable=unused-import
from qiskit.extensions.standard.i import IdGate, iden
    r"""Identity gate.

    Identity gate corresponds to a single-qubit gate wait cycle,
    and should not be optimized or unrolled (it is an opaque gate).

    **Matrix Definition**

    The matrix for this gate is given by:

    .. math::

        U_{\text{I}} =
            \begin{bmatrix}
                1 & 0 \\
                0 & 1
            \end{bmatrix}
    """

    def __init__(self, phase=0, label=None):
        """Create new Identity gate."""
        super().__init__("id", 1, [], phase=phase, label=label)

    def inverse(self):
        """Invert this gate."""
        return IdGate(phase=-self.phase)  # self-inverse

    def _matrix_definition(self):
        """Return a Numpy.array for the Id gate."""
        return numpy.array([[1, 0],
                            [0, 1]], dtype=complex)


@deprecate_arguments({'q': 'qubit'})
def iden(self, qubit, *, q=None):  # pylint: disable=unused-argument
    """Apply Identity to to a specified qubit (qubit).

    The Identity gate ensures that nothing is applied to a qubit for one unit
    of gate time. It leaves the quantum states |0> and |1> unchanged.
    The Identity gate should not be optimized or unrolled (it is an opaque gate).

    Examples:

        Circuit Representation:

        .. jupyter-execute::

            from qiskit import QuantumCircuit

            circuit = QuantumCircuit(1)
            circuit.iden(0)
            circuit.draw()

        Matrix Representation:

        .. jupyter-execute::

            from qiskit.extensions.standard.iden import IdGate
            IdGate().to_matrix()
    """
    return self.append(IdGate(), [qubit], [])


warnings.warn('This module is deprecated. The IdGate can now be found in i.py',
              category=DeprecationWarning, stacklevel=2)
