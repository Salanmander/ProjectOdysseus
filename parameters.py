
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

# Parameters about card size. Several of these are out of date since switching to
# mtgimage images
TITLEFRACTION = 0.11 # This is the fraction of the card that should be
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

CARDHEIGHT = 680 # resolution of original images
CARDWIDTH = 480

GAME_PLAYHEIGHT_BASE = 3000  # Game window dimensions if the cards are full 
GAME_PLAYWIDTH_BASE = 3700  # scale.

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
opts['thumbscale']=0.24
opts['bigscale'] = 0.5
opts['bigcardwidth']=int(opts['bigscale']*CARDWIDTH)
opts['bigcardheight']=int(opts['bigscale']*CARDHEIGHT)
opts['thumbremovetext']=False
opts['thumbretypetext']=True
opts['thumbwidth'] = int(opts['thumbscale']*CARDWIDTH)
if opts['thumbremovetext']: #If we're removing the text, still have bottom border
    opts['thumbheight'] = int(opts['thumbscale'] * CARDHEIGHT * \
                      (TYPEFRACTION+VBLACKFRACTION))
else:
    opts['thumbheight'] = int(opts['thumbscale'] * CARDHEIGHT)
opts['thumbtitleheight'] = int(opts['thumbscale'] * CARDHEIGHT * TITLEFRACTION)
opts['thumbtextheight'] = int(opts['thumbscale'] * CARDHEIGHT * VTEXTFRACTION)
opts['thumbtextwidth'] = int(opts['thumbscale'] * CARDWIDTH * HTEXTFRACTION)

# parameters only used in waiting window
opts['wait_width'] = 200 
opts['wait_height'] = 500
opts['wait_playerwidth'] = 140
opts['wait_playerheight'] = 140

# parameters only used in drafting
opts['draft_grids'] = {'packr':0,'packc':2,'packcs':2,'packrs':2,
                       'cardr':2,'cardc':0,
                       'pickr':2,'pickc':1,'pickcs':3,
                       'chatr':1,'chatc':0,'chatcs':2,
                       'plyrr':0,'plyrc':0,'plyrcs':2}
opts['deck_grids'] = {'deckr':0,'deckc':2,'deckcs':1,'deckrs':2,
                      'landr':0,'landc':3,'landrs':2}
opts['draft_pack_cardsperrow'] = 8 # Number of thumbnails per row in picking window
opts['draft_playerheight'] = 140
opts['draft_playerwidth'] = 310
opts['draft_pickedheight'] = opts['bigcardheight'] #Picked window fills in next to big card
opts['draft_pickedwidth'] = opts['hres'] - FRAMEWIDTH - opts['bigcardwidth']#Fills up rest of window
opts['draft_chatheight'] = 190
opts['draft_chatwidth'] = opts['draft_playerwidth']
# Booster pack display could be configured by pixels by making it similar
# to the play area, or maybe the chat box (turn off geometry propogation)

opts['deck_deckwidth'] = 790
opts['deck_deckheight'] = opts['draft_chatheight']+opts['draft_playerheight']


# parameters only used in game window
opts['game_grids']={'chatr':3,'chatc':0,'chatcs':4,
                 'playr':0,'playc':4,'playrs':4,
                 'handr':0,'handc':2,'handrs':1,'handcs':2,
                 'dispr':2,'dispc':3,'disprs':1,
                 'cardr':0,'cardc':0,'cardcs':2,
                 'toolr':2,'toolc':0,'toolcs':3,
                 'messr':1,'messc':0,'messrs':1,'messcs':4}
opts['game_messagewidth']=20
opts['game_messagerows']=2
opts['game_messagecols']=3
opts['game_messages']=("At the end of your turn...","Untap/upkeep/draw.",\
                 "Main phase.","Combat phase.","Hold on...","Your turn.",\
                 "Declare no blockers.")
opts['game_playwidth']=GAME_PLAYWIDTH_BASE*opts['thumbscale']
opts['game_playheight']=GAME_PLAYHEIGHT_BASE*opts['thumbscale']
opts['game_handwidth']=opts['thumbwidth']+4
opts['game_handheight']=opts['bigcardheight']
opts['game_chatwidth'] = opts['hres']-FRAMEWIDTH-opts['game_playwidth']
opts['game_chatheight'] = 150
opts['game_infobarwidth'] = 120
opts['game_infobarheight'] = 100
opts['game_labelspace'] = 30 # Space between the tops of indicators for life etc.
opts['game_opponentlifeX'] = 80 # x position in infobar for opponent indicators
opts['game_opponentlifeY'] = 0 # y position (for top)
opts['game_selflifeX'] = 0 # x position in infobar for opponent indicators
opts['game_selflifeY'] = 0 # y position (for top)
opts['game_deckoffset'] = 12 # offset between life and deck numbers to stay centered
opts['game_deckrows'] = 15 # Number of cards to display in a column when showing an
                   # entire deck.


