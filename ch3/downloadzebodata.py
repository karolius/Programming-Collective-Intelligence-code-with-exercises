from bs4 import BeautifulSoup
import urllib2
import re


'''
Struktura strony Zebo jest stosunkowo zlozona ale latwo jest okreslic ktore elementy
strony sa listami elementow, poniewaz maja typ klasy 'bgverdanasmall'.
'''
chare = re.compile(r'[!-\.&]')
itemowners = {}
currentuser = 0
# Slowa do usuniecia
dropword = ['a', 'new', 'some', 'more', 'my', 'own', 'the', 'many', 'other', 'another']

for i in range(1, 51):
    # URL dla pożądanych wyszukiwan stron
    c = urllib2.urlopen(
        'http://member.zebo.com/Main?event_key=USERSEARCH&wiowiw=wiw&keyword=car&page=%d' % i)
    soup = BeautifulSoup(c.read())
    for td in soup('td'):
        # Znajdz komorki tabeli
        if 'class' in dict(td.attrs) and td['class'] == 'bgverdanasmall':
            items = [re.sub(chare, '', a.contents[0].lower()).strip() for a in td('a')]
            for item in items:
                # Usun dodatkowe slowa
                txt = ' '.join([t for t in item.split(' ') if t not in dropword])
                if len(txt) < 2:
                    continue
                itemowners.setdefault(txt, {})
                itemowners[txt][currentuser] = 1
            currentuser += 1
'''
Dalsza czesc tworzy liste elementow, ktore sa pozadane przez wiecej niz 5 osob, natepnie tworzy
macierz z anonim. uzytkownikami jako kol. i elem. jako wier. Macierz zapisuje do pliku.
'''
out = file('zebo.txt', 'w')
out.write('Item')
for user in range(0, currentuser):
    out.write('\tU%d' % user)
out.write('\n')
for item, owners in itemowners.items():
    if len(owners) > 10:
        out.write(item)
        for user in range(0, currentuser):
            if user in owners:
                out.write('\t1')
            else:
                out.write('\t0')
        out.write('\n')