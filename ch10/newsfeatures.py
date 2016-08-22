import feedparser
import re
import docclass
import clusters
import nmf
import nmf2
import optimization
from numpy import *
import time
splitter = re.compile('\\W*')


feedlist = ['http://feeds.reuters.com/reuters/UKTopNews',
            'http://feeds.reuters.com/reuters/UKdomesticNews',
            'http://feeds.reuters.com/reuters/UKWorldNews',
            'http://hosted2.ap.org/atom/APDEFAULT/3d281c11a96b4ad082fe88aa0db04305',
            'http://hosted2.ap.org/atom/APDEFAULT/386c25518f464186bf7a2ac026580ce7',
            'http://hosted2.ap.org/atom/APDEFAULT/cae69a7523db45408eeb2b3a98c0c9c5',
            'http://hosted2.ap.org/atom/APDEFAULT/89ae8247abe8493fae24405546e9a1aa',
            'http://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml',
            'http://rss.nytimes.com/services/xml/rss/nyt/World.xml',
            'http://news.google.com/?output=rss',
            'http://www.salon.com/feed/',
            'http://www.foxnews.com/xmlfeed/rss/0,4313,0,00.rss',
            'http://feeds.foxnews.com/foxnews/national?format=xml',
            'http://feeds.foxnews.com/foxnews/world?format=xml',
            'http://feeds.foxnews.com/foxnews/politics?format=xml',
            'http://rss.cnn.com/rss/edition.rss',
            'http://rss.cnn.com/rss/edition_world.rss',
            'http://rss.cnn.com/rss/edition_us.rss']


def stripHTML(h):
    p = ''
    s = 0
    for c in h:
        if c == '<':
            s = 1
        elif c == '>':
            s = 0
            p += ' '
        elif s == 0:
            p += c
    return p


def separatewords(text):
    return [s.lower() for s in splitter.split(text) if len(s) > 3]


def getarticlewords():
    allwords = {}
    articlewords = []
    articletitles = []
    ec = 0
    # Loop over every feed
    for feed in feedlist:
        f = feedparser.parse(feed)

        # Loop over every article
        for e in f.entries:
            # Ignore identical articles
            if e.title in articletitles:
                continue
            # Extract the words
            txt = e.title.encode('utf8')
            try:
                txt += stripHTML(e.description.encode('utf8'))
            except AttributeError:
                # print("Nie ma descr: ", feed)
                pass
            words = separatewords(txt)
            articlewords.append({})
            articletitles.append(e.title)

            # Increase the counts for this word in allwords and in articlewords
            for word in words:
                allwords[word] = allwords.setdefault(word, 0) + 1
                articlewords[ec][word] = articlewords[ec].setdefault(word, 0) + 1
            ec += 1
    return allwords, articlewords, articletitles


def makematrix(allw, articlew):
    wordvec = []

    # Only take words that are common but now too common
    for w, c, in allw.items():
        if 3 < c < len(articlew)*0.6:
            wordvec.append(w)
    # Create the word matrix
    l1 = [[(word in f and f[word] or 0) for word in wordvec] for f in articlew]
    return l1, wordvec


def wordmatrixfeatures(x):
    return [wordvec[w] for w in range(len(x)) if x[w] > 0]


def showfeatures(w, h, titles, wordvec, out='features.txt'):
    outfile = file(out, 'w')
    pc, wc, = shape(h)
    toppatterns = [[] for i in range(len(titles))]
    patternnames = []
    # Loop over all the features
    for i in range(pc):
        slist = []
        # Create a list of words and their weights
        for j in range(wc):
            slist.append((h[i, j], wordvec[j]))
        # Reverse sort the word list
        slist.sort()
        slist.reverse()

        # Print the first six elements
        n = [s[1] for s in slist[:6]]
        outfile.write(str(n)+'\n')
        patternnames.append(n)

        # Create a list of articles for this feature
        flist = []
        for j in range(len(titles)):
            # Add the article with its weight
            flist.append((w[j, i], titles[j]))
            toppatterns[j].append((w[j, i], i, titles[j]))

        # Reverse sort the list
        flist.sort()
        flist.reverse()

        # Show the top 3 articles
        for f in flist[:3]:
            outfile.write(str(f)+'\n')
    outfile.close()
    # Return the pattern names for later use
    return toppatterns, patternnames


