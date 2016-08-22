"""
 Try this version of NMF that is about 15/20 times faster and in my opinion
 more accurate in the results it gives - lolamontes69
 # NMF by alternative non-negative least squares using projected gradients
 # Author: Chih-Jen Lin, National Taiwan University
 # Python/numpy translation: Anthony Di Franco
 # Adapted for the Chapter 10 Programming Collective Intelligence by lolamontes69
"""
import random
from numpy import *
from numpy.linalg import norm
from time import time
from sys import stdout


def factorize(v1, pc=20, maxiter=10):
    ic, fc = shape(v1)
    temp1 = v1.tolist()
    v = array(temp1)

    w = array([[random.random() for j in range(pc)] for i in range(ic)])
    h = array([[random.random() for i in range(fc)] for j in range(pc)])

    wo, ho = nmf(v, w, h, 0.00000001, 900, maxiter)

    temp2 = wo.tolist()
    wo1 = matrix(temp2)
    temp3 = ho.tolist()
    ho1 = matrix(temp3)

    return wo1, ho1


def nmf(V, Winit, Hinit, tol, timelimit, maxiter):
    """
    (W,H) = nmf(V,Winit,Hinit,tol,timelimit,maxiter)
    :param V:
    :param Winit: initial solution
    :param Hinit: initial solution
    :param tol: tolerance for a relative stopping condition
    :param timelimit: limit of time
    :param maxite: limit of iterations
    :return: W,H as output solution
    """
    W = Winit
    H = Hinit
    initt = time()

    gradW = dot(W, dot(H, H.T)) - dot(V, H.T)
    gradH = dot(dot(W.T, W), H) - dot(W.T, V)
    initgrad = norm(r_[gradW, gradH.T])
    print 'Init gradient norm {:f}'.format(initgrad)
    tolW = max(0.001, tol)*initgrad
    tolH = tolW

    for iter in xrange(1, maxiter):
        # stopping condition
        projnorm = norm(r_[gradW[logical_or(gradW < 0, W > 0)],
                           gradH[logical_or(gradH < 0, H > 0)]])
        if projnorm < tol*initgrad or time() - initt > timelimit:
            break

        W, gradW, iterW = nlssubprob(V.T, H.T, W.T, tolW, 1000)
        W = W.T
        gradW = gradW.T
        if iterW == 1:
            tolH *= 0.1

        H, gradH, iterH = nlssubprob(V, W, H, tolH, 1000)
        if iterH == 1:
            tolH *= 0.1

        if iter % 10 == 0:
            stdout.write('.')

    print '\nIter = {:d} Final proj-grad norm {:f}'.format(iter, projnorm)
    return W, H


def nlssubprob(V, W, Hinit, tol, maxiter):
    """
    :param V: constant matrice
    :param W: constant matrice
    :param Hinit: initial solution
    :param tol: stopping tolerance
    :param maxiter: limit of iterations
    :return: H, grad, [output solution and gradient]
             iter [iterations used]
    """
    H = Hinit
    WtV = dot(W.T, V)
    WtW = dot(W.T, W)

    alpha = 1
    beta = 0.1

    for iter in xrange(1, maxiter):
        grad = dot(WtW, H) - WtV
        projgrad = norm(grad[logical_or(grad < 0, H > 0)])
        if projgrad < tol:
            break
        # Search step size
        for inner_iter in xrange(1, 20):
            Hn = H - alpha*grad
            Hn = where(Hn > 0, Hn, 0)
            d = Hn - H
            gradd = sum(grad * d)
            dQd = sum(dot(WtW, d) * d)
            suff_decr = 0.99*gradd + 0.5*dQd < 0

            if inner_iter == 1:
                decr_alpha = not suff_decr
                Hp = H
            if decr_alpha:
                if suff_decr:
                    H = Hn
                    break
                else:
                    alpha *= beta
            else:
                if not suff_decr or (Hp == Hn).all():
                    H = Hp
                    break
                else:
                    alpha /= beta
                    Hp = Hn
        if iter == maxiter:
            print 'Max iter in nlssubprob'
    return H, grad, iter