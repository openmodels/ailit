import csv
import pandas as pd

from lib import interaction
from config import *

verdicts = pd.read_csv(verdict_file.replace(".csv", "-further.csv"))
summaries = pd.read_csv(summary_file.replace(".csv", "-merged.csv"))
with open('../extendeds.csv', 'w') as fp:
    writer = csv.writer(fp)
    writer.writerow(['DOI', 'Author(s)', 'Year', 'Paper Title', "Background", "Methodology", "Results", "Discussion"])
    
    for index, srow in summaries.iterrows():
        values = srow.to_dict()
        vrow = verdicts[verdicts.DOI == srow.DOI]

        saved = {}
        for drop in ['DOI', 'Author(s)', 'Year', 'Paper Title', 'Link to paper', 'Paper ID', 'Reviewer', 'Status', 'SummaryCount']:
            saved[drop] = values[drop]
            del values[drop]

        title = vrow.Title.iloc[0]
        abstract = vrow.Abstract.iloc[0]

        datainfo = ""
        for key in values:
            datainfo += f"{key}: {values[key]}\n"

    
        prompt = f"""{abstract_prompt} Here is a pager identified as relevant to the search:

{title}
Abstract: {abstract}

Here is additional information extracted from the paper:
{datainfo}

I would like you to construct an extended abstract from this information, with the following fields: Background, Methodology, Results, Discussion.
Make sure to include all of the material from the paper's actual abstract, but also key points from the additional extracted information.

Specify the results in a list with strings of text in a YAML dictionary (do not use YAML lists). Your response should look like this:
```
"Background": "..."
"Methodology": "..."
"Results": "..."
"Discussion": "..."
...
```
"""
        chat = [{"role": "user", "content": prompt}]

        foundall = False
        for attempt in range(3):
            response = interaction.aiengine.chat_response(chat)
            result = interaction.extract_yaml_dict(response)
            if isinstance(result, str):
                chat = interaction.chat_push(interaction.chat_push(chat, 'assistant', response), 'user', "I got the following error: " + result + ". Can you try again?")
                continue
            foundall = True
            for key in ['Background', 'Methodology', 'Results', 'Discussion']:
                if key not in result:
                    chat = interaction.chat_push(interaction.chat_push(chat, 'assistant', response), 'user', f"I did not find {key} in the result. This can happen if it was not provided as a single string. Can you try again with all the fields?")
                    foundall = False
                    break
            if foundall:
                break

        if foundall:
            writer.writerow([saved['DOI'], saved['Author(s)'], saved['Year'], saved['Paper Title'], result['Background'], result['Methodology'],
                             result['Results'], result['Discussion']])
