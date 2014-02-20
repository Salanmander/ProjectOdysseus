# YetAnotherDraftingProgramClient.py
# Author: Alan Kraut
# This is a program for free online drafting of Magic the Gathering.

from Tkinter import *
from PIL import Image, ImageTk
from socket import *
import time
import random

# Data protocol tags. I'm assuming I won't need more 2 characters
# to uniquely identify packet type. They are appended to the beginning
# of each packet.

MESSAGE = 'aa' # A text message
ALL = 'A' # Sends to everyone, displays on all chat boxes
WAITING = 'W' # Sends to everyone, displays in waiting/deck building rooms
GAME = 'G' # Sends to you and opponent, displays in game

PLAYERLIST = 'ab' # List of players in (a given? all?) room(s)
NEWPLAYER = 'ac' # The name of a player that has just joined
SETTAG = 'ad' # A player changing their tag
SETID = 'at' # A player is telling the server what their ID # is
LEAVE = 'ae' # A player just left
READINESS = 'af' # A player has set their readiness state
STARTDRAFT = 'ag' # The draft is starting
STARTDECK = 'ah' # The deck-building stage is starting
STARTGAME = 'ai' # A game is starting between two players

NEWPLAYERORDER = 'aj' # A list of the old indeces of players in ther new order
PACKLIST = 'ak' # A list of cards a player should add as a pack to their queue
PICKEDCARD = 'al' # The card from a player's current pack that they picked

CHALLENGE = 'am' # A challenge to a game has been issued
DECKLIST = 'an' # A full listing of a player's deck, minus basic lands
LANDLIST = 'ao' # A list of numbers of basic land cards in player's deck
DECKSIZES = 'ap' # Player's deck size followed by opponent's deck size;
                 # also sent to server to request said data\
HANDSIZES = 'aq'
CHNGHANDSIZE = 'ar' # I don't like needing to use this, but I couldn't think of
                    # a simpler way. This simply lets the server know (+/-)
                    # that the player's hand size has been changed by one.
LIFE = 'as' # A player sending the server their life, or the server sending
            # a player their opponent's life

REQUESTPLAYERLIST = 'ba' # A client requesting a PLAYERLIST
REQUESTREADINESS = 'bb' # A client requesting readiness values for all players

DRAW = 'ca' #The top card of a player's deck, or a request for such
DECKTOP = 'cb' #Tells the server to put the specified card on top of the deck
DECKBOTTOM = 'cc'
SHUFFLE = 'cd' #Tells the server to shuffle the player's deck
VIEWDECK = 'ce' # First char is player: 0 for self, 1 for opponent
                # Server adds the appropriate deck list and returns it
DECKREMOVE = 'cf' # Tells server to remove one copy of given card from
                  # (0/1) self or opponent's deck
                  # NOT GUARANTEED to take card from desired position
CARDPOSITION = 'cg' #These allow sharing of the virtual tabletop
NEWPLAYCARD = 'ch'
DELPLAYCARD = 'ci'
FLIPTOGGLE = 'cj'
TAPTOGGLE = 'ck'



# This is a single character used as a delimeter in sent messages.
# It can't appear in strings that will be sent across the network.
MARK = '='

# This is the mark of the end of a packet. I've decided it's
# sufficiently unlikely to not restrict its use explicitly,
# but putting it in the middle of packets will break the protocol.
# It is added by TopWindow.send.
ENDPACKET = '~`mq@'

# Indeces used for basic lands
PLAINS = 0
ISLAND = 1
SWAMP = 2
MOUNTAIN = 3
FOREST = 4

NETLAG = 1 # number of miliseconds between checking the network
TAG = 'YoungPadawan'
HOST = 'localhost'
PORT = 21567
BUFSIZ = 1024

# Parameters about card size
THUMBSCALE = 0.5 # Linear scaling factor to use for small size cards
TITLEFRACTION = 0.12 # This is the fraction of the card that should be
                    # displayed from the top for the title bar to be visible
