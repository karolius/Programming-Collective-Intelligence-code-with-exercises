import random
import math
import optimization

import time

# Dormitoria, kade ma dwa wolne miejsca
dorms=['Zeus','Athena','Hercules','Bacchus','Pluto']

#       Osoby z ich wyborami: 1, 2
prefs=[('Toby', ('Bacchus', 'Hercules')),
       ('Steve', ('Zeus', 'Pluto')),
       ('Andrea', ('Athena', 'Zeus')),
       ('Sarah', ('Zeus', 'Pluto')),
       ('Dave', ('Athena', 'Bacchus')),
       ('Jeff', ('Hercules', 'Pluto')),
       ('Fred', ('Pluto', 'Athena')),
       ('Suzie', ('Bacchus', 'Hercules')),
       ('Laura', ('Bacchus', 'Hercules')),
       ('Neil', ('Hercules', 'Athena'))]

        # [(0,9),(0,8),(0,7),(0,6),...,(0,0)]
domain = [(0, (len(dorms)*2)-i-1) for i in range(len(dorms)*2)]


def printsolution(vec):
    """
    Wyswietla rozwiazanie pokazujac jak rozlozone sa miejsca. Funkcja najpierw
    tworzy ich liste, 2 dla kazdego akademika. Nastepnie przeprowadza petle po kaz-
    dym numerze w rozwiazaniu i znajduje nr. dormu w takiej lokacji w liscie
    miejsc gdzie akademik jest przypisany do studenta. Wyswietla studenta i akademik
    oraz usuwa to miejsce z listy, aby zaden inny gosc nie byl tam przypisany.
    Na koncu lista miejsc jest puta, a wszyscy studenci przypisani do akademikow.
    :param vec: Lista wyborow kazdego studenta
    :return:
    """
    # Stworz dwa miejsca dla kazdego akademika
    slots = [i for i in range(len(dorms)) for j in range(2)]

    # Petla po wyborach kazdego studenta
    for i in range(len(vec)):
        x = int(vec[i])
        # Wybierz miejsce z pozostalych
        dorm = dorms[slots[x]]
        # Wyswietl studenta i przypisany mu akademik
        print prefs[i][0], dorm
        # Usun ten slot
        del slots[x]
    # Pokaz finalny koszt
    print "Koszt: ", dormcost(vec)


def dormcost(vec):
    """
    Lista miejsc jest tworzona, a miejsca usuwane gdy sa uzywane.
    Koszty: 1 wybor: 0, 2:1, inny:3
    :param vec: Lista wyborow kazdego studenta
    :return:
    """
    cost = 0
    # Stworz liste slotow
    slots = [0,0,1,1,2,2,3,3,4,4] # miejsca w akademikach po 2 na kazdym

    # Petla po kazdym studencie
    for i in range(len(vec)):
        x = int(vec[i])
        dorm = dorms[slots[x]]
        # print "x: ", x, "vec: ", vec, "slots ", slots, "\ti:", i, "vec[i"
        pref = prefs[i][1]
        if pref[0] == dorm:
            pass
        elif pref[1] == dorm:
            cost += 1
        else:
            cost += 3
        del slots[x]
    return cost


if __name__ == '__main__':
    start = time.time()
    s = optimization.randomoptimize(domain, dormcost)
    printsolution(s)
    print "Rand time:", time.time()-start

    start = time.time()
    s = optimization.geneticoptimize(domain, dormcost)
    printsolution(s)
    print "Geneticopt time:", time.time()-start
