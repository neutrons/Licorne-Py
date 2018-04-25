from __future__ import (absolute_import, division, print_function)
from PyQt5 import QtWidgets, QtCore, uic
import sys, os
from licorne.layer import Layer, RoughnessModel
from licorne.LayerList import generate_available_ties
from licorne.SampleModel import SampleModel
import numpy as np

ui = os.path.join(os.path.dirname(__file__), 'UI/LayerPropertiesWidget.ui')
Ui_LayerProperties, QtBaseClass = uic.loadUiType(ui)


class LayerPropertiesWidget(QtWidgets.QWidget, Ui_LayerProperties):
    sampleModelChanged=QtCore.pyqtSignal(SampleModel)
    def __init__(self, parent=None, sample_model=None, selected=None, *args):
        QtWidgets.QWidget.__init__(self, parent=parent, *args)
        Ui_LayerProperties.__init__(self)
        self.setupUi(self)
        self.sample_model=SampleModel()
        self.layer_list = []
        self.selection = []
        self.ties_nsld_real = []
        self.ties_nsld_imaginary = []
        self.ties_msld_rho = []
        self.ties_msld_theta = []
        self.ties_msld_phi = []
        self.ties_roughness = []
        self.ties_thickness = []
        self.show_hide_roughness_extras(0)
        if isinstance(sample_model,SampleModel):
            self.set_layer_list(sample_model)
            if selected is not None:
                self.set_selection(selected)
        self.Name_lineEdit.setFocus()
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Reset).clicked.connect(self.reset)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Apply).clicked.connect(self.apply)
        self.sublayers_spinBox.setSpecialValueText('Unchanged')
        self.roughness_model_comboBox.addItem('Unchanged')
        self.roughness_model_comboBox.addItems([r.name for r in RoughnessModel])

    def set_layer_list(self, new_sample_model):
        self.sample_model.set_model(new_sample_model)
        self.layer_list = [l for l in self.sample_model.layers]
        self.layer_list.insert(0,self.sample_model.incoming_media)
        self.layer_list.append(self.sample_model.substrate)
        self.selection = []
        self.ties_nsld_real, self.ties_nsld_imaginary, self.ties_msld_rho, \
        self.ties_msld_theta, self.ties_msld_phi, self.ties_roughness, self.ties_thickness = \
            generate_available_ties(self.layer_list[1:-1], self.layer_list[0], self.layer_list[-1])

    def set_selection(self, selected):
        self.selection = selected
        if not self.selection:
            return  # TODO: clear input
        name = self.layer_list[np.min(self.selection)].name
        if len(self.selection) > 1 and name != '':
            name += ' multiple'
        self.Name_lineEdit.setText(name)
        if selected == [0]:
            prefix = 'Incoming_media.'
            self.Name_lineEdit.setPlaceholderText('Incoming Media')
        elif selected == [len(self.layer_list) - 1]:
            prefix = 'Substrate.'
            self.Name_lineEdit.setPlaceholderText('Substrate')
        else:
            prefix = 'Layer{0}.'.format(np.min(selected) - 1)
            if len(selected) == 1:
                self.Name_lineEdit.setPlaceholderText('Layer{0}'.format(np.min(selected) - 1))
            else:
                self.Name_lineEdit.setPlaceholderText('Layer{0} multiple'.format(np.min(selected) - 1))
        self.Thickness.updateUiFromParameter([self.layer_list[x].thickness for x in self.selection],
                                             self.ties_thickness, prefix)
        self.NSLDR.updateUiFromParameter([self.layer_list[x].nsld_real for x in self.selection], self.ties_nsld_real,
                                         prefix)
        self.NSLDI.updateUiFromParameter([self.layer_list[x].nsld_imaginary for x in self.selection],
                                         self.ties_nsld_imaginary, prefix)
        self.MSLD_rho.updateUiFromParameter([self.layer_list[x].msld.rho for x in self.selection], self.ties_msld_rho,
                                            prefix)
        self.MSLD_theta.updateUiFromParameter([self.layer_list[x].msld.theta for x in self.selection],
                                              self.ties_msld_theta, prefix)
        self.MSLD_phi.updateUiFromParameter([self.layer_list[x].msld.phi for x in self.selection], self.ties_msld_phi,
                                            prefix)
        self.MSLD_rho.updateUiFromParameter([self.layer_list[x].msld.rho for x in self.selection], self.ties_msld_rho,
                                            prefix)
        self.Roughness.updateUiFromParameter([self.layer_list[x].roughness for x in self.selection],
                                             self.ties_roughness, prefix)
        self.update_UI_roughness_model([self.layer_list[x].roughness_model for x in self.selection],
                                       [self.layer_list[x].sublayers for x in self.selection])

    def reset(self):
        self.set_selection(self.selection)

    def update_UI_roughness_model(self, roughness_model_list, sublayers_list):
        if len(set(sublayers_list)) == 1:
            self.sublayers_spinBox.setValue(sublayers_list[0])
        else:
            self.sublayers_spinBox.setValue(-1)
        if len(set(roughness_model_list)) == 1:
            self.roughness_model_comboBox.setCurrentIndex(
                self.roughness_model_comboBox.findText(roughness_model_list[0].name))
        else:
            self.roughness_model_comboBox.setCurrentIndex(0)  # select the 'Unchanged'

    def update_roughness_model(self):
        if self.roughness_model_comboBox.currentIndex() != 0:  # not the 'Unchanged'
            for x in self.selection:
                self.layer_list[x].roughness_model = RoughnessModel[self.roughness_model_comboBox.currentText()]
        if self.sublayers_spinBox.value() != -1:  # not the 'Unchanged'
            for x in self.selection:
                self.layer_list[x].sublayers = self.sublayers_spinBox.value()

    def apply(self):
        if self.Name_lineEdit.text().strip() !='':
            for x in self.selection:
                self.layer_list[x].name=self.Name_lineEdit.text().strip()
        self.Thickness.update_parameter()
        self.NSLDR.update_parameter()
        self.NSLDI.update_parameter()
        self.MSLD_rho.update_parameter()
        self.MSLD_theta.update_parameter()
        self.MSLD_phi.update_parameter()
        self.Roughness.update_parameter()
        self.update_roughness_model()
        self.sampleModelChanged.emit(self.sample_model)

    def show_hide_roughness_extras(self, selected_tab):
        if selected_tab == 5:  # roughness tab selected
            self.roughness_model_label.show()
            self.roughness_model_comboBox.show()
            self.sublayers_label.show()
            self.sublayers_spinBox.show()
        else:
            self.roughness_model_label.hide()
            self.roughness_model_comboBox.hide()
            self.sublayers_label.hide()
            self.sublayers_spinBox.hide()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    #l1 = Layer(name='layer0', nsld_real=1)
    #l1.nsld_real.vary = True
    #l2 = Layer(nsld_real=2, name='L0')
    #l3 = Layer(nsld_real=3)
    #l4 = Layer(nsld_real=4)
    #sel = [1, 2]
    #window = LayerPropertiesWidget(layers=[l1, l2, l3, l4], selected=sel)
    #window.show()
    sys.exit(app.exec_())
