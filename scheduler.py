
from O365 import Account, MSGraphProtocol, FileSystemTokenBackend
from dotenv import load_dotenv
import os

# TO DO: Store & Read credentials from separate file
load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
SECRET_ID = os.getenv("CLIENT_SECRET")


class AuthorizeOutlook:
    """
    Class for authenticating outlook api

    Attributes:
        credentials: Stores the client id and secret id
        scopes: The scope of the API for this project, Permission to read and write to calendar
        account = Gets the account resources related to the specified credentials
        authorize: Boolean value which stores the status of whether the account was authenticated using the given scope.

    Methods:
        get_account: gets the account if authorized
    """
    def __init__(self):
        self.credentials = (CLIENT_ID, SECRET_ID)
        self.protocol = MSGraphProtocol()
        self.scopes = self.protocol.get_scopes_for(["Calendars.ReadWrite","offline_access"])#["Calendars.ReadWrite","offline_access"]
        token_backend = FileSystemTokenBackend(token_path='tokens', token_filename='o365_token.txt')
        self.account = Account(self.credentials, protocol=self.protocol, token_backend = token_backend)
        self.authorized = self.account.is_authenticated
        if not self.authorized:
            self.authorized = self.account.authenticate(scopes=self.scopes)

    def get_account(self):
        """
            returns the account object if authentication is successfull, else returns unauthorized
        """
        if self.authorized:
            return self.account
        else:
            return "Unauthorized"


class Scheduler:
    """
    Class for creating and managing events on the Outlook Calendar

    Attributes:
    scheduler: instance to work with calendar events for the specified account resource
    calendar: default calendar of the current user.

    Methods:

    """
    def __init__(self, account):
        self.scheduler = account.schedule()
        self.calendar = self.scheduler.get_calendar(calendar_name='legalaid')
        if(self.calendar is None):
            print("Create new calendar")
            self.calendar = self.scheduler.new_calendar(calendar_name='legalaid') #self.scheduler.get_default_calendar()

    def get_schedule(self):
        """returns the scheduler object"""
        return self.scheduler

    def get_calendar(self):
        """returns the calendar object"""
        return self.calendar

    def add_event(self, subject, description, start_time, end_time=None, all_day=True):
        """
        Creates an event in the user's calendar
            Parameters:
                subject (string): A string for event title
                description (string): A string for event description
                start_time (datetime): A datetime object for the start_time of the event.
                subject (datetime, optional, default = None): A datetime object for the start_time of the event.
                all_day (boolean, optional, default=True): A boolean value indicating if the event is an all day event

            Returns:
                None

        """
        new_event = self.calendar.new_event(subject=subject)
        new_event.body = description
        new_event.start = start_time
        new_event.is_all_day = all_day
        if end_time:
            new_event.end = end_time
        new_event.save()
