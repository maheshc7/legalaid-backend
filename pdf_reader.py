# importing required modules
import PyPDF2
import datefinder
import re

from O365 import Account, MSGraphProtocol
from datetime import datetime

CLIENT_ID = '6f3df88c-8168-4592-b1a0-bf4b7ef4c3e7'
SECRET_ID = 'f.p8Q~.k1_gxUFFruCv0rXczzKks0XoKUtvSOb~O'

credentials = (CLIENT_ID, SECRET_ID)

protocol = MSGraphProtocol() 
#protocol = MSGraphProtocol(defualt_resource='<sharedcalendar@domain.com>') 
scopes = ['Calendars.ReadWrite']
account = Account(credentials, protocol=protocol)

if account.authenticate(scopes=scopes):
    print('Authenticated!')


schedule = account.schedule()
calendar = schedule.get_default_calendar() 

# creating a pdf file object
pdfFileObj = open('sample-scheduling-order1.pdf', 'rb')

# creating a pdf reader object
pdfReader = PyPDF2.PdfFileReader(pdfFileObj)

# printing number of pages in pdf file
print(pdfReader.numPages)

# creating a page object
pageObj = pdfReader.getPage(0)

# extracting text from page
content = pageObj.extractText()
print(repr(content))
case = re.search('Case\s+Number:(.+)\n', content).group(1).replace(" ",'')
print(case)
paragraphs =  content.split("\n \n")
for i,line in enumerate(paragraphs):
    #print("Paragraph:",i)
    print(line)
    dates = list(datefinder.find_dates(line)) 
    event = re.match('\d+\.(.+)\:', line)
    if event:
        event = case+": "+event.group(1)
        print(event)
        print(dates)
        new_event = calendar.new_event(subject=event)
        new_event.body = "Event Description:" + event
        new_event.start = dates[0]
        new_event.is_all_day = True
        new_event.save()
    else:
        print("No Event Found")
    print("-----------------------------------------")
    
# closing the pdf file object
pdfFileObj.close()
