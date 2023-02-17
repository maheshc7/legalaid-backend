from io import StringIO
import datefinder
import re
import PyPDF2
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser



class PdfParser:
    def __init__(self,filepath):
        self.caseNum = None
        self.filepath = filepath
        # creating a pdf file object
        self.file = open(filepath, 'rb')
        # creating a pdf reader object
        #TODO: Account for other file types
        self.reader = PyPDF2.PdfFileReader(self.file)
        self.numPages = self.reader.numPages
        self.content = self.__parse().lower()
        

    def __parse(self):
        output_string = StringIO()
        with open(self.filepath, 'rb') as in_file:
            parser = PDFParser(in_file)
            doc = PDFDocument(parser)
            rsrcmgr = PDFResourceManager()
            device = TextConverter(rsrcmgr, output_string, laparams=LAParams())
            interpreter = PDFPageInterpreter(rsrcmgr, device)
            for page in PDFPage.create_pages(doc):
                interpreter.process_page(page)

        return output_string.getvalue()
    
        
    def close_pdf(self):
        self.file.close()
        
    def clean_page(self):
        #TODO: Remove extra spaces and newlines
        return
    
    def get_case_details(self):
        #Extracts information regarding the case
        page = self.reader.getPage(0)
        # extracting text from page
        content = page.extractText().lower()
        self.caseNum = re.search('(?:case no\.|case|no\.):?\s?([a-z]\w{5,})', content).group(1).replace(" ",'').upper()
        #TODO: Extract plaintiff & defendant name, county, attorney assigned and other details.
        return self.caseNum
    
    def get_events(self):
        events= {}
        event = ""

        content = self.content
        content = content.replace('\n','')
        content = re.sub('\n\s', '\n',content)
        content = re.sub('\s\n', '\n',content)
        content = re.sub('\n{2,}', '\n',content)
        content = re.sub(' {2,}', ' ',content)
        #print(repr(content))
        #print(content)
        paragraphs =  re.split('(\d+\.? *[A-Za-z()\- ]{10,}\:)', content)
        for para in paragraphs:
            new_event = re.search('\d+\.? *([A-Za-z()\- ]{10,})\:', para)
            
            if new_event:
                event = new_event.group(1)
                events[event] = []
                
            dates = list(datefinder.find_dates(para,strict=True))
            if event:
               events[event]+= dates
            
        return events