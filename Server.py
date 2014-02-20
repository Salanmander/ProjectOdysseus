# YetAnotherDraftingProgramServer.py
# Author: Alan Kraut
# This is the dedicated server for the YADP M:tG program.

from Tkinter import *
from socket import *
import time
import random

from protocolDefs import *

# These are actually defined below classes, but I've
# recorded names here for reference
#
# ALL numbers here are recorded as 4-character STRINGS
# I suggest maintaining this encoding, as it makes referencing files easy
# and their numerical relation to each other never has any effect
#
# rares = list of rare card numbers
# uncommons
# commons
# lands = [[plains numbers],[island numbers]...etc.]
#     indeces are given as constants PLAINS, ISLAND, etc. above
# runsFormat = "2%06=2%05"
# runs = [[runA card numbers],[runB card numbers]...etc.]

NETLAG = 1 #number of miliseconds between checking the network
HOST = 'localhost'
PORT = 21567
BUFSIZ = 1024
ADDR = (HOST, PORT)
#setList = ['SHM','SHM','SHM']
setList = ['SHM']

print(MARK)

class Client():
    def __init__(self, socket, IP):
        self.socket = socket
        self.tag = root.makeUniqueName("<Unnamed>")
        self.room = None
        self.ready = False
        self.ID = self.tag+'@'+IP
        self.oldID = self.tag+'@'+IP
        self.packQueue = []


        #For the draft the clients will be a doubly linked list
        self.next = None
        self.prev = None
        self.challenging = None # This will be an ID
        
        self.deck = []
        self.life = 20
        self.handSize = 0
        self.opponent = None # This will be a valid client object

class MainMenu(Menu):
    def __init__(self, master):
        Menu.__init__(self, master)
        self.createBasicMenus()

    def createBasicMenus(self):
        # File menu
        # Contains: exit
        self.filemenu = Menu(self)
        self.add_cascade(label = "File", menu=self.filemenu)
        self.filemenu.add_command(label = "Exit", \
                                command=self.winfo_toplevel().quit)

        # Player menu
        # Contains: kick selected, kick all
        self.playermenu = Menu(self)
        self.add_cascade(label = "Player", menu=self.playermenu)
        self.playermenu.add_command(label = "Kick Selected", \
                                    command = self.kickSelected)
        self.playermenu.add_command(label = "Kick All", \
                                    command = self.kickAll)

        # Help menu
        # Contains: about
        self.helpmenu = Menu(self)
        self.add_cascade(label = "Help", menu=self.helpmenu)
        self.helpmenu.add_command(label = "About", command=self.displayAbout)

    def displayAbout(self):
        print("The About dialogue has not been implemented yet.")

    def kickAll(self):
        root.sendToEveryone(MESSAGE + "Test")

    def kickSelected(self):
        print("Unimplemented")

        
class Room(Frame):
    def __init__(self, master, label):
        Frame.__init__(self,master)

        # Label the list
        self.title = Label(self, text = label)
        self.title.pack(side=TOP)

        # Create the list
        self.list = Listbox(self)
        self.list.pack(side=TOP)

class Pack():
    def __init__(self):
        self.cards = []

        # Create list of cards in pack
        # Rare
        self.cards.append(random.choice(rares))

        # 3 Uncommons
        while len(self.cards) < 4:
            card = random.choice(uncommons)
            if not card in self.cards:
                self.cards.append(card)

        # Commons: use print runs
        i = 0
        usedRuns = 0
        while i<len(runsFormat):
            # Grab the next run information
            runChoices = int(runsFormat[i])
            runCardNum = int(runsFormat[i+2:i+4])
            i = i+5 # start of next run information chunk

            # Pick a random run from our first runChoices unused
            # options, then update the number of used options
            runIndex = random.randint(0,runChoices-1) + usedRuns
            run = runs[runIndex]
            usedRuns = usedRuns + runChoices

            # Pick a random starting spot in that run
            cardIndex = random.randint(0,len(run)-1)

            # Add cards
            for j in range(runCardNum):
                # Loop if you need to
                if cardIndex >= len(run):
                    cardIndex = 0
                self.cards.append(run[cardIndex])
                cardIndex = cardIndex + 1

    def remove(self, card):
        self.cards.remove(card)

    def shuffle(self):
        random.shuffle(self.cards)

    def toPackList(self):
        data = PACKLIST
        for card in self.cards:
            data = data + card
        return data

                
