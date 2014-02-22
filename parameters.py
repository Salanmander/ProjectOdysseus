NETLAG = 1 # number of miliseconds between checking the network
TAG = 'YoungPadawan'
HOST = 'localhost'
PORT = 21567
BUFSIZ = 1024

#Horizontal and vertical resolution
HRES = 1280
VRES = 720
FRAMEWIDTH = 16 # pixel allowances for OS-applied frame
FRAMEHEIGHT = 37

# font data
FONT = "Inconsolata.otf"
FONTURL = "http://levien.com/type/myfonts/" + FONT

# json database location
JSON = "Cards/AllSets.json"
JSONURL = "http://mtgjson.com/json/AllSets.json"

# Location to fetch card back image from
CARDBACKURL = "http://upload.wikimedia.org/wikipedia/en/a/aa/Magic_the_gathering-card_back.jpg"
# "set code" of card images that aren't actually cards (like the card back)
SPECIALSET = "000"
# card info that represents the card back image
BACK = SPECIALSET + "000000"
# file path that gives the mask for the power/toughness box
PTBOX = "Cards/" + SPECIALSET + "/powerBoxMask.png"

# Parameters about card size
THUMBSCALE = 1 # Linear scaling factor to use for small size cards
TITLEFRACTION = 0.12 # This is the fraction of the card that should be
                    # displayed from the top for the title bar to be visible
TYPEFRACTION = 0.638 # Fraction to display the type line and above
VBLACKFRACTION = 0.04 # Fraction that is a single top or bottom black border
POWERBOX_X_FRACTION = 0.70 # horizontal place for power box on small thumbnails
POWERBOX_Y_FRACTION = 0.475 # vertical place
HBORDERFRACTION = 0.075 # Fraction of card for a horizontal border
VTEXTFRACTION = 0.28 # Fraction of card for text box
HTEXTFRACTION = 1-(2*HBORDERFRACTION)
TEXTLINEFRACTION = 1.2 # height of line of text compared to a capital letter

# This is how strong (in average intensity drop) an edge needs to be
CREATURE_EDGE_THRESHOLD = 40 

THUMBREMOVETEXT = True # cut rules text box off thumbnails.
THUMBRETYPETEXT = True # re-types the text, leaving out any that doesn't fit


CARDWIDTH = 220 # 265 is full width of original card images
                # about 180 is reasonably comfortable
                # about 130 is barely readable
CARDHEIGHT = int(CARDWIDTH * 680/480) # aspect ratio based on mtgimage resolution

# Derived parameters
CARDTITLEHEIGHT = int(CARDHEIGHT * TITLEFRACTION)
THUMBWIDTH = int(THUMBSCALE * CARDWIDTH)
if THUMBREMOVETEXT: #If we're removing the text, still have bottom border
    THUMBHEIGHT = int(THUMBSCALE * CARDHEIGHT * \
                      (TYPEFRACTION+VBLACKFRACTION))
else:
    THUMBHEIGHT = int(THUMBSCALE * CARDHEIGHT)
THUMBTITLEHEIGHT = int(THUMBSCALE * CARDHEIGHT * TITLEFRACTION)
THUMBTEXTHEIGHT = int(THUMBSCALE * CARDHEIGHT * VTEXTFRACTION)
THUMBTEXTWIDTH = int(THUMBSCALE * CARDWIDTH * HTEXTFRACTION)

# Other card appearance parameters
TEXTBOXCOLOR = (245,240,235)

# Parameters for waiting window
WAIT_WIDTH = 200 
WAIT_HEIGHT = 500
WAIT_PLAYERWIDTH = 140
WAIT_PLAYERHEIGHT = 140

# Parameters for draft window
DRAFT_PACK_CARDSPERROW = 8 # Number of thumbnails per row in picking window
DRAFT_PLAYERHEIGHT = 140
DRAFT_PLAYERWIDTH = 140
DRAFT_PICKEDHEIGHT = CARDHEIGHT #Picked window fills in next to big card
DRAFT_PICKEDWIDTH = HRES - FRAMEWIDTH - CARDWIDTH #Fills up rest of window
DRAFT_CHATHEIGHT = DRAFT_PLAYERHEIGHT
# Make chat window fit neatly under picked window
DRAFT_CHATWIDTH = DRAFT_PICKEDWIDTH - DRAFT_PLAYERWIDTH
# Unfortunately I haven't yet figured a way to set the size of the
# booster pack display conveniently

# The deck-building window just fills the space available in the grid

# Parameters for game window
GAME_MESSAGEWIDTH = 20 #Characters
GAME_MESSAGENUM = 15
GAME_MESSAGES = ("At the end of your turn...","Untap/upkeep/draw.",\
                 "Main phase.","Combat phase.","Hold on...","Your turn.",\
                 "Declare no blockers.")
GAME_PLAYHEIGHT_BASE = 1400  # Game window dimensions if the cards are full 
GAME_PLAYWIDTH_BASE = 1900   # scale.
GAME_PLAYHEIGHT = GAME_PLAYHEIGHT_BASE*THUMBSCALE
GAME_PLAYWIDTH = GAME_PLAYWIDTH_BASE*THUMBSCALE
GAME_HANDWIDTH = THUMBWIDTH + 4
GAME_HANDHEIGHT = 400
GAME_CHATWIDTH = GAME_PLAYWIDTH 
GAME_CHATHEIGHT = 150
GAME_INFOBARWIDTH = 52
GAME_LABELSPACE = 30 # Space between the tops of indicators for life etc.
GAME_LABELOFFSET = 12 # Shift the labels to center them WRT the life entry box
GAME_DECKROWS = 15 # Number of cards to display in a column when showing an
                   # entire deck.

