from PIL import Image, ImageDraw
from math import sqrt
import random


class bicluster:
    def __init__(self, vec, left=None, right=None, distance=0.0, id=None):
        self.left = left
        self.right = right
        self.vec = vec
        self.distance = distance
        self.id = id


def readfile(filename):
    """
    Funkcja czyta gorny wiersz jako liste nazw kolumn, a skrajnie lewa
    kolumne jako nazwe wierszy. Nastepnie umieszcza dane w liscie, gdzie
    kazdy jej element to dane dla tego wiersza. Naliczenie kazdej komorki
    moze byc przekazane przez wiersz i kolumne w danych, co odpowiada
    indeksom wierszy i kolumn listy.
    :param filename:
    :return: list where each element is a list with number of counts of
    each item, as element of the nested list
    """
    lines = [l for l in file(filename)]
    # Pierwsza linia jest kolumna tutulow
    colnames = lines[0].strip().split('\t')[1:]
    rownames = []
    data = []
    for l in lines[1:]:
        p = l.strip().split('\t')
        # Pierwsza kolumna w kazdym wierszu to jego nazwa
        rownames.append(p[0])
        # Dane dla tego wiersza to jego reszta
        data.append([float(x) for x in p[1:]])
    return rownames, colnames, data


def pearson(v1, v2):
    sum1 = sum(v1)
    sum2 = sum(v2)
    n = len(v1)

    sum1sq = sum([pow(v, 2) for v in v1])
    sum2sq = sum([pow(v, 2) for v in v2])

    psum = sum([v1[i] * v2[i] for i in range(n)])
    # Oblicz r (punktacje Pearsona)
    num = psum - sum1 * sum2 / n
    den = sqrt((sum1sq - pow(sum1, 2) / n) * (sum2sq - pow(sum2, 2) / n))
    if den == 0:
        return 0
    return 1.0 - num / den


def taniamoto(v1, v2):
    c1, c2, shr = 0, 0, 0
    for i in range(len(v1)):
        if v1[i] != 0:
            c1 += 1
        if v2[i] != 0:
            c2 += 1
        if v1[i] != 0 and v2[i] != 0:
            shr += 1
    return 1.0 - (float(shr) / (c1 + c2 - shr))


def hcluster(rows, distance=pearson):
    distances = {}
    currentclustid = -1
    # Klastery sa poczatkowo tylko wierszami
    clust = [bicluster(rows[i], id=i) for i in range(len(rows))]

    while len(clust) > 1:
        lowestpair = (0, 1)
        closest = distance(clust[0].vec, clust[1].vec)
        # Petla po wszystkich parach w poszukiwaniu namniejszego dystansu
        for i in range(len(clust)):
            # Przemiennosc azb to samo co bza
            for j in range(i + 1, len(clust)):
                # "distances" to pamiec podreczna obliczen dystansu
                if (clust[i].id, clust[j].id) not in distances:
                    distances[(clust[i].id, clust[j].id)] = distance(clust[i].vec, clust[j].vec)
                d = distances[(clust[i].id, clust[j].id)]
                # Wszystko sie zgadza w simPears jest return (1 - ...)
                if d < closest:
                    closest = d
                    lowestpair = (i, j)
        # Oblicz srednia z dwoch klasterow
        mergevec = [(clust[lowestpair[0]].vec[i] + clust[lowestpair[1]].vec[i]) / 2.0
                    for i in range(len(clust[0].vec))]
        # Stworz nowy klaster
        newcluster = bicluster(mergevec, left=clust[lowestpair[0]], right=clust[lowestpair[1]],
                               distance=closest, id=currentclustid)
        # Id klastru ktorego nie bylo w oryginalnym zestawie sa negatywne
        currentclustid -= 1
        del clust[lowestpair[1]]
        del clust[lowestpair[0]]
        clust.append(newcluster)
    return clust[0]


