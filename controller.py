"""
Entry point for the application.
Handles the calls to make the Outlook API authentication
Adds new events to the calendar.
"""
import sys
from scheduler import Scheduler, AuthorizeOutlook
from pdfparser import PdfParser

# Uncomment below lines to connect to outlook and add events
if sys.argv[1].lower().endswith(".pdf"):
    filepath = sys.argv[1]
    # account = AuthorizeOutlook().get_account()
    # scheduler = Scheduler(account)
    parser = PdfParser(filepath=filepath)
    case = parser.get_case_details()
    print(case)
    events = parser.get_events()
    for event, subevent in events.items():
        #print(event, "   :   ", subevent)
        event = event.title()
        print(event)
        subject = case + ":" + event
        for task,date in subevent.items():
            task = task.capitalize()
            print("   ",task, "   :   ", date)
            description = event + " : " + task
            start_time = date
            # scheduler.add_event(subject, description, start_time, all_day=True)

    parser.close_pdf()
else:
    print("Please enter a PDF filepath")
