# Client.py
# Author: Alan Kraut
# This is a program for free online drafting of Magic the Gathering.

from Tkinter import *
from PIL import Image, ImageTk, ImageFont, ImageDraw
from socket import *
from StringIO import StringIO
import random
import json
import urllib
import os
import textwrap
import time

from protocolDefs import *
from parameters import *


class CardImageManager:
    def __init__(self):
        # Image varaibles
        self.images = dict()
        self.thumbnails = dict()
        self.thumbTapped = dict()
        self.thumb180 = dict()
        self.thumb180Tap = dict()


        #load json database
        try:
            f = open(JSON,'r')
        except IOError: # if file doesn't exist
            print("Downloading data about EVERY MAGIC CARD EVER. (~10 MB)")
            print("This may take a little while.")
            print("(Have I mentioned that we're living in the future?)")
            urllib.urlretrieve(JSONURL,JSON)
            f = open(JSON,'r')
        s = f.read()
        f.close()
        self.allSets = json.loads(s)
        self.allCards = dict() # dict of cards by multiverseID


        if not os.path.exists(FONT):
            urllib.urlretrieve(FONTURL,FONT)
        self.font = ImageFont.truetype(FONT,10,encoding = "unic")
        self.charsize = self.font.getsize("k")

    def loadCardBack(self):
        #Special casing for loading card back image
        card = dict()
        setCode = "000"
        multiverseID = "000000"
        card['set'] = setCode
        card['multiverseid'] = multiverseID
        self.allCards[multiverseID] = card

        d = CARDDIR+setCode
        filename = d+"/"+multiverseID+".jpg"
        try:
            temp_image = Image.open(filename)
        except IOError: # Should be thrown if file doesn't exist
            f = StringIO(urllib.urlopen(CARDBACKURL).read())
            temp_image = Image.open(f)
            if not os.path.isdir(d):
                os.makedirs(d)
            temp_image.save(filename,"JPEG")
        self.loadHelper(multiverseID,temp_image)


    def loadMask(self):
        # load mask for finding power/toughness box
        self.powerBoxMask = Image.open(PTBOX)
        # Convert mask to greyscale (mode "L")
        self.powerBoxMask = self.powerBoxMask.convert("L")
        w = CARDWIDTH
        h = CARDHEIGHT
        # Resize to thumbnail size, won't use for full cards
        self.powerBoxMask = self.powerBoxMask.resize((int(w*THUMBSCALE),\
                                                      int(h*THUMBSCALE)),Image.ANTIALIAS)
        # Also get closely bounded mask
        self.smallPowerMask = self.powerBoxMask.crop(self.powerBoxMask.getbbox())
        # These are images we overwrite frequently, may have arbitrary data
        self.powerBackground = Image.new("RGB",(int(w*THUMBSCALE),\
                                                int(h*THUMBSCALE)))
        self.blankImage = Image.new("RGB",(THUMBWIDTH,THUMBHEIGHT))

    def loadCard(self,card):
        print ("startload")
        t = time.time()
        setCode =  card[0:3]
        multiverseID = card[3:]
        d = CARDDIR+setCode
        filename = d+"/"+multiverseID+".jpg"
        if not multiverseID in self.allCards:
            self.loadSetData(setCode)
            print (time.time() - t)
        try:
            temp_image = Image.open(filename)
        except IOError: # Should be thrown if file doesn't exist
            c = None
            for cEntry in self.allSets[setCode]['cards']:
                if cEntry['multiverseid'] == multiverseID:
                    c = cEntry
                    break
            if c == None:
                print("Error finding matching multiverse ID: " + setCode +
                      " " + multiverseID)
            else:
                URL = "http://mtgimage.com/multiverseid/"+\
                      c['multiverseid'].lstrip('0')+".jpg"
                f = StringIO(urllib.urlopen(URL).read())
                temp_image = Image.open(f)
                if not os.path.isdir(d):
                    os.makedirs(d)
                temp_image.save(filename,"JPEG")

        print (time.time()-t)
        self.loadHelper(multiverseID,temp_image)
        return

    def loadHelper(self,multiverseID,temp_image):
        temp_image = temp_image.resize((CARDWIDTH,\
                                        CARDHEIGHT),Image.ANTIALIAS)
        
        self.images[multiverseID] = ImageTk.PhotoImage(temp_image)

        # only retype the textbox text if there is rules text there
        retypeText = THUMBRETYPETEXT and ('text' in self.allCards[multiverseID])\
                     and (not self.allCards[multiverseID]['rarity'] == "Basic Land")
        temp_image = self.makeThumbnail(temp_image,retypeText,multiverseID)

        self.thumbnails[multiverseID] = ImageTk.PhotoImage(temp_image)

        # We use all four cardinal orientations
        temp_image = temp_image.rotate(90)
        self.thumbTapped[multiverseID] = ImageTk.PhotoImage(temp_image)
        temp_image = temp_image.rotate(90)
        self.thumb180[multiverseID] = ImageTk.PhotoImage(temp_image)
        temp_image = temp_image.rotate(90)
        self.thumb180Tap[multiverseID] = ImageTk.PhotoImage(temp_image)
        return

    def loadSetData(self,setCode):
        s = self.allSets[setCode]['cards']
        for card in s:
            card['set'] = setCode
            card['multiverseid'] = str(card['multiverseid']).zfill(6)
            self.allCards[card['multiverseid']] = card

    def makeThumbnail(self,fullImage,rewriteText,multiverseID = None):
        w,h = fullImage.size
        newImage = fullImage.resize((int(w*THUMBSCALE),\
                                     int(h*THUMBSCALE)),Image.ANTIALIAS)
        if(THUMBREMOVETEXT):
            # get the power/toughness box
            powerImage = newImage.crop(self.powerBoxMask.getbbox())

            creature = self.isCreature(multiverseID)
            
            # Get top of card and bottom border, then paste them together
            w,h = newImage.size
            topPixels = int(h*TYPEFRACTION)
            # THUMBHEIGHT is calculated using VBLACKFRACTION, so
            # THUMBHEIGHT-topPixels is the number of pixels we have left
            # for the bottom border. This is done so that the height of
            # the new image will exactly match THUMBHEIGHT, regardless of
            # rounding.
            bottomBorder = newImage.crop((0,h-(THUMBHEIGHT-topPixels),\
                                          w,h))
            newImage = newImage.crop((0,0,w,topPixels))

            self.blankImage.paste(newImage,(0,0)) # Paste into top-left corner
            self.blankImage.paste(bottomBorder,(0,topPixels)) # Paste below that

            if creature:
                # add on power/toughness box
                # horizontal location of top-left corner of box
                x = int(w*POWERBOX_X_FRACTION)
                # vertical location of top-left corner of box
                y = int(h*POWERBOX_Y_FRACTION)
                self.blankImage.paste(powerImage,(x,y),self.smallPowerMask)

            newImage = self.blankImage
        elif rewriteText:
            textBox = Image.new("RGB",(THUMBTEXTWIDTH,THUMBTEXTHEIGHT),
                                TEXTBOXCOLOR)
            text = self.allCards[multiverseID]['text']
            chars = int(THUMBTEXTWIDTH/self.charsize[0])
            lines = textwrap.wrap(text,width = chars)
            draw = ImageDraw.Draw(textBox)
            y = 0
            for line in lines:
                draw.text((1,y),line,font = self.font, fill = "Black")
                y = y + int(self.charsize[1]*TEXTLINEFRACTION)
            newImage.paste(textBox,(int(THUMBWIDTH*HBORDERFRACTION),
                                    int(THUMBHEIGHT*TYPEFRACTION)))
            
            
        return newImage

    def isCreature(self,multiverseID):
        return 'toughness' in self.allCards[multiverseID]
        #Obsolete code for using image processing to determine if it's a creature
