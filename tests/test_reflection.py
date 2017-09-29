from licorne import reflection
import numpy as np
from numpy.testing import assert_array_almost_equal
import os,copy
import unittest
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

class Layer(object):
    pass

class TestReflectionClass(unittest.TestCase):
    def test_reference_results(self):
        paramfile = open(os.path.join(os.path.dirname(__file__),'data/refl_par.dat'),'r')
        n_monte_carlo = int(paramfile.readline())
        formalism = int(paramfile.readline())
        res_mode = int(paramfile.readline())
        n_of_outputs = int(paramfile.readline())
        pol_vecs = np.array([float(value) for value in paramfile.readline().strip().split()]).reshape(6,3)
        an_vecs = np.array([float(value) for value in paramfile.readline().strip().split()]).reshape(6,3)
        pol_fun = [int(value) for value in paramfile.readline().split()]
        norm_factor = [int(value) for value in paramfile.readline().split()]
        maxwell = int(paramfile.readline())
        glance_angle = int(paramfile.readline())
        background = float(paramfile.readline())
        percentage = float(paramfile.readline())
        nlayers1 = int(paramfile.readline())
        substrate_tmp = [float(value) for value in paramfile.readline().split()]
        substrate = complex(substrate_tmp[0],substrate_tmp[1])
        NC = float(paramfile.readline())
        layers = []
        for i in range(nlayers1):
            l = Layer()
            l.thickness = float(paramfile.readline())
            nsld_tmp = [float(value) for value in paramfile.readline().split()]
            l.nsld = complex(nsld_tmp[0], nsld_tmp[1])
            l.msld = [float(value) for value in paramfile.readline().split()]
            l.NC = float(paramfile.readline())
            layers.append(l)

        paramfile.close()

        q, dq = np.loadtxt(os.path.join(os.path.dirname(__file__),'data/refl_q_dq.dat'),unpack=True)
        inc_moment = q / 2.0

        pol_eff = np.ones(len(q), dtype=np.complex128)
        an_eff = np.ones(len(q), dtype=np.complex128)

        R = reflection.reflection(inc_moment, layers, substrate)
        for k in range(n_of_outputs):
            RR = reflection.spin_av(R, pol_vecs[k], an_vecs[k], pol_eff, an_eff)
            RR = np.real(RR)
            for res_mode in range(1,3):
                RRr = reflection.resolut(RR, q, dq, res_mode)
                RRr = RRr * norm_factor[k] + background
                reference_values = np.loadtxt(os.path.join(os.path.dirname(__file__),'data/res_mode'+str(res_mode)+'refl'+str(k+1)+'.dat'), unpack=True)
                assert_array_almost_equal(reference_values, RRr)

def res_chi3_137(Q):
    Theta1 = 0.0068
    Theta2 = 0.01
    Theta3 = 0.017

    DTheta1 = 0.0003
    DTheta2 = 0.0005
    DTheta3 = 0.0009

    Q1 = 0.03
    Q2 = 0.045

    QP1 = Q < Q1
    QP2 = np.logical_and(Q >= Q1,Q <= Q2)
    QP3 = Q > Q2

    DLambda = 0.005
    Lambda = np.zeros(len(Q))
    sigma = np.zeros(len(Q))

    Lambda[QP1] = 4.0 * np.pi * np.sin(Theta1) / Q[QP1]
    Lambda[QP2] = 4.0 * np.pi * np.sin(Theta2) / Q[QP2]
    Lambda[QP3] = 4.0 * np.pi * np.sin(Theta3) / Q[QP3]

    sigma[QP1] = Q[QP1] * np.sqrt((DTheta1/Theta1)**2+(DLambda/Lambda[QP1])**2)
    sigma[QP2] = Q[QP2] * np.sqrt((DTheta2/Theta2)**2+(DLambda/Lambda[QP2])**2)
    sigma[QP3] = Q[QP3] * np.sqrt((DTheta3/Theta3)**2+(DLambda/Lambda[QP3])**2)

    return sigma

