import csv
import pandas as pd

from litreview0 import *

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
        return ' '.join(excludes)
    if len(includes) > 0 and len(excludes) == 0:
        return ' '.join(includes)
    
    if len(includes) == 0 and len(excludes) == 0:
        return "No codes"
    
    return "Ambiguous"

responses = pd.read_csv(response_file)
responses = responses.astype(str)

with open(verdict_file, 'w') as fp:
    writer = csv.writer(fp)
    writer.writerow(['DOI', 'gemini', 'openai', 'common'])

    for doi in set(responses.DOI):
        responses_gemini = responses[(responses.DOI == doi) & (responses.Source == 'gemini')].Response
        if len(responses_gemini) > 0:
            response_gemini = responses_gemini.iloc[0]
        else:
            continue
        responses_openai = responses[(responses.DOI == doi) & (responses.Source == 'openai')].Response
        if len(responses_openai) > 0:
            response_openai = responses_openai.iloc[0]
        else:
            continue

        print(doi)

        gemini_verdict = interpret_response(response_gemini)
        openai_verdict = interpret_response(response_openai)

        if "No codes" in [gemini_verdict, openai_verdict]:
            common_verdict = "Code failure"
        elif "Ambiguous" in [gemini_verdict, openai_verdict]:
            common_verdict = "Ambiguous"
        else:
            # Look for inclusion on either side
            gemini_includes = interpret_includes(response_gemini)
            openai_includes = interpret_includes(response_openai)
            if len(gemini_includes) > 0 or len(openai_includes) > 0:
                common_verdict = ' '.join(set(gemini_includes + openai_includes))
            else:
                gemini_excludes = interpret_excludes(response_gemini)
                openai_excludes = interpret_excludes(response_openai)
                common_excludes = set(gemini_excludes).intersection(openai_excludes)
                if len(common_excludes) > 0:
                    common_verdict = ' '.join(common_excludes)
                else:
                    common_verdict = "Disagree"

        writer.writerow([doi, gemini_verdict, openai_verdict, common_verdict])
