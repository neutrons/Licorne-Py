from __future__ import (absolute_import, division, print_function)
from PyQt5 import QtCore, QtWidgets, QtGui, uic
import numpy as np

Ui_dataloader, QtBaseClass = uic.loadUiType('UI/dataloader.ui')

class dataloader(QtWidgets.QWidget,Ui_dataloader):
    def __init__(self, *args):
        QtWidgets.QWidget.__init__(self, *args)
        Ui_dataloader.__init__(self)
        self.setupUi(self)
        self.filename=''
        self.startrow=1
        self.endrow=2
        self.qcolumn=1
        self.rcolumn=2
        self.ecolumn=3
        self.error_dialog = QtWidgets.QErrorMessage()
        self.updatedatalimits()
        #self.filename='/home/3y9/licorne/fromValeria/REF_M_24600+24601+24602+24603_Specular_++-SD-PFO30-2-20Oe.dat'
        #self.update_text()
        self.buttonBox.accepted.connect(self.senddata)
        self.buttonBox.rejected.connect(self.close)
        self.buttonBox.helpRequested.connect(self.showhelp)
        self.pushButton_Browse.clicked.connect(self.browsefile)
        self.pushButton_Load.clicked.connect(self.loadfile)
        self.filesize=0

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
            self.update_text()

    def senddata(self):
        data=np.genfromtxt(self.filename,skip_header=self.startrow-1,skip_footer=self.filesize-self.endrow)
        try:
            qvalues=data[:,self.qcolumn-1]
            rvalues=data[:,self.rcolumn-1]
            errvalues=data[:,self.ecolumn-1]
            #TODO send the data
            self.close()
        except IndexError:
            self.error_dialog.showMessage('Could not find columns for Q, Reflectivity, or Error')

    def showhelp(self):
        pass

    def update_text(self):
        self.plainTextEdit_FileContent.clear()
        self.endrow=2
        try:
            fh=open(self.filename)
        except IOError:
            self.error_dialog.showMessage('Could not read the file')
        else:
            with fh:
                lines=fh.readlines()
                self.filesize=len(lines)
                for line in lines:
                    self.plainTextEdit_FileContent.appendPlainText(line.rstrip())
                self.plainTextEdit_FileContent.moveCursor(QtGui.QTextCursor.Start)
                self.endrow=self.filesize
        self.startrow=1
        self.qcolumn=1
        self.rcolumn=2
        self.ecolumn=3
        self.updatedatalimits()


    def updatedatalimits(self):
        self.spinBox_FirstRow.setValue(self.startrow)
        self.spinBox_LastRow.setValue(self.endrow)
        self.spinBox_QColumn.setValue(self.qcolumn)
        self.spinBox_RColumn.setValue(self.rcolumn)
        self.spinBox_EColumn.setValue(self.ecolumn)


if __name__=='__main__':
    #This is for testing purposes only
    import sys
    app=QtWidgets.QApplication(sys.argv)
    mainForm=dataloader()
    mainForm.show()
    sys.exit(app.exec_())