CARDWIDTH = 265
CARDHEIGHT = 370
# Derived parameters
CARDTITLEHEIGHT = int(CARDHEIGHT * TITLEFRACTION)
THUMBWIDTH = int(THUMBSCALE * CARDWIDTH)
THUMBHEIGHT = int(THUMBSCALE * CARDHEIGHT)
THUMBTITLEHEIGHT = int(CARDHEIGHT * TITLEFRACTION * THUMBSCALE)


# Parameters for waiting window
WAIT_WIDTH = 50
WAIT_HEIGHT = 30

# Parameters for draft window
DRAFT_CHATHEIGHT = 8
DRAFT_CHATWIDTH = 108
DRAFT_PLAYERHEIGHT = 8
DRAFT_PLAYERWIDTH = 30
DRAFT_PICKEDHEIGHT = 375
DRAFT_PICKEDWIDTH = 837
# Unfortunately I haven't yet figured a way to set the size of the
# booster pack display conveniently

# The deck-building window just fills the space available in the grid

# Parameters for game window
GAME_MESSAGEWIDTH = 20
GAME_MESSAGENUM = 15
GAME_MESSAGES = ("At the end of your turn...","Untap/upkeep/draw.",\
                 "Main phase.","Combat phase.","Hold on...","Your turn.",\
                 "Declare no blockers.")
GAME_PLAYHEIGHT = 700
GAME_PLAYWIDTH = 950
GAME_HANDWIDTH = THUMBWIDTH + 4
GAME_HANDHEIGHT = 400
GAME_CHATWIDTH = 160 
GAME_CHATHEIGHT = 14
GAME_INFOBARWIDTH = 52
GAME_LABELSPACE = 30 # Space between the tops of indicators for life etc.
GAME_LABELOFFSET = 12 # Shift the labels to center them WRT the life entry box
GAME_DECKROWS = 15 # Number of cards to display in a column when showing an
                   # entire deck.

# Image global varaibles
images = dict()
thumbnails = dict()
thumbTapped = dict()
thumb180 = dict()
thumb180Tap = dict()

class ChatBox(Frame):
    def __init__(self,master,sendType = WAITING):
        Frame.__init__(self,master)

        self.sendType = sendType

        
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

        self.entry.pack(side = BOTTOM)
        self.scrollbar.pack(side = RIGHT, fill = Y)
        self.display.pack(side = TOP)

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
        self.entry.config(width = width)
        self.display.config(width = width-3, height = height-1)

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
        plains = self.plainsBox.get().zfill(2)
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
        self.show('0001')

    def show(self,card):
        if not card in thumbnails.keys():
            filename = "Cards/EN_SHM_"+card+".jpg"
            temp_image = Image.open(filename)
            images[card] = ImageTk.PhotoImage(temp_image)
            
            bbox = temp_image.getbbox()
            temp_image = temp_image.resize((int(bbox[2]*THUMBSCALE),\
                                            int(bbox[3]*THUMBSCALE)),Image.ANTIALIAS)
            thumbnails[card] = ImageTk.PhotoImage(temp_image)

            temp_image = temp_image.rotate(270)
            thumbTapped[card] = ImageTk.PhotoImage(temp_image)

        self.config(image = images[card])

class Draft_Menu(Menu):
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
        self.cardLabels = [None]*16
        i = 0
        for card in pack:

            self.cardLabels[i] = SmallCard(self, card)
            self.cardLabels[i].grid(row = int(i/8), column = i%8)
            self.cardLabels[i].config(bg = "White")
            self.cardLabels[i].bind("<Double-Button-1>",self.pickCard)
            i = i+1


        # This fills the rest of the panel with blank white JPEGs that don't
        # do anything. Why? So it doesn't shrink when you get fewer cards.
        card = '0000'
        for j in range(len(pack),16):
            if not card in thumbnails.keys():
                filename = "Cards/EN_SHM_"+card+".jpg"
                temp_image = Image.open(filename)
                images[card] = ImageTk.PhotoImage(temp_image)
                
                bbox = temp_image.getbbox()
                temp_image = temp_image.resize((int(bbox[2]*THUMBSCALE),\
                                                int(bbox[3]*THUMBSCALE)),Image.ANTIALIAS)
                thumbnails[card] = ImageTk.PhotoImage(temp_image)

                # We use all four cardinal orientations
                temp_image = temp_image.rotate(90)
                thumb180Tap[card] = ImageTk.PhotoImage(temp_image)
                temp_image = temp_image.rotate(90)
                thumb180[card] = ImageTk.PhotoImage(temp_image)
                temp_image = temp_image.rotate(90)
                thumbTapped[card] = ImageTk.PhotoImage(temp_image)

            self.cardLabels[i] = Label(self, image = thumbnails[card])
            self.cardLabels[i].config(bg = "White")
            self.cardLabels[i].grid(row = int(i/8), column = i%8)
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

