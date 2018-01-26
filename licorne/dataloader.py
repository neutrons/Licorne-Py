from __future__ import (absolute_import, division, print_function)
from PyQt5 import QtCore, QtWidgets, QtGui, uic
import numpy as np
import os,sys


ui=os.path.join(os.path.dirname(__file__),'UI/dataloader.ui')
Ui_dataloader, QtBaseClass = uic.loadUiType(ui)

class dataloader(QtWidgets.QWidget,Ui_dataloader):
    dataSignal=QtCore.pyqtSignal(tuple)
    def __init__(self, *args):
        QtWidgets.QWidget.__init__(self, *args)
        Ui_dataloader.__init__(self)
        self.setupUi(self)
        self.filename=''
        self.data=np.array([])
        self.startrow=1
        self.endrow=2
        self.qcolumn=1
        self.rcolumn=2
        self.ecolumn=3
        self.filesize=0
        self.Ppolarizer=np.zeros(3)
        self.Panalyzer=np.zeros(3)
        self.error_dialog = QtWidgets.QErrorMessage()
        self.updatedatalimits()
        self.buttonBox.accepted.connect(self.senddata)
        self.buttonBox.rejected.connect(self.close)
        self.buttonBox.helpRequested.connect(self.showhelp)
        self.pushButton_Browse.clicked.connect(self.browsefile)
        self.pushButton_Load.clicked.connect(self.loadfile)
        self.spinBox_FirstRow.valueChanged.connect(self.updateFRfromui)
        self.spinBox_LastRow.valueChanged.connect(self.updateLRfromui)
        self.spinBox_QColumn.valueChanged.connect(self.updateQCfromui)
        self.spinBox_RColumn.valueChanged.connect(self.updateRCfromui)
        self.spinBox_EColumn.valueChanged.connect(self.updateECfromui)
        self.dataSignal.connect(self.debuginfo)
        self.doubleSpinBox_Anax.valueChanged.connect(self.updatePfromui)
        self.doubleSpinBox_Anay.valueChanged.connect(self.updatePfromui)
        self.doubleSpinBox_Anaz.valueChanged.connect(self.updatePfromui)
        self.doubleSpinBox_Polx.valueChanged.connect(self.updatePfromui)
        self.doubleSpinBox_Poly.valueChanged.connect(self.updatePfromui)
        self.doubleSpinBox_Polz.valueChanged.connect(self.updatePfromui)
        self.disableOK()

    def debuginfo(self,content):
        pass
        #print("Data: {0} rows".format(content[0].shape[0]))
        #print("P_polarizer: ",content[1])
        #print("P_analyzer: ",content[2])

    def loadfile(self):
        if len(self.lineEdit_Filename.text().strip())==0:
            self.plainTextEdit_FileContent.clear()
        else:
            self.filename=self.lineEdit_Filename.text()
            self.update_text()

    def browsefile(self):        
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","All Files (*)", options=options)
        if fileName:
            self.filename=fileName
            self.lineEdit_Filename.setText(self.filename)
            self.update_text()

    def readdata(self):
        try:
            data=np.genfromtxt(self.filename,skip_header=self.startrow-1,skip_footer=self.filesize-self.endrow)
        except:
            self.disableOK()
            return
        testSet=set([self.qcolumn,self.rcolumn,self.ecolumn])
        if len(testSet)!=3:
            self.error_dialog.showMessage('Could not find independent columns for Q, Reflectivity, or Error')
            self.disableOK()
            return
        if len(data.shape)!=2:
            self.error_dialog.showMessage('Could not read enough data. Check that the last row is greater than the first row')
            self.disableOK()
            return
        if max(testSet)>data.shape[1]:
            self.error_dialog.showMessage('Column numbers for Q, Reflectivity, or Error must be less than {0}'.format(data.shape[1]))
            self.disableOK()
            return
        self.enableOK()
        self.data=data[:,[self.qcolumn-1,self.rcolumn-1,self.ecolumn-1]]

    def enableOK(self):
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)

    def disableOK(self):
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)

    def senddata(self):
        self.dataSignal.emit((self.data,self.Ppolarizer,self.Panalyzer,self.filename))
        self.close()

    def showhelp(self):
        pass

    def update_text(self):
        self.plainTextEdit_FileContent.clear()
        self.startrow=1
        self.endrow=2
        search_first_num=True
        try:
            kwargs=dict()
            if sys.version_info>(3,0):
                kwargs={'encoding':"utf-8"}
            fh=open(self.filename,**kwargs)
        except IOError:
            self.error_dialog.showMessage('Could not read the file')
        else:
            with fh:
                lines=fh.readlines()
                self.filesize=len(lines)
                for line_number,line in enumerate(lines):
                    self.plainTextEdit_FileContent.appendPlainText(line.rstrip())
                    try:
                        char0=line.strip()[0]
                    except IndexError:
                        char0='#'
                    if search_first_num and char0.isdigit():
                        search_first_num=False
                        self.startrow=line_number+1
                self.plainTextEdit_FileContent.moveCursor(QtGui.QTextCursor.Start)
                self.endrow=len(lines)#self.filesize
        self.qcolumn=1
        self.rcolumn=2
        self.ecolumn=3
        self.updatedatalimits()
        self.readdata()

    def updatedatalimits(self):
        self.spinBox_FirstRow.setValue(self.startrow)
        self.spinBox_LastRow.setValue(self.endrow)
        self.spinBox_QColumn.setValue(self.qcolumn)
        self.spinBox_RColumn.setValue(self.rcolumn)
        self.spinBox_EColumn.setValue(self.ecolumn)

    def updateFRfromui(self):
        self.startrow=int(self.spinBox_FirstRow.value())
        self.readdata()

    def updateLRfromui(self):
        self.endrow=int(self.spinBox_LastRow.value())
        self.readdata()

    def updateQCfromui(self):
        self.qcolumn=int(self.spinBox_QColumn.value())
        self.readdata()

    def updateRCfromui(self):
        self.rcolumn=int(self.spinBox_RColumn.value())
        self.readdata()

    def updateECfromui(self):        
        self.ecolumn=int(self.spinBox_EColumn.value())
        self.readdata()

    def updatePfromui(self):
        self.Ppolarizer=np.array([self.doubleSpinBox_Polx.value(),self.doubleSpinBox_Poly.value(),self.doubleSpinBox_Polz.value()])
        self.Panalyzer=np.array([self.doubleSpinBox_Anax.value(),self.doubleSpinBox_Anay.value(),self.doubleSpinBox_Anaz.value()])

if __name__=='__main__':
    #This is for testing purposes only
    app=QtWidgets.QApplication(sys.argv)
    mainForm=dataloader()
    mainForm.show()
    sys.exit(app.exec_())