##        # Convert to greyscale
##        im = im.convert("L")
##        w,h = im.size
##
##        # There should be a strong edge between 5 and 6 pixels from the bottom
##        # average pixel differences along there, NOT doing abs value
##        pix = im.load()
##
##        
##        # search the bottom half of the image for a strong edge
##        # ignoring the bottom two rows because of edge effects of downscaling
##        for row in range(h-3,int(h/2),-1):
##            diff = 0
##            for col in range(w):
##                diff = diff + (pix[col,row]-pix[col,row-1])
##            aveDiff = diff/w
##            if abs(aveDiff)> CREATURE_EDGE_THRESHOLD:
##                return True
##        return False


class ChatBox(Frame):
    def __init__(self,master,sendType = WAITING):
        Frame.__init__(self,master)

        self.sendType = sendType

        # We will be using the frame to set the size
        self.pack_propagate(0)

        
        # create scrollbar
        self.scrollbar = Scrollbar(self)
        
        
        # create text box
        self.display = Text(self, yscrollcommand = self.scrollbar.set)
        self.display.tag_config("indent",lmargin2 = 20)
        self.scrollbar.config(command = self.display.yview)

        self.display.unbind("<Key>")
        self.display.unbind("<Button-1>")


        # create entry box
        self.entry = Entry(self)
        self.entry.bind("<Return>",self.sendMessageEvent)

        # set sizes to minimum, then pack to fill frame
        self.entry.config(width = 1)
        self.display.config(width = 1, height = 1)

        self.entry.pack(side = BOTTOM, fill = X)
        self.scrollbar.pack(side = RIGHT, fill = Y)
        self.display.pack(side = TOP, fill = BOTH, expand = 1)
        


    def sendMessage(self, data):
        if len(data) == 0:
            return
        elif data[0] == '/':
            if data[1:6] == 'name ':
                root.send(SETTAG + data[6:])
            elif data[1:5] == 'raw ':
                root.send(data[5:])
            elif data[1:6] == 'yell ':
                root.send(MESSAGE + ALL + data[6:])
            else:
                self.recvMessage("Command not recognized.")
        else:
            root.send(MESSAGE +self.sendType+ data)
        self.entry.delete(0,END)

    def sendMessageEvent(self,event):
        data = self.entry.get()
        self.sendMessage(data)

    def recvMessage(self, data):
        self.display.insert(END, data+'\n', "indent")
        self.display.see(END+ "-2c")

    def resize(self,width,height):
        self.config(width = width, height = height)



class Deck_DeckBox(Frame):
    def __init__(self,master):
        Frame.__init__(self,master)
        self.config(height = DRAFT_PICKEDHEIGHT, \
                    width = DRAFT_PICKEDWIDTH + CARDWIDTH)
        self.config(bd = 2, relief = RIDGE)
        self.config(bg = 'White')
        self.cardLabels = []

        self.cardsPerCol = (DRAFT_PICKEDHEIGHT - THUMBHEIGHT + THUMBTITLEHEIGHT)\
                           / THUMBTITLEHEIGHT # Amount of space we have for
                                              # headers, divided by the width
                                              # of a header

    def addCard(self,card):

        self.cardLabels.append(SmallCard(self, card))

        row = (len(self.cardLabels)-1)%self.cardsPerCol
        col = int((len(self.cardLabels)-1)/self.cardsPerCol)
        y = row*THUMBTITLEHEIGHT
        x = col*THUMBWIDTH*1.1 #leave some space between columns
        
        # We're anchoring at the center, so we need to add these to where we
        # place the card.
        xoffset = THUMBWIDTH*0.5
        yoffset = THUMBHEIGHT*0.5
                          
        
        self.cardLabels[-1].config(bd = 0)
        self.cardLabels[-1].place(x = x + xoffset, y = y + yoffset, \
                                  anchor = CENTER)
        self.cardLabels[-1].updatePosition()
        self.cardLabels[-1].enableMovement()

        self.cardLabels[-1].bind("<Double-Button-1>",self.moveToAvail)

    def removeCard(self,cardLabel):
        self.cardLabels.remove(cardLabel)
        cardLabel.destroy()

    def moveToAvail(self,event):
        cardLabel = event.widget
        self.removeCard(cardLabel)

        self.master.deck_moveToAvail(cardLabel.card)

class Deck_LandOptions(Frame):
    def __init__(self,master):
        Frame.__init__(self,master)

        # these could be stored better in an array or dictionary or something        
        self.plainsLabel = Label(self, text = "Plains:")
        self.islandLabel = Label(self, text = "Islands:")
        self.swampLabel = Label(self, text = "Swamps:")
        self.mountainLabel = Label(self, text = "Mountains:")
        self.forestLabel = Label(self, text = "Forests:")

        self.plainsBox = Entry(self, width = 2)
        self.plainsBox.insert(END,'0')
        self.islandBox = Entry(self, width = 2)
        self.islandBox.insert(END,'0')
        self.swampBox = Entry(self, width = 2)
        self.swampBox.insert(END,'0')
        self.mountainBox = Entry(self, width = 2)
        self.mountainBox.insert(END,'0')
        self.forestBox = Entry(self, width = 2)
        self.forestBox.insert(END,'0')

        self.challengeButton = Button(self, text = "Challenge", command =\
                                      self.master.deck_challenge)

        self.plainsLabel.grid(row = 0, column = 0, sticky = E)
        self.islandLabel.grid(row = 1, column = 0, sticky = E)
        self.swampLabel.grid(row = 2, column = 0, sticky = E)
        self.mountainLabel.grid(row = 0, column = 2, sticky = E)
        self.forestLabel.grid(row = 1, column = 2, sticky = E)
        
        self.plainsBox.grid(row = 0, column = 1, padx = 3)
        self.islandBox.grid(row = 1, column = 1, padx = 3)
        self.swampBox.grid(row = 2, column = 1, padx = 3)
        self.mountainBox.grid(row = 0, column = 3, padx = 3)
        self.forestBox.grid(row = 1, column = 3, padx = 3)

        self.challengeButton.grid(row = 3, column = 0, \
                                  columnspan = 4, pady = 20)
        
    def getLandData(self):
        print("Getting land data")
        print self.plainsBox.get()
        plains = self.plainsBox.get().zfill(2)
        print plains
        islands = self.islandBox.get().zfill(2)
        swamps = self.swampBox.get().zfill(2)
        mountains = self.mountainBox.get().zfill(2)
        forests = self.forestBox.get().zfill(2)

        data = ''
        for i in range(5):
            if i == PLAINS:
                data = data+plains
            elif i == ISLAND:
                data = data+islands
            elif i == SWAMP:
                data = data+swamps
            elif i == MOUNTAIN:
                data = data+mountains
            elif i == FOREST:
                data = data+forests

        return data
        
                                 

class Draft_Card(Label):
    def __init__(self, master):
        Label.__init__(self,master)
        self.config(bd = 2, relief = SUNKEN)
        self.show(BACK)

    def show(self,card):
        multiverseID = card[3:]
        if not multiverseID in cards.thumbnails.keys():
            cards.loadCard(card)
            
        self.config(image = cards.images[multiverseID])

class Draft_Menu(Menu):
    def __init__(self, master):
        Menu.__init__(self,master)

        #Setup menus
        self.filemenu = Menu(self)
        self.add_cascade(label = "File", menu = self.filemenu)
        self.filemenu.add_command(label = "Quit", command = root.quitGame)

##        self.gamemenu = Menu(self)
##        self.add_cascade(label = "Game", menu = self.gamemenu)
##        self.gamemenu.add_command(label = "Ready", command = self.setReady)
##        self.gamemenu.add_command(label = "Not ready", command = self.setUnready)

    def setReady(self):
        root.send(READINESS + "1")

    def setUnready(self):
        root.send(READINESS + "0")
    
    
