import csv
import pandas as pd

from config import *
from lib.helpers import *

def interpret_excludes(response):
    excludes = []
    for code in exclude_codes:
        if code in response:
            excludes.append(code)
    return excludes

def interpret_includes(response):
    includes = []
    for code in include_codes:
        if code in response:
            includes.append(code)
    return includes

def interpret_response(response):
    excludes = interpret_excludes(response)
    includes = interpret_includes(response)
    
    if len(excludes) > 0 and len(includes) == 0:
        return (' '.join(excludes), 1)
    if len(includes) > 0 and len(excludes) == 0:
        return (' '.join(includes), 5)
    
    if len(includes) == 0 and len(excludes) == 0:
        return ("No codes", "NA")
    
    return ("Ambiguous", 3)

responses = pd.read_csv(response_file)
responses = responses.astype(str)

further_consideration = {} # doi: (gemini_response, openai_response, gemini_verdict, openai_verdict, common_verdict)
with open(verdict_file, 'w') as fp:
    writer = csv.writer(fp)
    writer.writerow(['DOI', 'gemini', 'openai', 'common', 'priority'])
    
    for doi in set(responses.DOI):
        responses_gemini = responses[(responses.DOI == doi) & (responses.Source == 'gemini')].Response
        if len(responses_gemini) > 0:
            if len(responses_gemini) > 1:
                ## Look for non-failed, non-ambiguous response, from the end
                for ii in range(len(responses_gemini)):
                    response_gemini = responses_gemini.iloc[len(responses_gemini) - ii - 1]
                    gemini_verdict, gemini_score = interpret_response(response_gemini)
                    if gemini_verdict not in ["No codes", "Ambiguous"]:
                        break
            else:
                response_gemini = responses_gemini.iloc[0]
                gemini_verdict, gemini_score = interpret_response(response_gemini)
        else:
            continue
        
        responses_openai = responses[(responses.DOI == doi) & (responses.Source == 'openai')].Response
        if len(responses_openai) > 0:
            if len(responses_openai) > 1:
                ## Look for non-failed, non-ambiguous response, from the end
                for ii in range(len(responses_openai)):
                    response_openai = responses_openai.iloc[len(responses_openai) - ii - 1]
                    openai_verdict, openai_score = interpret_response(response_openai)
                    if openai_verdict not in ["No codes", "Ambiguous"]:
                        break
            else:
                response_openai = responses_openai.iloc[0]
                openai_verdict, openai_score = interpret_response(response_openai)
        else:
            continue
        
        print(doi)
        
        further_check = True
        if "No codes" in [gemini_verdict, openai_verdict]:
            common_verdict = "Code failure"
            if gemini_verdict == "No codes" and openai_verdict == "No codes":
                score = "NA"
            elif gemini_verdict == "No codes":
                score = openai_score
            else:
                score = gemini_score
        elif "Ambiguous" in [gemini_verdict, openai_verdict]:
            common_verdict = "Ambiguous"
            score = (openai_score + gemini_score - 2) / 2 + 1
        else:
            # Look for inclusion on either side
            gemini_includes = interpret_includes(response_gemini)
            openai_includes = interpret_includes(response_openai)
            score = (openai_score + gemini_score - 2) / 2 + 1
            if len(gemini_includes) > 0 or len(openai_includes) > 0:
                common_verdict = ' '.join(set(gemini_includes + openai_includes))
            else:
                gemini_excludes = interpret_excludes(response_gemini)
                openai_excludes = interpret_excludes(response_openai)
                common_excludes = set(gemini_excludes).intersection(openai_excludes)
                if len(common_excludes) > 0:
                    common_verdict = ' '.join(common_excludes)
                    further_check = False
                    score = 0
                else:
                    common_verdict = "Disagree"
                    
        if further_check:
            further_consideration[doi] = [response_gemini.replace("\n", " "), response_openai.replace("\n", " "), gemini_verdict, openai_verdict, common_verdict, int(score)]
        writer.writerow([doi, gemini_verdict, openai_verdict, common_verdict, int(score)])

with open(verdict_file.replace(".csv", "-further.csv"), 'w') as fp:
    writer = csv.writer(fp)
    writer.writerow(['DOI', 'Title', 'Abstract', 'Gemini Response', 'OpenAI Response', 'Gemini Verdict', 'OpenAI Verdict', 'Common Verdict', 'Priority'])
    for search in searches:
        for row in iterate_search(search):
            if row['DOI'] in further_consideration.keys():
                writer.writerow([row['DOI'], row['Title'], row['Abstract']] + further_consideration[row['DOI']])
                del further_consideration[row['DOI']]
