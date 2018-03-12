from lmfit import Parameter, Parameters
from licorne.NumericParameter import NumericParameter


def convert_to_parameter(obj, name):
    """
    Converts a numeric parameter to an lmfit Parameter
    """
    return Parameter(name = name,
                     value = obj.value,
                     vary = obj.vary,
                     min = obj.minimum,
                     max = obj.maximum,
                     expr = obj.expr)


class ModelAdapter(object):
    """
    Adapter class to mediate between the Licorne representation of a set of layers
    and a parameter set we can pass to lmfit.
    """
    def __init__(self, sample_model):
        self.sample_model = sample_model

    def __repr__(self):
        output = ''
        return output

    def params_from_model(self):
        """
        Generate a parameter set with a given layer model.
        """
        params = Parameters()
        all_layers = [self.sample_model.incoming_media] + self.sample_model.layers + [self.sample_model.substrate]
        attribute_list=['thickness','nsld_real','nsld_imaginary','msld','roughness']
        msld_attribute_list=['rho','theta','phi']
        for i, l in enumerate(all_layers):
            l_name = l.name
            if l_name == '':
                l_name = 'Layer{0}'.format(i)
            for attribute in attribute_list:
                num_par = l.__getattribute__(attribute)
                if attribute == 'msld':
                    for msld_attribute in msld_attribute_list:
                        msld_par=num_par.__getattribute__(msld_attribute)
                        par = convert_to_parameter(msld_par,'.'.join([l_name,'msld',msld_attribute]))
                        params[par.name.replace('.','___').replace(' ','__')] = par
                else:
                    par = convert_to_parameter(num_par,'.'.join([l_name,attribute]))
                    params[par.name.replace('.','___').replace(' ','__')] = par
        return params

    def update_model_from_params(self,params):
        for i, p in enumerate(params):
            name = params[p].name.replace('___', '.').replace('__', ' ')
            if i//7 == 0:
                layer = self.sample_model.incoming_media
            elif i//7 == len(params)//7-1:
                layer = self.sample_model.substrate
            else:
                layer = self.sample_model.layers[i%7-1]
            property_name = name.split(layer.name+'.')[1]
            if 'msld' in property_name:
                msld_property_name = property_name.split('.')[1]
                layer.msld.__setattr__(msld_property_name, NumericParameter(name=msld_property_name,
                                                                            value=params[p].value,
                                                                            minimum=params[p].min,
                                                                            maximum=params[p].max,
                                                                            vary=params[p].vary,
                                                                            expr=params[p].expr))
            else:
                layer.__setattr__(property_name, NumericParameter(name=property_name,
                                                                  value=params[p].value,
                                                                  minimum=params[p].min,
                                                                  maximum=params[p].max,
                                                                  vary=params[p].vary,
                                                                  expr=params[p].expr))



if __name__ == "__main__":
    from licorne.SampleModel import SampleModel
    sm = SampleModel()
    print(sm.substrate)
    ma = ModelAdapter(sm)
    ps = ma.params_from_model()
    ps['substrate___nsld_real'].value=42.
    ps['substrate___msld___rho'].min=42.5
    ma.update_model_from_params(ps)
    print(sm.substrate)