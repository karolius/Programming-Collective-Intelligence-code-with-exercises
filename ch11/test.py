import random
import time
from itertools import combinations


def ipgenerator(i):
    for _ in xrange(i):
        yield '.'.join(map(str, (random.randint(0, 255) for _ in xrange(4))))


if __name__ == '__main__':
    '''
    l = [i for i in xrange(10000000)]
    k = []

    start = time.time()
    for e in l:
        k.append(e+1)
    print "Generator time: ", time.time()-start

    k = []
    start = time.time()
    for i in range(len(l)):
        k.append(l[i] + 1)
    print "Iterator pre len time: ", time.time() - start

    k = []

    start = time.time()
    for i in xrange(len(l)):
        k.append(l[i] + 1)
    print "Iterator time: ", time.time() - start

    start = time.time()
    prev = 1.0
    while True:
        r = random.random()
        if r < prev:
            print r
            prev = r
            if r == 0:
                print "Znaleziono 0 po: ", time.time()-start
                break
    '''

    start = time.time()
    listn = [random.randit(0, 15) for _ in xrange(25)]
    print "samo tworzenie: ", time.time() - start
    for comb in combinations()


    setn = (random.randit(0, 15) for _ in xrange(25))