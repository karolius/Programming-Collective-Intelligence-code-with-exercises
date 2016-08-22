import feedparser
import re
import docclass
splitter = re.compile('\\W*')


# Uyzskaj nazwe pliku lub URL kanalu bloga i klasyfikuj wejscia
def read(feed, classifier):
    # Uzyskaj wejscia kanalu i przeprowadz po nich petle
    f = feedparser.parse(feed)

    for entry in f['entries']:
        print '\n----'
        # Zawartosc
        print 'Title:       '+entry['title'].encode('utf-8')
        print 'Publisher:       '+entry['publisher'].encode('utf-8')
        print '\n'+entry['summary'].encode('utf-8')

        # Zloz caly tekst jako jeden element do klasyfikatora
        # fulltext = '%s\n%s\n%s' % (entry['title'], entry['publisher'], entry['summary'])

        # Wyswietl najlepsz przypuszczenie co do aktualnej kategorii
        print 'Guess: '+str(classifier.classify(entry))  # poprzednio fulltext

        # Popros uzytkownika o podanie poprawnjej kategorii i trenuj na niej
        cl = raw_input('Enter categorz: ')
        classifier.train(entry, cl)  # poprzednio fulltext


def entryfeatures(entry, multi=2):
    multi -= 1
    f = {}

    # Wyodrebnij slowa tytulu i opatrz przypisem
    titlewords = [s.lower() for s in splitter.split(entry['title'])
                  if 2 < len(s) < 20]
    for w in titlewords:
        f['Title: '+w] = 1
    # Wyodrebnij slowa podsumowania
    summarywords = [s.lower() for s in splitter.split(entry['summary'])
                    if 2 < len(s) < 20]

    if len(entry['summary']) > 250:
        f['EXCLENGTH'] = 1

    # Zlicz slowa zaczynajace sie z duzej litery, podejrzanie dlugie
    uc = 0
    lw = 0
    wordsamout = len(summarywords)
    for i in range(wordsamout):
        w = summarywords[i]
        f[w] = 1
        if w.isupper():
            uc += 1

        if len(w) > 16:
            lw += 1

        # Multi slowa jako argumenty
        if i < len(summarywords) - multi:
            multiwords = ' '.join(summarywords[i:i+multi])
            f[multiwords] = 1

    # Zachowaj tworce i publikatora jako calosc
    f['Publisher:'+entry['publisher']] = 1

    # Slowo zlozone z duzych liter oznacza wykrzykiwanie
    # i oznacz dokumenty zawierajace znaczna czesc dlugich slow
    if float(uc)/wordsamout > 0.3:
        f['UPPERCASE'] = 1
    if float(lw)/wordsamout > 0.3:
        f['PREPOFLONGWORDS'] = 1

    return f


if __name__ == '__main__':
    '''
    # filtrowaniei kanalow blogow
    cl = docclass.fisherclassifier(docclass.getwords)
    cl.setdb('python_feed.db') # tylko dla sqllite
    read('python_search.xml', cl)
    '''

    # ulepszona detekcja argumentow
    cl = docclass.fisherclassifier(entryfeatures)
    cl.setdb('python_feed.db')
    read('python_search.xml', cl)

    '''
    mynet = searchnet('nn.db')
    mynet.maketables()
    read('python_search.xml', cl)
    cl =
    '''