class TopWindow(Tk):
    def __init__(self):
        Tk.__init__(self)
        self.createOpeningScreenWidgets()
        self.addr = ADDR
        self.clients = {}
        self.clientsToRemove = []
        self.disconnectedClients = []
        self.rooms = dict()
        self.state = "ENTERIP"

        # This is used to store data if we don't get an ENDPACKET
        self.dataQueue = ''

        # If this is 1 you pass down the list, if it's -1 you pass
        # up the list.
        self.direction = -1



    def acceptIP(self):
        try:
            host = self.ipBox.get()
            port = int(self.portBox.get())
                            # Clean up previous screen
            for child in self.winfo_children():
                            child.destroy()
        except:
            print("Exception in TopWindow.acceptIP.")
            return

        # Set real IP address
        self.addr = (host,port)

        # initialize socket
        self.serversock = socket(AF_INET, SOCK_STREAM)
        self.serversock.bind(self.addr)
        self.serversock.listen(10)
        self.serversock.setblocking(0)
        self.listenID = self.after(NETLAG,self.checkNetwork)

        # Create new GUI
        self.createServerWidgets()
        self.state = "WAITING"
                    # start a list of rooms
        tempRoom = self.createRoom("Waiting Room")
            

    # This function does everything that happens upon receiving
    # any sort of message. It should probably be cleaned up
    # by breaking every type of message received into individual
    # function calls, but right now it's just massive.
    def checkNetwork(self):
        try:
            clientSock, cliAddr = self.serversock.accept()
            print '...connected from:', cliAddr
            clientSock.setblocking(0)

            client = Client(clientSock, cliAddr[0])
            ID = client.tag+'@'+cliAddr[0]
                                
            # If we just got a new connection, we need to
            # notify the rest of the clients.
            self.sendToEveryone(NEWPLAYER + \
                                client.ID)

            # We also need to make sure we give the new player a list
            # of players before ANYTHING ELSE gets sent to them.
            self.clients[client.ID] = client

            # Send player's own info as NEWPLAYER to them
            self.sendRobust(client, NEWPLAYER+client.ID)
            
            data = self.makePlayerlist()
            self.sendRobust(client, data)
        except:pass

        
        if len(self.clients) > 0:

            # Each time you check the network,
            # try to receive from each client.
            for key in self.clients.keys():
                client = self.clients[key]
                        
                try:
                    data = client.socket.recv(BUFSIZ)
                    #print "Received " + data
                    self.dataQueue = self.dataQueue+data
                    while(True):
                        index = self.dataQueue.find(ENDPACKET)
                        #print("Index is " + str(index))
                        if index == -1:
                            break
                        #TODO: create dataQueue for each client
                        data = self.dataQueue[0:index]
                        self.dataQueue = self.dataQueue\
                                            [index + len(ENDPACKET):]
                        print "Received: " + data + " from " + client.tag
                        self.checkNetwork_handlePacket(client, data)
                except:pass

        for dead in self.clientsToRemove:
            self.removeClient(dead)

        #TODO: Clear this list one by one, as you remove
        self.clientsToRemove = []
        self.listenID = root.after(NETLAG,self.checkNetwork)

    def checkNetwork_handlePacket(self,client,data):
        # A player just left
        if data[0:2] == LEAVE:
            self.removeClient(client)
            
        # Text message has been sent
        elif data[0:2] == MESSAGE:
            data = data[0:3] + client.tag + ": " + data[3:]
            if data[2] == WAITING or data[2] == ALL:
                self.sendToEveryone(data)
            elif data[2] == GAME:
                try:
                    self.sendRobust(client,data)
                    self.sendRobust(client.opponent,data)
                except:
                    pass
                            
        # A player is changing their tag
        elif data[0:2] == SETTAG:
            if self.isUniqueTag(data[2:]):
                newName = data[2:]
                client.tag = newName

                #TODO: implement dictionary wrappers for consistency
                # update client ID
                oldID = client.ID
                oldIDparts = oldID.split('@')
                ID = newName+'@'+oldIDparts[1]
                client.ID = ID

                #update dictionary
                self.clients.pop(oldID)
                self.clients[ID] = client

                #tell everyone
                self.sendToEveryone(SETTAG+oldID+MARK\
                                    +client.ID)
            else:
                data = MESSAGE + 'I\'m sorry, that tag is already in '\
                    +'use. Please choose a different one.'
                self.sendRobust(client,data)

        elif data[0:2] == SETID:
            print "I haven't implemented this yet"

        # A player set their readiness value
        elif data[0:2] == READINESS:
            client.ready = data[2]=="1"

            data = READINESS + client.ID + data[2]
            self.sendToEveryone(data)

            self.checkReadiness()

        # TODO: update system for ordering draft.
        elif data[0:2] == PICKEDCARD:
            card = data[2:]
            pack = client.packQueue.pop(0)
            pack.remove(card)
            if len(pack.cards) > 0:
                # Find the player to pass the pack to
                if self.direction == 1: #we're passing left
                    recipient = client.next
                elif self.direction == -1: #we're passing right
                    recipient = client.prev
                else:
                    print('Error: unexpected passing direction, passing left')
                    recipient = client.next

                # Update internal representation and send message                     
                recipient.packQueue.append(pack)
                self.sendRobust(recipient, pack.toPackList())

        elif data[0:2] == CHALLENGE:
            recipientID = data[2:]
            recipient = self.clients[recipientID]
            if recipient.challenging == client.ID:
                self.game_start(client, recipient)
            else:
                self.sendRobust(recipient, CHALLENGE + \
                                client.ID)
                client.challenging = recipientID


        elif data[0:2] == DECKLIST:
            client.deck = []
            data = data[2:]
            while data:
                client.deck.append(data[0:4])
                data = data[4:]

            # We'll never want the deck in sorted order
            random.shuffle(client.deck)

        elif data[0:2] == LANDLIST:
            data = data[2:]
            # Go through each land type
            for landType in (PLAINS, ISLAND, SWAMP, MOUNTAIN, FOREST):
                # Get the appropriate number
                index = 2*landType
                num = int(data[index:index+2])
                # Add that many lands of that type
                for i in range(num):
                    card = random.choice(lands[landType])
                    client.deck.append(card)

            print client.deck

            # We'll never want the deck in sorted order
            random.shuffle(client.deck)

        elif data[0:2] == DECKSIZES:
            self.game_sendDeckSizes(client)

        elif data[0:2] == CHNGHANDSIZE:
            if data[2] == '+':
                client.handSize = client.handSize+1
            else:
                client.handSize = client.handSize-1
            self.game_sendHandSizes(client)
            self.game_sendHandSizes(client.opponent)

        elif data[0:2] == LIFE:
            client.life = int(data[2:])
            self.game_sendOpponentLife(client.opponent)
            
        # A player is requesting a list of players
        elif data[0:2] == REQUESTPLAYERLIST:
            data = self.makePlayerlist()
            self.sendRobust(client, data)

        elif data[0:2] == REQUESTREADINESS:
            data = READINESS
            IDs = []
            for tempClient in self.clients.values():
                datapart = tempClient.ID
                if tempClient.ready:
                    datapart = datapart+"1"
                else:
                    datapart = datapart+"0"
                IDs.append(datapart)
            data = data + MARK.join(IDs)
                
            self.sendRobust(client,data)

        elif data[0:2] == DRAW:
            self.sendRobust(client,DRAW + client.deck.pop(0))

            self.game_sendDeckSizes(client)
            self.game_sendDeckSizes(client.opponent)

        elif data[0:2] == DECKTOP:
            card = data[2:]
            client.deck.insert(0,card)
            self.game_sendDeckSizes(client)
            self.game_sendDeckSizes(client.opponent)

        elif data[0:2] == DECKBOTTOM:
            card = data[2:]
            client.deck.append(card)
            self.game_sendDeckSizes(client)
            self.game_sendDeckSizes(client.opponent)

        elif data[0:2] == SHUFFLE:
            random.shuffle(client.deck)

        elif data[0:2] == VIEWDECK:
            if data[2] == "0":
                for card in client.deck:
                    data = data + card
            else:
                for card in client.opponent.deck:
                    data = data + card
            self.sendRobust(client,data)

        elif data[0:2] == DECKREMOVE:
            if data[2] ==  "0":
                client.deck.remove(data[3:])
            else:
                client.opponent.deck.remove(data[3:])

            self.game_sendDeckSizes(client)
            self.game_sendDeckSizes(client.opponent)

        # The server doesn't keep track of board positions, so it just
        # needs to forward this information along
        elif data[0:2] == CARDPOSITION or\
                data[0:2] == NEWPLAYCARD or\
                data[0:2] == DELPLAYCARD or\
                data[0:2] == FLIPTOGGLE or\
                data[0:2] == TAPTOGGLE:
            self.sendRobust(client.opponent, data)
                
        else:
            print("Invalid data type.")

    def checkReadiness(self):

        # If not all the ready values are True
        if False in map(lambda x: x.ready, self.clients.values()):
            return

        # Otherwise, all the ready values are True, and
        # we should start the draft
        else:
            # Tell everyone that nobody is ready
            data = READINESS
            IDs = []
            for tempClient in self.clients.values():
                tempClient.ready = False
                IDs.append(tempClient.ID + '0')
            data = data+MARK.join(IDs)
            self.sendToEveryone(data)
            if self.state == "WAITING":
                self.draft_start()
            elif self.state == "DRAFT":
                self.draft_nextPack()
            
                                
    def createOpeningScreenWidgets(self):
        # Create labels for entry boxes
        self.ipLabel = Label(self, text="IP Address: ")
        self.ipLabel.grid(row=0, column=0)
        self.portLabel = Label(self, text="Port:")
        self.portLabel.grid(row=1,column=0)

        # Create entry boxes
        self.ipBox = Entry(self)
        self.ipBox.insert(END,HOST)
        self.ipBox.grid(row=0, column=1)
        self.portBox = Entry(self)
        self.portBox.insert(END,str(PORT))
        self.portBox.grid(row=1,column=1)

        # Create accept/cancel buttons
        self.ipOK = Button(self, text = "OK", command = self.acceptIP)
        self.ipOK.grid(row=2, column=0)
        self.ipCancel = Button(self, text = "Cancel", command = self.quit)
        self.ipCancel.grid(row=2, column=1)

        # Useful key bindings
        self.bind("<Return>", self.keyHelperIpOK)
        self.bind("<Escape>", self.keyHelperIpCancel)

    def createRoom(self, label, roomType = None):
        # Create and record the room
        if roomType == None:
            room = Room(self, label)
        else:
            print("Invalid room type.")
            room = Room(self, label)
            self.rooms[label] = room
        room.pack(side=LEFT)
            
    def createServerWidgets(self):
        #set up menu system
        self.menu = MainMenu(self)
        self.config(menu=self.menu)

    def deck_start(self):
        self.sendToEveryone(STARTDECK)

    def draft_nextPack(self):
        # Switch passing direction
        self.direction = 0 - self.direction
        if len(setList) < 1:
            self.deck_start()
        else:
            nextSet = setList.pop(0)
            # If you want to implement multiple sets,
            # do it with the setList and an input to Pack()
            for client in self.clients.values():
                pack = Pack()
                client.packQueue.append(pack)
                self.sendRobust(client, pack.toPackList())

    def draft_start(self):
        self.sendToEveryone(STARTDRAFT)
        self.state = "DRAFT"


        # We need to mix up the clients, so that they have
        # random seating for the draft
        draftOrder = self.clients.keys()
        random.shuffle(draftOrder)

        # Create doubly linked list of clients
        for i in range(len(draftOrder)):
            client = self.clients[draftOrder[i]]
            client.prev = self.clients[draftOrder[i-1]]
            if i < (len(draftOrder)-1):
                client.next = self.clients[draftOrder[i+1]]
            else:
                client.next = self.clients[draftOrder[0]]

        # We also need to update the order for all the clients
        # Send keys in new order.
        data = NEWPLAYERORDER
        firstClient = self.clients[draftOrder[0]]
        client = firstClient
        while True:
            data = data+client.ID
            client = client.next
            if client == firstClient:
                break
            else:
                data = data+MARK

        self.sendToEveryone(data)
        self.draft_nextPack()


    def game_sendDeckSizes(self, client):
        data = DECKSIZES + str(len(client.deck)).zfill(3)\
                            + str(len(client.opponent.deck)).zfill(3)
        self.sendRobust(client,data)

    def game_sendHandSizes(self, client):
        data = HANDSIZES + str(client.handSize).zfill(2)\
                            + str(client.opponent.handSize).zfill(2)
        self.sendRobust(client,data)

    def game_sendOpponentLife(self,client):
        data = LIFE + str(client.opponent.life).zfill(3)
        self.sendRobust(client,data)

    def game_start(self, player1, player2):
        data = STARTGAME + player1.ID + MARK\
                            + player2.ID
        self.sendToEveryone(data)

        player1.opponent = player2
        player1.challenging = None
        player2.opponent = player1
        player2.challenging = None

    def isUniqueTag(self, tag):
        return not tag in map(lambda x:x.tag, self.clients.values())
    
    def keyHelperIpOK(self, event):
        focused = self.focus_get()
        try:
            if focused.__class__ == Button:
                focused.invoke()
            else:
                self.ipOK.invoke()
        except:
            print("Exception in TopWindow.keyHelperIPOK.")
            return

    def keyHelperIpCancel(self, event):
        try: self.ipCancel.invoke()
        except:
            print("Exception in TopWindow.keyHelperIpCancel.")
            return

    def makeUniqueName(self,baseName):
        if baseName in map(lambda x:x.tag, self.clients.values()):
            return self.makeUniqueName(baseName + '+')
        else:
            return baseName

    def makePlayerlist(self):
        print('Starting to make playerlist.')
        data = PLAYERLIST
        for client in self.clients.values():
            data = data+client.ID+MARK
        data = data[0:-1] #remove the last mark
        print('Successfully made playerlist: ' + data)
        return data

    def removeClient(self, client):
        client.socket.close()
        print("Removed " + client.tag)
        self.clients.pop(client.ID)
        self.sendToEveryone(LEAVE + client.ID)


    def sendRobust(self,recipient,data):
        print("Sending: "+data+" to "+recipient.tag)
        try:
            recipient.socket.sendall(data + ENDPACKET)
        except:
            self.clientsToRemove.append(recipient)
            return
        
    def sendToEveryone(self,data):
        for recipient in self.clients.values():
            self.sendRobust(recipient, data)

        

