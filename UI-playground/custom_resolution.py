import numpy as np

def resolution(Q):
    """
    Resolution calculator for TOF
    """
    Q=np.array(Q)
    Theta1=0.0068
    Theta2=0.01
    Theta3=0.017
    DTheta1=0.00032
    DTheta2=0.00045
    DTheta3=0.00075
    Q1=0.03
    Q2=0.045
    QP1=Q<Q1
    QP2=(Q>=Q1)&(Q<=Q2)
    QP3=Q>Q2
    DLambda=0.005
    Lambda=Q*0
    Sigma=Q*0
    Lambda[QP1]=4*np.pi*np.sin(Theta1)/Q[QP1] 
    Lambda[QP2]=4*np.pi*np.sin(Theta2)/Q[QP2]
    Lambda[QP3]=4*np.pi*np.sin(Theta3)/Q[QP3]  
    Sigma[QP1]=Q[QP1]*np.sqrt((DTheta1/Theta1)**2+(DLambda/Lambda[QP1])**2)
    Sigma[QP2]=Q[QP2]*np.sqrt((DTheta2/Theta2)**2+(DLambda/Lambda[QP2])**2) 
    Sigma[QP3]=Q[QP3]*np.sqrt((DTheta3/Theta3)**2+(DLambda/Lambda[QP3])**2)
    return Sigma