##        for card in ('0001','0002','0251','0125','0078'):
##            self.addCard(card)

        

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
        print("1")
        for cardLabel in self.cardLabels:
            print("1")
            if cardLabel.ID == cardID:
                print("1")
                cardLabel.tapped = not cardLabel.tapped
                print("1")
                cardLabel.updateImage()
                print("1")
                                    

    def tapToggle(self,event):
        cardLabel = event.widget
        cardLabel.tapped = not cardLabel.tapped
        cardLabel.updateImage()
        cardLabel.unbind("<Double-Button-1>")
        self.tapHelperQueue.append(cardLabel)
        self.after(500,self.tapToggleHelper)
        print("1")
        root.send(TAPTOGGLE + str(cardLabel.ID).zfill(3))
        print("2")

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
        self.master.playBox.addCard("BACK")

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
        self.title("YADP GAME: " + opponent.tag)

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
        print("1")
        self.playBox = Game_PlayArea(self)
        print("2")
        self.handBox = Game_Hand(self)
        print("3")
        
        self.chatBox = ChatBox(self, sendType = GAME)
        self.chatBox.resize(GAME_CHATWIDTH,GAME_CHATHEIGHT)
        print("3")
        
        self.cardBox = Draft_Card(self)
        print("4")
        self.displayBar = Game_Display(self)
        print("5")
        self.toolBox = Game_Tools(self)
        print("6")
        self.messagesBox = Game_Messages(self)
        print("7")
        
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
    def __init__(self,index,tag):
        self.index = index
        self.tag = tag
        self.room = None
        self.ready = False
        self.ID = None

        # These are used during games
        self.deckSize = 0
        self.handSize = 0
        self.life = 20
              

