# Client.py
# Author: Alan Kraut
# This is a program for free online drafting of Magic the Gathering.


# we probably don't need most of these imports
from Tkinter import *
from PIL import Image, ImageTk, ImageFont, ImageDraw
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
        # Image variables
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
        self.charsize = self.font.getsize("M")

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
        self.powerBoxMask = self.powerBoxMask.resize((int(w*opts['thumbscale']),\
                                                      int(h*opts['thumbscale'])),Image.ANTIALIAS)
        # Also get closely bounded mask
        self.smallPowerMask = self.powerBoxMask.crop(self.powerBoxMask.getbbox())
        # These are images we overwrite frequently, may have arbitrary data
        self.powerBackground = Image.new("RGB",(int(w*opts['thumbscale']),\
                                                int(h*opts['thumbscale'])))
        self.blankImage = Image.new("RGB",(opts['thumbwidth'],opts['thumbheight']))

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
        temp_image = temp_image.resize((opts['bigcardwidth'],\
                                        opts['bigcardheight']),Image.ANTIALIAS)
        
        self.images[multiverseID] = ImageTk.PhotoImage(temp_image)

        # only retype the textbox text if there is rules text there
        retypeText = opts['thumbretypetext'] and ('text' in self.allCards[multiverseID])\
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
        newImage = fullImage.resize((opts['thumbwidth'],\
                                     opts['thumbheight']),Image.ANTIALIAS)
        if(opts['thumbremovetext']):
            # get the power/toughness box
            powerImage = newImage.crop(self.powerBoxMask.getbbox())

            creature = self.isCreature(multiverseID)
            
            # Get top of card and bottom border, then paste them together
            w,h = newImage.size
            topPixels = int(h*TYPEFRACTION)
            # opts['thumbheight'] is calculated using VBLACKFRACTION, so
            # opts['thumbheight']-topPixels is the number of pixels we have left
            # for the bottom border. This is done so that the height of
            # the new image will exactly match opts['thumbheight'], regardless of
            # rounding.
            bottomBorder = newImage.crop((0,h-(opts['thumbheight']-topPixels),\
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
            textBox = Image.new("RGB",(opts['thumbtextwidth'],opts['thumbtextheight']),
                                TEXTBOXCOLOR)
            text = self.allCards[multiverseID]['text']
            chars = int(opts['thumbtextwidth']/self.charsize[0])
            lines = textwrap.wrap(text,width = chars)
            draw = ImageDraw.Draw(textBox)
            y = 0
            for line in lines:
                draw.text((1,y),line,font = self.font, fill = "Black")
                y = y + int(self.charsize[1]*TEXTLINEFRACTION)
            newImage.paste(textBox,(int(opts['thumbwidth']*HBORDERFRACTION),
                                    int(opts['thumbheight']*TYPEFRACTION)))
            
            
        return newImage

    def isCreature(self,multiverseID):
        return 'toughness' in self.allCards[multiverseID]

