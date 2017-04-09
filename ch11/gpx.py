from random import random, randint, uniform, choice
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
sqw = fwrapper(lambda l: l[0] ** 2, 1, 'square')
euclw = fwrapper(lambda l: ((l[0]-l[1])**2)+(l[2]-l[3])**2, 4, 'euclidean')
flist = [addw, mulw, ifw, gtw, subw, parw  # , sqw, euclw
        ]


def exampletree():
    return node(ifw, [node(gtw, [paramnode(0), constnode(3)]),
                      node(addw, [paramnode(1), constnode(5)]),
                      node(subw, [paramnode(1), constnode(2)]), ])


def makerandomtree(pc, maxdepth=4, fpr=0.5, ppr=0.6, chcount=None, prevfun=None):
    """
    :param pc:
    :param maxdepth:
    :param fpr:
    :param ppr:
    :param chcount: default None to deal with book usage and specified
    for replacement mutation
    :param prevfun:
    :return:
    """
    if maxdepth > 0 and random() < fpr:  # Better check first less computational intensive condition
        if chcount is None:
            f = choice(flist)
            chcount = f.childcount
            children = [makerandomtree(pc, maxdepth - 1, fpr, ppr)
                        for _ in xrange(chcount)]
        else:
            f = choice([f for f in flist if f.childcount == chcount and f != prevfun])
            children = None
        return node(f, children)
    elif random() < ppr:
        # return paramnode(randint(0, pc-1))
        return paramnode(randintexcl(0, pc-1, prevfun))
    else:
        # return constnode(randint(0, 10))
        return constnode((randintexcl(0, 10, prevfun)))


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


def repmutate(t, pc, probchange=0.1):
    """
    Travesing down, chooses a random node on the tree and changes just it.
    :param t:
    :param pc:
    :param probchange:
    :return:
    """
    if random() < probchange:
        if isinstance(t, node):
            tchildlist = t.children
            newnode = makerandomtree(pc, maxdepth=1, fpr=1, chcount=len(tchildlist), prevfun=t.function)
            newnode.children = tchildlist
            return newnode
        elif isinstance(t, paramnode):
            return makerandomtree(pc, maxdepth=0, ppr=1, prevfun=t.idx)
        else:
            return makerandomtree(pc, maxdepth=0, ppr=0, prevfun=t.v)
    else:
        result = deepcopy(t)
        if isinstance(t, node):
            result.children = [repmutate(c, pc, probchange) for c in t.children]
        return result


def crossover(t1, t2, probswap=0.7, top=1):
    if not top and random() < probswap:
        return deepcopy(t2)
    else:
        result = deepcopy(t1)
        if isinstance(t1, node) and isinstance(t2, node):
            result.children = [crossover(c, choice(t2.children), probswap, 0)
                               for c in t1.children]
        return result


def randcrossover(t1, t2, probswap=0.7, top=1):
    if not top and random() < probswap:
        return deepcopy(t2)
    else:
        result = deepcopy(t1)
        if isinstance(t1, node) and isinstance(t2, node):
            result.children = [crossover(c, choice(t2.children), probswap, 0)
                               for c in t1.children]
        return result