class Draft_Pack(Frame):
    def __init__(self,master):
        Frame.__init__(self,master)
        self.config(bd = 2, relief = RIDGE)
        self.config(bg = 'White')

    def display(self,pack):
        if pack == None:
            pack = []
        self.pack = pack
        # Get rid of the old cards
        for child in self.winfo_children():
            child.destroy()

        # For each card, if we don't already have the image set, get it.
        # Then make a label.
        self.cardLabels = [None]*15
        n = DRAFT_PACK_CARDSPERROW
        i = 0
        for card in pack:
            self.cardLabels[i] = SmallCard(self, card)
            self.cardLabels[i].grid(row = int(i/n), column = i%n)
            self.cardLabels[i].config(bg = "White")
            self.cardLabels[i].bind("<Double-Button-1>",self.pickCard)
            i = i+1


        # This fills the rest of the panel with blank white JPEGs that don't
        # do anything. Why? So it doesn't shrink when you get fewer cards.
        whiteImage = Image.new("RGB",(THUMBWIDTH,THUMBHEIGHT),"White")
        whiteImage = ImageTk.PhotoImage(whiteImage)
        for j in range(len(pack),15):
            self.cardLabels[i] = Label(self, image = whiteImage)
            self.cardLabels[i].config(bg = "White")
            self.cardLabels[i].grid(row = int(i/n), column = i%n)
            i = i+1
        

    def pickCard(self,event):
        index = self.cardLabels.index(event.widget)
        card = self.pack[index]
        self.master.draft_pickCard(card)

    def showBigCard(self, event):
        index = self.cardLabels.index(event.widget)
        card = self.pack[index]
        self.master.showBigCard(card)
            
            
        

class Draft_PickedCards(Frame):
    def __init__(self,master):
        Frame.__init__(self,master)
        self.config(height = DRAFT_PICKEDHEIGHT, width = DRAFT_PICKEDWIDTH)
        self.config(bd = 2, relief = RIDGE)
        self.config(bg = 'White')
        self.cardLabels = []
        self.canMoveToDeck = False # Initially the deck window doesn't exist

        self.cardsPerCol = (DRAFT_PICKEDHEIGHT - THUMBHEIGHT + THUMBTITLEHEIGHT)\
                           / THUMBTITLEHEIGHT # Amount of space we have for
                                              # headers, divided by the width
                                              # of a header

    def addCard(self,card):

        self.cardLabels.append(SmallCard(self, card))

        row = (len(self.cardLabels)-1)%self.cardsPerCol
        col = int((len(self.cardLabels)-1)/self.cardsPerCol)
        y = row*THUMBTITLEHEIGHT
        x = col*THUMBWIDTH*1.1 #leave some space between columns

        # We're anchoring at the center, so we need to add these to where we
        # place the card.
        xoffset = THUMBWIDTH*0.5
        yoffset = THUMBHEIGHT*0.5
        
        self.cardLabels[-1].config(bd = 0)
        self.cardLabels[-1].place(x = x + xoffset, y = y + yoffset, \
                                  anchor = CENTER)
        self.cardLabels[-1].updatePosition()
        self.cardLabels[-1].enableMovement()

        if self.canMoveToDeck:
            self.cardLabels[-1].bind("<Double-Button-1>",self.moveToDeck)

    def removeCard(self,cardLabel):
        self.cardLabels.remove(cardLabel)
        cardLabel.destroy()
        

    def enableMoveToDeck(self):
        self.canMoveToDeck = True

        for card in self.cardLabels:
            card.bind("<Double-Button-1>",self.moveToDeck)

    def moveToDeck(self,event):
        cardLabel = event.widget
        self.removeCard(cardLabel)

        self.master.deck_moveToDeck(cardLabel.card)

class Game_DeckWindow(Toplevel):
    def __init__(self,master,deck,playchar):
        Toplevel.__init__(self,master)
        
        self.cardLabels = []
        self.playchar = playchar # This is used to tag the messages we send
                                 # back to the server with which player's
                                 # deck we're looking at.

        self.cardsPerCol = GAME_DECKROWS # Arbitrary number
        self.cols = len(deck)/self.cardsPerCol+1

        self.backing = Frame(self)
        height = self.cardsPerCol*THUMBTITLEHEIGHT+THUMBHEIGHT
        width = int(self.cols * THUMBWIDTH * 1.1)
        
        self.backing.config(height = height, width = width)
        self.backing.config(bd = 2, relief = RIDGE)
        self.backing.config(bg = 'White')

        # All cards will be placed on top of this
        self.topOfBottom = self.backing

        self.backing.place(x = 0, y = 0)
        self.config(width = width, height = height)

        print deck
        for card in deck:
            print card
            self.addCard(card)
            

    def addCard(self,card):
        self.cardLabels.append(SmallCard(self, card))

        row = (len(self.cardLabels)-1)%self.cardsPerCol
        col = int((len(self.cardLabels)-1)/self.cardsPerCol)
        y = row*THUMBTITLEHEIGHT
        x = col*THUMBWIDTH*1.1 #leave some space between columns

        # We're anchoring at the center, so we need to add these to where we
        # place the card.
        xoffset = THUMBWIDTH*0.5 + 2
        yoffset = THUMBHEIGHT*0.5 + 2
        
        self.cardLabels[-1].config(bd = 0)
        self.cardLabels[-1].place(x = x + xoffset, y = y + yoffset, \
                                  anchor = CENTER)
        self.cardLabels[-1].updatePosition(sendNote = False)
        self.cardLabels[-1].bind("<Double-Button-1>", self.toPlay)
        self.cardLabels[-1].bind("<Shift-Button-1>",self.toHand)

    def removeCard(self,cardLabel):
        self.cardLabels.remove(cardLabel)
        cardLabel.destroy()

    def showBigCard(self,card):
        self.master.showBigCard(card)

    def toHand(self, event):
        cardLabel = event.widget
        self.master.putInHand(cardLabel.card)
        root.send(DECKREMOVE + self.playchar + cardLabel.card)
        self.removeCard(cardLabel)

    def toPlay(self, event):
        cardLabel = event.widget
        self.master.putInPlay(cardLabel.card)
        root.send(DECKREMOVE + self.playchar + cardLabel.card)
        self.removeCard(cardLabel)
              
        
        

class Game_Display(Frame):
    def __init__(self,master):
        Frame.__init__(self,master)

        self.config(width = GAME_INFOBARWIDTH, height = GAME_PLAYHEIGHT)
        self.opponentLife = 20
        self.opponentDeck = 0
        self.opponentHand = 0

        self.life = 20
        self.deck = 0

        self.opponentLifeLabel = Label(self, text = "  Life  \n" + \
                                    str(self.opponentLife))
        self.opponentDeckLabel = Label(self, text = "Deck\n"+ \
                                       str(self.opponentDeck))
        self.opponentHandLabel = Label(self, text = "Hand\n"+ \
                                       str(self.opponentHand))
        
        self.lifeFrame = Frame(self)
        self.lifeBox = Entry(self.lifeFrame, width = 3)
        self.lifeBox.insert(END,str(self.life))
        self.lifeBox.bind("<Key>",self.life_updateHelper)
        self.lifeUp = Button(self.lifeFrame, text = "+", \
                             command = self.life_add)
        self.lifeDown = Button(self.lifeFrame, text = "-", \
                               command = self.life_sub)

        self.lifeDown.pack(side = LEFT)
        self.lifeBox.pack(side = LEFT)
        self.lifeUp.pack(side = LEFT)

        self.deckLabel = Label(self, text = "Deck\n"+str(self.deck))

        self.opponentLifeLabel.place(x = GAME_LABELOFFSET, y = 0)
        self.opponentDeckLabel.place(x = GAME_LABELOFFSET, y = GAME_LABELSPACE)
        self.opponentHandLabel.place(x = GAME_LABELOFFSET, y = 2*GAME_LABELSPACE)
        
        self.lifeFrame.place(x = 0, y = GAME_PLAYHEIGHT / 2)
        self.deckLabel.place(x = GAME_LABELOFFSET, \
                             y = GAME_PLAYHEIGHT/2 + GAME_LABELSPACE)

    def life_add(self):
        self.life = self.life + 1
        self.lifeBox.delete(0,END)
        self.lifeBox.insert(END, str(self.life))
        self.life_update()

    def life_sub(self):
        self.life = self.life - 1
        self.lifeBox.delete(0,END)
        self.lifeBox.insert(END, str(self.life))
        self.life_update()

    def life_update(self):
        self.life = int(self.lifeBox.get())
        root.send(LIFE + str(self.life).zfill(3))

    def life_updateHelper(self,event):
        self.lifeUpdateID = self.after(1,self.life_update)

    def life_updateOpponent(self):
        self.opponentLifeLabel.config(text = "  Life  \n" + \
                                    str(self.opponentLife))

    def deck_update(self):
        self.deckLabel.config(text = "Deck\n"+str(self.deck))
        self.opponentDeckLabel.config(text = "Deck\n"+ \
                                       str(self.opponentDeck))

    def hand_update(self):
        self.opponentHandLabel.config(text = "Hand\n"+ \
                                       str(self.opponentHand))

    
