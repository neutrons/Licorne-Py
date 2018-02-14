import unittest,sys,os
from PyQt5 import QtTest,QtWidgets,QtCore
import numpy as np
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'../licorne')))#needed for UI
from licorne.data_loader import data_loader

app=QtWidgets.QApplication(sys.argv)

class Mock(object):
    def __init__(self,parent=None):
        self.shape=None
        self.ppol=None
        self.pana=None
    def signalReceived(self,signal):
        self.shape=signal[0].shape
        self.ppol=signal[1]
        self.pana=signal[2]

class dataloaderTest(unittest.TestCase):
    def setUp(self):
        self.form=data_loader()
        self.handler=Mock()
        self.form.dataSignal.connect(self.handler.signalReceived)
        
    def test_defaults(self):
        self.assertEqual(self.form.spinBox_FirstRow.value(),1)
        self.assertEqual(self.form.lineEdit_Filename.text().strip(),'')
        self.assertEqual(self.form.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).isEnabled(),False)

    def test_load(self):
        filename=os.path.abspath(os.path.join(os.path.dirname(__file__),'data/REF_M_24600+24601+24602+24603_Specular_---SD-PFO30-2-20Oe.dat'))
        self.form.lineEdit_Filename.setText(filename)
        loadbtn=self.form.pushButton_Load
        okbtn=self.form.buttonBox.button(QtWidgets.QDialogButtonBox.Ok)
        QtTest.QTest.mouseClick(loadbtn,QtCore.Qt.LeftButton)
        self.assertEqual(okbtn.isEnabled(),True)
        self.assertEqual(self.form.spinBox_FirstRow.value(),26)
        self.assertEqual(self.form.spinBox_LastRow.value(),159)
        QtTest.QTest.mouseClick(okbtn,QtCore.Qt.LeftButton)
        self.assertEqual(self.handler.shape,(134,3))
        
        
if __name__ == '__main__':
    unittest.main()
