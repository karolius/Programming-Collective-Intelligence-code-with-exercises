import feedparser
import re
import os
import clusters
import pydelicious


def getwordcounts(url):
    """
    Zwraca tytul i slownik naliczenia slow w kanale RSS
    przez analize skladniowo kanalu
    """
    d = feedparser.parse(url)
    wc = {}
    # Petla po wszystkich wejsciach
    for e in d.entries:
        if 'summary' in e:
            summary = e.summary
        else:
            summary = e.description
        # Wyekstrachuj liste slow
        words = getwords(e.title + ' ' + summary)
        for word in words:
            wc.setdefault(word, 0)
            wc[word] += 1
    return [d.feed.title], [wc]


def getwords(html):
    """
    Usuwa wszysktie tagi HTML
    Rozdziel slowa przez wszystkie znaki nie alfa
    Zwraca przekonwertowane do malych liter (slowa).
    """
    txt = re.compile(r'<[^>]+>').sub('', html)
    words = re.compile(r'[^A-Z^a-z]+').split(txt)
    return [word.lower() for word in words if word != '']


def collectblogdatebase(filename='blogdata.txt', feedlist='feedlist.txt', getitemscounts=getwordcounts):
    # Colecting datebase in terms of list arguments (work for ex2 and examples from book)
    try:
        if os.stat(filename).st_size == 0:
            print 'Datebase is already created.'
    except:
        print 'Collecting data...'
        apcount = {}
        wordcounts = {}

        feedlist = [l for l in file(feedlist)]

        for feedurl in feedlist:
            try:
                titles, wcs = getitemscounts(feedurl)
                for i in range(len(titles)):
                    wordcounts[titles[i]] = wcs[i]
                for wc in wcs:
                    for (word, count) in wc.items():
                        apcount.setdefault(word, 0)
                        if count > 1:
                            apcount[word] += 1
            except:
                print 'Failed to parse feed %s' % feedurl

        # Walidacja slow w kontekscie ich frekwencji w tekscie
        wordlist = []
        for w, bc in apcount.items():
            frac = float(bc) / len(feedlist)
            if 0.1 < frac < 0.5:
                wordlist.append(w)

        # Podpisanie wszystkich kolumn: Blog\tslowo0\tslowo1\t etc...
        out = file(filename, 'w')
        out.write(filename[:4])
        for word in wordlist:
            out.write('\t%s' % word)
        out.write('\n')

        # Wypisanie wszystkich blogow i wstawianie liczby slow w nim wyst.
        i = 1
        for blog, wc in wordcounts.items():
            if i:
                i -= 1
            if not blog:
                continue
            print filename[:4], ': ', blog
            try:
                out.write(blog)
                for word in wordlist:
                    if word in wc:
                        out.write('\t%d' % wc[word])
                    else:
                        # Jesli slowa nie bylo w slowniku zliczajacym->wstaw 0
                        out.write('\t0')
                out.write('\n')
            except:
                print '******Failed to write blog %s' % blog
        out.close()


# --------- Ex 1 -------------------------------------------------------
def getUserCounts(tag, lastNesting=False):
    """
    Zwraca tytul i slownik naliczenia uzytkownikow pod tagiem
    oraz slownik dla wyszukan pod nowymi tagami.
    """
    # Sprawdz czy bez lastNesting (jeszcze bool w wywol fun. w collectDatebase) jest szybciej.
    uc, tagDict = {}, {}
    # Petla po wszystkich wejsciach
    for p1 in pydelicious.get_tagposts(tag):
        user = p1['user']
        if user:
            uc.setdefault(user, 0)
            uc[user] += 1
            # tagDict = {tagDict.setdefault(p2['tags'].replace (' ', '_'), 1) for p2 in pydelicious.get_userposts(p1['user']) if p2['tags']}
            if lastNesting:
                break
            for p2 in pydelicious.get_userposts(p1['user']):
                if p2['tags']:
                    tagDict.setdefault(p2['tags'].replace(' ', '_'), 1)
    return (user, uc), tagDict


def collectDatebase(iniFeedList, nesting=2, fileName='data.txt'):
    userCounts, apcount = {}, {}
    feedList = []
    for i in range(nesting):
        nextFeedDict = {}
        feedList = iniFeedList
        for tag in iniFeedList:
            (tag, uc), newFeedDict = getUserCounts(tag, lastNesting=bool((i+1)==nesting))
            userCounts[tag] = uc
            for (user, count) in uc.items():
                    apcount.setdefault(user, 0)
                    if count > 1:
                        apcount[user] += 1
            nextFeedDict.update(newFeedDict) # dopisuj po kazdym obrocie
        iniFeedList = [t for t in nextFeedDict if t not in feedList]
        if not iniFeedList:
            print "Crawling finished before the limit- no more items to gather."
            break

   # Walidacja uzytkownikow w kontekscie ich frekwencji w tekscie
    usersList = []
    for (u, bc) in apcount.items():
        frac = float(bc)/len(feedList)
        if 0.1 < frac < 0.9: # pomanipuluj
            usersList.append(u)
    # Podpisanie wszystkich kolumn: Blog\tslowo0\tslowo1\t etc...
    out = file(fileName, 'w')
    out.write(fileName[:4])
    for user in usersList:
        out.write('\t%s' % user)
    out.write('\n')

    # Wypisanie wszystkich blogow i wstawianie liczby slow w nim wyst.
    i = 1
    for tag, uc in userCounts.items():
        if i:
            i -= 1
        if not tag:
            continue
        try:
            out.write(tag)
            for user in usersList:
                if user in uc:
                    out.write('\t%d' % uc[user])
                else:
                    # Jesli slowa nie bylo w slowniku zliczajacym->wstaw 0
                    out.write('\t0')
            out.write('\n')
        except:
            print '***Failed to write tag %s' % tag
    file.close()


