import os
import shutil
import subprocess
import sys
from tkinter import *
from tkinter import ttk
import threading
import requests
import cfscrape
from bs4 import BeautifulSoup
import webbrowser
from functools import partial
import time
from ebooklib import epub

version = "0.7" #Defines the current version

class WuxiaScraper(object):

    def __init__(self, window):
        self.window = window
        self.window.title("WuxiaWorld Scraper")
        self.window.configure(background = "black")

        #Labels
        Label(self.window, text="Novel Link: ", bg="black", fg="white", font="none 16").grid(row=0, column=0, sticky=W)

        Label(self.window, text="Volume Num [optional]: ", bg="black", fg="white", font="none 10").grid(row=1, column=0, sticky=W)

        Label(self.window, text="Cover Page [optional]: ", bg="black", fg="white", font="none 10").grid(row=2, column=0, sticky=W)

        #Entries
        self.eNovel = Entry(self.window, width=75, bg="white")
        self.eNovel.grid(row=0, column=1, sticky=W)
        self.eNovel.bind('<Return>', lambda _: self.compiler())

        self.eVolume = Entry(self.window, width=5, bg="white")
        self.eVolume.grid(row=1, column=1, sticky=W)
        self.eVolume.bind('<Return>', lambda _: self.compiler())

        self.eCover = Entry(self.window, width=20, bg="white")
        self.eCover.grid(row=2, column=1, sticky=W)
        self.eCover.bind('<Return>', lambda _: self.compiler())

        #Buttons
        Button(self.window, text="Compile", width=8, command=self.compiler).grid(row=3, column=1, sticky=W)

        #Text Boxes
        self.output = Text(self.window, width=75, height=10, state='disabled', wrap=WORD, background="white")
        self.output.grid(row=4, column=0, padx=5, columnspan=2, sticky=W)
        self.msg("LOG:")

        #Scroll Bars
        self.scroll = Scrollbar(self.window, width=10, command=self.output.yview)
        self.output.config(yscrollcommand=self.scroll.set)
        self.scroll.grid(row=4, column=1, sticky=E)

    def msg(self, text):
        self.output.config(state='normal')
        self.output.insert(END, text + '\n')
        self.output.see(END)
        self.output.config(state='disabled')

    def compiler(self):
        link = self.eNovel.get()
        volume = self.eVolume.get()
        cover = self.eCover.get()
        
        if volume == '':
            volume = 0
            self.msg('All Volumes will be compiled.')
        else:
            self.msg('Only Volume: ' + volume + ' will be compiled.')

        if cover == '':
            self.msg('The default cover will be added.')
            self.cover = 'rsc/Novel Cover.png'
        else:
            exists = os.path.isfile('rsc/' + cover)
            if exists:
                self.msg('The cover ' + cover + ' will be added from the rsc folder.')
                cover = 'rsc/' + cover
            else:
                self.msg('+'*20)
                self.msg('Error Occured!')
                self.msg('No cover found with the name ' + cover + ' in the rsc folder.')
                self.msg('Make sure the cover is inside the rsc folder and the name is correct.')
                self.msg('+'*20)
                return       

        def callback():
            try:
                self.getNovel(link, cover, volume)
                self.msg('starting...')
                self.start()
                self.msg('+'*20)
                self.msg('ALL DONE!')
                self.msg('+'*20)
            except Exception as e:
                self.msg('+'*20)
                self.msg('Error Occured!')
                self.msg('+'*20)
                self.msg(str(e))
                self.msg("If you continue to have this error then open an issue here:")
                self.msg("github.com/dr-nyt/Translated-Novel-Downloader/issues")
                self.msg('+'*20)
                self.msg('')
        t = threading.Thread(target=callback)
        t.daemon = True
        t.start()

    def getNovel(self, link, cover, volume=0):
        self.link = link    #Holds the link to the novel.
        self.cover = cover

        self.head = 0   #Indicator to check if the current chapter has a title.
        #Get Novel Name
        self.novelName = ''
        tempName = self.link.split('/')[4]  #Split the link of the website into a list separated by "/" and get the 4th index [eg: http://wuxiaworld/novel/my-novel-name/].
        tempName = tempName.split('-')  #Split that into another list separated by "-" [eg: my-novel-name].
        for name in tempName:
            self.novelName = self.novelName + name.capitalize() + ' '   #Capatalize each word of the novel name and add a space in between [eg: My Novel Name].
        self.novelName = self.novelName[:-1]    #IDK why I did this but there must be a reason... I'm sure of it!!!
        ###########
        self.chapterNum_start = 1   #The number of the starting chapter is initialized.
        self.chapterNum_end = 0     #This number of the last chapter is initialized.
        self.chapterCurrent = 1     #This is stores the number of the current chapter being compiled.

        self.volume = volume    #Holds the volume number specified, if no volume number is specified then default is 0.
        if(self.volume != 0):   #If the volume is not 0 then only the volume number specified will be downloaded.
            self.volume_limit = 1   #Sets the volume limit so only one volume will be allowed to download.
            self.volumeNum = int(self.volume)   #This variable is only used when only one volume needs to downloaded
        else:   #If the volume number is specified as 0 then all the volumes will be downloaded.
            self.volume_limit = 0   #Removes the volume limit to allow all volumes to be downloaded.
            self.volumeNum = 0  #This is set to 0 because all volumes will be downloaded now.
        self.volume_links = []  #Empty list to store links to the chapters of each volume, one volume at a time.

        page = requests.get(link)   #Connects to the website.
        self.soup = BeautifulSoup(page.text, 'html.parser')     #Gets the html from the website and converts it to readable text.
        
    def start(self):
        self.getChapterLinks()

    #I forgot what exactly this method does but it is something related to setting pointers to the starting and ending chapters of each volume in a novel.
    def getMetaData(self, link_start, link_end):
        metaData = []
        index = -1
        
        partsX = link_start.split('/')
        for x in partsX:
            if x != '' and x != 'novel':
                metaData.append(x)
        chapter_start = metaData[1].split('-')
        while index >= -len(chapter_start):
            if chapter_start[index].isdigit():
                self.chapterNum_start = int(chapter_start[index])
                index = -1
                break
            else:
                index = index - 1
        # for chapter in chapter_start:
        #     if chapter.isdigit():
        #         self.chapterNum_start = int(chapter)
        #         break
        self.chapterCurrent = self.chapterNum_start
        
        metaData = []

        partsY = link_end.split('/')
        for y in partsY:
            if y != '' and y != 'novel':
                metaData.append(y)
        chapter_end = metaData[1].split('-')
        while index >= -len(chapter_end):
            if chapter_end[index].isdigit():
                self.chapterNum_end = int(chapter_end[index])
                index = -1
                break
            else:
                index = index - 1
        # for chapter in chapter_end:
        #     if chapter.isdigit():
        #         self.chapterNum_end = int(chapter)
        #         break

    #This method loops between volumes and calls the getChapter method for each volume's chapters to be compiled and then saves them to a .doc file.   
    def getChapterLinks(self):
        volume_list = self.soup.find_all(class_="panel-body")
        
        if volume_list == []:
            self.msg('Either the link is invalid or your IP is timed out.')
            self.msg('In case of an IP timeout, it usually fixes itself after some time.')
            self.msg('Raise an issue @ https://github.com/dr-nyt/Translated-Novel-Downloader/issues if this issue persists')
        
        for v in volume_list:
            chapter_links = []
            
            if v.find(class_="col-sm-6") == None:
                continue

            #Skip over volumes if a specific volume is defined
            if self.volumeNum != 1 and self.volume_limit == 1:
                self.volumeNum-=1
                continue
            
            chapter_html_links = v.find_all(class_="chapter-item")
            for chapter_http in chapter_html_links:
                chapter_links.append(chapter_http.find('a').get('href'))
            
            self.volume_links.append(chapter_links)

            self.getMetaData(chapter_links[0], chapter_links[-1])

            self.book = epub.EpubBook()
            # add metadata
            self.book.set_identifier('dr_nyt')
            self.book.set_title(self.novelName + " Vol." + str(self.volume) + ' ' + str(self.chapterNum_start) + '-' + str(self.chapterNum_end))
            self.book.set_language('en')
            self.book.add_author('Unknown')
            self.chapterList = []

            #Add Coverpage if not already added
            if self.cover != '':
                self.book.set_cover("image.jpg", open(self.cover, 'rb').read())
            
            self.getChapter()

            self.volume_links = []
            if(self.volume_limit == 1):
                # create epub file
                epub.write_epub(self.novelName + " Vol." + str(self.volume) + ' ' + str(self.chapterNum_start) + '-' + str(self.chapterNum_end) + '.epub', self.book, {})
                if not os.path.exists(self.novelName):
                    os.mkdir(self.novelName)

                shutil.move(self.novelName + " Vol." + str(self.volume) + ' ' + str(self.chapterNum_start) + '-' + str(self.chapterNum_end) + '.epub', self.novelName + '/' + self.novelName + " Vol." + str(self.volume) + ' ' + str(self.chapterNum_start) + '-' + str(self.chapterNum_end) + '.epub')

                self.msg('+'*20)
                self.msg('Volume: ' + str(self.volume) + ' compiled!') 
                self.msg('+'*20)
                break
            
            self.volume+=1
            epub.write_epub(self.novelName + " Vol." + str(self.volume) + ' ' + str(self.chapterNum_start) + '-' + str(self.chapterNum_end) + '.epub', self.book, {})
            if not os.path.exists(self.novelName):
                os.mkdir(self.novelName)
                
            shutil.move(self.novelName + " Vol." + str(self.volume) + ' ' + str(self.chapterNum_start) + '-' + str(self.chapterNum_end) + '.epub', self.novelName + '/' + self.novelName + " Vol." + str(self.volume) + ' ' + str(self.chapterNum_start) + '-' + str(self.chapterNum_end) + '.epub')

            self.msg('+'*20)
            self.msg('Volume: ' + str(self.volume) + ' compiled!') 
            self.msg('+'*20)
            
    #This method loops through every chapter of a volume and compiles them properly, adding in headers and separator between each chapter.
    def getChapter(self):
        firstLine = 0
        for v in self.volume_links:
            for chapters in v:
                page = requests.get('https://www.wuxiaworld.com' + chapters)
                soup = BeautifulSoup(page.text, 'lxml')
                story_view = soup.find(class_='p-15')
                try:
                    chapterHead = story_view.find('h4').get_text()
                    c = epub.EpubHtml(title=chapterHead, file_name='Chapter_' + str(self.chapterCurrent) + '.xhtml', lang='en')
                    content = '<h2>' + chapterHead + '</h2>'
                except:
                    c = epub.EpubHtml(title="Chapter "  + str(self.chapterCurrent), file_name='Chapter_' + str(self.chapterCurrent) + '.xhtml', lang='en')
                    content = "<h2>Chapter " + str(self.chapterCurrent + "</h2>")

                story_view = soup.find(class_='fr-view')
                content += story_view.prettify().replace('\xa0', ' ').replace('Previous Chapter', '')

                content += "<p> </p>"
                content += "<p>Powered by dr_nyt</p>"
                content += "<p>If any errors occur, open an issue here: github.com/dr-nyt/Translated-Novel-Downloader/issues</p>"
                content += "<p>You can download more novels using the app here: github.com/dr-nyt/Translated-Novel-Downloader</p>"

                c.content = u'%s' % content
                self.chapterList.append(c)

                self.msg('Chapter: ' + str(self.chapterCurrent) + ' compiled!')
                self.chapterCurrent+=1

        for chap in self.chapterList:
            self.book.add_item(chap)

        self.book.toc = (self.chapterList)

        # add navigation files
        self.book.add_item(epub.EpubNcx())
        self.book.add_item(epub.EpubNav())

        # define css style
        style = '''
    @namespace epub "http://www.idpf.org/2007/ops";
    body {
        font-family: Cambria, Liberation Serif, Bitstream Vera Serif, Georgia, Times, Times New Roman, serif;
    }
    h2 {
         text-align: left;
         text-transform: uppercase;
         font-weight: 200;     
    }
    ol {
            list-style-type: none;
    }
    ol > li:first-child {
            margin-top: 0.3em;
    }
    nav[epub|type~='toc'] > ol > li > ol  {
        list-style-type:square;
    }
    nav[epub|type~='toc'] > ol > li > ol > li {
            margin-top: 0.3em;
    }
    '''

        # add css file
        nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
        self.book.add_item(nav_css)

        # create spin, add cover page as first page
        self.book.spine = ['cover', 'nav'] + self.chapterList




