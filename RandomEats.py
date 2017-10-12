
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

#For Google Drive API linking to Google Sheetes
import gspread
from oauth2client.service_account import ServiceAccountCredentials

global coordinates #user coordinates
global numofeats #numberofeateriesleft

class User(telepot.helper.ChatHandler):
    def __init__(self, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)

#------------possible inputs form user----------------#
            
    def on_chat_message(self, msg):
        #get data from user input for telegram msg fields
        content_type, chat_type, chat_id = telepot.glance(msg)

        #ensure data sent are not stickers, pictures, documents etc

        #get text
        if content_type == 'text' and msg['text'] != '/notok':
            userin = msg['text']
            global num
            
            if userin == '/start':
                self.sender.sendMessage('Welcome to Random Eats! Let us find all open eateries for you!\nAvailable commands.\n/start - list these commands\n/listeateries - list all eateries nearby\n/randomeatery - generate random nearby eatery\n/findeatery - find eatery by keyword\n/feedback - give us your feedback')
        
            #list all eateries
            if userin == '/listeateries':
                num=1 #indicate to function to generate list
                self.getlocation() #get location then go to elif content_type == 'location' below
                self.sender.sendMessage('Loading the list of eateries:')

            #generate a random eatery
            if userin == '/randomeatery':
                num=2 #indicate to function to generate only 1
                self.getlocation() #get location then go to ielif content_type == 'location' below

            # check if the user is agreeable with generated eatery
            if userin == '/ok':
                self.sender.sendMessage('Enjoy your meal!')
                num=0 #inform bot that no longer checking for agreeability
                self.close()

            #perform text search for eateries
            if userin == '/findeatery':
                self.sender.sendMessage('To search for eateries by keywords, \ntype /findeatery -search text-')
                
            elif ("/findeatery") in userin:
                global keywords
                num=3 #indicate to function to do keyword search
                keywords = userin.replace("-", "") #remove - if user types those
                keywords = keywords[12:] #remove "/findeatery "
                self.getlocation() #get location then go to ielif content_type == 'location' below
                

            #feedback
            if userin == '/feedback':
                self.sender.sendMessage('To leave us a comment, \ntype /feedback -your comment-\n\nTo partipate in our user testing, please click on this link: https://docs.google.com/forms/d/e/1FAIpQLSc1JWS2EZI7Gv0yKgnOjFO9TlyOcW4jeCouQhIMH3PtzVFk0w/viewform')
            elif ("/feedback") in userin:
                userin = userin.replace("-", "") #remove - if user types those
                usercomment = userin[10:] #remove "/feedback " and leave only the comment

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


        #get location and find nearby eateries!
        elif content_type == 'location':
            location = msg['location']
            lrepr = (repr(location))
            #replace unneeded part of string to leave only coordinates
            a = lrepr.replace("{'latitude': ", "")
            b = a.replace(" 'longitude': ", "")
            global coordinates
            coordinates = b.replace("}", "")
            
            if num == 1: #generate list
                eateries = self._alleat(coordinates)
                num = 0
                
            elif num == 2: #generate one eatery only
                firsttime = True #first time getting list of eateries nearby
                untilempty = False #there are still nearby eateries that have no been listed
                self._randeat(coordinates,firsttime,untilempty)
                
            elif num == 3: #generate one eatery only
                self._findeat(coordinates,keywords)
                num = 0
                
        elif content_type == 'text' and msg['text'] == '/notok' and num == 2:
            userin = msg['text']
            self.sender.sendMessage('Generating another eatery...')
            #Run self._randeat while telling function that it is not the first time running and there are still eateries to display
            untilempty2 = self._randeat(coordinates,False,False)
            if untilempty2 == True:
                num = 0
                self.sender.sendMessage('There are no more eateries left! \nT.T')
                self.close()
   
        #invalid input handling
        else:
            self.sender.sendMessage('Please input either the commands available for you or other plain text')
            self.close()

