from collections import Counter
import urllib2
import re
from bs4 import *
from urlparse import urljoin
from sqlite3 import dbapi2 as sqlite
import nn
from operator import itemgetter
import time

# Lista slow do zignorowania w analizie skladniowej
ignorewords={'the':1,'of':1,'to':1,'and':1,'a':1,'in':1,'is':1,'it':1}


class crawler:
    """
    Klasa crawler wylapuje wszystkie wazne informacje o linku.
    Tabela 'link' zawiera ID URLu dla zrodla i cel kazdego linku
    jaki to naliczylo. Tabela 'linkword' laczy slowa z linkami.
    """
    # Inicializacja od nazwy bazy danych
    def __init__(self, dbname):
        self.con = sqlite.connect(dbname)

    def __del__(self):
        self.con.close()

    def dbcommit(self):
        self.con.commit()

    # Pomocnicza funkcja do uzyskania id wejscia i dodawanie
    # go jesli nie ma on swojej reprezentacji.
    def getentryid(self, table, field, value, createnew=True):
        """
        Zwraca ID wejscia, jesli go nie ma- tworzy ID i zwraca
        """
        cur = self.con.execute("SELECT ROWID FROM %s WHERE %s = '%s'"
                               % (table, field, value))
        res = cur.fetchone()
        if res is None:
            cur = self.con.execute("INSERT INTO %s (%s) VALUES ('%s')"
                                   % (table, field, value))
            return cur.lastrowid
        else:
            return res[0]

    # Indeksuj pojedyncza strone
    def addtoindex(self, url, soup):
        """
        Metoda wywoluje 2 inne fun. by uzyskac liste slow na stronie.
        Nastepnie dodaje strone i wszystkie slowa do indeksu oraz tworzy
        linki pomiedzy nimi z ich(slow) lokalizacjami w dokumencie. W tym
        przyp. lokacja bedzie indeks w liscie slow.
        """
        if self.isindexed(url): return
        print 'Indexing ' + url

        # Uzyskaj pojedyczne slowa
        text = self.gettextonly(soup)
        words = self.separatewords(text)

        # Uzyskaj id URLu
        urlid = self.getentryid('urllist', 'url', url)

        # Linkuj kazde slowo z tym URLem
        for i, word in enumerate(words):
            if word in ignorewords: continue
            wordid = self.getentryid('wordlist', 'word', word)
            self.con.execute("INSERT INTO wordlocation(urlid, wordid, location) "
                             "VALUES (%d, %d, %d)" % (urlid, wordid, i))

    # Uzyskiwanie tekstu ze strony HTML (nie tagi)
    def gettextonly(self, soup):
        """
        Funckja zwraca dlugi string zawierajacy caly tekst ze strony
        przez rekursywne wywolywanie sie po nastepyjacych elementach
        dokumentu HTML w poszukiwaniu wezlow tekstowych. Text ktory
        byl w odseparowanych sekcjach jest w nadal odseparowany w
        roznych akapitach- to wazne dla zachowania porzadku przy
        okreslonym typie dzialan.
        """
        v = soup.string
        if v is None:
            c = soup.contents
            resulttext = ''
            for t in c:
                subtext = self.gettextonly(t)
                resulttext += subtext+'\n'
            return resulttext
        else:
            return v.strip()

    # Separuj slowa przez znak inny niz spacja
    def separatewords(self, text):
        """
        Funkcja traktuje kazdy znak nie alfanumeryczny jako
        separator- probelmy przy alfabetach nie anglojezycznych
        lub wyrazeniach uzywanych w roznych dziedzinach.
        """
        splitter = re.compile('\\W*')
        # splitter = re.compile('[^a-zA-Z0-9\*\+\$\!\@\#\%\^\&\_\-\|\\\/\<\>\;\:\~]')
        return [s.lower() for s in splitter.split(text) if s is not '']

    # Zwraca True jesli ten url jest juz zindeksowany
    def isindexed(self, url):
        """
        Odpowiada czy strona jest juz w bazie danych. Tak- czy
        ma juz jakies slowa z nia powiazane
        """
        u = self.con.execute("SELECT ROWID FROM urllist WHERE url = '%s'"
                             % url).fetchone()
        # Sprawdz czy URL byl przetwarzany (crawled)
        if u is not None:
            v = self.con.execute('SELECT  * FROM wordlocation WHERE urlid = %d'
                                 % u[0]).fetchone()
            if v is not None: return True
        return False

    # Dodaj link pomiedzy dwie strony (???)
    def addlinkref(self, urlFrom, urlTo, linkText):
        words = self.separatewords(linkText)
        fromid = self.getentryid('urllist', 'url', urlFrom)
        toid = self.getentryid('urllist', 'url', urlTo)
        if fromid == toid: return
        cur = self.con.execute("INSERT INTO link(fromid, toid) VALUES (%d, %d)" % (fromid, toid))
        linkid = cur.lastrowid
        for word in words:
            if word in ignorewords: continue
            wordid = self.getentryid('wordlist', 'word', word)
            self.con.execute("INSERT INTO linkwords(linkid, wordid) VALUES (%d, %d)" % (linkid, wordid))

    # Zaczynamy z lista stron zaglebiajac sie w kolejne linki
    # indeksujac je wraz z posuwaniem sie w przod
    def crawl(self, pages, depth=2):
        """
        Petla po stronach wywolujac addtoindex na kazdym obrocie
        uzywajac BS do uzyskania linkow na stronie i dodaniu URLi
        do zestawu newpages, ktore na koncu petli przechodza w
        kolejne strony do nastepenego wyszukiwania. Po czym proces
        sie powtarza.
        """
        for i in range(depth):
            newpages = {}
            for page in pages:
                try:
                    c = urllib2.urlopen(page)
                except:
                    print 'Could not open %s' % page
                    continue
                try:
                    soup = BeautifulSoup(c.read())
                    self.addtoindex(page, soup)
                    links = soup('a')
                    for link in links:
                        if ('href' in dict(link.attrs)):
                            url = urljoin(page, link['href'])
                            if url.find("'") != -1: continue
                            url = url.split('#')[0]
                            if url[:4] == 'http' and not self.isindexed(url):
                                newpages[url]=1
                            linkText = self.gettextonly(link)
                            self.addlinkref(page, url, linkText)
                    self.dbcommit()
                except:
                    print "Could not parse page %s" % page
            pages = newpages

    # Stworz tablice bazy danych
    def createindextables(self):
        """
        Tworzy system dla tabeli z dodatkowymi indeksami do przyspieszenia
        wyszukiwania (zwlaszcza przydatne przy duzych zestawach danych).
        """
        self.con.execute('CREATE TABLE urllist(url)')
        self.con.execute('CREATE TABLE wordlist(word)')
        self.con.execute('CREATE TABLE wordlocation(urlid, wordid, location)')
        self.con.execute('CREATE TABLE link(fromid integer, toid integer)')
        self.con.execute('CREATE TABLE linkwords(wordid, linkid)')
        self.con.execute('CREATE INDEX wordidx ON wordlist(word)')
        self.con.execute('CREATE INDEX urlidx ON urllist(url)')
        self.con.execute('CREATE INDEX wordurlidx ON wordlocation(wordid)')
        self.con.execute('CREATE INDEX urltoidx ON link(toid)')
        self.con.execute('CREATE INDEX urlfromidx ON link(fromid)')
        self.dbcommit()

    # Oblicz (poprawia obliczenia)ocen stron przy kazdym uzyciu.
    def calculatepagerank(self, iter=20):
        """
        Inicjuje PageRank dla kazdej strony na 1.0, nastepnie przepr.
        petle po kazdym URLu, uzyskuje PR i calkowita liczbe linkow
        dla kazdego powiazanego linku.
        """
        # Wyrzuc aktualna tabele PageRank
        self.con.execute('DROP TABLE IF EXISTS pagerank')
        self.con.execute('CREATE TABLE pagerank(urlid PRIMARY KEY , score)')

        # Ini. kazdy URL z wart. PageRank=1
        self.con.execute('INSERT INTO pagerank SELECT ROWID, 1.0 FROM urllist')
        self.dbcommit()

        for i in range(iter):
            print 'Iteration %d' % (i)
            for (urlid,) in self.con.execute('SELECT ROWID FROM urllist'):
                pr = 0.15

                # Petla po wszystkich stronach, ktore linkuja do tej.
                for (linker,) in self.con.execute(
                        'SELECT DISTINCT fromid FROM link WHERE toid = % d' % urlid):
                    # Uzyskaj PageRank linkera
                    linkingpr = self.con.execute(
                        'SELECT score FROM pagerank WHERE urlid = %d' % linker).fetchone()[0]

                    # Uzyskaj calkowita liczbe linkow z tego linkera
                    linkingcount = self.con.execute(
                        'SELECT count(*) FROM link WHERE fromid = %d' % linker).fetchone()[0]
                    pr += 0.85*(linkingpr/linkingcount)
                self.con.execute('UPDATE pagerank SET score = %f WHERE urlid = %d' % (pr, urlid))
            self.dbcommit()


