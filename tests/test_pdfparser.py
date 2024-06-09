from unittest.mock import Mock, patch
import pytest
import fitz
from app.services.pdfparser import PdfParser


@pytest.fixture
def pdf_parser():
    """
    Test init function for PdfParser class.
    """
    parser = PdfParser("./Sample Files/Posner -  Scheduling Order.pdf")
    # parser.nlp = MagicMock()
    return parser


@pytest.fixture
def pdf_page(pdf_parser):
    # This fixture can be used to create a mock PDF page for testing
    # You can customize it based on your actual needs
    return pdf_parser.file.load_page(0)

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
    expected_result = "This is some text with\n newlines and spaces."
    result = pdf_parser.clean_pdf(content)
    assert result == expected_result


def test_get_case_details(pdf_parser):
    """
    Test get_case_details function of PdfParser class.
    """
    # mock_page = Mock()
    mock_page = [
        "C123846",
        "Arizona Superior Maricopa County",
        "Saul Goodman",
        "Harvey Specter",
    ]
    pdf_parser.extract_parties_details = Mock(return_value=mock_page

    expected_result = {
        "caseNum": "C123846",
        "court": "Arizona Superior Maricopa County",
        "client": "",
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
    pdf_parser.content = pdf_parser.clean_pdf(
        """1. Initial disclosures: The parties’ initial disclosures shall be completed by July 1, 2022.\n\
    2. Private mediation. The  parties  shall  participate  in  mediation  using  a  private mediator  agreed  to  by  the  parties.\
    The  parties  shall  complete  mediation  by  December  30, 2022."""
    )

    result = pdf_parser.get_events()
    print(result)
    assert isinstance(result, dict)
    assert "no event" in result
    assert "Initial disclosures" in result
    assert "Private mediation" in r


def test_get_gpt_events_unauthorized(pdf_parser):
    """
    Test get_gpt_events function of PdfParser class when unauthorized.
    """
    result = pdf_parser.get_gpt_eve

    assert result == "Not Authorized to use GPT"


@patch("app.services.pdfparser.gpt_parser.get_completion")
def test_get_gpt_events_authorized(mock_get_completion, pdf_parser):
    """
    Test get_gpt_events function of PdfParser class when authorized.
    """
    mock_get_completion.return_value = [
        {
            "date": "2022-07-01",
            "description": "The parties' initial disclosures 
            "subject": "Initial Disclosures",
        },
        {
            "date": "2022-12-30",
            "description": "The parties shall com
            "subject": "Mediation",
        },
        {
            "date": "2022-09-02",
            "description": "The parties shall simultaneously disclose areas of expert testimony",
            "subject": "Expert Witness Disclosure",
        },
    ]

    result = pdf_pars
    assert isinstance(result, list)
    for event in result:
        assert isinstance(event, dict)
        assert "date" in event
        assert "description" in event
        assert "subject" in event


@patch("app.services.gpt_parser.config", autospec=True)
def test_get_gpt_events_invalid_key(mock_config, pdf_parser):
    """
    Test get_gpt_events function of PdfParser class when unauthorized.
    """
    mock_config.OPENAI_API_KEY = "invalid_key"
    with patch(
        "app.services.pdfparser.gpt_parser.get_completion"
    ) as mock_get_completion:
        mock_get_completion.side_effect = Exception(
            "Incorrect API key provided: invalid_key"
        )
        with pytest.raises(Exception) as exc_info:
            pdf_parser.get_gpt_events(is_authorized=True)

        assert "Error extracting GPT events:" in str(exc_info.value)
        assert "Incorrect API key provided: invalid_key" in str(exc_info.value)


def test_find_court_bbox(pdf_parser, pdf_page):
    top_half = pdf_page.get_textpage(clip=pdf_page.rect)
    court_bbox = pdf_parser._find_court_bbox(pdf_page, top_half)
    assert isinstance(court_bbox, fitz.Rect)


def test_find_parties_y0(pdf_parser, pdf_page):
    top_half = pdf_page.get_textpage(clip=pdf_page.rect)
    court_bbox = pdf_parser._find_court_bbox(pdf_page, top_half)
    parties_y0 = pdf_parser._find_parties_y0(pdf_page, court_bbox, top_half)
    assert isinstance(parties_y0, (int, float))


def test_find_case_x0_values(pdf_parser, pdf_page):
    case_page = pdf_page.get_textpage(clip=pdf_page.rect)
    x0_values = pdf_parser._find_case_x0_values(pdf_page, case_page)
    assert isinstance(x0_values, list)


def test_extract_case_number(pdf_parser):
    case_detail = "Case No.: ABC123"
    case_num = pdf_parser._extract_case_number(case_detail.lower())
    assert case_num == "ABC123"


def test_extract_case_and_parties(pdf_parser, pdf_page):
    top_half = pdf_page.get_textpage(clip=pdf_page.rect)
    court_bbox = pdf_parser._find_court_bbox(pdf_page, top_half)
    parties_y0 = pdf_parser._find_parties_y0(pdf_page, court_bbox, top_half)
    case_num, court_details, plaintiff, defendant = pdf_parser.extract_parties_details(
        pdf_page
    )
    assert isinstance(case_num, str)
    assert isinstance(court_details, str)
    assert isinstance(plaintiff, str)
    assert isinstance(defendant, str)
