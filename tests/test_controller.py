import io
from unittest.mock import patch
import pytest
from app.run import app as App
from app.services.pdf_service import PdfService


@pytest.fixture
def app():
    app = App
    app.config.update(
        {
            "TESTING": True,
        }
    )
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def test_index(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Homepage" in response.data


def test_upload_file_no_file(client):
    response = client.post("/upload")
    assert response.status_code == 400  # Correct the expected response code
    assert b"No file provided" in response.data


def test_upload_file_invalid_format(client):
    response = client.post(
        "/upload",
        content_type="multipart/form-data",
        data={"file": (io.BytesIO(b"sample content"), "sample.txt")},
    )
    assert response.status_code == 400
    assert b"Invalid file format" in response.data


@patch.object(PdfService, "parse_pdf")
def test_upload_file_success(mock_parse_pdf, client):
    mock_parse_pdf.return_value = {
        "case": {"caseNum": "12345", "court": "Court"},
        "events": [
            {
                "id": "uuid",
                "subject": "Event",
                "date": "2023-07-19",
                "description": "Description",
            }
        ],
        "length": 1,
    }
    response = client.post(
        "/upload",
        content_type="multipart/form-data",
        data={"file": (io.BytesIO(b"sample content"), "sample.pdf")},
    )

    assert response.status_code == 200
    assert b"caseNum" in response.data
    assert b"court" in response.data