#------------------timeout----------------------------#
                
    def on__idle(self, event):
        self.sender.sendMessage('Timeout! Sorry >  <')
        self.close()

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
        radius = "2000" #default distance from user location

        #Key to use Google Place API
        key = "&key=AIzaSyBOurCkVQACWK9HIxJcQzda785XXb71IsI"

        #entire query to attach at back of API url
        query = basequery + location + basetype + types + baserad + radius

        fullurl = baseurl + query  + key
        #Get JSON file from API for information on eateries
        res_json = requests.get(fullurl).json()
        resjson = res_json["results"]
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
        if returnedinfo != "": #there are eateries found nearby and result is not empty
            return str(returnedinfo)
        else: #no information found for nearby eateries
            return ("No eateries found! T.T")
        
#-----------(1)-list all nearby eateries--------------#
    def _alleat(self, coordinates):
        alleateries = self.geteaterydata(coordinates) #refer to above geteaterydata()
        self.sender.sendMessage(alleateries)
        self.close()

#-----------(2)-generate random eatery----------------#
    def _randeat(self,coordinates,firsttime,untilempty):

        #no eatery data acquired and sorted yet
        if firsttime == True:
            global alleateries
            alleateries = self.geteaterydata(coordinates) #refer to above geteaterydata()
            if alleateries == "No eateries found nearby! T.T":
                self.sender.sendMessage(alleateries)
                self.close() #exit
                
        if untilempty == False:
            listdetails = alleateries.split('\n')  #split into list
            listdetails[:-1]#remove extra \n at back of list
            numoeats = (len(listdetails)-1)/5
            randomeat = int(random.randint(0,numoeats-1))*5 #select random eatery "Name" line
            randeatery = "\n".join(listdetails[randomeat:randomeat+5])
            self.sender.sendMessage(randeatery) 

            #remove eatery that has been printed
            randeatery += "\n"

            alleateries = alleateries.replace(randeatery,'')
            numoeats=numoeats-1 #remove one eatery from list of acquired eateries
            self.sender.sendMessage('Is this eatery OK?\n/ok or /notok?\n If no, there are %d eater(y/ies) left' % numoeats)
            if numoeats == 0:
                return True;
            elif numoeats > 0:
                return False;

#-----------(3)-find eatery by keyword----------------#
    def _findeat(self,coordinates,keywords):
        #Get information from API
        baseurl= "https://maps.googleapis.com/maps/api/place/textsearch/json" #get json output with text search
        basequery = "?query="

        #split keywords
        keyword = keywords.replace(" ", "+").replace("\n","+") #replace all newlines and spaces with + for the query

        #get within range 
        location = "&location="
        location += coordinates
        lookforeats = "&radius=100000&type=restaurant|cafe"
        

        #Key to use Google Place API
        key = "&key=AIzaSyBOurCkVQACWK9HIxJcQzda785XXb71IsI"

        #entire query to attach at back of API url
        query = basequery + keyword + location + lookforeats

        fullurl = baseurl + query  + key
        #Get JSON file from API for information on eateries
        res_json = requests.get(fullurl).json()
        resjson = res_json["results"]
        returnedinfo =""
        for item in resjson:
            #information to get from JSON file
            name = item.get("name")
            rating = item.get("rating")
            vicinity = item.get("formatted_address")
            thisitem = "Name: %s \nLocation: %s\nRating(1-5):%s" %(name, vicinity, rating,)
            ophours = item.get("opening_hours")
            if ("'open_now': False") in repr(ophours): 
                thisitem += "\nClosed now"
            elif ("'open_now': True") in repr(ophours): 
                thisitem += "\nOpen now"
            else:
                thisitem += "\nOpening hours unknown"
            thisitem += "\n\n"
            returnedinfo += str(thisitem)
        if returnedinfo != "": #if eateries can be found
            self.sender.sendMessage(str(returnedinfo))
        else:
            self.sender.sendMessage("No eateries found within 100km! T.T")
    
#----------------------MAIN----------------------------#

TOKEN = "420741794:AAEZAyVossclOyogZfHJOqwL3N-kHDv3uOE"

bot = telepot.DelegatorBot(TOKEN, [
    pave_event_space()(
        per_chat_id(),create_open, User,timeout=120),
])
MessageLoop(bot).run_as_thread()
print('Listening ...')

while 1:
    time.sleep(10)
