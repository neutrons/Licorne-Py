import numpy as np
import operator


class NumericParameter(object):
    """
    A NumericParameter is an object used for fitting,
    modelled on lmfit.Parameter
    No validation for the order of minimum, maximum, value
    is being performed here
    Attributes
    ----------
    name : str
        NumericParameter name
    value : float
        The numerical value of the NumericParameter.
    vary : bool
        Whether the NumericParameter is fixed during a fit.
    minimum : float
        Lower bound for value (None or -inf means no lower bound).
    maximum : float
        Upper bound for value (None or inf means no upper bound).
    expr : str
        An expression specifying constraints for the NumericParameter. 
    """
    def __init__(self, name = None, value = None, 
                 minimum = -np.inf, maximum = np.inf,
                 vary = False,expr = None):
        """
        Parameters
        ----------
        name : str, optional
            Name of the parameter.
        value : float, optional
            Numerical Parameter value.
        vary : bool, optional
            Whether the Parameter is fixed during a fit.
        minimum : float, optional
            Lower bound for value (None or -inf means no lower bound).
        maximum : float, optional
            Upper bound for value (None or inf means no upper bound).
        expr : str, optional
            Mathematical expression used to constrain the value during the fit.
        """
        self._name = name
        self._minimum = minimum
        self._maximum = maximum
        self._value = value
        self._vary = vary
        self.expr = expr #TODO: validate expression

    name = property(operator.attrgetter('_name'))    
    @name.setter
    def name(self,n):
        if n is not None:
            self._name = str(n)
        else:
            self._name = ''

    minimum = property(operator.attrgetter('_minimum'))
    @minimum.setter
    def minimum(self,m):
        if m is None:
            self._minimum = -np.inf
        else:
            self._minimum = np.float(m)

    maximum = property(operator.attrgetter('_maximum'))
    @maximum.setter
    def maximum(self,m):
        if m is None:
            self._maximum = np.inf
        else:
            self._maximum = np.float(m)              

    value = property(operator.attrgetter('_value'))
    @value.setter
    def value(self,val):
        if val is not None:
            self._value=np.float(val)
        else:
            self._value = np.float(0.0)

    vary = property(operator.attrgetter('_vary'))
    @vary.setter
    def vary(self,val):
        self._vary = val in [True,1,'1','True','true']
            
    def __repr__(self):
        s=[]
        if self._name!='':
            s.append(self._name+':')
        s.append("Value: {0}".format(self._value))
        if self._vary:
            s.append("(Varying)")
        else:
            s.append("(Fixed)")
        s.append("Bounds: [{0},{1}]".format(self._minimum,self._maximum))
        s.append("Tie: {0}".format(self.expr))
        return ' '.join(s)
