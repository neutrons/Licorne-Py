import unittest,os
import numpy as np
import matplotlib
matplotlib.use("agg")
import matplotlib.pyplot as plt
from licorne.layer import Layer,RoughnessModel
from licorne.generateSublayers import generateSublayers
from licorne.layerplot import plot_sublayers


def layer_data_for_testing():
    Incoming=Layer(thickness=np.inf,
                   nsld_real=0,
                   nsld_imaginary=0,
                   msld_rho=0,
                   msld_phi=0,
                   msld_theta=0,
                   roughness=0,
                   roughness_model=RoughnessModel.NONE,
                   sublayers=16)
    Layer1=Layer(thickness=90.,
                   nsld_real=3.e-6,
                   nsld_imaginary=-3e-8,
                   msld_rho=0,
                   msld_phi=0,
                   msld_theta=90,
                   roughness=0.,
                   roughness_model=RoughnessModel.NONE,
                   sublayers=10)
    Layer2=Layer(thickness=40.,
                   nsld_real=3.5e-6,
                   nsld_imaginary=-3e-8,
                   msld_rho=5.31171e-7,
                   msld_phi=11.1877,
                   msld_theta=90,
                   roughness=8.,
                   roughness_model=RoughnessModel.TANH,
                   sublayers=10)
    Layer3=Layer(thickness=75,
                   nsld_real=2.3e-006,
                   nsld_imaginary=-3e-8,
                   msld_rho=1.96841e-006,
                   msld_phi=10.8359,
                   msld_theta=90,
                   roughness=5,
                   roughness_model=RoughnessModel.TANH,
                   sublayers=10)
    Layer4=Layer(thickness=125.,
                   nsld_real=2.4347e-006,
                   nsld_imaginary=-3e-8,
                   msld_rho=2.28882e-006,
                   msld_phi=9.48435,
                   msld_theta=90,
                   roughness=4,
                   roughness_model=RoughnessModel.TANH,
                   sublayers=10)                  
    Substrate=Layer(thickness=np.inf,
                   nsld_real=3.533e-006,
                   nsld_imaginary=0,
                   msld_rho=0,
                   msld_phi=0,
                   msld_theta=0,
                   roughness=5.,
                   roughness_model=RoughnessModel.TANH,
                   sublayers=10)
    layers=[Incoming,Layer1,Layer2,Layer3,Layer4,Substrate]
    return layers

class TestPlotLayerProperties(unittest.TestCase):

    def test_plot(self):
        layers=layer_data_for_testing()
        sublayers,corresponding=generateSublayers(layers)
        fig,ax=plt.subplots(2,1, sharex=False)
        plot_sublayers(ax[0],layers,parameter='NSLD_REAL')
        plot_sublayers(ax[1],layers,parameter='ROUGHNESS')
        #nsld_real plot
        pc=ax[0].get_children()[0]
        np.testing.assert_equal(pc.get_array(),corresponding)#colors are corresponding to the correct layer
        self.assertEqual(ax[0].get_xlabel(),'Depth')
        self.assertEqual(ax[0].get_ylabel(),'NSLD_REAL')
        #sublayer nslds
        sl_height_plot=np.array([path.vertices[2][1] for path in pc.get_paths()])
        sl_height_input=np.array([sl.nsld_real.value for sl in sublayers])
        np.testing.assert_allclose(sl_height_plot,sl_height_input,atol=1e-12)
        #roughness plot
        np.testing.assert_allclose(ax[1].get_children()[0].get_offsets(),np.array([[.0,0],[90,8],[130,5],[205,4],[330,5]]),atol=1e-3)
        self.assertEqual(ax[1].get_xlabel(),'Depth')
        self.assertEqual(ax[1].get_ylabel(),'ROUGHNESS')
        plt.close()

if __name__ == '__main__':
    unittest.main()     
