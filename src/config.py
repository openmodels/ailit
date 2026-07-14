from lib import commands, checks

abstract_count = 2000
openai_config = 'batch' #'slow'
gemini_config = 'batch' #'fast' #'slow'

searches = ["/Users/admin/groups/nca6/keywords/Max-energy-*"]
response_file = "../max-energy/responses.csv"
verdict_file = "../max-energy/verdicts.csv"

abstract_prompt = "I am performing a review of academic papers for the economics chapter of the U.S. National Climate Assessment. This section is specifically based on energy impacts."
exclude_codes = {'XC': "Not related to climate change",
                 'XV': "Not related to economics or social outcomes",
                 'XU': "No United States specific information",
                 'XO': "Excluded for another reason (please specify)"}
include_codes = {
    'R1': "Studies demand impacts: heating and cooling shifts, peak load stress, increased air conditioning demand; regional variation in net effects.",
    'R2': "Studies supply impacts: infrastructure damage from heat, flooding, and wildfire; supply shocks from extreme storms; water availability constraints on hydropower and thermoelectric cooling.",
    'R3': "Studies Efficiency improvements and grid investment as embedded adaptation; pass-through to households and other sectors.",
    'RP': "There is other plausible evidence that the abstract is relevant."}

filter_config = {'MinYear': 2022}

question_file = None
pdfs_dir = "../pdfs"

allow_missing_verdict = True