class Testchi3_137(unittest.TestCase):
    Q = np.loadtxt(os.path.join(os.path.dirname(__file__),'data/chi3_137/q.dat'),unpack=True)
    inc_moment = Q / 2.0

    sigma = res_chi3_137(Q)

    substrate = complex(3.6214e-006, 0.0)
    layer_info = np.loadtxt(os.path.join(os.path.dirname(__file__), 'data/chi3_137/profile_sublayers.dat'))
    layer_info = layer_info[:-1]
    layers = []
    for line in layer_info:
        l = Layer()
        l.thickness = line[1]
        l.nsld = complex(line[2], line[3])
        msld = [line[4], np.deg2rad(line[5]), np.deg2rad(line[6])]
        l.msld = [msld[0]*np.sin(msld[2])*np.cos(msld[1]), msld[0]*np.sin(msld[2])*np.sin(msld[1]), msld[0]*np.cos(msld[2])]
        l.NC = 0.0
        layers.append(l)

    R = reflection.reflection(inc_moment, layers, substrate)
    pol_vecs = [[0.98,0.0,0.0], [-0.98,0.0,0.0], [0.98,0.0,0.0], [0.0,0.0,0.0], [0.0,0.0,0.0], [0.0,0.0,0.0]]
    an_vecs = [[0.98,0.0,0.0], [-0.98,0.0,0.0], [-0.98,0.0,0.0], [0.0,0.0,0.0], [0.0,0.0,0.0], [0.0,0.0,0.0]]
    norm_factor=[1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
    background=1.2e-05;

    pol_eff = np.ones(len(Q), dtype = np.complex128)
    an_eff = np.ones(len(Q), dtype = np.complex128)

    n_of_outputs = 3
    for k in range(n_of_outputs):
        RR = reflection.spin_av(R, pol_vecs[k], an_vecs[k], pol_eff, an_eff)
        RR = np.real(RR)
        RRr = reflection.resolut(RR, Q, sigma, 3)
        RRr = RRr * norm_factor[k] + background
        fig,ax = plt.subplots()
        ax.semilogy(Q,RRr,label='calculation')
        #plt.xlim([0.0,0.06])
        #plt.ylim([1.0e-4,10.0])
        reference_values = np.loadtxt(os.path.join(os.path.dirname(__file__),'data/chi3_137/rtheory'+str(k+1)+'.dat'), unpack=True)
        assert_array_almost_equal(RRr,reference_values,2)
        ax.semilogy(Q, reference_values, label='reference')
        ax.set_xlabel('Momentum Transfer $\AA^{-1}$')
        ax.set_ylabel('Reflectivity')
        ax.set_title('Polarization ({},{},{}), Analysis({},{},{})'.format(pol_vecs[k][0],pol_vecs[k][1],pol_vecs[k][2],an_vecs[k][0],an_vecs[k][1],an_vecs[k][2]))
        ax.legend()
        fig.savefig('chi3_137_'+str(k+1)+'.pdf')
        plt.close()

class Testr2_6_508(unittest.TestCase):
    q = np.loadtxt(os.path.join(os.path.dirname(__file__),'data/r2_6_508/q.dat'),unpack=True)
    inc_moment = q / 2.0

    sigma = res_chi3_137(q)

    substrate = complex(3.533e-006, 0.0)
    layer_info = np.loadtxt(os.path.join(os.path.dirname(__file__), 'data/r2_6_508/profile_sublayers.dat'))
    layer_info = layer_info[:-1]
    layers = []
    for line in layer_info:
        l = Layer()
        l.thickness = line[1]
        l.nsld = complex(line[2], line[3])
        msld = [line[4], np.deg2rad(line[5]), np.deg2rad(line[6])]
        l.msld = [msld[0]*np.sin(msld[2])*np.cos(msld[1]), msld[0]*np.sin(msld[2])*np.sin(msld[1]), msld[0]*np.cos(msld[2])]
        l.NC = 0.0
        layers.append(l)

    R = reflection.reflection(inc_moment, layers, substrate)
    pol_vecs = [[0.98,0.0,0.0], [-0.98,0.0,0.0], [0.98,0.0,0.0], [0.0,0.0,0.0], [0.0,0.0,0.0], [0.0,0.0,0.0]]
    an_vecs = [[0.98,0.0,0.0], [-0.98,0.0,0.0], [-0.98,0.0,0.0], [0.0,0.0,0.0], [0.0,0.0,0.0], [0.0,0.0,0.0]]
    norm_factor=[1.05, 1.05, 1.05, 1.05, 1.05, 1.05]
    background=1.e-06;

    pol_eff = np.ones(len(q), dtype = np.complex128)
    an_eff = np.ones(len(q), dtype = np.complex128)

    n_of_outputs = 3
    for k in range(n_of_outputs):
        RR = reflection.spin_av(R, pol_vecs[k], an_vecs[k], pol_eff, an_eff)
        RR = np.real(RR)
        RRr = reflection.resolut(RR, q, sigma, 3)
        RRr = RRr * norm_factor[k] + background
        fig,ax = plt.subplots()
        ax.semilogy(q, RRr, label='calculation')
        reference_values = np.loadtxt(os.path.join(os.path.dirname(__file__),'data/r2_6_508/rtheory'+str(k+1)+'.dat'), unpack=True)
        assert_array_almost_equal(RRr,reference_values,5)
        ax.semilogy(q, reference_values, label='reference')
        ax.set_xlabel('Momentum Transfer $\AA^{-1}$')
        ax.set_ylabel('Reflectivity')
        ax.set_title('Polarization ({},{},{}), Analysis({},{},{})'.format(pol_vecs[k][0],pol_vecs[k][1],pol_vecs[k][2],an_vecs[k][0],an_vecs[k][1],an_vecs[k][2]))
        ax.legend()
        fig.savefig('r2_6_508_'+str(k+1)+'.pdf')
        plt.close()

def res_helix100(Q):
    DTheta1 = 0.0
    DTheta2 = 0.0007
    Q1 = 0.0
    Lambda = 5.0
    DLambda = 0.01

    Theta = np.arcsin(Q * Lambda / (4.0 * np.pi))
    DTheta = np.zeros(len(Q));
    DTheta[Q > Q1] = 0.0007;
    Sigma = Q * np.sqrt((DTheta / Theta)**2 + (DLambda / Lambda)**2);
    return Sigma

class Testhelix100(unittest.TestCase):
    q = np.loadtxt(os.path.join(os.path.dirname(__file__),'data/helix100/q.dat'),unpack=True)
    inc_moment = q / 2.0

    sigma = res_helix100(q)

    substrate = complex(6.0e-6, 0.0)
    layer_info = np.loadtxt(os.path.join(os.path.dirname(__file__), 'data/helix100/profile_sublayers.dat'))
    layer_info = layer_info[:-1]
    layers = []
    for line in layer_info:
        l = Layer()
        l.thickness = line[1] # +0.05 # fit improved by adding 0.05?
        l.nsld = complex(line[2], line[3])
        msld = [line[4], np.deg2rad(line[5]), np.deg2rad(line[6])]
        l.msld = [msld[0]*np.sin(msld[2])*np.cos(msld[1]), msld[0]*np.sin(msld[2])*np.sin(msld[1]), msld[0]*np.cos(msld[2])]
        l.NC = 0.0
        layers.append(l)
    R = reflection.reflection(inc_moment, layers, substrate)

    pol_vecs = [[1,0,0],[-1,0,0],[-1,0,0],[0,0,0],[0,0,0],[0,0,0]]
    an_vecs = [[1,0,0],[-1,0,0],[1,0,0],[0,0,0],[0,0,0],[0,0,0]]

    norm_factor=[1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
    background=1.e-06

    pol_eff = np.ones(len(q), dtype = np.complex128)
    an_eff = np.ones(len(q), dtype = np.complex128)

    n_of_outputs = 3
    for k in range(n_of_outputs):
        RR = reflection.spin_av(R, pol_vecs[k], an_vecs[k], pol_eff, an_eff)
        RR = np.real(RR)
        RRr = reflection.resolut(RR, q, sigma, 3)
        RRr = RRr * norm_factor[k] + background
        fig,ax = plt.subplots()
        ax.semilogy(q,RRr,label='calculation')
        reference_values = np.loadtxt(os.path.join(os.path.dirname(__file__),'data/helix100/rtheory'+str(k+1)+'.dat'), unpack=True)
        assert_array_almost_equal(RRr,reference_values,5)
        ax.semilogy(q, reference_values, label='reference')
        ax.set_xlabel('Momentum Transfer $\AA^{-1}$')
        ax.set_ylabel('Reflectivity')
        ax.set_title('Polarization ({},{},{}), Analysis({},{},{})'.format(pol_vecs[k][0],pol_vecs[k][1],pol_vecs[k][2],an_vecs[k][0],an_vecs[k][1],an_vecs[k][2]))
        ax.legend()
        fig.savefig('helix100_'+str(k+1)+'.pdf')
        plt.close()

if __name__ == '__main__':
    unittest.main()

