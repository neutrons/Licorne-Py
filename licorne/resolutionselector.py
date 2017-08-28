from __future__ import (absolute_import, division, print_function)
from PyQt5 import QtCore, QtWidgets, QtGui, uic
import numpy as np
import sys,os,shutil
import licorne.utilities as lu
try:
    reload
except NameError:
    from importlib import reload
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib

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
        self.canvas = ResolutionPlotCanvas(self.Q,self.Q*0.,self.widget_plot_area)
        self.tempdir=lu.tempdir().get_tempdir()
        self.comboBox_resolution_mode.addItem("TOF")
        self.comboBox_resolution_mode.addItem("Monochromatic")
        self.comboBox_resolution_mode.addItem("Custom")
        self.resolution_mode='TOF'
        self.comboBox_resolution_mode.activated[str].connect(self.resolution_mode_changed)
        self.resolution_mode_changed(self.resolution_mode)
        self.btn=self.buttonBox.button(QtWidgets.QDialogButtonBox.Apply)
        self.btn.clicked.connect(self.test_script)
        self.plainTextEdit_script.textChanged.connect(self.editing)

    def resizeEvent(self, event):
        self.canvas.setGeometry(self.widget_plot_area.rect())

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
        #Force reloading of the resolution function
        import resolution
        if hasattr(resolution,'resolution'):
            del resolution.resolution
        reload(resolution)
        self.update_text_from_file()
        self.update_plot()

    def update_text_from_file(self):
        filename=os.path.join(self.tempdir,'resolution.py')
        with open(filename) as f:
            text=f.read()
        self.plainTextEdit_script.clear()
        self.plainTextEdit_script.appendPlainText(text)
        self.plainTextEdit_script.moveCursor(QtGui.QTextCursor.Start)

    def update_plot(self):
        r=self.Q*0.
        import resolution
        reload(resolution)
        if hasattr(resolution,'resolution'):
            r=resolution.resolution(self.Q)
        self.canvas.plot(self.Q,r)

    def test_script(self):
        #make a backup of resolution file
        shutil.copy(os.path.join(self.tempdir,'resolution.py'),os.path.join(self.tempdir,'resolution.py.bck'))
        try:
            with open(os.path.join(self.tempdir,'resolution.py'),'w') as fh:
                fh.write(self.plainTextEdit_script.toPlainText())
            import resolution
            reload(resolution)
            r=self.Q*0.
            if hasattr(resolution,'resolution'):
                r=resolution.resolution(self.Q)
            self.canvas.plot(self.Q,r)
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
            shutil.copy(os.path.join(self.tempdir,'resolution.py'),os.path.join(self.tempdir,'CustomResolution.py'))
        except Exception as e:#TODO message
            print(e)
            shutil.copy(os.path.join(self.tempdir,'resolution.py.bck'),os.path.join(self.tempdir,'resolution.py'))
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)

    def editing(self):
        pass

class ResolutionPlotCanvas(FigureCanvas):

    def __init__(self,x,y, parent=None):
        self.fig = Figure()
        self.fig.patch.set_facecolor('white')
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        matplotlib.rc('text', usetex=True)
        FigureCanvas.setSizePolicy(self,
                QtWidgets.QSizePolicy.Expanding,
                QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.plot(x,y)

    def plot(self,x,y):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.plot(x,y)
        ax.set_xlabel(r'Momentum transfer Q (${\textrm \AA}^{-1}$)')
        ax.set_ylabel(r'Resolution $\sigma$ (${\textrm \AA}^{-1}$)')
        self.figure.tight_layout()
        self.draw()

if __name__=='__main__':
    #This is for testing purposes only
    temp_dir=lu.tempdir()
    app=QtWidgets.QApplication(sys.argv)
    mainForm=resolutionselector()
    mainForm.show()
    ret=app.exec_()
    temp_dir.del_tempdir()
    sys.exit(ret)
