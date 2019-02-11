from __future__ import absolute_import, division, print_function, unicode_literals
import sys, os, copy
import yaml
import numpy as np
import matplotlib
import zipfile
import shutil

matplotlib.use('qt5agg')
import licorne.layer
import licorne.SampleModel
import licorne.LayerList
import licorne.data_manager_widget as data_manager_widget
import licorne.data_model
import licorne.utilities as lu
import licorne.generateSublayers
import licorne.reflection
import licorne.resolutionselector
from licorne.model_adapter import ModelAdapter
from lmfit import minimize, report_fit, Parameters, minimizer
from licorne.fit_worker import FitWorker

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
                ax.errorbar(data_model.datasets[i].Q,
                            data_model.datasets[i].R * data_model.experiment_factor,
                            data_model.datasets[i].E * data_model.experiment_factor,
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
        self.fit_results_widget = None

        sys.path.append(lu.tempdir().get_tempdir())

        self.data_manager = data_manager_widget.data_manager()
        self.resolution_selector = licorne.resolutionselector.resolutionselector()

        self.update_sample_model(sample_model)

        self.layerselector_widget.listView.selectionModel().selectionChanged.connect(self.update_selection)
        self.layerselector_widget.listView.selectionModel().selectionChanged.connect(
            self.layerselector_widget.selectionChanged)
        self.layerselector_widget.sampleModelChanged[licorne.SampleModel.SampleModel].connect(self.update_sample_model)
        self.layer_properties_widget.sampleModelChanged[licorne.SampleModel.SampleModel].connect(self.refresh)
        self.plot_widget.canvas.selectionChanged.connect(self.plot_set_selection)
        self.data_manager.dataModelChanged.connect(self.update_data_model)
        # menu items
        self.actionLoad_experiment_data.triggered.connect(self.load_experiment)
        self.actionLoad_layers.triggered.connect(self.load_layers)
        self.actionSave_layers.triggered.connect(self.save_layers)
        self.actionSave_status.triggered.connect(self.save_state_dialog)
        self.actionLoad_status.triggered.connect(self.load_state_dialog)
        self.actionSave_report.triggered.connect(self.save_report)

        self.pushButton_plot.clicked.connect(self.do_plot)
        self.pushButton_fit.clicked.connect(self.do_fit)
        self.plot_widget.updateSample(self.sample_model)

        self.fit_thread = FitWorker()
        self.fit_thread.chiSquaredChanged[float].connect(self.update_fit)
        self.fit_thread.smChanged[minimizer.MinimizerResult].connect(self.update_from_fit_parameters)

    def save_report(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save report",
                                                             "", "zip (*.zip);;All Files (*)",
                                                             options=options)
        if file_name:
            folder=os.path.join(lu.tempdir().get_tempdir(),
                                os.path.splitext(os.path.basename(file_name))[0])
            if os.path.isdir(folder):
                shutil.rmtree(folder)
            os.mkdir(folder)
            files_to_zip=[]
            #save layers
            with open(os.path.join(folder,'layers.txt'),'w') as f:
                f.write('#incoming media\n')
                f.write(self.sample_model.incoming_media.__repr__())
                f.write('\n#layers\n')
                for l in self.sample_model.layers:
                    f.write(l.__repr__()+'\n')
                f.write('#substrate\n')
                f.write(self.sample_model.substrate.__repr__())
            files_to_zip.append(os.path.join(folder,'layers.txt'))
            #save sublayers
            with open(os.path.join(folder,'sublayers.txt'),'wb') as f:
                layers = [self.sample_model.incoming_media] + self.sample_model.layers + [self.sample_model.substrate]
                sublayers = licorne.generateSublayers.generateSublayers(layers)[0]
                values=[[sl.thickness.value, sl.nsld_real.value,
                         sl.nsld_imaginary.value, sl.msld.rho.value,
                         sl.msld.theta.value, sl.msld.phi.value] for sl in sublayers]
                np.savetxt(f,np.array(values),delimiter=',', fmt=str('%1.6e'),
                           header='thickness, nsld_real, nsld_imaginary, msld_rho, msld_theta, msld_phi')
            files_to_zip.append(os.path.join(folder,'sublayers.txt'))
            #save resolution
            resolution_filename = os.path.join(lu.tempdir().get_tempdir(),'resolution.py')
            files_to_zip.append(resolution_filename)
            #save experimental data and calculated reflectivity
            if self.data_model is not None:
                 with open(os.path.join(folder,'data.txt'),'w') as f:
                    f.write('# Background = {}\n'.format(self.data_model.background))
                    f.write('# Theory normalization factor = {}\n'.format(self.data_model.theory_factor))
                    f.write('# Experiment multiplicative factor = {}\n'.format(self.data_model.experiment_factor))
                    f.write('\n# Data\n')
                    for i,ds in enumerate(self.data_model.datasets):
                        if ds.Q is not None:
                            f.write('\n# ----- Dataset {} -----\n'.format(i))
                            f.write('# Experimental data filename = {}\n'.format(ds.filename))
                            f.write('# Polarization polarizer = {}\n'.format(ds.pol_Polarizer))
                            f.write('# Polarization analyzer = {}\n'.format(ds.pol_Analyzer))
                            ds_temp=copy.deepcopy(ds)
                            lq=len(ds_temp.Q)
                            if ds_temp.R is None:
                                ds_temp.R=['']*lq
                            if ds_temp.E is None:
                                ds_temp.E=['']*lq
                            if ds_temp.R_calc is None:
                                ds_temp.R_calc=['']*lq
                            f.write('# Q,  R_measured,  Error, R_calculated\n')
                            for j in range(lq):
                                f.write('{}, {}, {}, {}\n'.format(ds_temp.Q[j], ds_temp.R[j], ds_temp.E[j], ds_temp.R_calc[j]))
                 files_to_zip.append(os.path.join(folder,'data.txt'))
            with zipfile.ZipFile(file_name, 'w') as myzip:
                for f in files_to_zip:
                    myzip.write(f,os.path.basename(f))


    def update_from_fit_parameters(self, pars):
        ma = ModelAdapter(self.sample_model)
        ma.update_model_from_params(pars.params)
        output_string = 'Reduced chi square = {0:.5f}\n\n'.format(pars.redchi)
        for parameter in pars.params:
            if pars.params[parameter].vary:
                output_string += pars.params[parameter].name.replace('___', '.').replace('__', ' ')
                output_string += ' {0:.5}'.format(float(pars.params[parameter].value))
                if pars.errorbars:
                    output_string += ' +/- {0:.5}'.format(float(pars.params[parameter].stderr))
                output_string += ' (initial value: {0:.5})\n'.format(float(pars.init_values[parameter]))
        self.refresh(self.sample_model)
        self.fit_results_widget = QtWidgets.QTextEdit(readOnly=True, minimumWidth=700)
        self.fit_results_widget.setText(output_string)
        self.fit_results_widget.show()

    def update_fit(self, value):
        self.pushButton_fit.setText('Fit chi={0:.4f}'.format(value))

    def update_data_model(self, data_model):
        self.data_model = data_model
        self.update_data_figure()

    def update_data_figure(self):
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
        """
        sample model changed, including number of layers
        """
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
        try:
            self.fit_results_widget.close()
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
        file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Layers",
                                                             "", "YAML (*.yaml);;All Files (*)",
                                                             options=options)
        if file_name:
            licorne.LayerList.save_layers(self.sample_model.layers,
                                          self.sample_model.incoming_media,
                                          self.sample_model.substrate,
                                          file_name)

    def save_state_dialog(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save state",
                                                             "", "YAML (*.yaml);;All Files (*)",
                                                             options=options)
        if file_name:
            self.save_state_yaml(file_name)

    def save_state_yaml(self, filename):
        state = {}
        if self.sample_model is not None:
            state['model'] = dict(layers=self.sample_model.layers,
                                  incoming_media=self.sample_model.incoming_media,
                                  substrate=self.sample_model.substrate)
        if self.data_model is not None:
            state['experimental_data'] = dict(datasets=self.data_model.datasets,
                                              background=self.data_model.background,
                                              theory_factor=self.data_model.theory_factor,
                                              experiment_factor=self.data_model.experiment_factor)
        resolution_filename = os.path.join(lu.tempdir().get_tempdir(),'resolution.py')
        with open(resolution_filename) as rf:
            state['resolution'] = rf.read()
        try:
            with open(filename, 'w') as f:
                yaml.dump(state, f)
        except IOError:
            pass  # TODO: error message

    def load_state_dialog(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Load state",
                                                             "", "YAML (*.yaml);;All Files (*)",
                                                             options=options)
        if file_name and os.path.isfile(file_name):
            self.load_state_yaml(file_name)

    def load_state_yaml(self,file_name):
        with open(file_name,'r') as f:
            state=yaml.load(f)

        if 'model' in state.keys():
            temp_sample_model=licorne.SampleModel.SampleModel()
            temp_sample_model.layers=state['model']['layers']
            temp_sample_model.incoming_media=state['model']['incoming_media']
            temp_sample_model.substrate=state['model']['substrate']
            self.selection = []
            self.refresh(temp_sample_model)

        if 'experimental_data' in state.keys():
            self.data_model=licorne.data_model.data_model()
            self.data_model.datasets=state['experimental_data']['datasets']
            self.data_model.background=state['experimental_data']['background']
            self.data_model.experiment_factor=state['experimental_data']['experiment_factor']
            self.data_model.theory_factor=state['experimental_data']['theory_factor']
            self.data_manager.update_data_model(self.data_model)

        resolution_filename = os.path.join(lu.tempdir().get_tempdir(),'CustomResolution.py')
        with open(resolution_filename,'w') as rf:
            rf.write(state['resolution'])
        self.data_manager.resolution_dialog.comboBox_resolution_mode.setCurrentIndex(2)  # custom
        self.data_manager.resolution_dialog.resolution_mode_changed('Custom')

        self.update_data_figure()

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
        """
        only layer properties changed, not selection/number of layers
        """
        self.sample_model = sample_model
        self.layerselector_widget.set_sample_model(self.sample_model)

        self.layer_properties_widget.set_layer_list(self.sample_model)
        self.layer_properties_widget.set_selection(self.selection)
        self.generate_parameter_list()
        self.plot_widget.updateSample(self.sample_model)
        self.update_data_model(self.data_model)
        self.pushButton_fit.setText('Fit')

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
                name = 'Layer{0}'.format(i)
            string_list.append('{0}\t{0}.{1}\t{2}'.format(name, p, t))
        self.fit_parameters_textEdit.setText('\n'.join(string_list))

    def calculate_reflectivity(self):
        layers = [self.sample_model.incoming_media] + self.sample_model.layers + [self.sample_model.substrate]
        sublayers = licorne.generateSublayers.generateSublayers(layers)[0]
        for ds in self.data_model.datasets:
            Q = ds.Q / 2.
            R = licorne.reflection.reflection(Q, sublayers)
            pol_eff = np.ones(len(Q), dtype=np.complex128)
            an_eff = np.ones(len(Q), dtype=np.complex128)
            RR = np.real(licorne.reflection.spin_av(R, ds.pol_Polarizer, ds.pol_Analyzer, pol_eff, an_eff))
            import resolution
            sigma = resolution.resolution(Q)
            RRr = licorne.reflection.resolut(RR, Q, sigma, 4)
            ds.R_calc = RRr

    def calculate_residuals(self, parameters):
        sm = copy.deepcopy(self.sample_model)
        ma = ModelAdapter(sm)
        ma.update_model_from_params(parameters)
        layers = [sm.incoming_media] + sm.layers + [sm.substrate]
        sublayers = licorne.generateSublayers.generateSublayers(layers)[0]
        chi_array = []
        for ds in self.data_model.datasets:
            if ds.R is not None and len(ds.R) > 1:
                Q = ds.Q / 2.
                R = licorne.reflection.reflection(Q, sublayers)
                pol_eff = np.ones(len(Q), dtype=np.complex128)
                an_eff = np.ones(len(Q), dtype=np.complex128)
                RR = np.real(licorne.reflection.spin_av(R, ds.pol_Polarizer, ds.pol_Analyzer, pol_eff, an_eff))
                import resolution
                sigma = resolution.resolution(Q)
                RRr = licorne.reflection.resolut(RR, Q, sigma, 4)*self.data_model.theory_factor+self.data_model.background
                chi_array.append((RRr/self.data_model.experiment_factor - ds.R) / ds.E)
        chi = np.array(chi_array).ravel()
        print((chi ** 2).mean())
        return chi

    def do_fit(self):
        if self.data_model is None or len(self.data_model.datasets) == 0:
            print("Not enough data to fit. Please load more data")
            return
        enough_data = False
        for ds in self.data_model.datasets:
            if ds.R is not None and 1 < len(ds.R) == len(ds.E):
                enough_data = True
        if not enough_data:
            print("Could not find data to fit. Did you load any real data?")
            return
        self.fit_thread.initialize(self.sample_model, self.data_model)
        self.fit_thread.start()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    temp_dir = lu.tempdir()
    smod = licorne.SampleModel.SampleModel()
    from licorne.layer import RoughnessModel

    smod.substrate.nsld = 3.533e-6
    smod.substrate.roughness = 5.
    smod.substrate.roughness_model = RoughnessModel.TANH
    smod.substrate.sublayers = 3

    layer_1 = licorne.layer.Layer(thickness=40.129,
                                  nsld_real=2.6091e-6,
                                  nsld_imaginary=-3e-8,
                                  msld_phi=0,
                                  msld_theta=90,
                                  sublayers=5,
                                  roughness=20,
                                  roughness_model=RoughnessModel.TANH)
    layer_2 = licorne.layer.Layer(thickness=44.7345,
                                  nsld_real=3.5471e-6,
                                  nsld_imaginary=-3e-8,
                                  msld_phi=0,
                                  msld_theta=90,
                                  sublayers=5,
                                  roughness=5,
                                  roughness_model=RoughnessModel.TANH)
    layer_3 = licorne.layer.Layer(thickness=74.9724,
                                  nsld_real=2.7438e-6,
                                  nsld_imaginary=-3e-8,
                                  msld_rho=8.3597e-007,
                                  msld_theta=90,
                                  msld_phi=22.83,
                                  sublayers=5,
                                  roughness=5.7701,
                                  roughness_model=RoughnessModel.TANH)
    layer_4 = licorne.layer.Layer(thickness=182.5007,
                                  nsld_real=2.3033e-6,
                                  nsld_imaginary=-3e-8,
                                  msld_rho=2.7461e-006,
                                  msld_phi=30,
                                  msld_theta=90,
                                  sublayers=5,
                                  roughness=10.0965,
                                  roughness_model=RoughnessModel.TANH)
    layer_5 = licorne.layer.Layer(thickness=37.4808,
                                  nsld_real=2.3092e-006,
                                  nsld_imaginary=-3e-8,
                                  msld_rho=1.6061e-007,
                                  msld_phi=160,
                                  msld_theta=90,
                                  sublayers=5,
                                  roughness=5,
                                  roughness_model=RoughnessModel.TANH)
    layer_6 = licorne.layer.Layer(thickness=233.4451,
                                  nsld_real=6.0653e-006,
                                  nsld_imaginary=0,
                                  msld_rho=0,
                                  msld_theta=90,
                                  sublayers=5,
                                  roughness=5,
                                  roughness_model=RoughnessModel.TANH)
    layer_7 = licorne.layer.Layer(thickness=12.601,
                                  nsld_real=4.1822e-006,
                                  nsld_imaginary=0,
                                  msld_rho=1.9973e-008,
                                  msld_theta=90,
                                  sublayers=5,
                                  roughness=9.8641,
                                  roughness_model=RoughnessModel.TANH)
    layer_8 = licorne.layer.Layer(thickness=212.6825,
                                  nsld_real=3.7e-006,
                                  nsld_imaginary=0,
                                  msld_rho=9.452e-007,
                                  msld_phi=10,
                                  msld_theta=90,
                                  sublayers=5,
                                  roughness=15.8909,
                                  roughness_model=RoughnessModel.TANH)
    layer_3.msld.phi.vary = True
    layer_4.msld.phi.vary = True
    layer_5.msld.phi.vary = True
    layer_7.msld.phi.vary = True
    layer_8.msld.phi.vary = True
    smod.layers = [layer_1, layer_2, layer_3, layer_4, layer_5, layer_6, layer_7, layer_8]
    window = MainWindow(smod)
    window.show()
    sys.exit(app.exec_())
