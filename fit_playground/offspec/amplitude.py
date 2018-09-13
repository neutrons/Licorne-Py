#pylint: disable=too-many-branches, too-many-lines, line-too-long
"""
    Transcription into code of Toperverg off-specular write-up.
    Implementation note:
        At this point we are not trying to be clever. We just want a quick
        run-through to understand what comes out and catch inconsistencies.
"""
import numpy as np
from numpy import linalg


class Layer(object):
    """
        Sample layer
    """
    thickness = 100
    rho = 1
    irho = 0
    mrho = 0
    gamma = 0
    beta = 0
    cos_delta_gamma = 0
    sin_delta_gamma = 0
    roughness = 0

    p_i_plus = None
    p_i_minus = None
    phi_i_plus = None
    phi_i_minus = None
    e_i_plus = None
    e_i_minus = None
    b = None

    # Debye-Waller (roughness) matrices
    w_ir = None
    w_it = None

    def initialize(self, n_alpha_i, n_wl):
        self.p_i_plus = np.zeros([n_alpha_i, n_wl])
        self.p_i_minus = np.zeros([n_alpha_i, n_wl])
        self.phi_i_plus = np.zeros([n_alpha_i, n_wl])
        self.phi_i_minus = np.zeros([n_alpha_i, n_wl])
        self.e_i_plus = np.zeros([n_alpha_i, n_wl])
        self.e_i_minus = np.zeros([n_alpha_i, n_wl])
        self.b = np.zeros(3)
        self.p_i_matrix = n_alpha_i*[n_wl*[0]]
        self.e_i_matrix = n_alpha_i*[n_wl*[0]]

    def rho_plus(self):
        # 1.5
        return self.rho - 1j*self.irho - self.mrho

    def rho_minus(self):
        # 1.5
        return self.rho - 1j*self.irho + self.mrho

    def p_c_plus_sq(self):
        # 1.6
        return 4.0 * np.pi * self.rho - 1j*self.irho - self.mrho

    def p_c_minus_sq(self):
        # 1.6
        return 4.0 * np.pi * self.rho - 1j*self.irho + self.mrho


