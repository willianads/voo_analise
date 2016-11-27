from __future__ import division #somente para python 2
import time
import math
from PyQt4.QtCore import *

def Ler_Cps(cps_arquivo,delimitador):
    with open(cps_arquivo,'rt') as arquivo:
        linhas = arquivo.readlines()
        numero_cps=len(linhas)
        jj=0 #comeca do 1 se tiver no cabecario
        #cp_id=[]
        cps=[]
        #Yo=[]
        #Zo=[]
        #omega=[]
        #phi=[]
        #kappa=[]
        #est_atu=[]
        #est_ant=[]
        pontos_borda=[]
        
        while jj < numero_cps:
            itens=linhas[jj].split(delimitador)
            cp_id=itens[0]
            Xo=float(itens[1])
            Yo=float(itens[2])
            Zo=float(itens[3])
            omega=float(itens[4])
            phi=float(itens[5])
            kappa=float(itens[6][:-1])
            est_atu = int(0)
            est_ant = int(0)
            
            pontos_borda.append([])
            vet=[cp_id,Xo,Yo,Zo,omega,phi,kappa,est_atu,est_ant]
            cps.append(vet)
            
            jj=jj+1
            
    print('Foram encontrados ' + str(numero_cps) + ' cps no arquivo informado\n')
    return cps,pontos_borda,numero_cps
    

def Ponto_visivel(Xo,Yo,Zo,omega,phi,kappa,X,Y,Z,f,x_min,x_max,y_min,y_max):
    
    c=math.pi/180
    f=float(f)
    
    k=float(kappa)*-c
    o=float(omega)*-c
    p=float(phi)*-c
    
    cosp=math.cos(p)
    cosk=math.cos(k)
    coso=math.cos(o)
    
    senk=math.sin(k)
    senp=math.sin(p)
    seno=math.sin(o)
    
    dX=(float(X)-float(Xo))
    dY=(float(Y)-float(Yo))
    dZ=(float(Z)-float(Zo))
    
    m11=cosp*cosk
    m12=coso*senk+seno*senp*cosk
    m13=seno*senk-coso*senp*cosk
    m21=-cosp*senk
    m22=coso*cosk-seno*senp*senk
    m23=seno*cosk+coso*senp*senk
    m31=senp
    m32=-seno*cosp
    m33=coso*cosp
    
    A= m11*dX + m12*dY + m13*dZ
    B= m21*dX + m22*dY + m23*dZ
    C= m31*dX + m32*dY + m33*dZ
    
    
    x=-f*(A/C)
    y=-f*(B/C)
    
    
    if x>x_min and x<x_max and y>y_min and y<y_max:
        return 1
    else:
        return 0

def GDS_Calc(Xo,Yo,Zo,omega,phi,kappa,X,Y,Z,f,pixel):

        dx2=pow((float(Xo))-(float(X)),2)
        dy2=pow((float(Yo))-(float(Y)),2)
        dz2=pow((float(Zo))-(float(Z)),2)
        Dist=math.sqrt(dx2+dy2+dz2)
        Ratio=Dist/float(f)
        GDS=float(pixel)*Ratio
        return GDS
        

def Ler_Cam(cam_arquivo):
    with open(cam_arquivo,'rt') as arquivo:
        linhas = arquivo.readlines()
        focal=float(linhas[0])/1000
        yframe=float(linhas[1])/1000
        xframe=float(linhas[2])/1000
        pixelsize=float(linhas[3])/1000000
        
        x_min=-xframe/2
        x_max=xframe/2
        y_min=-yframe/2
        y_max=yframe/2
        
        return focal, x_min, x_max, y_min, y_max, pixelsize