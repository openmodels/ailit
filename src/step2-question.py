import re, csv

from lib import interaction
from lib.helpers import *
from config import *

if os.path.exists(question_file):
    answers = pd.read_csv(question_file)
    dones = set(answers.DOI)
else:
    with open(question_file, 'w') as fp:
        writer = csv.writer(fp)
        writer.writerow(['DOI', 'Outcome'])
    dones = []

with open(question_file, 'a') as fp:
    writer = csv.writer(fp)

    for row in iterate_search(questionsource):
        if row['DOI'] in dones:
            continue
        print(row['DOI'])
        
        title = row['Title']
        abstract = row['Abstract']
        prompt = f"""{abstract_prompt} The following paper was identified as potentially relevant to my review:

{title}
Abstract: {abstract}

{singlequestion}
Specify your answer as '[yes]', '[no]', or '[maybe]' in brackets."""
        
        response = interaction.aiengine.chat_response([{"role": "user", "content": prompt}])
        matches = re.findall(r'\[([A-Za-z0-9.]+)\]', response, re.DOTALL)
        if len(matches) == 0:
            writer.writerow([row['DOI'], "No codes"])
        elif len(matches) > 1:
            writer.writerow([row['DOI'], "Ambiguous"])
        elif matches[0] in ['yes', 'no', 'maybe']:
            if matches[0] == 'yes':
                writer.writerow([row['DOI'], "Passed"])
            elif matches[0] == 'no':
                writer.writerow([row['DOI'], "Failed"])
            else:
                writer.writerow([row['DOI'], "Unknown"])
        else:
            writer.writerow([row['DOI'], "No codes"])
