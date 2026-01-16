import os, csv, time
import pandas as pd
from chatwrap import gemini, openaigpt, openai_batch

from config import *
from lib.helpers import *

def get_fullprompt(title, abstract, keywords):
    exclude_text = "  " + "\n  ".join([f"{key}: {value}" for key, value in exclude_codes.items()])
    include_text = "  " + "\n  ".join([f"{key}: {value}" for key, value in include_codes.items()])
    return f"""{abstract_prompt}

The following is a paper identified by very general search:
{title}
Abstract: {abstract}
Keywords: {keywords}

Based on this information, should this paper be included in the review? If *not*, please classify this with one or more of the following codes:
{exclude_text}
If it *should* be included, classify it with one or more of the following codes:
{include_text}

Provide a succinct explanation, and only mention codes identified for this paper."""

print(get_fullprompt("My paper", "Something something", "Keyword 1, and 2"))

def submit_single_abstract_openai(doi, title, abstract, keywords):
    prompt = get_fullprompt(title, abstract, keywords)
    return openaigpt.single_prompt(prompt)

def submit_single_abstract_gemini(doi, title, abstract, keywords):
    prompt = get_fullprompt(title, abstract, keywords)
    return gemini.single_prompt(prompt)

knowndoi_gemini, knowndoi_openai = get_knowns(response_file)

def get_prompts(knowndoi, searches, maxcount):
    prompts = {}
    count = 0
    for search in searches:
        for row in iterate_search(search):
            if row['DOI'] not in knowndoi:
                prompts[row['DOI']] = get_fullprompt(row['Title'], row['Abstract'], row['Author Keywords'])
                count += 1
                if count == maxcount:
                    break
    return prompts

if openai_config == 'batch':
    responses = openai_batch.main_flow(openaigpt.client, response_file + "-batch.jsonl", "../waiting.pkl", lambda: get_prompts(knowndoi_openai, searches, abstract_count))
    for doi, response in responses.items():
        knowndoi_openai.add(doi)
        add_response(response_file, doi, 'openai', response)

for search in searches:
    count = 0
    lasttime_gemini = time.time()
    for row in iterate_search(search):
        if row['DOI'] not in knowndoi_gemini:
            if gemini_config == 'slow':
                nowtime = time.time()
                time.sleep(max(24*60*60 / 1490 - (nowtime - lasttime_gemini), 0))
            lasttime_gemini = time.time()
            response = submit_single_abstract_gemini(row['DOI'], row['Title'], row['Abstract'], row['Author Keywords'])
            add_response(response_file, row['DOI'], 'gemini', response)
            knowndoi_gemini.add(row['DOI'])
            count += 1
        if openai_config == 'slow' and row['DOI'] not in knowndoi_openai:
            response = submit_single_abstract_openai(row['DOI'], row['Title'], row['Abstract'], row['Author Keywords'])
            add_response(response_file, row['DOI'], 'openai', response)
            knowndoi_openai.add(row['DOI'])
            count += 1
        if count >= abstract_count:
            break

if openai_config == 'batch':
    responses = openai_batch.main_flow(openaigpt.client, response_file + "-batch.jsonl", "waiting.pkl", lambda: get_prompts(knowndoi_openai, searches, abstract_count))
    for doi, response in responses.items():
        knowndoi_openai.add(doi)
        add_response(response_file, doi, 'openai', response)
