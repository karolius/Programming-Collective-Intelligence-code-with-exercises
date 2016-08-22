import time
import urllib2
import xml.dom.minidom

kayakkey = 'Klucz'


def getkayaksession():
    # Tworzy URL do rozpoczecia sesji
    url='http://www.kayak.com/k/ident/apisession?token=%s&version=1' % kayakkey

    # Analizuj skladniowo rezultat XML
    doc = xml.dom.minidom.parseString(urllib2.urlopen(url).read())

    # Znaidz <sid>xxxxxxxx</sid>
    sid = doc.getElementsByTagName('sid')[0].firstChild.data
    return sid


def flightsearch(sid, origin, destination, depart_date):
    # Zbuduj URL do poszukiwan
    url='http://www.kayak.com/s/apisearch?basicmode=true&oneway=y&origin=%s' % origin
    url+='&destination=%s&depart_date=%s' % (destination,depart_date)
    url+='&return_date=none&depart_time=a&return_time=a'
    url+='&travelers=1&cabin=e&action=doFlights&apimode=1'
    url+='&_sid_=%s&version=1' % (sid)

    # Uzyskaj XML
    doc = xml.dom.minidom.parseString(urllib2.urlopen(url).read())

    # Wyodrebnij ID wyszukiwania
    searchid = doc.getElementsByTagName('searchid')[0].firstChild.data

    return searchid


def flightsearchresult(sid, searchid):
    """
    Funkcja zada wynikow dopoki sa. W XMLu jest tag "morepending" majacy slowo "true"
    dopoki wyszukiwanie nie jest zakonczone.
    :param sid:
    :param searchid:
    :return:
    """
    # Usun poprzedzajace $,. i zamien liczby na format float
    def parseprice(p):
        return float(p[1:].replace(',',''))

    # Petla pytajaca cyklicznie
    while 1:
        time.sleep(2)
        # Tworzy URL do pytania cyklinego
        url='http://www.kayak.com/s/basic/flight?'
        url+='searchid=%s&c=5&apimode=1&_sid_=%s&version=1' % (searchid,sid)
        doc=xml.dom.minidom.parseString(urllib2.urlopen(url).read())
        # Szukaj wiecej oczekujacych tagow i czekaj dopoki to nie jest prawda
        morepending = doc.getElementsByTagName('morepending')[0].firstChild
        if morepending == None or morepending.data == 'false': break

    # Teraz pobierz kompletna liste
    url='http://www.kayak.com/s/basic/flight?'
    url+='searchid=%s&c=999&apimode=1&_sid_=%s&version=1' % (searchid,sid)
    doc = xml.dom.minidom.parseString(urllib2.urlopen(url).read())

    # Uzyskaj rowne elementy jako liste
    prices = doc.getElementsByTagName('price')
    departures = doc.getElementsByTagName('depart')
    arrivals = doc.getElementsByTagName('arrive')

    # Zzipuj je razem
    return zip([p.firstChid.data.split(' ')[1] for p in departures],
               [p.firstChid.data.split(' ')[1] for p in arrivals],
               [parseprice(p.firstChid.data) for p in prices]) # konwert. cene do float(parseprice(..)


def createschedule(people, dest, dep, ret):
    # Uzyskaj id sesji dla tych wyszukan
    sid = getkayaksession()
    flights = {}

    for p in people:
        name, origin = p
        # Lot wychodzacy
        searchid = flightsearch(sid, origin, dest, ret)
        flights[(origin, dest)] = flightsearchresult(sid, searchid)

        # Loty powrotne
        searchid = flightsearch(sid, dest, origin, ret)
        flights[(dest, origin)] = flightsearchresult(sid, searchid)
    return flights
