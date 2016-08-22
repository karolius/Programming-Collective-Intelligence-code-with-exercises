from pylab import *
import math
import time
from svmutil import *
import optimization
svm_model.predict = lambda self, i: svm_predict([0], [i], self)[0][0]


class matchrow:
    def __init__(self, row, allnum=False):
        rowlen = len(row)-1
        if allnum:
            self.data = [float(row[i]) for i in range(rowlen)]
        else:
            self.data = row[:rowlen]
        self.match = int(row[rowlen])  # match: if pair match


def loadmatch(fname, allnum=False):
    """
    :param fname:
    :param allnum:
    :return: list of matchrow classes, each containing raw data and info about match
    """
    return [matchrow(line.split(','), allnum) for line in file(fname)]


def plotagematches(rows):
    xdm, ydm = [r.data[0] for r in rows if r.match == 1], \
               [r.data[1] for r in rows if r.match == 1]
    xdn, ydn = [r.data[0] for r in rows if r.match == 0], \
               [r.data[1] for r in rows if r.match == 0]

    plot(xdm, ydm, 'go')
    plot(xdn, ydn, 'r+')
    show()


def lineartrain(rows):
    averages = {}
    counts = {}

    for row in rows:
        datalen = len(row.data)
        # Geet the class of this point
        cl = row.match
        averages.setdefault(cl, [0, 0]*datalen)
        # Keep track of how many points in each class
        counts[cl] = counts.setdefault(cl, 0) + 1

        # Add this point to the averages
        for i in range(datalen):
            averages[cl][i] += float(row.data[i])

    # Divide sums by counts to get the averages
    for cl, avg in averages.items():
        for l in range(len(avg)):
            avg[l] /= counts[cl]
    return averages


def dotproduct(v1, v2):
    return sum([v1[l]*v2[l] for l in range(len(v1))])


def dpclassify(point, avgs):
    b = (dotproduct(avgs[1], avgs[1]) - dotproduct(avgs[0], avgs[0])) / 2
    y = dotproduct(point, avgs[0]) - dotproduct(point, avgs[1]) + b
    if y > 0:
        return 0
    else:
        return 1


def yesno(v):
    if v == 'yes':
        return 1
    elif v == 'no':
        return -1
    else:
        return 0


def matchcount(interest1, interest2):
    l1 = interest1.split(':')
    l2 = interest2.split(':')
    x = 0
    for v in l1:
        if v in l2:
            x += 1
    return x


def milesdistance(a1, a2):
    return 0


def loadnumerical():
    oldrows = loadmatch('matchmaker.csv')
    newrows = []

    for row in oldrows:
        d = row.data
        data = [float(d[0]), yesno(d[1]), yesno(d[2]),
                float(d[5]), yesno(d[6]), yesno(d[7]),
                matchcount(d[3], d[8]),
                milesdistance(d[4], d[9]),
                row.match]
        newrows.append(matchrow(data))
    return newrows


def scaledata(rows):
    """
    :param rows:
    :return: scaled data by applying scaleinput() to all rows (scaled data in range <0; 1>)
    and scale function to use it with queries
    """
    datalen = len(rows[0].data)
    low = [999999999.0]*datalen
    high = [-999999999.0]*datalen
    # Find the lowest and highest values
    for row in rows:
        d = row.data
        for i in range(len(d)):
            if d[i] < low[i]:
                low[i] = d[i]
            if d[i] > high[i]:
                high[i] = d[i]

    def scaleinput(d):
        return [(d[i] - low[i]) / (high[i] - low[i])
                if high[i] - low[i] else 0
                for i in range(len(low))]

    # Return scaled all the data and the function
    return [matchrow(scaleinput(row.data)+[row.match])
            for row in rows], scaleinput


def veclength(v):
    return sum([p**2 for p in v])


def rbf(v1, v2, gamma=20):
    """
    radial-basis function
    :param v1:
    :param v2:
    :param gamma:
    :return:
    """
    dv = [v1[i] - v2[i] for i in range(len(v1))]
    l = veclength(dv)
    return math.e**(-gamma*l)


def nlclassify(point, rows, offset, gamma=10):
    sum0=0.0
    sum1=0.0
    count0=0
    count1=0

    for row in rows:
        if row.match == 0:
            sum0 += rbf(point, row.data, gamma)
            count0 += 1
        else:
            sum1 += rbf(point, row.data, gamma)
            count1 += 1
    a = (1.0/count0)*sum0
    b = (1.0/count1)*sum1
    y = a - b + offset

    if y > 0:
        return 0
    else:
        return 1


