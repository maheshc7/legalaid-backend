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
            self.content = self.__read_pdf()  # .lower()
        except Exception as error:
            raise Exception("Error initializing PdfParser:",
                            str(error)) from error

    def __read_pdf(self):
        """
        Parses the pdf file and returns the full content as string.
        """
        # Using PyMuPDF - fitz library to crop
        try:
            content = ""
            for page_num in range(self.file.page_count):
                page = self.file.load_page(page_num)
                text = page.get_text()
                content += text
            return content
        except Exception as error:
            raise Exception("Error reading PDF content:",
                            str(error)) from error

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

        # content = content.lower()
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

    def extract_meaningful_words(self, text):
        # Process the text with SpaCy
        doc = self.nlp(text)

        meaningful_words = [token.text for token in doc if token.pos_ in {
            "NOUN", "ADJ", "VERB", "PROPN"}]

        return " ".join(meaningful_words)

    def extract_parties_details(self, page):
        """
        Extract plaintiff and defendant details and case number.

        Args:
            page (fitz.Page): The PDF page to extract information from.

        Returns:
            tuple: A tuple containing case number, court details, plaintiff, and defendant.
        """
        try:
            top_half = fitz.Rect(0, 0, page.rect.width, page.rect.height / 2)
            top_half = page.get_textpage(clip=top_half)
            court_bbox = self._find_court_bbox(page, top_half)
            parties_y0 = self._find_parties_y0(page, court_bbox, top_half)

            court_bbox = fitz.Rect(
                50, court_bbox.y0, page.rect.width, parties_y0)
            court_details = self.clean_pdf(
                page.get_text(clip=court_bbox)).title()
            case_num, plaintiff, defendant = self._extract_case_and_parties(
                page, parties_y0
            )

            return case_num, court_details, plaintiff, defendant
        except Exception as error:
            raise Exception("Error extracting parties details:", str(error))

    def _find_court_bbox(self, page, top_half):
        """
        Find the bounding box of the court section.

        Args:
            page (fitz.Page): The PDF page to search on.
            top_half (fitz.TextPage): The top half of the page as a TextPage object.

        Returns:
            fitz.Rect: The bounding box of the court section.
        """
        try:
            court_bbox = page.search_for("superior court", textpage=top_half)
            court_bbox += page.search_for("district court", textpage=top_half)
            court_bbox = sorted(court_bbox, key=lambda x: x.y1)
            return court_bbox[-1]
        except Exception as error:
            raise Exception("Error finding court bounding box:", str(error))

    def _find_parties_y0(self, page, court_bbox, top_half):
        """
        Find the Y0 coordinate for the parties' section.

        Args:
            page (fitz.Page): The PDF page to search on.
            court_bbox (fitz.Rect): The bounding box of the court section.
            top_half (fitz.TextPage): The top half of the page as a TextPage object.

        Returns:
            float: The Y0 coordinate for the parties' section.
        """
        try:
            parties_y0 = court_bbox.y1 + 30
            for term in ["COUNTY", "DISTRICT"]:
                term_bbox = page.search_for(term, textpage=top_half)
                if term_bbox:
                    parties_y0 = min(parties_y0, term_bbox[-1].y1)
            return parties_y0
        except Exception as error:
            raise Exception("Error finding parties Y0 coordinate:", str(error))

    def _find_case_x0_values(self, page, case_page):
        """
        Find the x0 value of the case detail box.

        Args:
            page (fitz.Page): The PDF page to search on.
            case_page (fitz.TextPage): The TextPage containing case details.

        Returns:
            list: A list of x0 values.
        """
        try:
            case_1 = page.search_for("case", textpage=case_page)
            case_2 = page.search_for("No.", textpage=case_page)

            x0_values = [bbox[0].x0 for bbox in (case_1, case_2) if bbox]

            return x0_values
        except Exception as error:
            raise Exception("Error finding case x0 values:", str(error))

    def _extract_case_number(self, case_detail):
        """
        Extract the case number using regex.

        Args:
            case_detail (str): The case details as a string.

        Returns:
            str: The extracted case number.
        """
        try:
            case_num = ""
            case_detail = case_detail.splitlines()
            for line in case_detail:
                line = re.split(r"case no\.|case|no\.:?\s?", line)[-1]
                line = line.replace(" ", "")
                match = re.search(r"([a-z]\S{5,})", line)
                if match:
                    case_num = match.group(1).replace(" ", "").upper()
                    return self.clean_pdf(case_num)
        except Exception as error:
            raise Exception("Error extracting case number:", str(error))

    def _extract_case_and_parties(self, page, parties_y0):
        """
        Extract case number, plaintiff, and defendant.

        Args:
            page (fitz.Page): The PDF page to extract information from.
            parties_y0 (float): The Y0 coordinate for the parties' section.

        Returns:
            tuple: A tuple containing case number, plaintiff, and defendant.
        """
        try:
            defendant_bbox = page.search_for("defendant")[-1]

            case_clip = fitz.Rect(
                page.rect.width / 2, parties_y0 + 20, page.rect.width, defendant_bbox.y0
            )  # mid right
            case_detail = page.get_text(clip=case_clip).lower()
            case_num = self._extract_case_number(case_detail)

            case_page = page.get_textpage(clip=case_clip)
            x0_values = self._find_case_x0_values(page, case_page)
            case_clip.x1 = min(
                x0_values) if x0_values else page.rect.width / 1.75

            parties_clip = fitz.Rect(
                50, parties_y0 + 20, case_clip.x1, defendant_bbox.y1
            )
            parties_page = page.get_textpage(clip=parties_clip)

            plaintiff_bbox = page.search_for(
                "plaintiff", textpage=parties_page)[0]
            defendant_bbox = page.search_for(
                "defendant", textpage=parties_page)[0]
            parties_clip.y1 = defendant_bbox.y1

            plaintiff_bbox = fitz.Rect(
                parties_clip.x0, parties_clip.y0, parties_clip.x1, plaintiff_bbox.y0
            )
            defendant_bbox = fitz.Rect(
                parties_clip.x0,
                plaintiff_bbox.y1 + 20,
                parties_clip.x1,
                defendant_bbox.y0,
            )
            plaintiff = self.clean_pdf(
                page.get_text(clip=plaintiff_bbox)).title()
            defendant = self.clean_pdf(
                page.get_text(clip=defendant_bbox)).title()

            return case_num, plaintiff, defendant
        except Exception as error:
            raise Exception(
                "Error extracting case and parties details:", str(error))

    def get_case_details(self):
        """
        Extracts the details of the case
        Returns:
            case_num (string): A string containing the case number
        """
        try:
            # Extracts information regarding the case
            page = self.file.load_page(0)

            case_num, court, plaintiff, defendant = self.extract_parties_details(
                page)

            case_info = {
                "caseNum": case_num,
                "court": self.extract_meaningful_words(court),
                "client": "",
                "plaintiff": self.extract_meaningful_words(plaintiff),
                "defendant": self.extract_meaningful_words(defendant),
            }
            return case_info
        except Exception as error:
            raise Exception("Error extracting case details:",
                            str(error)) from error

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

        If the extracted task is just a single word or has more than 15 words return the sentence.

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
        text = text.title()
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
                        settings={
                            "STRICT_PARSING": False,
                            "PARSERS": ["absolute-time"],
                            "REQUIRE_PARTS": ['day', 'month', 'year']
                        },
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
            content = self.clean_pdf(self.content)  # .lower())
            events["no event"] = {}
            paragraphs = re.split("\n", content)
            for para in paragraphs:
                para = self.clean_pdf(para)
                new_events = re.findall(
                    r"(\d{1,3}\.[A-Za-z()\-\, ]+)(?:\.|\:)", para)
                if new_events:
                    para = re.sub(
                        r"(\d{1,3}\.[A-Za-z()\-\, ]+)(?:\.|\:)", r"\1:", para)
                new_event = re.search(
                    r"\d{1,3}\. *([A-Za-z()\-\, ]{10,})(?:\:|\.)", para
                )
                para = re.sub(
                    r"\d{1,3}\. *([A-Za-z()\-\, ]{10,})(?:\:|\.)", "", para)
                if new_event:
                    event = new_event.group(1)
                    events[event] = {}

                sentences = self.nlp(para.strip())
                for line in sentences.sents:
                    line = line.text.strip()
                    re_dates = search_dates(
                        line,
                        settings={"STRICT_PARSING": True,
                                  "PARSERS": ["absolute-time"]},
                    )
                    nlp_dates = self.extract_date(line)
                    if not re_dates:
                        re_dates = []

                    dates = nlp_dates if (
                        len(nlp_dates) > len(re_dates)) else re_dates
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

    def get_gpt_events(self, is_authorized):
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

            gpt_events = gpt_parser.get_completion(content)
            return gpt_events
        except Exception as error:
            raise Exception("Error extracting GPT events:",
                            str(error)) from error
