import os, csv, time
import pandas as pd
from chatwrap import gemini, openaigpt

from litreview0 import *
from litreviewlib import *

def get_fullprompt(fulltext):
    exclude_text = "  " + "\n  ".join([f"{key}: {value}" for key, value in exclude_codes.items()])
    include_text = "  " + "\n  ".join([f"{key}: {value}" for key, value in include_codes.items()])
    return f"""{abstract_prompt}

The following is the full paper, as downloaded as a PDF:
{text}

Based on this information, should this paper be included in the review? If *not*, please classify this with one or more of the following codes:
{exclude_text}
If it *should* be included, classify it with one or more of the following codes:
{include_text}

Provide a succinct explanation, and only mention codes identified for this paper."""

print(get_fullprompt("Full paper text..."))

def submit_single_abstract_openai(doi, fulltext):
    prompt = get_fullprompt(fulltext)
    return openaigpt.single_prompt(prompt)

def submit_single_abstract_gemini(doi, fulltext):
    prompt = get_fullprompt(fulltext)
    return gemini.single_prompt(prompt)
    
def get_prompts(knowndoi, searches, maxcount):
    prompts = {}
    count = 0
        if THE_DOI not in knowndoi:
            prompts[THE_DOI] = get_fullprompt(THE_FULLTEXT)
            count += 1
            if count == maxcount:
                break
    return prompts
    
for PDF IN DIRECTORY:
    count = 0
    lasttime_gemini = time.time()
    if THE_DOI not in knowndoi_gemini:
        if gemini_config == 'slow':
            nowtime = time.time()
            time.sleep(max(24*60*60 / 1490 - (nowtime - lasttime_gemini), 0))
        lasttime_gemini = time.time()
        response = submit_single_abstract_gemini(THE_FULLTEXT)
        add_response(response_round2_file, THE_DOI, 'gemini', response)
        knowndoi_gemini.add(THE_DOI)
        count += 1
    if THE_DOI not in knowndoi_openai:
        response = submit_single_abstract_openai(THE_FULLTEXT)
        add_response(response_round2_file, THE_DOI, 'openai', response)
        knowndoi_openai.add(THE_DOI)
        count += 1
    if count >= count_perrun:
        break
