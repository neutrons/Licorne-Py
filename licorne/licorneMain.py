from __future__ import absolute_import, division, print_function, unicode_literals
import matplotlib
matplotlib.use('qt5agg')
from PyQt5 import QtWidgets, QtCore, uic
import sys,os
from licorne import LayerPropertiesWidget, layerselector,layer,SampleModel, LayerList, data_manager_widget

Ui_MainWindow, QtBaseClass = uic.loadUiType('UI/MainWindow.ui')

from matplotlib.backends.backend_qt5agg import (
        FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import numpy as np


class DataPlotWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(DataPlotWindow, self).__init__()
        self._main = QtWidgets.QWidget()
        self.setCentralWidget(self._main)
        layout = QtWidgets.QVBoxLayout(self._main)

        self.static_canvas = FigureCanvas(Figure())
        layout.addWidget(self.static_canvas)
        self.addToolBar(NavigationToolbar(self.static_canvas, self))
    
    def update_plot(self,datasets):
        nplots=len(datasets)
        ncols=int(np.ceil(np.sqrt(nplots)))
        nrows=int(np.ceil(nplots/ncols))
        self.static_canvas.figure.clf()
        for i in range(nplots):
            ax=self.static_canvas.figure.add_subplot(nrows,ncols,i+1)
            ax.plot(datasets[i].Q,datasets[i].R)
            #ax.set_title(os.path.basename(datasets[i].filename))
            ax.set_yscale("log")
            ax.set_ylabel('Reflectivity')
            ax.set_xlabel('Q $(\AA^{-1})$')
        #self.static_canvas.figure.tight_layout()   
        self.static_canvas.draw()
        


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
        self.data_manager=data_manager_widget.data_manager()
        self.actionLoad_experiment_data.triggered.connect(self.load_experiment)
        self.figure=DataPlotWindow()
        self.pushButton_plot.clicked.connect(self.do_plot)

    def do_plot(self):
        datasets=self.data_manager.data_model.datasets
        if len(datasets)>0:
            self.figure.update_plot(datasets)
            self.figure.show()
        

    def load_experiment(self):
        self.data_manager.show()

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
    sm.addItem(layer.Layer(name='L0',thickness=1,nsld_real=5))
    sm.addItem(layer.Layer(name='L1',thickness=2.,nsld_real=3))
    sm.addItem(layer.Layer(name='L2',thickness=1,nsld_real=5))
    sm.substrate.nsld_real.vary=True
    sm.layers[0].nsld_real.vary=True
    sm.layers[0].nsld_real.expr='substrate.nsld_real'
    sm.layers[0].thickness.vary=True
    window = MainWindow([sm])
    window.show()
    sys.exit(app.exec_())
