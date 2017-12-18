"""
    Test cost function for Licorne
"""
#pylint: disable=invalid-name, protected-access, line-too-long
from __future__ import absolute_import, division, print_function, unicode_literals
import os
import numpy as np
from licorne import reflection
from licorne.layer import Layer, RoughnessModel
from licorne.generateSublayers import generateSublayers
from lmfit import minimize, Parameters, report_fit

def bare_silicon_model(ox_thick=18, ox_sld=2.0e-6, ox_rough=3.0, si_rough=3.0):
    """
        Generate a bare silicon substrate in air
    """
    _incoming=Layer(name='air',
                    thickness=np.inf,
                    nsld_real=0,
                    nsld_imaginary=0,
                    msld_rho=0,
                    msld_phi=0,
                    msld_theta=0,
                    roughness=0,
                    roughness_model=RoughnessModel.NONE,
                    sublayers=10)

    _oxide = Layer(name='SiOx',
                   thickness=ox_thick,
                   nsld_real=ox_sld,
                   nsld_imaginary=0,
                   msld_rho=0,
                   msld_phi=0,
                   msld_theta=0,
                   roughness=ox_rough,
                   roughness_model=RoughnessModel.ERFC,
                   sublayers=10)
    _oxide._nsld_real.vary = True
    _oxide._nsld_real.minimum = 1e-6
    _oxide._nsld_real.maximum = 4e-6

    _oxide._thickness.vary = True
    _oxide._thickness.minimum = 1
    _oxide._thickness.maximum = 50

    _oxide._roughness.vary = True
    _oxide._roughness.minimum = 1
    _oxide._roughness.maximum = 8

    _substrate=Layer(name='Si',
                     thickness=np.inf,
                     nsld_real=2.07e-006,
                     nsld_imaginary=0,
                     msld_rho=0,
                     msld_phi=0,
                     msld_theta=0,
                     roughness=si_rough,
                     roughness_model=RoughnessModel.ERFC,
                     sublayers=8)
    _substrate._roughness.vary = True
    _substrate._roughness.minimum = 1
    _substrate._roughness.maximum = 10

    return [_incoming, _oxide, _substrate]

class ModelAdapter(object):
    """
        Adapter class to mediate between the Licorne representation of a set of layers
        and a parameter set we can pass to lmfit.
    """
    def __init__(self, model_layers):
        self._model_layers = model_layers

    def __repr__(self):
        output = ''
        for layer in self._model_layers:
            output += "%s: \tthickness=%s, \tsld=%s, \troughness=%s\n" % ( layer.name, layer.thickness.value,
                                                                     layer.nsld_real.value, layer.roughness.value)
        return output

    def params_from_model(self):
        """
            Generate a parameter set with a given layer model.
            TODO: Right a decoding equivalent to pass to lmfit.minimize
        """
        params = Parameters()

        def _process_parameter(layer_name, p):
            if p.vary:
                params.add('%s__%s' % (layer_name, p.name), value=p.value, min=p.minimum, max=p.maximum)

        for l in self._model_layers:
            _process_parameter(l.name, l._thickness)
            _process_parameter(l.name, l._nsld_real)
            _process_parameter(l.name, l._roughness)

        return params

    def update_model_with_params(self, params):
        """
            Update a layer model from a parameter set.
        """
        for p in params.keys():
            toks = p.split('__')
            for i in range(len(self._model_layers)):
                if self._model_layers[i].name == toks[0]:
                    obj = getattr(self._model_layers[i], '_%s' % toks[1])
                    obj.value=params[p].value
        return self._model_layers

    def generate_sub_layers(self):
        """
            Wrapper to generate sub layers.

            TODO: There is an inconsistency between the reflectivity calculation and the
            sublayer generation. The sublayer generation generates
                layer.msld = MSLD(rho, theta, phi)
            but the reflectivity calculation expects
                layer.msld = [rho_x, rho_y, rho_z]
        """
        _sublayers, _ = generateSublayers(self._model_layers)

        for l in _sublayers:
            l._thickness = l.thickness.value
            l._msld = [0, 0, 0]

        return _sublayers

def residual_with_adapter(params, q, r, dr, model_adapter):
    """
        Compute residuals
    """
    model_adapter.update_model_with_params(params)
    model_layers = model_adapter.generate_sub_layers()

    substrate = np.complex(2.07e-006, 0.0)

    pol_eff = np.ones(len(q), dtype = np.complex128)
    an_eff = np.ones(len(q), dtype = np.complex128)

    # Why do we need to divide by 2?
    R = reflection.reflection(q/2, model_layers[1:-1], substrate)

    RR = reflection.spin_av(R, [1,0,0], [1,0,0], pol_eff, an_eff)
    RR = np.real(RR)

    return (RR-r)/dr

def fit_model_with_adapter(method = 'nelder'):
    """
        Test fit of a bare silicon with oxide.

        These are the REFL1D results for the same model:

        Chi2 = 1.307

        SiOx thickness    6.7 +- 1.7
        SiOx SLD          4.0 +- 0.3
        SiOx roughness    1.0 +- 0.7
        Si roughness      5.7 +- 2.0

    """
    # This is how the interface will use its layer model
    model_adapter = ModelAdapter(bare_silicon_model())
    params = model_adapter.params_from_model()

    # Load the data
    q, r, dr, _ = np.loadtxt(os.path.join(os.path.dirname(__file__),
                                           'data/Si_137848_1850_800.txt'), unpack=True)

    # Perform the fit
    result = minimize(residual_with_adapter, params, args=(q, r, dr, model_adapter), method=method)
    report_fit(result)

if __name__ == '__main__':
    fit_model_with_adapter() #method = 'differential_evolution')
