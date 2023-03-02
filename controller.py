"""
Entry point for the application.
Handles the calls to make the Outlook API authentication
Adds new events to the calendar.
"""
from scheduler import Scheduler, AuthorizeOutlook
from pdfparser import PdfParser

# Uncomment below lines to connect to outlook and add events

account = AuthorizeOutlook().get_account()
scheduler = Scheduler(account)
parser = PdfParser("Sample Files/Posner -  Scheduling Order.pdf")
case = parser.get_case_details()
print(case)
events = parser.get_events()
for event, subevent in events.items():
    #print(event, "   :   ", subevent)
    event = event.title()
    print(event)
    subject = case + ":" + event
    for task,dates in subevent.items():
        task = task.capitalize()
        print(task, "   :   ", dates)
        description = event + " : " + task
        start_time = dates[0]
        scheduler.add_event(subject, description, start_time, all_day=True)

parser.close_pdf()
