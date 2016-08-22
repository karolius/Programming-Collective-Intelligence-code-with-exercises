import re
import math
from sqlite3 import dbapi2 as sqlite


def sampletrain(cl):
    cl.train('Nobody owns the water.','good')
    cl.train('the quick rabbit jumps fences','good')
    cl.train('buy pharmaceuticals now','bad')
    cl.train('make quick money at the online casino','bad')
    cl.train('the quick brown fox jumps','good')


def getwords(doc):
    """
    Wychwutuje argumenty, ktore sa lub ich nie ma, sa to slowa w dokumencie.
    Pewne slowa maja tendencje to pojawiania sie w spamie
    :param doc: dokument do rozbicia na wyrazy
    :return: Zwraca rozbity tekst na slowa, przez dzielenie gdy pojawi sie znak
    nie bedacy litera. Zostawi tylko slowa skonwertowane do malej litery
    """
    splitter = re.compile('\\W*')
    # Rozdziel slowa na znaki nie alfanumeryczne
    words = [s.lower() for s in splitter.split(doc) if 2 < len(s) < 20]

    # Zwroc tylko unikalne slowa
    return {w: 1for w in words}


class classifier:
    # SPRAWDZ KONFIGURACJE Z DEFAULTDICT, CHYBA BEDZIE SPORO SZYBCIEJ
    """
    Enkapsuuje to czego do tad klasyfikator sie nauczyl. Strukturyzacja modulu
    sprawia, ze od reki mozna tworzyc klasyfikatory dla roznych problemow, aby
    byly responsywne wobec swoich zadan (potrzeb grup).
    """
    def __init__(self, getfeatures, ap=0.5):
        """
        Metody w klasie nie uzywaja bezposrednio slownikow, gdyz to ogranicza
        potencjalne mozliwosci na przechowywanie danych w pliku lub bazie danych.

        :local fc: przechowuje zliczenia dla roznych cech w roznych klasyfikacjach
        np. {'python': {'bad': 0, 'good': 6}, 'the': {'bad': 3, 'good': 3}}
        :local cc: (slownik) ile razy dana klasyfikacja byla uzyta
        :param getfeatures: (wenatrz) to funkcja do ekstrachowania cech ze sklasy-
        fikowanych elementow
        :param filename:
        :return:
        """
        # Zlicz cechy/kategorie kombinacji
        self.fc = {}
        # Zlicz dokumenty w kazdej kategorii
        self.cc = {}
        self.getfeatures = getfeatures
        # Parametryzacja zalozenia Pr poczatkowego
        self.ap = ap

    # Zwieksz licznik par cecha/kategoria
    def incf(self, f, cat):
        """
        prev:
        self.fc[f][cat] = self.fc.setdefault(f, {}).setdefault(cat, 0) + 1
        """
        count = self.fcount(f, cat)
        if count == 0:
            self.con.execute("INSERT INTO fc VALUES ('%s', '%s', 1)"
                             % (f, cat))
        else:
            self.con.execute(
                "UPDATE fc SET count=%d WHERE feature='%s' and category='%s'"
                % (count+1, f, cat))

    def incfold(self, f, cat):
        self.fc[f][cat] = self.fc.setdefault(f, {}).setdefault(cat, 0) + 1

    # Zwieksz licznik danej kategorii
    def incc(self, cat):
        """
        prev:
        self.cc[cat] = self.cc.get(cat, 0) + 1
        """
        count = self.catcount(cat)
        if count == 0:
            self.con.execute("INSERT INTO cc VALUES ('%s', 1)" % (cat))
        else:
            self.con.execute("UPDATE cc SET count=%d WHERE category='%s'"
                             % (count+1, cat))

    # Liczba informujaca o tym ile razy cecha wystapila w danej kategorii
    def fcount(self, f, cat):
        """
        :param f: argument
        :param cat: kategoria
        :return:
        prev:
        return self.fc.get(f, {'': 0}).get(cat, 0)
        """
        res = self.con.execute(
            'SELECT count FROM fc WHERE feature ="%s" AND category="%s"'
            % (f, cat)).fetchone()
        if res == None: return 0
        else: return float(res[0])

    # Liczba elementow w kategorii
    def catcount(self, cat):
        """
        prev:
        return float(self.cc.get(cat, 0))
        """
        res = self.con.execute('SELECT count FROM cc WHERE category="%s"'
                               % cat).fetchone()
        if res == None: return 0
        else: return float(res[0])

    # Calkowita liczba elementow
    def totalcount(self):
        res = self.con.execute('SELECT  sum(count) FROM cc').fetchone()
        if res == None: return 0
        return res[0]

    # Lista wszystkich kategorii
    def categories(self):
        cur = self.con.execute('SELECT category FROM cc')
        return [d[0] for d in cur]

    def train(self, item, cat):
        """
        Majac dany element i sposob klasyfikacji uzywa getfeatures z klasy aby
        rozbic podany element na cechy. Nastepnie uzywa incf do zliczenia cech,
        ktore wystapily, a finalnie takze samego rodzaju klasyfikacji.
        :param item: wnp. to dokument
        :param cat: klasyfikacja dokumentu
        :return:
        """
        features = self.getfeatures(item)
        # Zwieksz licznik dla kazdego pojawienia sie cechy przypisanej do danej kat.
        for f in features:
            self.incf(f, cat)

        # Zwieksz licznik dla tej kategorii
        self.incc(cat)
        self.con.commit()

    def fprob(self, f, cat):
        """
        Dzieli ilosc wystapien slowa w dokumencie w danej kategorii
        przez calkowita liczbe dokumentow dla tej kategorii
        :param f: cecha (slowo)
        :param cat:
        :return: prawdopowdobienstwo ze slowo jest w danej kategorii
        """
        if self.catcount(cat) == 0: return 0
        return self.fcount(f, cat)/self.catcount(cat)

    def weightedprob(self, f, cat, prf, weight=1.0): # przed bylo jeszcze ap=0.5 domyslnie
        # Oblicz aktualne P.
        basicprob = prf(f, cat)

        # Zlicz ilosc wystapien danego argumentu we wszystkich kategoriach
        totals = sum([self.fcount(f, c) for c in self.categories()])

        # Oblicz wazona srednia
        return ((weight*self.ap)+(totals*basicprob))/(weight+totals)

    def setdb(self, dbfile):
        self.con = sqlite.connect(dbfile)
        self.con.execute('CREATE TABLE if NOT EXISTS fc(feature, category, count)')
        self.con.execute('CREATE TABLE  if NOT EXISTS cc(category, count)')


