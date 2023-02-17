from O365 import Account, MSGraphProtocol
from datetime import datetime

#TO DO: Store & Read credentials from separate file
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