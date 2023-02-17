# importing required modules
import PyPDF2
import datefinder
import re

from O365 import Account, MSGraphProtocol
from datetime import datetime

#TODO: Store credentials in a separate file
CLIENT_ID = '6f3df88c-8168-4592-b1a0-bf4b7ef4c3e7'
SECRET_ID = 'f.p8Q~.k1_gxUFFruCv0rXczzKks0XoKUtvSOb~O'

class AuthorizeOutlook:
    def __init__(self):
        self.credentials = (CLIENT_ID, SECRET_ID)
        
        self.protocol = MSGraphProtocol() 
        self.scopes = ['Calendars.ReadWrite']
        self.account = Account(self.credentials, protocol=self.protocol)
        self.authorized = self.account.authenticate(scopes=self.scopes)
        
    def get_account(self):
        if self.authorized:
            return self.account
        else:
            return "Unauthorized"

class Scheduler:
    def __init__(self,account):
        self.scheduler = account.schedule()
        self.calendar = self.scheduler.get_default_calendar()
        
    def get_schedule(self):
        return self.scheduler
    
    def get_calendar(self):
        return self.calendar
    
    def add_event(self,subject,description,start_time,end_time=None,all_day=True):
        new_event = self.calendar.new_event(subject=subject)
        new_event.body = "Event Description:" + description
        new_event.start = start_time
        new_event.is_all_day = all_day
        if end_time:
            new_event.end = end_time
        new_event.save()
        
class PdfParser:
    def __init__(self,filepath):
        self.caseNum = None
        self.filepath = filepath
        # creating a pdf file object
        self.file = open(filepath, 'rb')
        # creating a pdf reader object
        #TODO: Account for other file types
        self.reader = PyPDF2.PdfFileReader(self.file)
        self.numPages = self.reader.numPages
        
    def close_pdf(self):
        self.file.close()
        
    def clean_page(self):
        #TODO: Remove extra spaces and newlines
        return
    
    def get_case_details(self):
        #Extracts information regarding the case
        page = self.reader.getPage(0)
        # extracting text from page
        content = page.extractText()
        self.caseNum = re.search('Case\s+Number:(.+)\n', content).group(1).replace(" ",'')
        #TODO: Extract plaintiff & defendant name, county, attorney assigned and other details.
        return self.caseNum
    
    def get_events(self):
        events= {}
        #TODO: Parse all pages
        page = self.reader.getPage(0)
        # extracting text from page
        content = page.extractText()
        paragraphs =  content.split("\n \n")
        for i,line in enumerate(paragraphs):
            #print("Paragraph:",i)
            #print(line)
            dates = list(datefinder.find_dates(line)) 
            event = re.match('\d+\.(.+)\:', line)
            if event:
                event = event.group(1)
                #print(event)
                #print(dates)
                events[event] = dates
            #else:
            #    print("No Event Found")
            #print("-----------------------------------------")
        
        return events
    
        

account = AuthorizeOutlook().get_account()
scheduler = Scheduler(account)
parser = PdfParser("sample-scheduling-order1.pdf")
case = parser.get_case_details()
events = parser.get_events()
print(events)
for event,dates in events.items():
    subject = case + ":" + event
    description = "Event Description:" + event
    start_time = dates[0]
    scheduler.add_event(subject,description, start_time,all_day=True)
    
parser.close_pdf()
