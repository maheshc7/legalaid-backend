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
                TODO: Extract plaintiff & defendant name, county, attorney assigned etc.
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
    
    def extract_task(self,sentence):
        """
        This algorithm uses the spaCy library to tokenize and parse the input sentence. 
        First identifies the action verb in the sentence by finding the first verb in the sentence.
        Then it looks for the object or complement of the verb by searching for related dependencies 
        such as direct object, clausal complement, open clausal complement, or subject complement.
        Checks if the current token has any left or right children in the dependency tree, 
        which indicates that it is part of a noun chunk. 
        If so, it includes all the tokens in the subtree of the current token as part of the task. 
        Otherwise, it just includes the current token as part of the task.

        If the extracted task is just a single word or has more than 15 words we return the sentence itself.

        Parameter:
            sentence (string): A string

        Returns:
            task (string): A string 
        """
        doc = self.nlp(sentence)
        task = ""
        for token in doc:
            if token.pos_ == "VERB":
                task = token.text
                break
        for token in doc:
            if token.text == task:
                continue
            if token.dep_ in ["dobj", "ccomp", "xcomp", "attr"]:
                # check if token is part of a noun chunk
                if token.n_lefts > 0 or token.n_rights > 0:
                    task += " " + " ".join([t.text for t in token.subtree])
                else:
                    task += " " + token.text
        task = task.strip()
        task = re.sub(r'[^\w\s]', '', task) #remove punctuation
        print(repr(task), len(task))
        return (sentence if not (2<=len(task.split(" "))<=15) else task)

    def get_events(self):
        """
        Returns the events and their corresponding dates
            Returns:
                events: A dictionary of events and its subevents and corresponding dates.
        """
        events = {}
        event = ""

        content = self.clean_page(self.content)
        paragraphs = re.split("(\d{1,3}\. *[A-Za-z()\- ]{10,}\:)", content)
        for para in paragraphs:
            new_event = re.search("\d{1,3}\. *([A-Za-z()\- ]{10,})\:", para)

            if new_event:
                event = new_event.group(1)
                events[event] = {}

            sentences = self.nlp(para.strip())
            for line in sentences.sents:
                line = line.text.strip()
                dates = search_dates(
                    line,
                    settings={"STRICT_PARSING": True, "PARSERS": ["absolute-time"]},
                )

                if event and dates:
                    for date in dates:
                        lines = [line]
                        if len(dates) > 1:
                            lines = line.split(date[0])
                        new_line =lines[0].replace(date[0],'')
                        task = self.extract_task(new_line)
                        events[event][task] = date[1]
                        if len(lines) > 1:
                            line = lines[1]

        return events