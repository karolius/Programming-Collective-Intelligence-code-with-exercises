import akismet

defaultkey = "b2a78beeceae"
pageurl = "http://yoururlhere.com"

defaultagent="Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.0.7) "
defaultagent+="Gecko/20060909 Firefox/47.0.1"


def isspam(comment, author, ipaddress, agent=defaultagent, apikey=defaultkey):
    try:
        valid = akismet.verify_key(apikey, pageurl)
        if valid:
            return akismet.comment_check(apikey, pageurl, ipaddress, agent,
                                         comment_content=comment, comment_author_email=author,
                                         comment_type="comment")
        else:
            print 'Invalid key'
            return False
    except akismet.AkismetError, e:
        print e.response, e.statuscode
        return False


if __name__ == '__main__':
    msg = 'Make money fast! Online Casino!'
    print isspam(msg, 'spammer@spam.com', '127.0.0.1')