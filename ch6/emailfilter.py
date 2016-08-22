# encoding: utf-8
# poplib is a little obsolete protocol
import docclass
import imaplib
import email.header
import re

# regexp na zewnatrz bedzie kompilowany tylko raz, a nie przy kazdym uzyciu funkcji
tagre = re.compile(r'<[^>]+>')
splitter = re.compile('\\W*')
# ipre = re.compile(r'\b25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?\.25[0-5]|2[0-4][0-9]|[01]'
#                   r'?[0-9][0-9]?\.25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?\.25[0-5]|2[0-4]'
#                   r'[0-9]|[01]?[0-9][0-9]?\b')

ipre = re.compile(r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)?$ ')


def cleanhtml(raw_html):
    # Usuwa znaczniki html z tekstu, takze to co jest pomiedzy nimi i skrypty
    return tagre.sub('', raw_html)


def get_decoded_email_body(msg):
    """
    author: miohtama (GitHub) by ive modified it a little
    Decode email body.
    Detect character set if the header is not set.
    We try to get text/plain, but if there is not one then fallback to text/html.
    :param message_body: Raw 7-bit message body input e.g. from imaplib. Double encoded in quoted-printable and latin-1
    :return: Message body as unicode string
    """
    text = ""
    if msg.is_multipart():
        html = None
        for part in msg.get_payload():
            print "%s, %s" % (part.get_content_type(), part.get_content_charset())

            if part.get_content_charset() is None:
                # We cannot know the character set, so return decoded "something"
                text = part.get_payload(decode=True)
                continue

            charset = part.get_content_charset()

            if part.get_content_type() == 'text/plain':
                text = unicode(part.get_payload(decode=True), str(charset), "ignore").encode('utf8', 'replace')

            if part.get_content_type() == 'text/html':
                html = unicode(part.get_payload(decode=True), str(charset), "ignore").encode('utf8', 'replace')

        if text is not None:
            return text.strip()
        elif text is None:
            return ''
        else:
            return html.strip()
    elif msg is None:
        return ''
    else:
        # text = unicode(msg.get_payload(decode=True), msg.get_content_charset(), 'ignore').encode('utf8', 'replace')
        text = unicode(
            msg.get_payload(decode=True),
            msg.get_content_charset() if msg.get_content_charset() is not None else 'utf-8', 'replace')\
            .encode('utf8', 'replace')
    return text.strip()


def read(login, password, classifier, folder='inbox'):
    # Uzyskaj dostep do skrzynki i zapisz wiadomosci
    # Detekcja po ip jest troszke oszukana, bo nie pokazuje adresu wysylajacego,
    # nie wiem czy imap to umozliwia

    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login(login, password)
    mail.list()
    mail.select('inbox')

    # Uzyskanie wszystkich wiadomosci z maila, ale czasowo dobor pojedynczych lepiej pasuje do potrzeb
    # messages = [mail.fetch(i, '(RFC822)')[1][0][1] for i in mail.search(None, 'ALL')[1][0].split()]
    entry = {}
    _, maildata = mail.search(None, 'ALL')
    for num in maildata[0].split():
        _, messagedata = mail.fetch(num, '(RFC822)')
        emailmessage = email.message_from_string(messagedata[0][1])
        try:
            # Umiesc wybrane dane w slowniku dla klasyfikatora
            entry['From'] = unicode(email.header.make_header
                                    (email.header.decode_header(emailmessage['From'])))
            entry['Subject'] = unicode(email.header.make_header
                                       (email.header.decode_header(emailmessage['Subject'])))
            entry['Messagebody'] = get_decoded_email_body(emailmessage)
            entry['Ip'] = [w for w in emailmessage['Received'].split()][1][:-1]
        except UnicodeDecodeError:  # nie chcialo mi sie dalej brnac w durne zawilosci dekodowania
            continue
        # Wyswietl zawartosc maila
        print '\n\n----'
        print '\n'+entry['Messagebody']
        print '\nFrom:       '+entry['From']
        print '\nSender IP:       '+entry['Ip']
        print 'Subject:       '+entry['Subject']

        # Wyswietl najlepsze przypuszczenie co do aktualnej kategorii
        print 'Guess: '+str(classifier.classify(entry))  # poprzednio fulltext

        # Popros uzytkownika o podanie poprawnjej kategorii i trenuj na niej
        cl = raw_input('Enter category: ')
        classifier.train(entry, cl)

    mail.logout()


def entryfeatures(entry):
    f = {}

    # Wyodrebnij slowa
    fromwords = [s.lower() for s in splitter.split(entry['From']) if 2 < len(s) < 20]
    for w in fromwords:
        f['From: '+w] = 1
    subjectwords = [s.lower() for s in splitter.split(entry['Subject']) if 2 < len(s) < 20]
    for w in subjectwords:
        f['Subject: '+w] = 1

    f['Ip'+entry['Ip']] = 1
    messagebodywords = [s.lower() for s in splitter.split(entry['Messagebody']) if 2 < len(s) < 20]

    # Zlicz slowa zaczynajace sie z duzej litery
    uc = 0
    for i in range(len(messagebodywords)):
        w = messagebodywords[i]
        f[w] = 1
        if w.isupper():
            uc += 1

        # Uzyskaj pary slow w podsomuwaniu jako argumenty
        if i < len(messagebodywords) - 1:
            twowords = ' '.join(messagebodywords[i:i+1])
            f[twowords] = 1

    # Slowo zlozone z duzych liter oznacza wykrzyczenie
    if float(uc)/len(messagebodywords) > 0.3:
        f['UPPERCASE'] = 1

    return f


if __name__ == '__main__':
    # klasyfikator wiadomosci email
    cl = docclass.fisherclassifier(entryfeatures)
    cl.setdb('mail_feed.db')
    read('encore127@gmail.com', 'przykromitoniehasloD', cl)
    print 'Przed proba zalogowania wlacz w ustawieniach skrzynki dostep\n' \
          'do maila dla niezabezpieczonych aplikacji (wiecej info w linku\n' \
          'https://support.google.com/accounts/answer/6010255 ).'
    while 1:
        login = raw_input('Wpisz login do emaila: ')
        password = raw_input('Wpisz haslo do emaila: ')
        try:
            read(login, password, cl)
            break
        except:
            print 'Podales zly login, haslo, lub nie zmieniles ustawien.'