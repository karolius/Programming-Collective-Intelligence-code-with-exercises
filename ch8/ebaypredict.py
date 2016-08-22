# __author__ = 'karolius'
# 2016-08-01    00:10
# -*- coding: utf-8 -*-

import httplib
from xml.dom.minidom import parse, parseString, Node

devKey = 'c148b830-c9de-4183-8b92-ec10dda4807c'
appKey = 'DominikJ-pricepre-SBX-613d8b9b0-180433dd'
certKey = 'SBX-13d8b9b0406b-66b6-49c7-84f5-c006'
userToken = 'AgAAAA**AQAAAA**aAAAAA**uXmeVw**nY+sHZ2PrBmdj6wVnY+sEZ2PrA2dj6wFk4GjCZmHoQ6dj6x9nY+seQ**' \
            '5OUDAA**AAMAAA**R/lwZ1B9IqrQJru0IY0wvnErLuwmpQ4N7CANjT2yFI0mxzSo0R0NnA+RZY7vY6ZZaR2kqoG9' \
            '0gMOc11t97+JT+9DlzV4zH+1A2dI+jMmGQi7Q3DuppW7DBNLSjTZtONf+Hw80gBegXMumNYyXjts+yclYH1gpcKL' \
            'rrI4OEpyam2wbd9UC82JwFlulFY3LIt/ZUmxZeNDEgLQV47KCH9QbiIaVywVtBCxpktb+dzqOqwGvnd1eIEN4Mvv' \
            'CvBEXEBCOoMuefvGr3i78qX1XqtajjBxXvecLgO4/xjyh5mPDORq1NJqfZGmqBe0c5Z9mNlQt6WvGJexM8e2eLIn' \
            'OLO80INP44cey/tzkb2G4tHYvFm/G1Z3IAlPW+x6p6UCCsmBu6EHqNNNW/TSqKrUfdU0Tik/BHlNz7vcF6z1vVcD' \
            'g9UqJ16oVHeIC9D/VTFfDxjxMvBA7zKKgb8TVADAr0UGp5fRxRhhv573ij81DbEvPTy7AX/uQkl7EUs/JCI39YYC' \
            'ZktBcP7NqMY0wEQOEezkFazohaYKK1LRsW+8TOxcRUckRta2KmP6rlA6Yk+7ftd9JG47RpOxzy7zQH0nJUgulNSJ' \
            'IRVuhPSSx+nAUTQPT/lQPCR/HwiCr5I2hlkKw835dSLPyC9XZ23ULCwKD2bdFo02ZZs1kIecH44TChESQGDrZSgM' \
            'GY9GXB0P+HAoPr75E3+AaykLcJWmeRbuXBb+Scpk6on7c9/hctQFzRkF0ag3awI8DcVHQ4loifTuqM/s'
serverUrl = 'api.ebay.com'


def getHeaders(apicall, siteID='0', requestVersion='915'):
    headers = {"X-EBAY-API-REQUEST-VERSION": requestVersion,
               "X-EBAY-API-DEV-NAME": devKey,
               "X-EBAY-API-APP-NAME": appKey,
               "X-EBAY-API-CERT-NAME": certKey,
               "X-EBAY-API-CALL-NAME": apicall,
               "X-EBAY-API-SITEID": siteID,
               "Content-Type": "text/xml"}
    return headers


def sendRequest(apicall, xmlparameters):
    connection = httplib.HTTPSConnection(serverUrl)
    connection.request("POST", '/ws/api.dll', xmlparameters, getHeaders(apicall))
    response = connection.getresponse()
    if response.status != 200:
        print "Error sending request:"+response.reason
    else:
        data = response.read()
        connection.close()
    return data


def getSingleValue(node, tag):
    nl = node.getElementsByTagName(tag)
    if len(nl) > 0:
        tagNode = nl[0]
        if tagNode.hasChildNodes():
            return tagNode.firstChild.nodeValue
    return '-1'


