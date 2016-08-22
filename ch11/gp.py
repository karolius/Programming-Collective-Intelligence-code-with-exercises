from random import random, randint, choice
from copy import deepcopy
from math import log
import time


class fwrapper:
    """
    A wrapper for the functions that will be used on function nodes. Its memeber
    variables are the name of the function, the function itself, and the number
    of paremeters it takes.
    """
    def __init__(self, function, childcount, name):
        self.function = function
        self.childcount = childcount
        self.name = name


class node:
    """
    The class for function nodes (nodes with children). This is initialized with
    an fwrapper. When evaluated is called, it evaluates the child nodes and then
    applies the function to their results.
    """
    def __init__(self, fw, children):
        self.function = fw.function
        self.name = fw.name
        self.children = children

    def evaluate(self, inp):
        results = [n.evaluate(inp) for n in self.children]
        return self.function(results)

    def display(self, indent=0):
        print (' '*indent)+self.name
        for c in self.children:
            c.display(indent+1)


class paramnode:
    """
    The class for nodes that only return one of the parameters passed to the
    program. Its evaluate method returns the parameter specified by idx.
    """
    def __init__(self, idx):
        self.idx = idx

    def evaluate(self, inp):
        return inp[self.idx]

    def display(self, indent=0):
        print '%sp%d' % (' '*indent, self.idx)


class constnode:
    """
    Nodes that return a constatn value. The evaluate method simply returns
    the value with which it was initialized.
    """
    def __init__(self, v):
        self.v = v

    def evaluate(self, inp):
        return self.v

    def display(self, indent=0):
        print '%s%d' % (' '*indent, self.v)


# Changed all to lambda for practise + some functions added
addw = fwrapper(lambda l: l[0] + l[1], 2, 'add')
subw = fwrapper(lambda l: l[0] - l[1], 2, 'subtract')
mulw = fwrapper(lambda l: l[0] * l[1], 2, 'multiply')
ifw = fwrapper(lambda l: l[1] if l[0] > 0 else l[2], 3, 'if')
gtw = fwrapper(lambda l: 1 if l[0] > l[1] else 0, 2, 'isgreater')
parw = fwrapper(lambda l: 1 if l[1] != 0 and l[0] % l[1] else 0, 3, 'parity')
expw = fwrapper(lambda l: l[0] ** l[1], 2, 'exponentiation')
rootw = fwrapper(lambda l: l[0] ** (1.0 / l[1]), 2, 'root')
flist = [addw, mulw, ifw, gtw, subw
        #, parw, expw, rootw
        ]


def exampletree():
    return node(ifw, [node(gtw, [paramnode(0), constnode(3)]),
                      node(addw, [paramnode(1), constnode(5)]),
                      node(subw, [paramnode(1), constnode(2)]), ])


def exampletree2():
    # if x%2 == 1: return x**(1.0/y) else return y**x
    return node(ifw, [node(parw, [paramnode(0), constnode(2)]),
                      node(rootw, [paramnode(0), paramnode(1)]),
                      node(expw, [paramnode(1), paramnode(0)]), ])


def makerandomtree(pc, maxdepth=4, fpr=0.5, ppr=0.6):
    if random() < fpr and maxdepth > 0:
        f = choice(flist)
        children = [makerandomtree(pc, maxdepth-1, fpr, ppr)
                    for _ in xrange(f.childcount)]
        return node(f, children)

    elif random() < ppr:
        return paramnode(randint(0, pc-1))
    else:
        return constnode(randint(0, 10))


def hiddenfunction(x, y):
    return x**2 + 2*y + 3*x + 5


def buildhiddenset():
    rows = []
    for i in xrange(200):
        x = randint(0, 40)
        y = randint(0, 40)
        rows.append([x, y, hiddenfunction(x, y)])
    return rows


def scorefunction(tree, s):
    dif = 0
    for data in s:
        v = tree.evaluate([data[0], data[1]])
        dif += abs(v - data[2])
    return dif


def mutate(t, pc, probchange=0.1):
    if random() < probchange:
        return makerandomtree(pc)
    else:
        result = deepcopy(t)
        if isinstance(t, node):
            result.children = [mutate(c, pc, probchange) for c in t.children]
        return result


def crossover(t1, t2, probswap=0.7, top=1):
    if random() < probswap and not top:
        return deepcopy(t2)
    else:
        result = deepcopy(t1)
        if isinstance(t1, node) and isinstance(t2, node):
            result.children = [crossover(c, choice(t2.children), probswap, 0)
                               for c in t1.children]
        return result


