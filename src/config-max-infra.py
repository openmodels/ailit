from lib import commands, checks

abstract_count = 2000
openai_config = 'batch' #'slow'
gemini_config = 'batch' #'fast' #'slow'

searches = ["/Users/admin/groups/nca6/keywords/Max-infra-*"]
response_file = "../max-infra/responses.csv"
verdict_file = "../max-infra/verdicts.csv"

abstract_prompt = "I am performing a review of academic papers for the economics chapter of the U.S. National Climate Assessment. This section is specifically based on infrastructure impacts."
exclude_codes = {'XC': "Not related to climate change",
                 'XV': "Not related to economics or social outcomes",
                 'XU': "No United States specific information",
                 'XO': "Excluded for another reason (please specify)"}
include_codes = {
    'R1': "Studies transportation infrastructure: roads, bridges, rail, ports, and airports.",
    'R2': "Studies coastal and flood protection infrastructure.",
    'R3': "Studies urban infrastructure, water systems, and public services.",
    'R4': "Studies infrastructure adaptation, resilience, investment, and policy.",
    'RP': "There is other plausible evidence that the abstract is relevant."}

filter_config = {'MinYear': 2022}

question_file = None
pdfs_dir = "../pdfs"

allow_missing_verdict = True
