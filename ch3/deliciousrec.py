from pydelicious import *
from time import sleep
from random import randint
from recommendations import *
import pickle


def initializeUserDict(tag, count=15):
    user_dict = {}
    # get the top count' popular posts
    for p1 in get_popular(tag=tag)[0:count]:
        # find all users who posted this
        try:
            for p2 in get_urlposts(p1['href']):
                user = p2['user']
                user_dict[user] = {}
        except:
            pass
    return user_dict


def fillItems(user_dict):
    all_items = {}
    # Find links posted by all users
    for user in user_dict:
        for i in range(3):
            try:
                posts = get_userposts(user)
                break
            except:
                print "Failed user "+user+", retrying..."
                time.sleep(4)
        for post in posts:
            url = post['href']
            user_dict[user][url] = 1.0
            all_items[url] = 1

    # Fill in missing items with 0
    for ratings in user_dict.values():
        for item in all_items:
            if item not in ratings:
                ratings[item] = 0.0


# Exercises code -------------------------------------
def fillItemsTags(tags_dict):
    all_urls = {}
    # Rozszerz baze przez inne tagi
    old_tag_dict = tags_dict.keys()
    for tag in old_tag_dict:
        for k in range(3):
            try:
                for post in get_popular(tag=tag)[0:15]:
                    # find all urls whith this tag
                    for i in range(3):
                        try:
                            url = post['href']
                            for subpost in get_urlposts(url):
                                if not subpost['tags']:
                                    continue
                                elif subpost['tags'] in tags_dict:
                                    tags_dict[tag][url] = 1.0
                                else:
                                    for tag in subpost['tags'].split():
                                        if not tag:
                                            continue
                                        tags_dict[tag] = {}
                                        tags_dict[tag][url] = 1.0
                            all_urls[url] = 1
                            break
                        except:
                            pass
            except:
                print 'Failed on tag: ', tag
    # Uzupelnianie brakujacych linkow zerami
    for urls in tags_dict.values():
        for url in all_urls:
            if url not in urls:
                urls[url] = 0.0


def initializeTagsDict(initag, count=15):
    tags_dict = {}
    # Uzyskaj najczesciej wyswietlane posty z danym tagiem
    for post in get_popular(tag=initag)[0:count]:
        # Znajdz wszytkie top linki z tym tagiem
        try:
            for post2 in get_urlposts(post['href']):
                for tag in post2['tags'].split():
                    if not tag:
                        continue
                    tags_dict[tag] = {}
        except:
            pass
    return tags_dict


def createTagsDict(initag, nesting=2, saveAsMatrix=False, fileName='data.txt', fColName='col0'):
    tag_list = {initag: 1}
    ntag_list = {}
    atag_list = {initag: 1}

    tag_dict = {}
    all_urls = {}

    for i in range(nesting+1):
        print(atag_list)
        for tag in atag_list:
            print(tag)
            tag_dict[tag] = {}
            try:
                for item in get_popular(tag=tag):
                    item_url = item['href']
                    tag_dict[tag][item_url] = 1.0
                    all_urls[item_url] = 1
                    if i == nesting:
                        continue
                    try:
                        for url in get_urlposts(item_url):
                            for subtag in url['tags'].split():
                                if subtag and subtag not in tag_list and subtag not in ntag_list:
                                        ntag_list[subtag] = 1
                    except:
                        pass
            except:
                pass
        atag_list = ntag_list
        tag_list.update(atag_list)
        ntag_list = {}
    # Uzupelnianie brakujacych linkow zerami
    for tag in tag_dict.values():
        for url in all_urls:
            if url not in tag:
                tag[url] = 0.0

    if saveAsMatrix:
        createMatrixDateBase(tag_dict, outFile=fileName, firstColName=fColName)
    else:
        save_obj(tag_list, 'tags_list')
        save_obj(tag_dict, 'tags_dict')


def save_obj(obj, name):
    with open(name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)
    with open(name + '.txt', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)


def load_obj(name):
    with open(name + '.pkl', 'rb') as f:
        return pickle.load(f)


def createMatrixDateBase(wordlist, outFile='data.txt', firstColName='col0'):
    # Podpisanie wszystkich kolumn: Blog\tslowo0\tslowo1\t etc...
    out = file(outFile, 'w')
    out.write(firstColName)
    for word in wordlist:
        out.write('\t%s' % word)
    out.write('\n')

    # Wypisanie wszystkich blogow i wstawianie liczby slow w nim wyst.
    for (blog, wc) in wordcounts.items():
        if not blog:
            continue
        print firstColName,': ', blog
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


if __name__ == '__main__':

    createTagsDict('food', nesting=4)
    obj = load_obj('tags_dict', )
    '''
    for tag in obj:
        print('Url tags: ', tag)
        for url in obj[tag]:
            print(obj[tag][url], url)
    '''
    print(topMatches(obj, 'food'))
    # print getRecommendedItems(obj, itemsim, 'Toby')
    '''
    delusers = initializeUserDict('food')
    fillItems(delusers)

    tag = 'games'
    deltags = initializeTagsDict(tag)
    print deltags
    fillItemsTags(deltags)
    print deltags.keys()
    print "DLA:", tag
    print topMatches(deltags, tag, similarity=sim_distance)
    print getRecommendations(deltags, tag)[0:10]
    '''