class Amplitude(object):
    """ Scattering amplitude """
    wl_min = 1
    wl_max = 10
    n_wl = 10

    alpha_i_min = .005
    alpha_i_max = 5
    n_alpha_i = 10

    def __init__(self):
        # Ordered list of layers
        self.layers = []

        _p_i0 = np.zeros([self.n_alpha_i, self.n_wl])
        for i, layer in enumerate(self.layers):
            layer.initialize(self.n_alpha_i, self.n_wl)

        # 1.8
        for i_wl in range(self.n_wl):
            _wl = self.wl_min + i_wl * (self.wl_max - self.wl_min) / (self.n_wl - 1)

            # 1.9
            for i_alpha_i in range(self.n_alpha_i):
                # 1.10
                _alpha_i = self.alpha_i_min + i_alpha_i * (self.alpha_i_max - self.alpha_i_min) / (self.n_alpha_i - 1)
                # 1.11
                _p_i0[i_alpha_i][i_wl] = 2.0 * np.pi * np.sin(_alpha_i / _wl)

                for i, layer in enumerate(self.layers):
                    # 1.12
                    layer.p_i_plus[i_alpha_i][i_wl] = np.sqrt(_p_i0[i_alpha_i][i_wl]**2 - layer.p_c_plus_sq())
                    layer.p_i_minus[i_alpha_i][i_wl] = np.sqrt(_p_i0[i_alpha_i][i_wl]**2 - layer.p_c_minus_sq())

                    # 1.13
                    layer.phi_i_plus[i_alpha_i][i_wl] = layer.p_i_plus[i_alpha_i][i_wl] * layer.thickness
                    layer.phi_i_minus[i_alpha_i][i_wl] = layer.p_i_minus[i_alpha_i][i_wl] * layer.thickness

                    # 1.14
                    layer.e_i_plus[i_alpha_i][i_wl] = np.exp(1j * layer.phi_i_plus[i_alpha_i][i_wl])
                    layer.e_i_minus[i_alpha_i][i_wl] = np.exp(1j * layer.phi_i_minus[i_alpha_i][i_wl])

                    # 1.15, 1.16
                    p_i = build_spin_matrix(layer.p_i_plus[i_alpha_i][i_wl], layer.p_i_minus[i_alpha_i][i_wl], layer.b)

                    # 1.17 - invert p_i
                    p_i_inv = linalg.inv(p_i)

                    # For some reason the p matrices are defined with a factor 1/2
                    p_i = p_i / 2.0
                    p_i_inv = p_i_inv / 2.0
                    layer.p_i_matrix[i_alpha_i][i_wl] = p_i

                    # 1.18, 1.19
                    e_i = build_spin_matrix(layer.e_i_plus[i_alpha_i][i_wl], layer.e_i_minus[i_alpha_i][i_wl], layer.b)
                    layer.e_i_matrix[i_alpha_i][i_wl] = e_i

                    # 1.20, 1.21 -  Roughness
                    # Here we should be careful with the first and last layer
                    # For the reflected component, skip the last layer
                    if i < len(self.layers) - 2:
                        w_ir = 2.0 * self.layers[i+1].roughness**2 * np.cross(p_i, self.layers[i+1].p_i_matrix[i_alpha_i][i_wl])
                    # For the transmission component, skip the first layer
                    if i > 0:
                        w_it = 0.5 * layer.roughness**2 * (self.layers[i-1].p_i_matrix[i_alpha_i][i_wl] - p_i)**2

                    # 1.22 - Roughness eigenvalues
                    w_ir_plus = 0.5 * ((w_ir[0][0] + w_ir[1][1]) + np.sqrt((w_ir[0][0] - w_ir[1][1])**2 + 4.0 * w_ir[0][1] * w_ir[1][0]))
                    w_ir_minus = 0.5 * ((w_ir[0][0] + w_ir[1][1]) - np.sqrt((w_ir[0][0] - w_ir[1][1])**2 + 4.0 * w_ir[0][1] * w_ir[1][0]))
                    w_it_plus = 0.5 * ((w_it[0][0] + w_it[1][1]) + np.sqrt((w_it[0][0] - w_it[1][1])**2 + 4.0 * w_it[0][1] * w_it[1][0]))
                    w_it_minus = 0.5 * ((w_it[0][0] + w_it[1][1]) - np.sqrt((w_it[0][0] - w_it[1][1])**2 + 4.0 * w_it[0][1] * w_it[1][0]))

                    # 1.23 Would be nice to have this in matrix notation
                    b_i_r = np.zeros(3)
                    b_i_r[0] = w_ir[0][0] - w_ir[1][1]
                    b_i_r[1] = w_ir[0][1] + w_ir[1][0]
                    b_i_r[2] = 1j * w_ir[0][1] - w_ir[1][0]
                    b_i_r = b_i_r / (w_ir_plus - w_ir_minus)

                    b_i_t = np.zeros(3)
                    b_i_t[0] = w_it[0][0] - w_it[1][1]
                    b_i_t[1] = w_it[0][1] + w_it[1][0]
                    b_i_t[2] = 1j * w_it[0][1] - w_it[1][0]
                    b_i_t = b_i_t / (w_it_plus - w_it_minus)

                    # 1.24 Eigenvalues of D-W exponents


def build_spin_matrix(p_plus, p_minus, b_vector):
    """
        Build a spin matrix based on the given components and Pauli matrices.
        #TODO: This probably simplifies to something obvious.
        This appears in 1.15, 1.18
    """
    p_matrix = np.zeros([2,2])
    p_matrix[0][0] = p_plus * (1 + b_vector[0]) + p_minus * (1 - b_vector[0])
    p_matrix[0][1] = (p_plus - p_minus) * (b_vector[1] - 1j * b_vector[2])
    p_matrix[1][0] = (p_plus - p_minus) * (b_vector[1] + 1j * b_vector[2])
    p_matrix[1][1] = p_plus * (1 - b_vector[0]) + p_minus * (1 + b_vector[0])
    return p_matrix