class naivebayes(classifier):
    def __init__(self, getfeatures):
        classifier.__init__(self, getfeatures)
        self.thresholds = {}

    def docprob(self, item, cat):
        """
        Do uzycia klasyfikatora naive Bayesian, najpierw nalezy okreslic
        Pr calego dokumentu jako poddanego klasyfikacji. Zakladajac, ze Pr
        poszczegolnych argunentow (slow) sa niezalezne => P wszystkich
        mozna obliczyc przez przemnozenie wszystkich razem. Np.
        Pr(Python | Bad) = 0.2 i (Pr(Casino | Bad) = 0.8) =>
        Pr(Python & Casino | Bad)= 0.8 * 0.2 = 0.16
        :param item: dokument wnp
        :param cat: kategoria
        :return: Pr calkowite dla dokumentu dla danej klasyfikacji
                 (Pr(Document | Category)- ze dana kategoria pasuje
                 do dokumentu)
        """
        features = self.getfeatures(item)
        # Wymnoz P wszystkich argumentow razem
        p = 1
        for f in features: p *= self.weightedprob(f, cat, self.fprob)
        return p

    def prob(self, item, cat):
        """
        **DOBRE ODNIESIENIE co do zaleznosci Pr**
        Pr(Category | Document) = Pr(Document | Category) * Pr(Category)/Pr(Document)
        Gdzie:  1.Pr. ze dany dokument pasuje do danej kategorii
                2.Pr. ze dana kategoria pasuje do danego dokumentu
                3.Pr. ze losowy dokument bedzie pasowal do tej kategorii
                4.Pr. ze losowa kategoria pasuje do dokumentu [jest to stala
                taka sama dla kazdej kategorii, zamiast tego w obliczeniach
                kazda pr kategorii bedzie liczony osobno i porownany na koncu)
                Na mocy prawa Baysa [Pr(A | B) = Pr(B | A) x Pr(A)/Pr(B)]
        :param item:
        :param cat:
        :return:
        # Pr(Category) to Pr, ze losowo wybrany dokument bedzie pasowal do danej
        kategorii, stad jest to liczba dokumentow w tej kategorii dzielona przez
        calkowita liczbe dokumentow.
        """
        catprob = self.catcount(cat)/self.totalcount()
        docprob = self.docprob(item, cat)
        return docprob*catprob

    def setthreshold(self, cat, t):
        self.thresholds[cat] = t

    def getthreshold(self, cat):
        # Szybsze niz 2x przeszukiwanie...
        return self.thresholds.get(cat, 1.0)

    def classify(self, item, default=None):
        """
        :param item: to argumenty
        :param default:
        :return:
        """
        probs = {}
        # Znajdz kategorie z najwiekszym Pr
        max = 0.0
        for cat in self.categories():
            probs[cat] = self.prob(item, cat)
            if probs[cat] > max:
                max = probs[cat]
                best = cat
        # Pewnosc, ze Pr przekracza prog*nastepny_lepszy
        for cat in probs:
            if cat == best: continue
            if probs[cat]*self.getthreshold(best) > probs[best]: return default
        return best


