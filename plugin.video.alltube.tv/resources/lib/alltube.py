# -*- coding: utf-8 -*-

import urllib2,urllib
import re,os
import base64,json

BASEURL='http://alltube.tv'
TIMEOUT = 10
UA='Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_4; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.472.63 Safari/534.3'

def getUrl(url,data=None):
    req = urllib2.Request(url,data)
    req.add_header('User-Agent', UA)
    response = urllib2.urlopen(req,timeout=TIMEOUT)
    link = response.read()
    response.close()
    return link
    
# url='http://alltube.tv/filmy-online/'
# url='http://alltube.tv/filmy-online/kategoria[1]+wersja[Lektor,Dubbing]+strona[2]+'
# filmy,pagination=scanMainpage(url,page=1)

def scanMainpage(url,page=1,data=None):
   
    if 'strona' in url:
        url = re.sub(r'strona\[\d+\]','strona[%d]'%page,url)
    else:
        url = url + 'strona[%d]+'%page
    
    content = getUrl(url,data)
    ids = [(a.start(), a.end()) for a in re.finditer('<div class="item-block clearfix">', content)]
    if not ids:
        ids = [(a.start(), a.end()) for a in re.finditer('<div class="cartoon">', content)]
    ids.append( (-1,-1) )
    out=[]
    for i in range(len(ids[:-1])):
        #print content[ ids[i][1]:ids[i+1][0] ]
        subset = content[ ids[i][1]:ids[i+1][0] ]
        href = re.compile('<a href="(.*?)"',re.DOTALL).search(subset)
        title = re.compile('<h3>(.*?)</h3>',re.DOTALL).search(subset)
        title2= re.compile('<div class="second-title">(.*?)</div>').search(subset)
        plot = re.compile('<p[^>]>(.*?)</p>',re.DOTALL).search(subset)
        img = re.compile('<img src="(.*?)"',re.DOTALL).search(subset)
        year = re.compile('<div class="item-details">(.*?)<',re.DOTALL).search(subset)
        lang = re.compile('aria-hidden="true"></i>(.*?)<').search(subset)
        if year:
            year =  re.compile('(\d{4})',re.DOTALL).search(year.group(1))
        
        lang = lang.group(1).replace('&nbsp;','').strip() if lang else ''
        

        if href and title:
            img = img.group(1) if img else ''
            
            one = {'href'   : href.group(1),
                'title'  : unicodePLchar(title.group(1)),
                'plot'   : unicodePLchar(plot.group(1)) if plot else '',
                'img'    : img,
                'year'   : year.group(1) if year else '?',
                'code'   : lang,
                    }
            out.append(one)

    nextPage=False
    if content.find('strona[%d]'%(page+1))>-1:
        nextPage = page+1
        
    prevPage = page-1 if page>1 else False
    return (out, (prevPage,nextPage))

#url='http://alltube.tv/seriale-online/'
#url='http://alltube.tv/seriale-online/filter=popular'

def scanTVshows(data=None,page=1):
    url='http://alltube.tv/seriale-online/'
    urlpage = url + '%d'%page
    content = getUrl(urlpage,data)

    ids = [(a.start(), a.end()) for a in re.finditer('  <div class="item-block clearfix">', content)]
    ids.append( (-1,-1) )
    out=[]
    for i in range(len(ids[:-1])):
        #print content[ ids[i][1]:ids[i+1][0] ]
        subset = content[ ids[i][1]:ids[i+1][0] ]
        
        href = re.compile('<a href="(.*?)"',re.DOTALL).search(subset)
        img = re.compile('<img src="(.*?)"',re.DOTALL).search(subset)
        #title = re.compile('<h3>(.*?)</h3>',re.DOTALL).search(subset)
        #plot = re.compile('<p>(.*?)</p>',re.DOTALL).search(subset)
        title_1 = re.compile('<div class="top-belt">(.*?)<').search(subset)
        title_2 = re.compile('<div class="bottom-belt">(.*?)<').search(subset)

        if href and title_1:
            title = unicodePLchar(title_1.group(1))
            if title_2:
               title = unicodePLchar(title_2.group(1)) +', ' + title 
            one = {'href'   : href.group(1),
                'title'  : title,
                #'plot'   : unicodePLchar(plot.group(1)) if plot else '',
                'img'    : img.group(1) if img else '',
                #'year'   : year.group(1) if year else '?',
                    }
            out.append(one)

    nextPage=False
    if content.find('href="%d"'%(page+1))>-1:
        nextPage = page+1
        
    prevPage = page-1 if page>1 else False
    return (out, (prevPage,nextPage))


