#!/usr/bin/env python
import random
from subprocess import call
import os, sys
# External dependencies:
import iota
import pyqrcode

printerName = 'star'

def createQR(char, font, fontSize, Hpos, Vpos, lineSpacing, charSpacing, data):
    "Creates Postscript code for a text based QR code. All 8 parameters are required."
    qrScript = ""
    qrObj = pyqrcode.create(data)
    qrText = (qrObj.text())
    for qrLineCount in range (4, (len(qrText.splitlines()))-4): # There are four blank lines over and under the QR data
        qrLine = qrText.splitlines()[qrLineCount]
        qrLine = qrLine.replace("0", " ")
        qrLine = qrLine.replace("1", char) # This sets what character the QR code will be compriced of
        qrScript += '/'+font+'\n'+str(fontSize)+' selectfont\n'+str(Hpos)+' '+str(Vpos)+' mm moveto\n'+str(charSpacing)+' 0 ('+qrLine+') ashow\n'
        Vpos -= lineSpacing
    return qrScript

print '\n\n           IOTAnote\n\n  Iota Paper Wallet Generator\n  by fakearchitect - oct 2017\n'
print '\n-------------------------------\nAlfa version - Use at own risk!\n-------------------------------\n\n\n'
amountMiota = raw_input('      Enter amount in Mi\n\n    (0.000001-99999999999)\n\n>')
print "\nRendering image...\n"

# Various variables:
IOTAnotePath = os.path.dirname(sys.argv[0]) # Path to this script
with open(IOTAnotePath+'/Postscript/PSbegin.txt', 'r') as bgBeginFile: # The first half of "RenderedImage.ps"
    bgBegin=bgBeginFile.read()
with open(IOTAnotePath+'/Postscript/PSend.txt', 'r') as bgEndFile: # The second half
    bgEnd=bgEndFile.read()
seed = ''
script = bgBegin # Start filling up the Postscript
script += '/mm {360 mul 127 div} def\n 81 121.5 mm moveto' # Set the length unit to millimeter (as opposed to 1/72 inch)
fontbig = '/Courier\n29 selectfont\n'
fontsmall = '/Courier\n24 selectfont\n'
fontamount = '/Courier\n50 selectfont\n75 145 mm moveto\n'
beforetype = '('
aftertype = ') show\n'
noError = True

# Centering the amount by adding spacing before and after amount:
amount=''
amountChars = len(amountMiota)
if (amountChars % 2 == 0):
    iotaAbbr = 'Mi'
    spacing = 6
else:
    iotaAbbr = ' Mi' # If the amount is an odd number, we need to offset the denotation to center it all
    spacing = 5
for i in range(spacing-(amountChars/2)):
    amount += "~"
amount += (amountMiota+iotaAbbr)
for i in range(spacing-(amountChars/2)):
    amount += "~"



# For the seed, we want random length words, but exactly 27 characters on each of the 3 lines. Medium length words are preferred over
# short and long words, so they appear several times in the list of available word lengths.
wordLengths = [3, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 6, 7, 8, 9]
wordLengthArray=[]
wordsPerRow = [1, 1, 1]
for rowNumber in range(0,3):
    row=[11] # The first value is always 11 to begin with. If the row gets more than 27 chars, the excess will be substracted from this.
             # Words from this list and the 10-letter one will only be used if the sum of a row is 27 or 28 characters initially.
    while sum(row) < 27:
        row.append(random.choice(wordLengths))
        wordLengthArray.append(row[-1])
        wordsPerRow[rowNumber] += 1
    row[0]-=(sum(row)-27) # substract any excess
    wordLengthArray.append(row[0])
if sum(wordLengthArray) is not 81:
    noError = False