class NovelPlanetScraper(object):

    #The __init__ function only manages the GUI
    #The actual novel code starts in the getNovel() function
    def __init__(self, window):
        self.window = window
        self.window.title("NovelPlanet Scraper")
        self.window.configure(background = "black")

        #Canvas 1
        self.canv1 = Canvas(self.window, highlightthickness=0, relief='ridge')
        self.canv1.configure(background = "black")
        self.canv1.pack(fill=X)

        Label(self.canv1, text="Novel Link: ", bg="black", fg="white", font="none 16").pack(padx=5, side=LEFT)
        self.eNovel = Entry(self.canv1, width=75, bg="white")
        self.eNovel.pack(padx=5, side=LEFT)
        self.eNovel.bind('<Return>', lambda _: self.compiler())

        #Canvas 2
        self.canv2 = Canvas(self.window, highlightthickness=0, relief='ridge')
        self.canv2.configure(background = "black")
        self.canv2.pack(fill=X)

        Label(self.canv2, text="Chapter Range [optional]: ", bg="black", fg="white", font="none 10").pack(padx=5, side=LEFT)

        self.eChapterStart = Entry(self.canv2, width=5, bg="white")
        self.eChapterStart.pack(padx=5, side=LEFT)
        self.eChapterStart.bind('<Return>', lambda _: self.compiler())

        self.eChapterEnd = Entry(self.canv2, width=5, bg="white")
        self.eChapterEnd.pack(padx=5, side=LEFT)
        self.eChapterEnd.bind('<Return>', lambda _: self.compiler())

        #Canvas 3
        self.canv3 = Canvas(self.window, highlightthickness=0, relief='ridge')
        self.canv3.configure(background = "black")
        self.canv3.pack(fill=X)

        Label(self.canv3, text="Cover Page [optional]: ", bg="black", fg="white", font="none 10").pack(padx=5, side=LEFT)

        self.eCover = Entry(self.canv3, width=20, bg="white")
        self.eCover.pack(padx=5, side=LEFT)
        self.eCover.bind('<Return>', lambda _: self.compiler())

        #Canvas 4
        self.canv4 = Canvas(self.window, highlightthickness=0, relief='ridge')
        self.canv4.configure(background = "black")
        self.canv4.pack(fill=X)

        Button(self.canv4, text="Compile", width=8, command=self.compiler).pack(padx=150, side=LEFT)

        #Text Boxes
        self.output = Text(self.window, width=75, height=10, state='disabled', wrap=WORD, background="white")
        self.output.pack(fill=X, side=LEFT)
        self.msg('LOG:')

        #Scroll Bars
        self.scroll = Scrollbar(self.window, width=10, command=self.output.yview)
        self.output.config(yscrollcommand=self.scroll.set)
        self.scroll.pack(side=LEFT)

    def msg(self, text):
        self.output.config(state='normal')
        self.output.insert(END, text + '\n')
        self.output.see(END)
        self.output.config(state='disabled')

    def compiler(self):
        link = self.eNovel.get()
        start = self.eChapterStart.get()
        end = self.eChapterEnd.get()

        #Checks for invalid input
        if start != '':
            try:
                int(start)
            except:
                self.msg('+'*20)
                self.msg('Error Occured!')
                self.msg('Invalid chapter start number')
                self.msg('+'*20)
                return
        if end != '':
            try:
                int(end)
            except:
                self.msg('+'*20)
                self.msg('Error Occured!')
                self.msg('Invalid chapter end number')
                self.msg('+'*20)
                return

        cover = self.eCover.get()
        if cover == '':
            self.msg('The default cover will be added')
            cover = 'rsc/Novel Cover.png'
        else:
            exists = os.path.isfile('rsc/' + cover)
            if exists:
                self.msg('The cover ' + cover + ' will be added from the rsc folder.')
                cover = 'rsc/' + cover
            else:
                self.msg('+'*20)
                self.msg('Error Occured!')
                self.msg('No cover found with the name ' + cover + ' in the rsc folder.')
                self.msg('Make sure the cover is inside the rsc folder and the name is correct.')
                self.msg('+'*20)
                return       

        def callback():
            try:
                self.msg('Connecting to NovelPlanet...')
                self.getNovel(link, start, end, cover)
                self.msg('starting...')
                self.compileNovel()
                self.msg('+'*20)
                self.msg('ALL DONE!')
                self.msg('+'*20)
            except Exception as e:
                self.msg('+'*20)
                self.msg('Error Occured!')
                self.msg('+'*20)
                self.msg(str(e))
                self.msg("If you continue to have this error then open an issue here:")
                self.msg("github.com/dr-nyt/Translated-Novel-Downloader/issues")
                self.msg('+'*20)
                self.msg('')
        t = threading.Thread(target=callback)
        t.daemon = True
        t.start()

    def getNovel(self, link, chapterStart, chapterEnd, cover):
        self.link = link
        self.cover = cover

        #Initialize connection with NovelPlanet
        self.scraper = cfscrape.create_scraper()
        page = self.scraper.get(link)
        soup = BeautifulSoup(page.text, 'html.parser')

        #Get Novel Name
        self.novelName = soup.find(class_='title').get_text()

        #Get the html that stores links to each chapter
        chapters = soup.find_all(class_='rowChapter')

        #Get all the specified links from the html
        self.chapter_links = []
        for chapter in chapters:
            self.chapter_links.append(chapter.find('a').get('href'))
        self.chapter_links.reverse() #Reverse the list so the first index will be the first chapter and so on

        #Cut down the links if the number of chapters are specified and,
        #Set the starting and last chapter number
        if chapterStart != '':
            self.chapterNum_start = int(chapterStart)
            self.currentChapter = int(chapterStart)
            self.chapter_links = self.chapter_links[self.chapterNum_start - 1:]
        else:
            self.chapterNum_start = 1
            self.currentChapter = 1

        if chapterEnd != '':
            self.chapterNum_end = int(chapterEnd)
            self.chapter_links = self.chapter_links[:abs((int(chapterEnd) + 1) - self.chapterNum_start)]
        else:
            self.chapterNum_end = len(chapters)

        self.msg("Chapter " + str(self.chapterNum_start) + " to Chapter " + str(self.chapterNum_end) + " will be compiled!")

    def compileNovel(self):
        book = epub.EpubBook()
        # add metadata
        book.set_identifier('dr_nyt')
        book.set_title(self.novelName)
        book.set_language('en')
        book.add_author('Unknown')

        #Set the cover if defined by the user
        if self.cover != '':
            book.set_cover("image.jpg", open(self.cover, 'rb').read())

        chapters = []
        #Loop through each link
        for chapter_link in self.chapter_links:

            page = self.scraper.get('https://novelplanet.com' + chapter_link)
            soup = BeautifulSoup(page.text, 'lxml')

            #Add a header for the chapter
            try:
                chapterHead = soup.find('h4').get_text()
                c = epub.EpubHtml(title=chapterHead, file_name='Chapter_' + str(self.currentChapter) + '.xhtml', lang='en')
                content = '<h2>' + chapterHead + '</h4>'
            except:
                c = epub.EpubHtml(title="Chapter "  + str(self.currentChapter), file_name='Chapter_' + str(self.currentChapter) + '.xhtml', lang='en')
                content = "<h2> Chapter "  + str(self.currentChapter) + "</h4>"

            #Get all the paragraphs from the chapter
            paras = soup.find(id="divReadContent").find_all('p')

            #Add each paragraph to the docx file
            for para in paras:
                content += para.prettify()

            content += "<p> </p>"
            content += "<p>Powered by dr_nyt</p>"
            content += "<p>If any errors occur, open an issue here: github.com/dr-nyt/Translated-Novel-Downloader/issues</p>"
            content += "<p>You can download more novels using the app here: github.com/dr-nyt/Translated-Novel-Downloader</p>"

            c.content = u'%s' % content
            chapters.append(c)

            self.msg('Chapter: ' + str(self.currentChapter) + ' compiled!')
            self.currentChapter+=1

        for chap in chapters:
            book.add_item(chap)

        book.toc = (chapters)

        # add navigation files
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        # define css style
        style = '''
    @namespace epub "http://www.idpf.org/2007/ops";
    body {
        font-family: Cambria, Liberation Serif, Bitstream Vera Serif, Georgia, Times, Times New Roman, serif;
    }
    h2 {
         text-align: left;
         text-transform: uppercase;
         font-weight: 200;     
    }
    ol {
            list-style-type: none;
    }
    ol > li:first-child {
            margin-top: 0.3em;
    }
    nav[epub|type~='toc'] > ol > li > ol  {
        list-style-type:square;
    }
    nav[epub|type~='toc'] > ol > li > ol > li {
            margin-top: 0.3em;
    }
    '''

        # add css file
        nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
        book.add_item(nav_css)

        # create spin, add cover page as first page
        book.spine = ['cover', 'nav'] + chapters

        # create epub file
        epub.write_epub(self.novelName + ' ' + str(self.chapterNum_start) + '-' + str(self.chapterNum_end) + '.epub', book, {})

        if not os.path.exists(self.novelName):
            os.mkdir(self.novelName)

        shutil.move(self.novelName + ' ' + str(self.chapterNum_start) + '-' + str(self.chapterNum_end) + '.epub', self.novelName + '/' + self.novelName + ' ' + str(self.chapterNum_start) + '-' + str(self.chapterNum_end) + '.epub')

        self.msg('+'*20)
        self.msg(self.novelName + ' has compiled!') 
        self.msg('+'*20)

