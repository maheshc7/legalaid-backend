"""
Entry point for the application.
Handles the calls to make the Outlook API authentication
Adds new events to the calendar.
"""

import boto3
import json
from flask import Blueprint, jsonify, request
from app.services.pdf_service import PdfService
from app import config

main_app = Blueprint("main_app", __name__)


@main_app.route("/", methods=["GET"])
def index():
    """
    Index page for the server
    """
    return "You have reached the Homepage of LegalAid Backend"


@main_app.route("/case/<case_id>", methods=["GET"])
def get_details(case_id):
    """
    Checks if the request contains the file name,
    Get the file from S3 bucket and process it.
    Returns
        200 : Suceess
        500 : Error
    """
    try:
        filename = str(case_id) + ".pdf"
        filepath = f"./temp_files/{filename}"
        bucket_name = config.S3_BUCKET
        s3_client = boto3.client('s3')
        s3_client.download_file(bucket_name, filename, filepath)

        pdf_service = PdfService(filepath=filepath)

        is_authorized = request.args['is_authorized'].lower() == "true"
        case_and_events = pdf_service.parse_pdf(is_authorized)

        # re-upload the updated(masked) file to s3
        s3_client.download_file(bucket_name, filename, filepath)

        return jsonify(case_and_events), 200

    except Exception as error:
        return jsonify({"error": str(error)}), 400


@main_app.route("/upload", methods=["POST"])
def upload_file():
    """
    Checks if the request consists of a pdf file and
    saves it in as a temporary file before processing it.
    Sends the file to pdfparser and returns the case and events in a json format (as dict).
    Returns
        200 : Suceess
        500 : Error
    """
    try:
        if "file" not in request.files:
            print("here")
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]
        if not file.filename.lower().endswith(".pdf"):
            return (
                jsonify(
                    {"error": "Invalid file format, only PDF files are allowed"}),
                400,
            )

        is_authorized = False
        if "data" in request.form:
            request_data = json.loads(request.form.get('data'))
            # Check if 'is_authorized' is present in the request body and is a boolean
            is_authorized = request_data.get('is_authorized')
            if is_authorized is None or not isinstance(is_authorized, bool):
                is_authorized = False
            print("is Auth: ", is_authorized)

        pdf_service = PdfService(file)
        case_and_events = pdf_service.parse_pdf(is_authorized)

        return jsonify(case_and_events), 200

    except Exception as error:
        return jsonify({"error": str(error)}), 400
