from __future__ import (absolute_import, division, print_function)
from PyQt5 import QtCore, QtWidgets, QtGui, uic
import numpy as np
import sys,os,shutil
import licorne.utilities as lu
try:
    reload
except NameError:
    from importlib import reload


ui=os.path.join(os.path.dirname(__file__),'UI/resolution.ui')
Ui_resolution, QtBaseClass = uic.loadUiType(ui)

class resolutionselector(QtWidgets.QWidget,Ui_resolution):
    def __init__(self, parent=None,Qvec=None):
        QtWidgets.QWidget.__init__(self, parent)
        Ui_resolution.__init__(self)
        self.setupUi(self)
        if Qvec==None:
            self.Q=lu.defaultQ()
        else:
            self.Q=Qvec
        self.tempdir=lu.tempdir().get_tempdir()
        self.comboBox_resolution_mode.addItem("TOF")
        self.comboBox_resolution_mode.addItem("Monochromatic")
        self.comboBox_resolution_mode.addItem("Custom")
        self.resolution_mode='TOF'
        self.comboBox_resolution_mode.activated[str].connect(self.resolution_mode_changed)
        self.resolution_mode_changed(self.resolution_mode)

    def resolution_mode_changed(self,res):
        if res=="TOF":
            #copy the tof resolution to the temp directory as resolution.py
            shutil.copy(os.path.join(os.path.dirname(__file__),'DefaultResolutionTOF.py'),
                        os.path.join(self.tempdir,'resolution.py'))
        elif res=="Monochromatic":
            #copy the mono resolution to the temp directory as resolution.py
            shutil.copy(os.path.join(os.path.dirname(__file__),'DefaultResolutionMONO.py'),
                        os.path.join(self.tempdir,'resolution.py'))
        else:
            #if we don't have a custom file create an empty one
            if not os.path.isfile(os.path.join(self.tempdir,'CustomResolution.py')):
                open(os.path.join(self.tempdir,'CustomResolution.py'),'w').close()
            #copy the custom file
            shutil.copy(os.path.join(self.tempdir,'CustomResolution.py'),
                        os.path.join(self.tempdir,'resolution.py'))                 
        if not os.path.join(self.tempdir,'resolution.py') in sys.path:
            sys.path.append(self.tempdir)
        import resolution
        reload(resolution)
        self.update_plot(self.Q,resolution.resolution(self.Q))

    def update_plot(self,x,y):
        print(x,y)

if __name__=='__main__':
    #This is for testing purposes only
    app=QtWidgets.QApplication(sys.argv)
    mainForm=resolutionselector()
    mainForm.show()
    sys.exit(app.exec_())