class Game_Hand(Frame):
    def __init__(self,master):
        Frame.__init__(self,master)
        self.config(width = GAME_HANDWIDTH, height = GAME_HANDHEIGHT)
        self.config(bd = 2, relief = RIDGE)
        self.config(bg = 'White')
        self.cardLabels = []

        # We're anchoring at the center, so we need to add these to where we
        # place the card.
        self.xoffset = THUMBWIDTH*0.5
        self.yoffset = THUMBHEIGHT*0.5
        

    def addCard(self,card):

        self.cardLabels.append(SmallCard(self, card))

        pos = (len(self.cardLabels)-1)
        y = pos*THUMBTITLEHEIGHT
        
        self.cardLabels[-1].config(bd = 0)
        self.cardLabels[-1].place(x = self.xoffset, y = y + self.yoffset, \
                                  anchor = CENTER)
        self.cardLabels[-1].bind("<Shift-Button-1>", self.bringToFront)
        self.cardLabels[-1].bind("<Double-Button-1>",self.play)
        self.cardLabels[-1].enableGameChecks()

        self.master.me.handSize = self.master.me.handSize + 1
        root.send(CHNGHANDSIZE+ '+')


    def removeCard(self,cardLabel):
        self.cardLabels.remove(cardLabel)
        cardLabel.destroy()
        self.redisplay()

        self.master.me.handSize = self.master.me.handSize - 1
        root.send(CHNGHANDSIZE+ '-')

    def bringToFront(self,event):
        frontCard = event.widget
        self.cardLabels.remove(frontCard)
        self.cardLabels.append(frontCard)
        self.redisplay()

    def play(self,event):
        cardLabel = event.widget
        card = cardLabel.card

        self.removeCard(cardLabel)

        self.master.putInPlay(card)
        
        
    def redisplay(self):
        
        for i in range(len(self.cardLabels)):
            y = i*THUMBTITLEHEIGHT
            self.cardLabels[i].place(x = self.xoffset, y = y+self.yoffset,\
                                     anchor = CENTER)
            self.cardLabels[i].lift()


class Game_Messages(Frame):
    def __init__(self,master):
        Frame.__init__(self,master)
        self.messageBoxes = []
        for i in range(GAME_MESSAGENUM):
            newBox = Entry(self)
            newBox.config(width = GAME_MESSAGEWIDTH)
            newBox.bind("<Return>",self.send)
            newBox.pack(pady = 3)
            
            # These pre-made messages are defined
            # at the top of the file
            if i < len(GAME_MESSAGES):
                newBox.insert(END,GAME_MESSAGES[i])
            self.messageBoxes.append(newBox)

    def send(self, event):
        message = event.widget.get()
        if len(message) == 0:
            return
        else:
            self.master.chatBox.sendMessage(message)

class Game_PlayArea(Frame):
    def __init__(self,master):
        Frame.__init__(self,master)
        self.config(width = GAME_PLAYWIDTH, height = GAME_PLAYHEIGHT)
        self.config(bd = 2, relief = RIDGE)
        self.config(bg = 'White')
        self.cardLabels = []
        self.cardIDList = []
        self.tapHelperQueue = []

        self.cardsPerCol = (GAME_PLAYHEIGHT - THUMBHEIGHT + THUMBTITLEHEIGHT)\
                           / THUMBTITLEHEIGHT # Amount of space we have for
                                              # headers, divided by the width
                                              # of a header
                                              
        self.dividerLabel = Label(self, width = GAME_PLAYWIDTH, height = 2,\
                                  bd = 0, bg = 'Black', bitmap = "gray75")
        self.topOfBottom = self.dividerLabel
        self.dividerLabel.place(x = 0, y = GAME_PLAYHEIGHT/2, anchor = W)

    def addCard(self,card,flipped = False, newID = None, sendNote = True):
        # Find what the ID of the new card will be
        if newID == None:
            for i in range(1000):
                if not i in self.cardIDList:
                    newID = i
                    break
        elif newID in self.cardIDList:
            self.master.chatBox.recvMessage("Encountered ID the same as " +\
                    "another card in play. Two cards were likely played near-"+\
                    "simultaneously by different players. Returning all "+\
                    "recently played cards to one person's hand and playing "+\
                    "them again should fix the problem, but I don't know for "+\
                    "sure because this was a hard error to generate for testing.")

        self.cardIDList.append(newID)
        self.cardLabels.append(SmallCard(self, card, flipped))
        self.cardLabels[-1].ID = newID
        self.cardLabels[-1].enableSendPosition()
        if sendNote:
            if flipped:
                fchar = "F"
            else:
                fchar = "R"
            root.send(NEWPLAYCARD + fchar + str(newID).zfill(3) + card) 
        
        xoffset = THUMBWIDTH*0.5
        yoffset = THUMBHEIGHT*0.5
        
        self.cardLabels[-1].config(bd = 0)
        # Always place at lower left
        self.cardLabels[-1].place(x = xoffset, y = GAME_PLAYHEIGHT - yoffset, \
                                  anchor = CENTER)
        
        self.cardLabels[-1].updatePosition(sendNote = sendNote)
        self.cardLabels[-1].enableMovement()
        self.cardLabels[-1].enableTopRotate()
        self.cardLabels[-1].enableGameChecks()
        

        # This should probably be done as a function of the card, not of the
        # play area. It doesn't really matter, but for consistency.
        self.cardLabels[-1].bind("<Double-Button-1>",self.tapToggle)

    def removeCard(self,cardLabel, sendNote = True):
        self.cardLabels.remove(cardLabel)
        self.cardIDList.remove(cardLabel.ID)
        if sendNote:
            root.send(DELPLAYCARD + str(cardLabel.ID).zfill(3))
        cardLabel.destroy()

    def removeCardID(self, cardID):
        for cardLabel in self.cardLabels:
            if cardLabel.ID == cardID:
                self.removeCard(cardLabel, sendNote = False)

    def flipCardID(self,cardID):
        for cardLabel in self.cardLabels:
            if cardLabel.ID == cardID:
                cardLabel.flipped = not cardLabel.flipped
                cardLabel.updateImage()

    def setCardPosition(self,cardID,x,y):
        for cardLabel in self.cardLabels:
            if cardLabel.ID == cardID:
                cardLabel.place(x = x, y = y)
                cardLabel.updatePosition(sendNote = False)

    def tapCardID(self, cardID):
        for cardLabel in self.cardLabels:
            if cardLabel.ID == cardID:
                cardLabel.tapped = not cardLabel.tapped
                cardLabel.updateImage()
                                    

    def tapToggle(self,event):
        cardLabel = event.widget
        cardLabel.tapped = not cardLabel.tapped
        cardLabel.updateImage()
        cardLabel.unbind("<Double-Button-1>")
        self.tapHelperQueue.append(cardLabel)
        self.after(500,self.tapToggleHelper)
        root.send(TAPTOGGLE + str(cardLabel.ID).zfill(3))

    def tapToggleHelper(self):
        cardLabel = self.tapHelperQueue.pop(0)
        cardLabel.bind("<Double-Button-1>",self.tapToggle)

        

