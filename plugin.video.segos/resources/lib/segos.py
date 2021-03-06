# -*- coding: utf-8 -*-

import urllib2,urllib
import os,re
import urlparse
import cookielib

BASEURL='http://segos.es'
TIMEOUT = 10
UA='Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'

COOKIEFILE=''

def getUrl(url,data=None,header={},useCookies=True,saveCookie=False):
    if COOKIEFILE and os.path.isfile(COOKIEFILE) and useCookies:
        cj = cookielib.LWPCookieJar()
        cj.load(COOKIEFILE)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        urllib2.install_opener(opener)
    
    req = urllib2.Request(url,data)
    if not header:
        header = {'User-Agent':UA}
    req = urllib2.Request(url,data,headers=header)
    try:
        response = urllib2.urlopen(req,timeout=TIMEOUT)
        link =  response.read()
        response.close()
        if COOKIEFILE and os.path.isfile(COOKIEFILE) and saveCookie and useCookies:
             cj.save(COOKIEFILE, ignore_discard = True) 
    except urllib2.HTTPError as e:
        #link = e.read()
        link = ''
    return link
    
# url='http://segos.es/filmy.php?page=1'    
# url='http://segos.es/filmy/gatunek.php?gatunek=Akcja'
# url='http://segos.es/bajki.php?page=2'
def scanMainpage(url,page=1):
    if 'page=' in url:
        url = re.sub('page=\d+','page=%d'%int(page),url)
    else:
        url = url + '&page=%d' %page
    content = getUrl(url)
    
    nextPage=False
    next_url=url.replace(BASEURL,'').replace('page=%d'%page,'page=%d' %(page+1))
    if content.find(next_url.split('//')[-1])>-1:
        nextPage = page+1
   
        
    ids = [(a.start(), a.end()) for a in re.finditer('<div class="col-lg-3 col-md-3 col-sm-6 segos">', content)]
    ids.append( (-1,-1) )
    out=[]
    for i in range(len(ids[:-1])):
        #print content[ ids[i][1]:ids[i+1][0] ]
        subset = content[ ids[i][1]:ids[i+1][0] ]

        href = re.compile('<a href="(.*?view.*?)"').findall(subset)
        title = re.compile('">(\w+.*?)</').findall(subset)

        
        img = re.compile('<img .*? img-glowna" src="(.*?)"').findall(subset)
        img = img[0] if img else ''
        if img.startswith('http'):
            img=img
        elif img.startswith('../'):
            img=img.replace('..',BASEURL)
        elif img.startswith('obrazki'):
            img=BASEURL+'/'+img
        jezyk=''
        quality=''
        flags = re.compile('px;" src="(.*?)"').findall(subset)
        for im in flags:
            if 'lek.png' in im:
                jezyk = 'Lektor '
            elif 'hd.png' in im:
                quality = 'HD'

        
        if href and title and img:
            one = {'url'   : BASEURL+href[0],
                'title'  : unicodePLchar(title[0]),
                'plot'   : '',
                'img'    : img,
                'rating' : '',
                'year'   : '',
                'code'  : jezyk+quality
                    }
            out.append(one)
            
    prevPage = page-1 if page>1 else False
    return (out, (prevPage,nextPage))  

def get_polecane(url='http://segos.es/recomend_list.php'):
    out_F=[]
    out_B=[]
    content = getUrl(url)
    trs = re.compile('<tr>(.*?)</tr>',re.DOTALL).findall(content)
    for tr in trs:
        href_title = re.compile('<p><a href="(.*?)">(.*?)</a></p>').findall(tr)
        img = re.compile('<img src="(.*?)"').findall(tr)
        if href_title:
            one = {'url'   : BASEURL+href_title[0][0],
                'title'  : unicodePLchar(href_title[0][1]),
                'plot'   : '',
                'img'    : BASEURL+img[0] if img else '',
                'rating' : '',
                'year'   : '',
                'code'  : '',
                    }
            if   '/bajki/' in href_title[0][0]:
                out_B.append(one)
            elif '/filmy/' in href_title[0][0]:
                out_F.append(one)
    return (out_F,out_B)
    
#url='http://segos.es/filmy/view.php?id=1776'    
def get_info(url,infoTab=True):
    info={}
    if infoTab:
        content = getUrl(url)
        infx = content.find('<div id="myTabContent" class="tab-content">')
        if infx:
            subset=content[infx:-1]
            year = re.search('<b>Rok produkcji</b>:(.*?)<',subset,flags=re.MULTILINE|re.I)
            genre = re.search('<b>Gatunek</b>:(.*?)<',subset,flags=re.DOTALL)
            quality = re.search('<b>Jakość</b>:(.*?)<',subset,flags=re.MULTILINE|re.I)
            audio = re.search('<b>Audio</b>:(.*?)<',subset,flags=re.MULTILINE|re.I)
            lang = re.search('<b>Język</b>:(.*?)<',subset,flags=re.MULTILINE|re.I)
            plot = re.search('<b>Opis</b>:(.*?)<',subset,flags=re.MULTILINE|re.I)
            if year:    info['year']=year.group(1).strip().strip('(').strip(')')
            if genre:   info['genre']=genre.group(1).strip()
            if quality: info['quality']=quality.group(1).strip()
            if audio:   info['audio']=audio.group(1).strip()
            if lang:    info['lang']=lang.group(1).strip()
            if plot:    info['plot']=unicodePLchar(plot.group(1).strip())
            info['code']= ','.join([info.get('quality'),info.get('lang'),info['audio']])
    return info
    
