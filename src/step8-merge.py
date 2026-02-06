import os, re
import pandas as pd

from lib import interaction, helpers
from config import *

def merge_rows(verdictrow, applied, columns):
    title = verdictrow.Title.iloc[0]
    abstract = verdictrow.Abstract.iloc[0]

    template = ""
    expectedcolumns = set()
    knowncolumns = {}
    rowinfo = ""
    for column in applied.columns:
        if all(str(applied[column].iloc[ii]) == str(applied[column].iloc[0]) for ii in range(1, len(applied))):
            colinfo = column + ": " + str(applied[column].iloc[0]) + "\n"
            rowinfo += colinfo
            knowncolumns[column] = [applied[column].iloc[0]]
        else:
            if columns[column]:
                colinfo = column + ":\n  Description: " + columns[column] + "\n"
            else:
                colinfo = column + ":\n"
            rowinfo += "\n" + colinfo + "  Recorded: " + "\n  Recorded: ".join(map(str, applied[column])) + "\n\n"
            template += f'"{column}": "..."\n'
            expectedcolumns.add(column)
    
    prompt = f"""{abstract_prompt} Here is a pager identified as relevant to the search:

{title}
Abstract: {abstract}

Multiple reviewers have provided summaries of this paper, and now I want to merge these into a consistent summary. The summary should focus on information that is corroborated by more than one reviewer, where possible.

Here is the data from the reviewers:

{rowinfo}

Specify the results in a list with single lines of text in a YAML dictionary. Your response should look like this:
```
{template}
```
"""

    chat = [{"role": "user", "content": prompt}]

    for attempts in range(3):
        response = interaction.aiengine.chat_response(chat)
        result = interaction.extract_yaml_dict(response)
    
        if isinstance(result, str):
            chat = interaction.chat_push(interaction.chat_push(chat, 'assistant', response),
                                         'user', f"Sorry, I had trouble with this: {result} Can you try again?")
        else:
            remainingcolumns = expectedcolumns - result.keys()
            if len(remainingcolumns) > 0:
                chat = interaction.chat_push(interaction.chat_push(chat, 'assistant', response),
                                             'user', f"Sorry, I am missing the following columns: {', '.join(remainingcolumns)}. Can you try again?")
            else:
                print("Successful merging.")
                break

    if isinstance(result, dict):
        for col in result:
            knowncolumns[col] = [result[col]]
        for col in remainingcolumns:
            knowncolumns[col] = [applied[column].iloc[-1]] # choose the latest one

        return pd.DataFrame(knowncolumns)
    else:
        print("Providing the most recent row.")
        return applied.iloc[-1]

def merge_extract(verdictrow, detaileds, paperinfo, request, instructs):
    title = verdictrow.Title.iloc[0]
    abstract = verdictrow.Abstract.iloc[0]

    datainfo = ""
    for ii in range(len(detaileds)):
        datainfo += f"Reviewer {ii+1}:\n\n{detaileds[ii].to_csv(index=False)}\n\n"

    headerstr = ",".join([f"\"{column}\"" for column in instructs.keys()])
        
    prompt = f"""{abstract_prompt} Here is a pager identified as relevant to the search:

{title}
Abstract: {abstract}

{paperinfo}

Multiple reviewers have extracted detailed information from this paper, and now I want to merge these into a consistent dataset. The dataset should focus on information that is corroborated by more than one reviewer, where possible.

Here was the request to the reviewers: {request}

Here is the data from the reviewers:

{datainfo}

Specify the result as a CSV, provided in triple quotes. Your response should start:
```
{headerstr}
...
```
"""

    chat = [{"role": "user", "content": prompt}]

    return interaction.get_csvtext_validated(chat, 3, instructs)

def save_merged(merged):
    for key in merged:
        merged[key].to_csv(summary_file.replace(".csv", merge_suffix[key] + ".csv"), index=False)

def save_extracts(extracts):
    for key in extracts:
        extracts[key].to_csv(merge_extract_file.replace(".csv", merge_suffix[key] + ".csv"), index=False)

verdicts = pd.read_csv(verdict_file.replace('.csv', '-further.csv'))