# Set up card lists
f = open("Cards/SHM_List.txt",'r')
rares = []
uncommons = []
commons = []
lands = [[],[],[],[],[]] # plains, island, swamp, mountain, forest

# Format is <# print runs to choose from>%<# cards from run>
# with run sets delimeted by '='
runsFormat = "2%06=2%05"
runs = [[],[],[],[]]
cardNumbers = dict()

line = f.readline()
while not line == 'PRINT RUNS\n':
    #print ("Line is " + line)
    cardNumbers[line[5:]] = line[0:4]
    if line[4] == 'C':
        commons.append(line[0:4])
    elif line[4] == 'U':
        uncommons.append(line[0:4])
    elif line[4] == 'R':
        rares.append(line[0:4])
    elif line[4] == 'L':
        if line[5:] == 'Plains\n':
            lands[PLAINS].append(line[0:4])
        elif line[5:] == 'Island\n':
            lands[ISLAND].append(line[0:4])
        elif line[5:] == 'Swamp\n':
            lands[SWAMP].append(line[0:4])
        elif line[5:] == 'Mountain\n':
            lands[MOUNTAIN].append(line[0:4])
        elif line[5:] == 'Forest\n':
            lands[FOREST].append(line[0:4])
        else:
            print("Card number "+line[0:4]+" basic land not recognized.")
    else:
        print("Card number "+line[0:4]+" rarity not recognized.")
    line = f.readline()

# Use to run common name with print run consistency check
##line = f.readline()
##commonsRemoved = []
##print("Cards unique to print run:\n")
##while not line == '':
##       if not line == '=\n':
##              try:
##                     card = cardNumbers[line]
##              except:
##                     print(line+"\n")
##              try:
##                     if not card in commonsRemoved:
##                            commons.remove(card)
##                            commonsRemoved.append(card)
##              except:
##                     print(line+" recorded, but not common.\n")
##       line = f.readline()
##
##print("Common numbers not found in print run:\n")
##for card in commons:
##       print(card)
        
line = f.readline() # Get past the PRINT RUNS line
runNumber = 0 # Save which run we're working on
while not line == '':
    if line == '=\n':
        runNumber = runNumber +1
    else:
        card = cardNumbers[line]
        runs[runNumber].append(card)
    line = f.readline()       


root = TopWindow()
root.mainloop()    
