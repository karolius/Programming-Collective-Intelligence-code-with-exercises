import time
import random
import math

if __name__ == '__main__':

    people = [('Seymour', 'BOS'),
              ('Franny', 'DAL'),
              ('Zooey', 'CAK'),
              ('Walt', 'MIA'),
              ('Buddy', 'ORD'),
              ('Les', 'OMA'),]

    # LaGuardia airport in New York
    destination = 'LGA'

    flights = {}
    # Plik z danymi zawiera takie dane jak: miejsce odlotu, cel, czas odlotu, przybycia
    # oraz cena dla zestawu danych (poszczegolne aspekty odzielone przecinkiem). Dane
    # sa umieszczane w slowniku (origin, dest)- klucz, a detale jako wartosci.
    for origin, dest, depart, arrive, price in [line.strip().split(',') for line in file('schedule.txt')]:
        flights.setdefault((origin, dest), []).append((depart, arrive, int(price)))


def getminutes(t):
    '''
    :param t:
    :return: zwraca ilosc minut
    '''
    x = time.strptime(t, '%H:%M')
    return x[3]*60+x[4]


def printschedule(r):
    '''
    :param r:
    :return: zwraca loty jakie ludzie wybrali w wygodnym do odczytania formacie- tabeli
    '''
    for d in range(len(r)/2):
        name = people[d][0]
        origin = people[d][1]
        out = flights[(origin, destination)][r[2*d]]
        ret = flights[(destination, origin)][r[2*d+1]]
        print '%10s%10s %5s-%5s $%3s %5s-%5s $%3s' % (name, origin,
                                                  out[0], out[1], out[2],
                                                  ret[0], ret[1], ret[2])


def schedulecost(sol):
    totalprice = 0
    latesarrival = 0
    earliestdep = 24*60

    for d in range(len(sol)/2):
        # Uzyskaj przyloty i odloty
        origin = people[d][1]
        outbound = flights[(origin, destination)][int(sol[2*d])]
        returnf = flights[(destination, origin)][int(sol[2*d+1])]

        outboundend = getminutes(outbound[1])
        outboundstart = getminutes(outbound[0])
        returnfend = getminutes(returnf[1])
        returnfstart = getminutes(returnf[0])

        # Calkowita cena to suma lotow tam i z powrotem +0.5$ za minute lotu + 20$ za lot przed 8 rano
        totalprice += outbound[2]+returnf[2] + 0.5*(outboundend-outboundstart
                                                    + returnfend-returnfstart)
        if outboundstart-480 < 0: totalprice += 20
        if returnfstart-480 < 0: totalprice += 20

        # Sledz ostatni przylot i najwczesniejszy wylot
        if latesarrival<outboundend: latesarrival=outboundend
        if earliestdep>returnfstart: earliestdep=returnfstart

    # Kazda osoba musi czekac na lotnisku dopoki nie dotrze ostatnia.
    # Wszyscy musza takze przybyc w tym samym czasie i czekac na swoje loty.
    totalwait = 0
    for d in range(len(sol)/2):
        origin = people[d][1]
        outbound = flights[(origin, destination)][int(sol[2*d])]
        returnf = flights[(destination, origin)][int(sol[2*d+1])]
        totalwait += latesarrival-getminutes(outbound[1])
        totalwait += getminutes(returnf[0])-earliestdep
    # Czy to rozwiazanie wymaga dodatkowego dnia wynajmu auta? Dodatkowe $50.
    if latesarrival>earliestdep:totalprice+=50
    return totalprice+totalwait


def randomoptimize(domain, costf):
    '''
    :param domain: lista 2 krotek okreslajaca min i max wartosc dla zmiennych
                    dlugosc rozwiazania jest taka sama jak listy (wnp. 9 odlotow
                    i przylotow dla kazdej osoby -> jest to lista (0,8) x2)
    :param costf:  funkcja kosztu (wnp. schedulecost), jest przekazywana jako
                    param stad moze byc uzyta dla roznych prolemow optymalizacyj
                    -nych
    :return:        po generacji 1k losowych indeksow i wywolywaniu f. kosztu
                    zwraca najlepsze trafienie (o najmniejszym koszcie)
    '''
    best = 999999999999
    bestr = None
    for i in range(1000):
        # Tworzy losowe rozwiazanie
        r = [random.randint(d[0], d[1]) for d in domain]
        cost = costf(r)
        if cost<best:
            best = cost
            bestr = r
    return bestr


def hillclimb(domain, costf):
    # Tworzy losowe rozwiazanie
    sol = [random.randint(d[0], d[1]) for d in domain]
    best = 999999
    # Glowna petla
    while True:
        # Tworzy liste sasiednich rozwiazan
        neighbors = []
        for j in range(len(domain)):
            # "O jeden" w kazda strone
            if sol[j]>domain[j][0]:
                neighbors.append(sol[0:j]+[sol[j]+1]+sol[j+1:])
            if sol[j]<domain[j][1]:
                neighbors.append(sol[0:j]+[sol[j]-1]+sol[j+1:])

        # Zobacz jakie jest najlepsze rozwiazanie posrod sasiednich
        current = costf(sol)
        # best = current ????WTF???
        for n in neighbors:
            cost = costf(n)
            if cost < best:
                best = cost
                sol = n
        if best == current:
            break
    return sol


