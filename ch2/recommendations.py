critics = {'Lisa Rose':         {'Lady in the Water': 2.5, 'Snakes on a Plane': 3.5,
                                'Just My Luck': 3.0, 'Superman Returns': 3.5,
                                'You, Me and Dupree': 2.5, 'The Night Listener': 3.0},
            'Gene Seymour':     {'Lady in the Water': 3.0, 'Snakes on a Plane': 3.5,
                                'Just My Luck': 1.5, 'Superman Returns': 5.0,
                                'The Night Listener': 3.0, 'You, Me and Dupree': 3.5},
            'Michael Phillips': {'Lady in the Water': 2.5, 'Snakes on a Plane': 3.0,
                                'Superman Returns': 3.5, 'The Night Listener': 4.0},
            'Claudia Puig':     {'Snakes on a Plane': 3.5, 'Just My Luck': 3.0,
                                'The Night Listener': 4.5, 'Superman Returns': 4.0,
                                'You, Me and Dupree': 2.5},
            'Mick LaSalle':     {'Lady in the Water': 3.0, 'Snakes on a Plane': 4.0,
                                'Just My Luck': 2.0, 'Superman Returns': 3.0,
                                'The Night Listener': 3.0, 'You, Me and Dupree': 2.0},
            'Jack Matthews':    {'Lady in the Water': 3.0, 'Snakes on a Plane': 4.0,
                                'The Night Listener': 3.0, 'Superman Returns': 5.0,
                                'You, Me and Dupree': 3.5},
            'Toby':             {'Snakes on a Plane': 4.5, 'You, Me and Dupree': 1.0,
                                 'Superman Returns': 4.0}}

from math import sqrt


# Returns a distance -based similarity score for p1 and p2
def sim_distance(prefs, p1, p2):
    # Get the lis of shared_its
    si = {it: 1 for it in prefs[p1] if it in prefs[p2]}

    # if they have no ratings in common, return 0
    if not len(si):
        return 0

    # Add up the squares of all the differences
    sum_of_squares = sum([pow(prefs[p1][it]-prefs[p2][it], 2)
                          for it in prefs[p1] if it in prefs[p2]])
    return 1/(1+sum_of_squares)


# Returns the Pearson correlation coefficient for p1 and p2
def sim_pearson(prefs, p1, p2):
    # Get the list of mutually rated its
    si = {it: 1 for it in prefs[p1] if it in prefs[p2]}

    # if they are no ratings in common, return 0
    n = len(si)
    if not n:
        return 0

    # Add up all the preferences
    sum1 = sum([prefs[p1][it] for it in si])
    sum2 = sum([prefs[p2][it] for it in si])

    # Sum up the squares
    sum1Sq = sum([pow(prefs[p1][it], 2) for it in si])
    sum2Sq = sum([pow(prefs[p2][it], 2) for it in si])

    # Sum up the products
    pSum = sum([prefs[p1][it]*prefs[p2][it] for it in si])

    # Calculate Pearson score
    num = pSum-(sum1*sum2/n)
    den = sqrt((sum1Sq-pow(sum1, 2)/n)*(sum2Sq-pow(sum2, 2)/n))
    if not den:
        return 0
    return num/den


def topMatches(prefs, person, n=5, similarity=sim_pearson):
    """
    Returns the best matches for person from the prefs dictionary.
    Number of results and similarity function are optional params
    :param prefs: dataset
    :param person: podmiot ktoremu szukamy dopasowan
    :param n: liczba najlepszych dopasowan
    :param similarity: rozdzaj porownania
    :return: n najlepszych dopasowan
    """
    scores = [(similarity(prefs, person, other), other) for other in prefs if other is not person]

    # Sort the list so the highest scores appear at the top
    scores.sort()
    scores.reverse()
    return scores[0:n]


def getRecommendations(prefs, person, similarity=sim_pearson):
    """
    Gets recommendations for a person by using a weighted
    average of every other user's rankings
    """
    totals = {}
    simSums = {}
    for other in prefs:
        if other is person:
            continue
        sim = similarity(prefs, person, other)
        if sim <= 0:
            continue
        for item in prefs[other]:
            # only score movies i havent seen yet
            if item not in prefs[person] or not prefs[person][item]:
                totals.setdefault(item, 0)
                totals[item] += prefs[other][item]*sim
                simSums.setdefault(item, 0)
                simSums[item] += sim

    # Create the normalized list values of each film
    # recomendation corrected by similarity ratio of all users (/person)
    # divided by summary ratio of similarity to person
    rankings = [(total/simSums[item], item) for item,total in totals.items()]
    rankings.sort()
    rankings.reverse()
    return rankings