class Game_Tools(Frame):
    def __init__(self,master):
        Frame.__init__(self,master)

        self.buttons = []
        for row in range(3):
            for column in range(4):
                button = Button(self, text = "Button " + \
                                str(4*row + column + 1))
                button.grid(row = row, column = column, pady = 2, padx = 2)
                self.buttons.append(button)

        self.buttons[0].config(text = "Draw", command = self.draw)
        self.buttons[1].config(text = "Move to\nTop\nof Deck", \
                               command = self.deckTop)
        self.buttons[2].config(text = "Move to\nBottom\nof Deck",\
                               command = self.deckBottom)
        self.buttons[3].config(text = "Move to\nHand",\
                               command = self.moveToHand)
        self.buttons[4].config(text = "Flip (Play\nFace Down)",\
                               command = self.flip)
        self.buttons[5].config(text = "Peek at\nFlipped",\
                               command = self.peek)
        self.buttons[6].config(text = "Create\nToken",\
                               command = self.tokenMake)
        self.buttons[7].config(text = "Destroy\nToken",\
                               command = self.tokenDestroy)
        self.buttons[8].config(text = "Shuffle", command = self.shuffle)
        self.buttons[9].config(text = "Look at\nDeck",\
                               command = self.seeDeck)
        self.buttons[10].config(text = "Look at\nOpponent's Deck",\
                                command = self.seeOpponentDeck)
        

    def draw(self):
        root.send(DRAW)

    def deckBottom(self):
        self.unpressAll()
        self.master.moveToDeckBottom = True
        self.buttons[2].config(relief = SUNKEN)
        self.buttons[2].config(command = self.unpressAll)

    def deckTop(self):
        self.unpressAll()
        self.master.moveToDeckTop = True
        self.buttons[1].config(relief = SUNKEN)
        self.buttons[1].config(command = self.unpressAll)

    def moveToHand(self):
        self.unpressAll()
        self.master.moveToHand = True
        self.buttons[3].config(relief = SUNKEN)
        self.buttons[3].config(command = self.unpressAll)

    def flip(self):
        self.unpressAll()
        self.master.flipCard = True
        self.buttons[4].config(relief = SUNKEN)
        self.buttons[4].config(command = self.unpressAll)

    def peek(self):
        self.unpressAll()
        self.master.peekAtCard = True
        self.buttons[5].config(relief = SUNKEN)
        self.buttons[5].config(command = self.unpressAll)

    def shuffle(self):
        root.send(SHUFFLE)

    def seeDeck(self):
        root.send(VIEWDECK + "0")

    def seeOpponentDeck(self):
        root.send(VIEWDECK + "1")

    def tokenMake(self):
        self.master.playBox.addCard(BACK)

    def tokenDestroy(self):
        self.unpressAll()
        self.master.tokenDestroy = True
        self.buttons[7].config(relief = SUNKEN)
        self.buttons[7].config(command = self.unpressAll)

    def unpressAll(self):
        # deckTop button
        self.master.moveToDeckTop = False
        self.buttons[1].config(relief = RAISED)
        self.buttons[1].config(command = self.deckTop)

        # deckBottom
        self.master.moveToDeckBottom = False
        self.buttons[2].config(relief = RAISED)
        self.buttons[2].config(command = self.deckBottom)

        # hand
        self.master.moveToHand = False
        self.buttons[3].config(relief = RAISED)
        self.buttons[3].config(command = self.moveToHand)

        # flip
        self.master.flipCard = False
        self.buttons[4].config(relief = RAISED)
        self.buttons[4].config(command = self.flip)

        # peek
        self.master.peekAtCard = False
        self.buttons[5].config(relief = RAISED)
        self.buttons[5].config(command = self.peek)
        

        # token destroy
        self.master.tokenDestroy = False
        self.buttons[7].config(relief = RAISED)
        self.buttons[7].config(command = self.tokenDestroy)
                
        

class Game_Window(Toplevel):
    def __init__(self,master, me, opponent):
        Toplevel.__init__(self,master)
        self.title("Odyssey Game: " + me.tag + "vs." + opponent.tag)

        # make game state variables
        self.me = me
        self.opponent = opponent
        
        self.moveToDeckTop = False
        self.moveToDeckBottom = False
        self.moveToHand = False
        self.flipCard = False
        self.peekAtCard = False
        self.tokenDestroy = False

        
        # create widgets
        self.playBox = Game_PlayArea(self)
        self.handBox = Game_Hand(self)
        
        self.chatBox = ChatBox(self, sendType = GAME)
        self.chatBox.resize(GAME_CHATWIDTH,GAME_CHATHEIGHT)
        
        self.cardBox = Draft_Card(self)
        self.displayBar = Game_Display(self)
        self.toolBox = Game_Tools(self)
        self.messagesBox = Game_Messages(self)
        
        self.playBox.grid(row = 0, column= 3, rowspan = 3)
        self.handBox.grid(row = 2, column = 0, rowspan = 2)
        self.displayBar.grid(row = 0, column = 2, rowspan = 3)
        self.chatBox.grid(row = 3, column = 2, columnspan = 2)
        self.cardBox.grid(row = 0, column = 0, columnspan = 2)
        self.toolBox.grid(row = 1, column = 0, columnspan = 2)
        self.messagesBox.grid(row = 2, column = 1, rowspan = 2)
                                    


    def showBigCard(self,card):
        self.cardBox.show(card)

    def showDeck(self, deck,playchar):
        self.deckWindow = Game_DeckWindow(self, deck, playchar)

    def putInHand(self,card):
        self.handBox.addCard(card)

    def putInPlay(self,card):
        self.playBox.addCard(card)

    def updateDeckSizes(self):
        self.displayBar.opponentDeck = self.opponent.deckSize
        self.displayBar.deck = self.me.deckSize
        self.displayBar.deck_update()

    def updateHandSizes(self):
        self.displayBar.opponentHand = self.opponent.handSize
        self.displayBar.hand_update()

    def updateLife(self):
        print(self.opponent.life)
        self.displayBar.opponentLife = self.opponent.life
        self.displayBar.life_updateOpponent()
        

        
    


class Player():
    def __init__(self,ID,tag):
        self.ID = ID
        self.tag = tag
        self.room = None
        self.ready = False
        self.next = None #player to the left
        self.prev = None #player to the right

        # These are used during games
        self.deckSize = 0
        self.handSize = 0
        self.life = 20

# This is a small class that allows the player box to be
# sized in pixels.
class PlayerBox(Frame):
    def __init__(self,master):
        Frame.__init__(self,master)

        self.list = Listbox(self)

        # Makes frame not resize to fit contents
        self.pack_propagate(0)

        self.list.pack(side = TOP, fill = BOTH, expand = 1)

    # These functions simply pass calls on to the Listbox
    def curselection(self):
        return self.list.curselection()

    def get(self, index):
        return self.list.get(index)

    def delete(self, start, end):
        return self.list.delete(start, end)

    def insert(self, index, message):
        return self.list.insert(index, message)

    def resize(self, width, height):
        self.config(width = width, height = height)

