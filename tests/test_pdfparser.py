import os
from unittest.mock import Mock, MagicMock, patch
from dotenv import load_dotenv
import pytest
import spacy
from app.services.pdfparser import PdfParser


@pytest.fixture
def pdf_parser():
    """
    Test init function for PdfParser class.
    """
    parser = PdfParser("./Sample Files/Posner -  Scheduling Order.pdf")
    # parser.nlp = MagicMock()
    return parser


# def test_read_pdf(pdf_parser):
#     """
#     Test __read_pdf function of PdfParser class.
#     """
#     # Mock the load_page method to return a mock page object
#     mock_page = Mock()
#     mock_page.get_text.return_value = "Sample content from page"
#     pdf_parser.file.load_page = Mock(return_value=mock_page)

#     result = pdf_parser._PdfParser__read_pdf()

#     assert result == "Sample content from page"


def test_extract_task(pdf_parser):
    """
    Test extract_task function of PdfParser class.
    """
    # pdf_parser.nlp = spacy.load("en_core_web_sm")
    sentence = "plaintiff shall provide full and complete disclosures."
    expected_result = "plaintiff: provide full and complete disclosures"
    result = pdf_parser.extract_task(sentence)
    assert result == expected_result


def test_extract_date(pdf_parser):
    """
    Test extract_date function of PdfParser class.
    """
    text = "The hearing is scheduled for 2022-07-31."
    expected_dates = "2022-07-31"
    result = pdf_parser.extract_date(text)[0][0]
    assert result == expected_dates


def test_clean_pdf(pdf_parser):
    """
    Test clean_pdf function of PdfParser class.
    """
    content = """This is some text with\n\n\nnewlines and     spaces."""
    expected_result = "this is some text with\n newlines and spaces."
    result = pdf_parser.clean_pdf(content)
    assert result == expected_result


def test_get_case_details(pdf_parser):
    """
    Test get_case_details function of PdfParser class.
    """
    mock_page = Mock()
    mock_page.get_text.return_value = "case no.: C123846"
    pdf_parser.file.load_page = Mock(return_value=mock_page)

    expected_result = {
        "caseNum": "C123846",
        "court": "Arizona Superior Maricopa County",
        "plaintiff": "Saul Goodman",
        "defendant": "Harvey Specter",
    }
    result = pdf_parser.get_case_details()
    assert result == expected_result


def test_get_events(pdf_parser):
    """
    Test get_events function of PdfParser class.
    """
    # Mock the content and spacy
    pdf_parser.content = pdf_parser.clean_pdf("""1. Initial disclosures: The parties’ initial disclosures shall be completed by July 1, 2022.\n\
    2. Private mediation. The  parties  shall  participate  in  mediation  using  a  private mediator  agreed  to  by  the  parties.\
    The  parties  shall  complete  mediation  by  December  30, 2022.""")

    result = pdf_parser.get_events()
    print(result)
    assert isinstance(result, dict)
    assert "no event" in result
    assert "initial disclosures" in result
    assert "private mediation" in result


def test_get_gpt_events_unauthorized(pdf_parser):
    """
    Test get_gpt_events function of PdfParser class when unauthorized.
    """
    app_mock = Mock()

    result = pdf_parser.get_gpt_events(app_mock, False)

    assert result == "Not Authorized to use GPT"


@patch("app.services.pdfparser.gpt_parser.get_completion")
def test_get_gpt_events_authorized(mock_get_completion, pdf_parser):
    """
    Test get_gpt_events function of PdfParser class when authorized.
    """
    app_mock = Mock()
    # load_dotenv()
    app_mock.config = {"OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY")}
    mock_get_completion.return_value = [
        {
            "date": "2022-07-01",
            "description": "The parties’ initial disclosures shall be completed",
            "subject": "Initial Disclosures",
        },
        {
            "date": "2022-12-30",
            "description": "The parties shall complete mediation",
            "subject": "Mediation",
        },
        {
            "date": "2022-09-02",
            "description": "The parties shall simultaneously disclose areas of expert testimony",
            "subject": "Expert Witness Disclosure",
        },
    ]

    result = pdf_parser.get_gpt_events(app_mock, True)
    assert isinstance(result, list)
    for event in result:
        assert isinstance(event, dict)
        assert "date" in event
        assert "description" in event
        assert "subject" in event


def test_get_gpt_events_invalid_key(pdf_parser):
    """
    Test get_gpt_events function of PdfParser class when unauthorized.
    """
    app_mock = Mock()
    app_mock.config = {"OPENAI_API_KEY": "invalid_key"}
    with patch(
        "app.services.pdfparser.gpt_parser.get_completion"
    ) as mock_get_completion:
        mock_get_completion.side_effect = Exception(
            "Incorrect API key provided: invalid_key"
        )
        with pytest.raises(Exception) as exc_info:
            pdf_parser.get_gpt_events(app_mock, is_authorized=True)

        assert "Error extracting GPT events:" in str(exc_info.value)
        assert "Incorrect API key provided: invalid_key" in str(exc_info.value)


# Add more test functions...