#url='http://alltube.tv/gra-o-tron-game-of-thrones/odcinek-08/odcinek-8-sezon-6/60500'
#url='http://alltube.tv/serial/nie-z-tego-swiata-supernatural/320'
def scanEpisodes(url):
    content = getUrl(url)
    episodes = re.compile('<li class="episode"><a href="(.*?)">(.*?)</a></li>').findall(content)
    out=[]    
    for e in episodes:
        season = re.findall('s(\d+)',e[1],flags=re.I)
        season = int(season[0]) if season else ''
        episode = re.findall('e(\d+)',e[1],flags=re.I)
        episode = int(episode[0]) if episode else ''
        one = { 'href'  : e[0],
                'season' : season,
                'episode' : episode,
                'mediatype': 'episode',
                'title' : unicodePLchar(e[1].strip())}
        out.append(one)
    return out

#out = scanEpisodes(url)
def splitToSeasons(out):
    out_s={}
    seasons = [x.get('season') for x in out]
    for s in set(seasons):
        out_s['Sezon %02d'%s]=[out[i] for i, j in enumerate(seasons) if j == s]
    return out_s
            
#url=href_go
def parseVideoLink(url,host):
    if 'cda' in host:
        return 'http://www.cda.pl/video/%s'%(url.split('id=')[-1])
    elif 'posiedze' in host:
        return ''
    elif 'alltube.tv' in url:
        content = getUrl(url)
        outurl=''
        href= re.compile('src="(.*?)"').findall(content)
        if href:
            outurl = href[0]
            if outurl.startswith('//'):
                outurl = 'http:'+outurl
        return outurl
    elif host in url:
        if url.startswith('//'):
            url = 'http:' + url 
        return url
    else:
        print url
        return url
        
#url='http://alltube.tv/film/polska-irlandia-polnocna-grupa-c-12-06-2016-2016-pl/27690'
#url='http://alltube.tv/film/re-kill-2015-eng/19090'
def getVideoLinks(url):
    content = getUrl(url)
    tbody = re.compile('<tbody>(.*?)</tbody>',re.DOTALL).findall(content)
    tbody = tbody[0] if tbody else ''
    ids = [(a.start(), a.end()) for a in re.finditer('<tr>', tbody)]
    ids.append( (-1,-1) )
    out=[]
    for i in range(len(ids[:-1])):
        #print content[ ids[i][1]:ids[i+1][0] ]
        subset = tbody[ ids[i][1]:ids[i+1][0] ]
        
        href = re.compile('data-iframe="(.*?)"').search(subset)
        jezyk = re.compile('class="text-center">(.*?)<',re.DOTALL).search(subset)
        host = re.compile('<img src=".*?"\s*alt=".*?">(.*?)<').search(subset)
        rate =re.compile('class="rate">(.*?)</div>',re.DOTALL).search(subset)
        
        # if host.groups()[-1].strip() =='vshare':
        #     break
        
        if href and host:
            wersja= jezyk.group(1) if jezyk else ''
            ocena = rate.group(1) if rate else ''
            host  = host.groups()[-1].strip()
            href_go = base64.b64decode(href.group(1))
            href_url = parseVideoLink(href_go,host)
            if href_url:
                one = {'url' : href_url,
                    'title': "[COLOR green]%s[/COLOR] | Ocena Linku: %s | [%s]" %(wersja,ocena,host),
                    'host': host,
                    'rate':int(ocena.strip('%')),
                    'wersja':wersja,
                    }
                out.append(one)
            else:
                print 'LINK PROBLEM: %s'%href_go
    return out
 

def Search(txt='futurama'):
    out_f=[]
    out_s=[]

    url='http://alltube.tv/index.php?url=search/autocomplete/&phrase=%s'%urllib.quote_plus(txt)
    content= getUrl(url)
    if content:
        items=json.loads(content)
        for item in items.get('suggestions',[]):
            href  = item.get('data','')
            title = unicodePLchar(item.get('value',''))
            if 'serial' in href:
                out_s.append({'title':title,'href':href})
            else:
                out_f.append({'title':title,'href':href})
    return (out_f,out_s)

def getPlaylist():
    content=getUrl('http://alltube.tv/playlist/')
    ids = [(a.start(), a.end()) for a in re.finditer('<div class="playlist-item', content)]
    ids.append( (-1,-1) )
    out=[]
   
    for i in range(len(ids[:-1])):
        #print content[ ids[i][1]:ids[i+1][0] ]
        offset=200
        subset = content[ ids[i][1]-offset:ids[i+1][0] ]
        
        href = re.compile('<a href="(http://alltube.tv/playlista.*?)"').search(subset)
        title = re.compile('<h3>(.*?)</h3>').search(subset)
        inside = re.compile('<div class="col-sm-6 text-right">(.*?)</div>',re.DOTALL).search(subset)
        
        inside = inside.group(1).replace('&nbsp;','').strip().replace('  ',' ') if inside else ''
        
        if href and title:
            title= unicodePLchar(title.group(1)) if title else ''
            inside = unicodePLchar(inside)
            href_url = href.group(1)
            print title,inside
            one = {'href' : href_url,
                   'title': "[COLOR cyan]%s[/COLOR] [%s]" %(title,inside),
                    }
            out.append(one)
    return out
    
