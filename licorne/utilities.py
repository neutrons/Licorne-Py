import tempfile
import shutil
import numpy

class tempdir(object):
    """
    A class to create a temporary folder for one application instance
    """
    __tempdir=''
    def __init__(self):
        if self.__tempdir=='':
            tempdir.__tempdir=tempfile.mkdtemp(prefix='licorne')
    def del_tempdir(self):
        shutil.rmtree(self.__tempdir,ignore_errors=True)
        tempdir.__tempdir=''
    def get_tempdir(self):
        return self.__tempdir

def defaultQ():
    """
    return the default Q range if no data is loaded
    """
    return numpy.linspace(0.002,0.17,150)
