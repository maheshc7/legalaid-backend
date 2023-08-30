import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import pytest
from app.services.pdf_service import PdfService

# Fixture for mocking the Flask app
@pytest.fixture
def app_mock():
    return Mock()

# Fixture for mocking the PDF file
@pytest.fixture
def pdf_file_mock():
    return Mock()

# Fixture for mocking the PdfParser class
@pytest.fixture
def pdf_parser_mock():
    return MagicMock()

# Test the parse_pdf method
@patch("app.services.pdf_service.PdfParser", autospec=True)
@patch("tempfile.NamedTemporaryFile", autospec=True)
@patch("os.remove", autospec=True)
def test_parse_pdf(os_remove_mock, tempfile_mock, pdf_parser_mock, pdf_file_mock, app_mock):
    """
    Test the PdfParser Service 
    Mock the PdfParser and pdf_file to test only the working of the Service class.
    """
    # Arrange
    temp_file_instance = tempfile_mock.return_value.__enter__.return_value
    temp_file_instance.name = "tempfile_name"
    today = datetime.now()

    pdf_parser_instance = pdf_parser_mock.return_value
    pdf_parser_instance.get_case_details.return_value = {"caseNum": "C123", "court": "Court"}
    pdf_parser_instance.get_events.return_value = {
        "Event 1": {"Subevent 1": today},
        "Event 2": {"Subevent 2": today},
    }
    pdf_parser_instance.get_gpt_events.return_value = [
        {"date": "2023-07-03", "description": "GPT Event 1"},
        {"date": "2023-07-04", "description": "GPT Event 2"},
    ]

    pdf_service = PdfService(pdf_file_mock)

    # Act
    result = pdf_service.parse_pdf(app_mock)

    # Assert
    assert result == {
        "case": {"caseNum": "C123", "court": "Court"},
        "events": [
            {
                "id": result["events"][0]["id"],
                "subject": "Event 1",
                "date": str(today.date()),
                "description": "Subevent 1",
            },
            {
                "id": result["events"][1]["id"],
                "subject": "Event 2",
                "date": str(today.date()),
                "description": "Subevent 2",
            },
        ],
        "gpt_events": [
            {"date": "2023-07-03", "description": "GPT Event 1"},
            {"date": "2023-07-04", "description": "GPT Event 2"},
        ],
        "length": 2,
    }

    # Ensure that PdfParser methods were called
    pdf_parser_mock.assert_called_once_with("tempfile_name")
    pdf_parser_instance.get_case_details.assert_called_once()
    pdf_parser_instance.get_events.assert_called_once()
    pdf_parser_instance.get_gpt_events.assert_called_once_with(app_mock, False)
    pdf_parser_instance.close_pdf.assert_called_once()

    # Ensure that tempfile methods were called
    tempfile_mock.assert_called_once_with(suffix=".pdf", delete=False)
    # temp_file_instance.__exit__.assert_called_once()

    # Ensure that the temporary file was not removed
    os_remove_mock.assert_called_once()

# TODO: Add more tests to cover different scenarios