#url='http://alltube.tv/playlista/gwiezdne-wojny-star-wars/100/1'
#url='http://alltube.tv/playlista/o-diable/468/1'

def getPlaylistContent(url,page=1):
    page = int(page)
    out_f=[]
    out_s=[]
    url = re.sub('/\d+$','/%d'%page,url)
    content=getUrl(url)
    ids = [(a.start(), a.end()) for a in re.finditer('<div class="item-block clearfix">', content)]
    ids.append( (-1,-1) )
    for i in range(len(ids[:-1])):
        #print content[ ids[i][1]:ids[i+1][0] ]
        subset = content[ ids[i][1]:ids[i+1][0] ]
        href = re.compile('<a href="(.*?)"',re.DOTALL).search(subset)
        title = re.compile('<h3>(.*?)</h3>',re.DOTALL).search(subset)
        title2= re.compile('<div class="second-title">(.*?)</div>').search(subset)
        plot = re.compile('<p[^>]>(.*?)</p>',re.DOTALL).search(subset)
        img = re.compile('<img src="(.*?)"',re.DOTALL).search(subset)
        year = re.compile('<div class="item-details">(.*?)<',re.DOTALL).search(subset)
        if year:
            year =  re.compile('(\d{4})',re.DOTALL).search(year.group(1))
        
        #lang = re.compile('aria-hidden="true"></i>(.*?)<').search(subset)
        #lang = lang.group(1).replace('&nbsp;','').strip() if lang else ''
        

        if href and title:
            img = img.group(1) if img else ''
            
            one = {'href'   : href.group(1),
                'title'  : unicodePLchar(title.group(1)),
                'plot'   : unicodePLchar(plot.group(1)) if plot else '',
                'img'    : img,
                'year'   : year.group(1) if year else '?',
                #'code'   : lang,
                    }
            if '/film/' in one.get('href'):
                out_f.append(one)
            else:
                out_s.append(one)
    nextPage=False
    
    if content.find('strona" href="%d"'%(page+1))>-1:
        nextPage = page+1
        
    prevPage = page-1 if page>1 else False
    return ((out_f,out_s), (prevPage,nextPage))
    

## Filter Category/Version/Year
#filter('gatunek')
#filter('rok')
#filter('jezyk')
def filter(what):
    content = getUrl('http://alltube.tv/filmy-online/')
    if   what == 'gatunek':
        filter = re.compile('<ul class="filter-list filter-category">(.*?)</ul>',re.DOTALL).findall(content)
        pattern = 'kategoria[%s]+'
    elif what =='rok':
        filter = re.compile('<ul class="filter-list" id="filter-year">(.*?)</ul>',re.DOTALL).findall(content)
        pattern = 'rok[%s]+'
    elif what =='jezyk': 
        filter = re.compile('<ul class="filter-list" id="filter-version">(.*?)</ul>',re.DOTALL).findall(content)
        pattern = 'wersja[%s]+'
    else:
        filter = []
    if filter:
        items = re.compile('<li data-id="(.*?)"[^>]*>(.*?)</li>',re.DOTALL).findall(filter[0])
        kat = [pattern%x[0] for x in items]
        display = [x[1] for x in items]
        return (display,kat)
    return (None,None)

##
def unicodePLchar(txt):
    if type(txt) is not str:
        txt=txt.encode('utf-8')
        
    txt = txt.replace('&nbsp;','')
    txt = txt.replace('#038;','')
    txt = txt.replace('&lt;br/&gt;',' ')
    txt = txt.replace('&#34;','"')
    txt = txt.replace('&#39;','\'').replace('&#039;','\'')
    txt = txt.replace('&#8221;','"')
    txt = txt.replace('&#8222;','"')
    txt = txt.replace('&#8217;','\'')
    txt = txt.replace('&#8211;','-').replace('&ndash;','-')
    txt = txt.replace('&quot;','"').replace('&amp;quot;','"')
    txt = txt.replace('&oacute;','ó').replace('&Oacute;','Ó')
    txt = txt.replace('&amp;oacute;','ó').replace('&amp;Oacute;','Ó')
    #txt = txt.replace('&amp;','&')
    txt = txt.replace('\u0105','ą').replace('\u0104','Ą')
    txt = txt.replace('\u0107','ć').replace('\u0106','Ć')
    txt = txt.replace('\u0119','ę').replace('\u0118','Ę')
    txt = txt.replace('\u0142','ł').replace('\u0141','Ł')
    txt = txt.replace('\u0144','ń').replace('\u0144','Ń')
    txt = txt.replace('\u00f3','ó').replace('\u00d3','Ó')
    txt = txt.replace('\u015b','ś').replace('\u015a','Ś')
    txt = txt.replace('\u017a','ź').replace('\u0179','Ź')
    txt = txt.replace('\u017c','ż').replace('\u017b','Ż')
    return txt