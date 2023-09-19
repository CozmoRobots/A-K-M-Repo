from pyzbar.pyzbar import decode, ZBarSymbol
import qrcode
import pyqrcode
import cozmo
from PIL import Image
import time
from cozmo.util import degrees
import socket
from socket import error as socket_error

############################################################
# Generating the QR codes for all 52 cards
############################################################

# specials = {
#     11: 'Jack',
#     12: 'Queen',
#     13: 'King',
#     14: 'Ace',
# }

# for j in ['Hearts', 'Clubs', 'Diamonds', 'Spades']:
#     for i in range(2, 15):
#         if i > 10:
#             card = f'{specials[i]}_{j}'
#             # print(card)
#             img = qrcode.make(card)
#             # Cards will be saved in the folder cards
#             img.save(f'cards/{specials[i]}_{j}.png')
#         else:
#             card = f'{i}_{j}'
#             # print(card)
#             img = qrcode.make(card)
#             img.save(f'cards/{i}_{j}.png')

############################################################
# Identify the cards and send the info over the network
############################################################

# dict for special values
special_values = {
    'Jack': 10,
    'Queen': 10,
    'King': 10,
    'Ace': 1,
}

# function for reading QR codes
def read_qrcode(robot):

    robot.world.wait_for(cozmo.world.EvtNewCameraImage)
    img_latest = robot.world.latest_image.raw_image
    img_convert = img_latest.convert('L')
    decodeImage = decode(img_convert,symbols=[ZBarSymbol.QRCODE])

    if len(decodeImage)>0:
        codeData = decodeImage[0]
        myData = codeData.data
        myString = myData.decode('ASCII')
        return myString
    
    return False

def cozmo_program(robot: cozmo.robot.Robot):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket_error as msg:
        robot.say_text("socket failed" + msg).wait_for_completed()
    ip = "10.0.1.10"
    port = 5000
    
    try:
        s.connect((ip, port))
    except socket_error as msg:
        robot.say_text("socket failed to bind").wait_for_completed()
    cont = True
    
    robot.say_text("ready").wait_for_completed()   

    # name of cozmo
    cozmo_name = "Psi"

    robot.set_head_angle(degrees(25)).wait_for_completed()

    # number of cards that cozmo will read
    cardsToRead = 2

    cards = []
    value_in_hand = 0
    
    while cont:
        # read the cards
        card = read_qrcode(robot)
        if card:
            if card not in cards:
                try:
                    value_in_hand += int(card.split("_")[0])
                except:
                    value_in_hand += int(special_values[(card.split("_")[0])])
                 
                # make cozmo say the card name and hand value   
                robot.say_text(f'{card.split("_")[0]} of {card.split("_")[1]}, hand value is {value_in_hand}').wait_for_completed()
                cards.append(card)

            if len(cards) >= cardsToRead:
                # Hit or Stay, Cozmo will hit for hand value >= 13
                if value_in_hand <= 13: 
                    robot.say_text("Hit").wait_for_completed()
                    robot.turn_in_place(degrees(360)).wait_for_completed()
                else:
                    robot.say_text("Stay").wait_for_completed()
                    robot.turn_in_place(degrees(90)).wait_for_completed()
                
                # Send the card info over the network
                myString = cozmo_name
                for c in cards:
                    myString = myString + f";{c}"                 

                s.sendall(myString.encode('utf-8'))

                # print(myString.encode('utf-8'))
                break
    
    return

cozmo.run_program(cozmo_program, use_viewer=True, force_viewer_on_top=False)
