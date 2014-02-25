
NETLAG = 1 # number of miliseconds between checking the network
TAG = 'Player'
HOST = 'localhost'
PORT = 21567
BUFSIZ = 1024


FRAMEWIDTH = 16 # pixel allowances for OS-applied frame
FRAMEHEIGHT = 37

# font data
FONT = "Inconsolata.otf"
FONTURL = "http://levien.com/type/myfonts/" + FONT

# directory to store card images. I have this set up to check for
# a file that isn't currently being listed by github so that people can
# easily use a different directory during dev.
try:
    f = open('config.ini')
    CARDDIR = f.readline()
    f.close()
except:
    CARDDIR = "Cards/"

# json database location
JSON = CARDDIR + "AllSets.json"
JSONURL = "http://mtgjson.com/json/AllSets.json"

# Location to fetch card back image from
CARDBACKURL = "http://upload.wikimedia.org/wikipedia/en/a/aa/Magic_the_gathering-card_back.jpg"
# "set code" of card images that aren't actually cards (like the card back)
SPECIALSET = "000"
# card info that represents the card back image
BACK = SPECIALSET + "000000"
# file path that gives the mask for the power/toughness box
PTBOX = CARDDIR + SPECIALSET + "/powerBoxMask.png"

# Parameters about card size
TITLEFRACTION = 0.12 # This is the fraction of the card that should be
                    # displayed from the top for the title bar to be visible
TYPEFRACTION = 0.638 # Fraction to display the type line and above
VBLACKFRACTION = 0.02 # Fraction that is a single top or bottom black border
POWERBOX_X_FRACTION = 0.70 # horizontal place for power box on small thumbnails
POWERBOX_Y_FRACTION = 0.475 # vertical place
HBORDERFRACTION = 0.075 # Fraction of card for a horizontal border
VTEXTFRACTION = 0.28 # Fraction of card for text box
HTEXTFRACTION = 1-(2*HBORDERFRACTION)
TEXTLINEFRACTION = 1.2 # height of line of text compared to a capital letter

# This is how strong (in average intensity drop) an edge needs to be
CREATURE_EDGE_THRESHOLD = 40 

ASPECTRATIO = 680.0/480.0 # aspect ratio based on mtgimage resolution

GAME_PLAYHEIGHT_BASE = 1000  # Game window dimensions if the cards are full 
GAME_PLAYWIDTH_BASE = 1500  # scale.

# Other card appearance parameters
TEXTBOXCOLOR = (245,240,235)


allResOptions = dict()

# --------------------------------------------------------------------------
# parameters for 1280x720 resolution
# --------------------------------------------------------------------------

opts = dict()
allResOptions['1280x720'] = opts

opts['hres'] = 1280 # not an actual guarantee of window size, but used
opts['vres'] = 720  #    to derive some things
opts['thumbscale']=0.5
opts['cardwidth']=180
opts['cardheight']=int(opts['cardwidth']* ASPECTRATIO)
opts['thumbremovetext']=False
opts['thumbretypetext']=True
opts['thumbwidth'] = int(opts['thumbscale']*opts['cardwidth'])
if opts['thumbremovetext']: #If we're removing the text, still have bottom border
    opts['thumbheight'] = int(opts['thumbscale'] * opts['cardheight'] * \
                      (TYPEFRACTION+VBLACKFRACTION))
else:
    opts['thumbheight'] = int(opts['thumbscale'] * opts['cardheight'])
opts['thumbtitleheight'] = int(opts['thumbscale'] * opts['cardheight'] * TITLEFRACTION)
opts['thumbtextheight'] = int(opts['thumbscale'] * opts['cardheight'] * VTEXTFRACTION)
opts['thumbtextwidth'] = int(opts['thumbscale'] * opts['cardwidth'] * HTEXTFRACTION)

# parameters only used in waiting window
opts['wait_width'] = 200 
opts['wait_height'] = 500
opts['wait_playerwidth'] = 140
opts['wait_playerheight'] = 140

# parameters only used in drafting
opts['draft_pack_cardsperrow'] = 8 # Number of thumbnails per row in picking window
opts['draft_playerheight'] = 140
opts['draft_playerwidth'] = 140
opts['draft_pickedheight'] = opts['cardheight'] #Picked window fills in next to big card
opts['draft_pickedwidth'] = opts['hres'] - FRAMEWIDTH - opts['cardwidth'] #Fills up rest of window
opts['draft_chatheight'] = opts['draft_playerheight']
# Make chat window fit neatly under picked window
opts['draft_chatwidth'] = opts['draft_pickedwidth'] - opts['draft_playerwidth']
# Booster pack display could be configured by pixels by making it similar
# to the play area, or maybe the chat box (turn off geometry propogation)

# parameters only used in game window
opts['game_grids']={'chatr':3,'chatc':2,'chatcs':2,
                 'playr':0,'playc':3,'playrs':3,
                 'handr':2,'handc':0,'handrs':2,
                 'dispr':0,'dispc':2,'disprs':3,
                 'cardr':0,'cardc':0,'cardcs':2,
                 'toolr':1,'toolc':0,'toolcs':2,
                 'messr':2,'messc':1,'messrs':2}
opts['game_messagewidth']=20
opts['game_messagenum']=10
opts['game_messages']=("At the end of your turn...","Untap/upkeep/draw.",\
                 "Main phase.","Combat phase.","Hold on...","Your turn.",\
                 "Declare no blockers.")
opts['game_playwidth']=GAME_PLAYWIDTH_BASE*opts['thumbscale']
opts['game_playheight']=GAME_PLAYHEIGHT_BASE*opts['thumbscale']
opts['game_handwidth']=opts['thumbwidth']+4
opts['game_handheight']=200
opts['game_chatwidth'] = opts['game_playwidth']
opts['game_chatheight'] = 100
opts['game_infobarwidth'] = 52
opts['game_labelspace'] = 30 # Space between the tops of indicators for life etc.
opts['game_labeloffset'] = 12 # Shift the labels to center them WRT the life entry box
opts['game_deckrows'] = 15 # Number of cards to display in a column when showing an
                   # entire deck.



