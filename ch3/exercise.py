import feedparser
import re
import os
import clusters
import pydelicious


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


# --------- Ex 1 -------------------------------------------------------
def collectDatebase(iniFeedList, hollow=2, fileName='data.txt'):
    userCounts, apcount = {}, {}
    feedList = []
    for i in range(hollow):
        nextFeedDict = {}
        feedList = iniFeedList
        for tag in iniFeedList:
            (tag, uc), newFeedDict = getUserCounts(tag, lastNesting=bool((i+1)==hollow))
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
        if frac > 0.1 and frac < 0.9: # pomanipuluj
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


if __name__ == '__main__':
    #--------- ZAD 1 -------------------------------------------------------
    saveFile = 'tagsdata.txt'
    iniFeedList = ['seo', 'shopping', 'programming', 'food']

    collectDatebase(iniFeedList, fileName=saveFile)
    tagNames, urls, tagData = clusters.readfile(saveFile)

    tagClust = clusters.hcluster(tagData)
    clusters.drawdendrogram(tagData, tagNames, jpeg='tagClust.jpg')
     # pousuwaj zbeden gowna z delicious w ch3, moze i delicious ? Spr.

    #--------- ZAD 2 -------------------------------------------------------