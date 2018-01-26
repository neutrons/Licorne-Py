from PyQt5 import QtWidgets, QtCore, uic
import sys
from licorne import LayerPropertiesWidget, layerselector,layer,SampleModel, LayerList

Ui_MainWindow, QtBaseClass = uic.loadUiType('UI/MainWindow.ui')

class  MainWindow(QtWidgets.QMainWindow,Ui_MainWindow):
    def __init__(self,sample_model_list):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.update_model(sample_model_list)
        self.selection=[]
        self.layerselector_widget.listView.selectionModel().selectionChanged.connect(self.update_selection)
        self.layerselector_widget.listView.selectionModel().selectionChanged.connect(self.layerselector_widget.selectionChanged)
        self.layerselector_widget.sampleModelChanged[SampleModel.SampleModel].connect(self.update_model)


    def update_model(self,sample_model):
        if isinstance(sample_model,SampleModel.SampleModel):
            self.sample_model=[sample_model]
        else:
            self.sample_model=sample_model
        self.layerselector_widget.set_sample_model(self.sample_model[0])
        
        all_layers=[s for s in [self.sample_model[0].incoming_media]+
                                     self.sample_model[0].layers+
                                     [self.sample_model[0].substrate]]
                                     
        self.layer_properties_widget.set_layer_list(all_layers)
        self.selection=[]
        self.layer_properties_widget.set_selection(self.selection)
        self.generate_parameter_list()
        
    def update_selection(self,selected,deselected):
        all_selected=self.layerselector_widget.listView.selectionModel().selectedRows()
        self.selection=sorted([s.row() for s in all_selected])
        self.layer_properties_widget.set_selection(self.selection)

    def generate_parameter_list(self):
        string_list=['Layer\tParameter\t\tTied to:']
        string_list.append('='*35)
        indexes,names,parameters,ties=LayerList.generate_parameter_lists(self.sample_model[0].layers,
                                                                         self.sample_model[0].incoming_media,
                                                                         self.sample_model[0].substrate)
        for i,n,p,t in zip(indexes,names,parameters,ties):
            if n in ['substrate','incoming_media']:
                name=n
            else:
                name='Layer{0}'.format(i-1)
            string_list.append('{0}\t{0}.{1}\t{2}'.format(name,p,t))
        self.fit_parameters_textEdit.setText('\n'.join(string_list))


if __name__=='__main__':
    app = QtWidgets.QApplication(sys.argv)
    sm=SampleModel.SampleModel()
    #sm.addItem(layer.Layer(name='L0',thickness=1,nsld_real=5))
    #sm.addItem(layer.Layer(name='L1',thickness=2.,nsld_real=3))
    #sm.addItem(layer.Layer(name='L2',thickness=1,nsld_real=5))
    #sm.substrate.nsld_real.vary=True
    #sm.layers[0].nsld_real.vary=True
    #sm.layers[0].nsld_real.expr='substrate.nsld_real'
    #sm.layers[0].thickness.vary=True
    window = MainWindow([sm])
    window.show()
    sys.exit(app.exec_())
