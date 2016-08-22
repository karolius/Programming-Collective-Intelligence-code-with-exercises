import time
from math import log
from PIL import Image, ImageDraw
import zillow
import itertools

my_data=[  # [None,'USA','yes',18,'None'], :::::Dodany wiersz dla zadania 4
         ['slashdot','USA','yes',18,'None'],
         ['google','France','yes',23,'Premium'],
         ['digg','USA','yes',24,'Basic'],
         ['kiwitobes','France','yes',23,'Basic'],
         ['google','UK','no',21,'Premium'],
         ['(direct)','New Zealand','no',12,'None'],
         ['(direct)','UK','no',21,'Basic'],
         ['google','USA','no',24,'Premium'],
         ['slashdot','France','yes',19,'None'],
         ['digg','USA','no',18,'None'],
         ['google','UK','no',18,'None'],
         ['kiwitobes','UK','no',19,'None'],
         ['digg','New Zealand','yes',12,'Basic'],
         ['slashdot','UK','no',21,'None'],
         ['google','UK','yes',18,'Basic'],
         ['kiwitobes','France','yes',19,'Basic']]
"""
W tym programie uzyty jest alg. CART(classif&regr trees). Alg napierw tworzy
wezel korzenia i wybiera najlepsza zmienna by podzielic dane tak, by latwo
okreslic co zrobi uzytkownik
"""


class decisionnode:
    def __init__(self, col=-1, value=None, results=None, bdict={}):
        self.col = col
        self.value = value
        self.results = results
        self.bdict = bdict


# Dzieli zestaw danych wzgledem okreslonej kolumny.
def divideset(rows, column, values):
    # Tworzy funkcje ktora okresla czy dany wiersz jest w 1, czy 2 grupie.
    val0 = values[0]
    vallen = len(values)
    setdict = {}
    valisnumb = True
    if isinstance(val0, int) or isinstance(val0, float):
        values = sorted(values)
        split_function = lambda row, val: row[column] >= val
    else:
        split_function = lambda row, val: row[column] == val
        valisnumb = False

    # Dziel wiersze na grupy
    for row in rows:
        # tylko dla liczb
        for i, val in enumerate(values):
            if split_function(row, val) and (not valisnumb
                                             or (i + 1 == vallen or not split_function(row, values[i + 1]))):
                setdict.setdefault(val, []).append(row)
                break
        else:
            setdict.setdefault("else", []).append(row)
    return setdict


# Tworzy zliczenia mozliwych rezultatow (ostatnia kolumna kazdego wiersza to rezultat)
def uniquecounts(rows):
    results = {}
    for row in rows:
        # Rezultat to ostatnia kolumna
        r = row[-1]
        results[r] = results.get(r, 0) + 1
    return results


# Pr, ze losowo umieszczony element bedzie w zlej kategorii
def giniimpurity(rows):
    total = len(rows)
    counts = uniquecounts(rows)
    imp = 0
    for k1 in counts:
        p1 = float(counts[k1])/total
        for k2 in counts:
            if k1 == k2:
                continue
            p2 = float(counts[k2])/total
            imp += p1*p2
    return imp


# Entropia to suma p(x)log(p(x)) dla wszystkich roznych rezultatow
def entropy(rows):
    log2 = lambda x: log(x)/log(2)
    results = uniquecounts(rows)
    # Oblicz entropie
    ent = 0.0
    for r in results.keys():
        p = float(results[r])/len(rows)
        ent -= p*log2(p)
    return ent


