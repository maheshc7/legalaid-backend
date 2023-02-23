"""
Module for parsing the pdf and returning the events and their associated sub-events and dates
"""
import re
from io import StringIO
import PyPDF2
import spacy
from dateparser.search import search_dates
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser


class PdfParser:
    """
    Class for reading and parsing the passed PDF file.

    Attributes:
        nlp: A spacy model used for splitting paragraphs.
        filepath: Path location of the pdf file to be parsed.
        file: PDF file to be parsed.
        content: Full content of the pdf file.

    Methods:
        __parse: method which reads and
        clean_pdf: trims(sapce and newline) the content of the file.
        get_case_details: function to extract case details
        close_pdf: function to close the pdf
        get_events: function to get the events and their associated subevents and dates.
    """

    def __init__(self, filepath):
        self.nlp = spacy.load("en_core_web_sm")
        self.case_num = None
        self.filepath = filepath
        # creating a pdf file object
        self.file = open(filepath, "rb")
        # creating a pdf reader object
        self.reader = PyPDF2.PdfFileReader(self.file)
        self.num_pages = self.reader.numPages
        self.content = self.__parse().lower()

    def __parse(self):
        """
        Parses the pdf file and returns the full content as string.
        """
        output_string = StringIO()
        parser = PDFParser(self.file)
        doc = PDFDocument(parser)
        rsrcmgr = PDFResourceManager()
        device = TextConverter(rsrcmgr, output_string, laparams=LAParams())
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        for page in PDFPage.create_pages(doc):
            interpreter.process_page(page)

        return output_string.getvalue()

    def close_pdf(self):
        """
        Closes the file
        """
        self.file.close()

    def clean_page(self, content):
        """
        Applies all regex substitutions to remove additional new lines and whitespace.
            Returns:
                The cleaned up string.
        """
        content = content.replace("\n", "")
        content = re.sub("\n\s", "\n", content)
        content = re.sub("\s\n", "\n", content)
        content = re.sub("\n{2,}", "\n", content)
        content = re.sub(" {2,}", " ", content)
        content = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]", "", content)
        content = re.sub("a.m.", "am.", content)
        content = re.sub("p.m.", "pm.", content)
        return content

    def get_case_details(self):
        """
        Extracts the details of the case
            Returns:
                case_num (string): A string containing the case number
                TODO: Extract plaintiff & defendant name, county, attorney assigned and other details.
        """
        # Extracts information regarding the case
        page = self.reader.getPage(0)
        # extracting text from page
        content = page.extractText().lower()
        self.case_num = (
            re.search("(?:case no\.|case|no\.):?\s?([a-z]\w{5,})", content)
            .group(1)
            .replace(" ", "")
            .upper()
        )
        return self.case_num

    def get_events(self):
        """
        Returns the events and their corresponding dates
            Returns:
                events: A dictionary of events and its subevents and corresponding dates.
        """
        events = {}
        event = ""

        content = self.clean_page(self.content)
        # print(repr(content))
        # print(content)
        paragraphs = re.split("(\d{1,3}\. *[A-Za-z()\- ]{10,}\:)", content)
        for para in paragraphs:
            new_event = re.search("\d{1,3}\. *([A-Za-z()\- ]{10,})\:", para)

            if new_event:
                event = new_event.group(1)
                events[event] = []

            sentences = self.nlp(para.strip())
            for line in sentences.sents:
                line = line.text.strip()
                dates = search_dates(
                    line,
                    settings={"STRICT_PARSING": True, "PARSERS": ["absolute-time"]},
                )
                if event and dates:
                    events[event] += (line, dates[0][1])

        return events
