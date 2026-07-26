from lib import commands, checks

abstract_count = 10000
openai_config = 'batch' #'slow'
gemini_config = 'batch' #'fast' #'batch' #'skip' #'slow'

searches = ["/Users/admin/groups/nca6/keywords/Howard-4*",
            "/Users/admin/groups/nca6/keywords/Howard-5*"]
response_file = "../howard-so/responses.csv"
verdict_file = "../howard-so/verdicts.csv"

abstract_prompt = "I am performing a review of spill-over and cross-boundary risks for the economics chapter of the U.S. National Climate Assessment."
exclude_codes = {'XC': "Not related to climate change",
                 'XV': "Not related to economics or social outcomes",
                 'XU': "No United States specific information",
                 'XO': "Excluded for another reason (please specify)"}
include_codes = {'RO': "Discusses observed spill-overs (e.g., trade networks, damage transmission)",
                 'RF': "Discusses projected spill-overs (e.g., in 2050)",
                 'RP': "There is other plausible evidence that the abstract is relevant."}

filter_config = {'MinYear': 2022}

question_file = None
pdfs_dir = None

allow_missing_verdict = True