def buildtree(rows, scoref=entropy, mingain=0):
    """
    Jest poczatkowo uruchamiana z lista wierszy. Petla przechodzi po wszystkch kolumnach
    poza ostatnia (zawierajaca wynik), znajdujac dla nich kazda mozliwa wartosc i dzielac
    zestaw danych na dwie podgrupy. Oblicza wazona srednia entropi dla kazdej pary podgrup,
    przez mnozenie entropii kazdej grupy przez ulamek elementow, ktore sie "zakonczyly" w
    kazdej grupie, pamietajac, ktora para miala mniejsza entropie. Jesli tak wazona entropia
    par nie jest mniejsza od galezi, z ktorej zostala wydzielona para, to galazc sie konczy,
    zas zliczenia mozliwych wynikow sa zachowane. W przeciwnym przypadku rekursja i dodanie
    par do galezi. Wyniki wywolan dzielone na podgrupy sa podpiete pod galzezie T-F do
    odtworzenia calego drzewa
    :param rows:
    :param scoref:
    :mingain:
    :return:
    """
    rowlen = len(rows)
    if rowlen == 0:
        return decisionnode()
    current_score = scoref(rows)

    # Sledz najlepsze kryterium
    best_gain = 0.0
    best_criteria = None
    best_sets = None

    column_count = len(rows[0])-1
    for col in range(column_count):
        # Generuje liste z roznymi wartosciami w tej kolumnie
        column_values = {row[col]: 1 for row in rows}
        # Sproboj podzielic wiersze dla kazdej wartosci w tej kolumnie
        for i in range(1, len(column_values)+1):
            for valcombset in itertools.combinations(column_values.keys(), i):
                setsdict = divideset(rows, col, valcombset)
                emptyset = False
                # Uzyskana informacja
                gain = current_score
                for s in setsdict.values():
                    gain -= (float(len(s))/rowlen)*scoref(s)
                    if len(s) <= 0:
                        emptyset = True

                if gain > best_gain and not emptyset:
                    best_gain = gain
                    best_criteria = col, valcombset
                    best_sets = setsdict
    # Stworz rozgalezienia o ile entropia > minimalnego progu
    if best_gain > mingain:
        branchdict = {k: buildtree(s, mingain=mingain) for k, s in best_sets.items()}
        return decisionnode(col=best_criteria[0], value=best_criteria[1], bdict=branchdict)
    else:
        return decisionnode(results=uniquecounts(rows))


def printtree(tree, indent='    '):
    # Czy to lisc?
    if tree.results is not None:
        print str(tree.results)
    else:
        # Wyswietl kryteria
        print str(tree.col)+':'+str(tree.value)+'? '

        # Wyswietl galezie
        for k, node in tree.bdict.items():
            print indent+str(k)+'->',
            printtree(node, indent+'   ')


def getwidth(tree):
    if tree.tb is None and tree.fb is None:
        return 1
    return getwidth(tree.tb)+getwidth(tree.fb)


def getdepth(tree):
    if tree.tb is None and tree.fb is None:
        return 0
    return max(getdepth(tree.tb), getdepth(tree.fb))+1


