from random import random, randint
import math
import optimization
from pylab import *

weightdomain = [(0, 20)] * 4


def wineprice(rating, age):
    peak_age = rating - 50

    # Oblicz cene w oparciu o ocene
    price = rating / 2
    if age > peak_age:
        # Po przjsciu przez wiercholek cena spada w przeciagu 10 lat
        price *= (5 - (age - peak_age) / 2)
    else:
        # Zwieksz do 5x wartosc przy osiaganiu wiercholka
        price *= (5 * (age + 1) / peak_age)
    if price < 0:
        price = 0
    return price


def wineset1():
    rows = []
    for i in range(300):
        # Stworz losowy wiek i ocene
        rating = random() * 50 + 50
        age = random() * 50

        # Uzyskaj cene referowana
        price = wineprice(rating, age)
        price *= (random() * 0.4 + 0.8)  # szum

        # Dodaj do zestawu danych
        rows.append({'input': (rating, age),
                     'result': price})
    return rows


def euclidean(v1, v2):
    d = 0.0
    for i in range(len(v1)):
        d += (v1[i] - v2[i]) ** 2
    return math.sqrt(d)


def getdistances(data, vec1):
    distancelist = []
    for i in range(len(data)):
        vec2 = data[i]['input']
        distancelist.append((euclidean(vec1, vec2), i))
    distancelist.sort()
    return distancelist


def knnestimate(data, vec1, k=3):
    # Uzyskaj posortowane odleglosci
    dlist = getdistances(data, vec1)
    avg = 0.0

    # Wez srednia z k wynikow
    for i in range(k):
        idx = dlist[i][1]
        avg += data[idx]['result']
    return avg / k


def inverseweight(dist, num=1.0, const=0.1):
    return num / (dist + const)


def subtractweight(dist, const=1.0):
    if dist > const:
        return 0
    else:
        return const - dist


def gaussian(dist, sigma=5.0):
    return math.e ** (-dist ** 2 / (2 * sigma ** 2))


def weightedknn(data, vec1, k=5, weightf=inverseweight):
    dlist = getdistances(data, vec1)
    avg = 0.0
    totalweight = 0.0

    # Uzyskaj wazona srednia
    for i in range(k):
        weight = weightf(dlist[i][0])
        avg += weight * data[dlist[i][1]]['result']  # idx jako dlist[i][1]
        totalweight += weight
    if avg == 0:
        return 0
    return avg / totalweight


def dividedata(data, test=0.05):
    trainset = []
    testset = []
    for row in data:
        if random() < test:
            testset.append(row)
        else:
            trainset.append(row)
    return trainset, testset


def testalgorithm(algf, trainset, testset, neighnumb):
    error = 0.0
    for row in testset:
        guess = algf(trainset, row['input'], k=neighnumb)
        error += (row['result'] - guess) ** 2
    return error / len(testset)


def crossvalidate(algf, data, trials=100, test=0.05, neighnumb=3, divfun=dividedata):
    error = 0.0
    for i in range(trials):
        trainset, testset = divfun(data, test)
        error += testalgorithm(algf, trainset, testset, neighnumb)
    return error / trials


def wineset2():
    rows = []
    for i in range(300):
        rating = random() * 50 + 50
        age = random() * 50
        aisle = float(randint(1, 20))
        bottlesize = [375.0, 750.0, 1500.0][randint(0, 2)]
        price = wineprice(rating, age) * (bottlesize / 750) * (random() * 0.2 + 0.9)
        rows.append({'input': (rating, age, aisle, bottlesize),
                     'result': price})
    return rows


def rescale(data, scale):
    scaleddata = []
    for row in data:
        scaled = [scale[i] * row['input'][i] for i in range(len(scale))]
        scaleddata.append({'input': scaled, 'result': row['result']})
    return scaleddata


def createcostfunction(algf, data):
    def costf(scale):
        sdata = rescale(data, scale)
        return crossvalidate(algf, sdata, trials=10)
    return costf


def wineset3():
    rows = wineset1()
    for row in rows:
        if random() < 0.5:
            # Wino zostalo kupione w sklepowej przecenie
            row['result'] *= 0.6
    return rows


