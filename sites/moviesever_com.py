# -*- coding: utf-8 -*-
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser
from resources.lib import logger
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.pluginHandler import cPluginHandler
import re

SITE_IDENTIFIER = 'moviesever_com'
SITE_NAME = 'MoviesEver'
SITE_ICON = 'moviesever.png'

URL_MAIN = 'http://moviesever.com/'

SERIESEVER_IDENTIFIER = 'seriesever_net'

def load():
    oParams = ParameterHandler()

    oGui = cGui()
    oGui.addFolder(cGuiElement('Neue Filme', SITE_IDENTIFIER, 'showNewMovies'), oParams)
    oGui.addFolder(cGuiElement('Kategorien', SITE_IDENTIFIER, 'showGenresMenu'), oParams)
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'), oParams)
    oGui.setEndOfDirectory()


def __isSeriesEverAvaiable():
    cph = cPluginHandler()

    for site in cph.getAvailablePlugins():
        if site['id'] == SERIESEVER_IDENTIFIER:
            return True

    return False

def __getHtmlContent(sUrl=None):
    oParams = ParameterHandler()
    # Test if a url is available and set it
    if sUrl is None and not oParams.exist('sUrl'):
        logger.error("There is no url we can request.")
        return False
    else:
        if sUrl is None:
            sUrl = oParams.getValue('sUrl')
    # Make the request
    oRequest = cRequestHandler(sUrl)
    oRequest.addHeaderEntry('Referer', URL_MAIN)
    oRequest.addHeaderEntry('Accept', '*/*')

    return oRequest.request()


def showNewMovies():
    showMovies(URL_MAIN, False)


def showSearch():
    logger.info('load showSearch')
    oGui = cGui()

    sSearchText = oGui.showKeyBoard()
    if (sSearchText != False and sSearchText != ''):
        showMovies(URL_MAIN + '?s=' + sSearchText, True)
    else:
        return
    oGui.setEndOfDirectory()


def showGenresMenu():
    logger.info('load showGenresMenu')
    oParams = ParameterHandler()
    sPattern = '<li class="cat-item.*?href="(.*?)"\s*?>(.*?)<'

    # request
    sHtmlContent = __getHtmlContent(URL_MAIN)
    # parse content
    oParser = cParser()
    aResult = oParser.parse(sHtmlContent, sPattern)

    oGui = cGui()

    if aResult[0]:
        for link, title in aResult[1]:
            guiElement = cGuiElement(title, SITE_IDENTIFIER, 'showMovies')
            guiElement.setMediaType('fGenre')
            oParams.addParams({'sUrl': link, 'bShowAllPages': True})
            oGui.addFolder(guiElement, oParams)

    oGui.setEndOfDirectory()

def showMovies(sUrl = False, bShowAllPages = False):
    logger.info('load showMovies')
    oParams = ParameterHandler()

    if not sUrl:
        sUrl = oParams.getValue('sUrl')

    if oParams.exist('bShowAllPages'):
        bShowAllPages = oParams.getValue('bShowAllPages')

    sPagePattern = '%spage/(.*?)/' % sUrl

    # request
    sHtmlContent = __getHtmlContent(sUrl)
    # parse content
    oParser = cParser()
    aPages = oParser.parse(sHtmlContent, sPagePattern)

    pages = 1

    if aPages[0] and bShowAllPages:
        pages = aPages[1][-1]

    oGui = cGui()

    for x in range(1, int(pages) + 1):
        sHtmlContentPage = __getHtmlContent('%spage/%s/' % (sUrl, str(x)))
        __getMovies(oGui, sHtmlContentPage)

    oGui.setEndOfDirectory()


def __getMovies(oGui, sHtmlContent):
    oParams = ParameterHandler()

    sBlockPattern = '<div class="moviefilm">.*?href="(.*?)"(.*?)src="(.*?)".*?alt="(.*?)"'

    # TODO: Add proper decoding (.decode) doesn't work
    sHtmlContent = __decode(sHtmlContent)
    # parse content
    oParser = cParser()
    aResult = oParser.parse(sHtmlContent, sBlockPattern)


    if aResult[0]:
        for link, tmp, img, title in aResult[1]:
            guiElement = cGuiElement(title, SITE_IDENTIFIER, 'showHosters')
            guiElement.setThumbnail(img)
            oParams.addParams({'sUrl': link, 'Title': title})
            # TODO: Looking for span isn't the best way, but the only difference I found
            if "span" not in tmp:
                oGui.addFolder(guiElement, oParams)
            else:
                oGui.addFolder(guiElement, oParams, bIsFolder=False)


def __decode(text):
    text = text.replace('&#8211;', '-')
    text = text.replace('&#038;', '&')
    text = text.replace('&#8217;', '\'')
    return text


def showHosters():
    logger.info('load showHosters')
    oParams = ParameterHandler()
    sPattern = 'a href="(' + oParams.getValue('sUrl') + '.*?/)"'

    # request
    sHtmlContent = __getHtmlContent()
    # parse content
    oParser = cParser()
    aResult = oParser.parse(sHtmlContent, sPattern)

    hosters = []

    hosters = getHoster(sHtmlContent, hosters)

    if hosters[0]['name'] == 'seriesever':
        addSeriesEverLink(hosters[0])
        return

    if aResult[0]:
        for link in aResult[1]:
            sHtmlContentTmp = __getHtmlContent(link)
            hosters = getHoster(sHtmlContentTmp, hosters)

    if hosters:
        hosters.append('getHosterUrl')

    return hosters


def addSeriesEverLink(hoster):
    oParams = ParameterHandler()
    oGui = cGui()

    guiElement = cGuiElement(hoster['displayedName'], SERIESEVER_IDENTIFIER, 'showMovie')
    oParams.addParams({'sUrl': hoster['link']})
    oGui.addFolder(guiElement, oParams)

    oGui.setEndOfDirectory()

def getHoster(sHtmlContent, hosters):
    sPattern = '<p><iframe src="(.*?)"'
    sSEPattern = '<a href="(http://seriesever.com/serien/.*?)" target="MoviesEver">'

    # parse content
    oParser = cParser()

    aResult = oParser.parse(sHtmlContent, sPattern)
    aSEResult = oParser.parse(sHtmlContent, sSEPattern)

    if aSEResult[0]:
        hoster = dict()

        hoster['link'] = aSEResult[1][0]
        hoster['name'] = 'seriesever'
        hoster['displayedName'] = 'Gehe zu SeriesEver'

        hosters.append(hoster)

    if aResult[0]:
        hoster = dict()

        hoster['link'] = aResult[1][0]

        hname = 'Unknown Hoster'
        try:
            hname = re.compile('^(?:https?:\/\/)?(?:[^@\n]+@)?([^:\/\n]+)', flags=re.I | re.M).findall(hoster['link'])[0]
        except:
            pass

        hoster['name'] = hname
        hoster['displayedName'] = hname

        hosters.append(hoster)

    return hosters


def getHosterUrl(sUrl=False):
    oParams = ParameterHandler()

    logger.info(oParams.getAllParameters())

    if not sUrl:
        sUrl = oParams.getValue('url')

    results = []
    result = {}
    result['streamUrl'] = sUrl
    result['resolved'] = False
    results.append(result)
    return results