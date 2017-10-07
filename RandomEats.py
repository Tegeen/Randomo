
import sys
import time
import datetime
import random
import traceback
import telepot
import requests
import json
from telepot.loop import MessageLoop
from telepot.delegate import per_chat_id, create_open, pave_event_space
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton

#For Google Dirve API linking to Google Sheetes
import gspread
from oauth2client.service_account import ServiceAccountCredentials

global coordinates

class User(telepot.helper.ChatHandler):
    def __init__(self, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)


#---------------variables and greeting message-----------------------#
    def open(self, initial_msg, seed):
        self.sender.sendMessage('Welcome to Random Eats! Available commands.\n/listeateries - list all eateries nearby\n/randomeatery - generate random nearby eatery\n/feedback - give us your feedback')
        return True  # prevent on_message() from being called on the initial message

#---------------repeated functions for use-----------------------------#
    def getlocation(self):
        markup = ReplyKeyboardMarkup(keyboard=[
                [KeyboardButton(text='Location', request_location=True)]
        ], one_time_keyboard = True)
        location = self.sender.sendMessage('Please share your current location', reply_markup=markup)
        return location

    def geteaterydata(self,coordinates):
        #API url 
        baseurl= "https://maps.googleapis.com/maps/api/place/nearbysearch/json" #get json output
        basequery = "?"

        #query parameters
        location = "location="
        location += coordinates
        basetype = "&type="
        types="cafe|restaurant" #only display cafes and restaurants
        baserad = "&radius="
        radius = "500" #default distance from user location

        #Key to use Google Place API
        key = "&key=AIzaSyBOurCkVQACWK9HIxJcQzda785XXb71IsI"

        #entire query to attach at back of API url
        query = basequery + location + basetype + types + baserad + radius

        fullurl = baseurl + query  + key
        print(fullurl)
        #Get JSON file from API for information on eateries
        res_json = requests.get(fullurl).json()
        resjson = res_json["results"]
        print("marker here")
        returnedinfo =""
        for item in resjson:
            #information to get from JSON file
            ophours = item.get("opening_hours")
            if ("'open_now': False") in repr(ophours): #only list shops open now
                donothing = 0
            else:
                name = item.get("name")
                rating = item.get("rating")
                vicinity = item.get("vicinity")
                thisitem = "Name: %s \nLocation: %s\nRating(1-5):%s" %(name, vicinity, rating,)
                if ("'open_now': True") in repr(ophours): 
                    thisitem += "\nOpen now"
                else:
                    thisitem += "\nOpening hours unknown"
                thisitem += "\n\n"
                returnedinfo += str(thisitem)
        return str(returnedinfo)
        
#-----------(1)-list all nearby eateries--------------#
    def _alleat(self, coordinates):
        alleateries = self.geteaterydata(coordinates) #refer to above geteaterydata()
        self.sender.sendMessage(alleateries)
        self.close()

#-----------(2)-generate random eatery----------------#
    def _randeat(self,coordinates):
        alleateries = self.geteaterydata(coordinates) #refer to above geteaterydata()
        listdetails = alleateries.split('\n')  #split into list       
        numoeats = (len(listdetails)-1)/5
        print (numoeats)
        randomeat = int(random.randint(0,numoeats))*5 #select random eatery "Name" line
        randeatery = "\n".join(listdetails[randomeat:randomeat+5])
        self.sender.sendMessage(randeatery) 
        self.sender.sendMessage('Eatery: #%d\nIs this eatery OK?\n/ok or /notok ?')
    
#------------possible inputs form user----------------#
    def on_chat_message(self, msg):
        #get data from user input for telegram msg fields
        content_type, chat_type, chat_id = telepot.glance(msg)

        #ensure data sent are not stickers, pictures, documents etc

        #get text
        if content_type == 'text': 
            userin = msg['text']
            global num

            #
            if userin == '/listeateries':
                num=1 #indicate to function to generate list
                self.getlocation() #get location then go to elif content_type == 'location' below
                self.sender.sendMessage('Loading the list of eateries:')

            #generate a random eatery
            elif userin == '/randomeatery':
                num=2 #indicate to function to generate only 1
                self.getlocation() #get location then go to ielif content_type == 'location' below

            # check if the user is agreeable with generated eatery
            elif userin == '/ok' and num == 2:
                self.sender.sendMessage('Enjoy your meal!')
                num=0 #inform bot that no longer checking for agreeability
                self.close()
            elif userin == '/notok' and num == 2:
                self.sender.sendMessage('Please generate another eatery!')
                num=0 #inform bot that no longer checking for agreeability
                self.close()

            #feedback
            elif userin == '/feedback':
                self.sender.sendMessage('To leave us a comment, \ntype /feedback -your comment-\n\nTo partipate in our user testing, please click on this link: https://docs.google.com/forms/d/e/1FAIpQLSc1JWS2EZI7Gv0yKgnOjFO9TlyOcW4jeCouQhIMH3PtzVFk0w/viewform')
            elif ("/feedback") in userin:
                usercomment = userin[9:] #remove /feedback and leave only the comment

                #Link to spreadsheet on Google Docs using Google drive API
                # use creds to create a client to interact with the Google Drive API
                scope = ['https://spreadsheets.google.com/feeds']
                creds = ServiceAccountCredentials.from_json_keyfile_name("keyfile.json", scope)
                client = gspread.authorize(creds)
 
                # Find a workbook by name and add row to exiting rows
                sheet = client.open("RandomEatsFeedback").sheet1
                nowDT = datetime.datetime.now() #get current date and time
                row = [str(nowDT),usercomment] #[time, comment] will be added
                index = int(sheet.row_count)+1
                sheet.insert_row(row, index)
                
                self.close()

            #Input error handling
            else:
                self.sender.sendMessage('Invalid reply.')
                self.close()

        #get location and find nearby eateries!
        elif content_type == 'location':
            location = msg['location']
            lrepr = (repr(location))
            #replace unneeded part of string to leave only coordinates
            a = lrepr.replace("{'latitude': ", "")
            b = a.replace(" 'longitude': ", "")
            coordinates = b.replace("}", "")
            print(coordinates)
            if num == 1: #generate list
                eateries = self._alleat(coordinates)
            elif num == 2: #generate one eatery only
               eateries = self._randeat(coordinates)
            
            
        #invalid input handling
        else:
            self.sender.sendMessage('Please input only plain text')
            self.close()

#------------------timeout----------------------------#
                
    def on__idle(self, event):
        self.sender.sendMessage('Timeout')
        self.close()


#----------------------MAIN----------------------------#

TOKEN = "420741794:AAEZAyVossclOyogZfHJOqwL3N-kHDv3uOE"

bot = telepot.DelegatorBot(TOKEN, [
    pave_event_space()(
        per_chat_id(), create_open, User,timeout=120),
])
MessageLoop(bot).run_as_thread()
print('Listening ...')

while 1:
    time.sleep(10)