def probguess(data, vec1, low, high, k=5, weightf=gaussian):
    dlist = getdistances(data, vec1)
    nweight = 0.0
    tweight = 0.0

    for i in range(k):
        dist = dlist[i][0]
        idx = dlist[i][1]
        weight = weightf(dist)
        v = data[idx]['result']

        # Czy ten pkt jest w zakresie?
        if low <= v <= high:
            nweight += weight
        tweight += weight
    if tweight == 0:
        return 0

    # Pr. to wagi w zakresie / wszystkie wagi
    return nweight / tweight


def cumulativegraph(data, vec1, high, k=5, weightf=gaussian):
    t1 = arange(0.0, high, 0.1)
    cprob = array([probguess(data, vec1, 0, v, k, weightf) for v in t1])
    plot(t1, cprob)
    show()


def probabilitygraph(data, vec1, high, k=5, weightf=gaussian, ss=5.0):
    # Stworz zakres cen
    t1 = arange(0.0, high, 0.1)

    # Uzyskaj Pr'dobienstwa dla calego zakresu
    probs = [probguess(data, vec1, v, v + 0.1, k, weightf) for v in t1]

    # Wygladz je przez dodanie gaussa sasiednich prawdopodobienstw
    smoothed = []
    for i in range(len(probs)):
        sv = 0.0
        for j in range(len(probs)):
            dist = abs(i - j) * 0.1
            weight = gaussian(dist, sigma=ss)
            sv += weight * probs[j]
        smoothed.append(sv)
    smoothed = array(smoothed)

    plot(t1, smoothed)
    show()


# -------------------------------------------------------
def neighborscostfunction(algf, sdata, testingels, df):
    def costf(k):
        return crossvalidate(algf, sdata, trials=10, neighnumb=k[0], test=testingels, divfun=df)
    return costf


def pickrandom(data, amout=1):
    if amout >= len(data):
        amout = len(data)//2
    trainset = [] + data
    testset = []
    for i in range(amout):
        idx = randint(0, len(trainset)-1)
        testset.append(trainset[idx])
        del trainset[idx]
    return trainset, testset