# --------------------------------------------------------------------------
# parameters for 1280x1024 resolution
# --------------------------------------------------------------------------

opts = dict()
allResOptions['1280x1024'] = opts

opts['hres'] = 1280 # not an actual guarantee of window size, but used
opts['vres'] = 1024 #    to derive some things
opts['thumbscale']=0.273
opts['bigscale'] = 0.5
opts['bigcardwidth']=int(opts['bigscale']*CARDWIDTH)
opts['bigcardheight']=int(opts['bigscale']*CARDHEIGHT)
opts['thumbremovetext']=False
opts['thumbretypetext']=True
opts['thumbwidth'] = int(opts['thumbscale']*CARDWIDTH)
if opts['thumbremovetext']: #If we're removing the text, still have bottom border
    opts['thumbheight'] = int(opts['thumbscale'] * CARDHEIGHT * \
                      (TYPEFRACTION+VBLACKFRACTION))
else:
    opts['thumbheight'] = int(opts['thumbscale'] * CARDHEIGHT)
opts['thumbtitleheight'] = int(opts['thumbscale'] * CARDHEIGHT * TITLEFRACTION)
opts['thumbtextheight'] = int(opts['thumbscale'] * CARDHEIGHT * VTEXTFRACTION)
opts['thumbtextwidth'] = int(opts['thumbscale'] * CARDWIDTH * HTEXTFRACTION)

# parameters only used in waiting window
opts['wait_width'] = 200 
opts['wait_height'] = 500
opts['wait_playerwidth'] = 140
opts['wait_playerheight'] = 140

# parameters only used in drafting
opts['draft_grids'] = {'packr':0,'packc':0,'packcs':3,'packrs':1,
                       'cardr':1,'cardc':0,
                       'pickr':1,'pickc':1,'pickcs':2,
                       'chatr':2,'chatc':1,'chatcs':1,
                       'plyrr':2,'plyrc':2,'plyrcs':1}
opts['deck_grids'] = {'deckr':0,'deckc':0,'deckcs':3,'deckrs':1,
                      'landr':2,'landc':0,'landrs':1}
opts['draft_pack_cardsperrow'] = 8 # Number of thumbnails per row in picking window
opts['draft_playerheight'] = 140
opts['draft_playerwidth'] = 140
opts['draft_pickedheight'] = opts['bigcardheight'] #Picked window fills in next to big card
opts['draft_pickedwidth'] = opts['hres'] - FRAMEWIDTH - opts['bigcardwidth'] #Fills up rest of window
opts['draft_chatheight'] = opts['draft_playerheight']
# Make chat window fit neatly under picked window
opts['draft_chatwidth'] = opts['draft_pickedwidth'] - opts['draft_playerwidth']
# Booster pack display could be configured by pixels by making it similar
# to the play area, or maybe the chat box (turn off geometry propogation)

opts['deck_deckwidth'] = opts['hres']-FRAMEWIDTH
opts['deck_deckheight'] = 400

# parameters only used in game window
opts['game_grids']={'chatr':4,'chatc':2,'chatcs':1,
                 'playr':0,'playc':2,'playrs':4,
                 'handr':2,'handc':0,'handrs':3,'handcs':1,
                 'dispr':2,'dispc':1,'disprs':1,
                 'cardr':0,'cardc':0,'cardcs':2,
                 'toolr':1,'toolc':0,'toolcs':2,
                 'messr':3,'messc':1,'messrs':2,'messcs':1}
opts['game_messagewidth']=20
opts['game_messagerows']=16
opts['game_messagecols']=1
opts['game_messages']=("At the end of your turn...","Untap/upkeep/draw.",\
                 "Main phase.","Combat phase.","Hold on...","Your turn.",\
                 "Declare no blockers.")
opts['game_playwidth']=GAME_PLAYWIDTH_BASE*opts['thumbscale']
opts['game_playheight']=GAME_PLAYHEIGHT_BASE*opts['thumbscale']
opts['game_handwidth']=opts['thumbwidth']+4
opts['game_handheight']=450
opts['game_chatwidth'] = opts['game_playwidth']
opts['game_chatheight'] = 100
opts['game_infobarwidth'] = 120
opts['game_infobarheight'] = 100
opts['game_labelspace'] = 30 # Space between the tops of indicators for life etc.
opts['game_opponentlifeX'] = 80 # x position in infobar for opponent indicators
opts['game_opponentlifeY'] = 0 # y position (for top)
opts['game_selflifeX'] = 0 # x position in infobar for opponent indicators
opts['game_selflifeY'] = 0 # y position (for top)
opts['game_deckoffset'] = 12 # offset between life and deck numbers to stay centered
opts['game_deckrows'] = 15 # Number of cards to display in a column when showing an
                   # entire deck.



