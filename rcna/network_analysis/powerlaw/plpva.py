from math import *
from random import *

# function [alpha, xmin, n]=plpva(x, xmin, varargin)
# PLPVA calculates the p-value for the given power-law fit to some data.
#    Source: http://www.santafe.edu/~aaronc/powerlaws/
# 
#    PLPVA(x, xmin) takes data x and given lower cutoff for the power-law
#    behavior xmin and computes the corresponding p-value for the
#    Kolmogorov-Smirnov test, according to the method described in 
#    Clauset, Shalizi, Newman (2007).
#    PLPVA automatically detects whether x is composed of real or integer
#    values, and applies the appropriate method. For discrete data, if
#    min(x) > 1000, PLPVA uses the continuous approximation, which is 
#    a reliable in this regime.
#   
#    The fitting procedure works as follows:
#    1) For each possible choice of x_min, we estimate alpha via the 
#       method of maximum likelihood, and calculate the Kolmogorov-Smirnov
#       goodness-of-fit statistic D.
#    2) We then select as our estimate of x_min, the value that gives the
#       minimum value D over all values of x_min.
#
#    Note that this procedure gives no estimate of the uncertainty of the 
#    fitted parameters, nor of the validity of the fit.
#
#    Example:
#       x = [500,150,90,81,75,75,70,65,60,58,49,47,40]
#       [p, gof] = plpva(x, 1);
#
#    For more information, try 'type plpva'
#
#    See also PLFIT, PLVAR

# Version 1.0.7 (2009 October)
# Copyright (C) 2008-2011 Aaron Clauset (Santa Fe Institute)

# Ported to Python by Joel Ornstein (2011 July)
#(joel_ornstein@hmc.edu)

# Distributed under GPL 2.0
# http://www.gnu.org/copyleft/gpl.html
# PLPVA comes with ABSOLUTELY NO WARRANTY
#
# 
# The 'zeta' helper function is modified from the open-source library 'mpmath'
#   mpmath: a Python library for arbitrary-precision floating-point arithmetic
#   http://code.google.com/p/mpmath/
#   version 0.17 (February 2011) by Fredrik Johansson and others
# 

# Notes:
# 
# 1. In order to implement the integer-based methods in Matlab, the numeric
#    maximization of the log-likelihood function was used. This requires
#    that we specify the range of scaling parameters considered. We set
#    this range to be 1.50 to 3.50 at 0.01 intervals by default. 
#    This range can be set by the user like so,
#
#       x = [500,150,90,81,75,75,70,65,60,58,49,47,40]
#       a = plpva(x,1,'range',[1.50,3.50,0.01])
#    
# 2. PLPVA can be told to limit the range of values considered as estimates
#    for xmin in two ways. First, it can be instructed to sample these
#    possible values like so,
#    
#       a = plpva(x,1,'sample',100);
#    
#    which uses 100 uniformly distributed values on the sorted list of
#    unique values in the data set. Second, it can simply omit all
#    candidates above a hard limit, like so
#    
#       a = plpva(x,1,'limit',3.4);
#    
#    Finally, it can be forced to use a fixed value, like so
#    
#       a = plpva(x,1,'xmin',1);
#    
#    In the case of discrete data, it rounds the limit to the nearest
#    integer.
# 
# 3. The default number of semiparametric repetitions of the fitting
# procedure is 1000. This number can be changed like so
#    
#       p = plpva(x, 1,'reps',10000);
# 
# 4. To silence the textual output to the screen, do this
#    
#       p = plpva(x, 1,'reps',10000,'silent');
# 