def kcluster(rows, distance=pearson, k=4, rettotaldist=False):
    """
    Tworzy losowo zestaw klastrow w zasiegu kazdej zmiennej.
    Z kazda iteracja wiersze sa przypisane do poszcz. centroid,
    a dane centroidy sa uaktualniane do sredniej ze wszystkich
    przypisan. Gdy przypisania sa takie same jak poprzednio-
    alg. konczy prace, a listy K reprezentujace klaster kazda-
    sa zwracane. Ilosc iteracji potrzebna do osiagniecia wyniku
    koncowego jest stosunkowo mala w porownaniu do klastrowania
    hierarchicznego.
    Skoro funkcja uzywa losowej liczby centroid do rozpoczecia
    wiec przynaleznosc elementow niemal za kazdym razem bedzie
    inna, lub bedzie tak z przyczyny losowej inicializowanej
    lokacji centroidy
    :param rows: tablica danych, kazdy element zawiera informacje
     o ilosci slow w nim wysteujacych
    :param distance: metoda obliczania dystansu
    :param k: docelowa ilosc centroid
    :return:
    """
    # Okresl min i max wartosci dla kazdego blogu
    ranges = [(min([row[i] for row in rows]), max([row[i] for row in rows]))
              for i in range(len(rows[0]))]

    # Tworzy k losowo umieszczonych centroid
    clusters = [[random.random() * (ranges[i][1] - ranges[i][0]) + ranges[i][0]
                 for i in range(len(rows[0]))] for j in range(k)]

    lastmatches = None

    for t in range(100):
        bestmatches = [[] for i in range(k)]
        # Znajdz ktora centroida jest najblizsza dla danego wiersza.
        for j in range(len(rows)):
            row = rows[j]
            bestmatch = 0
            for i in range(k):
                d = distance(clusters[i], row)  # kombinacja wszystkich wierszy z klastrami
                if d < distance(clusters[bestmatch], row):
                    bestmatch = i
            bestmatches[bestmatch].append(j)

        # Jesli rezultaty sa te same jak ostatnio => koniec alg.
        if bestmatches == lastmatches:
            print 'Completed after {:d} iterations'.format(t)
            sumdist = sum([sum([distance(clusters[i], rows[rowid]) for rowid in bestmatch
                                if len(bestmatches[i]) > 0]) for i, bestmatch in enumerate(bestmatches)])
            break
        lastmatches = bestmatches

        # Przenies centroidy do sredniej ich czlonkow (poszcz.)
        for i in range(k):  # dla kalstrow
            avgs = [0.0] * len(rows[0])
            if len(bestmatches[i]) > 0: # jesli dany klaster ma przynajmniej 1 przypisany wiersz
                for rowid in bestmatches[i]: # dla wierszy (po id) w klastrze
                    for m in range(len(rows[rowid])):   # dla elementow w wierszu
                        avgs[m] += rows[rowid][m]
                for j in range(len(avgs)):
                    avgs[j] /= len(bestmatches[i])
                clusters[i] = avgs

    if rettotaldist:
        return bestmatches, sumdist
    return bestmatches


def printclust(clust, labels=None, n=0):
    """
    Prints results of hierarhical cluster
    :param clust:
    :param labels:
    :param n:
    :return:
    """
    # Wciecie dla oznaczenia ukladu hierarchii
    for i in range(n):
        print ' ',
    if clust.id < 0:
        # Ujemne id oznacza galaz
        print '-'
    else:
        # Dodatnie id oznacza, ze to jest punkt koncowy
        if labels == None:
            print clust.id
        else:
            print labels[clust.id]

    # Pokaz prawa i lewa galaz
    if clust.left != None:
        printclust(clust.left, labels=labels, n=n + 1)
    if clust.right != None:
        printclust(clust.right, labels=labels, n=n + 1)


