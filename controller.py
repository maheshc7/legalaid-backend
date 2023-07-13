"""
Entry point for the application.
Handles the calls to make the Outlook API authentication
Adds new events to the calendar.
"""

from flask import Flask, request, jsonify
import uuid
import os
import tempfile
from pdfparser import PdfParser
import concurrent.futures

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

        # Process the PDF file in a separate thread
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(extract_details, temp_file)
            case_info = future.result()
        # # Extract event details from the PDF
        # case_info = extract_details(temp_file)
        os.remove(temp_file.name)
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
                "date" : str(date.date()),
                "description": task
            }

            event_details.append(data)
    
    details["case"] = case_details
    details["events"] = event_details
    details["length"] = len(event_details)
    
    return details

if __name__ == '__main__':
    app.run( threaded=True)