class SmallCard(Label):
    def __init__(self,master,card, flipped = False):
        Label.__init__(self,master)
        multiverseID = card[3:]
        if not multiverseID in cards.thumbnails.keys():
            cards.loadCard(card)

        self.card = card
        self.multiverseID = multiverseID
        self.bind("<Enter>", self.showBigCard)
        self.bind("<Button-1>", self.click)
        self.gameChecks = False
        self.canMove = False
        self.topRotate = False
        self.sendPosition = False
        
        self.flipped = flipped
        self.rotated = False
        self.tapped = False
        self.updateImage()

        self.ID= None
        

    # This function returns a list of all the cards which are touching
    # this one, either directly or through other cards. It is here rather
    # than a level up, because it is used for the behavior of moving cards.
    def connectedCards(self):
        # Retrieve a list of cards in the master widget
        cards = []
        for card in self.master.cardLabels:
            cards.append(card)

            
        cards.remove(self)
        
        return self.connectedCardsHelper([], cards) + [self]

    def connectedCardsHelper(self, foundCards, iteratorList):
        cardsLeft = []
        for card in iteratorList:
            cardsLeft.append(card)

        for card in iteratorList:
            # This is a hack to modify a list we're iterating over
            if card in cardsLeft:
                inX = not(self.right < card.left or card.right < self.left)
                inY = not(self.top > card.bottom or card.top > self.bottom)

                # If the cards are touching
                if inX and inY:
                    foundCards.append(card)
                    cardsLeft.remove(card)
                    moreFound = card.connectedCardsHelper([],cardsLeft)
                    for newCard in moreFound:
                        foundCards.append(newCard)
                        cardsLeft.remove(newCard)
                        
        return foundCards
            
        
        
    def click(self, event):
        if self.gameChecks:
            top = self.winfo_toplevel()
            if top.moveToDeckTop:
                root.send(DECKTOP + self.card)
                self.master.removeCard(self)
                return
            elif top.moveToDeckBottom:
                root.send(DECKBOTTOM+self.card)
                self.master.removeCard(self)
                return
            elif top.moveToHand:
                self.winfo_toplevel().handBox.addCard(self.card)
                self.master.removeCard(self)
                return
            elif top.flipCard:
                # In this case need to special-case if it's in the hand
                if self.master.__class__ == Game_Hand:
                    self.master.removeCard(self)
                    top.playBox.addCard(self.card, flipped = True)
                else:
                    if self.flipped:
                        self.flipped = False                           
                    else:
                        self.flipped = True
                    root.send(FLIPTOGGLE + str(self.ID).zfill(3))
                    self.updateImage()
                        
            elif top.peekAtCard:
                top.showBigCard(self.card)

            elif top.tokenDestroy:
                if self.card == BACK:
                    self.master.removeCard(self)
                    
                
        if self.canMove:
            self.clickedx = event.x_root
            self.clickedy = event.y_root
            info = self.place_info()
            self.oldx = int(info['x'])
            self.oldy = int(info['y'])
            self.bind("<B1-Motion>", self.drag)
            self.bind("<ButtonRelease-1>", self.dragEnd)

    def drag(self, event):
        movex = event.x_root-self.clickedx
        movey = event.y_root-self.clickedy
        newx = self.oldx + movex
        newy = self.oldy + movey
        if newx < -(THUMBWIDTH/2) + 4:
            newx = -(THUMBWIDTH/2) + 4
        elif newx > int(self.master.cget('width')) + (THUMBWIDTH/2) - 8:
            newx = int(self.master.cget('width')) + (THUMBWIDTH/2) - 8
        if newy < -(THUMBHEIGHT/2) + 4:
            newy = -(THUMBHEIGHT/2) + 4
        elif newy > int(self.master.cget('height')) + (THUMBHEIGHT/2) - 8:
            newy = int(self.master.cget('height')) + (THUMBHEIGHT/2) - 8
        self.place(x = newx, y = newy, anchor = CENTER)
        self.updatePosition()

    def dragEnd(self,event):
        self.unbind("<B1-Motion>")
        self.unbind("<ButtonRelease-1>")
        self.updatePosition()

    def enableMovement(self):
        self.canMove = True
        
    def enableGameChecks(self):
        self.gameChecks = True

    def enableSendPosition(self):
        self.sendPosition = True

    def enableTopRotate(self):
        self.topRotate = True

    def showBigCard(self,event):
        if not self.flipped:
            self.winfo_toplevel().showBigCard(self.card)

    def updateImage(self):
        if self.flipped:
            if self.rotated:
                if self.tapped:
                    self.configure(image = cards.thumb180Tap[BACK])
                else:
                    self.configure(image = cards.thumb180[BACK])
            else:
                if self.tapped:
                    self.configure(image = cards.thumbTapped[BACK])
                else:
                    self.configure(image = cards.thumbnails[BACK])
        else:
            if self.rotated:
                if self.tapped:
                    self.configure(image = cards.thumb180Tap[self.multiverseID])
                else:
                    self.configure(image = cards.thumb180[self.multiverseID])
            else:
                if self.tapped:
                    self.configure(image = cards.thumbTapped[self.multiverseID])
                else:
                    self.configure(image = cards.thumbnails[self.multiverseID])
                    

    # This function keeps running track of the position in the master
    # of the edges of the card
    def updatePosition(self, sendNote = True):
        cardInfo = self.place_info()
        x = int(cardInfo['x'])
        y = int(cardInfo['y'])
        self.left = x - (THUMBWIDTH/2)
        self.top = y - (THUMBHEIGHT/2)
        self.right = self.left + THUMBWIDTH
        self.bottom = self.top + THUMBHEIGHT
        

        if self.topRotate and y < (GAME_PLAYHEIGHT/2):
            rotate = True
        else:
            rotate = False


        if not rotate == self.rotated:
            self.rotated = rotate
            self.updateImage()

        
        self.updateStacking(reverse = rotate)


        if self.sendPosition and sendNote:
            root.send(CARDPOSITION + str(self.ID).zfill(3) + \
                      str(x).zfill(4) + str(y).zfill(4))


        
    def updateStacking(self, reverse = False):
        # modify stacking order based on y placement
        cards = []
        if self.topRotate:
            if reverse:
                for card in self.master.cardLabels:
                    if card.top + THUMBHEIGHT/2 < (GAME_PLAYHEIGHT/2):
                        cards.append(card)
                    
                cards.sort(lambda x,y: cmp(x.top,y.top))
                map(lambda x: x.top, cards)
                index = cards.index(self)
                if index == (len(cards)-1):
                    try:
                        self.lift(self.master.topOfBottom)
                    except:
                        self.lower()
                else:
                    self.lift(cards[index+1])
            
            else:  
                for card in self.master.cardLabels:
                    if card.top + THUMBHEIGHT/2 > (GAME_PLAYHEIGHT/2):
                        cards.append(card)
                    
                cards.sort(lambda x,y: cmp(x.top,y.top))
                map(lambda x: x.top, cards)
                index = cards.index(self)      
                if index == 0:
                    try:
                        self.lift(self.master.topOfBottom)
                    except:
                        self.lower()
                else:
                    self.lift(cards[index-1])
        else:
            for card in self.master.cardLabels:
                cards.append(card)
                
            cards.sort(lambda x,y: cmp(x.top,y.top))
            map(lambda x: x.top, cards)
            index = cards.index(self)      
            if index == 0:
                try:
                    self.lift(self.master.topOfBottom)
                except:
                    self.lower()
            else:
                self.lift(cards[index-1])
    

        






