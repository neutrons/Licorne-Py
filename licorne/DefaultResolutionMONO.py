import numpy as np

def resolution(Q):
    """
    Resolution calculator for monochromatic beam
    """
    Q=np.array(Q)
    Lambda=5
    DLambda=0.01
    Theta=np.arcsin(Q*Lambda/(4*np.pi))
    DTheta=Q*0
    DTheta[Q>0]=0.0007
    Sigma=Q*np.sqrt((DTheta/Theta)**2+(DLambda/Lambda)**2)
    return Sigma