summaries = []
knowndoi = set()
for dopass in range(dopass_count):
    summaries_pass, knowndoi_pass = helpers.get_summaries(summary_file, dopass)

    summaries.append(summaries_pass)
    knowndoi |= set(knowndoi_pass)

merged = {}
for key in merge_suffix:
    merged_file = summary_file.replace(".csv", merge_suffix[key] + ".csv")
    if os.path.exists(merged_file):
        merged[key] = pd.read_csv(merged_file)
    else:
        merged[key] = pd.DataFrame({'DOI': []})

extracts = {}
for key in merge_suffix:
    extract_file = merge_extract_file.replace(".csv", merge_suffix[key] + ".csv")
    if os.path.exists(extract_file):
        extracts[key] = pd.read_csv(extract_file)
    else:
        extracts[key] = pd.DataFrame({'DOI': []})
        
if __name__ == '__main__':
    count = 0
    for doi in knowndoi:
        # Get the original authors and abstract
        verdictrow = verdicts[verdicts.DOI == doi]

        # Merge the summaries, column by column
        doisummaries = []
        for dopass in range(dopass_count):
            rows = summaries[dopass][summaries[dopass].DOI == doi]
            doisummaries.append(rows)

        doisummaries = pd.concat(doisummaries, ignore_index=True)
        if extract_fromsummary == 'All':
            dropped = []
        else:
            dropped = doisummaries[doisummaries[extract_fromsummary] == ""]
        
        for key, columns in merge_columns.items():
            if extract_fromsummary == 'All':
                applied = doisummaries
            else:
                applied = doisummaries[doisumkey == key]
            applied = applied[columns.keys()]

            if len(applied) <= len(dropped):
                print(f"Conservatively dropping {key} from {doi}")
                continue

            if any(merged[key].DOI == doi):
                last_summarycount = merged[key].SummaryCount[merged[key].DOI == doi].iloc[0]
            else:
                last_summarycount = 0
            if len(applied) != last_summarycount:
                if len(applied) == 1:
                    applied['SummaryCount'] = len(applied)
                    applied['DOI'] = doi
                    newrow = applied
                    merged[key] = pd.concat([merged[key][merged[key].DOI != doi], applied], ignore_index=True)
                else:
                    applied2 = merge_rows(verdictrow, applied, columns)
                    applied2['SummaryCount'] = len(applied)
                    applied2['DOI'] = doi
                    newrow = applied2
                    merged[key] = pd.concat([merged[key][merged[key].DOI != doi], applied2], ignore_index=True)
                save_merged(merged)
            else:
                newrow = merged[key][merged[key].DOI == doi]

            dones = extracts[key][extracts[key].DOI == doi]
                
            detaileds = []
            fileroot = re.sub(r'[^\w\.\-]', '_', doi)
            for dopass in range(dopass_count):
                dopass_suffix = f"-pass{dopass}" if dopass > 0 else ""
                detailpath = os.path.join(extract_dir, fileroot + dopass_suffix + '.csv')
                if os.path.exists(detailpath):
                    try:
                        rows = pd.read_csv(detailpath)
                        rows = rows.loc[:, ~rows.columns.str.startswith('Unnamed')]
                        detaileds.append(rows)
                    except Exception as ex:
                        print(f"Failed to read {detailpath}.")

            if len(detaileds) == 0:
                continue

            if len(dones) == 0 or dones.ExtractCount.iloc[0] < len(detaileds):
                if len(detaileds) == 1:
                    validrows2 = detaileds[0]
                else:
                    paperinfo = [f"  {key}: {value.iloc[0]}" for key, value in newrow.items() if not pd.isna(value.iloc[0]) and not key[:7] == "Unnamed"]
                    instructs = column_defs_extract[key]
                    if isinstance(extract_request, str):
                        request = extract_request
                    else:
                        request = extract_request[key]
                
                    validrows = merge_extract(verdictrow, detaileds, "\n".join(paperinfo), request, instructs)
                    validrows2 = pd.DataFrame(validrows)
                    
                validrows2['ExtractCount'] = len(detaileds)
                validrows2['DOI'] = doi
                extracts[key] = pd.concat([extracts[key][extracts[key].DOI != doi], validrows2], ignore_index=True)
                save_extracts(extracts)

    save_merged(merged)
    save_extracts(extracts)