if __name__ == '__main__':
    data = wineset1()
    # data = wineset2()
    # data = wineset3()
    # sdata = rescale(data, [15, 13, 1, 8])

    '''
    # Test wineprice
    print wineprice(95.0, 3.0)
    print wineprice(95.0, 8.0)
    print wineprice(99.0, 1.0)

    print data[0]
    print data[1]

    # Similarity
    print euclidean(data[0]['input'], data[1]['input'])

    # Price estimate for new item
    print knnestimate(data, (95.0, 3.0))
    print knnestimate(data, (99.0, 3.0))
    print knnestimate(data, (99.0, 5.0))

    print wineprice(99.0, 5.0)  # Cena aktualna
    print knnestimate(data, (99.0, 5.0), k=1)
    print knnestimate(data, (99.0, 5.0), k=5)

    # Weighting functions
    print subtractweight(0.0)
    print inverseweight(0.0)
    print gaussian(0.0)
    print "----------------------"
    print subtractweight(0.1)
    print inverseweight(0.1)
    print gaussian(0.1)
    print "----------------------"
    print subtractweight(1)
    print inverseweight(1)
    print gaussian(1.0)
    print "----------------------"
    print gaussian(1.0, sigma=0.5)

    # Compare weighted - normal KNN
    print "\tknn\t\t\t  weighted\t\t\tprice"
    print knnestimate(data, (95.0, 3.0)), '\t', weightedknn(data, (95.0, 3.0)),
    '\t', wineprice(95.0, 3.0)
    print knnestimate(data, (99.0, 3.0)), '\t', weightedknn(data, (99.0, 3.0)),
    '\t', wineprice(99.0, 3.0)
    print knnestimate(data, (99.0, 5.0)), '\t', weightedknn(data, (99.0, 5.0)),
    '\t', wineprice(99.0, 5.0)

    # Crossvalidation
    print 'Crossvalidate with knnestimte:'
    print '[k=3]:\t', crossvalidate(knnestimate, data)
    def knn5(d, v): return knnestimate(d, v, k=5)
    print '[k=5]:\t', crossvalidate(knn5, data)
    def knn1(d, v): return knnestimate(d, v, k=1)
    print '[k=1]:\t', crossvalidate(knn1, data)

    print '\nCrossvalidate with weightedknn:'
    print 'weightf- gaussian:\t', crossvalidate(weightedknn, data)
    print 'weightf- inverseweight:\t', crossvalidate(knninverse, data)

    #
    print 'Crossvalidate with knnestimte:'
    print '[k=3]:\t', crossvalidate(knnestimate, data)

    print '\nCrossvalidate with weightedknn:'
    print 'weightf- gaussian:\t', crossvalidate(weightedknn, data)
    print 'weightf- inverseweight:\t', crossvalidate(knninverse, data)

    # Data2 and compared (Scaled Dimensions) scaled data2
    sdata = rescale(data, [10, 10, 0, 0.5])

    print "Type of crossvalidate\t\t\t\tdata\t\t\tscaled data"
    print 'knnestimte [k=3]:\t\t\t\t', crossvalidate(knnestimate, data), \
        '\t\t', crossvalidate(knnestimate, sdata)
    print 'weightedknn- gaussian:\t\t\t', crossvalidate(weightedknn, data), \
        '\t\t', crossvalidate(weightedknn, sdata)
    print 'weightedknn- inverseweight:\t\t', crossvalidate(knninverse, data), \
        '\t\t', crossvalidate(knninverse, sdata)

    # Optimization
    costf = createcostfunction(weightedknn, data)
    optanneal = optimization.annealingoptimize(weightdomain, costf, step=2)
    optgenet = optimization.geneticoptimize(weightdomain, costf, popsize=25, step=1, maxiter=50)
    scales = [[11,18,0,6], [20,18,0,12], [15, 13, 1, 8], [9, 17, 1, 19], [7, 9, 1, 12], [10, 15, 3, 13]] # 2 ost z mojego

    for scale in scales:
        sdata = rescale(data, scale)
        print "Scale: ", scale
        print "Type of crossvalidate\t\t\t\tdata\t\t\tscaled data"
        print 'knnestimte [k=3]:\t\t\t\t', crossvalidate(knnestimate, data), \
            '\t\t', crossvalidate(knnestimate, sdata)
        print 'weightedknn- gaussian:\t\t\t', crossvalidate(weightedknn, data), \
            '\t\t', crossvalidate(weightedknn, sdata)
        print 'weightedknn- inverseweight:\t\t', crossvalidate(knninverse, data), \
            '\t\t', crossvalidate(knninverse, sdata)

    # Uneven distribution
    data = wineset3()
    wine = [99.0, 20.0]
    print "For wine: ", wine
    print "wineprice is %.2f" % wineprice(wine[0], wine[1])
    print "weightedknn is %.2f" % weightedknn(data, wine)
    print "crossvalidate is %.2f" % crossvalidate(weightedknn, data)

    # Estimating the Probability Density
    print "probguess <40; 80> is %.2f" % probguess(data, [99, 20], 40, 80)
    print "probguess <80; 120> is %.2f" % probguess(data, [99, 20], 80, 120)
    print "probguess <120; 1000> is %.2f" % probguess(data, [99, 20], 120, 1000)
    print "probguess <30; 120> is %.2f" % probguess(data, [99, 20], 30, 120)

    # Graphing the Probabilities (recomended to use some libs pack instead of raw py and install all stuff
    a = array([1, 2, 3, 4])
    b = array([4, 2, 3, 1])
    plot(a, b)
    show()
    t1 = arange(0.0, 10.0, 0.1)
    plot(t1, sin(t1))
    show()

    # Cumulative probability graph
    cumulativegraph(data, (1, 1), 120)

    # Probability density graph
    probabilitygraph(data, (1, 1), 120)
    '''
    # Ex 1 & 2
    neighborsdomain = [(1, int((len(data)-1)*0.90))]
    costf = neighborscostfunction(knnestimate, data, testingels=1, df=pickrandom)
    neighoptgenet = optimization.annealingoptimize(neighborsdomain, costf, step=8, samples=1, cool=0.92)[0]

    wine = (99.0, 5.0)
    klist = [1, 5, neighoptgenet]
    for kel in klist:
        print 'k=', kel, ' :\t', knnestimate(data, wine, k=kel)
    print 'wineprice: ', wineprice(wine[0], wine[1])