class SmallCard(Label):
    def __init__(self,master,card, flipped = False):
        Label.__init__(self,master)
        if not card in thumbnails.keys():
            filename = "Cards/EN_SHM_"+card+".jpg"
            temp_image = Image.open(filename)
            images[card] = ImageTk.PhotoImage(temp_image)
            
            
            bbox = temp_image.getbbox()
            temp_image = temp_image.resize((int(bbox[2]*THUMBSCALE),\
                                            int(bbox[3]*THUMBSCALE)),Image.ANTIALIAS)
            thumbnails[card] = ImageTk.PhotoImage(temp_image)

            # We use all four cardinal orientations
            temp_image = temp_image.rotate(90)
            thumb180Tap[card] = ImageTk.PhotoImage(temp_image)
            temp_image = temp_image.rotate(90)
            thumb180[card] = ImageTk.PhotoImage(temp_image)
            temp_image = temp_image.rotate(90)
            thumbTapped[card] = ImageTk.PhotoImage(temp_image)

        self.card = card
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
                print self.card
                if self.card == "BACK":
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
                    self.configure(image = thumb180Tap["BACK"])
                else:
                    self.configure(image = thumb180["BACK"])
            else:
                if self.tapped:
                    self.configure(image = thumbTapped["BACK"])
                else:
                    self.configure(image = thumbnails["BACK"])
        else:
            if self.rotated:
                if self.tapped:
                    self.configure(image = thumb180Tap[self.card])
                else:
                    self.configure(image = thumb180[self.card])
            else:
                if self.tapped:
                    self.configure(image = thumbTapped[self.card])
                else:
                    self.configure(image = thumbnails[self.card])
                    

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
        self.title("YADP")
        
        self.players = []
        self.index = None
        self.ID = ''
        for i in range(4):
            self.ID = self.ID + chr(random.randint(0,255))
        self.opponentIndex = None
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
            self.tag = self.tagBox.get()


        except:
            print("Exception in TopWindow.acceptIP.")
            return
        
        if MARK in self.tag:
            print "Can't include " + MARK + " in tag."
            return

        self.unbind("<Return>")
        self.unbind("<Escape>")

        # Clean up previous screen
        for child in self.winfo_children():
            child.destroy()

        # Create new GUI
        self.createWaitingRoomWidgets()

                        
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
        time.sleep(0.01)

        # Send ID to server
        self.send(SETID+self.ID)
        # Send tag to server
        self.send(SETTAG+self.tag)
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
            number = int(data[2:4])
            self.index = number-1
            data = data[4:]
            self.players = [None]*number
            while(True):
                # Get the next index, and remove it from the data
                nextIndex = int(data[0:2])
                data = data[2:]
                
                # Find the latest delimiter
                # If there are none, we have one more name and this
                # sets to -1.
                index = data.find(MARK)
                # Fetch everything before it
                if index == -1:
                    nextName = data
                else:
                    nextName = data[0:index]
                # Add that name to the list
                self.players[nextIndex] = Player(nextIndex, nextName)
                # Delete everything before the last delimeter
                data = data[index+1:]
                # Break out of the loop if this was the last name
                if index == -1:
                    break
            self.updatePlayerBox()

        elif data[0:2] == NEWPLAYER:
            index = int(data[2:4])
            tag = data[4:]
            player = Player(index, tag)
            if(len(self.players) == index):
                self.players.append(player)
            else:
                print("ERROR\nERROR\nnewplayer index inconsistency")
                        
                    

        # A player changed their tag
        elif data[0:2] == SETTAG:

            # Get index and new tag
            index = int(data[2:4])
            newTag = data[4:]

            # Make sure we have that player
            if index < len(self.players):
                # Change the tag of the player
                self.players[index].tag = newTag
                self.updatePlayerBox()

            # If we encountered an inconsistency, keep going but note the error
            else:
                print("ERROR!\nERROR!\nIndex of updated player name outside range.")

        # A player has left the game
        elif data[0:2] == LEAVE:
            index = int(data[2:4])
            self.players.pop(index)
            print(map(lambda x:x.tag,self.players))

            for i in range(len(self.players)):
                self.players[i].index = i
            self.updatePlayerBox()

        elif data[0:2] == READINESS:
            # Remove the type marker
            data = data[2:]
            while(data):
                # Get the next index
                nextIndex = int(data[0:2])
                
                # Set the appropriate readiness value
                self.players[nextIndex].ready = data[2] == "1"

                # Remove that player's readiness from the data
                data = data[3:]

            self.updatePlayerBox()

        elif data[0:2] == STARTDRAFT:
            self.draft_start()

        elif data[0:2] == STARTDECK:
            self.deck_start()

        elif data[0:2] == STARTGAME:
            index1 = int(data[2:4])
            index2 = int(data[4:])

            if index1 == self.index:
                self.game_start(index2)
            elif index2 == self.index:
                self.game_start(index1)
            else:
                self.chatBox.recvMessage(self.players[index1].tag + " and "\
                                         + self.players[index2].tag\
                                         + " have started a game.")
            

        elif data[0:2] == NEWPLAYERORDER:
            data = data[2:]

            print map(lambda x: x.tag,self.players)
            # We're going through in the new order, being given
            # the old indeces
            newIndex = 0
            while data:
                oldIndex = int(data[0:2])
                if oldIndex == self.index:
                    self.index = newIndex
                    
                self.players[oldIndex].index = newIndex
                data = data[2:]
                newIndex = newIndex+1

            self.players.sort(lambda x,y:cmp(x.index,y.index))

            self.updatePlayerBox()

        elif data[0:2] == PACKLIST:
            data = data[2:]

            pack = []
            while data:
                pack.append(data[0:4])
                data = data[4:]

            self.packQueue.append(pack)
            self.chatBox.recvMessage("You have " + str(len(self.packQueue))\
                                     + " packs enqueued.")

            if self.pack == None:
                self.draft_nextPack()

        elif data[0:2] == CHALLENGE:
            self.chatBox.recvMessage("You have been challenged to a duel by "\
                                     + self.players[int(data[2:])].tag + ". "\
                                     + "To start a game, reciprocate.")

        elif data[0:2] == DECKSIZES:
            self.players[self.index].deckSize = int(data[2:5])
            self.players[self.opponentIndex].deckSize = int(data[5:])
            self.gameWindow.updateDeckSizes()

        elif data[0:2] == HANDSIZES:
            self.players[self.index].handSize = int(data[2:4])
            self.players[self.opponentIndex].handSize = int(data[4:])
            self.gameWindow.updateHandSizes()

        elif data[0:2] == LIFE:
            self.players[self.opponentIndex].life = int(data[2:])
            self.gameWindow.updateLife()
            

        elif data[0:2] == DRAW:
            card = data[2:]
            self.gameWindow.handBox.addCard(card)

        elif data[0:2] == VIEWDECK:
            playchar = data[2]
            data = data[3:]
            deck = []
            while data:
                deck.append(data[0:4])
                data = data[4:]
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
        print("2")
        self.cardBox = Draft_Card(self)
        self.chatBox.resize(DRAFT_CHATWIDTH,DRAFT_CHATHEIGHT)
        self.chatBox.pack_forget()
        self.playerBox.config(width = DRAFT_PLAYERWIDTH, \
                              height = DRAFT_PLAYERHEIGHT)
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
        self.playerBox = Listbox(self)
        self.playerBox.pack(side = LEFT)

    def deck_challenge(self):
        slappedIndex = int(self.playerBox.curselection()[0])
        self.chatBox.recvMessage("You have challenged " \
                                 + self.players[slappedIndex].tag\
                                 + " to a duel.")
        self.challenging = slappedIndex

        self.send(CHALLENGE+str(slappedIndex).zfill(2))
        

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
        for player in self.players:
            player.ready = False

        self.createDraftWidgets()

    def game_start(self, opponentIndex):
        # Give the server your deck
        data = DECKLIST
        for cardLabel in self.deckBox.cardLabels:
            data = data + cardLabel.card 
        self.send(data)

        data = LANDLIST
        data = data + self.landBox.getLandData()
        self.send(data)

        # Keep around a reference to who your opponent is
        self.opponentIndex = opponentIndex

        # Game widgets go in a new window
        self.gameWindow = Game_Window(self, self.players[self.index],\
                                      self.players[opponentIndex])
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
        self.clientSock.sendall(data+ENDPACKET)

    def showBigCard(self,card):
        try:
            self.cardBox.show(card)
        except:
            print("Error in TopWindow.showBigCard.")
        

    def updatePlayerBox(self):
        try:
            self.playerBox.delete(0,END)
            for player in self.players:
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

root = TopWindow()

# Getting the card back image, since we don't check for it other places
card = "BACK"
filename = "Cards/EN_SHM_"+card+".jpg"
temp_image = Image.open(filename)
temp_image = temp_image.resize((CARDWIDTH,\
                                CARDHEIGHT),Image.ANTIALIAS)
images[card] = ImageTk.PhotoImage(temp_image)

bbox = temp_image.getbbox()
temp_image = temp_image.resize((int(bbox[2]*THUMBSCALE),\
                                int(bbox[3]*THUMBSCALE)),Image.ANTIALIAS)
thumbnails[card] = ImageTk.PhotoImage(temp_image)

temp_image = temp_image.rotate(90)
thumb180Tap[card] = ImageTk.PhotoImage(temp_image)
temp_image = temp_image.rotate(90)
thumb180[card] = ImageTk.PhotoImage(temp_image)
temp_image = temp_image.rotate(90)
thumbTapped[card] = ImageTk.PhotoImage(temp_image)

root.mainloop()
