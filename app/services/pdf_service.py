# app/services/pdf_service.py
import os
import tempfile
import uuid

from app.pdfparser import PdfParser


class PdfService:
    def __init__(self, file):
        self.file = file

    def parse_pdf(self):
        try:
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
                self.file.save(temp_file.name)

            parser = PdfParser(temp_file.name)
            case_details = parser.get_case_details()
            events = parser.get_events()
            gpt_events = parser.get_gpt_events(False)

            event_details = []
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
                "gpt_events": gpt_events,
                "length": len(event_details),
            }

            return details

        except Exception as error:
            raise Exception("Error parsing PDF: ", str(error)) from error
        
        finally:
            os.remove(temp_file.name)
