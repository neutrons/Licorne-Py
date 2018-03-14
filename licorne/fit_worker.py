from __future__ import absolute_import, division, print_function, unicode_literals

import copy,time

import numpy as np
from PyQt5 import QtCore
import licorne.SampleModel
from licorne.SampleModel import SampleModel
from licorne.model_adapter import ModelAdapter
from licorne.reflection import reflection,resolut, spin_av
from licorne.generateSublayers import generateSublayers
import licorne.utilities as lu
from lmfit import minimize, report_fit, Parameters


class FitWorker(QtCore.QThread):
    smChanged = QtCore.pyqtSignal(Parameters)
    chiSquaredChanged = QtCore.pyqtSignal(float)

    def __init__(self):
        super(FitWorker, self).__init__()
        self.sample_model=None
        self.data_model=None

    def initialize(self, sm, dm):
        self.sample_model = copy.deepcopy(sm)
        self.data_model = copy.deepcopy(dm)
        import resolution
        for ds in self.data_model.datasets:
            if ds.R is not None and len(ds.R)>1:
                Q = ds.Q/2.
                ds.sigmaQ = resolution.resolution(Q)

    def calculate_residuals(self,parameters):
        ma = ModelAdapter(self.sample_model)
        ma.update_model_from_params(parameters)
        layers = [self.sample_model.incoming_media]+self.sample_model.layers+[self.sample_model.substrate]
        sublayers = generateSublayers(layers)[0]
        chi_array = []
        for ds in self.data_model.datasets:
            if ds.R is not None and len(ds.R)>1:
                q = ds.Q/2.
                r = reflection(q, sublayers)
                pol_eff = np.ones(len(q), dtype = np.complex128)
                an_eff = np.ones(len(q), dtype = np.complex128)
                rr = np.real(spin_av(r, ds.pol_Polarizer, ds.pol_Analyzer, pol_eff,an_eff))
                sigma = ds.sigmaQ
                rrr = resolut(rr, q, sigma, 4)
                chi_array.append((rrr-ds.R)/ds.E)
        chi = np.array(chi_array).ravel()
        self.chiSquaredChanged.emit((chi**2).mean())
        return chi

    def run(self):
        ma = ModelAdapter(self.sample_model)
        parameters=ma.params_from_model()
        result=minimize(self.calculate_residuals, parameters,method=lu.get_minimizer())
        #report_fit(result)
        #ma.update_model_from_params(result.params)
        #print(self.sample_model.substrate)
        #p=Parameters()
        self.smChanged.emit(result.params)
