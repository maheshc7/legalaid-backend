"""
Entry point for the application.
Handles the calls to make the Outlook API authentication
Adds new events to the calendar.
"""
# import sys
from flask import Flask, request, jsonify
import uuid
import tempfile
# from scheduler import Scheduler, AuthorizeOutlook
from .pdfparser import PdfParser

# Uncomment below lines to connect to outlook and add events
# if sys.argv[1].lower().endswith(".pdf"):
#     filepath = sys.argv[1]
#     # account = AuthorizeOutlook().get_account()
#     # scheduler = Scheduler(account)
#     parser = PdfParser(filepath=filepath)
#     case = parser.get_case_details()
#     print(case)
#     events = parser.get_events()
#     for event, subevent in events.items():
#         #print(event, "   :   ", subevent)
#         event = event.title()
#         print(event)
#         subject = case + ":" + event
#         for task,date in subevent.items():
#             task = task.capitalize()
#             print("   ",task, "   :   ", date)
#             description = event + " : " + task
#             start_time = date
#             # scheduler.add_event(subject, description, start_time, all_day=True)

#     parser.close_pdf()
# else:
#     print("Please enter a PDF filepath")

app = Flask(__name__)

# Define a custom middleware function to handle CORS headers
@app.after_request
def add_cors_headers(response):
    # Replace '*' with the appropriate origin(s) allowed to make requests
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response

@app.route('/', methods=['GET'])
def index():
    return "You have reached the Homepage of LegalAid Backend"

@app.route('/upload', methods=['POST'])
def upload_file():
    # Check if a file was included in the request
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    
    # Check if the file has a PDF extension
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Invalid file format, only PDF files are allowed'}), 400

    try:
        # Save the uploaded file to a temporary file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            file.save(temp_file.name)

        # Extract event details from the PDF
        case_info = extract_details(temp_file)
        
        # Return the events in JSON format
        return jsonify(case_info), 200

    except Exception as error:
        return jsonify({'error': str(error)}), 500

def extract_details(file):
    details ={}
    parser = PdfParser(file)
    case_details = parser.get_case_details()

    events = parser.get_events()

    event_details = []
    for event, subevent in events.items():
        if event == "no event":
            continue
        event = event.title()
        for task,date in subevent.items():
            task = task.capitalize()
            data = {
                "id" : uuid.uuid4(),
                "subject": event,
                "date" : date,
                "description": task
            }

            event_details.append(data)
    
    details["case"] = case_details
    details["events"] = event_details
    
    return details

if __name__ == '__main__':
    app.run()
