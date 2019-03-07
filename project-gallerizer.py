# partially adapted from Martin's wikicrawler (as of 2019-2-10)
# https://github.com/comakingspace/CommonFiles/tree/master/Printouts/QRCodes

import argparse
import mwapi
import json
import random
import requests
import re
from bs4 import BeautifulSoup

# functions copied from the wikicrawler, then adapted
def crawlpage(title, infoboxname, categoryname=''):
    print("Crawled: " + title) #user feedback
    rawurl = "https://wiki.comakingspace.de/index.php?title=" + title + '&action=raw'
    responseraw = requests.get(rawurl)
    infoboxes = extractinfoboxes(responseraw.text, infoboxname)
    number = 1
    if len(infoboxes) == 0:
        global errors
        errors = errors + title + " is missing an InfoBox and was ignored\n"
    else:
        for infobox in infoboxes:
            navigationInfo = parseToolbox(infobox, title)
        
            return(navigationInfo) #raw list, to check output
 
def parseToolbox(infoboxtext, title):
    #Getting the parsed html of the infobox
    global session
    url = "https://wiki.comakingspace.de/" + title
    url = url.replace(' ', '_')
    parsingresponse = session.get(action='parse', text=infoboxtext, contentmodel='wikitext', disablelimitreport=1)
    parsedwikitext = parsingresponse['parse']['text']['*']
    parsedwikitext = ('<html><body>' + parsedwikitext + '</body></html>')
    
    #Generating a BeatifulSoup object, which allows us to modify the DOM
    html = BeautifulSoup(parsedwikitext, 'html.parser')

    #Adding the mediawiki CSS file into the head
    head = html.new_tag('head')
    style = html.new_tag('link')
    style['href'] = 'https://wiki.comakingspace.de/load.php?debug=false&lang=en&modules=ext.slideshow.css%7Cmediawiki.legacy.commonPrint%2Cshared%7Cmediawiki.sectionAnchor%7Cmediawiki.skinning.interface%7Cskins.vector.styles&only=styles&skin=vector'
    style['rel'] = 'stylesheet'
    head.append(style)
    html.html.body.insert_before(head)
    
    #find the image tag
    image_link = html.find('a', 'image')
    #filter out pages with a broken file link in the InfoBox
    if image_link is not None:
        image_tag = image_link.find('img')
        #find the image title within image_tag
        image_title=str(image_tag)
        title_start = image_title.find("alt=") + 5
        image_title = image_title[title_start:]
        title_end = image_title.find("height=") - 2
        image_title = "File:" + image_title[:title_end]
    else:
        image_title = "broken"  
    
    #find the InfoBox title via its "big" attribute -> TODO: replace <br> or </br> by spaces!
    box_tag = html.find('big')
    box_title = box_tag.get_text()

    # return values; ignore pages with the default image or broken links
    global errors
    if image_title == "File:Project-default.png":
        errors = errors + title + " still has the default photo and was ignored\n "
        return None
    elif image_title == "broken":
        errors = errors + title + " has a broken image link and was ignored\n"
        return None     
    else:
        info = [image_title, title, box_title]
        return info

def extractinfoboxes(wikitext, infoboxname):
    infoboxes = []
    infoboxstart = wikitext.find("{{" + infoboxname)
    infoboxtext = None
    while infoboxstart != -1:
        infoboxend = wikitext.find("}}", infoboxstart)
        infoboxtext = wikitext[infoboxstart:infoboxend+2]
        while infoboxtext.count("{{") != infoboxtext.count('}}'):
            infoboxend = wikitext.find("}}", infoboxend+2)
            infoboxtext = wikitext[infoboxstart:infoboxend+2]
        if infoboxtext is not None:
            infoboxes.append(infoboxtext)
        infoboxstart = wikitext.find("{{" + infoboxname, infoboxend)
    return infoboxes


##### execution of the script #####
session = mwapi.Session(host='https://wiki.comakingspace.de', api_path='/api.php')

#asks for the first **3** pages in the "Project" namespace (ID 4)
Response = session.get(action='query', list='allpages', apnamespace='4', aplimit='3')

#initialize array that collects outputs for messing with later
navigationInfo = []

#initialize "errors" string to collect failure information
errors = "Errors:\n"

#initialize wikitext to be given out (with " in string as escape sequences \")
gallerycode = "<gallery mode=packed heights=150 caption=\"click photos for more!\">\n"
DATA = Response['query']['allpages']

for page in DATA:
    #get the content of the page and add it to an array
    crawl_result = crawlpage(page['title'], 'ProjectInfoBox', 'ProjectInfoBox')
    if crawl_result is not None: #excludes insufficient pages
        #crawl_result[0]: crawled image title, crawl_result[1]: crawled page title, crawl_result[2]: crawled project title
        gallerycode = gallerycode + crawl_result[0] + "|link=[[" + crawl_result[1] + "]]|" + crawl_result[2] + "\n"
    # else:
      #  print("insufficient content") ##TODO: add to error report
        
    navigationInfo.append(crawl_result) 

##### tell the user what came out of it
print("\nSuccess on " + str(len(navigationInfo)) + " pages!\n")

#error output:
print(errors) #line break already included
    
#straight gallery output:  
gallerycode = gallerycode + "</gallery> \n"
print("ALPHABETICAL gallery wikitext:\n" + gallerycode)

#randomized gallery output:
random.shuffle(navigationInfo)
gallerycode = "<gallery mode=packed heights=150 caption=\"click photos for more!\">\n"
while(len(navigationInfo) >> 0):
    crawl_result = navigationInfo[0]
    gallerycode = gallerycode + crawl_result[0] + "|link=[[" + crawl_result[1] + "]]|" + crawl_result[2] + "\n"
    navigationInfo = navigationInfo[1:]

gallerycode = gallerycode + "</gallery> \n"
print("RANDOMIZED gallery wikitext:\n" + gallerycode)


  ### TODO:
  ## known bugs: line break in box title not shown - should be replaced by space
  ## wanted features: timestamp/link to script; randomized output; recently updated pages; error reports (missing photo/broken link)
