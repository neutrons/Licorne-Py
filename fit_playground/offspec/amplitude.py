#pylint: disable=too-many-branches, too-many-lines, line-too-long
import numpy as np

class Layer(object):
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

    def initialize(self, n_alpha_i, n_wl):
        self.p_i_plus = np.zeros([n_alpha_i, n_wl])
        self.p_i_minus = np.zeros([n_alpha_i, n_wl])
        self.phi_i_plus = np.zeros([n_alpha_i, n_wl])
        self.phi_i_minus = np.zeros([n_alpha_i, n_wl])
        self.e_i_plus = np.zeros([n_alpha_i, n_wl])
        self.e_i_minus = np.zeros([n_alpha_i, n_wl])
        self.b = np.zeros(3)

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

                    # 1.16
                    p_i = np.zeros([2,2])
                    p_i[0][0] = layer.p_i_plus[i_alpha_i][i_wl] * (1 + layer.b[0]) + layer.p_i_minus[i_alpha_i][i_wl] * (1 - layer.b[0])