class TopWindow(Tk):
    def __init__(self):
        Tk.__init__(self)
        self.title("Odyssey")
        
        self.players = {}
        self.ID = None
        self.opponentID = None
        self.createOpeningScreenWidgets()
        self.dataQueue = ''
        
        self.pack = None
        self.packQueue = []
        self.picking = False

        self.cardsAvailable = []
        self.deck = []

        self.challenging = None

    def acceptIP(self):
        try:
            host = self.ipBox.get()
            port = int(self.portBox.get())
            startingTag = self.tagBox.get()


        except:
            print("Exception in TopWindow.acceptIP.")
            return
        
        if MARK in startingTag:
            print "Can't include " + MARK + " in tag."
            return

        if ENDPACKET in startingTag:
            print "Can't include " + ENDPACKET + " in tag."
            return

        self.unbind("<Return>")
        self.unbind("<Escape>")

        # Clean up previous screen
        for child in self.winfo_children():
            child.destroy()

        # Create new GUI
        self.createWaitingRoomWidgets()

        # Do setting-dependant initialization of card manager
        if THUMBREMOVETEXT:
            cards.loadMask()
        cards.loadCardBack()
                        
        # Set real IP address
        self.addr = (host,port)

        # Connect to the server
        self.clientSock = socket(AF_INET, SOCK_STREAM)
        try:
            self.clientSock.connect(self.addr)
        except:
            print("Server not found.")
            return
        self.clientSock.setblocking(0)
        self.listenID = self.after(NETLAG,self.checkNetwork)

        # Pause for a bit, because if we get the name change message
        # before that is fully processed, bad things happen
        time.sleep(0.1)


        # Send tag to server
        self.send(SETTAG+startingTag)
        # Send requests for player information
        self.send(REQUESTREADINESS)


    # This function does everything that happens upon receiving
    # any sort of message. It should probably be cleaned up
    # by breaking every type of message received into individual
    # function calls, but right now it's just massive.
    def checkNetwork(self):
        try:
            data = self.clientSock.recv(BUFSIZ)
            #print("Received " + data)
            self.dataQueue = self.dataQueue+data
            while(True):
                index = self.dataQueue.find(ENDPACKET)
                #print("Index is " + str(index))
                if index == -1:
                      break
                data = self.dataQueue[0:index]
                self.dataQueue = self.dataQueue\
                                [index + len(ENDPACKET):]
                #print "Data is " + data
                self.checkNetwork_handlePacket(data)
        except:
            pass
                        
        self.listenID = self.after(NETLAG,self.checkNetwork)

    def checkNetwork_handlePacket(self,data):
        print('Received: '+data)
        # Received a text message
        if data[0:2] == MESSAGE:
            if data[2] == WAITING:
                self.chatBox.recvMessage(data[3:])
            elif data[2] == GAME:
                try:
                    self.gameWindow.chatBox.recvMessage(data[3:])
                except:
                    pass
            elif data[2] == ALL:
                self.chatBox.recvMessage(data[3:])
                try:
                    self.gameWindow.chatBox.recvMessage(data[3:])
                except:
                    pass

        # Got a full list of players
        elif data[0:2] == PLAYERLIST:
            data = data[2:].split(MARK)
            for ID in data:
                # grab the tag from the ID
                tag = ID.split('@')[0] #everything before the first @
                
                # Create a player, add them to the dict
                self.players[ID] = Player(ID, tag)

            self.updatePlayerBox()

        elif data[0:2] == NEWPLAYER:
            ID = data[2:]
            parts = ID.split('@')
            tag = parts[0]
            player = Player(ID, tag)
            self.players[ID]=player

            print(self.ID)
            #If we haven't set our tag yet, this is the first time we're
            #getting this, and it's us.
            if self.ID == None:
                self.ID = ID
                self.tag = tag

            self.updatePlayerBox()

        # A player changed their tag
        elif data[0:2] == SETTAG:

            # Get old ID and new ID
            IDs = data[2:].split(MARK)
            oldID = IDs[0]
            newID = IDs[1]

            parts = newID.split('@')
            tag = parts[0]

            # If the old ID is the same as ours, replace our ID and tag.
            if oldID == self.ID:
                self.ID = newID
                self.tag = tag

            # Make sure we have that player
            if oldID in self.players.keys():
                # Change the tag of the player
                self.players[newID] = self.players.pop(oldID)
                self.players[newID].ID = newID
                self.players[newID].tag = tag
                self.updatePlayerBox()

            # Otherwise, create the player and comment on it. Shouldn't happen.
            else:
                print('Warning: Tag change of nonexistant player.')
                player = Player(newID,tag)
                self.players[newID] = player

                # Check to see if we've set our own tag
                if self.ID == None:
                    print(' (Received before we set our own tag.)')
                    #Assume it's because this is our ID.
                    #Set our ID and create player
                    self.ID = newID
                    self.tag = tag

   
        # A player has left the game
        elif data[0:2] == LEAVE:
            ID = data[2:]
            self.players.pop(ID)
            print(map(lambda x:x.tag,self.players.values()))

            self.updatePlayerBox()

        elif data[0:2] == READINESS:
            # Remove the type marker
            data = data[2:]
            # Get each player separately
            data = data.split(MARK)
            for entry in data:
                readiness = entry[-1] == "1"
                ID = entry[0:-1]
                print(ID)
                # Set the appropriate readiness value
                self.players[ID].ready = readiness

            self.updatePlayerBox()

        elif data[0:2] == STARTDRAFT:
            self.draft_start()

        elif data[0:2] == STARTDECK:
            self.deck_start()

        elif data[0:2] == STARTGAME:
            IDs = data[2:].split(MARK)

            print('a')
            if IDs[0] == self.ID:
                print('b1')
                self.game_start(IDs[1])
            elif IDs[1] == self.ID:
                print('b2')
                self.game_start(IDs[0])
            else:
                print('b3')
                self.chatBox.recvMessage(self.players[IDs[0]].tag + " and "\
                                         + self.players[IDs[1]].tag\
                                         + " have started a game.")
            

        elif data[0:2] == NEWPLAYERORDER:
            data = data[2:]

            IDs = data.split(MARK)
            for i in range(len(IDs)):
                player = self.players[IDs[i]]
                player.prev = self.players[IDs[i-1]]
                if i < (len(IDs)-1):
                    player.next = self.players[IDs[i+1]]
                else:
                    player.next = self.players[IDs[0]]

            self.updatePlayerBox()

        elif data[0:2] == PACKLIST:
            data = data[2:]

            pack = []
            while data:
                pack.append(data[0:9])
                data = data[9:]

            self.packQueue.append(pack)
            self.chatBox.recvMessage("You have " + str(len(self.packQueue))\
                                     + " packs enqueued.")

            if self.pack == None:
                self.draft_nextPack()

        elif data[0:2] == CHALLENGE:
            self.chatBox.recvMessage("You have been challenged to a duel by "\
                                     + self.players[data[2:]].tag + ". "\
                                     + "To start a game, reciprocate.")

        elif data[0:2] == DECKSIZES:
            self.players[self.ID].deckSize = int(data[2:5])
            self.players[self.opponentID].deckSize = int(data[5:])
            self.gameWindow.updateDeckSizes()

        elif data[0:2] == HANDSIZES:
            self.players[self.ID].handSize = int(data[2:4])
            self.players[self.opponentID].handSize = int(data[4:])
            self.gameWindow.updateHandSizes()

        elif data[0:2] == LIFE:
            self.players[self.opponentID].life = int(data[2:])
            self.gameWindow.updateLife()
            

        elif data[0:2] == DRAW:
            card = data[2:]
            self.gameWindow.handBox.addCard(card)

        elif data[0:2] == VIEWDECK:
            playchar = data[2]
            data = data[3:]
            deck = []
            while data:
                deck.append(data[0:9])
                data = data[9:]
            self.gameWindow.showDeck(deck,playchar)

        elif data[0:2] == CARDPOSITION:
            cardID = int(data[2:5])
            x = int(data[5:9])
            y = int(data[9:])
            y = GAME_PLAYHEIGHT-y
            self.gameWindow.playBox.setCardPosition(cardID,x,y)

        elif data[0:2] == NEWPLAYCARD:
            fchar = data[2]
            cardID = int(data[3:6])
            card = data[6:]
            self.gameWindow.playBox.addCard(card,newID = cardID, \
                                            flipped = fchar == "F", \
                                            sendNote = False)

        elif data[0:2] == DELPLAYCARD:
            cardID = int(data[2:])
            self.gameWindow.playBox.removeCardID(cardID)

        elif data[0:2] == FLIPTOGGLE:
            cardID = int(data[2:])
            self.gameWindow.playBox.flipCardID(cardID)

        elif data[0:2] == TAPTOGGLE:
            cardID = int(data[2:])
            self.gameWindow.playBox.tapCardID(cardID)

                        
                                    
                
        else:
            print("Invalid data type.")
            
    


    def createOpeningScreenWidgets(self):
        # Create labels for entry boxes
        self.tagLabel = Label(self, text = "Tag: ")
        self.tagLabel.grid(row = 0, column=0)
        self.ipLabel = Label(self, text="Server IP Address: ")
        self.ipLabel.grid(row=1, column=0)
        self.portLabel = Label(self, text="Server Port:")
        self.portLabel.grid(row=2,column=0)

        # Create entry boxes
        self.tagBox = Entry(self)
        self.tagBox.insert(END,TAG)
        self.tagBox.grid(row=0, column=1)
        self.ipBox = Entry(self)
        self.ipBox.insert(END,HOST)
        self.ipBox.grid(row=1, column=1)
        self.portBox = Entry(self)
        self.portBox.insert(END,str(PORT))
        self.portBox.grid(row=2,column=1)

        # Create accept/cancel buttons
        self.ipOK = Button(self, text = "OK", command = self.acceptIP)
        self.ipOK.grid(row=3, column=0)
        self.ipCancel = Button(self, text = "Cancel", command = self.quit)
        self.ipCancel.grid(row=3, column=1)

        # Useful key bindings
        self.bind("<Return>", self.keyHelperIpOK)
        self.bind("<Escape>", self.keyHelperIpCancel)

    def createDraftWidgets(self):

        print("Creating draft widgets")
        self.menu = Draft_Menu(self)
        self.config(menu = self.menu)

        self.packBox = Draft_Pack(self)
        self.pickedBox = Draft_PickedCards(self)
        self.cardBox = Draft_Card(self)
        self.chatBox.resize(DRAFT_CHATWIDTH,DRAFT_CHATHEIGHT)
        self.chatBox.pack_forget()
        self.playerBox.resize(DRAFT_PLAYERWIDTH, DRAFT_PLAYERHEIGHT)
        self.playerBox.pack_forget()


        self.packBox.grid(row = 0, column = 0, columnspan = 3)
        self.cardBox.grid(row = 1, column = 0)
        self.pickedBox.grid(row = 1, column = 1, columnspan = 2)
        self.chatBox.grid(row = 2, column = 1)
        self.playerBox.grid(row = 2, column = 2)
        

        
        
    def createWaitingRoomWidgets(self):
        # Create menus
        self.menu = WaitingMenu(self)
        self.config(menu=self.menu)

        # Create text window
        self.chatBox = ChatBox(self)
        self.chatBox.resize(WAIT_WIDTH,WAIT_HEIGHT)
        self.chatBox.pack(side = LEFT)

        # Create player list box
        self.playerBox = PlayerBox(self)
        self.playerBox.resize(WAIT_PLAYERWIDTH,WAIT_PLAYERHEIGHT)
        self.playerBox.pack(side = LEFT)

    def deck_challenge(self):
        print(self.playerBox.curselection())
        # We have to reference the player by tag...we could get around this
        # by keeping an array of IDs in the same order as the listbox
        # if desired in the future.
        slappedIndex = self.playerBox.curselection()[0]
        slappedTag = self.playerBox.get(slappedIndex)
        print(slappedTag)

        # Find the player with that tag.
        slappedPlayer = None
        for player in self.players.values():
            if player.tag == slappedTag:
                slappedPlayer = player

        print(slappedPlayer.ID)
        
        self.chatBox.recvMessage("You have challenged " \
                                 + slappedPlayer.tag\
                                 + " to a duel.")
        self.challenging = slappedPlayer.ID

        self.send(CHALLENGE+slappedPlayer.ID)
        

    def deck_start(self):
        # Most of the interface is staying the same from the drafting window
        self.packBox.destroy()

        self.deckBox = Deck_DeckBox(self)
        self.deckBox.grid(row = 0, column = 0, columnspan = 3, sticky = N+E+W+S)

        self.landBox = Deck_LandOptions(self)
        self.landBox.grid(row = 2, column = 0, sticky = N)

        self.pickedBox.enableMoveToDeck()

    def deck_moveToAvail(self, card):
        self.deck.remove(card)
        self.cardsAvailable.append(card)
        self.pickedBox.addCard(card)

    def deck_moveToDeck(self, card):
        self.cardsAvailable.remove(card)
        self.deck.append(card)
        self.deckBox.addCard(card)

    def draft_nextPack(self):
        if len(self.packQueue) > 0:
            self.pack = self.packQueue.pop(0)
            self.chatBox.recvMessage("You have " + str(len(self.packQueue))\
                                     + " packs enqueued.")
            self.packBox.display(self.pack)
            
            
