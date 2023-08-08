import json

import openai
# from flask import current_app

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())

# openai.api_key  = current_app.config["OPENAI_API_KEY"]

def get_completion(content, model="gpt-3.5-turbo"):
    """
     Sends the scheduling order content to chatGPT model and retrieves the desired output in JSON.

    Parameter:
        content (string): A string
        model (string): OpenAI model, default gpt-3.5-turbo
    Returns:
        response (string): A string
    """
    prompt = f"""
    Extract the following details from the scheduling order for each procedure:
    - Procedure title (we will call this the subject)
    - Task to be carried out for that procedure (we will call this description)
    - Deadline or date of the procedure (in the format YYY-MM-DD)

    The scheduling order is delimited with triple backticks.
    Format your response as a list of JSON objects with
    "date", "description", "subject" as the keys.
    Like the following example: 
    [{{  "date": "1998-09-21",
        "description": "The  parties  shall  simultaneously  disclose  areas  of  expert testimony",
        "subject": "Expert Witness Disclosure"
        }},]
        Don't add newline or \ characters.
    Each sentence will contain one or more dates and will describe a procedure or task or event.
    The subject should be a title for the procedure, specific for each procedure and not generic titles.
    The description should describe the procedure or task or event and the description brief and to the point. 
    For each sentence describing a procedure and containing a date, \
    create a JSON item for that sentence with the above mentioned keys.
    If the sentence has two or more dates, create separate JSON item for each date. DO not skip any date.
    If the information isn't present, use blank values.
    Don't add dates in them as we already have a separate field for dates.

    Scheduling order text: ```{content}```
    """

    messages = [
        {'role': 'system', 'content': 'You are a legal assistant.'},
        {"role": "user", "content": prompt}
        ]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0, # this is the degree of randomness of the model's output
    )
    # TODO: Add error handling. Make sure it is in json format else retry.
    output = response.choices[0].message["content"]
    output = json.loads(output)

    return output
