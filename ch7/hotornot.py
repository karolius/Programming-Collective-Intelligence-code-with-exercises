import urllib2
import xml.dom.minidom
import treepredict
api_key = "XXXXXXXX"
stateregions={'New England':['ct','mn','ma','nh','ri','vt'],
              'Mid Atlantic':['de','md','nj','ny','pa'],
              'South':['al','ak','fl','ga','ky','la','ms','mo',
                       'nc','sc','tn','va','wv'],
              'Midwest':['il','in','ia','ks','mi','ne','nd','oh','sd','wi'],
              'West':['ak','ca','co','hi','id','mt','nv','or','ut','wa','wy']}


def getrandomratings(c):
    """
    :param c:
    :return: wynik jako liste
    """
    # Skleij URL dla getRandomProfile
    url="http://services.hotornot.com/rest/?app_key=%s" % api_key
    url+="&method=Rate.getRandomProfile&retrieve_num=%d" % c
    url+="&get_rate_info=true&meet_users_only=true"

    f1 = urllib2.urlopen(url).read()
    doc = xml.dom.minidom.parseString(f1)

    emids = doc.getElementsByTagName('emid')
    ratings = doc.getElementsByTagName('rating')

    # Zloz emid i rating jako list
    return [(e.firstChild.data, r.firstChild.data)
            for e, r in zip(emids, ratings) if r.firstChild is not None]


def getpeopledata(rating):
    result = []
    for emid, rating in ratings:
        # URL dla MeetMe.getProfile
        url = "http://services.hotornot.com/rest/?app_key=%s" % api_key
        url += "&method=MeetMe.getProfile&emid=%s&get_keywords=true" % emid

        # Uzyskaj informacje o tej osobie
        try:
            rating = int(float(rating)+0.5)
            doc2 = xml.dom.minidom.parseString(urllib2.urlopen(url).read())
            gender = doc2.getElementsByTagName('gender')[0].firstChild.data
            age = doc2.getElementsByTagName('age')[0].firstChild.data
            loc = doc2.getElementsByTagName('location')[0].firstChild.data[0:2]

            # Konwertuj stan na region
            for r, s in stateregions.items():
                if loc in s:
                    region = r
            if region is not None:
                result.append((gender, int(age), region, rating))
        except:
            pass
    return result


if __name__ == '__main__':
    l1 = getrandomratings(500)
    print(len(l1))
    pdata = getpeopledata(l1)
    print(pdata[0])
    hottree=treepredict.buildtree(pdata,scoref=treepredict.variance)
    treepredict.prune(hottree, 0.5)
    treepredict.drawtree(hottree, 'hottree.jpg')
    # south = treepredict2.mdclassify((None,None,'South'),hottree)
    # midat = treepredict2.mdclassify((None,None,'Mid Atlantic'),hottree)