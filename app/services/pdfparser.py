"""
Module for parsing the pdf and returning the events and their associated sub-events and dates
"""
import re

import fitz
import spacy
from dateparser.search import search_dates

import app.services.gpt_parser as gpt_parser


class PdfParser:
    """
    Class for reading and parsing the passed PDF file.

    Attributes:
        nlp: A spacy model used for splitting paragraphs.
        file: PDF file to be parsed.
        content: Full content of the pdf file.

    Methods:
        __parse: method which reads and
        clean_pdf: trims(sapce and newline) the content of the file.
        get_case_details: function to extract case details
        close_pdf: function to close the pdf
        extract_task: function to extract the title/subject from a sentence
        extract_dates: extract the dates from a sentence
        get_events: function to get the events and their associated subevents and dates.
        get_gpt_events: function to get the list of procedures and dates in JSON using ChatGPT
    """

    def __init__(self, filepath):
        try:
            self.nlp = spacy.load("en_core_web_sm")
            # creating a pdf file object
            self.file = fitz.open(filepath, filetype="pdf")
            self.content = self.__read_pdf().lower()
        except Exception as error:
            raise Exception("Error initializing PdfParser:", str(error)) from error

    def __read_pdf(self):
        """
        Parses the pdf file and returns the full content as string.
        """
        ###Using PyMuPDF - fitz library to crop
        try:
            content = ""
            for page_num in range(self.file.page_count):
                page = self.file.load_page(page_num)
                text = page.get_text()
                content += text
            return content
        except Exception as error:
            raise Exception("Error reading PDF content:", str(error)) from error

    def close_pdf(self):
        """
        Closes the file
        """
        self.file.close()

    def clean_pdf(self, content):
        """
        Applies all regex substitutions to remove additional new lines and whitespace.
            Returns:
                The cleaned up string.
        """
        
        content = content.lower()
        content = re.sub(r"\n\s+", "\n ", content)
        content = re.sub(r"(\s\n)+", " \n", content)
        content = re.sub(r"( +)", " ", content)
        content = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]", "", content)
        content = re.sub(r"\d{1,2}\s\n", "", content)
        content = re.sub(r"(\W\d{1,2}\.\s)\n+", r"\n \1", content)
        content = re.sub(r"\n(\d{1,2}\.)", r"\n \1", content)
        content = re.sub(r"\n(\S+?)", r"\1", content)
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
        try:
            court = "Arizona Superior Maricopa County"
            plaintiff = "Saul Goodman"
            defendant = "Harvey Specter"
            # Extracts information regarding the case
            page = self.file.load_page(0)
            # extracting text from page
            content = page.get_text().lower()
            match = re.search(r"(?:case no\.|case|no\.):?\s?([a-z]\w{5,})", content)
            if match:
                case_num = match.group(1).replace(" ", "").upper()
            else:
                case_num = ""
            
            case_info = {
                "caseNum": case_num,
                "court": court,
                "plaintiff": plaintiff,
                "defendant": defendant,
            }
            return case_info
        except Exception as error:
            raise Exception("Error extracting case details:", str(error)) from error


    def extract_task(self, sentence):
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
        try:
            doc = self.nlp(sentence)
            task = ""
            for token in doc:
                if token.pos_ == "VERB":
                    task = token.text
                    break
            for token in doc:
                if token.lemma_ in ["plaintiff", "defendant", "attorney"]:
                    task = token.text + ": " + task

                if token.text == task:
                    continue
                if token.dep_ in ["dobj", "ccomp", "xcomp", "attr"]:
                    # check if token is part of a noun chunk
                    if token.n_lefts > 0 or token.n_rights > 0:
                        task += " " + " ".join([t.text for t in token.subtree])
                    else:
                        task += " " + token.text
            task = task.strip()
            return sentence if not (3 <= len(task.split(" ")) <= 15) else task
        except Exception as error:
            raise Exception("Error extracting task:", str(error)) from error

    def extract_date(self, text):
        """
        Extract the dates using spacy library
        """
        # process the text with spaCy
        try:
            doc = self.nlp(text)
            dates = []
            # iterate over each entity in the document
            for ent in doc.ents:
                # check if the entity is a date
                if ent.label_ == "DATE":
                    # print the text and label of the date entity
                    date = search_dates(
                        ent.text,
                        settings={"STRICT_PARSING": False, "PARSERS": ["absolute-time"]},
                    )
                    if date:
                        dates.append(date[0])
            return dates
        except Exception as error:
            raise Exception("Error extracting dates:", str(error)) from error

    def get_events(self):
        """
        Returns the events and their corresponding dates
            Returns:
                events: A dictionary of events and its subevents and corresponding dates.
        """
        try:
            events = {}
            event = ""
            content = self.clean_pdf(self.content)
            events["no event"] = {}
            paragraphs = re.split("\n", content)
            for para in paragraphs:
                para = self.clean_pdf(para)
                new_events = re.findall("(\d{1,3}\.[A-Za-z()\-\, ]+)(?:\.|\:)", para)
                if new_events:
                    para = re.sub(r"(\d{1,3}\.[A-Za-z()\-\, ]+)(?:\.|\:)", r"\1:", para)
                new_event = re.search(r"\d{1,3}\. *([A-Za-z()\-\, ]{10,})(?:\:|\.)", para)
                para = re.sub(r"\d{1,3}\. *([A-Za-z()\-\, ]{10,})(?:\:|\.)", "", para)
                if new_event:
                    event = new_event.group(1)
                    events[event] = {}

                sentences = self.nlp(para.strip())
                for line in sentences.sents:
                    line = line.text.strip()
                    re_dates = search_dates(
                        line,
                        settings={"STRICT_PARSING": True, "PARSERS": ["absolute-time"]},
                    )
                    nlp_dates = self.extract_date(line)
                    if not re_dates:
                        re_dates = []

                    dates = nlp_dates if (len(nlp_dates) > len(re_dates)) else re_dates

                    if not event:
                        event = "no event"

                    if event and len(dates) > 0:
                        for date in dates:
                            lines = [line]
                            if len(dates) > 1:
                                lines = line.split(date[0])
                            new_line = lines[0].replace(date[0], "")
                            task = self.extract_task(new_line)
                            if task in events[event]:
                                task = line
                            events[event][task] = date[1]
                            if len(lines) > 1:
                                line = lines[1]

            return events
        except Exception as error:
            raise Exception("Error extracting events:", str(error)) from error
    
    def get_gpt_events(self,app, is_authorized):
        """
        Returns the events and their corresponding dates
            Returns:
                events: List of JSON items containing the subject, description and dates.
        """
        if not is_authorized:
            return "Not Authorized to use GPT"
        try:
            content = self.clean_pdf(self.content)
            sentences = self.nlp(content)
            content = ""
            for line in sentences.sents:
                line = line.text.strip()
                nlp_dates = self.extract_date(line)
                if nlp_dates:
                    content += line

            gpt_events = gpt_parser.get_completion(app, content)
            return gpt_events
        except Exception as error:
            raise Exception("Error extracting GPT events:", str(error)) from error
                