def drawtree(tree, jpeg='tree.jpg'):
    w = getwidth(tree)*100
    h = getdepth(tree)*100+120

    img = Image.new('RGB', (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    drawnode(draw, tree, w/2, 20)
    img.save(jpeg, 'JPEG')


def drawnode(draw, tree, x, y):
    if tree.results is None:
        # Get the width of each branch
        w1 = getwidth(tree.fb)*100
        w2 = getwidth(tree.tb)*100

        # Okresl calkowite miejsce potrzebne na wezel
        left = x - (w1+w2)/2
        right = x + (w1+w2)/2

        # Napisz nazwe warunku
        draw.text((x-20, y-10), str(tree.col)+':'+str(tree.value), (0, 0, 0))

        # Rysuj polaczenia do galezi
        draw.line((x, y, left+w1/2, y+100), fill=(255, 0, 0))
        draw.line((x, y, right-w2/2, y+100), fill=(255, 0, 0))

        # Rysuj wezly galezi
        drawnode(draw, tree.fb, left+w1/2, y+100)
        drawnode(draw, tree.tb, right-w2/2, y+100)
    else:
        txt = ' \n'.join(['%s:%d'%v for v in tree.results.items()])
        draw.text((x-20, y), txt, (0, 0, 0))


def classify(observation, tree):
    if tree.results is not None:
        cat = tree.results.keys()[0]
        return {cat: float(uniquecounts(my_data)[cat])/len(my_data)}
    else:
        v = observation[tree.col]
        branch = None
        if isinstance(v, int) or isinstance(v, float):
            if v >= tree.value:
                branch = tree.tb
            else:
                branch = tree.fb
        else:
            if v == tree.value:
                branch = tree.tb
            else:
                branch = tree.fb
        return classify(observation, branch)


def prune(tree, mingain):
    """
    Funkcja wywolana na glownym wezle przechodzi po nim wzdluz, az trafi na wezely, ktore maja
    dzieci wylacznie w postaci lisci. Nastepnie stworzy zlaczona liste wynikow z pary i sprawdzi
    entropie. Jesli zmiana w niej bedzie mniejsza niz prog (argument), to liscie zostana usuniete,
    zas wyniki trafia powroca do wezlow-rodzicow. Wtedy zlaczony wezel staje sie kandydatem do
    usuniecia i podzialu z innym wezlem.
    :param tree:
    :param mingain:
    :return:
    """
    # Jesli galezie nie sa lisciami- przytnij je
    if tree.tb.results is None:
        prune(tree.tb, mingain)
    if tree.fb.results is None:
        prune(tree.fb, mingain)

    # Jesli obie podgalezie sa liscmi- sprawdz czy powinny byc dalej rozgalezione
    if tree.tb.results is not None and tree.fb.results is not None:
        # Stworz zlaczony zestaw danych
        tb, fb = [], []
        for v, c in tree.tb.results.items():
            tb += [[v]]*c
        for v, c in tree.fb.results.items():
            fb += [[v]]*c

        # Sprawdz redukcje w entropii
        if entropy(tb+fb) - (entropy(tb)+entropy(fb)/2) < mingain:
            # Rozdziel galezie
            tree.tb, tree.fb = None, None
            tree.results = uniquecounts(tb+fb)


def mdclassify(observation, tree):
    if tree.results is not None:
        cat = tree.results.keys()[0]
        return {cat: float(uniquecounts(my_data)[cat])/len(my_data)}
    else:
        v = observation[tree.col]
        if v is None:
            tr, fr = mdclassify(observation, tree.tb), mdclassify(observation, tree.fb)
            tcount = sum(tr.values())
            fcount = sum(fr.values())
            tcfcsum = tcount+fcount
            tw = float(tcount) / tcfcsum
            fw = float(fcount) / tcfcsum
            result = {}
            for k, v in tr.items():
                result[k] = v * tw
            for k, v in fr.items():
                result[k] = v * fw
            return result
        elif isinstance(v, tuple):
            branchlist = []
            if v[0] >= tree.value or v[1] >= tree.value:
                branchlist.append(tree.tb)
            if v[0] < tree.value or v[1] < tree.value:
                branchlist.append(tree.fb)
            return [mdclassify(observation, b) for b in branchlist]
        else:
            if isinstance(v, int) or isinstance(v, float):
                if v >= tree.value:
                    branch = tree.tb
                else:
                    branch = tree.fb
            else:
                if v == tree.value:
                    branch = tree.tb
                else:
                    branch = tree.fb
            return mdclassify(observation, branch)


def variance(rows):
    """
    Warjancja bierze pod uwage bliskosc liczb wzgledem siebie, zamiast traktowac je jako
    odrebne kategorie. Niska oznacza, ze liczby sa zblizone, duza, ze bardziej oddalone.
    :param rows:
    :return: warjancja
    """
    if len(rows) == 0:
        return 0
    data = [float(row[len(row)-1]) for row in rows]
    datalen = len(data)
    mean = sum(data)/datalen
    return sum([(d-mean)**2 for d in data]) / datalen  # variance


if __name__ == '__main__':
    # decisionnode, divideset, buildtree changed for ex 5
    # Exe 5 with print function edited and else changed for 1-4 exercises
    tree2 = buildtree(my_data)
    printtree(tree2)