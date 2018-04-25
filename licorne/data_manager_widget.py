from __future__ import (absolute_import, division, print_function)
from PyQt5 import QtWidgets, QtCore, QtGui, uic
import sys, os
import numpy as np
from licorne.data_model import data_model
from licorne.data_loader import data_loader
from licorne.generate_q_data import generate_q_data
from licorne.resolutionselector import resolutionselector

ui = os.path.join(os.path.dirname(__file__),'UI/data_manager.ui')
Ui_data_manager, QtBaseClass = uic.loadUiType(ui)


class data_manager(QtWidgets.QWidget,Ui_data_manager):
    dataModelChanged=QtCore.pyqtSignal(data_model)
    def __init__(self, *args):
        QtWidgets.QWidget.__init__(self, *args)
        Ui_data_manager.__init__(self)
        self.setupUi(self)
        self.pushButton_load.clicked.connect(self.loadfile)
        self.pushButton_generate.clicked.connect(self.generate)
        self.pushButton_delete.clicked.connect(self.deletedata)
        self.data_model=data_model()
        self.data_model.setParent(self)
        self.listView.setModel(self.data_model)
        self.selection=None
        self.listView.selectionModel().selectionChanged.connect(self.selectionChanged)
        self.disable_delete()
        self.doubleSpinBox_Polx.setEnabled(False)
        self.doubleSpinBox_Poly.setEnabled(False)
        self.doubleSpinBox_Polz.setEnabled(False)
        self.doubleSpinBox_Anax.setEnabled(False)
        self.doubleSpinBox_Anay.setEnabled(False)
        self.doubleSpinBox_Anaz.setEnabled(False)
        self.doubleSpinBox_Anax.valueChanged.connect(self.updatePfromui)
        self.doubleSpinBox_Anay.valueChanged.connect(self.updatePfromui)
        self.doubleSpinBox_Anaz.valueChanged.connect(self.updatePfromui)
        self.doubleSpinBox_Polx.valueChanged.connect(self.updatePfromui)
        self.doubleSpinBox_Poly.valueChanged.connect(self.updatePfromui)
        self.doubleSpinBox_Polz.valueChanged.connect(self.updatePfromui)
        self.lineEdit_background.setValidator(QtGui.QDoubleValidator())
        self.lineEdit_background.textChanged.connect(self.update_other)
        self.doubleSpinBox_experiment_norm.valueChanged.connect(self.update_other)
        self.doubleSpinBox_theory_norm.valueChanged.connect(self.update_other)
        self.pushButton_resolution.clicked.connect(self.load_resolution)
        self.resolution_dialog = resolutionselector(parent=None, Qvec=None)
        self.resolution_dialog.resolution_changed.connect(self.resolution_changed)

    def update_data_model(self,dm):
        self.lineEdit_background.setText(str(dm.background))
        self.doubleSpinBox_experiment_norm.setValue(dm.experiment_factor)
        self.doubleSpinBox_theory_norm.setValue(dm.theory_factor)
        self.data_model.set_model(dm)
        self.data_model.setParent(self)
        self.listView.setModel(self.data_model)


    def load_resolution(self):
        q_array = None
        try:
            q = []
            for ds in self.data_model.datasets:
                q = np.concatenate([q,ds.Q])
            q_array = np.linspace(np.min(q),np.max(q),150)
        except:
            pass
        self.resolution_dialog.update_q(q_array)
        self.resolution_dialog.show()

    def resolution_changed(self):
        self.dataModelChanged.emit(self.data_model)

    def closeEvent(self, event):
        try:
            self.data_dialog.close()
        except:
            pass
        try:
            self.generate_dialog.close()
        except:
            pass
        try:
            self.resolution_dialog.close()
        except:
            pass
        event.accept()

    def accept(self):
        self.dataModelChanged.emit(self.data_model)
        self.close()

    def reject(self):
        pass

    def updatePfromui(self):
        self.data_model.datasets[self.selection].pol_Polarizer=[self.doubleSpinBox_Polx.value(),
                                                                self.doubleSpinBox_Poly.value(),
                                                                self.doubleSpinBox_Polz.value()]
        self.data_model.datasets[self.selection].pol_Analyzer=[self.doubleSpinBox_Anax.value(),
                                                               self.doubleSpinBox_Anay.value(),
                                                               self.doubleSpinBox_Anaz.value()]

    def update_other(self):
        try:
            bkg=float(self.lineEdit_background.text())
        except:
            bkg=0.0
        self.data_model.background=bkg
        self.data_model.experiment_factor=self.doubleSpinBox_experiment_norm.value()
        self.data_model.theory_factor=self.doubleSpinBox_theory_norm.value()

    def enable_delete(self):
        self.pushButton_delete.setEnabled(True)

    def disable_delete(self):
        self.pushButton_delete.setEnabled(False)

    def selectionChanged(self,selected,deselected):
        if len(selected)==1:
            self.selection=selected.indexes()[0].row()
            Ppolarizer=self.data_model.datasets[self.selection].pol_Polarizer
            Panalyzer=self.data_model.datasets[self.selection].pol_Analyzer
            self.doubleSpinBox_Polx.setValue(Ppolarizer[0])
            self.doubleSpinBox_Poly.setValue(Ppolarizer[1])
            self.doubleSpinBox_Polz.setValue(Ppolarizer[2])
            self.doubleSpinBox_Anax.setValue(Panalyzer[0])
            self.doubleSpinBox_Anay.setValue(Panalyzer[1])
            self.doubleSpinBox_Anaz.setValue(Panalyzer[2])            
            
            self.doubleSpinBox_Polx.setEnabled(True)
            self.doubleSpinBox_Poly.setEnabled(True)
            self.doubleSpinBox_Polz.setEnabled(True)
            self.doubleSpinBox_Anax.setEnabled(True)
            self.doubleSpinBox_Anay.setEnabled(True)
            self.doubleSpinBox_Anaz.setEnabled(True)
            self.enable_delete()
        else:
            self.selection=None
            self.doubleSpinBox_Polx.setEnabled(False)
            self.doubleSpinBox_Poly.setEnabled(False)
            self.doubleSpinBox_Polz.setEnabled(False)
            self.doubleSpinBox_Anax.setEnabled(False)
            self.doubleSpinBox_Anay.setEnabled(False)
            self.doubleSpinBox_Anaz.setEnabled(False)
            self.disable_delete()
    
    def deletedata(self):
        ind= self.listView.selectionModel().selectedRows()[0].row()
        self.data_model.delItem(ind)
        self.dataModelChanged.emit(self.data_model)

    def generate(self):
        self.generate_dialog=generate_q_data()
        self.generate_dialog.dataSignal.connect(self.add_data)
        self.generate_dialog.show()
    
    def add_data(self,content):
        self.data_model.addItem(content)
        self.dataModelChanged.emit(self.data_model)
                
    def loadfile(self):
        self.data_dialog=data_loader()
        self.data_dialog.dataSignal.connect(self.add_data)
        self.data_dialog.show()
        

if __name__=='__main__':
    #This is for testing purposes only
    app=QtWidgets.QApplication(sys.argv)
    mainForm=data_manager()
    mainForm.show()
    sys.exit(app.exec_())
