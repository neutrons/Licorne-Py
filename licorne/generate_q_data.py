from __future__ import (absolute_import, division, print_function)
from PyQt5 import QtCore, QtWidgets, QtGui, uic
import numpy as np
import os,sys
from licorne.experimental_data import experimental_data
import licorne.utilities as lu

ui=os.path.join(os.path.dirname(__file__),'UI/generate_Q_data.ui')
Ui_generate_q_data, QtBaseClass = uic.loadUiType(ui)

class generate_q_data(QtWidgets.QWidget,Ui_generate_q_data):
    dataSignal=QtCore.pyqtSignal(experimental_data)

    def __init__(self, *args):
        QtWidgets.QWidget.__init__(self, *args)
        Ui_generate_q_data.__init__(self)
        self.setupUi(self)
        self.error_dialog = QtWidgets.QErrorMessage()
        q_default = lu.defaultQ()
        self.doubleSpinBox_qmin.setValue(q_default[0])
        self.doubleSpinBox_qmax.setValue(q_default[-1])
        self.doubleSpinBox_qstep.setValue(q_default[1]-q_default[0])

    def accept(self):
        P_polarizer=np.array([self.doubleSpinBox_Polx.value(), self.doubleSpinBox_Poly.value(), self.doubleSpinBox_Polz.value()])
        P_analyzer=np.array([self.doubleSpinBox_Anax.value(), self.doubleSpinBox_Anay.value(), self.doubleSpinBox_Anaz.value()])
        try:
            Q = np.arange(self.doubleSpinBox_qmin.value(), self.doubleSpinBox_qmax.value(), self.doubleSpinBox_qstep.value())
            if Q[-1]<self.doubleSpinBox_qmax.value():
                Q = np.arange(self.doubleSpinBox_qmin.value(),
                              self.doubleSpinBox_qmax.value()+self.doubleSpinBox_qstep.value(),
                              self.doubleSpinBox_qstep.value())
        except:
            self.error_dialog.showMessage('Could not generate Q. Check values for Q min, Q max, Qstep')
            return
        if len(Q)<10:
            self.error_dialog.showMessage('Could not generate enough Q values (at least 10). Check values for Q min, Q max, Qstep')
            return
        ed=experimental_data()
        ed.Q=Q
        ed.pol_Polarizer=P_polarizer
        ed.pol_Analyzer=P_analyzer
        ed.filename='Generated Q dataset'
        self.dataSignal.emit(ed)
        self.close()

    def reject(self):
        self.close()