versionCheck = 0 #Boolean to check if we have already checked for a newer version or not.

# This function makes a pop up box if the current version is out of date.
def updateMsg():
    popup = Tk()
    popup.wm_title("Update")
    popup.configure(background = "black")
    label = Label(popup, text="New Update Available here: ", bg="black", fg="white", font="none 15")
    link = Label(popup, text="Github/WuxiaNovelDownloader", bg="black", fg="lightblue", font="none 12")
    B1 = Button(popup, text="Okay", command=popup.destroy)
    label.pack(padx=10)
    link.pack(padx=10)
    link.bind("<Button-1>", callback)
    link.bind("<Enter>", partial(color_config, link, "white"))
    link.bind("<Leave>", partial(color_config, link, "lightblue"))
    B1.pack()
    popup.call('wm', 'attributes', '.', '-topmost', '1')
    popup.mainloop()

def color_config(widget, color, event):
    widget.configure(foreground=color)

# Open the link to the novel on a browser
def callback(event):
    webbrowser.open_new(r"https://github.com/dr-nyt/WuxiaWorld-Novel-Downloader")

#Checks if this is the latest version
def versionControl():
    url = 'https://pastebin.com/7HUqzRGT'
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'lxml')
    checkVersion = soup.find(class_='de1')
    if version not in checkVersion:
        updateMsg()