def annealingoptimize(domain, costf, T=10000.0, cool=0.95, step=1, samples=5):
    '''
    p = e^((-wyzszyKoszt - nizszyKoszt)/temperatura) ( dla wysokich wykladnik ->0,
    p-> 1, zas przy nizszej temp. na znaczeniu przybiera roznica w liczniku wykladnika
    p spada wiec alg. pozwala tylko na odrobine gorsze rozwiazania, a nie drastycznie
    gorsze.
    :param domain:
    :param costf:
    :param T:
    :param cool:
    :param step:
    :return:
    '''
    # Losowa inicjalizacja wartosci.
    bestvec = [int(random.randint(d[0], d[1])) for d in domain]
    vec = bestvec
    for s in range(samples):
        i = 0
        while T > 0.1:
            i += 1
            # Wybierz jeden z indeksow
            i = random.randint(0, len(domain)-1)

            # Wybierz kierunek zmian
            dir = random.randint(-step, step)

            # Stworz nowa liste z jedna wartoscia zmieniona
            vecb = vec[:]
            vecb[i] += dir
            # Spr. czy nie wychodzi poza dziedziene.
            if vecb[i] < domain[i][0]:
                vecb[i] = domain[i][0]
            elif vecb[i] > domain[i][1]:
                vecb[i] = domain[i][1]

            # Oblicz stary i nowy koszt
            ea = costf(vec)
            eb = costf(vecb)

            # Rozwiazanie jest lepsze-nadpisz, wpp. sprawdz inne rozwiazanie.
            if eb < ea or random.random() < pow(math.e, (ea-eb)/T):
                vec = vecb
            # Obniz temperature
            T *= cool
            if i % 10 == 0:
                print 'Temperature: ', T
        if costf(vec) < costf(bestvec):
            bestvec = vec
    return vec


def geneticoptimize(domain, costf, popsize=50, step=1, mutprob=0.2, elite=0.2, maxiter=100, maxnoimp=12):
    '''
    :param domain: dziedzina elmentow rozwiazania
    :param costf:
    :param popsize: ilosc rozwiazan poczatkowych
    :param step: wielkosc kroku mutacji
    :param mutprob: P. zajscia mutacji,a nie krzyzowanai
    :param elite: odsetek najlepszych rozwiazan na ktorych bazuja kolejne
    :param maxiter: liczba maxymalnych iteracji (generacji populacji
    :return:
    '''
    if len(domain)-2 < 1:
        mutprob = 2.0
    # Mutacja
    def mutate(vec):
        i = random.randint(0, len(domain)-1)
        if random.random() < 0.5 and vec[i] > domain[i][0]:
            return vec[0:i] + [vec[i]-step] + vec[i+1:]
        elif vec[i] < domain[i][1]:
            return vec[0:i] + [vec[i]+step] + vec[i+1:]
        else:
            return vec

    # Krzyzowanie
    def crossover(r1, r2):
        i = random.randint(1, len(domain)-2)
        return r1[:i] + r2[i:]

    # Stworz inicjacyjna populacje
    if isinstance(step, int):
        pop = [[random.randint(d[0], d[1]) for d in domain] for _ in range(popsize)]
    elif isinstance(step, float):
        pop = [[random.random() for __ in domain] for _ in range(popsize)]

    # Ilu zwyciezcow w kazdej generacji?
    topelite = int(elite*popsize)
    minscore = 9999999

    prevtop = pop[:topelite]
    noimpr = 0

    # Glowna petla
    for i in range(maxiter):
        scores = [(costf(v), v) for v in pop]
        scores.sort()
        ranked = [v for _, v in scores]
        # Zacznij od wygranego
        pop = ranked[:topelite]

        for e in range(topelite):
            if prevtop[e] != pop[e]:
                noimpr = 0
                prevtop = pop
                break
        else:
            noimpr += 1

        if noimpr >= maxnoimp:
            break

        # Dodaj zmutowane i wytworzone jednostki
        while len(pop) < popsize:
            if random.random() < mutprob:
                # Mutacja
                new = mutate(ranked[random.randint(0, topelite)])
            else:
                # Krzyzowanie
                new = crossover(ranked[random.randint(0, topelite)],
                                ranked[random.randint(0, topelite)])
            if new not in pop:
                pop.append(new)
        # Drukuj aktualny wynik
        if scores[0][0] < minscore: minscore = scores[0][0]
        print "minscore: %s" % minscore
    return scores[0][1]


if __name__ == '__main__':
    domain = [(0,8)]*(len(people)*2)
    '''
    # Funkcja kosztu i wydruk danych.
    s = [1,4,3,2,7,3,6,3,2,4,5,3] # kazda para to lot do, z reprezentujacy poszczegolne osoby
    printschedule(s)
    print "Wynik: ", schedulecost(s),"\n", printschedule(s)


    # Wyszukiwanie losowe
    s = randomoptimize(domain, schedulecost)
    print "Wynik(rand): ", schedulecost(s),"\n", printschedule(s)


    # "Wspinaczka"
    s = hillclimb(domain, schedulecost)
    print "Wynik(hillclimb): ", schedulecost(s),"\n", printschedule(s)


    # Hartowanie
    s = annealingoptimize(domain, schedulecost, cool=0.995, samples=10)
    print "Wynik (anneal): ", schedulecost(s),"\n", printschedule(s)


    # Alg. genet.
    s = geneticoptimize(domain, schedulecost, mutprob=0.2, elite=0.25)
    print "Wynik(genet): ", schedulecost(s),"\n", printschedule(s)
    '''

    s = geneticoptimize(domain, schedulecost, mutprob=0.2, elite=0.25)
    print "Wynik(genet): ", schedulecost(s),"\n", printschedule(s)