def getheight(clust):
    """
    :param clust: wezel i jego odgalezienia
    :return: calkowita wysokosc i gdzie umiescic poszcz. wezly
            (wazne by znac ich calkowita wysokosc)
            pkt. konc - wysokosc = 1
            wpp wysokoc = suma wysokosci jej galezi
            [rekursywnosc robi reszte]
    """
    # Czy to jest pkt. koncowy? Wiec wysokosc to 1
    if clust.left == None and clust.right == None:
        return 1
    # W innym wypadku wysokosc jest suma takich samych wysokosci poszcz. galezi
    return getheight(clust.left) + getheight(clust.right)


def getdepth(clust):
    """
    Liczy calkowite niescislosci korzenia galezi.
    Dlugosc linni jest skalowana do tego ile niescisl.
    jest w danym wezle, stad bedzie generowany wpsolczynnik
    bazowany na tym ile niescisl. jest.
    Glebokosc (depth) wezla to max moliwa niescisloc dla
    danej galezi.
    """
    # Odleglosc od pkt. koncowego to 0.0
    if clust.left == None and clust.right == None:
        return 0
    # Dlugosc galezi jest wieksza z dwoch jej stron + jej dlugosc wlasna
    return max(getdepth(clust.left), getdepth(clust.right)) + clust.distance


