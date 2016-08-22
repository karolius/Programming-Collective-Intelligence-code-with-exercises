from numpy import *
import random


def difcost(a, b):
    dif = 0
    r, c = shape(a)
    # Loop over every row and column in the matrix
    for i in range(r):
        for j in range(c):
            # Add together the difrences
            dif += pow(a[i, j] - b[i, j], 2)
    return dif


def factorize(v, pc=10, iter=50):
    """
    :param v:
    :param pc: specify the number of features you want to find
    :param iter:
    :return:
    """
    ic, fc = shape(v)
    eps = 0.00000000000000000000000001

    # Initialize the weight and features matrices with random values
    w = matrix([[random.random() for j in range(pc)] for i in range(ic)])
    h = matrix([[random.random() for i in range(fc)] for i in range(pc)])

    # Perform operation a maximum of iter times
    pcost = 99999999999999999999999
    for i in range(iter):
        wh = w*h

        # Calculate the current diffrence
        cost = difcost(v, wh)
        if i % 10 == 0:
            print cost
        # Terminate if the matrix has been fully factorized
        if cost == 0:
            break
        if 99*pcost < 100*cost:  # ex 4
            break
        pcost = cost

        # Update feature matrix
        hn = (transpose(w)*v)
        hd = (transpose(w)*w*h) + eps
        h = matrix(array(h)*array(hn) / array(hd))

        # Update weights matrix
        wn = (v*transpose(h))
        wd = (w*h*transpose(h)) + eps
        w = matrix(array(w)*array(wn) / array(wd))
    return w, h


if __name__ == '__main__':
    l1 = [[1,2,3], [4,5,6]]
    m1 = matrix(l1)
    m2 = matrix([[1,2], [3,4], [5,6]])

    # Factorization
    w, h = factorize(m1*m2, pc=3, iter=100)

    print 'w*h=', w*h
    print 'm1*m2=', m1*m2