# Pick words from the lists and add them to the PS:
for i in range(0, len(wordLengthArray)):
    wordLength = str(wordLengthArray[i])
    randomWord = random.choice(open(IOTAnotePath+'/Wordlists/'+wordLength+'letterwords.txt').readlines()).rstrip()
    seed += randomWord
    thefirst = (randomWord[0]).rstrip()
    therest = (randomWord[1:wordLengthArray[i]]).rstrip()
    script += fontbig
    script += beforetype+thefirst+aftertype
    script += fontsmall
    script += beforetype+therest+aftertype
    if i == (wordsPerRow[0] - 1):
        script += '81 112.5 mm moveto'
    if i == (wordsPerRow[0] + wordsPerRow[1] - 1):
        script += '81 103.5 mm moveto'

# Add the Mi amount:
script += fontamount+beforetype+amount+aftertype

# Create text based QR from seed:
script += createQR(char=".", font="Courier", fontSize=23.85, Hpos=103, Vpos=84.15, lineSpacing=1.44, charSpacing=-10, data=seed)

# Finally, add the rest of the Postscript and save the file:
script += bgEnd
PSfile = open(IOTAnotePath+'/Rendered/RenderedImage.ps', 'w')
PSfile.write(script)
PSfile.close()

# Generate address from seed and create a PS file with QR codes and info:
api = iota.Iota('http://null', seed)
response = (api.get_new_addresses(index=0, count=1))
addr1 = (response['addresses'][0])
addrWithChecksum = (addr1 + (iota.Address(addr1)._generate_checksum()[0:9]))
amountIota = int(float(amountMiota) * 1000000) # Iota.link doesn't like decimals, so we convert it to an int
iotaLink = 'https://iota.link/'+str(addrWithChecksum)+'/'+str(amountIota)+'i' # Not yet implemented in the official wallet, but I hope it'll be.
addrScript = '%!PS-Adobe-3.0\n<< /PageSize [595 842] >> setpagedevice\n/mm {360 mul 127 div} def\n'
addrScript += '/Courier-Bold\n24 selectfont\n5 290 mm moveto\n(To give the note value, send an amount of) show\n'
addrScript += '5 280 mm moveto\n('+amountMiota+'Mi to this address:) show\n'
addrScript += createQR(char=".", font="Courier", fontSize=23.85, Hpos=175, Vpos=260, lineSpacing=1.44, charSpacing=-10, data=addrWithChecksum)
addrScript += '/Courier-Bold\n24 selectfont\n5 175 mm moveto\n(Or use iota.link:) show\n'
addrScript += createQR(char=".", font="Courier", fontSize=23.85, Hpos=147, Vpos=160, lineSpacing=1.44, charSpacing=-10, data=iotaLink)
addrScript += '/Courier-Bold\n24 selectfont\n5 60 mm moveto\n(Remember to enlighten the recipient of) show\n'
addrScript += '5 53 mm moveto\n(the note that it is not suitable for) show\n'
addrScript += '5 46 mm moveto\n(long time storage, due to the nature) show\n'
addrScript += '5 39 mm moveto\n(of receipt paper. Heat and light may) show\n'
addrScript += '5 32 mm moveto\n(make the code unreadable, so keep the) show\n'
addrScript += '5 25 mm moveto\n(note out of direct sunshine, and move) show\n'
addrScript += '5 18 mm moveto\n(the funds to another wallet as soon as) show\n'
addrScript += '5 11 mm moveto\n(possible.) show\n'
addrScript += 'showpage'
PSfile = open(IOTAnotePath+'/Rendered/Address.ps', 'w')
PSfile.write(addrScript)
PSfile.close()

if noError: # The error handling is admittedly lacking, I'll have to work on that
    print "Printing...\n"
    call(['lpr -P ' + printerName + ' ' + IOTAnotePath + '/Rendered/Address.ps'], shell=True)
    call(['lpr -P ' + printerName + ' ' + IOTAnotePath + '/Rendered/RenderedImage.ps'], shell=True)
    print "Done.\n"
else:
    print "Error generating seed."

# Clean after printing so nothing is saved on the HDD:
#thefile = open(IOTAnotePath+'/Rendered/RenderedImage.ps', 'w')
#thefile.write('nada')
#thefile.close()