## Use these if you want to implement a safety on selecting cards in the draft
##
##    def draft_pick(self):
##        self.pickButton.config(text = "Cancel",\
##                               command = self.draft_pickCancel)
##        self.picking = True
##
##    def draft_pickCancel(self):
##        self.pickButton.config(text = "Pick",\
##                               command = self.draft_pick)
##        self.picking = False

    def draft_pickCard(self,card):
        # If that was the last card, we're also ready for the next new pack
        if len(self.pack) <= 1:
            self.send(READINESS+'1')
            
        # Remove the last pack
        self.pack = None
        self.packBox.display(self.pack)

        # Add the card to the list of cards we have,
        # and the picked cards window
        self.cardsAvailable.append(card)
        self.pickedBox.addCard(card)

        # Let the server know what card you picked
        self.send(PICKEDCARD + card)

        # Get the next pack (if possible)
        self.draft_nextPack()
        
        
        
    def draft_start(self):
        #for player in self.players.values():
        #    player.ready = False

        self.createDraftWidgets()

    def game_start(self, opponentID):
        # Give the server your deck
        data = DECKLIST
        for cardLabel in self.deckBox.cardLabels:
            data = data + cardLabel.card 
        self.send(data)

        data = LANDLIST
        data = data + self.landBox.getLandData()
        self.send(data)

        # Keep around a reference to who your opponent is
        self.opponentID = opponentID

        # Game widgets go in a new window
        self.gameWindow = Game_Window(self, self.players[self.ID],\
                                      self.players[opponentID])
        self.send(DECKSIZES)
        

    def keyHelperIpOK(self,event):
        focused = self.focus_get()
        try:
            if focused.__class__ == Button:
                focused.invoke()
            else:
                self.ipOK.invoke()
        except:
            print("Exception in TopWindow.keyHelperIpOK.")
            return

    def keyHelperIpCancel(self,event):
        try: self.ipCancel.invoke()
        except:
            print("exception in TopWindow.keyHelperIpCancel.")
            return

    def send(self, data):
        print('Sending: '+data)
        self.clientSock.sendall(data+ENDPACKET)

    def showBigCard(self,card):
        try:
            self.cardBox.show(card)
        except:
            print("Error in TopWindow.showBigCard.")
        

    def updatePlayerBox(self):
        try:
            self.playerBox.delete(0,END)
            for player in self.players.values():
                print('updating player: ' + str(player.ready))
                if player.ready:
                    self.playerBox.insert(END,player.tag+" (ready)")
                else:
                    self.playerBox.insert(END,player.tag)
        except:
            print("Exception in TopWindow.updatePlayerBox.")

    def quitGame(self):
        self.send(LEAVE)
        self.clientSock.close()
        self.quit()


class WaitingMenu(Menu):
    def __init__(self, master):
        Menu.__init__(self,master)

        #Setup menus
        self.filemenu = Menu(self)
        self.add_cascade(label = "File", menu = self.filemenu)
        self.filemenu.add_command(label = "Quit", command = root.quitGame)

        self.gamemenu = Menu(self)
        self.add_cascade(label = "Game", menu = self.gamemenu)
        self.gamemenu.add_command(label = "Ready", command = self.setReady)
        self.gamemenu.add_command(label = "Not ready", command = self.setUnready)

    def setReady(self):
        root.send(READINESS + "1")

    def setUnready(self):
        root.send(READINESS + "0")

if not os.path.isdir(CARDDIR):
    os.makedirs(CARDDIR)
root = TopWindow()

# This object holds and manipulates all the card images
cards = CardImageManager()

root.mainloop()