def evolve(pc, popsize, rankfunction, maxgen=500,
           mutationrate=0.1, breedingrate=0.4, pexp=0.7, pnew=0.05):
    """
    This function creates an initial random population. It then loops up to maxgen times,
    each time calling rankfunction to rank the programs from best to worst. The best
    program is automatically passed through to the next generation unaltered, which is
    sometimes referred to as elitism. The rest of the next generation is constructed by
    randomly choosing programs that are near the top of the ranking, and then breeding
    and mutating them. This process repeats until either a program has a perfect score of
    0 or maxgen is reached.
    :param pc: number of input variables for trees
    :param popsize: size of the initial population
    :param rankfunction:
    :param maxgen:
    :param mutationrate: Pr of a mutation
    :param breedingrate: Pr of a crossover
    :param pexp: lowering its value, you allow weaker solutions into the final result,
     turning the process from "survival of the fittest" to "survival of the fittest
     and luckiest."
    :param pnew: Pr when building the new population that a completely new, random
                 program is introduced
    :return:
    """
    # Returns a random number, tending towards lower numbers. The
    # lower pexp is, more lower numbers you will get
    def selectindex():
        return int(log(random()) / log(pexp))

    # Create a random initial population
    population = [makerandomtree(pc) for _ in range(popsize)]
    for i in xrange(maxgen):
        scores = rankfunction(population)
        print scores[0][0]
        if scores[0][0] == 0:
            break
        # The two best always make it
        newpop = [scores[0][1], scores[1][1]]

        # Build the next generation
        while len(newpop) < popsize:
            if random() > pnew:
                newpop.append(mutate(crossover(scores[selectindex()][1],
                                               scores[selectindex()][1],
                                               probswap=breedingrate),
                                     pc, probchange=mutationrate))
            else:
                # Add a random node to mix things up
                newpop.append(makerandomtree(pc))
        population = newpop
    scores[0][1].display()
    return scores[0][1]


def getrankfunction(dataset):
    def rankfunction(population):
        scores = [(scorefunction(t, dataset), t) for t in population]
        scores.sort()
        return scores
    return rankfunction


def gridgame(p):
    max = (3, 3)  # Board size
    # Remember the last move for each player
    lastmove = [-1, -1]

    # Remember the player's locations and put the second player a
    # sufficient didstance from the first
    location = [[randint(0, max[0]), randint(0, max[1])]]
    location.append([(location[0][0] + 2) % 4, (location[0][1] + 2) % 4])

    # Maximum of 50 moves before a tie
    for o in xrange(50):
        for i in xrange(2):  # for each player
            locs = location[i][:] + location[1-i][:]
            locs.append(lastmove[i])
            move = p[i].evaluate(locs)


if __name__ == '__main__':
    '''
    # Building and Evaluating Trees
    exampletree = exampletree()
    exampletree2 = exampletree2()

    print exampletree.evaluate([2, 3])
    print exampletree.evaluate([5, 3])
    print exampletree.evaluate([4, 5])

    print exampletree2.evaluate([8, 3])
    print exampletree2.evaluate([9, 2])
    print exampletree2.evaluate([4, 2])


    # Displaying the Program
    exampletree = exampletree()
    exampletree2 = exampletree2()
    exampletree.display()
    print '\n'
    exampletree2.display()


    # Creating the Initial Population
    for _ in xrange(4):
        exampletree = makerandomtree(2)
        print exampletree.evaluate([2, 3])
        print exampletree.evaluate([5, 3])
        exampletree.display()
        print '\n'


    random1 = makerandomtree(2)
    random2 = makerandomtree(2)

    hiddenset = buildhiddenset()
    print scorefunction(random1, hiddenset)
    print scorefunction(random2, hiddenset)

    # Found 'good'(data fit, but function wasnt the same) result after 5,7 mln iterations
    prev = 999999999999
    i = 0
    random1 = makerandomtree(2)
    start = time.time()
    while True:
        random1 = makerandomtree(2)
        sc = scorefunction(random1, hiddenset)
        if sc < prev:
            prev = sc
            print 'Iter: {:d} \nWith score: {:d} for function:\n'.format(i, sc)
            print 'Czas: ', time.time() - start
            random1.display()
            if sc == 0:
                print 'Motyla noga, udalo sie!'
                print 'Czas: ', time.time()-start
                break
        i += 1


    # Building the Environment
    rf = getrankfunction(buildhiddenset())
    evolve(2, 500, rf, mutationrate=0.2, breedingrate=0.1, pexp=0.7, pnew=0.1)
    '''

