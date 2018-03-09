from __future__ import (absolute_import, division, print_function)
import PyQt5.uic
import sys, os
import licorne.NumericParameter
import numpy as np
import collections

ui = os.path.join(os.path.dirname(__file__), 'UI/NumericParameterWidget.ui')
Ui_NumericParameter, QtBaseClass = PyQt5.uic.loadUiType(ui)


class NumericParameterWidget(PyQt5.QtWidgets.QWidget, Ui_NumericParameter):
    def __init__(self, *args, **kwargs):
        PyQt5.QtWidgets.QWidget.__init__(self, *args)
        Ui_NumericParameter.__init__(self)
        self.setupUi(self)
        self.parameter = kwargs.pop('parameter', None)
        self.available_ties = kwargs.pop('available_ties', None)
        self.prefix = kwargs.pop('prefix', '')
        if self.parameter is not None:
            self.updateUiFromParameter(self.parameter, self.available_ties, self.prefix)

    def updateUiFromParameter(self, parameter, available_ties=None, prefix=''):
        if isinstance(parameter, licorne.NumericParameter.NumericParameter):
            if self.ties_comboBox.count()==0:
                self.ties_comboBox.addItem('')
            if isinstance(available_ties, str):
                self.ties_comboBox.addItem(available_ties)
            elif isinstance(available_ties, collections.Iterable):
                for ties in available_ties:
                    self.ties_comboBox.addItem(ties)
            else:
                pass  # None case or some weird input
            self.value_lineEdit.setText(str(parameter.value))
            self.unchanged_radioButton.setEnabled(False)
            try:
                tie_index = available_ties.index(parameter.expr) + 1
            except:
                tie_index = 0
            self.ties_comboBox.setCurrentIndex(tie_index)
            if parameter.vary:
                self.fit_radioButton.setChecked(True)
                self.add_current_tie(prefix + parameter.name, available_ties)
            else:
                self.fixed_radioButton.setChecked(True)
            if parameter.minimum == -np.inf:
                self.minimum_lineEdit.setText('')
            else:
                self.minimum_lineEdit.setText(str(parameter.minimum))
            if parameter.maximum == np.inf:
                self.maximum_lineEdit.setText('')
            else:
                self.maximum_lineEdit.setText(str(parameter.maximum))
        else:
            self.updateUiFromParameter(parameter[0], available_ties, prefix)
            if self.ties_comboBox.findText('Mixed/Unchanged')==-1:
                self.ties_comboBox.insertItem(1, 'Mixed/Unchanged')
            if len(set((p.expr for p in parameter))) != 1:
                self.ties_comboBox.setCurrentIndex(1)
            if len(set((p.value for p in parameter))) != 1:
                self.value_lineEdit.setText(str(parameter[0].value) + ' multiple')
            if len(set((p.vary for p in parameter))) != 1:
                self.unchanged_radioButton.setChecked(True)
                self.unchanged_radioButton.setEnabled(True)
            if len(set((p.minimum for p in parameter))) != 1:
                self.minimum_lineEdit.setText(str(parameter[0].minimum) + ' multiple')
            if len(set((p.maximum for p in parameter))) != 1:
                self.maximum_lineEdit.setText(str(parameter[0].maximum) + ' multiple')
        self.parameter=parameter

    def add_current_tie(self, name, available_ties):
        if self.fit_radioButton.isChecked() and self.ties_comboBox.findText(name) == -1:
            self.ties_comboBox.addItem(name)

    def update_parameter(self):
        value=self.value_lineEdit.text().strip()
        if not(value=='' or 'multiple' in value):
            value=float(value)
            if isinstance(self.parameter, licorne.NumericParameter.NumericParameter):
                self.parameter.value=value
            else:
                for p in self.parameter:
                    p.value=value
        minimum=self.minimum_lineEdit.text().strip()
        if not(minimum=='' or 'multiple' in minimum):
            minimum=float(minimum)
            if isinstance(self.parameter, licorne.NumericParameter.NumericParameter):
                self.parameter.minimum=minimum
            else:
                for p in self.parameter:
                    p.minimum=minimum
        maximum=self.maximum_lineEdit.text().strip()
        if not(maximum=='' or 'multiple' in maximum):
            maximum=float(maximum)
            if isinstance(self.parameter, licorne.NumericParameter.NumericParameter):
                self.parameter.maximum=maximum
            else:
                for p in self.parameter:
                    p.maximum=maximum
        if self.fit_radioButton.isChecked():
            vary = True
        elif self.fixed_radioButton.isChecked():
            vary = False
        else:
            vary = None
        if vary is not None:
            if isinstance(self.parameter, licorne.NumericParameter.NumericParameter):
                self.parameter.vary=vary
            else:
                for p in self.parameter:
                    p.vary=vary

        print(self.parameter)


if __name__ == '__main__':
    app = PyQt5.QtWidgets.QApplication(sys.argv)
    par1 = licorne.NumericParameter.NumericParameter(name='par1', value=3, maximum=7, vary=True, expr='other value1')
    par2 = licorne.NumericParameter.NumericParameter(name='par2', value=3, maximum=7, vary=True)
    par3 = licorne.NumericParameter.NumericParameter(name='par3', value=3, vary=False)
    window = NumericParameterWidget(parameter=[par1, par2, par3], available_ties=['other value', 'different value'])
    window.show()
    sys.exit(app.exec_())
