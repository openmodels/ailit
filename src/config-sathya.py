from lib import commands, checks

abstract_count = 2000
openai_config = 'batch' #'slow'
gemini_config = 'batch' #'fast' #'slow'

searches = ["/Users/admin/groups/nca6/keywords/Sathya-*"]
response_file = "../sathya/responses.csv"
verdict_file = "../sathya/verdicts.csv"

abstract_prompt = "I am performing a review of academic papers for the economics chapter of the U.S. National Climate Assessment."
exclude_codes = {'XC': "Not related to climate change",
                 'XV': "Not related to economics or social outcomes",
                 'XU': "No United States specific information",
                 'XO': "Excluded for another reason (please specify)"}
include_codes = {
    'R1': "Overview of NCA's treatment of coastal climate risk and identified knowledge gaps.",
    'R2': "Examines how flood risk is capitalized into property values and key research findings.",
    'R3': "Discusses financial sector exposure to sea-level rise and mispricing in insurance and mortgage markets.",
    'R4': "Evaluates coastal adaptation strategies and their economic implications, highlighting key studies.",
    'R5': "Explores coastal displacement dynamics, impacts on receiving communities, and existing knowledge gaps.",
    'RP': "There is other plausible evidence that the abstract is relevant."}

filter_config = {'MinYear': 2022}

question_file = None
pdfs_dir = "../pdfs"

allow_missing_verdict = True
