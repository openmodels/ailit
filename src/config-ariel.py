from lib import commands, checks

abstract_count = 2000
openai_config = 'batch' #'slow'
gemini_config = 'batch' #'fast' #'slow'

searches = ["/Users/admin/groups/nca6/keywords/ariel-*"]
response_file = "../ariel/responses.csv"
verdict_file = "../ariel/verdicts.csv"

abstract_prompt = "I am performing a review of academic papers for the economics chapter of the U.S. National Climate Assessment. This section is specifically based on agricultural impacts."
exclude_codes = {'XC': "Not related to climate change",
                 'XV': "Not related to economics or social outcomes",
                 'XU': "No United States specific information",
                 'XO': "Excluded for another reason (please specify)"}
include_codes = {
    'R1': "Studies the scale and scope of agricultural climate damages.",
    'R2': "Studies the potential, limits, and costs of adaptation.",
    'R3': "Studies indirect and cascading effects.",
    'R4': "Studies policy barriers (e.g., in crop insurance and water).",
    'RP': "There is other plausible evidence that the abstract is relevant."}

filter_config = {'MinYear': 2022}

question_file = None
pdfs_dir = "../pdfs"

allow_missing_verdict = True