class fisherclassifier(classifier):
    """
    Oblicza Pr kategorii dla danego argumentu w dokumencie. Nastepnie laczy
    poszczegolne Pr i sprawdza czy jest bardziej dopasowane niz rozwiazanie losowe.
    Zwraca Pr dla poszczegolnych kategorii aby mozna je bylo porownac do innych.
    Pr(kategoria|argument) = (liczba dokumentow w tej kategorii z danym argumentem)/
                            (calkowita liczba dokumentow z danym argumentem)
    Wada rozwiazania jest to, ze potrzebuje takiej samej liczby przykladow dla kazdej
    kategorii, by wypracowac sobie umiejetnosc odrozniania.
    Do dzialania normalizacji dla powyzszej metody wymagane jest (ilosc wystapien arg):
    clf = Pr(feature | category) dla tej kategorii
    freqsum = Sum of Pr(feature | category) dla wszystki kategorii
    cprob = clf / (clf+nclf)
    """
    def cprob(self, f, cat):
        # Wystepowanie tego argumentu w kategorii
        clf = self.fprob(f, cat)
        if clf == 0: return 0

        # Wystepowanie tego argumentu we wszystkich kategoriach
        freqsum = sum([self.fprob(f, c) for c in self.categories()])

        # Pr to wystepowanie w tej kategorii / calkowite wystepowanie
        return clf/freqsum

    def fisherprob(self, item, cat):
        # Wymnoz wszystkie Pr razem
        p = 1
        features = self.getfeatures(item)
        for f in features:
            p *= (self.weightedprob(f, cat, self.cprob))

        fscore = -2*math.log(p)

        # Uzyj odrwrotnej chi2 funkcji by uzyskac Pr
        return self.invchi2(fscore, len(features)*2)

    def invchi2(self, chi, df):
        """
        Fisher pokazal, ze jesli Prdobienstwa sa niezalezne i losowe
        to obliczenie bedzie pasowac do
        Oczekujesz elementu, ktory nie nalezy do poszczegolnej
        kategorii zawiera slowa zmiennych Prbienstw dla tej kategorii
        (ktore wystepuja dosc losowo), a element, ktory nie nalezy do
        tej kategorii by mial wiele cech z wysokim Pr. Przez dostarcz-
        anie wyniku obliczen Fisher'a do funkcji inverse chi-kwadrat,
        uzyskasz Pr, ze losowo zestaw Prdobienstw zwroci tak wysoka liczbe
        :param chi:
        :param df:
        :return:
        """
        m = chi/2.0
        sum = term = math.exp(-m)
        for i in range(1, df//2):
            term *= m/i
            sum += term
        return min(sum, 1.0)

    def __init__(self, getfeatures):
        # Przechowuje granice dolne
        classifier.__init__(self, getfeatures)
        self.minimums = {}

    def setminimum(self, cat, min):
        self.minimums[cat] = min

    def getmininum(self, cat):
        if cat not in self.minimums: return 0
        return self.minimums[cat]

    def classify(self, item, default=None):
        # Petla poszukujaca najlepszego rozwiazania
        best = default
        max = 0.0
        for c in self.categories():
            p = self.fisherprob(item, c)
            # Sprawdz czy przekracza minumum
            if p > self.getmininum(c) and p > max:
                best = c
                max = p
        return best

if __name__ == '__main__':
    '''
    # classifier
    cl = classifier(getwords)
    sampletrain(cl)
    print cl.fcount('quick', 'good')
    print cl.fcount('quick', 'bad')
    print cl.fprob('quick', 'good')
    print cl.weightedprob('money', 'good', cl.fprob)


    # naivebayes
    cl = naivebayes(getwords)
    sampletrain(cl)
    print cl.prob('quick rabbit', 'good')
    print cl.prob('quick rabbit', 'bad')

    # classifier with Pr
    cl = naivebayes(getwords)
    sampletrain(cl)
    print "quick rabbit: ", cl.classify('quick rabbit', default='unknown')
    print "quick money: ", cl.classify('quick money', default='unknown')

    cl.setthreshold('bad', 3.0)
    print "quick money [threshold:3]: ", cl.classify('quick money', default='unknown')
    for l in range(10): sampletrain(cl)
    print "quick money [threshold:3 & 10x trenowanie]: ", cl.classify('quick money', default='unknown')

    # fisherclassifier
    cl = fisherclassifier(getwords)
    sampletrain(cl)
    print cl.cprob('quick', 'good')
    print cl.cprob('money', 'bad')
    print cl.weightedprob('money', 'bad', cl.cprob)

    # fisherclassifier fisherprob
    cl = fisherclassifier(getwords)
    sampletrain(cl)
    print cl.cprob('quick', 'good')
    print cl.fisherprob('quick rabbit', 'good')
    print cl.fisherprob('quick rabbit', 'bad')

    # fisher scoring method
    print 'Scoring quick rabbit: ', cl.classify('quick rabbit')
    print 'Scoring quick money: ', cl.classify('quick money')

    cl.setminimum('bad', 0.8)
    print 'Scoring quick rabbit: ', cl.classify('quick rabbit')
    cl.setminimum('good', 0.4)
    print 'Scoring quick money: ', cl.classify('quick money')
    '''
    cl = fisherclassifier(getwords)
    cl.setdb('test1.db')
    sampletrain(cl)

    cl2 = naivebayes(getwords)
    cl2.setdb('test1.db')
    print cl2.classify('quick money')