def doSearch(query, categoryID=Node, page=1):
    """
    :param query: Ciag znakow zawierajacy wyszukiwane pojecia. Uzycie tego parametru,
    jest jak wyszukiwanie na glownej stronie ebay
    :param categoryID: Okresla kategorie w ktorej chcemy szukac. Ebay ma bardzo duza
    herarchie kategorie, do ktore dostep mozna uzyskac przez GetCategories() [API]
    Par. moze byc uzyty sam lub z pierwszym par. (zapytaniem).
    :param page:
    :return: lista ID przedmiotow z ich cechami (cena, opis, itp.)
    """
    xml = "<?xml version='1.0' encoding='utf-8'?>"+ \
          "<GetSearchResultsRequest xmlns=\"urn:ebay:apis:eBLBaseComponents\">"+ \
          "<RequesterCredentials><eBayAuthToken>" + \
          userToken + \
          "</eBayAuthToken></RequesterCredentials>" + \
          "<Pagination>"+ \
          "<EntriesPerPage>200</EntriesPerPage>"+ \
          "<PageNumber>"+str(page)+"</PageNumber>"+ \
          "</Pagination>"+ \
          "<Query>" + query + "</Query>"
    if categoryID is not None:
        xml += "<CategoryID>"+str(categoryID)+"</CategoryID>"
    xml += "</GetSearchResultsRequest>"

    data = sendRequest('GetSearchResults', xml)
    response = parseString(data)
    itemNodes = response.getElementsByTagName('Item')
    results = []
    for item in itemNodes:
        itemId = getSingleValue(item, 'ItemID')
        itemTitle = getSingleValue(item, 'Title')
        itemPrice = getSingleValue(item, 'CurrentPrice')
        itemEnds = getSingleValue(item, 'EndTime')
        results.append((itemId, itemTitle, itemPrice, itemEnds))
    return results


def getCategory(query='', parentID=Node, siteID='0'):
    """
    :param query:
    :param parentID:
    :param siteID:
    :return: wszystkie kategorie zawierajace dane zapytanie z podana kategoria jako najwyzsza w hierarchii
    """
    lquery = query.lower()
    xml = "<?xml version='1.0' encoding='utf-8'?>"+ \
          "<GetCategoriesRequest xmlns=\"urn:ebay:apis:eBLBaseComponents\">"+ \
          "<RequesterCredentials><eBayAuthToken>" + \
          userToken + \
          "</eBayAuthToken></RequesterCredentials>"+ \
          "<DetailLevel>ReturnAll</DetailLevel>"+ \
          "<ViewAllNodes>true</ViewAllNodes>"+ \
          "<CategorySiteID>"+siteID+"</CategorySiteID>"
    if parentID is None:
        xml += "<LevelLimit>1</LevelLimit>"
    else:
        xml += "<CategoryParent>"+str(parentID)+"</CategoryParent>"
    xml += "</GetCategoriesRequest>"
    data = sendRequest('GetCategories', xml)
    categoryList = parseString(data)
    catNodes = categoryList.getElementsByTagName('Category')
    for node in catNodes:
        catid = getSingleValue(node, 'CategoryID')
        name = getSingleValue(node, 'CategoryName')
        if name.lower().find(lquery) != -1:
            print catid, name


def getItem(itemID):
    xml = "<?xml version='1.0' encoding='utf-8'?>"+ \
          "<GetItemRequest xmlns=\"urn:ebay:apis:eBLBaseComponents\">"+ \
          "<RequesterCredentials><eBayAuthToken>" + \
          userToken + \
          "</eBayAuthToken></RequesterCredentials>" + \
          "<ItemID>" + str(itemID) + "</ItemID>"+ \
          "<DetailLevel>ItemReturnAttributes</DetailLevel>"+ \
          "</GetItemRequest>"
    data = sendRequest('GetItem', xml)
    result = {}
    response = parseString(data)
    result['title'] = getSingleValue(response, 'Title')
    sellingStatusNode = response.getElementsByTagName('SellingStatus')[0]
    result['price'] = getSingleValue(sellingStatusNode, 'CurrentPrice')
    result['bids'] = getSingleValue(sellingStatusNode, 'BidCount')
    seller = response.getElementsByTagName('Seller')
    result['feedback'] = getSingleValue(seller[0], 'FeedbackScore')
    attributeSet = response.getElementsByTagName('Attribute')
    attributes = {}
    for att in attributeSet:
        attID = att.attributes.getNamedItem('attributeID').nodeValue
        attValue = getSingleValue(att, 'ValueLiteral')
        attributes[attID] = attValue
    result['attributes'] = attributes
    return result



if __name__ == '__main__':
    laptops = doSearch('laptop')
    print laptops[:10]