def okButtonClick():
    if tkvar.get() == "NovelPlanet":
        def npcallback():
            npWindow = Tk()
            npGUI = NovelPlanetScraper(npWindow)
            npWindow.mainloop() 
        t = threading.Thread(target=npcallback)
        t.daemon = True
        t.start()
    elif tkvar.get() == "WuxiaWorld":
        def wcallback():
            wWindow = Tk()
            wGUI = WuxiaScraper(wWindow)
            wWindow.mainloop() 
        t = threading.Thread(target=wcallback)
        t.daemon = True
        t.start()
        
############################################################################
#Tkinter
window = Tk()
window.title("Hana Novel Scraper")
window.configure(background = "black")

# Create a Tkinter variable
tkvar = StringVar(window)

# Dictionary with options
choices = {'NovelPlanet', 'WuxiaWorld'}
tkvar.set('NovelPlanet') # set the default option

# Drop down menu
dropMenu = OptionMenu(window, tkvar, *choices)
Label(window, text="Select Source: ", bg="black", fg="white", font="none 16").grid(row=0, column=0, sticky=W, padx=5, pady=10)
dropMenu.grid(row=0, column=1, sticky=W, padx=10, pady=10)

canv1 = Canvas(window, highlightthickness=0, relief='ridge')
canv1.configure(background="black")
canv1.grid(row=1, column=0, columnspan=2)

Button(canv1, text="OK", width=8, command=okButtonClick).pack(pady=5)

# link function to change dropdown
# tkvar.trace('w', change_dropdown)

if versionCheck == 0:
    versionControl()
    versionCheck = 1

window.mainloop()
################################################################################