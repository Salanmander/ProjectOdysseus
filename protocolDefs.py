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
           # also sent to server to request said data
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
                # Second char is "for scry": 0 for no, 1 for yes
                # Remaining chars WHEN SENDING CLIENT->SERVER are
                # the number of cards to view from top:
                # 0 for all, N for "min(N, remaining cards in deck)
                # Server adds the appropriate deck list and returns it
                # Remaining chars WHEN SENDING SERVER->CLIENT are
                # the card infos, 9 chars per card
DECKREMOVE = 'cf' # Tells server to remove one copy of given card from
                    # (0/1) self or opponent's deck
                    # Will ALWAYS take the copy closest to top of deck, even
                    # if the remove event was triggered by clicking
                    # a different copy
                    
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
# It is added by TopWindow.sendRobust.
ENDPACKET = '~`mq|'

# Indices used for basic lands
PLAINS = 0
ISLAND = 1
SWAMP = 2
MOUNTAIN = 3
FOREST = 4

