

import feedparser
import re
import nn  # W generatehiddennode() jest wylaczony warunek < 3 argumenty
from sqlite3 import dbapi2 as sqlite
splitter = re.compile('\\W*')


# Wez nazwe pliku lub URL kanalu bloga i klasyfikuj wejscia
def read(feed, nnclasifier, datafile):
    # Uzyskaj wejscia kanalu i przeprowadz po nich petle
    f = feedparser.parse(feed)
    categories = [datafile.getentryid('catlist', 'cat', 'inne')]
    catnames = ['inne']
    for i, entry in enumerate(f['entries']):
        print '\n_____________________________________________________'
        # Zawartosc
        print 'Title:       '+entry['title'].encode('utf-8')
        print 'Publisher:       '+entry['publisher'].encode('utf-8')
        print '\n'+entry['summary'].encode('utf-8')

        # Zloz caly tekst jako jeden element do klasyfikatora
        # fulltext = '%s\n%s\n%s' % (entry['title'], entry['publisher'], entry['summary'])

        # Wyswietl najlepsz przypuszczenie co do aktualnej kategorii
        parsedentry = entryfeatures(entry)
        datafile.addtoindex(i, parsedentry)
        indexedwords = datafile.geturlwordids(i)
        # dla ustawienia z parametrem wyswietli bezposrednio kategorie, bez- wagi kategorii
        print 'Guess: ', nnclasifier.getresult(indexedwords, categories)

        # Popros uzytkownika o podanie poprawnjej kategorii i trenuj na niej, jesli jest
        # nowa, to dodaj ja do listy kategorii
        correctcat = raw_input('Enter category: ')
        if correctcat not in catnames:
            categories.append(datafile.getentryid('catlist', 'cat', correctcat))
            catnames.append(correctcat)
            print("***Added category: ", correctcat, '***')
        nnclasifier.trainquery(indexedwords, categories, datafile.getentryid('catlist', 'cat', correctcat))  # poprzednio fulltext
        print 'Result after train: ', nnclasifier.getresult(indexedwords, categories)
        print'Catnames: ', catnames


def entryfeatures(entry):  # flist dla ulatwienia pracy z NN
    l = []

    # Wyodrebnij slowa tytulu
    for s in splitter.split(entry['title']):
        if 2 < len(s) < 20:
            l.append(s.lower())

    for s in splitter.split(entry['summary']):
        if 2 < len(s) < 20:
            l.append(s.lower())

    if len(entry['summary']) > 250:
        l.append("EXCLENGTH*&q$%")

    # Zlicz slowa zaczynajace sie z duzej litery, podejrzanie dlugie
    uc = 0
    lw = 0
    wordsamout = len(l)
    for word in l:
        if word.isupper():
            uc += 1

        if len(word) > 16:
            lw += 1

    # Slowo zlozone z duzych liter oznacza wykrzykiwanie
    # i oznacz dokumenty zawierajace znaczna czesc dlugich slow
    if float(uc)/wordsamout > 0.3:
        l.append("UPPERCASE*&q$%")
    if float(lw)/wordsamout > 0.3:
        l.append("PREPOFLONGWORDS*&q$%")

    return l


class nnclassifierdatatable:
    def __init__(self, dbname):
        self.con = sqlite.connect(dbname)

    def __del__(self):
        self.con.close()

    def maketables(self):
        self.con.execute('CREATE TABLE wordlist(word)')
        self.con.execute('CREATE TABLE urllist(url)')
        self.con.execute('CREATE TABLE wordlocation(urlid, wordid)')
        self.con.execute('CREATE INDEX wordidx ON wordlist(word)')
        self.con.execute('CREATE INDEX urlidix ON urllist(url)')
        self.con.execute('CREATE INDEX wordulridx ON wordlocation(wordid)')

        self.con.execute('CREATE TABLE catlist(cat)')
        self.dbcommit()

    def dbcommit(self):
        self.con.commit()

    def getentryid(self, table, field, value):
        """
        :param table: tabela z jakiej zwracane jest id
        :param field: kolumna z jakiej zwracane jest id
        :param value: wartosc dla jakiej zwracane jest id
        :return: ID wejscia, jeli go nie ma to najpierw tworzy i zwraca
        """
        cur = self.con.execute("SELECT ROWID FROM %s WHERE %s='%s'"
                               % (table, field, value))
        res = cur.fetchone()
        if res is None:
            cur = self.con.execute("INSERT INTO %s (%s) VALUES ('%s')"
                                   % (table, field, value))
            self.dbcommit()
            return cur.lastrowid
        else:
            return res[0]

    # Spr czy url jest juz zindeksowany
    def isindexed(self, url):
        u = self.con.execute("SELECT ROWID FROM urllist WHERE url = '%s'"
                             % url).fetchone()
        # Spr czy url byl przetwarzany
        if u is not None:
            v = self.con.execute('SELECT * FROM wordlocation WHERE urlid = %d'
                                 % u[0]).fetchone()
            if v is not None:
                return True
        return False

    # Indeksuje pojedyncza strone
    def addtoindex(self, url, words):
        if self.isindexed(url):
            return
        print 'Indexing '+str(url)

        # Uzyskaj id urla
        urlid = self.getentryid('urllist', 'url', url)
        # Linkuj slowa z urlem
        for word in words:
            wordid = self.getentryid('wordlist', 'word', word)
            self.con.execute("INSERT INTO wordlocation(urlid, wordid) VALUES (%d, %d)"
                             % (urlid, wordid))
        self.dbcommit()

    def geturlwordids(self, url):
        uid = self.con.execute("SELECT ROWID FROM urllist WHERE url='%s'" % url).fetchone()[0]
        return [wordid[0] for wordid in self.con.execute(
            "SELECT wordid FROM wordlocation WHERE urlid=%s" % uid).fetchall()]

    def getallcatids(self):
        return [cid[0] for cid in self.con.execute("SELECT ROWID FROM catlist").fetchall()]


if __name__ == '__main__':
    '''
    # Tworzenie tabel tylko przy 1 uruchomieniu
    data.maketables()
    mynet.maketables()
    '''
    # Dane z blogow i dane dla nn w oddzielnych bazach
    data = nnclassifierdatatable('nndata.db')
    mynet = nn.searchnet('nnclassiffier.db')
    read('python_search.xml', mynet, data)