def plpva(x,xmin, *varargin):
    vec     = []
    sample  = []
    xminx   = []
    limit   = []
    Bt      = []
    quiet   = False
    

    # parse command-line parameters trap for bad input
    i=0 
    while i<len(varargin): 
        argok = 1 
        if type(varargin[i])==str: 
            if varargin[i]=='range':
                Range = varargin[i+1]
                if Range[1]>Range[0]:
                    argok=0
                    vec=[]
                try:
                    vec=map(lambda X:X*float(Range[2])+Range[0],\
                            range(int((Range[1]-Range[0])/Range[2])))
                    
                    
                except:
                    argok=0
                    vec=[]
                    

                if Range[0]>=Range[1]:
                    argok=0
                    vec=[]
                    i-=1

                i+=1
                    
                            
            elif varargin[i]== 'sample':
                sample  = varargin[i+1]
                i = i + 1
            elif varargin[i]==  'limit':
                limit   = varargin[i+1]
                i = i + 1
            elif varargin[i]==  'xmin':
                xminx   = varargin[i+1]
                i = i + 1
            elif varargin[i]==  'reps':
                Bt   = varargin[i+1]
                i = i + 1
            elif varargin[i]==  'silent':       quiet  = True    
 
            else: argok=0 
        
      
        if not argok:
            print '(PLPVA) Ignoring invalid argument #',i+1 
      
        i = i+1 

    if vec!=[] and (type(vec)!=list or min(vec)<=1):
        print '(PLPVA) Error: ''range'' argument must contain a vector or minimum <= 1. using default.\n'                        
              
        vec = []
    
    if sample!=[] and sample<2:
        print'(PLPVA) Error: ''sample'' argument must be a positive integer > 1. using default.\n'
        sample = []
    
    if limit!=[] and limit<min(x):
        print'(PLPVA) Error: ''limit'' argument must be a positive value >= 1. using default.\n'
        limit = []
    
    if xminx!=[] and xminx>=max(x):
        print'(PLPVA) Error: ''xmin'' argument must be a positive value < max(x). using default behavior.\n'
        xminx = []
    if Bt!=[] and Bt<2:
        print '(PLPVA) Error: ''reps'' argument must be a positive value > 1; using default.\n'
        Bt = [];


    # select method (discrete or continuous) for fitting
    if     reduce(lambda X,Y:X==True and floor(Y)==float(Y),x,True): f_dattype = 'INTS'
    elif reduce(lambda X,Y:X==True and (type(Y)==int or type(Y)==float or type(Y)==long),x,True):    f_dattype = 'REAL'
    else:                 f_dattype = 'UNKN'
    
    if f_dattype=='INTS' and min(x) > 1000 and len(x)>100:
        f_dattype = 'REAL'
    
    N=len(x)
    
    if Bt==[]: Bt=1000
    nof = []
    if not quiet:
        print 'Power-law Distribution, p-value calculation\n'
        print '   Copyright 2007-2010 Aaron Clauset\n'
        print '   Warning: This can be a slow calculation; please be patient.\n'
        print '   n    = ',len(x),'\n   xmin = ',xmin,'\n   reps = ',Bt
    # estimate xmin and alpha, accordingly
    if f_dattype== 'REAL':
        # compute D for the empirical distribution
        z = filter(lambda X:X>=xmin,x)
        z.sort()
        nz = len(z)
        y = filter(lambda X:X<xmin,x)
        ny = len(y)
        alpha = 1 + float(nz) / sum(map(lambda X: log(float(X)/xmin),z))
        cz    = map(lambda X:X/float(nz),range(0,nz))
        cf    = map(lambda X:1-pow((xmin/float(X)),(alpha-1)),z)
        gof   = max( map(lambda X:abs(cz[X] - cf[X]),range(0,nz)))
        pz    = nz/float(N)
        
        # compute distribution of gofs from semi-parametric bootstrap
        # of entire data set with fit
        for B in range(0,Bt):
            # semi-parametric bootstrap of data
            n1=0
            for i in range(0,N):
                if random()>pz: n1+=1

            q1=[]
            for i in range(0,n1):
                q1.append(y[int(floor(ny*random()))])
            n2 = N-n1;
            q2=[]
            for i in range (0,n2):
                q2.append(random())
            q2 = map(lambda X:xmin*pow(1.-X,(-1./(alpha-1.))),q2)

            q  = q1+q2
            q.sort()

            

            # estimate xmin and alpha via GoF-method
            qmins = unique(q);
            qmins.sort()
            qmins = qmins[0:-1];
            
            if xminx!=[]:
                
                qmins = [min(filter(lambda X: X>=xminx,qmins))]
                
            
            if limit!=[]:
                qmins=filter(lambda X: X<=limit,qmins)
                if qmins==[]: qmins=[min(q)]
                
            if sample!=[]:
                step = float(len(qmins))/(sample-1)
                index_curr=0
                new_qmins=[]
                for i in range (0,sample):
                    if round(index_curr)==len(qmins): index_curr-=1
                    new_qmins.append(qmins[int(round(index_curr))])
                    index_curr+=step
                qmins = unique(new_qmins)
                qmins.sort()
            
            
        
            dat   = []
            
            for qm in range(0,len(qmins)):
                qmin = qmins[qm]
                zq   = filter(lambda X:X>=qmin,q)
                nq   = len(zq)
               
                a    = float(nq)/sum(map(lambda X: log(float(X)/qmin),zq))
                cf   = map(lambda X:1-pow((float(qmin)/X),a),zq)
                
                dat.append( max( map(lambda X: abs(cf[X]-float(X)/nq),range(0,nq))))
            if not quiet:
                print '['+str(B+1)+']\tp = ',round(len(filter(lambda X:X>=gof,nof))/float(B+1),3)
            nof.append(min(dat))
        p=len(filter(lambda X:X>=gof,nof))/float(Bt+1) 

    elif f_dattype== 'INTS':
        x=map(int,x)
        if vec==[]:
            for X in range(150,351):
                vec.append(X/100.)    # covers range of most practical 
                                    # scaling parameters
        zvec = map(zeta, vec)
        z = filter (lambda X:X>=xmin,x)
        nz = len(z)
        y = filter (lambda X:X<xmin,x)
        ny = len(y)
        xmax=max(z)
        L       = []
        for k in range(0,len(vec)):
            L.append(-vec[k]*float(sum(map(log,z))) - float(nz)*log(float(zvec[k]) - sum(map(lambda X:pow(float(X),-vec[k]),range(1,xmin)))))
        I = L.index(max(L))
        alpha=vec[I]
        print("alpha: %f"%alpha)
        fit = reduce(lambda X,Y: X+[Y+X[-1]],\
                     (map(lambda X: pow(X,-alpha)/(float(zvec[I])-sum(map(lambda X: pow(X,-alpha),map(float,range(1,xmin))))),range(xmin,xmax+1))),[0])[1:]
        cdi=[]
        for XM in range(xmin,xmax+1):
            cdi.append(len(filter(lambda X: floor(X)<=XM,z))/float(nz))
        
        gof= max( map(lambda X: abs(fit[X] - cdi[X]),range(0,xmax-xmin+1)))
        pz=nz/float(N)
        mmax = 20*xmax
        pdf=[]
        for i in range(0,xmin):
            pdf.append(0)
        pdf += map(lambda X: pow(X,-alpha)/(float(zvec[I])-sum(map(lambda X: pow(X,-alpha),map(float,range(1,xmin))))),range(xmin,mmax+1))
        cdf = reduce(lambda X,Y: X+[Y+X[-1]],pdf,[0])[1:]+[1]

        # compute distribution of gofs from semi-parametric bootstrap
        # of entire data set with fit
        for B in range(0,Bt):
            # semi-parametric bootstrap of data
            n1=0
            for i in range(0,N):
                if random()>pz: n1+=1

            q1=[]
            for i in range(0,n1):
                q1.append( y[int(floor(ny*random()))])
            n2 = N-n1;
            r2=[]
            for i in range (0,n2):
                r2.append(random())
            r2.sort()
            c=0
            k=0
            q2=[]
            for i in range(xmin,mmax+2):
                while c<n2 and r2[c]<=cdf[i]:c+=1
                for k in range(k,c):q2.append(i)
                k=c
                if k>=n2: break

            q  = q1+q2
            qmins = unique(q)
            qmins.sort()
            qmins = qmins[0:-1]

            if xminx!=[]:
                
                qmins = [min(filter(lambda X: X>=xminx,qmins))]
                
            
            if limit!=[]:
                qmins=filter(lambda X: X<=limit,qmins)
                if qmins==[]: qmins=[min(q)]
                
            if sample!=[]:
                step = float(len(qmins))/(sample-1)
                index_curr=0
                new_qmins=[]
                for i in range (0,sample):
                    if round(index_curr)==len(qmins): index_curr-=1
                    new_qmins.append(qmins[int(round(index_curr))])
                    index_curr+=step
                qmins = unique(new_qmins)
                qmins.sort()
        
            qmax   = max(q)
            dat=[]
            zq=q


            for qm in range(0,len(qmins)):
                qmin = qmins[qm]
                zq    = filter(lambda X:X>=qmin,zq)
                nq    = len(zq)
                if nq>1:
                    L=[]
                    slogzq = sum(map(log,zq))
                    qminvec = range (1,qmin)
                    for k in range (1,len(vec)):
                        L.append(-vec[k]*float(slogzq) - float(nq)*log(float(zvec[k]) - sum(map(lambda X:pow(float(X),-vec[k]),qminvec))))
            
                    I = L.index(max(L))
                    fit = reduce(lambda X,Y: X+[Y+X[-1]],\
                                 (map(lambda X: pow(X,-vec[I])/(float(zvec[I])-sum(map(lambda X: pow(X,-vec[I]),map(float,range(1,qmin))))),range(qmin,qmax+1))),[0])[1:]
                    cdi=[]
                    for QM in range(qmin,qmax+1):
                        cdi.append(len(filter(lambda X: floor(X)<=QM,zq))/float(nq))
                    
                    dat.append(max( map(lambda X: abs(fit[X] - cdi[X]),range(0,qmax-qmin+1))))
                else: dat[qm]=float('-inf')
            if not quiet:
                print '['+str(B+1)+']\tp = ',round(len(filter(lambda X:X>=gof,nof))/float(B+1),3)
            nof.append(min(dat))
        
        p=len(filter(lambda X:X>=gof,nof))/float(Bt)
    else:
        print '(PLPVA) Error: x must contain only reals or only integers.\n'
        p = []
        gof  = []
        

    return [p,gof]


