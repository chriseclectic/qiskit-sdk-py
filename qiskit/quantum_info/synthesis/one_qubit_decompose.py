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

# pylint: disable=invalid-name
"""
Decompose a single-qubit unitary via Euler angles.
"""

import math
import numpy as np
import scipy.linalg as la

from qiskit.circuit.quantumcircuit import QuantumCircuit
from qiskit.extensions.standard import (U3Gate, U1Gate, RXGate,
                                        RYGate, RZGate, RGate)
from qiskit.exceptions import QiskitError
from qiskit.quantum_info.operators import Operator
from qiskit.quantum_info.operators.predicates import is_unitary_matrix

DEFAULT_ATOL = 1e-12


class OneQubitEulerDecomposer:
    r"""A class for decomposing 1-qubit unitaries into Euler angle rotations.

    The resulting decomposition is parameterized by 3 Euler rotation angle
    parameters :math:`(\theta, \phi\ lambda)`, and a phase parameter
    :math:`\gamma`. The value of the parameters for an input unitary depends
    on the decomposition basis. Allowed bases and the resulting circuits are
    shown in the following table. Note that for the non-Euler bases (U3, U1X,
    RR), the ZYZ euler parameters are used.

    .. list-table:: Supported circuit bases
        :widths: auto
        :header-rows: 1

        * - Basis
          - Euler Angle Basis
          - Decomposition Circuit
        * - 'ZYZ'
          - :math:`Z(\phi) Y(\theta) Z(\lambda)`
          - :math:`e^{i\gamma} R_Z(\phi).R_Y(\theta).R_Z(\lambda)`
        * - 'ZXZ'
          - :math:`Z(\phi) X(\theta) Z(\lambda)`
          - :math:`e^{i\gamma} R_Z(\phi).R_X(\theta).R_Z(\lambda)`
        * - 'XYX'
          - :math:`X(\phi) Y(\theta) X(\lambda)`
          - :math:`e^{i\gamma} R_X(\phi).R_Y(\theta).R_X(\lambda)`
        * - 'U3'
          - :math:`Z(\phi) Y(\theta) Z(\lambda)`
          - :math:`e^{i\left(\gamma-\left\frac{\phi+\lambda}{2}\right)\right)}`
            :math:`U_3(\theta,\phi,\lambda)`
        * - 'U1X'
          - :math:`Z(\phi) Y(\theta) Z(\lambda)`
          - :math:`e^{i\left(\gamma-\frac{\theta+\phi+\lambda}{2}\right)\right)}
            :math:`U_1(\phi+\pi).R_X\left(\frac{\pi}{2}\right).U_1(\theta+\pi).`
            :math:`R_X\left(\frac{\pi}{2}\right).U_1(\lambda)`
        * - 'RR'
          - :math:`Z(\phi) Y(\theta) Z(\lambda)`
          - :math:`e^{i\gamma} R\left(-\pi,\frac{\phi-\lambda+\pi}{2}\right).`
            :math:`R\left(\theta+\pi,\frac{\pi}{2}-\lambda\right)`
    """

    def __init__(self, basis='U3'):
        """Initialize decomposer

        Supported bases are: 'U3', 'U1X', 'RR', 'ZYZ', 'ZXZ', 'XYX'.

        Args:
            basis (str): the decomposition basis [Default: 'U3]

        Raises:
            QiskitError: If input basis is not recognized.
        """
        basis_methods = {
            'U3': (self._angles_zyz, self._circuit_u3),
            'U1X': (self._angles_zyz, self._circuit_u1x),
            'RR': (self._angles_zyz, self._circuit_u1x),
            'ZYZ': (self._angles_zyz, self._circuit_zyz),
            'ZXZ': (self._angles_zxz, self._circuit_zxz),
            'XYX': (self._angles_xyx, self._circuit_xyx)
        }
        if basis not in basis_methods:
            raise QiskitError("OneQubitEulerDecomposer: unsupported basis")
        self._basis = basis
        self._angles, self._circuit = basis_methods[self._basis]

    def __call__(self,
                 unitary,
                 simplify=True,
                 phase_equal=True,
                 atol=DEFAULT_ATOL):
        """Decompose single qubit gate into a basis circuit.

        Args:
            unitary (Operator or Gate or array): 1-qubit unitary matrix
            simplify (bool): remove zero-angle rotations [Default: True].
            phase_equal (bool): verify the output circuit is phase equal
                                to the input matrix [Default: True].
            atol (float): absolute tolerance for checking angles zero.

        Returns:
            QuantumCircuit: the decomposed single-qubit gate circuit

        Raises:
            QiskitError: if input is invalid or synthesis fails.
        """
        if hasattr(unitary, 'to_operator'):
            # If input is a BaseOperator subclass this attempts to convert
            # the object to an Operator so that we can extract the underlying
            # numpy matrix from `Operator.data`.
            unitary = unitary.to_operator().data
        elif hasattr(unitary, 'to_matrix'):
            # If input is Gate subclass or some other class object that has
            # a to_matrix method this will call that method.
            unitary = unitary.to_matrix()
        # Convert to numpy array incase not already an array
        unitary = np.asarray(unitary, dtype=complex)

        # Check input is a 2-qubit unitary
        if unitary.shape != (2, 2):
            raise QiskitError("OneQubitEulerDecomposer: "
                              "expected 2x2 input matrix")
        if not is_unitary_matrix(unitary):
            raise QiskitError("OneQubitEulerDecomposer: "
                              "input matrix is not unitary.")
        theta, phi, lam, phase = self._angles(unitary)
        circuit = self._circuit(theta, phi, lam, phase,
                                simplify=simplify, atol=atol)
        # Check circuit is correct
        self.check_equiv(unitary, circuit, phase_equal=phase_equal)
        return circuit

    @property
    def basis(self):
        """The decomposition basis."""
        return self._basis

    def angles(self, unitary):
        """Return the Euler angles and phase for input array.

        Args:
            unitary (np.ndarray): 2x2 unitary matrix.

        Returns:
            tuple: (theta, phi, lambda, phase).
        """
        return self._angles(unitary)

    def circuit(self, theta, phi, lam, phase=0, simplify=True,
                atol=DEFAULT_ATOL):
        """Return the basis circuit for the input parameters.

        Args:
            theta (float): euler angle parameter
            phi (float): euler angle parameter
            lam (float): euler angle parameter
            phase (float): phase parameter [Default: 0]
            simplify (bool): simplify output circuit [Default: True]
            atol (float): absolute tolerance for checking angles zero
                          [Default: 1e-12].

        Returns:
            QuantumCircuit: the basis circuits.
        """
        return self._circuit(theta, phi, lam, phase=phase,
                             simplify=simplify, atol=atol)

    @staticmethod
    def check_equiv(unitary, circuit, phase_equal=True):
        """Check a circuit is equivalent to a unitary.

        Args:
            unitary (Operator or Gate or array): unitary operator.
            circuit (QuantumCircuit or Instruction): decomposition circuit.
            phase_equal (bool): require the decomposition to be global phase
                                equal [Default: True]
        
        Raises:
            QiskitError: if the input unitary and circuit are not equivalent.
        """
        # NOTE: this function isn't specific to this class so could be
        # moved to another location for more general use.
        if phase_equal and not Operator(circuit) == Operator(unitary):
            raise QiskitError(
                "Phase equal circuit synthesis failed within required accuracy.")
        if not phase_equal and not Operator(circuit).equiv(
                Operator(unitary)):
            raise QiskitError("Circuit synthesis failed within required accuracy.")

    @staticmethod
    def _angles_zyz(unitary_mat):
        """Return euler angles for a unitary matrix in ZYZ basis.

        In this representation U = exp(1j * phase) * Rz(phi).Ry(theta).Rz(lam)
        """
        # We rescale the input matrix to be special unitary (det(U) = 1)
        # This ensures that the quaternion representation is real
        coeff = la.det(unitary_mat)**(-0.5)
        phase = -np.angle(coeff)
        U = coeff * unitary_mat  # U in SU(2)
        # OpenQASM SU(2) parameterization:
        # U[0, 0] = exp(-i(phi+lambda)/2) * cos(theta/2)
        # U[0, 1] = -exp(-i(phi-lambda)/2) * sin(theta/2)
        # U[1, 0] = exp(i(phi-lambda)/2) * sin(theta/2)
        # U[1, 1] = exp(i(phi+lambda)/2) * cos(theta/2)
        theta = 2 * math.atan2(abs(U[1, 0]), abs(U[0, 0]))
        phiplambda = 2 * np.angle(U[1, 1])
        phimlambda = 2 * np.angle(U[1, 0])
        phi = (phiplambda + phimlambda) / 2.0
        lam = (phiplambda - phimlambda) / 2.0
        return theta, phi, lam, phase

    @staticmethod
    def _angles_zxz(unitary_mat):
        """Return euler angles for special unitary matrix in ZXZ basis.

        In this representation U = exp(1j * phase) * Rz(phi).Rx(theta).Rz(lam)
        """
        theta, phi, lam , phase = OneQubitEulerDecomposer._angles_zyz(unitary_mat)
        return theta, phi + np.pi / 2, lam - np.pi / 2, phase

    @staticmethod
    def _angles_xyx(mat):
        """Return Euler angles for a unitary matrix in XYX basis.

        In this representation U = exp(1j * phase) * Rx(phi).Ry(theta).Rx(lam)
        """
        # We use the fact that
        # Rx(a).Ry(b).Rx(c) = H.Rz(a).Ry(-b).Rz(c).H
        mat_zyz = 0.5 * np.array([
            [mat[0, 0] + mat[0, 1] + mat[1, 0] + mat[1, 1], 
             mat[0, 0] - mat[0, 1] + mat[1, 0] - mat[1, 1]],
            [mat[0, 0] + mat[0, 1] - mat[1, 0] - mat[1, 1], 
             mat[0, 0] - mat[0, 1] - mat[1, 0] + mat[1, 1]]], dtype=complex)
        theta, phi, lam, phase = OneQubitEulerDecomposer._angles_zyz(mat_zyz)
        return -theta, phi, lam, phase

    @staticmethod
    def _circuit_zyz(theta,
                     phi,
                     lam,
                     phase=0,
                     simplify=True,
                     atol=DEFAULT_ATOL):
        circuit = QuantumCircuit(1)
        if simplify and np.isclose(theta, 0.0, atol=atol):
            circuit.append(RZGate(phi + lam, phase=phase), [0])
            return circuit
        if not simplify or not np.isclose(lam, 0.0, atol=atol):
            circuit.append(RZGate(lam), [0])
        if not simplify or not np.isclose(theta, 0.0, atol=atol):
            circuit.append(RYGate(theta, phase=phase), [0])
        if not simplify or not np.isclose(phi, 0.0, atol=atol):
            circuit.append(RZGate(phi), [0])
        return circuit

    @staticmethod
    def _circuit_u3(theta, phi, lam, phase=0,
                    simplify=True,
                    atol=DEFAULT_ATOL):
        # pylint: disable=unused-argument

        # The determinant of U3 gate depends on its params
        # via det(u3(theta, phi, lam)) = exp(1j*(phi+lam))
        # Since the phase is wrt to a SU matrix we must rescale
        # phase to correct this
        phase = phase - 0.5 * (phi + lam)
        circuit = QuantumCircuit(1)
        circuit.append(U3Gate(theta, phi, lam, phase=phase), [0])
        return circuit

    @staticmethod
    def _circuit_u1x(theta,
                     phi,
                     lam,
                     phase=0,
                     simplify=True,
                     atol=DEFAULT_ATOL):
        # The determinant of this decomposition depends on its params
        # Since the phase is wrt to a SU matrix we must rescale
        # phase to correct this

        # Check for U1 and U2 decompositions into minimimal
        # required X90 pulses
        if simplify and np.allclose([theta, phi], [0., 0.], atol=atol):
            # zero X90 gate decomposition
            phase = phase - 0.5 * lam
            circuit = QuantumCircuit(1)
            circuit.append(U1Gate(lam, phase=phase), [0])
            return circuit
        if simplify and np.isclose(theta, np.pi / 2, atol=atol):
            # single X90 gate decomposition
            phase = phase - 0.5 * (phi + lam)
            circuit = QuantumCircuit(1)
            circuit.append(U1Gate(lam - np.pi / 2), [0])
            circuit.append(RXGate(np.pi / 2, phase=phase), [0])
            circuit.append(U1Gate(phi + np.pi / 2), [0])
            return circuit
        # General two-X90 gate decomposition
        phase = phase - 0.5 * (theta + phi + lam)
        circuit = QuantumCircuit(1)
        circuit.append(U1Gate(lam), [0])
        circuit.append(RXGate(np.pi / 2, phase=phase), [0])
        circuit.append(U1Gate(theta + np.pi), [0])
        circuit.append(RXGate(np.pi / 2), [0])
        circuit.append(U1Gate(phi + np.pi), [0])
        return circuit

    @staticmethod
    def _circuit_rr(theta,
                     phi,
                     lam,
                     phase=0,
                     simplify=True,
                     atol=DEFAULT_ATOL):
        circuit = QuantumCircuit(1)
        if not simplify or not (np.isclose(abs(theta), np.pi, atol=atol)):
            circuit.append(RGate(theta + np.pi, np.pi / 2 - lam), [0])
        circuit.append(RGate(-np.pi, 0.5 * (phi - lam + np.pi), phase=phase), [0])
        return circuit

    @staticmethod
    def _circuit_zxz(theta,
                     phi,
                     lam,
                     phase=0,
                     simplify=False,
                     atol=DEFAULT_ATOL):
        if simplify and np.isclose(theta, 0.0, atol=atol):
            circuit = QuantumCircuit(1)
            circuit.append(RZGate(phi + lam, phase=phase), [0])
            return circuit
        circuit = QuantumCircuit(1)
        if not simplify or not np.isclose(lam, 0.0, atol=atol):
            circuit.append(RZGate(lam), [0])
        if not simplify or not np.isclose(theta, 0.0, atol=atol):
            circuit.append(RXGate(theta, phase=phase), [0])
        if not simplify or not np.isclose(phi, 0.0, atol=atol):
            circuit.append(RZGate(phi), [0])
        return circuit

    @staticmethod
    def _circuit_xyx(theta,
                     phi,
                     lam,
                     phase=0,
                     simplify=True,
                     atol=DEFAULT_ATOL):
        circuit = QuantumCircuit(1)
        if simplify and np.isclose(theta, 0.0, atol=atol):
            circuit.append(RXGate(phi + lam, phase=phase), [0])
            return circuit
        if not simplify or not np.isclose(lam, 0.0, atol=atol):
            circuit.append(RXGate(lam), [0])
        if not simplify or not np.isclose(theta, 0.0, atol=atol):
            circuit.append(RYGate(theta, phase=phase), [0])
        if not simplify or not np.isclose(phi, 0.0, atol=atol):
            circuit.append(RXGate(phi), [0])
        return circuit
