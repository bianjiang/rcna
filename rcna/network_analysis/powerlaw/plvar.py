from math import *
from random import *

# function [alpha, xmin, n]=plvar(x, varargin)
# PLVAR estimates the uncertainty in the estimated power-law parameters.
#    Source: http://www.santafe.edu/~aaronc/powerlaws/
# 
#    PLVAR(x) takes a vector of observations x and returns estimated
#    uncertainties in the estimated power-law parameters, based on the
#    nonparametric approach described in Clauset, Shalizi, Newman (2007). 
#    PLVAR automatically detects whether x is composed of real or integer
#    values, and applies the appropriate method. For discrete data, if
#    min(x) > 1000, PLVAR uses the continuous approximation, which is 
#    a reliable in this regime.
#   
#    The fitting procedure works as follows:
#    1) For each possible choice of x_min, we estimate alpha via the 
#       method of maximum likelihood, and calculate the Kolmogorov-Smirnov
#       goodness-of-fit statistic D.
#    2) We then select as our estimate of x_min, the value that gives the
#       minimum value D over all values of x_min.
#
#    Note that this procedure gives no estimate of the validity of the fit.
#
#    Example:
#
#       x = [500,150,90,81,75,75,70,65,60,58,49,47,40]
#       [alpha, xmin, ntail] = plvar(x);
#
#    For more information, try 'type plvar'
#
#    See also PLFIT, PLPVA


# Version 1.0.8 (2010 April)
# Copyright (C) 2008-2011 Aaron Clauset (Santa Fe Institute)

# Ported to Python by Joel Ornstein (2011 July)
#(joel_ornstein@hmc.edu)

# Distributed under GPL 2.0
# http://www.gnu.org/copyleft/gpl.html
# PLVAR comes with ABSOLUTELY NO WARRANTY
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
#       a = plvar(x,'range',[1.50,3.50,0.01])
#    
#    
# 2. PLVAR can be told to limit the range of values considered as estimates
#    for xmin in three ways. First, it can be instructed to sample these
#    possible values like so,
#    
#       a = plvar(x,'sample',100);
#    
#    which uses 100 uniformly distributed values on the sorted list of
#    unique values in the data set. Second, it can simply omit all
#    candidates above a hard limit, like so
#    
#       a = plvar(x,'limit',3.4);
#    
#    Finally, it can be forced to use a fixed value, like so
#    
#       a = plvar(x,'xmin',3.4);
#    
#    In the case of discrete data, it rounds the limit to the nearest
#    integer.
# 
# 3. The default number of nonparametric repetitions of the fitting
# procedure is 1000. This number can be changed like so
#    
#       a = plvar(x,'reps',10000);
#    
# 4. To silence the textual output to the screen, do this
#    
#       p = plvar(x,'silent');
# 
#