# helper functions (unique and zeta)


def unique(seq): 
    # not order preserving 
    set = {} 
    map(set.__setitem__, seq, []) 
    return set.keys()

def _polyval(coeffs, x):
    p = coeffs[0]
    for c in coeffs[1:]:
        p = c + x*p
    return p

_zeta_int = [\
-0.5,
0.0,
1.6449340668482264365,1.2020569031595942854,1.0823232337111381915,
1.0369277551433699263,1.0173430619844491397,1.0083492773819228268,
1.0040773561979443394,1.0020083928260822144,1.0009945751278180853,
1.0004941886041194646,1.0002460865533080483,1.0001227133475784891,
1.0000612481350587048,1.0000305882363070205,1.0000152822594086519,
1.0000076371976378998,1.0000038172932649998,1.0000019082127165539,
1.0000009539620338728,1.0000004769329867878,1.0000002384505027277,
1.0000001192199259653,1.0000000596081890513,1.0000000298035035147,
1.0000000149015548284]

_zeta_P = [-3.50000000087575873, -0.701274355654678147,
-0.0672313458590012612, -0.00398731457954257841,
-0.000160948723019303141, -4.67633010038383371e-6,
-1.02078104417700585e-7, -1.68030037095896287e-9,
-1.85231868742346722e-11][::-1]