class searcher:
    def __init__(self, dbname):
        self.con = sqlite.connect(dbname)

    def __del__(self):
        self.con.close()

    def getmatchrows(self,q, exactmatches):
        """
        Dzieki tabeli 'wordlocation' (prosta mozliwosc do linkowania slow do tabeli)
        latwo jest widziec jaka strona zawiera dane slowo.
        Nasza fun. otrzymuje zapytanie stringu, rozdziela je na pojedyncze slowa i
        tworzy zapytanie do SQL, by znalezc tylko te URL majace wszystkie inne slowa.
        """
        # Strings do tworzenia zapytan
        fieldlist = 'w0.urlid'
        tablelist, clauselist = '', ''
        wordids = []

        # Rozdziel slowa spacjami
        words = q.split(' ')
        tablenumber = 0

        for word in words:
            # Uzyskaj ID slowa
            wordrow = self.con.execute(
                "SELECT ROWID FROM wordlist WHERE word = '%s'" % word).fetchone()
            if wordrow is not None:
                # kol. 0 to id slowa
                wordid = wordrow[0]
                wordids.append(wordid)
                if tablenumber > 0:
                    tablelist += ','
                    clauselist +=  ' and '
                    clauselist += 'w%d.urlid=w%d.urlid and ' % (tablenumber-1, tablenumber)
                fieldlist += ',w%d.location' % tablenumber
                tablelist += 'wordlocation w%d' % tablenumber
                clauselist += 'w%d.wordid=%d' % (tablenumber, wordid)
                tablenumber += 1

        # Tworzy zapytania z odseparowanych czesci
        fullquery = "SELECT %s FROM %s WHERE %s" % (fieldlist, tablelist, clauselist)
        print fullquery
        cur = self.con.execute(fullquery)
        rows = [row for row in cur]

        if exactmatches and len(rows[0])>2:
            exact_rows = []
            for u in rows:
                urlmatch = True
                for i, w in enumerate(u[2:]):
                    if w != u[i+1]+1:
                        urlmatch = False
                        break
                if urlmatch: exact_rows.append(u)
            rows = exact_rows
        return rows, wordids

    def getscoredlist(self, rows, wordids):
        """
        Przyjmuje zapytanie, uzyskuje wiersze umieszajac je w
        slowniku i wyswietla w sformatowanej liscie
        """
        totalscores = {row[0]: 0 for row in rows}

        # Funkcja rankingujaca
        weights = [ (0.18, self.frequencyscore(rows)),
                    (0.14, self.locationscore(rows)),
                    (0.24, self.distancescore(rows))
                    ]

        rows = set(row[0] for row in rows)
        uniqueweights = [
                    (0.15, self.pagerankscore(rows)),
                    # (0.1, self.linktextscore(rows, wordids))
                    (0.15, self.longshortdocumentscore(rows, promoteshorter=False)),
                    (0.15, self.inboundlinkscore(rows))
                    ]

        # Kombinacja punktacji dla roznych metod.
        for (weight, scores) in weights:
            for url in totalscores:
                totalscores[url] += weight*scores[url]
        for (weight, scores) in uniqueweights:
            for url in totalscores:
                totalscores[url] += weight*scores[url]
        return totalscores

    def geturlname(self, id):
        return self.con.execute("SELECT url FROM urllist WHERE ROWID = %d"
                                % id).fetchone()[0]

    def query(self, q, exactmatches=False):

        rows, wordids = self.getmatchrows(q, exactmatches)
        scores = self.getscoredlist(rows, wordids)
        rankedscores = sorted([(score, url) for (url, score) in scores.items()], reverse=1)
        for (score, urlid) in rankedscores[0:10]:
            print '%f\t%s' % (score, self.geturlname(urlid))
        return wordids, [r[1] for r in rankedscores[:10]]

    def normalizescores(self, scores, smallIsBetter=False):
        """
        Wszystkie funkcje punktujace (tu) zwracaja slowniki id URLi
        i punktacje liczbowa w roznych postaciach stad potrzeba normalizacji
        Fun. normalizujaca otrzymuje slownik ID i punktacji, a zwraca nowy z
        tymi samymi ID, ale puntkacja w przedz (0,1). Kazda punktacja jest
        skalowana odpowiednio do tego jak dokladnie odpowiada najlepszemu
        zapytaniu (1). Wymaga ozn.: wieksza-mniejsza puntkacja jest lepsza.
        """
        vsmall = 0.00001 # Zabezpieczenie przed /0
        if smallIsBetter:
            minscore = min(scores.values())
            return dict([(u, float(minscore)/max(vsmall, l))
                         for (u, l) in scores.items()])
        else:
            maxscore = max(scores.values())
            if not maxscore:
                maxscore = vsmall
            return dict([(u, float(c)/maxscore) for (u, c) in scores.items()])

    def frequencyscore(self, rows):
        """
        Punktuje strone w relacji czestotliwosci wystepowania slow na stronie
        dla danego zapytanie. Funckja tworzy slownik z wejsciami dla kazdego
        unikalnego ID URLu w wierszu i zlicza ile razy dany elemen wystepowal.
        Nastepnie nastepuje normalizacja (Wiekszy->lepszy wp.)
        Finalnie daje poprawke na zaleznosc wystepowania wyrazenia w stosunku
        do dlugosci tekstu.
        """
        counts = dict([(row[0], 0) for row in rows])
        for row in rows: counts[row[0]] += 1
        return self.normalizescores({url: float(count)/self.con.execute(
            'SELECT max(location) FROM wordlocation WHERE urlid=%d'%url).fetchone()[0]
                                     for url, count in counts.items()})

    def locationscore(self, rows):
        """
        Rankuje wyzej dokumenty ktore zawieraja dane wyrazenie w swoich pocz.
        ,np. tytulach itp. (wyrazenie pojawia sie szybciej) -> dla przyporz.
        w tabeli danych z dok., tytuly sa na pierwszych miejscach.
        Pierwszy element w kazdym wierszu to ID URLu sledzone przez
        lokalizacje wszystkich roznych szukanych wyrazen. Kazde Id moze wystepowac
        wiele razy, raz dla kazdej kombinacji lokacji. Dla kazdego wiersza sumuj
        lokacje wszystkich (szukanych) slow i okresl na tej podstawie jak ten
        wynik ma sie do najelepszego dla tego URLu (jak do tad). Nastepnie
        wynik jest normalizowany. (wp wynik z najmniejsza suma lokacji ~> 1)
        """
        locations = dict([(row[0], 1000000) for row in rows])
        for row in rows:
            loc = sum(row[1:])
            if loc < locations[row[0]]:
                locations[row[0]] = loc
        return self.normalizescores(locations, smallIsBetter=True)

    def distancescore(self, rows):
        """
        Wylapuje wyniki, gdzie dla danego zapytania slowa sa blisko
        siebie na stronie. Wp alg. toleruje rozny ukl. slow (nie musi
        byc zachowana kolejnosc jak w zapytaniu) i nie uzaleznia wyniku
        od slow pomiedzy tymi z zapytania.
        Podstawowa roznica jest taka, ze funkcja przechodzi po lokacjach
        (dist = sum([abs(rows[i]-rows[i-1]) for row in rows]) - biorac
        roznice pomiedzy poszczegolnymi lokacjami a poprzednimi. Przez
        to, ze kazda kombinacja odleglosci jest zwracana dla zapytania,
        pewne jest, iz znajdziemy najmniejsza sume odleglosci.
        """
        # Jesli jest tlko jedno slowo, kazde wygrywa.
        if len(rows[0]) <= 2:
            return dict([(rows[0], 1.0) for row in rows])
        # Inicjalizuj slownik z duzymi wyartosciami
        mindistance  = dict([(row[0], 1000000) for row in rows])

        for row in rows:
            dist = sum([abs(row[i]-row[i-1]) for i in range(2, len(row))])
            if dist < mindistance[row[0]]:
                mindistance[row[0]] = dist
        return self.normalizescores(mindistance, smallIsBetter=False)

    def inboundlinkscore(self, rows):
        """
        Zlicza linki na stronie, na tej podstawie ocenia trafnosc.
        (Podobnie jak literatura/art./ naukowe- ile do danego ref.)
        Funkcja tworzy slownik zliczen przez zapytania do tabeli
        linkow dla kazdego unikalnego ID URLu w wierszach i zwraca
        znormalizowana punktacje.
        """
        return self.normalizescores({u: self.con.execute(
            'SELECT count(*) FROM link WHERE toid = %d'% u).fetchone()[0]
                                     for u in rows})

    def pagerankscore(self, rows):
        """
        Przypisuje kazdej stronie ocene, ktora mowi o jej waznosci.
        Jest ona obliczana na podstawie oceny/waznosci innych stron,
        ktore sie do niej odwoluja.
        W teorii PageRank liczy prawdopod., ze ktos losowo klikajacy
        w linki, dotrze do okreslonej strony. Im wiecej powiazanych
        linkow jest na danej stronie z innych popularnych stron, tym
        wieksza szansa, ze ktos zakonczy poszukiwania w tym miejscu
        (tylko z szacunku prawdop.). Gdyby ktos klikal w nieskonczo-
        nosc, to odwiedzi kazda strone. Jednak wiekszosc ludzi prze-
        staje po chwili. By to wylapac PageRank uzywa wspolcz. damping
        ~0.85 oznaczajacego, ze jest 85% sznsy na to, ze uzytkownik
        bedzie kontynuowal klikanie po linkach na danej stronie. Np.
        PR(A) = 0.15 + 0.85 * ( PR(B)/links(B) + PR(C)
                                /links(C) + PR(D)/links(D) )
        Aby rozpoczac trzeba miec wczesniej ocenione strony-> wp zakl
        sie, poczatkowa ocene (np. 1.0) i powtarza proces liczenia
        aproksymujac do prawdziwej wartosci z kazda iteracja.
        (dla malych zest danych wystarczy 20 iter. < zalezne od ilosci)
        Dla efektywnosci alg. warto obliczyc wczesniej oceny stron.
        """
        pageranks = {row: self.con.execute(
            'SELECT score FROM  pagerank WHERE urlid = %d'
            % row).fetchone()[0] for row in rows}
        maxrank = max(pageranks.values())
        return {u: float(l)/maxrank for (u, l) in pageranks.items()}

    def linktextscore(self, rows, wordids):
        """
        Przechodzi po slowach w wordids i szukajac linkow zawierajacych te slowa.
        Jesli cel linku pasuje do wyszukiwanego wyrazenia, to PR zrodla linku jest
        dodawany do wyniku docelowegj strony. Strona z wieloma linkami z waznych
        stron, ktora zawiera wyrazenia dla zapytania, dostanie bardz wysoka pun-
        ktacje. Wiele stron w wynikach nie bedzie mialo linkow z odpowiednim tekst
        em i bedzie mialo punktacje = 0.
        """

        print("rows: ", rows)
        print("rows: ", wordids)
        linkscores = {row: 0 for row in rows}
        for wordid in wordids:
            cur = self.con.execute('SELECT link.fromid, link.toid FROM linkwords, link WHERE '
                                   'wordid = %d AND linkwords.linkid = link.rowid' % wordid)
            print("cur: ", cur)
            for (fromid, toid) in cur:
                if toid in linkscores:
                    pr = self.con.execute('SELECT score FROM pagerank WHERE urlid = %d'
                                          % fromid).fetchone()[0]
                    linkscores[toid] += pr
        maxscore = max(linkscores.values())
        normalizedscores = {u: float(l)/maxscore for (u, l) in linkscores.items()}
        return normalizedscores

    def nnscore(self, rows, wordids):
        # Uzyskaj unikalne id URLi jako uporzadkowana lista
        urlids = [urlid for urlid in set([row[0] for row in rows])]
        nnres = mynet.getresult(wordids, urlids)
        scores = dict([(urlids[i], nnres[i]) for i in range(len(urlids))])
        return self.normalizescores(scores)

    def longshortdocumentscore(self, rows, promoteshorter=True, colid=0):
        scores = {row: self.con.execute(
            'SELECT max(location) FROM wordlocation WHERE urlid=%d'%row).fetchone()[0]
                       for row in rows}
        return self.normalizescores(scores, smallIsBetter=promoteshorter)

    def getpotentialrelevantlinks(self, rows):
        dict = {}
        for row in rows:
            rowlinks = self.con.execute(
                "SELECT toid FROM link WHERE fromid = %d" % row).fetchall()
            if not dict:
                for url in rowlinks:
                    dict[url[0]] = 1
            else:
                for url in rowlinks:
                    if url[0] not in dict:
                        dict[url[0]] = 1
                    else:
                        dict[url[0]] += 1
        return [k for k, _ in Counter(dict).most_common(len(dict)/250)]

        # zmierz czas jak zrobisz slownik, a jak zwrocisz odrazu lub w slowniku powtarzasz funkcje
        # np. max(...)


