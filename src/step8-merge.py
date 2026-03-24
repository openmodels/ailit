import os, re
import pandas as pd

from lib import interaction, helpers
from config import *

def merge_column_with_sourcematerial(chat, applied, columns, column):
    if columns[column]:
        colinfo = "\nHere is a description of the column: " + columns[column] + "\n"
    else:
        colinfo = ""

    smcolname = column + '-sourcematerial'
        
    rowinfo = ""
    for ii, row in applied.iterrows():
        rowinfo += "Recorded: " + str(applied.loc[ii, column]) + "\n"
        rowinfo += "Source material: " + str(applied.loc[ii, smcolname]) + "\n\n"

    prompt = f"""Now, I would like you to merge the `{column}` column, which also has source material associated with it. The source material should also be merged, ensuring succinct completeness.
{colinfo}
Here is the column data from the reviewers:

{rowinfo}

Specify the results in a list with single lines of text in a YAML dictionary. Your response should look like this:
```
"{column}": "..."
"sourcematerial": "..."
```
"""


    chat2 = interaction.chat_push(chat, 'user', prompt)
    result, response = interaction.get_yaml_validated(chat2, 3, [column, 'sourcematerial'])

    if isinstance(result, dict):
        chat2 = interaction.chat_push(interaction.chat_push(chat, 'user', prompt),
                                      'assistant', response)
        return chat2, result.get(column, applied[column].iloc[-1]), result.get('sourcematerial', applied[smcolname].iloc[-1])
    else:
        print("Providing the most recent row for {column}.")
        return chat, applied[column].iloc[-1], applied[smcolname].iloc[-1]

def merge_rows(verdictrow, applied, columns):
    title = verdictrow.Title.iloc[0]
    abstract = verdictrow.Abstract.iloc[0]

    cols_with_sourcematerial = []
    template = ""
    expectedcolumns = set()
    knowncolumns = {}
    rowinfo = ""
    for column in applied.columns:
        if '-sourcematerial' in column:
            continue
        if (column + '-sourcematerial') in applied.columns:
            cols_with_sourcematerial.append(column)
        elif all(str(applied[column].iloc[ii]) == str(applied[column].iloc[0]) for ii in range(1, len(applied))):
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

Here is the basic data from the reviewers:

{rowinfo}
"""
    
    if not template:
        ## All of the non-sourcematerial columns agree
        chat2 = [{"role": "user", "content": prompt}]
        for column in cols_with_sourcematerial:
            chat2, value, sourcematerial = merge_column_with_sourcematerial(chat2, applied, columns, column)
            knowncolumns[column] = value
            knowncolumns[column + '-sourcematerial'] = sourcematerial
            
        return pd.DataFrame(knowncolumns)
            
    prompt += f"""Specify the results in a list with single lines of text in a YAML dictionary. Your response should look like this:
```
{template}
```
"""

    chat = [{"role": "user", "content": prompt}]

    result, response = interaction.get_yaml_validated(chat, 3, expectedcolumns)

    if isinstance(result, dict):
        for col in result:
            knowncolumns[col] = [result[col]]
        for col in remainingcolumns:
            knowncolumns[col] = [applied[column].iloc[-1]] # choose the latest one

        ## Now do the sourcematerial columns
        chat2 = interaction.chat_push(chat, 'assisant', response)
        for column in cols_with_sourcematerial:
            chat2, value, sourcematerial = merge_column_with_sourcematerial(chat2, applied, columns, column)
            knowncolumns[column] = value
            knowncolumns[column + '-sourcematerial'] = sourcematerial
            
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

    instructs2 = copy.copy(instructs)
    instructs2['sourcematerial'] = ["Provide quotes or evidence from the contributing source material that justifies or provides necessary context for the results you gave."]
        
    headerstr = ",".join([f"\"{column}\"" for column in instructs2.keys()])
    columninfo = "  " + "\n  ".join([f"{column}: {question[0]}" for column, question in instructs2.items()])
        
    prompt = f"""{abstract_prompt} Here is a pager identified as relevant to the search:

{title}
Abstract: {abstract}

{paperinfo}

Multiple reviewers have extracted detailed information from this paper, and now I want to merge these into a consistent dataset. The dataset should focus on information that is corroborated by more than one reviewer, where possible.

Here was the request to the reviewers: {request}

And the definitions for the columns are as follows:
{columninfo}

Here is the data from the reviewers:

{datainfo}

Specify the result as a CSV, provided in triple quotes. Your response should start:
```
{headerstr}
...
```
"""

    chat = [{"role": "user", "content": prompt}]

    return interaction.get_csvtext_validated(chat, 3, instructs2)

def save_merged(merged):
    for key in merged:
        merged[key].to_csv(summary_file.replace(".csv", merge_suffix[key] + ".csv"), index=False)

def save_extracts(extracts):
    for key in extracts:
        extracts[key].to_csv(merge_extract_file.replace(".csv", merge_suffix[key] + ".csv"), index=False)

def merge_extracts(doi, key):
    dones = extracts[key][extracts[key].DOI == doi]
            
    detaileds = []
    fileroot = re.sub(r'[^\w\.\-]', '_', doi)
    for dopass in range(dopass_count):
        dopass_suffix = f"-pass{dopass}" if dopass > 0 else ""
        detailpath = os.path.join(extract_dir, fileroot + dopass_suffix + '.csv')
        if os.path.exists(detailpath) and os.path.getsize(detailpath) > 2:
            try:
                rows = pd.read_csv(detailpath)
                rows = rows.loc[:, ~rows.columns.str.startswith('Unnamed')]
                detaileds.append(rows)
            except Exception as ex:
                print(f"Failed to read {detailpath}.")

    if len(detaileds) == 0:
        return

    if len(dones) == 0 or dones.ExtractCount.iloc[0] < len(detaileds):
        if len(detaileds) == 1:
            validrows2 = detaileds[0]
        else:
            paperinfo = [f"  {kk}: {value.iloc[0]}" for kk, value in newrow.items() if not pd.isna(value.iloc[0]) and not kk[:7] == "Unnamed"]
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
    for doi in knowndoi:
        # Get the original authors and abstract
        verdictrow = verdicts[verdicts.DOI == doi]

        # Merge the summaries, column by column
        doisummaries = []
        for dopass in range(dopass_count):
            if summaries[dopass] is not None:
                rows = summaries[dopass][summaries[dopass].DOI == doi]
                doisummaries.append(rows)

        if len(doisummaries) == 1:
            applied = doisummaries[0].copy()
            applied['SummaryCount'] = 1
            merged[key] = pd.concat([merged[key][merged[key].DOI != doi], applied], ignore_index=True)

            for key, columns in merge_columns.items():
                merge_extracts(doi, key)
            continue
            
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
            colstouse = []
            for column in columns:
                colstouse.append(column)
                if (column + '-sourcematerial') in applied.columns:
                    colstouse.append(column + '-sourcematerial')
            applied = applied[colstouse]

            if len(applied) <= len(dropped):
                print(f"Conservatively dropping {key} from {doi}")
                continue

            if any(merged[key].DOI == doi):
                last_summarycount = merged[key].SummaryCount[merged[key].DOI == doi].iloc[0]
            else:
                last_summarycount = 0
            if len(applied) != last_summarycount:
                if len(applied) == 1:
                    applied.loc[0, 'SummaryCount'] = len(applied)
                    applied.loc[0, 'DOI'] = doi
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

            merge_extracts(doi, key)
                
    save_merged(merged)
    save_extracts(extracts)