_zeta_Q = [1.00000000000000000, -0.936552848762465319,
-0.0588835413263763741, -0.00441498861482948666,
-0.000143416758067432622, -5.10691659585090782e-6,
-9.58813053268913799e-8, -1.72963791443181972e-9,
-1.83527919681474132e-11][::-1]

_zeta_1 = [3.03768838606128127e-10, -1.21924525236601262e-8,
2.01201845887608893e-7, -1.53917240683468381e-6,
-5.09890411005967954e-7, 0.000122464707271619326,
-0.000905721539353130232, -0.00239315326074843037,
0.084239750013159168, 0.418938517907442414, 0.500000001921884009]

_zeta_0 = [-3.46092485016748794e-10, -6.42610089468292485e-9,
1.76409071536679773e-7, -1.47141263991560698e-6, -6.38880222546167613e-7,
0.000122641099800668209, -0.000905894913516772796, -0.00239303348507992713,
0.0842396947501199816, 0.418938533204660256, 0.500000000000000052]

def zeta(s):
    """
    Riemann zeta function, real argument
    """
    if not isinstance(s, (float, int)):
        try:
            s = float(s)
        except (ValueError, TypeError):
            try:
                s = complex(s)
                if not s.imag:
                    return complex(zeta(s.real))
            except (ValueError, TypeError):
                pass
            raise NotImplementedError
    if s == 1:
        raise ValueError("zeta(1) pole")
    if s >= 27:
        return 1.0 + 2.0**(-s) + 3.0**(-s)
    n = int(s)
    if n == s:
        if n >= 0:
            return _zeta_int[n]
        if not (n % 2):
            return 0.0
    if s <= 0.0:
        return 0
    if s <= 2.0:
        if s <= 1.0:
            return _polyval(_zeta_0,s)/(s-1)
        return _polyval(_zeta_1,s)/(s-1)
    z = _polyval(_zeta_P,s) / _polyval(_zeta_Q,s)
    return 1.0 + 2.0**(-s) + 3.0**(-s) + 4.0**(-s)*z



    