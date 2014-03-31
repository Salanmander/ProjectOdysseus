from Tkinter import *
import json
import tkFileDialog

def save(cards):
  # make some sort of save dialog??
  f = tkFileDialog.asksaveasfile(mode='w', defaultextension=".json")
  if f is None:
    return
  saveToFile(cards,f)


def saveToFile(cards,f):
  # temporary structure to keep track of what cards we have seen
  tempDict = dict()
  for card in cards:
    if card in tempDict.keys():
      tempDict[card]['numCopies'] = tempDict[card]['numCopies'] + 1
    else:
      tempDict[card] = {'numCopies':1}
    
  # Save format:
  # Array of dicts,
  # dict fields:
  #   card (same representation as given in the input array)
  #   numCopies
  saveStructure = []
  for key in tempDict:
    entry = {'card': key,
             'numCopies': tempDict[key]['numCopies']}
    saveStructure.append(entry)


  text = json.dumps(saveStructure)
  f.write(text)
  f.close()
  print "Deck saved."

def load():
  # let them pick the file to load
  f = tkFileDialog.askopenfile(mode='r')
  if f is None:
    return None
  
  text = f.read()
  f.close()
  return json.loads(text)
