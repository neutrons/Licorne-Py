from PyQt5 import QtCore
import licorne.layer
import numpy as np
from six import Iterator


class SampleModelIterator(Iterator):
    """
    Implements an iterator over the SampleModel.layers
    """
    def __init__(self,SampleModelInstance):
        self.SampleModelInstance=SampleModelInstance
        self._index=0

    def __next__(self):
        try:
            result=self.SampleModelInstance.layers[self._index]
        except IndexError:
            raise StopIteration
        self._index += 1
        return result


class SampleModel(QtCore.QAbstractListModel):
    """
    SampleModel is a class to wrap layers, substrate, and incoming media
    It can be used for both calculations and UI display
    """
    def __init__(self, *args, **kwargs):
        """
        Create a sample model with only an incoming media and substrate
        """
        QtCore.QAbstractListModel.__init__(self, *args, **kwargs)
        self.incoming_media=licorne.layer.Layer(name='incoming media',thickness=np.inf)
        self.substrate=licorne.layer.Layer(name='substrate',thickness=np.inf)
        self.layers = []

    def rowCount(self, parent=None):
        """
        UI related
        returns numbers of layers+substrate+incoming_media
        """
        return len(self.layers)+2

    def data(self, index, role=QtCore.Qt.DisplayRole):
        """
        UI related
        function to return the names of the layers (including substrate and incoming media)
        for display purposes
        """
        display_names = [l.name if l.name!='' else 
                         'Layer{0}'.format(i-1) 
                         for i,l in enumerate([self.incoming_media]+self.layers+[self.substrate])]
        if not index.isValid():
            return QtCore.QVariant()
        elif role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()
        return QtCore.QVariant(display_names[index.row()])

    def addItem(self,item,position=None):
        """
        UI and data related
        add a single layer at the end of the layer list
        """
        if position is None:
            position = len(self.layers)
        if not isinstance(item,licorne.layer.Layer):
            return
        self.beginInsertRows(QtCore.QModelIndex(), position, position)
        self.layers.insert(position, item)
        self.endInsertRows()

    def delItem(self,position):
        """
        UI and data related
        delete a single layer (but not incoming media or substrate).
        The position is the index in the self.layer
        This allows to handle UI stuff
        """
        if position in range(len(self.layers)):
            #The UI position needs to account for substrate/incoming media
            self.beginRemoveRows(QtCore.QModelIndex(), position+1, position+1)
            del self.layers[position]
            self.endRemoveRows()

    # iterate over the layers, no substrate
    def __iter__(self):
        return SampleModelIterator(self)

    def move_down_1(self,selected_indices):
        """
        UI and data related
        Move one or more layers up (towards substrate)
        selected_indices : iterable (list)
            indices of the layers to be moved. It won't affect substrate or incoming media
        """
        if set(selected_indices)<set(range(len(self.layers)-1)):
            for si in selected_indices[::-1]:
                if not self.beginMoveRows(QtCore.QModelIndex(), si-1, si-1, QtCore.QModelIndex(), si+1):
                    return
                self.layers[si],self.layers[si+1]=self.layers[si+1],self.layers[si]
                self.endMoveRows()
        
    def move_up_1(self,selected_indices):
        if set(selected_indices)<set(range(1,len(self.layers))):
            for si in selected_indices:
                if not self.beginMoveRows(QtCore.QModelIndex(), si+1, si+1, QtCore.QModelIndex(), si):
                    return
                self.layers[si-1],self.layers[si]=self.layers[si],self.layers[si-1]
                self.endMoveRows()

    def get_names_list(self):
        names = [self.substrate.name,self.incoming_media.name]
        for l in self.layers:
            names.append(l.name)
        return names