def getoffset(rows, gamma=10):
    l0 = []
    l1 = []
    for row in rows:
        if row.match == 0:
            l0.append(row.data)
        else:
            l1.append(row.data)
    sum0 = sum(sum([rbf(v1, v2, gamma) for v1 in l0]) for v2 in l0)
    sum1 = sum(sum([rbf(v1, v2, gamma) for v1 in l1]) for v2 in l1)
    return (1.0/(len(l1)**2))*sum1 - (1.0/(len(l0)**2))*sum0


# ----------------------------------------------------
def getdomain(numberofvariables, classnumb=2):
    return [(0.0, 1.0)]*numberofvariables*classnumb


def testalgorithm(algf, dataset, avgs):
    error = 0.0
    for row in dataset:
        guess = algf(row.data, avgs)
        error += (row.match - guess) ** 2
    return error / len(dataset)


def avgstodict(avgs):
    half = (len(avgs)+1)/2
    return {0: avgs[:half], 1: avgs[half:]}


def createcostfunction(algf, data):
    def costf(avgs):
        avgsdicted = avgstodict(avgs)
        return testalgorithm(algf, data, avgsdicted)
    return costf


# ----------------------------------------------------
def gcreatecostfunction(algf, data):
    def costf(gamma):
        return crossvalidate(algf, data, g=gamma[0])
    return costf


def dividedata(data, test=0.05):
    trainset = []
    testset = []
    for row in data:
        if random() < test:
            testset.append(row)
        else:
            trainset.append(row)
    return trainset, testset


def crossvalidate(algf, data, g, trials=7, test=0.05, divfun=dividedata):
    error = 0.0
    for i in range(trials):
        trainset, testset = divfun(data, test)
        offset = getoffset(trainset, g)
        error += gtestalgorithm(algf, trainset, testset, offset, g)
    return error / trials


def gtestalgorithm(algf, trainset, testset, offset, g):
    error = 0.0
    for row in testset:
        # nlc(point, rows, offset, gamma=10)
        guess = algf(row.data, trainset, offset, g)
        error += (row.match - guess) ** 2
    return error / len(testset)


def countinterests():
    data = loadmatch('matchmaker.csv')
    interests = {}
    for row in data:
        r = row.data
        for inter in (r[3].split(':') + r[8].split(':')):
            interests[inter] = interests.setdefault(inter, 0) + 1
    return interests


def matchcount(interest1, interest2):
    l1 = interest1.split(':')
    l2 = interest2.split(':')
    x = 0
    for v in l1:
        if v in l2:
            x += 1
    return x


def loadnumerical():
    oldrows = loadmatch('matchmaker.csv')
    newrows = []

    for row in oldrows:
        d = row.data
        data = [float(d[0]), yesno(d[1]), yesno(d[2]),
                float(d[5]), yesno(d[6]), yesno(d[7]),
                matchcount(d[3], d[8]),
                milesdistance(d[4], d[9]),
                row.match]
        newrows.append(matchrow(data))
    return newrows