# url='http://segos.es/filmy/view.php?id=1583'
# url='http://segos.es/bajki/view.php?id=1209'  
# url='http://segos.es/filmy/view.php?id=1229'
# url='http://segos.es/bajki/view.php?id=1266'
def getVideoLinks(url):
    outL=[]
    content = getUrl(url)
    iframes = re.compile('<iframe(.*?)</iframe>',re.DOTALL).findall(content)
    #iframe = iframes[0]
    for iframe in iframes:
        href = re.compile('src="(.*?)"').findall(iframe)
        if href:
            link = href[0]
            host = urlparse.urlparse(link).netloc
            if 'greevid.com' in host:
                link = get_greevid(link)
                host += ' - ' + urlparse.urlparse(link).netloc
            if 'ebd.cda.pl' in host:
                link = 'http://www.cda.pl/video/'+link.split('/')[-1]
                host = urlparse.urlparse(link).netloc
        outL.append({'href':link,'host':host})
    idx = content.find('Inne jakości')
    if idx:
        items = re.compile( '<div class="col-lg-1">(.*?)</div>[ \t\n]*<div class="col-lg-1">(.*?)</div>[ \t\n]*<div class="col-lg-7">(.*?)</div>[ \t\n]*<div class="col-lg-2">(.*?)</div>[ \t\n]*<div class="col-lg-1">(.*?)</div>',re.DOTALL).findall(content[idx:-1])
        #item = items[2]
        if len(items)>1:
            for item in items[1:]:
                audio = re.compile('title="(.*)"').findall(item[0])
                audio = '[COLOR green]%s[/COLOR]'%audio[0] if audio else ''
                dzwiek = ' dźwięk:[B]%s[/B]'%item[1] if len(item[1]) else ''
                quality = re.compile('\[(.*?)\]').findall(item[2])
                quality = ' jakść:[B]%s[/B]'%quality[0] if quality else ''
                link = re.compile('href="(.*?)"').findall(item[2])
                if link:
                    link='http'+link[0].split('http')[-1]
                    if 'greevid.com' in link:
                        link = get_greevid(link)
                    host = urlparse.urlparse(link).netloc +'  '+ audio + dzwiek + quality
                    outL.append({'href':link,'host':host})
    return outL    

# url = 'http://greevid.com/video_148786?player=embed&width=708&height=400'     
def get_greevid(url):
    content = getUrl(url)
    iframes = re.compile('<iframe(.*?)</iframe>',re.DOTALL).findall(content)
    if iframes:
        href = re.compile('src="(.*?)"').findall(iframes[0])
        if href:
            href = 'http'+href[0].split('http')[-1]
            return href
    return ''
    
def get_kategorie(url='http://segos.es/filmy.php'):
    cat=[]
    content = getUrl(url)
    idx=content.find('<h4>Kategorie</h4>')
    if idx:
        cat = re.compile('<li><a href="(.*?)">(.*?)</a></li>').findall(content[idx:-1])
        if cat:
            cat = [(BASEURL+x[0],x[1].strip()) for x in cat]
    return cat

url='http://segos.es/szukaj.php?title=dom' 
def szukaj(url,page=1):
    content = getUrl(url)
    ids = [(a.start(), a.end()) for a in re.finditer('<div class="col-lg-12" style="padding:0 0 5px 0;">', content)]
    ids.append( (-1,-1) )
    out=[]
    for i in range(len(ids[:-1])):
        #print content[ ids[i][1]:ids[i+1][0] ]
        subset = content[ ids[i][1]:ids[i+1][0] ]

        href = re.compile('href="(.*?view.*?)"').findall(subset)
        title = re.compile('">(\w+.*?)</').findall(subset)
        img = re.compile('<img src="(.*?)"').findall(subset)
        img = img[0] if img else ''
        if img.startswith('http'):
            img=img
        elif img.startswith('../'):
            img=img.replace('..',BASEURL)
        elif img.startswith('obrazki'):
            img=BASEURL+'/'+img
        elif img.startswith('/obrazki'):
            img=BASEURL+img            
        
        if href and title and img:
            one = {'url'   : BASEURL+href[0],
                'title'  : unicodePLchar(title[0]),
                'plot'   : '',
                'img'    : img,
                'rating' : '',
                'year'   : '',
                'code'  : ''
                    }
            out.append(one)
    return out
    
def unicodePLchar(txt):
    if type(txt) is not str:
        txt=txt.encode('utf-8')
        
    txt = txt.replace('#038;','')
    txt = txt.replace('&lt;br/&gt;',' ')
    txt = txt.replace('&#34;','"')
    txt = txt.replace('&#39;','\'').replace('&#039;','\'')
    txt = txt.replace('&#8221;','"')
    txt = txt.replace('&#8222;','"')
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
    