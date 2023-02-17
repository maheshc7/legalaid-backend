from scheduler import Scheduler, AuthorizeOutlook
from pdfparser import PdfParser

#Uncomment below lines to connect to outlook and add events

# account = AuthorizeOutlook().get_account()
# scheduler = Scheduler(account)
parser = PdfParser("Sainz - Scheduling Order (Court Filed).pdf")
case = parser.get_case_details()
print(case)
events = parser.get_events()
for event,dates in events.items():
    print(event,"   :   ", dates)
#     subject = case + ":" + event
#     description = "Event Description:" + event
#     start_time = dates[0]
#     scheduler.add_event(subject,description, start_time,all_day=True)
    
parser.close_pdf()