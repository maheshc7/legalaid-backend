# app/services/pdf_service.py
import os
import tempfile
import uuid

from app.services.pdfparser import PdfParser


class PdfService:
    """
    Service class for PdfParser
    """

    def __init__(self, file):
        self.file = file

    def parse_pdf(self, is_authorized):
        """
        Creates a temporary file for the passed file and calls PdfParser on this file
        Extracts the case details, events and gpt_events if authorized
        TODO: Gpt authorization is hardcoded to False, will create a separate endpoint for it.
        """
        try:
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
                self.file.save(temp_file.name)

            parser = PdfParser(temp_file.name)
            case_details = parser.get_case_details()

            event_details = []
            if is_authorized:
                event_details = parser.get_gpt_events(is_authorized)

            else:
                events = parser.get_events()
                for event, subevent in events.items():
                    if event == "no event":
                        continue
                    event = event.title()
                    for task, date in subevent.items():
                        task = task.capitalize()
                        data = {
                            "id": str(uuid.uuid4()),
                            "subject": event,
                            "date": str(date.date()),
                            "description": task,
                        }
                        event_details.append(data)

            details = {
                "case": case_details,
                "events": event_details,
                "length": len(event_details),
            }

            return details

        except Exception as error:
            raise Exception("Error parsing PDF: ", str(error)) from error

        finally:
            parser.close_pdf()
            os.remove(temp_file.name)
