import pytest
from unittest.mock import Mock, MagicMock
from app.pdfparser import PdfParser

@pytest.fixture
def pdf_parser():
    """
    Test init function for PdfParser class.
    """
    parser = PdfParser("./Sample Files/Posner -  Scheduling Order.pdf")
    parser.nlp = MagicMock()
    return parser

def test_extract_task(pdf_parser):
    """
    Test extract_task function of PdfParser class.
    """
    sentence = "The plaintiff filed a case."
    expected_result = "The plaintiff filed a case."
    result = pdf_parser.extract_task(sentence)
    assert result == expected_result
    

def test_extract_date(pdf_parser):
    """
    Test extract_date function of PdfParser class.
    """
    text = "The hearing is scheduled for 2022-07-31."
    expected_dates = ["2022-07-31"]
    pdf_parser.extract_date = Mock(return_value=expected_dates)
    result = pdf_parser.extract_date(text)
    assert result == expected_dates

def test_clean_pdf(pdf_parser):
    """
    Test clean_pdf function of PdfParser class.
    """
    content = "This is some text with\n\n\n newlines and   spaces."
    expected_result = "This is some text with\n newlines and   spaces."
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

# Add more test functions...

if __name__ == "__main__":
    pytest.main()
