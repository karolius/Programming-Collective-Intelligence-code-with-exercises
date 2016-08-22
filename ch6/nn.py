from math import tanh
import sqlite3
# from sqlite3 import dbapi2 as sqlite


def dtanh(y):
    return 1.0-y*y


class searchnet:
    """
    Jako, ze NN musi byc trenowana w czasie gdy uzytkownik kieruje zapyta
    nia, potrzeba przechowywac dane w DB. (Aktualnie mamy tabele slow i
    urli). Potrzebna jest table na przechowywanie (hiddennode) war. ukry
    tej oraz 2 tab. na polaczenie (tabela slow->ukt. war.
    oraz ukr.war-> war. wyj).
    """
    def __init__(self, dbname):
        self.con = sqlite3.connect(dbname)

    def __del__(self):
        self.con.close()

    def maketables(self):
        """
        Tablica nie posiada indeksowania, co moze poprawic jej szybkosc.
        """
        self.con.execute('create TABLE hiddennode(create_key)')
        self.con.execute('create TABLE wordhidden(fromid, toid, strength)')
        self.con.execute('create TABLE hiddenurl(fromid, toid, strength)')
        self.con.commit()

    def getstrength(self, fromid, toid, layer):
        """
        Okresla aktualna sile polaczenia. Poniewaz nowe polaczenia sa tworzo
        -ne tylko gdy zachodzi potrzeba, stad metoda zwraca wartosc domyslna
        jesli nie ma polaczen. Dla linkow od slow do HL (hidden layer), wart.
        wynosci -0.2 wiec domyslnie dodatkowe slowa beda mialy lekko ujemna
        wartosc na etapie aktywacji wezlow ukrytych. Od linkow z HL do URLi
        metoda zwraca domyslnie 0.
        """
        if not layer: table = 'wordhidden'
        else: table = 'hiddenurl'
        res = self.con.execute('select strength FROM %s WHERE fromid=%d AND toid=%d'
                               % (table, fromid, toid)).fetchone()
        if res is None:
            if layer==0: return -0.2
            if layer==1: return 0
        return res[0]

    def setstrength(self, fromid, toid, layer, strength):
        """
        Okresla czy polaczenie juz istnieje i aktualizuje, lub tworzy polo
        -czenie o nowej sile.
        """
        if not layer: table = 'wordhidden'
        else: table = 'hiddenurl'
        res = self.con.execute('select rowid FROM %s WHERE fromid=%d AND toid=%d'
                               % (table, fromid, toid)).fetchone()

        if res is None:
            self.con.execute('insert INTO %s (fromid, toid, strength) VALUES (%d, %d, %f)'
                             % (table, fromid, toid, strength))
        else:
            rowid = res[0]
            self.con.execute('update %s SET strength=%f WHERE rowid=%d'
                             % (table, strength, rowid))

    def generatehiddennode(self, wordids, urls):
        """
        Tworzy nowy wezel w HL za kazdym razem, gdy zachodzi nowa kombinacja
        slow, ktorych wczesniej w takim ukladzie nie widzianio. Funkcja two
        -rzy domyslno-wagowe linki pomiedzy slowami i HL oraz wezlem zapytania
        i URLem wynikowym zwracanym przez to zapytanie.
        """
        # if len(wordids) > 3: return None
        # Sprawdz czy juz istnieja wezly dla tego zestawu slow
        createkey = '_'.join(sorted([str(wi) for wi in wordids]))
        res = self.con.execute("select rowid FROM hiddennode WHERE create_key='%s'"
                               % createkey).fetchone()
        # Jesli nie- stworz go
        if res is None:
            cur = self.con.execute(
                "insert INTO hiddennode (create_key) values ('%s')" % createkey)
            hiddenid = cur.lastrowid
            # Nadaj jakies domyslne wagi
            for wordid in wordids:
                self.setstrength(wordid, hiddenid, 0, 1.0/len(wordids))
            for urlid in urls:
                self.setstrength(hiddenid, urlid, 1, 0.1)
            self.con.commit()

    def getallhiddenids(self, wordids, urlids):
        """
        Przed propagacja przednia alg. musi stworzyc czesc NN odpowiedniej
        dla zapytania wezlow i polaczen w DB.
        Pierwszy etap to znalezienie wezlow dla danego zapyt.
        -wnp- wezly polaczone ze slowami z zapytania lub URLami z wyniku.
        Jako, ze pozostale wezly niczego w tym przyp. nie determnuja (wyj.
        i trenowanie sieci)- pomijamy je.
        """
        l1 = {}
        for wordid in wordids:
            cur = self.con.execute('SELECT toid FROM wordhidden WHERE fromid=%d'
                                   % wordid)
            for row in cur: l1[row[0]] = 1
        for urlid in urlids:
            cur = self.con.execute('SELECT fromid FROM hiddenurl WHERE toid=%d'
                                   % urlid)
            for row in cur: l1[row[0]] = 1
        return l1.keys()

    def setupnetwork(self, wordids, urlids):
        """
        Konstruuje odpowiednia siec z aktualnymi wagami z DB. Funkcja usta
        -wia wiele zmiennych dla roznych przypadkow dla tej klasy- lista
        slow, wezly zapytania i urli, stopien wyjscia kazdego wezla i wagi
        dla kazdego linku pomiedzy wezlami. Wagi sa pobierane z DB uzywajac
        fun. ktore byly zdefiniowane wczesniej.
        """
        # lista wartosci
        self.wordids = wordids
        self.hiddenids = self.getallhiddenids(wordids, urlids)
        self.urlids = urlids

        # wezel wyjsc
        self.ai = [1.0]*len(self.wordids)
        self.ah = [1.0]*len(self.hiddenids)
        self.ao = [1.0]*len(self.urlids)

        # tworzy matyce wag
        self.wi = [[self.getstrength(wordid, hiddenid, 0)
                    for hiddenid in self.hiddenids]
                   for wordid in self.wordids]

        self.wo = [[self.getstrength(hiddenid, urlid, 1)
                    for urlid in self.urlids]
                   for hiddenid in self.hiddenids]

    def feedforward(self):
        """
        Alg. propagacji przedniej. Otrzymuje liste wejsc, przepuszcza je
        przez siec i zwraca wyjscia wszystkich wezlow w OL (output layer).
        Wnp. jesli tylko skonstuowalismy siec ze slowami w zapytaniu, to
        wy ze wszystkich we zawsze dadza wartosc 1.
        Funckja przechodzac po wezlach HL i sumujac wy z IL*str_pol.
        Wy. kazdego z wezlow to tanh(sum) wszystkich wejsc przepuszczonych
        przez OL. OL takze przemnaza wyjscia poprzedniej warstwy * ich_str
        i naklada tgh() do uzyskania wyniku koncowego. Przez taki mechanizm
        latwo jest poszerzyc siec o kolejne warstwy traktujac wy 1 jak we 2.
        """
        # Wyjsciami sa tylko slowa z zapytania
        for i in range(len(self.wordids)):
            self.ai[i] = 1.0

        # aktywacja ukrytych
        for j in range(len(self.hiddenids)):
            sum = 0.0
            for i in range(len(self.wordids)):
                sum += self.ai[i] * self.wi[i][j]
            self.ah[j] = tanh(sum)

        # aktywacja wyjscia
        for k in range(len(self.urlids)):
            sum = 0.0
            for j in range(len(self.hiddenids)):
                sum += self.ah[j] * self.wo[j][k]
            self.ao[k] = tanh(sum)

        return self.ao

    def getresult(self, wordids, urlids, retcat=False):
        self.setupnetwork(wordids, urlids)
        if retcat:
            l = self.feedforward()
            return urlids[l.index(max(l))]
        return self.feedforward()

    def backPropagate(self, targets, N=0.5):
        """
        Oblicza na bierzaco bledy i koryguje wagi (obliczenia bazuja na akt.
        wagach, a nie zaktualiz.)
        """
        # Oblicza blad dla wy
        output_deltas = [0.0]*len(self.urlids)
        for k in range(len(self.urlids)):
            error = targets[k]-self.ao[k]
            output_deltas[k] = dtanh(self.ao[k])*error

        # Oblicz bledy dla HL
        hidden_deltas = [0.0]*len(self.hiddenids)
        for j in range(len(self.hiddenids)):
            error = 0.0
            for k in range(len(self.urlids)):
                error = error+output_deltas[k]*self.wo[j][k]
            hidden_deltas[j] = dtanh(self.ah[j]) *error

        # Zaktualizuj wyjsciowe wagi
        for j in range(len(self.hiddenids)):
            for k in range(len(self.urlids)):
                change = output_deltas[k]*self.ah[j]
                self.wo[j][k] = self.wo[j][k]+N*change

        # Zaktualizuj we. wagi
        for i in range(len(self.wordids)):
            for j in range(len(self.hiddenids)):
                change = hidden_deltas[j]*self.ai[i]
                self.wi[i][j] = self.wi[i][j]+N*change

    def trainquery(self, wordids, urlids, selectedurl):
        """
        Tworzy siec, uruchamia propagacje przednia i wsteczna.
        """
        # generuj wezel ukryty jesli jest taka potrzeba
        self.generatehiddennode(wordids, urlids)

        self.setupnetwork(wordids, urlids)
        self.feedforward()
        targets = [0.0]*len(urlids)
        targets[urlids.index(selectedurl)] = 1.0
        self.backPropagate(targets)
        self.updatedatebase()

    def updatedatebase(self):
        """
        Aktualizuje DB nowymi wagami przechowywanymi w zmiennych wi, wo.
        """
        # Ustaw je wartosciom DB
        for i in range(len(self.wordids)):
            for j in range(len(self.hiddenids)):
                self.setstrength(self.wordids[i], self.hiddenids[j], 0, self.wi[i][j])
        for j in range(len(self.hiddenids)):
            for k in range(len(self.urlids)):
                self.setstrength(self.hiddenids[j], self.urlids[k], 1, self.wo[j][k])
        self.con.commit()


