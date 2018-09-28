#pylint: disable=too-many-branches, too-many-lines, line-too-long
"""
    Transcription into code of Toperverg off-specular write-up.
    Implementation note:
        At this point we are not trying to be clever. We just want a quick
        run-through to understand what comes out and catch inconsistencies.
"""
import sys
import numpy as np
from numpy import linalg

DEBUG = False

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

    def __init__(self, thickness, rho, roughness, irho=0, mrho=0):
        self.thickness = thickness
        self.rho = rho
        self.roughness = roughness
        self.irho = irho
        self.mrho = mrho

    def initialize(self, n_alpha_i, n_wl):
        self.p_i_plus = np.zeros([n_alpha_i, n_wl], dtype=np.complex)
        self.p_i_minus = np.zeros([n_alpha_i, n_wl], dtype=np.complex)
        self.phi_i_plus = np.zeros([n_alpha_i, n_wl], dtype=np.complex)
        self.phi_i_minus = np.zeros([n_alpha_i, n_wl], dtype=np.complex)
        self.e_i_plus = np.zeros([n_alpha_i, n_wl], dtype=np.complex)
        self.e_i_minus = np.zeros([n_alpha_i, n_wl], dtype=np.complex)
        self.e_ir_plus = np.zeros([n_alpha_i, n_wl], dtype=np.complex)
        self.e_ir_minus = np.zeros([n_alpha_i, n_wl], dtype=np.complex)
        self.e_it_plus = np.zeros([n_alpha_i, n_wl], dtype=np.complex)
        self.e_it_minus = np.zeros([n_alpha_i, n_wl], dtype=np.complex)
        self.b = np.asarray([0, 0, 1]) # np.zeros(3, dtype=np.complex)
        self.p_i_matrix = n_alpha_i*[n_wl*[np.zeros([2,2], dtype=np.complex)]]
        self.p_i_inv_matrix = n_alpha_i*[n_wl*[np.zeros([2,2], dtype=np.complex)]]
        self.e_i_matrix = n_alpha_i*[n_wl*[np.zeros([2,2], dtype=np.complex)]]
        self.e_ir_matrix = n_alpha_i*[n_wl*[np.zeros([2,2], dtype=np.complex)]]
        self.e_it_matrix = n_alpha_i*[n_wl*[np.zeros([2,2], dtype=np.complex)]]
        self.a_i_matrix = n_alpha_i*[n_wl*[np.zeros([2,2], dtype=np.complex)]]
        self.b_i_matrix = n_alpha_i*[n_wl*[np.zeros([2,2], dtype=np.complex)]]
        self.r_i_matrix = n_alpha_i*[n_wl*[np.zeros([2,2], dtype=np.complex)]]
        self.t_i_matrix = n_alpha_i*[n_wl*[np.eye(2, dtype=np.complex)]]

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
    def __init__(self, layers, p_i=[0,0,1], p_f=[0,0,1], n_alpha_i=5, n_wl=2, wl_min=2, wl_max=5, alpha_i_min=0.05, alpha_i_max=5):
        # Ordered list of layers
        self.layers = layers
        self.n_alpha_i = n_alpha_i
        self.n_wl = n_wl
        self.wl_min = wl_min
        self.wl_max = wl_max
        self.alpha_i_min = alpha_i_min * np.pi / 180.0
        self.alpha_i_max = alpha_i_max * np.pi / 180.0

        self.p_i = np.asarray(p_i)
        self.p_f = np.asarray(p_f)
        self.R = np.zeros([self.n_alpha_i, self.n_wl], dtype=np.complex)
        #self.R = n_alpha_i*[n_wl*[np.zeros([2,2], dtype=np.complex)]]

        for i, layer in enumerate(self.layers):
            layer.initialize(self.n_alpha_i, self.n_wl)

    def log(self, msg):
        if DEBUG:
            print(msg)

    def wavelength(self, i_wl):
        return self.wl_min + i_wl * (self.wl_max - self.wl_min) / (self.n_wl - 1)

    def __call__(self):
        _p_i0 = np.zeros([self.n_alpha_i, self.n_wl], dtype=np.complex)
        # 1.8
        for i_wl in range(self.n_wl):
            _wl = self.wl_min + i_wl * (self.wl_max - self.wl_min) / (self.n_wl - 1)

            # 1.9
            for i_alpha_i in range(self.n_alpha_i):
                # 1.10
                _alpha_i = self.alpha_i_min + i_alpha_i * (self.alpha_i_max - self.alpha_i_min) / (self.n_alpha_i - 1)
                # 1.11
                _p_i0[i_alpha_i][i_wl] = 2.0 * np.pi * np.sin(_alpha_i) / _wl

                for i, layer in enumerate(self.layers):
                    self.log("Angle: %s   Wl: %s   p_i0: %s" % (_alpha_i, _wl, _p_i0[i_alpha_i][i_wl]))
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
                    p_i = build_spin_matrix(layer.p_i_plus[i_alpha_i][i_wl], layer.p_i_minus[i_alpha_i][i_wl], layer.b) / 2.0

                    # 1.17 - invert p_i
                    p_i_inv = linalg.inv(p_i)

                    # For some reason the p matrices are defined with a factor 1/2 
                    #p_i = p_i / 2.0   ERROR IN MANUSCRIPT
                    #p_i_inv = p_i_inv / 2.0
                    layer.p_i_matrix[i_alpha_i][i_wl] = p_i
                    layer.p_i_inv_matrix[i_alpha_i][i_wl] = p_i_inv

                    # 1.18, 1.19
                    e_i = build_spin_matrix(layer.e_i_plus[i_alpha_i][i_wl], layer.e_i_minus[i_alpha_i][i_wl], layer.b)
                    layer.e_i_matrix[i_alpha_i][i_wl] = e_i / 2.0

                # 1.20, 1.21 -  Roughness - if roughness = 0, we get identity
                # Here we should be careful with the first and last layer
                # For the reflected component, skip the last layer
                # --> We need to have computed all the p_i values before iterating
                for i, layer in enumerate(self.layers):
                    w_ir = np.zeros([2,2], dtype=np.complex)
                    w_it = np.zeros([2,2], dtype=np.complex)
                    if i < len(self.layers) - 1:
                        self.log(str(self.layers[i].p_i_matrix[i_alpha_i][i_wl]))
                        self.log(str(self.layers[i+1].p_i_matrix[i_alpha_i][i_wl]))
                        w_ir = 2.0 * self.layers[i+1].roughness**2 * np.matmul(self.layers[i].p_i_matrix[i_alpha_i][i_wl], self.layers[i+1].p_i_matrix[i_alpha_i][i_wl])
                        self.log(str(w_ir.shape))
                    # For the transmission component, skip the first layer
                    if i > 0:
                        w_it = 0.5 * layer.roughness**2 * (self.layers[i-1].p_i_matrix[i_alpha_i][i_wl] - self.layers[i].p_i_matrix[i_alpha_i][i_wl])**2

                    # 1.22 - Roughness eigenvalues
                    w_ir_plus = 0.5 * ((w_ir[0][0] + w_ir[1][1]) + np.sqrt((w_ir[0][0] - w_ir[1][1])**2 + 4.0 * w_ir[0][1] * w_ir[1][0]))
                    w_ir_minus = 0.5 * ((w_ir[0][0] + w_ir[1][1]) - np.sqrt((w_ir[0][0] - w_ir[1][1])**2 + 4.0 * w_ir[0][1] * w_ir[1][0]))
                    w_it_plus = 0.5 * ((w_it[0][0] + w_it[1][1]) + np.sqrt((w_it[0][0] - w_it[1][1])**2 + 4.0 * w_it[0][1] * w_it[1][0]))
                    w_it_minus = 0.5 * ((w_it[0][0] + w_it[1][1]) - np.sqrt((w_it[0][0] - w_it[1][1])**2 + 4.0 * w_it[0][1] * w_it[1][0]))

                    # 1.23 Would be nice to have this in matrix notation
                    # TODO: check that this is good. The denominator is zero when there is no roughness
                    b_i_r = np.zeros(3, dtype=np.complex)
                    if layer.roughness>0.0:
                        b_i_r[0] = w_ir[0][0] - w_ir[1][1]
                        b_i_r[1] = w_ir[0][1] + w_ir[1][0]
                        b_i_r[2] = 1j * w_ir[0][1] - w_ir[1][0]
                        b_i_r = b_i_r / (w_ir_plus - w_ir_minus)

                    b_i_t = np.zeros(3, dtype=np.complex)
                    if layer.roughness>0.0:
                        b_i_t[0] = w_it[0][0] - w_it[1][1]
                        b_i_t[1] = w_it[0][1] + w_it[1][0]
                        b_i_t[2] = 1j * w_it[0][1] - w_it[1][0]
                        b_i_t = b_i_t / (w_it_plus - w_it_minus)

                    # 1.24 Eigenvalues of D-W exponents
                    layer.e_ir_plus[i_alpha_i][i_wl] = np.exp(-w_ir_plus)
                    layer.e_ir_minus[i_alpha_i][i_wl] = np.exp(-w_ir_minus)
                    layer.e_it_plus[i_alpha_i][i_wl] = np.exp(-w_it_plus)
                    layer.e_it_minus[i_alpha_i][i_wl] = np.exp(-w_it_minus)

                    # 1.25, 1.26
                    e_ir = build_spin_matrix(layer.e_ir_plus[i_alpha_i][i_wl], layer.e_ir_minus[i_alpha_i][i_wl], b_i_r) / 2.0
                    e_it = build_spin_matrix(layer.e_it_plus[i_alpha_i][i_wl], layer.e_it_minus[i_alpha_i][i_wl], b_i_t) / 2.0
                    layer.e_ir_matrix[i_alpha_i][i_wl] = e_ir
                    layer.e_it_matrix[i_alpha_i][i_wl] = e_it

                    # Sanity check
                    if layer.roughness == 0:
                        _sum_r = np.sum(e_ir - np.eye(2))
                        _sum_t = np.sum(e_it - np.eye(2))
                        if not (_sum_r==0 and _sum_t==0):
                            raise RuntimeError("Roughness calculation is wrong: %s" % str(_sum))

                    # 1.27 - recursion
                    # Here we should be careful with the first and last layer
                    # For the reflected component, skip the last layer
                    if i < len(self.layers) - 1:
                        _a_i = np.eye(2) - np.matmul(self.layers[i].p_i_inv_matrix[i_alpha_i][i_wl], self.layers[i+1].p_i_matrix[i_alpha_i][i_wl])
                        layer.a_i_matrix[i_alpha_i][i_wl] = np.matmul(_a_i, e_ir)
                        layer.b_i_matrix[i_alpha_i][i_wl] = np.eye(2) + np.matmul(self.layers[i].p_i_inv_matrix[i_alpha_i][i_wl], self.layers[i+1].p_i_matrix[i_alpha_i][i_wl])
                        #print('a: %s' % str(layer.a_i_matrix[i_alpha_i][i_wl].shape))
                        #print('b: %s' % str(layer.b_i_matrix[i_alpha_i][i_wl].shape))

                # 1.28 (part of init), 1.29
                for i in range(len(self.layers)-2, -1, -1):
                    _partial_a = self.layers[i].a_i_matrix[i_alpha_i][i_wl] + np.matmul(self.layers[i].b_i_matrix[i_alpha_i][i_wl], self.layers[i+1].r_i_matrix[i_alpha_i][i_wl])
                    _partial_b = self.layers[i].b_i_matrix[i_alpha_i][i_wl] + np.matmul(self.layers[i].a_i_matrix[i_alpha_i][i_wl], self.layers[i+1].r_i_matrix[i_alpha_i][i_wl])
                    try:
                        _partial_b = linalg.inv(_partial_b)
                        _r_i = np.matmul(_partial_b, self.layers[i].e_i_matrix[i_alpha_i][i_wl])
                        _r_i = np.matmul(_partial_a, _r_i)
                        _r_i = np.matmul(self.layers[i].e_i_matrix[i_alpha_i][i_wl], _r_i)
                        _r_i = np.matmul(_partial_a, _partial_b)
                        self.layers[i].r_i_matrix[i_alpha_i][i_wl] = _r_i
                    except:
                        print("1.28 OOPS! Layer %s" % i)
                        print(sys.exc_info()[1])

                # 1.30, 1.31
                for i in range(len(self.layers)-1):
                    #print("t_i %s" % str(self.layers[i].t_i_matrix[i_alpha_i][i_wl].shape))
                    _partial_a = self.layers[i].a_i_matrix[i_alpha_i][i_wl] + np.matmul(self.layers[i].b_i_matrix[i_alpha_i][i_wl], self.layers[i+1].r_i_matrix[i_alpha_i][i_wl])
                    #print('partial a shape: %s' % str(_partial_a.shape))
                    try:
                        _partial_a = linalg.inv(_partial_a)
                        t_i = np.matmul(self.layers[i].t_i_matrix[i_alpha_i][i_wl], self.layers[i].e_i_matrix[i_alpha_i][i_wl])
                        #t_i = np.matmul(self.layers[i].t_i_matrix[i_alpha_i][i_wl], self.layers[i].e_it_matrix[i_alpha_i][i_wl])
                        #t_i = self.layers[i].t_i_matrix[i_alpha_i][i_wl]
                        t_i = np.matmul(self.layers[i].e_i_matrix[i_alpha_i][i_wl], t_i)
                        t_i = 2.0 * np.matmul(_partial_a, t_i)
                        t_i = np.matmul(_partial_a, self.layers[i].t_i_matrix[i_alpha_i][i_wl])
                        self.layers[i+1].t_i_matrix[i_alpha_i][i_wl] = t_i
                    except:
                        print("1.30 OOPS! Layer %s" % i)

                # 1.32
                #self.R[i_alpha_i][i_wl] = 0#np.zeros([2,2], dtype=np.complex)

                r_i_amplitude_i = np.matmul(self.layers[0].r_i_matrix[i_alpha_i][i_wl], self.layers[0].t_i_matrix[i_alpha_i][i_wl])
                # 1.33
                r_i_plus_i = np.asarray(np.matrix(r_i_amplitude_i).H)

                # 1.34
                _r = np.matmul(self.rho_i(), r_i_plus_i)
                _r = np.matmul(r_i_amplitude_i, _r)
                _r = np.matmul(self.rho_f(), _r)
                # Look at the 1,1 entry for now
                self.R[i_alpha_i][i_wl] += _r[0][0] + _r[1][1]

    def reflectivity(self, i_wl):
        _wl = self.wl_min + i_wl * (self.wl_max - self.wl_min) / (self.n_wl - 1)
        print("Wavelength = %s" % _wl)
        q_array = []
        r_array = []
        for i_alpha_i in range(self.n_alpha_i):
            _alpha_i = self.alpha_i_min + i_alpha_i * (self.alpha_i_max - self.alpha_i_min) / (self.n_alpha_i - 1)
            _q = 4.0 * np.pi * np.sin(_alpha_i) / _wl
            q_array.append(_q.real)
            r_array.append(self.R[i_alpha_i][i_wl].real)#[0][0])
            #print("%6g  %6g" % (_q, self.R[i_alpha_i][i_wl].real))
        return q_array, r_array

    def rho_i(self):
        _matrix = np.zeros([2,2], dtype=np.complex)
        _matrix[0][0] = 1.0 + self.p_i[2]
        _matrix[0][1] = self.p_i[0] - 1j * self.p_i[1]
        _matrix[1][0] = self.p_i[0] + 1j * self.p_i[1]
        _matrix[1][1] = 1.0 - self.p_i[2]
        return 0.5 * _matrix

    def rho_f(self):
        _matrix = np.zeros([2,2], dtype=np.complex)
        _matrix[0][0] = 1.0 + self.p_i[2]
        _matrix[0][1] = self.p_i[0] - 1j * self.p_i[1]
        _matrix[1][0] = self.p_i[0] + 1j * self.p_i[1]
        _matrix[1][1] = 1.0 - self.p_i[2]
        return 0.5 * _matrix

def build_spin_matrix(p_plus, p_minus, b_vector):
    """
        Build a spin matrix based on the given components and Pauli matrices.
        #TODO: This probably simplifies to something obvious.
        This appears in 1.15, 1.18
    """
    p_matrix = np.zeros([2,2], dtype=np.complex)
    p_matrix[0][0] = p_plus * (1 + b_vector[0]) + p_minus * (1 - b_vector[0])
    p_matrix[0][1] = (p_plus - p_minus) * (b_vector[1] - 1j * b_vector[2])
    p_matrix[1][0] = (p_plus - p_minus) * (b_vector[1] + 1j * b_vector[2])
    p_matrix[1][1] = p_plus * (1 - b_vector[0]) + p_minus * (1 + b_vector[0])
    return p_matrix

if __name__ == "__main__":
    layers = []
    layers.append(Layer(1000, 0, 0))    # Air
    layers.append(Layer(250, 8e-6, 0))
    layers.append(Layer(1000, 2.07e-6, 0)) # Si substrate

    amplitude = Amplitude(layers=layers, p_i=[0,0,1], p_f=[0,0,1])
    amplitude()
    #print(amplitude.R)
    print("\n\n\n\n")
    amplitude.reflectivity(4)