def plvar(x,*varargin):
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
            print '(PLVAR) Ignoring invalid argument #',i+1 
      
        i = i+1 

    if vec!=[] and (type(vec)!=list or min(vec)<=1):
        print '(PLVAR) Error: ''range'' argument must contain a vector or minimum <= 1. using default.\n'                        
              
        vec = []
    
    if sample!=[] and sample<2:
        print'(PLVAR) Error: ''sample'' argument must be a positive integer > 1. using default.\n'
        sample = []
    
    if limit!=[] and limit<min(x):
        print'(PLVAR) Error: ''limit'' argument must be a positive value >= 1. using default.\n'
        limit = []
    
    if xminx!=[] and xminx>=max(x):
        print'(PLVAR) Error: ''xmin'' argument must be a positive value < max(x). using default behavior.\n'
        xminx = []
    if Bt!=[] and Bt<2:
        print '(PLVAR) Error: ''reps'' argument must be a positive value > 1; using default.\n'
        Bt = [];


    # select method (discrete or continuous) for fitting
    if     reduce(lambda X,Y:X==True and floor(Y)==float(Y),x,True): f_dattype = 'INTS'
    elif reduce(lambda X,Y:X==True and (type(Y)==int or type(Y)==float or type(Y)==long),x,True):    f_dattype = 'REAL'
    else:                 f_dattype = 'UNKN'
    
    if f_dattype=='INTS' and min(x) > 1000 and len(x)>100:
        f_dattype = 'REAL'
    
    N=len(x)
    
    if Bt==[]: Bt=1000
    bofA = []
    bofB = []
    bofC = []
    if not quiet:
        print 'Power-law Distribution, parameter error calculation\n'
        print '   Copyright 2007-2009 Aaron Clauset\n'
        print '   Warning: This can be a slow calculation; please be patient.\n'
        print '   n    = ',len(x),'\n   reps = ',Bt
    # estimate xmin and alpha, accordingly
    if f_dattype== 'REAL':

        for B in range(0,Bt):
            #  bootstrap resample
            y = []
            for i in range(0,N):
                y.append(x[int(floor(N*random()))])
            ymins = unique(y)
            ymins.sort()
            ymins=ymins[0:-1]
            
            if xminx!=[]:
                
                ymins = [min(filter(lambda X: X>=xminx,ymins))]
                
            
            if limit!=[]:
                qmins=filter(lambda X: X<=limit,qmins)
                if qmins==[]: qmins=[min(y)]
                
            if sample!=[]:
                step = float(len(ymins))/(sample-1)
                index_curr=0
                new_ymins=[]
                for i in range (0,sample):
                    if round(index_curr)==len(ymins): index_curr-=1
                    new_ymins.append(ymins[int(round(index_curr))])
                    index_curr+=step
                ymins = unique(new_ymins)
                ymins.sort()

            z = sorted(y)

            dat   = []
            
            for xm in range(0,len(ymins)):
                xmin = ymins[xm]
                z   = filter(lambda X:X>=xmin,z)
                n   = len(z)
                # estimate alpha using direct MLE
                a    = float(n)/sum(map(lambda X: log(float(X)/xmin),z))
                # compute KS statistic
                cf   = map(lambda X:1-pow((float(xmin)/X),a),z)
                
                dat.append( max( map(lambda X: abs(cf[X]-float(X)/n),range(0,n))))
            ymin = ymins[dat.index(min(dat))]
            z = filter(lambda X: X>=ymin,y)
            n = len(z)
            alpha    = 1+float(n)/sum(map(lambda X: log(float(X)/ymin),z))
            bofA.append(n)
            bofB.append(ymin)
            bofC.append(alpha)
            # store distribution of estimated parameter values 
            if not quiet:
                print '['+str(B+1)+']\tntail = ',round(mean(bofA),3),' (',round(std(bofA),3),')','\txmin = ',\
                      round(mean(bofB),3),' (',round(std(bofB),3),')','\talpha = ',round(mean(bofC),3),' (',round(std(bofC),3),')'

        n = std(bofA)
        xmin = std(bofB)
        alpha = std(bofC)

    elif f_dattype== 'INTS':
        x=map(int,x)
        if vec==[]:
            for X in range(150,351):
                vec.append(X/100.)    # covers range of most practical 
                                    # scaling parameters
        zvec = map(zeta, vec)

        for B in range(0,Bt):
            #  bootstrap resample
            y = []
            for i in range(0,N):
                y.append(x[int(floor(N*random()))])
            ymins = unique(y)
            ymins.sort()
            ymins=ymins[0:-1]
            
            if xminx!=[]:
                
                ymins = [min(filter(lambda X: X>=xminx,ymins))]
                
            
            if limit!=[]:
                qmins=filter(lambda X: X<=limit,qmins)
                if qmins==[]: qmins=[min(y)]
                
            if sample!=[]:
                step = float(len(ymins))/(sample-1)
                index_curr=0
                new_ymins=[]
                for i in range (0,sample):
                    if round(index_curr)==len(ymins): index_curr-=1
                    new_ymins.append(ymins[int(round(index_curr))])
                    index_curr+=step
                ymins = unique(new_ymins)
                ymins.sort()
                
            ymax = max(y)
            z = sorted(y)

            datA = []
            datB = []
            for xm in range(0,len(ymins)):
                xmin = ymins[xm]
                z = filter(lambda X:X>=xmin,z)
                n = len(z)
                L = []
                slogz = sum(map(log,z))
                xminvec = range (1,xmin)
                for k in range (1,len(vec)):
                    L.append(-vec[k]*float(slogz) - float(n)*log(float(zvec[k]) - sum(map(lambda X:pow(float(X),-vec[k]),xminvec))))
        
                I = L.index(max(L))

                # compute KS statistic
                fit = reduce(lambda X,Y: X+[Y+X[-1]],\
                             (map(lambda X: pow(X,-vec[I])/(float(zvec[I])-sum(map(lambda X: pow(X,-vec[I]),map(float,range(1,xmin))))),range(xmin,ymax+1))),[0])[1:]
                cdi=[]
                for XM in range(xmin,ymax+1):
                    cdi.append(len(filter(lambda X: floor(X)<=XM,z))/float(n))
                
                datA.append(max( map(lambda X: abs(fit[X] - cdi[X]),range(0,ymax-xmin+1))))
                datB.append(vec[I])
                
            I = datA.index(min(datA))
            ymin = ymins[I]
            n = len(filter(lambda X:X>=ymin,y))
            alpha = datB[I]

            bofA.append(n)
            bofB.append(ymin)
            bofC.append(alpha)
            # store distribution of estimated parameter values 
            if not quiet:
                print '['+str(B+1)+']\tntail = ',round(mean(bofA),3),' (',round(std(bofA),3),')','\txmin = ',\
                      round(mean(bofB),3),' (',round(std(bofB),3),')','\talpha = ',round(mean(bofC),3),' (',round(std(bofC),3),')'
        n = std(bofA)
        xmin = std(bofB)
        alpha = std(bofC)
        
    else:
        print '(PLVAR) Error: x must contain only reals or only integers.\n'
        n = []
        xmin = []
        alpha = []
        

    return [alpha,xmin,n]


# helper functions (unique and zeta)
def mean(L):
    try:
        return float(sum(L))/len(L)
    except:
        
        return 0

def std(L):
    try:
        u = mean(L)
        return sqrt((1./(len(L)-1))*sum(map(lambda X: pow(X-u,2),L)))
    except:
        return 0
        

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



    
