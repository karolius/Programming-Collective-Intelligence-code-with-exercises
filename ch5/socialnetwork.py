import math
import optimization
import time
from PIL import Image, ImageDraw

people = ['Charlie','Augustus','Veruca','Violet','Mike','Joe','Willy','Miranda']

links = [('Augustus', 'Willy'),
            ('Mike', 'Joe'),
            ('Miranda', 'Mike'),
            ('Violet', 'Augustus'),
            ('Miranda', 'Willy'),
            ('Charlie', 'Mike'),
            ('Veruca', 'Joe'),
            ('Miranda', 'Augustus'),
            ('Willy', 'Augustus'),
            ('Joe', 'Charlie'),
            ('Veruca', 'Augustus'),
            ('Miranda', 'Joe')]


def crosscount(v):
    """
    Fun przechodzi po kazdej parze linii uzywajac aktualnych koordynatow ich
    koncow, by okreslic czy sie przecinaja. Jesli tak- fun dodaje 1 do calkowitego
    wyniku
    :param v:
    :return:
    """
    # Zamien liste liczb na slownik: osoba:(x, y)
    loc = {p:(v[2*i],v[2*i+1]) for i, p in enumerate(people)}
    total = 0

    # Petla po kazdej parze polaczen
    for i in range(len(links)):
        for j in range(i+1, len(links)):
            # Uzyskaj lokacje
            (x1,y1),(x2,y2) = loc[links[i][0]],loc[links[i][1]]
            (x3,y3),(x4,y4) = loc[links[j][0]],loc[links[j][1]]
            den = (y4-y3)*(x2-x1)-(x4-x3)*(y2-y1)

            # den == 0 -> linie sa rownolegle
            if den == 0: continue

            # Wpp ua i ub sa wpolzednymi przeciecia linni
            ua=((x4-x3)*(y1-y3)-(y4-y3)*(x1-x3))/den
            ub=((x2-x1)*(y1-y3)-(y2-y1)*(x1-x3))/den

            # Jesli jest pomiedzy 0-1 dla obu linni-> przecin. sie
            if ua>0 and ua<1 and ub>0 and ub<1: total +=1

        for i in range(len(people)):
            for j in range(i+1, len(people)):
                # Uzyskaj lokacje dwoch wezlow
                (x1,y1), (x2,y2) = loc[people[i]], loc[people[j]]

                # Znajdz odleglosc pomiedzy nimi
                dist = math.sqrt(math.pow(x1-x2,2)+math.pow(y1-y2,2))
                # Karaj kazdy wezel blizszy niz 50px
                if dist < 50: total += (1.0-(dist/50))
    return total


def drawnetwork(sol, imgname='socialnetwork.jpg'):
    """
    Tworzy obrazek, polaczenia miedzy ludzmi i wezly miedzy nimi
    na koncu imiona aby linie ich nie zakrywaly
    :param sol: koordynaty poszczegolnych osob zapisane na jednej liscie
    :return:
    """
    # Tworzy obraz
    img = Image.new('RGB', (400, 400), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Tworzy slownik pozycji
    pos = {p: (sol[2*i], sol[2*i+1]) for i, p in enumerate(people)}

    # Rysuj polaczenia
    for (a, b) in links:
        draw.line((pos[a], pos[b]), fill=(255, 0, 0))

    # Rysuj ludzi
    for n, p in pos.items():
        draw.text(p, n, (0, 0, 0))

    img.save(imgname, 'JPEG')


if __name__ == '__main__':
    domain = [(10, 380)]*(len(people)*2)
    sol = optimization.randomoptimize(domain, crosscount)
    print 'randomoptimize: ', crosscount(sol), '\nsol: ', sol
    # drawnetwork(sol)

    sol = optimization.annealingoptimize(domain, crosscount, step=50, cool=0.99)
    print 'annealingoptimize: ', crosscount(sol), '\nsol: ', sol
    drawnetwork(sol)