def generate_available_ties(layer_list,incoming_media, substrate):
    ties_nsld_real=[]
    ties_nsld_imaginary=[]
    ties_msld_rho=[]
    ties_msld_theta=[]
    ties_msld_phi=[]
    ties_roughness=[]
    ties_thickness=[]
    for i,l in enumerate(layer_list):
        if l.nsld_real.vary and l.nsld_real.expr=='':
            ties_nsld_real.append("Layer{0}.nsld_real".format(i))
        if l.nsld_imaginary.vary and l.nsld_imaginary.expr=='':
            ties_nsld_imaginary.append("Layer{0}.nsld_imaginary".format(i))
        if l.msld.rho.vary and l.msld.rho.expr=='':
            ties_msld_rho.append("Layer{0}.msld_rho".format(i))
        if l.msld.theta.vary and l.msld.theta.expr=='':
            ties_msld_theta.append("Layer{0}.msld_theta".format(i))
        if l.msld.phi.vary and l.msld.phi.expr=='':
            ties_msld_phi.append("Layer{0}.msld_phi".format(i))
        if l.roughness.vary and l.roughness.expr=='':
            ties_roughness.append("Layer{0}.roughness".format(i))
        if l.thickness.vary and l.thickness.expr=='':
            ties_thickness.append("Layer{0}.thickness".format(i))
    if incoming_media.nsld_real.vary and incoming_media.nsld_real.expr=='':
        ties_nsld_real.append("Incoming_Media.nsld_real")
    if incoming_media.nsld_imaginary.vary and incoming_media.nsld_imaginary.expr=='':
        ties_nsld_imaginary.append("Incoming_Media.nsld_imaginary")
    if incoming_media.msld.rho.vary and incoming_media.msld.rho.expr=='':
        ties_msld_rho.append("Incoming_Media.msld_rho")
    if incoming_media.msld.theta.vary and incoming_media.msld.theta.expr=='':
        ties_msld_theta.append("Incoming_Media.msld_theta")
    if incoming_media.msld.phi.vary and incoming_media.msld.phi.expr=='':
        ties_msld_phi.append("Incoming_Media.msld_phi")
    if incoming_media.roughness.vary and incoming_media.roughness.expr=='':
        ties_roughness.append("Incoming_Media.roughness")
    if incoming_media.thickness.vary and incoming_media.thickness.expr=='':
        ties_thickness.append("Incoming_Media.thickness")
    if substrate.nsld_real.vary and substrate.nsld_real.expr=='':
        ties_nsld_real.append("Substrate.nsld_real")
    if substrate.nsld_imaginary.vary and substrate.nsld_imaginary.expr=='':
        ties_nsld_imaginary.append("Substrate.nsld_imaginary")
    if substrate.msld.rho.vary and substrate.msld.rho.expr=='':
        ties_msld_rho.append("Substrate.msld_rho")
    if substrate.msld.theta.vary and substrate.msld.theta.expr=='':
        ties_msld_theta.append("Substrate.msld_theta")
    if substrate.msld.phi.vary and substrate.msld.phi.expr=='':
        ties_msld_phi.append("Substrate.msld_phi")
    if substrate.roughness.vary and substrate.roughness.expr=='':
        ties_roughness.append("Substrate.roughness")
    if substrate.thickness.vary and substrate.thickness.expr=='':
        ties_thickness.append("Substrate.thickness")
    return (ties_nsld_real, ties_nsld_imaginary, ties_msld_rho, \
            ties_msld_theta, ties_msld_phi, ties_roughness,ties_thickness)


def generate_parameter_lists(layer_list,incoming_media, substrate):
    layer_indexes=[]
    layer_names=[]
    layer_parameters=[]
    layer_ties=[]
    attribute_list=['thickness','nsld_real','nsld_imaginary','msld','roughness']
    msld_attribute_list=['rho','theta','phi']
    for i,current_layer in enumerate([incoming_media]+layer_list+[substrate]):
        for attribute in attribute_list:
            num_par=current_layer.__getattribute__(attribute)
            if attribute=='msld':
                for msld_attribute in msld_attribute_list:
                    msld_par=num_par.__getattribute__(msld_attribute)
                    if msld_par.vary:
                        layer_indexes.append(i)
                        layer_names.append(current_layer.name)
                        layer_parameters.append('msld.'+msld_par.name)
                        layer_ties.append(msld_par.expr)
            else:
                if num_par.vary:
                    layer_indexes.append(i)
                    layer_names.append(current_layer.name)
                    layer_parameters.append(num_par.name)
                    layer_ties.append(num_par.expr)
    return(layer_indexes,layer_names,layer_parameters,layer_ties)
                    