def evolve(pc, popsize, rankfunction, maxgen=500,
           mutationrate=0.1, breedingrate=0.4, pexp=0.7, pnew=0.05, prepmut=0.7):
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
    :param pexp: lowering its value, you allow weaker solutions into the final result
                it should be in range of 0 < p < 1 due to log assumption
     turning the process from "survival of the fittest" to "survival of the fittest
     and luckiest."
    :param pnew: Pr when building the new population that a completely new, random
                 program is introduced
    :param prepmut: Pr of replacement mutation instead of branch replacement
    :return:
    """
    # Compute constants once
    xmin = pexp**(popsize-2)
    den = log(pexp)
    def selectindex():
        """
        xmin prevents functionf from risisng error by restricting X (it still return
        pseudo random number)
        :return: random number, tending towards lower numbers. The lower pexp is, more
        lower numbers you will get
        """
        return int(log(uniform(xmin, 1.0)) / den)

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
                idx1, idx2 = selectindex(), selectindex()
                while idx1 == idx2:  # Prevent from self crossing
                    idx2 = selectindex()
                mutfun = repmutate
                if random() > prepmut:  # Replacement mutation combined with whole branch replacemnt.
                    mutfun = mutate
                newpop.append(mutfun(crossover(scores[idx1][1],
                                               scores[idx2][1],
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
    """
    :param p:
    :return:
     0 - player 1 is the winner
     1 - player 2 is the winner
     -1 - player 1 is the winner
    """
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
            move = p[i].evaluate(locs) % 4

            # You lose if you move the same direction twice in a row
            if lastmove[i] == move:
                return 1-i
            lastmove[i] = move

            # Checkig which side was choosen and board limits
            if move == 0:
                location[i][0] -= 1
                if location[i][0] < 0:
                    location[i][0] = 0
            if move == 1:
                location[i][0] += 1
                if location[i][0] > max[0]:
                    location[i][0] = max[0]
            if move == 2:
                location[i][1] -= 1
                if location[i][1] < 0:
                    location[i][1] = 0
            if move == 3:
                location[i][1] += 1
                if location[i][1] > max[1]:
                    location[i][1] = max[1]

            # If you have captured the other player, you win
            if location[i] == location[1-i]:
                return i
    return -1


def tournament(pl):
    # Count losses
    losses = [0 for p in pl]

    # Every player plays every other player
    for i in xrange(len(pl)):
        for j in xrange(len(pl)):
            if i == j:
                continue
            # Who is the winner!?
            winner = gridgame([pl[i], pl[j]])

            # Two points for a loss, one point for a tie
            if winner == 0:
                losses[j] += 2
            elif winner == 1:
                losses[i] += 2
            elif winner == -1:
                losses[i] += 1
                losses[j] += 1
    # Sort and return the results
    z = zip(losses, pl)
    z.sort()
    return z


class humanplayer:
    def evaluate(self, board):
        # Get my location and the location of other player
        me = tuple(board[0:2])
        others = [tuple(board[x: x+2]) for x in xrange(2, len(board)-1, 2)]

        # Display the board
        for i in xrange(4):
            for j in xrange(4):
                if (i, j) == me:
                    print '0',
                elif (i, j) in others:
                    print 'X',
                else:
                    print '.',
            print
        # Show moves, for reference
        print 'Your last move was %d' % board[len(board)-1]
        print ' 0'
        print '2 3'
        print ' 1'
        print 'Enter move: ',

        # Return whatever the user enters
        move = int(raw_input())
        return move


def exampletree2():
    # if x%2 == 1: return x**(1.0/y) else return y**x
    return node(euclw, [node(parw, [paramnode(0), constnode(2)]),
                        node(addw, [paramnode(0), paramnode(1)]),
                        node(subw, [paramnode(1), paramnode(0)]),
                        node(sqw, [paramnode(1)]), ])


if __name__ == '__main__':
    exampletree2 = exampletree2()

    print exampletree2.evaluate([8, 3])
    print exampletree2.evaluate([9, 2])
    print exampletree2.evaluate([4, 2])
    exampletree2.display()

    # Building the Environment
    rf = getrankfunction(buildhiddenset())
    evolve(2, 500, rf, mutationrate=0.1, breedingrate=0.03, pexp=0.75, pnew=0.2, prepmut=0.1)
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

    # Function found after 5,7 mln iterations
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


    # Gridgame
    p1 = makerandomtree(5)
    p2 = makerandomtree(5)

    print gridgame([p1, p2])


    # A Round-Robin Tournament and Playing Against Real People
    winner = evolve(5, 100, tournament, maxgen=50)
    gridgame([winner, humanplayer()])


    # Replacement muation
    exampletree = exampletree()
    print '\n'
    exampletree.display()
    nt = repmutate(exampletree, 2, probchange=0.6)
    print '\n'
    nt.display()

    # Building the Environment
    rf = getrankfunction(buildhiddenset())
    evolve(2, 500, rf, mutationrate=0.2, breedingrate=0.1, pexp=0.7, pnew=0.1, prepmut=0.2)
    '''