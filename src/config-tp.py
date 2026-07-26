from lib import commands, checks

abstract_count = 1000
openai_config = 'batch' #'slow'
gemini_config = 'batch' #'fast' #'slow'

searches = ["/Users/admin/groups/nca6/keywords/Howard-1*",
            "/Users/admin/groups/nca6/keywords/Howard-2*",
            "/Users/admin/groups/nca6/keywords/Howard-3*"]
response_file = "../howard-tp/responses.csv"
verdict_file = "../howard-tp/verdicts.csv"

abstract_prompt = "I am performing a review of climate, biophysical, and social tipping points for the economics chapter of the U.S. National Climate Assessment."
exclude_codes = {'XC': "Not related to climate change",
                 'XV': "Not related to economics or social outcomes",
                 'XU': "No United States specific information",
                 'XO': "Excluded for another reason (please specify)"}
include_codes = {'RO': "Discusses observed tipping points (e.g., coral reef regime shifts, civit unrest)",
                 'RF': "Discusses projected tipping points (e.g., in 2050)",
                 'RP': "There is other plausible evidence that the abstract is relevant."}

filter_config = {'MinYear': 2022}

question_file = None
pdfs_dir = "../pdfs"

allow_missing_verdict = True