# --------- Ex 2 -------------------------------------------------------
def getwordcountsentries(url):
    """
    Zwraca liste tytulow i liste slownikow naliczenia slow w kanale
    RSS przez analize skladniowo kanalu z wyodrebnieniem wejsc.
    """
    d = feedparser.parse(url)
    wcl, tittlelist = [], []
    # Petla po wszystkich wejsciach
    for e in d.entries:
        if 'summary' in e:
            summary = e.summary
        else:
            summary = e.description
        # Wyekstrachuj liste slow
        words = getwords(e.title + ' ' + summary)
        wc = {}
        for word in words:
            wc.setdefault(word, 0)
            wc[word] += 1
        tittlelist.append(d.feed.title + "_" + e.title)
        wcl.append(wc)

    return tittlelist, wcl


# --------- Ex 6 -------------------------------------------------------
def varyclustnumbofkmean(rate=5):
    data = clusters.readfile('blogdata.txt')[2]
    for i in range(10, 30):
        n = rate*i
        kclust, dist = clusters.kcluster(data, k=n, rettotaldist=True)
        print('For k = ', n, ' clusters dist = ', dist)


if __name__ == '__main__':
    '''
    collectblogdatebase()

    # Hierarchical clustering
    blognames, words, data = clusters.readfile('blogdata.txt')
    clust = clusters.hcluster(data)
    clusters.printclust(clust, labels=blognames)


    # Drawing the Dendrogram
    clusters.drawdendrogram(clust, blognames, jpeg='blogclust.jpg')


    # Column Clustering
    rdata = clusters.rotatematrix(data)
    wordclust = clusters.hcluster(rdata)
    clusters.drawdendrogram(wordclust, labels=words, jpeg='wordclust.jpg')


    # K-Means Clustering
    blognames, words, data = clusters.readfile('blogdata.txt')
    kclust=clusters.kcluster(data,k=10)
    #Iteration 0 ...
    [rownames[r] for r in k[0]]
    #['The Viral Garden', 'Copyblogger', 'Creating Passionate Users',
    #'Oilman', 'ProBlogger Blog Tips', "Seth's Blog"]


    # Zebo
    wants, people, data = clusters.readfile('zebo.txt')
    clust = clusters.hcluster(data, distance=clusters.tanamoto)
    clusters.drawdendrogram(clust, wants, jpeg='zeboclust_tanimoto.jpg')


    # Viewing Data in Two Dimensions (scaling)
    blognames, word, data = clusters.readfile('blogdata.txt')
    coords = clusters.scaledown(data, rate=0.01)
    clusters.draw2d(coords, blognames, jpeg='blogs2d.jpg')


    #--------- EXE 1 -------------------------------------------------------
    saveFile = 'tagsdata.txt'
    inifeedlist = ['seo', 'shopping', 'programming', 'food']

    collectdatebase(inifeedlist, filename=saveFile)
    tagNames, urls, tagData = clusters.readfile(saveFile)

    tagClust = clusters.hcluster(tagData)
    clusters.drawdendrogram(tagData, tagNames, jpeg='tagClust.jpg')


    #--------- EXE 2 -------------------------------------------------------
    entriesdatafile = 'entriesblogdata.txt'
    collectblogdatebase(filename=entriesdatafile, getitemscounts=getwordcountsentries)
    # Hierarchical clustering
    blognames, words, data = clusters.readfile(entriesdatafile)
    clust = clusters.hcluster(data)

    # Drawing the Dendrogram
    clusters.drawdendrogram(clust, blognames, jpeg='entriesblogclust.jpg')


    #--------- EXE 3 -------------------------------------------------------
    collectblogdatebase()

    # Hierarchical clustering
    blognames, words, data = clusters.readfile('blogdata.txt')
    clust = clusters.hcluster(data, distance=clusters.euclidean)

    # Drawing the Dendrogram
    clusters.drawdendrogram(clust, blognames, jpeg='blogclust_euclidean.jpg')


    #--------- EXE 4 -------------------------------------------------------
    # K-Means Clustering, zebo ??
    wants, people, data = clusters.readfile('zebo.txt')
    clust = clusters.hcluster(data, distance=clusters.manhattan)
    clusters.drawdendrogram(clust, wants, jpeg='zeboclust_manhattan.jpg')


    #--------- EXE 5-6 -----------------------------------------------------
    varyclustnumbofkmean()


    #--------- EXE 7 -------------------------------------------------------
    dimensions = 1
    blognames, word, data = clusters.readfile('blogdata.txt')
    coords = clusters.scaledown(data, rate=0.01, dim=dimensions)
    clusters.draw2d(coords, blognames, jpeg='blogs1d.jpg', dim=dimensions)
    '''

    # K-Means Clustering
    blognames, words, data = clusters.readfile('blogdata.txt')
    kclust = clusters.kcluster(data, k=10)
    clusters.kclustresultsave(data, blognames)  # i hope it works
    # print kclust