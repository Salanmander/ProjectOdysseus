from Tkinter import *
import tkFileDialog

def save():
  # make some sort of save dialog??
  f = tkFileDialog.asksaveasfile(mode='w', defaultextension=".xml")
  if f is None:
    return

  text = "This is TOTALLY an XML file full of magic cards."
  f.write(text)
  f.close()
  print "Deck saved."

#def load():
  # let them pick the file to load
