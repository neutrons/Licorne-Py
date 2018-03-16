from __future__ import (absolute_import, division, print_function)
from PyQt5 import QtCore, QtWidgets
import numpy as np
import copy
from licorne.layer import Layer
from licorne.generateSublayers import generateSublayers

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.cm
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection


class layerplot(QtWidgets.QWidget):
    def __init__(self, *args):
        QtWidgets.QWidget.__init__(self, *args)
        self.sample=[Layer(thickness=np.inf),Layer(thickness=np.inf)]
        self.setLayout(QtWidgets.QVBoxLayout())
        function_options=['NSLD_REAL','NSLD_IMAGINARY','MSLD_RHO','MSLD_THETA','MSLD_PHI','ROUGHNESS']
        self.combo = QtWidgets.QComboBox(self)
        for f in function_options:
            self.combo.addItem(f)
        self.function='NSLD_REAL'
        self.paintwidget=QtWidgets.QWidget(self)
        self.paintwidget.setMinimumSize(450,350)
        self.canvas = PlotCanvas(self.sample, self.function,self.paintwidget)
        self.hlayout=QtWidgets.QHBoxLayout()
        self.hlayout.addStretch(1)
        self.hlayout.addWidget(self.combo)
        self.hlayout.addStretch(1)
        self.layout().addLayout(self.hlayout)
        self.layout().addWidget(self.paintwidget)
        self.combo.activated[str].connect(self.functionSelected)

    def resizeEvent(self, event):
        self.canvas.setGeometry(self.paintwidget.rect())

    def updateSample(self,newsamplemodel):
        ll=copy.deepcopy(newsamplemodel.layers)
        ll.append(newsamplemodel.substrate)
        ll.insert(0,newsamplemodel.incoming_media)
        self.sample=ll
        self.canvas.updateLF(self.sample,self.function)

    def functionSelected(self,text):
        self.function=text
        self.canvas.updateLF(self.sample,self.function)


class PlotCanvas(FigureCanvas):
    selectionChanged=QtCore.pyqtSignal(int)
    def __init__(self, layers, function, parent=None):
        self.fig = Figure()
        self.fig.patch.set_facecolor('white')
        self.corresponding=[]
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self,
                QtWidgets.QSizePolicy.Expanding,
                QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.updateLF(layers,function)
        self.fig.canvas.mpl_connect('pick_event', self.onpick)
 
    def updateLF(self,newlayers,newfunction):
        self.data=newlayers
        self.variable=newfunction
        self.plot()

    def onpick(self,event):
        ind=event.ind[0]
        layer_ind=self.corresponding[ind]
        self.selectionChanged.emit(layer_ind)
        # for debug purposes
        #if layer_ind==len(self.data)-1:
        #    layer_ind='substrate'
        #if layer_ind==0:
        #    layer_ind='incoming media'
        #print('picked layer {0}'.format(layer_ind))

        return True

    def plot(self):
        ax = self.figure.add_subplot(111)
        sublayers,self.corresponding=plot_sublayers(ax, self.data, parameter=self.variable)
        self.figure.tight_layout()
        self.draw()


def plot_sublayers(ax, layers, parameter='NSLD_REAL'):
    sublayers,corresponding=generateSublayers(layers)
    thick=[sl.thickness.value for sl in sublayers]
    depth=np.array(thick)
    try:
        thic_kmax = depth[np.isfinite(depth)].max()
    except ValueError:
        # all layers are infinite (maybe just incoming media and substrate)
        thic_kmax = 1
    depth[np.isinf(depth)]=thic_kmax
    th1 = depth[corresponding.index(1)]
    depth = depth.cumsum()
    depth -= depth[corresponding.index(1)]-th1
    depth = np.insert(depth,0,depth[0]-thic_kmax)
    ax.clear()
    if parameter == 'NSLD_REAL':
        val=np.array([sl.nsld_real.value for sl in sublayers])
    elif parameter == 'NSLD_IMAGINARY':
        val=np.array([sl.nsld_imaginary.value for sl in sublayers])
    elif parameter == 'MSLD_RHO':
        val=np.array([sl.msld.rho.value for sl in sublayers])
    elif parameter == 'MSLD_THETA':
        val=np.array([sl.msld.theta.value for sl in sublayers])
    elif parameter == 'MSLD_PHI':
        val=np.array([sl.msld.phi.value for sl in sublayers])
    elif parameter == 'ROUGHNESS':
        val=np.array([layer.roughness.value for layer in layers[1:]])
    else:
        raise ValueError('The variable to be plotted could not be found')
    if parameter != 'ROUGHNESS':
        ax.plot(depth[1:],val,visible=False)
        ax.plot([-1],[0.],visible=False)
        patches=[]
        for i,v in enumerate(val):
            polygon=Polygon([[depth[i],0.],[depth[i],v],[depth[i+1],v],[depth[i+1],0]],True)
            patches.append(polygon)
        xmin,xmax=ax.get_xlim()
        patches[0]=Polygon([[xmin,0.],[xmin,val[0]],[depth[1],val[0]],[depth[1],0]],True)
        patches[-1]=Polygon([[depth[-2],0.],[depth[-2],val[-1]],[xmax,val[-1]],[xmax,0]],True)
        p = PatchCollection(patches, cmap=matplotlib.cm.jet, alpha=0.4, picker=True)
        p.set_array(np.array(corresponding))
        ax.add_collection(p)
        ax.ticklabel_format(axis='y', style='sci', scilimits=(-2,2))
    if parameter== 'ROUGHNESS':
        ax.plot([-1,depth[1],depth[-1]],[0,np.max(val),np.min(val)],visible=False)
        xmin, xmax = ax.get_xlim()
        lthick = [l.thickness.value for l in layers[1:]]
        lthick.insert(0,0.)
        lthick = np.array(lthick[:-1])
        depth = lthick.cumsum()
        ax.stem(depth,val,linefmt='--')
        #ax.scatter(depth,val,c=np.arange(len(val)))
        ax.set_xlim(xmin,xmax)
    ax.axhline(y=0)
    ax.set_xlabel('Depth')
    ax.set_ylabel(parameter.replace('_', ' '))
    return sublayers, corresponding


if __name__ == '__main__':
    # This is for testing purposes only
    import sys
    app=QtWidgets.QApplication(sys.argv)
    mainForm=layerplot()
    from licorne.layer import RoughnessModel
    newSample=[Layer(thickness=np.inf,nsld_real=1.5),
               Layer(thickness=20.,nsld_real=1.),
               Layer(thickness=25.,nsld_real=3.,roughness=5, roughness_model=RoughnessModel.TANH,sublayers=7),
               Layer(thickness=30.,nsld_real=5.,msld_rho=7e-7,roughness=3, roughness_model=RoughnessModel.TANH,sublayers=7),
               Layer(nsld_real=4.,thickness=np.inf)]
    mainForm.updateSample(newSample)
    mainForm.show()
    sys.exit(app.exec_())
