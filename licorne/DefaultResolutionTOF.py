import numpy as np
def resolution(Q):
    """
    Resolution calculator for TOF
    """
    print('tof')
    Theta=0.01
    DTheta=0.0003
    DLambda=0.01
    Lambda=4*np.pi*np.sin(Theta)/Q
    Sigma=Q*np.sqrt((DTheta/Theta)**2+(DLambda/Lambda)**2)
    return Sigma