if __name__ == '__main__':
    # Read data
    agesonly = loadmatch('agesonly.csv', allnum=True)
    matchmaker = loadmatch('matchmaker.csv')
    numericalset = loadnumerical()
    scaledset, scalef = scaledata(numericalset)

    for inter in countinterests().keys():
        print inter

    '''
    # Plot matches
    plotagematches(agesonly)


    # Basic Linear Classification vs averages found by optimization (Ex 2)
    # avgs = lineartrain(agesonly)
    nscaledset, nscalef = scaledata(agesonly)
    avgsscaled = lineartrain(nscaledset)

    weightdomain = getdomain(len(agesonly[0].data))
    costf = createcostfunction(dpclassify, nscaledset)
    optgenet = optimization.geneticoptimize(weightdomain, costf, popsize=25, step=0.03, maxiter=35)
    optavgs = avgstodict(optgenet)

    print 'Scaled averages found with: '
    print 'ineartrain: ', avgsscaled
    print 'optimization: ', optavgs

    print '\t\t\t\tlineartrain\t\toptimization'
    print '[30, 30] --->  ', dpclassify(nscalef([30, 30]), avgsscaled),\
        '\t\t\t\t', dpclassify(nscalef([30, 30]), optavgs)
    print '[30, 25] --->  ', dpclassify(nscalef([30, 25]), avgsscaled),\
        '\t\t\t\t', dpclassify(nscalef([30, 25]), optavgs)
    print '[25, 40] --->  ', dpclassify(nscalef([25, 40]), avgsscaled),\
        '\t\t\t\t', dpclassify(nscalef([25, 40]), optavgs)
    print '[48, 20] --->  ', dpclassify(nscalef([48, 20]), avgsscaled),\
        '\t\t\t\t', dpclassify(nscalef([48, 20]), optavgs)
    print '[25, 35] --->  ', dpclassify(nscalef([25, 35]), avgsscaled),\
        '\t\t\t\t', dpclassify(nscalef([25, 35]), optavgs)


    # Creating the New Dataset & Scaling the Data
    numericalset = loadnumerical()
    print 'numericalset[0]: ', numericalset[0].data

    scaledset, scalef = scaledata(numericalset)
    avgs = lineartrain(scaledset)

    print '\nCompare normal and scaled data for linear train- will pair match?'
    print '\t\t\t\tnormal\t\tscaled'
    print 'numset[0]:\t\t', numericalset[0].match,\
        '\t\t\t', dpclassify(scalef(numericalset[0].data), avgs)
    print 'numset[11]:\t\t', numericalset[11].match,\
        '\t\t\t', dpclassify(scalef(numericalset[11].data), avgs)


    # Kernel Methods
    offset = getoffset(agesonly)

    print 'Age only data: ' \
          '\npair ages\t\tmatch'
    print '[30,30] ->\t\t', nlclassify([30, 30], agesonly, offset)
    print '[30,25] ->\t\t', nlclassify([30, 25], agesonly, offset)
    print '[25,40] ->\t\t', nlclassify([25, 40], agesonly, offset)
    print '[48,20] ->\t\t', nlclassify([48, 20], agesonly, offset)

    ssoffset = getoffset(scaledset)

    print '\nCompare scaled and nonlinearprepared data- will pair match?'
    print '\t\t\t\tscaled\t\tnonlinear and scaled'
    print 'numset[0]:\t\t', numericalset[0].match,\
        '\t\t\t', nlclassify(scalef(numericalset[0].data), scaledset, ssoffset)
    print 'numset[1]:\t\t', numericalset[1].match,\
        '\t\t\t', nlclassify(scalef(numericalset[1].data), scaledset, ssoffset)
    print 'numset[2]:\t\t', numericalset[2].match,\
        '\t\t\t', nlclassify(scalef(numericalset[2].data), scaledset, ssoffset)

    print '\nMan doesn\'t want children, woman does\tBoth want children'
    print nlclassify(scalef([28.0,-1,-1,26.0,-1,1,2,0.8]), scaledset, ssoffset),\
        '\t\t\t\t\t\t\t\t\t\t\t',\
        nlclassify(scalef([28.0,-1,1,26.0,-1,1,2,0.8]), scaledset, ssoffset)


    # LIBSVM test
    x = [[1, 0, 1], [-1, 0, -1]]
    y = [1, -1]
    # svm_model.predict = lambda self, i: svm_predict([0], [i], self)[0][0]

    prob = svm_problem(y, x)
    param = svm_parameter()
    param.kernel_type = LINEAR
    param.C = 10

    m = svm_train(prob, param)
    print 'm.predict([1, 1, 1]): ', m.predict([1, 1, 1])

    svm_save_model('test.model', m)
    m = svm_load_model('test.model')


    # Applying SVM to the Matchmaker Dataset
    answers, inputs = [r.match for r in scaledset], [r.data for r in scaledset]
    param = svm_parameter()
    param.kernel_type = RBF
    prob = svm_problem(answers, inputs)

    m = svm_train(prob, param)

    # Predicting with scaled vars
    newrow = [28.0, -1, -1, 26.0, -1, 1, 2, 0.8]  # Man doesn't want children, woman does
    print newrow, ': -> ', m.predict(scalef(newrow))
    newrow = [28.0, -1, 1, 26.0, -1, 1, 2, 0.8]  # Both want children
    print newrow, ': -> ', m.predict(scalef(newrow))

    CV_ACC = svm_train(answers, inputs, '-v 10')


    # Find G for Kernel (using optimization to practise crossvalidation, there is no sense to use opti)
    gammadomain = [(1, 30)]
    costf = gcreatecostfunction(nlclassify, agesonly)
    optg = optimization.geneticoptimize(gammadomain, costf, popsize=5, step=1, maxiter=9)[0]

    offset = getoffset(agesonly)
    optoffset = getoffset(agesonly, optg)

    print 'Age only data: ' \
          '\npair ages\t\tG=10\t\tG=', optg
    print '[30,30] ->\t\t', nlclassify([30, 30], agesonly, offset), \
        '\t\t', nlclassify([30, 30], agesonly, optoffset)
    print '[30,25] ->\t\t', nlclassify([30, 25], agesonly, offset), \
        '\t\t', nlclassify([30, 25], agesonly, optoffset)
    print '[25,40] ->\t\t', nlclassify([25, 40], agesonly, offset), \
        '\t\t', nlclassify([25, 40], agesonly, optoffset)
    print '[48,20] ->\t\t', nlclassify([48, 20], agesonly, offset), \
        '\t\t', nlclassify([48, 20], agesonly, optoffset)
    '''