def drawdendrogram(clust, labels, jpeg='clusters.jpg'):
    """
    Tworzy nowy obrazek dajac 20px wysokosci i poprawiona
    szerokosc dla kazdego koncowego klastru. Wsp. skalujacy
    jest okreslony przez poprawiona szerokosc/calkowite zagleb.
    Funkcja tworzy obiekt do rysowania dla tego obrazku i wywol.
    'drawnode' dla korzenia wezla mowiac, ze jego lokacja
    powinna byc w polowie drogi w dol lewej czesci obrazka.
    """
    # Wys. i szer.
    depth = getdepth(clust)
    h = getheight(clust) * 20
    w = 1200

    # Szerokosc jest poprawiona, opowiednio skalowanie takze.
    scaling = float(w - 150) / depth
    # Add some width due to long titles etc.
    w += int(30*depth)

    # Tworzy nowy obrazek z bialym tlem
    img = Image.new('RGB', (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    halfh = h/2

    draw.line((0,halfh, 10, halfh), fill=(255, 0, 0))

    # Rysuj pierwszy wezel
    drawnode(draw, clust, 10, halfh, scaling, labels)
    img.save(jpeg, 'JPEG')


def drawnode(draw, clust, x, y, scaling, labels):
    """
    Bierze klaster i jego lokacje, nastepnie najwyrzszy powiazany
    wezel, liczy gdzie powinien byc i rysuje linnie:
    pozioma i dwie pionowe. Pionowe zaleza od ilosci niescislosci
    w wezle. Im dluzsza linia pozioma tym mniej zbieznosci pomiedzy
    zlaczonymi klastrami.
    """
    if clust.id < 0:
        h1 = getheight(clust.left) * 20
        h2 = getheight(clust.right) * 20
        top = y - (h1 + h2) / 2
        bottom = y + (h1 + h2) / 2
        # Dlugosc linni
        ll = clust.distance * scaling
        # Pozioma linia od klastru do potomka
        draw.line((x, top + h1 / 2, x, bottom - h2 / 2), fill=(255, 0, 0))

        # Pionowa linia do lewego elementu
        draw.line((x, top + h1 / 2, x + ll, top + h1 / 2), fill=(255, 0, 0))

        # Pionowa linia do lewego elementu
        draw.line((x, bottom - h2 / 2, x + ll, bottom - h2 / 2), fill=(255, 0, 0))

        # Wezwij funkcje do rysowania lewego i prawego wezla
        drawnode(draw, clust.left, x + ll, top + h1 / 2, scaling, labels)
        drawnode(draw, clust.right, x + ll, bottom - h2 / 2, scaling, labels)
    else:
        # Jesli to jest pkt. koncowy- rysuj oznaczenie elementu
        draw.text((x + 5, y - 7), labels[clust.id], (0, 0, 0))


def rotatematrix(data):
    """
    Obraca dane: kol->wiersze i odwrotnie
    """
    newdata = []
    for i in range(len(data[0])):
        newrow = [data[j][i] for j in range(len(data))]
        newdata.append(newrow)
    return newdata


def scaledown(data, distance=pearson, rate=0.01, dim=2):
    n = len(data)
    # Rzeczywisty dystans pomiedzy parami elem.
    realdist = [[distance(data[i], data[j]) for j in range(n)]
                for i in range(0, n)]
    outersum = 0.0

    # Losowe inicjalizowanie pkt. startowych w dim D
    loc = [[random.random() for d in range(dim)] for i in range(n)]
    fakedist = [[0.0 for j in range(n)] for i in range(n)]

    lasterror = None
    for m in range(0, 1000):
        # Znajdz rzutowane odleglosci
        for i in range(n):
            for j in range(n):
                fakedist[i][j] = sqrt(sum([pow(loc[i][x] - loc[j][x], 2)
                                           for x in range(len(loc[i]))]))
                # Przesun pkt.
        grad = [[0.0 for d in range(dim)] for i in range(n)]

        totalerror = 0
        for k in range(n):
            for j in range(n):
                if j is k:
                    continue
                # Blad to % roznicy pomiedzy odleglosciami
                errorterm = (fakedist[j][k] - realdist[j][k]) / realdist[j][k]

                # Kazdy pkt musi byc przesuniete w stosunku do innego pkt w
                # proporcji do tego jaki blad ma
                for d in range(dim):
                    grad[k][d] += ((loc[k][d] - loc[j][d]) / fakedist[j][k]) * errorterm

                # Sledz blad totalny
                totalerror += abs(errorterm)
        print totalerror

        # Jesli jest gorzej po przesunieciu => koniec
        if lasterror and lasterror < totalerror:
            break
        lasterror = totalerror

        # Przesun kazdy z pkt. o rate*gradient
        for k in range(n):
            for d in range(dim):
                loc[k][d] -= rate * grad[k][d]
    return loc


def draw2d(data, labels, jpeg='mds2d.jpg', dim=2):
    img = Image.new('RGB', (2000, 2000), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    if dim == 1:
        for i in range(len(data)):
            x = (data[i][0] + 0.5) * 1000
            draw.text((0, x), labels[i], (0, 0, 0))
    elif dim == 2:
        for i in range(len(data)):
            x = (data[i][0] + 0.5) * 1000
            y = (data[i][1] + 0.5) * 1000
            draw.text((x, y), labels[i], (0, 0, 0))
    img.save(jpeg, 'JPEG')


def euclidean(v1, v2):
    n = len(v1)
    if not n:
        return 1
    return 1 - sqrt(sum([pow(v1[i] - v2[i], 2) for i in range(n)])) / n


def pythagorean(v1, v2):
    n = len(v1)
    if not n:
        return 1
    return 1 - float(sum([sqrt(v1[i] ** 2 + v2[i] ** 2) for i in range(n)])) / n


def manhattan(v1, v2):
    n = len(v1)
    if not n:
        return 1
    return 1 - float(sum([abs(v1[i] - v2[i]) for i in range(n)])) / n


def kclustresultsave(clust, labels, out='kclustresluts.txt'):
    """
    Save results of k mean cluster as a text file
    :param clust: data of clust in list format, where each element is a list of
    ids which are attached to same centroid in clustering algorythm
    :param labels:
    :param outfile:
    :return:
    """
    outfile=file(out, 'w')
    # Loop over all the clusters in data
    clustnumb = len(clust)
    for i, cl in enumerate(clust):
        outfile.write('----------- Centroid no {} -----------\n'.format(i+1))
        for id in cl:
            outfile.write(labels[id].encode('utf8')+'\n')
        if i+1 < clustnumb:
            outfile.write('\n\n')
    outfile.close()