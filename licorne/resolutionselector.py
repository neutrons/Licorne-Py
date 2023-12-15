from __future__ import (absolute_import, division, print_function)
from PyQt5 import QtCore, QtWidgets, QtGui, uic
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
    resolution_changed = QtCore.pyqtSignal()
    def __init__(self, parent=None,Qvec=None):
        QtWidgets.QWidget.__init__(self, parent)
        Ui_resolution.__init__(self)
        self.setupUi(self)
        if Qvec is None:
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
        self.apply_btn=self.buttonBox.button(QtWidgets.QDialogButtonBox.Apply)
        self.apply_btn.clicked.connect(self.test_script)
        self.plainTextEdit_script.textChanged.connect(self.editing)
        self.ok_btn=self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok)
        self.cancel_btn=self.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel)
        self.ok_btn.clicked.connect(self.test_script_and_close)
        self.cancel_btn.clicked.connect(self.close)

    def update_q(self, new_q):
        if new_q is None:
           self.Q=lu.defaultQ()
        else:
            self.Q=new_q
        self.resolution_mode_changed(self.resolution_mode)

    def resizeEvent(self, event):
        self.canvas.setGeometry(self.widget_plot_area.rect())

    def resolution_mode_changed(self,res):
        self.resolution_mode=res
        if res=="TOF":
            #copy the tof resolution to the temp directory as resolution.py
            shutil.copy(os.path.join(os.path.dirname(__file__),'DefaultResolutionTOF.py'),
                        os.path.join(self.tempdir,'resolution.py'))
        elif res=="Monochromatic":
            #copy the mono resolution to the temp directory as resolution.py
            shutil.copy(os.path.join(os.path.dirname(__file__),'DefaultResolutionMONO.py'),
                        os.path.join(self.tempdir,'resolution.py'))
        elif res=="Custom":
            #if we don't have a custom file create an empty one
            if not os.path.isfile(os.path.join(self.tempdir,'CustomResolution.py')):
                open(os.path.join(self.tempdir,'CustomResolution.py'),'w').close()
            #copy the custom file
            shutil.copy(os.path.join(self.tempdir,'CustomResolution.py'),
                        os.path.join(self.tempdir,'resolution.py'))
        if 'editing' not in res:
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
        self.ignore_text_changed=True
        filename=os.path.join(self.tempdir,'resolution.py')
        with open(filename) as f:
            text=f.read()
        self.plainTextEdit_script.clear()
        self.plainTextEdit_script.appendPlainText(text)
        self.plainTextEdit_script.moveCursor(QtGui.QTextCursor.Start)
        self.ignore_text_changed=False

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
            if self.comboBox_resolution_mode.currentIndex()==3:
                self.comboBox_resolution_mode.setCurrentIndex(2)
                self.comboBox_resolution_mode.removeItem(3)
            self.resolution_changed.emit()
        except Exception as e:#TODO message
            print(e)
            shutil.copy(os.path.join(self.tempdir,'resolution.py.bck'),os.path.join(self.tempdir,'resolution.py'))
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)

    def test_script_and_close(self):
        self.test_script()
        self.close()

    def editing(self):
        if self.comboBox_resolution_mode.count()==3 and not self.ignore_text_changed:
            self.comboBox_resolution_mode.addItem("Custom (editing)")
            self.comboBox_resolution_mode.setCurrentIndex(3)

class ResolutionPlotCanvas(FigureCanvas):

    def __init__(self,x,y, parent=None):
        self.fig = Figure()
        self.fig.patch.set_facecolor('white')
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self,
                QtWidgets.QSizePolicy.Expanding,
                QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.plot(x,y)

    def plot(self,x,y):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.plot(x,y)
        ax.set_xlabel(r'Momentum transfer Q $({\AA}^{-1})$')
        ax.set_ylabel(r'Resolution $\sigma$ $({\AA}^{-1})$')
        ax.ticklabel_format(style='sci',scilimits=(-1,1),axis='both')
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
