from __future__ import absolute_import, division, print_function, unicode_literals
import sys, os, copy
import numpy as np
import matplotlib
matplotlib.use('qt5agg')
import licorne.layer
import licorne.SampleModel
import licorne.LayerList
import licorne.data_manager_widget as data_manager_widget
import licorne.utilities as lu
import licorne.generateSublayers
import licorne.reflection
import licorne.resolutionselector
from licorne.model_adapter import ModelAdapter
from lmfit import minimize, report_fit

from matplotlib.backends.backend_qt5agg import (
    FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure
from PyQt5 import QtWidgets, QtCore, uic

ui = os.path.join(os.path.dirname(__file__), 'UI/MainWindow.ui')
Ui_MainWindow, QtBaseClass = uic.loadUiType(ui)

matplotlib.rcParams['text.usetex'] = True
matplotlib.rcParams['text.latex.preamble'] = ['\\' + 'usepackage{amsmath}']


class DataPlotWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(DataPlotWindow, self).__init__()
        self.setWindowTitle('Reflectivity')
        self._main = QtWidgets.QWidget()
        self.setCentralWidget(self._main)
        layout = QtWidgets.QVBoxLayout(self._main)

        self.static_canvas = FigureCanvas(Figure())
        # noinspection PyTypeChecker
        layout.addWidget(self.static_canvas)
        # noinspection PyTypeChecker
        self.addToolBar(NavigationToolbar(self.static_canvas, self))

    def update_plot(self, data_model):
        n_plots = len(data_model.datasets)
        n_cols = int(np.ceil(np.sqrt(n_plots)))
        n_rows = int(np.ceil(n_plots / n_cols))
        self.static_canvas.figure.clf()
        for i in range(n_plots):
            ax = self.static_canvas.figure.add_subplot(n_rows, n_cols, i + 1)
            if data_model.datasets[i].R is not None:
                ax.plot(data_model.datasets[i].Q,
                        data_model.datasets[i].R * data_model.experiment_factor,
                        color=lu.data_color(), label='exp')
            if data_model.datasets[i].R_calc is not None:
                ax.plot(data_model.datasets[i].Q,
                        data_model.datasets[i].R_calc * data_model.theory_factor + data_model.background,
                        color=lu.calculated_color(),
                        label='calc')
            ax.set_yscale("log")
            ax.set_ylabel('Reflectivity')
            ax.set_xlabel(r'Q $({\mathrm \AA}^{-1})$')
            ax.set_title('Pol:{0} Ana:{1}'.format(data_model.datasets[i].pol_Polarizer,
                                                  data_model.datasets[i].pol_Analyzer))
            if data_model.datasets[i].R is not None or data_model.datasets[i].R_calc is not None:
                ax.legend()
        self.static_canvas.figure.tight_layout()
        self.static_canvas.draw()


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, sample_model):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.sample_model = None
        self.data_model = None
        self.selection = []
        self.figure = []
        self.data_manager = data_manager_widget.data_manager()
        sys.path.append(lu.tempdir().get_tempdir())
        self.update_sample_model(sample_model)
        licorne.resolutionselector.resolutionselector()

        self.layerselector_widget.listView.selectionModel().selectionChanged.connect(self.update_selection)
        self.layerselector_widget.listView.selectionModel().selectionChanged.connect(
            self.layerselector_widget.selectionChanged)
        self.layerselector_widget.sampleModelChanged[licorne.SampleModel.SampleModel].connect(self.update_sample_model)
        self.layer_properties_widget.sampleModelChanged[licorne.SampleModel.SampleModel].connect(self.refresh)
        self.plot_widget.canvas.selectionChanged.connect(self.plot_set_selection)
        self.actionLoad_experiment_data.triggered.connect(self.load_experiment)
        self.actionLoad_layers.triggered.connect(self.load_layers)
        self.actionSave_layers.triggered.connect(self.save_layers)
        self.pushButton_plot.clicked.connect(self.do_plot)
        self.pushButton_fit.clicked.connect(self.do_fit)
        self.plot_widget.updateSample(self.sample_model)
        self.data_manager.dataModelChanged.connect(self.update_data_model)

    def update_data_model(self,data_model):
        self.data_model=data_model

        if len(self.figure) > 0:
            if len(self.data_manager.data_model.datasets) > 0:
                self.calculate_reflectivity()
                self.figure[-1].update_plot(self.data_manager.data_model)
            else:
                self.figure[-1].static_canvas.figure.clf()
                self.figure[-1].static_canvas.draw()

    def plot_set_selection(self, selection):
        layer_index = self.layerselector_widget.sample_model.index(selection)
        self.layerselector_widget.listView.selectionModel().select(layer_index, QtCore.QItemSelectionModel.Toggle)

    def refresh(self, new_sample_model):
        if isinstance(new_sample_model, licorne.SampleModel.SampleModel):
            self.sample_model = new_sample_model
            self.update_sample_model(self.sample_model)
        if self.selection:
            for s in self.layerselector_widget.listView.selectionModel().selectedRows():
                self.layerselector_widget.listView.selectionModel().select(s, QtCore.QItemSelectionModel.Deselect)
                self.layerselector_widget.listView.selectionModel().select(s, QtCore.QItemSelectionModel.Select)

    def closeEvent(self, event):
        try:
            self.data_manager.close()
        except:
            pass
        for f in self.figure:
            try:
                f.close()
            except:
                pass
        lu.tempdir().del_tempdir()
        event.accept()

    def do_plot(self):
        if self.data_model is None:
            print("Load/generate some experimental data first")
            return
        self.figure.append(DataPlotWindow())
        if len(self.data_model.datasets) > 0:
            self.calculate_reflectivity()
            self.figure[-1].update_plot(self.data_model)
            self.figure[-1].show()

    def load_experiment(self):
        self.data_manager.show()

    def save_layers(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        fileName, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Layers",
                                                            "", "YAML (*.yaml);;All Files (*)",
                                                            options=options)
        if fileName:
            licorne.LayerList.save_layers(self.sample_model.layers,
                                          self.sample_model.incoming_media,
                                          self.sample_model.substrate,
                                          fileName)

    def load_layers(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Load Layers",
                                                            "", "YAML (*.yaml);;All Files (*)",
                                                            options=options)
        if file_name:
            ll = licorne.LayerList.load_layers(file_name)
            sm = licorne.SampleModel.SampleModel()
            sm.incoming_media = copy.deepcopy(ll[0])
            sm.substrate = copy.deepcopy(ll[-1])
            for l in ll[1:-1]:
                sm.addItem(l)
            self.update_sample_model(sm)

    def update_sample_model(self, sample_model):
        self.sample_model = sample_model
        self.layerselector_widget.set_sample_model(self.sample_model)

        all_layers = [s for s in [self.sample_model.incoming_media] +
                      self.sample_model.layers +
                      [self.sample_model.substrate]]

        self.layer_properties_widget.set_layer_list(self.sample_model)
        self.layer_properties_widget.set_selection(self.selection)
        self.generate_parameter_list()
        self.plot_widget.updateSample(self.sample_model)
        self.update_data_model(self.data_model)

    def update_selection(self, selected, deselected):
        all_selected = self.layerselector_widget.listView.selectionModel().selectedRows()
        self.selection = sorted([s.row() for s in all_selected])
        self.layer_properties_widget.set_selection(self.selection)

    def generate_parameter_list(self):
        string_list = ['Layer\tParameter\t\tTied to:', '=' * 35]
        indexes, names, parameters, ties = licorne.LayerList.generate_parameter_lists(self.sample_model.layers,
                                                                                      self.sample_model.incoming_media,
                                                                                      self.sample_model.substrate)
        for i, n, p, t in zip(indexes, names, parameters, ties):
            if n in ['substrate', 'incoming_media']:
                name = n
            else:
                name = 'Layer{0}'.format(i - 1)
            string_list.append('{0}\t{0}.{1}\t{2}'.format(name, p, t))
        self.fit_parameters_textEdit.setText('\n'.join(string_list))

    def calculate_reflectivity(self):
        layers=[self.sample_model.incoming_media]+self.sample_model.layers+[self.sample_model.substrate]
        sublayers = licorne.generateSublayers.generateSublayers(layers)[0]
        for ds in self.data_model.datasets:
            Q = ds.Q/2.
            R = licorne.reflection.reflection(Q,sublayers)
            pol_eff = np.ones(len(Q), dtype = np.complex128)
            an_eff = np.ones(len(Q), dtype = np.complex128)
            RR = np.real(licorne.reflection.spin_av(R, ds.pol_Polarizer, ds.pol_Analyzer, pol_eff,an_eff))
            import resolution
            sigma = resolution.resolution(Q)
            RRr = licorne.reflection.resolut(RR, Q, sigma, 3)
            ds.R_calc=RRr

    def calculate_residuals(self,parameters):
        sm = copy.deepcopy(self.sample_model)
        ma = ModelAdapter(sm)
        ma.update_model_from_params(parameters)
        layers=[sm.incoming_media]+sm.layers+[sm.substrate]
        sublayers = licorne.generateSublayers.generateSublayers(layers)[0]
        chi_array=[]
        for ds in self.data_model.datasets:
            if ds.R is not None and len(ds.R)>1:
                Q = ds.Q/2.
                R = licorne.reflection.reflection(Q,sublayers)
                pol_eff = np.ones(len(Q), dtype = np.complex128)
                an_eff = np.ones(len(Q), dtype = np.complex128)
                RR = np.real(licorne.reflection.spin_av(R, ds.pol_Polarizer, ds.pol_Analyzer, pol_eff,an_eff))
                import resolution
                sigma = resolution.resolution(Q)
                #FIXME: do resolution convolution (slow)
                RRr = RR#licorne.reflection.resolut(RR, Q, sigma, 3)
                chi_array.append((RRr-ds.R)/ds.E)
        print(np.array(chi_array).ravel().mean())
        return np.array(chi_array).ravel()

    def do_fit(self):
        #TODO: move to separate thread
        if self.data_model is None or len(self.data_model.datasets) == 0:
            print("Not enough data to fit. Please load more data")
            return
        enough_data=False
        for ds in self.data_model.datasets:
            if ds.R is not None and 1 < len(ds.R) == len(ds.E):
                enough_data=True
        if not enough_data:
            print("Could not find data to fit. Did you load any real data?")
            return
        ma = ModelAdapter(self.sample_model)
        parameters=ma.params_from_model()
        result=minimize(self.calculate_residuals,parameters,method=lu.get_minimizer())
        #report_fit(result)
        ma.update_model_from_params(result.params)
        self.refresh(self.sample_model)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    temp_dir=lu.tempdir()
    sm = licorne.SampleModel.SampleModel()
    from licorne.layer import RoughnessModel

    sm.incoming_media.name = 'Air'
    siox = licorne.layer.Layer(name = 'SiOx',
                               thickness = 18.,
                               nsld_real = 2e-6,
                               sublayers=10,
                               roughness=3,
                               roughness_model=RoughnessModel.ERFC)
    siox._nsld_real.vary=True
    siox._nsld_real.minimum=1e-6
    siox._nsld_real.maximum=4e-6
    siox._thickness.vary = True
    siox._thickness.minimum = 1
    siox._thickness.maximum = 50
    siox._roughness.vary = True
    siox._roughness.minimum = 1
    siox._roughness.maximum = 8
    sm.addItem(siox)
    sm.substrate.name = 'Si'
    sm.substrate.nsld_real = 2.07e-6
    sm.substrate.roughness = 3.
    sm.substrate.roughness_model = RoughnessModel.ERFC
    sm.substrate.sublayers = 8
    sm.substrate.roughness.vary = True
    sm.substrate.roughness.minimum = 1
    sm.substrate.roughness.maximum = 10
    window = MainWindow(sm)
    window.show()
    sys.exit(app.exec_())