if __name__ == '__main__':
    '''
    mynet = searchnet('nn.db')
    mynet.maketables()
    wWorld,wRiver,wBank =101,102,103
    uWorldBank,uRiver,uEarth =201,202,203
    mynet.generatehiddennode([wWorld,wBank],[uWorldBank,uRiver,uEarth])
    '''
    # Tworzenie nowego wezla w HL i linkow do nowego wezla z domyslnymi
    # wartosciami. Funkcja inicjacyjnie odpowiada kiedykolwiek "word" i
    # "bank" sa podane razem, ale to polaczenie moze slabnosc w czasie.
    '''
    for c in mynet.con.execute('select * from wordhidden'): print c
    for c in mynet.con.execute('select * from hiddenurl'): print c
    '''

    # Dzieki NN, siec wie nie tylko z jakimi linkami dane zapytania sa
    # powiazane ale tez jakie slowa sa kluczowe dla danych linkow.
    mynet = searchnet('nn.db')
    mynet.maketables()

    wWorld,wRiver,wBank, ww, wb, wc, we, wg, wh, wj =101,102,103, 1,2,3,4,5,6,7
    uWorldBank,uRiver,uEarth =201,202,203
    mynet = searchnet('nn.db')
    print 'Przed:\n', mynet.getresult([wWorld, wBank], [uWorldBank, uRiver, uEarth])

    for i in range(9):
        mynet.trainquery([wWorld, wBank], [uWorldBank, uRiver, uEarth], uWorldBank)
        print mynet.getresult([wWorld, wBank], [uWorldBank, uRiver, uEarth], retcat=True)
    print '\n\nPo:\n', mynet.getresult([wWorld, wBank], [uWorldBank, uRiver, uEarth])