def showarticles(titles, toppatterns, patternnames, out='articles.txt'):
    outfile=file(out, 'w')

    # Loop over all the articles
    for j in range(len(titles)):
        outfile.write(titles[j].encode('utf8')+'\n')

        # Get the top featues for this article and
        # reverse sort them
        toppatterns[j].sort()
        toppatterns[j].reverse()

        # Print the top three patterns
        for i in range(3):
            toppat = toppatterns[j][i]
            outfile.write(str(toppat[0]) + ' ' +
                          str(patternnames[toppat[1]]) + '\n')
        outfile.write('n')
    outfile.close()


def createcostfunction(data, alg=nmf2.factorize, iter=10):
    """
    :param data: matrix()
    :param alg:
    :param iter:
    :return: cost function as object
    """
    def costf(par):
        w, h = alg(data, pc=par[0], maxiter=iter)
        return nmf.difcost(data, w*h)
    return costf


if __name__ == '__main__':
    # Converting to a Matrix
    allw, artw, artt = getarticlewords()
    wordmatrix, wordvec = makematrix(allw, artw)

    '''
    print 'wordvec[:10]: ', wordvec[:10]
    print '\nartt[1]: ', artt[1]
    print '\nwordmatrix[1][:10]: ', wordmatrix[1][:10]


    # Bayesian Classification
    wordmatrixfeatures(wordmatrix[0])
    classifier = docclass.naivebayes(wordmatrixfeatures)
    classifier.setdb('newstest.db')
    print artt[0]
    print artt[1]
    print artt[2]


    # Train this as an '(some meaning word)' story
    classifier.train(wordmatrix[0], 'bank')
    classifier.train(wordmatrix[1], 'terrorism')
    classifier.train(wordmatrix[2], 'work')


    # Clustering + additional word clustering
    artmatrix = clusters.rotatematrix(wordmatrix)

    clust = clusters.hcluster(wordmatrix)
    rotclust = clusters.hcluster(artmatrix)

    clusters.drawdendrogram(clust, artt, jpeg='news.jpg')
    clusters.drawdendrogram(rotclust, wordvec, jpeg='newswords.jpg')


    # Factorize articles matrix
    v = matrix(wordmatrix)
    weights, feat = nmf.factorize(v, pc=20, iter=50)

    topp, pn = showfeatures(weights, feat, artt, wordvec)
    showarticles(artt, topp, pn)


    # K-Means Clustering (Ex 2)
    kclust = clusters.kcluster(wordmatrix, k=20)
    clusters.kclustresultsave(kclust, artt)


    # Ex 3
    v = matrix(wordmatrix)
    difcostf = createcostfunction(v)
    k = optimization.annealingoptimize([(12, 40)], difcostf, T=10000.0, cool=0.96, step=1, samples=3)[0]
    print 'K=', k  # For me it was 32
    w, h = nmf.factorize(v, k)
    print 'Cost fot this k: ', nmf.difcost(v, w*h)


    # Comparision of alg example from book vs more sophisticated but faster and more precise
    v = matrix(wordmatrix)

    start = time.time()
    weights, feat = nmf2.factorize(v, pc=20, maxiter=10)
    print "Spec nmf time {:f}  with cost {:f}".format(time.time()-start, nmf.difcost(v, weights*feat))

    start = time.time()
    weights, feat = nmf.factorize(v, pc=20, iter=10)
    print "Norm nmf time {:f}  with cost {:f}".format(time.time()-start, nmf.difcost(v, weights*feat))
    '''