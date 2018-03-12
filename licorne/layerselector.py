from PyQt5 import QtWidgets, QtCore, uic
import sys,os,copy

from licorne.layer import Layer
from licorne.SampleModel import SampleModel

ui=os.path.join(os.path.dirname(__file__),'UI/layerselector.ui')
Ui_layerselector, QtBaseClass = uic.loadUiType(ui)

class layerselector(QtWidgets.QWidget, Ui_layerselector):
    invalidSelection=QtCore.pyqtSignal(str)
    sampleModelChanged=QtCore.pyqtSignal(SampleModel)
    def __init__(self,sample_model=SampleModel(),*args):
        QtWidgets.QWidget.__init__(self,*args)
        Ui_layerselector.__init__(self)
        self.setupUi(self)
        self.set_sample_model(sample_model)
        self.listView.selectionModel().selectionChanged.connect(self.selectionChanged)
        self.invalidSelection[str].connect(self.module_logger)

    def set_sample_model(self,sample_model):
        self.sample_model=sample_model
        self.sample_model.setParent(self)
        self.listView.setModel(self.sample_model)

    def module_logger(self,message):
        print('[layerselector]: '+message)

    def addClicked(self):
        selected=self.listView.selectionModel().selectedRows()
        inds=sorted([s.row() for s in selected])
        selected=[]
        if inds:
            for i, j in enumerate(inds):
                if j in [0,self.sample_model.rowCount()-1]:
                    self.invalidSelection.emit('Cannot add another substrate or incoming media')
                else:
                    self.sample_model.addItem(copy.deepcopy(self.sample_model.layers[i-1+j]),i+j)
                    selected.append(i+j)
        else:
            self.sample_model.addItem(Layer())
        self.sampleModelChanged.emit(self.sample_model)
        self.listView.selectionModel().clear()
        for selection in selected:
            self.listView.selectionModel().select(self.sample_model.index(selection),QtCore.QItemSelectionModel.Select)

    def delClicked(self):
        inds=sorted([s.row() for s in self.listView.selectionModel().selectedRows()], reverse=True)
        if inds:
            if inds in [[0],[self.sample_model.rowCount()-1]]:
                self.invalidSelection.emit('Cannot delete substrate or incoming media')
            else:
                for i in inds:
                    self.sample_model.delItem(i-1)
        else:
            self.invalidSelection.emit("nothing selected")
        self.sampleModelChanged.emit(self.sample_model)
            
    def selectionEntered(self):
        selection_string=str(self.select_lineEdit.text())
        slice_parts=selection_string.split(':')
        if len(slice_parts)>3:
            self.invalidSelection.emit(selection_string+" has more than three arguments")
            return
        if len(slice_parts)==1:
            try:
                index=int(slice_parts[0])
                selection_slice=slice(index,index+1)
            except ValueError:
                self.invalidSelection.emit(selection_string+' cannot be converted to a slice')
                return
        else:
            try:
                s=[int(x) if x.strip()!='' else None for x in slice_parts]
                selection_slice=slice(*s)
            except ValueError:
                self.invalidSelection.emit(selection_string+' cannot be converted to a slice')
                return
        self.listView.selectionModel().clear()
        all_layers=range(1,self.sample_model.rowCount()-1)
        new_selection=all_layers[selection_slice]
        for i in new_selection:
            layer_index=self.sample_model.index(i)
            self.listView.selectionModel().select(layer_index,QtCore.QItemSelectionModel.Select)

    def selectionChanged(self,selected,deselected):
        incoming_media_index=self.sample_model.index(0)
        substrate_index=self.sample_model.index(self.sample_model.rowCount()-1)
        all_rows=self.listView.selectionModel().selectedRows()
        if (substrate_index in all_rows) and len(all_rows)>1:
            if substrate_index in selected:
                if len(selected)>1:
                    self.listView.selectionModel().select(substrate_index,QtCore.QItemSelectionModel.Deselect)
                else:
                    self.listView.selectionModel().clear()
                    self.listView.selectionModel().select(substrate_index,QtCore.QItemSelectionModel.Select)             
            else:
                self.listView.selectionModel().select(substrate_index,QtCore.QItemSelectionModel.Deselect)
        if (incoming_media_index in all_rows) and len(all_rows)>1:
            if incoming_media_index in selected:
                if len(selected)>1:
                    self.listView.selectionModel().select(incoming_media_index,QtCore.QItemSelectionModel.Deselect)
                else:
                    self.listView.selectionModel().clear()
                    self.listView.selectionModel().select(incoming_media_index,QtCore.QItemSelectionModel.Select)             
            else:
                self.listView.selectionModel().select(incoming_media_index,QtCore.QItemSelectionModel.Deselect)


if __name__=='__main__':
    app = QtWidgets.QApplication(sys.argv)
    sm=SampleModel()
    sm.addItem(Layer(name='L0'))
    sm.addItem(Layer(name='L1',thickness=2))
    sm.addItem(Layer(name='L2'))
    sm.addItem(Layer(name='L3'))
    window = layerselector(sm)
    window.show()
    sys.exit(app.exec_())