if __name__ == '__main__':
    '''
    # Dzialanie Crawlera
    pages = ['https://en.wikipedia.org/wiki/Mutiny_on_the_Bounty']
    crawler = crawler('')
    crawler.crawl(pages)


    # Tworzenie indeksow i schematu DB
    crawler = crawler('searchindex.db')
    crawler.createindextables()


    # Indeksuje strony przy dzialaniu
    crawler = crawler('searchindex.db')
    crawler.createindextables()
    pages = ['https://en.wikipedia.org/wiki/Mutiny_on_the_Bounty']
    crawler.crawl(pages)


    # Tworzy i uzupelnia tabele.
    crawler = crawler('searchindex.db')
    crawler.createindextables()
    pages = ['https://en.wikipedia.org/wiki/Mutiny_on_the_Bounty']
    crawler.crawl(pages)


    # Wypisanie slow
    crawler = crawler('searchindex.db')
    print [row for row in crawler.con.execute
    ('SELECT rowid FROM wordlocation WHERE wordid=1')]
    '''

    # Wyszukiwanie slow
    e = searcher('searchindex.db')
    e.query('national park', exactmatches=True)

    '''
    e = searcher('searchindex.db')
    crawler = crawler('searchindex.db')
    crawler.calculatepagerank()
    e.query('big island')

    mynet = nn.searchnet('nn.db')
    '''