def transformPrefs(prefs):
    result = {}
    for person in prefs:
        for item in prefs[person]:
            result.setdefault(item, {})
            # Flip item and person
            result[item][person] = prefs[person][item]
    return result


def calculateSimilarItems(prefs, n=10):
    """
    Tworzy slownik przedmiotow pokazujacych jaki inny przedmiot
    jest najbardziej do niego podobny.
    """
    result = {}

    # Odwroc preferencje macierzy, by byc przedmiotowo centryczna
    itemPrefs = transformPrefs(prefs)
    c = 0
    for item in itemPrefs:
        # Aktualizacja statusu dla duzych zestawow danych
        c += 1
        if c%100 == 0:
            print "%d / %d" % (c, len(itemPrefs))
        # Znajdz najbardziej podobne przedmioty do tego
        scores = topMatches(itemPrefs, item, n=n, similarity=sim_distance)
        result[item] = scores
    return result


def getRecommendedItems(prefs, itemMatch, user):
    userRatings = prefs[user]
    scores = {}
    totalSim = {}

    # Petla po przedmiotach ocenanych przez uzytkownika
    for (item, rating) in userRatings.items():
        # Petla po przedmiotach pdoobnych do tego
        for (similarity, item2) in itemMatch[item]:
            # Ignoruj jesli ten uzytkownik ma juz oceniony ten przedmiot
            if item2 in userRatings:
                continue
            # Wazone sumy ratingow razy podobienstwo
            scores.setdefault(item2, 0)
            scores[item2] += similarity*rating
            # Sumy wszystkich podobienstw
            totalSim.setdefault(item2, 0)
            totalSim[item2] += similarity
    # Dziel kazde zsumowane punkty przez zsumowane wagi by uzyskac srednia
    rankings = [(score/totalSim[item], item) for item, score in scores.items()]
    # Zwroc ranking od najwiekszego do najmniejszego
    rankings.sort()
    rankings.reverse()
    return rankings[:5]


def loadMovieLens(path=''):
    # Uzyskiwanie tytulow filmow
    movies = {}
    for line in open('u.item'):
        (id, title) = line.split('|')[0:2]
        movies[id] = title
    # Wczytaj dane
    prefs = {}
    for line in open('u.data'):
        (user, movieid, rating, ts) = line.split('\t')
        prefs.setdefault(user, {})
        prefs[user][movies[movieid]] = float(rating)
    return prefs


# Exercises code ------------------------------------------
def sim_tanimoto(prefs, p1, p2):
    # Get the list of shared items (shr/(1s_in_p1+in_p2 - shr)
    si = {it: 1 for it in prefs[p1] if it in prefs[p2]}
    # if they have no ratings in common, return 0
    AandB = len(si)
    den = (len(prefs[p1]) + len(prefs[p2]) - AandB)
    if not AandB or not den:
        return 0
    return float(AandB)/den


def preCompUserSim(prefs, user, similarity=sim_pearson):
    """
    This function compute top 5 similar users to user
    and return them as a dict to get faster recomendations
    :param prefs:
    :param user:
    :param similarity:
    :return:
    """
    top_list = [(0, prefs['1'])]
    for other in prefs:
        if other is user:
            continue
        sim = similarity(prefs, user, other)
        newitem = (sim, other)
        lscore, _ = top_list[-1]
        if lscore < sim:
            top_list.append(newitem)
        top_list.sort()
        top_list.reverse()
        if len(top_list) > 5:
            del top_list[-1]
    top_list.append((1, user))
    return {id: prefs[id] for _, id in top_list}


if __name__ == '__main__':
    '''
    print 'Sim_dist for: Lisa Rose and Gene Seymour: ',\
            sim_distance(critics, 'Lisa Rose', 'Gene Seymour')


    print 'Sim_pears for: Lisa Rose and Gene Seymour: ',\
            sim_pearson(critics, 'Lisa Rose', 'Gene Seymour')


    print topMatches(critics,'Toby',n=3)


    movies = transformPrefs(critics)
    print topMatches(movies,'Superman Returns')


    itemsim = calculateSimilarItems(critics)
    print getRecommendedItems(critics, itemsim, 'Toby')
    '''

    prefs = loadMovieLens()
    person = '81'
    print getRecommendations(preCompUserSim(prefs, person, similarity=sim_pearson), person)
    print getRecommendations(prefs, person)
    # print prefs['81']
    # print getRecommendations(prefs,'87')[0:7]