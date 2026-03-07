import os, re, random
import numpy as np
import pandas as pd

from lib import interaction, helpers
from config import *

def harmonize_rows(rows, instructs, request):
    datainfo = rows.to_csv(index=False)

    instructs2 = copy.copy(instructs)
    instructs2['sourcematerial'] = ["Provide quotes or evidence from the contributing source material that justifies or provides necessary context for the results you gave."]

    headerstr = ",".join([f"\"{column}\"" for column in instructs2.keys()])
    columninfo = "  " + "\n  ".join([f"{column}: {question[0]}" for column, question in instructs2.items()])

    prompt = f"""{abstract_prompt} I now have entries from multiple reviewers looking at multiple papers, organized as CSV table rows. I would like you to harmonize their outputs, without losing any information.  This consists of:
 - Using a common interpretation of the various columns.
 - Where columns offer qualitative label information, using a standardized format and labels.
 - Where columns offer summaries, ensuring brevity and a common structure.

It is okay for the rows to express different or even contradictory information. The goal here is to just to harmonize the formatting.

Here was the request to the reviewers: {request}

Here is a description of the columns:
{columninfo}

And here are the rows for you to harmonize:
{datainfo}

Do not modify the `sourcematerial` column, except to add to it if relevant information is being dropped from other columns in the harmonization process.
Do not drop any rows and keep them in the same order.

Specify the results in a list with single lines of text in a YAML dictionary. Your response should look like this:
```
{headerstr}
```
"""

    chat = [{"role": "user", "content": prompt}]
    while ii in range(3):
        rows = interaction.get_csvtext_validated(chat, 3, instructs2)
        if len(rows) < len(df):
            chat = chat_push(chat_push(chat, 'assistant', f"```{response}```"), 'user', "Sorry, the number of rows does not match the original. Please include all rows.")
            rows = None
            continue
        if np.any(rows.DOI != df.DOI):
            chat = chat_push(chat_push(chat, 'assistant', f"```{response}```"), 'user', "Sorry, but the DOI column did not exactly match the original. Please do not change the order and keep the same formatting for this column.")
            rows = None
            continue

    return rows

## NOTE: ExtractCount or SummaryCount should already be dropped, and HarmonizeCount should already be added
def harmonize_draw(df, passdf, instructs, request):
    if len(df) <= 1:
        return None # unchanged
    
    if len(df) <= 20:
        iis = np.range(len(df))
        result = harmonize_rows(df.drop('HarmonizeCount'), instructs, request)
    else:
        ## Throw in some single-pass results, then drop them, since these are more carefully checked
        bigdf = pd.concat([df, passdf.sample(n=len(df) / 2)], ignore_index=True)
        iis = np.random.randint(0, len(bigdf), size=20)
        result = harmonize_rows(bigdf.iloc[iis].drop('HarmonizeCount'), instructs, request)

    if result is None:
        return None # unchanged
        
    for jj in len(iis):
        if iis[jj] >= len(df):
            continue
        row = result.iloc[jj]
        row['HarmonizeCount'] = df.HarmonizeCount.iloc[iis[jj]] + 1
        df.iloc[ii] = row

    return df

summaries = []
knowndoi = set()
for dopass in range(dopass_count):
    summaries_pass, knowndoi_pass = helpers.get_summaries(summary_file, dopass)

    summaries.append(summaries_pass)
    knowndoi |= set(knowndoi_pass)

detaileds = []
for dopass in range(dopass_count):
    passdetaileds = []
    for doi in knowndoi:
        fileroot = re.sub(r'[^\w\.\-]', '_', doi)
        dopass_suffix = f"-pass{dopass}" if dopass > 0 else ""
        detailpath = os.path.join(extract_dir, fileroot + dopass_suffix + '.csv')
        if os.path.exists(detailpath):
            try:
                rows = pd.read_csv(detailpath)
                rows = rows.loc[:, ~rows.columns.str.startswith('Unnamed')]
                passdetaileds.append(rows)
            except Exception as ex:
                pass
    detaileds.append(passdetaileds)

merged_harmonized = {}
for key in merge_suffix:
    harmonized_file = summary_file.replace(".csv", merge_suffix[key] + "-harmonized.csv")
    if os.path.exists(harmonized_file):
        merged_harmonized[key] = pd.read_csv(harmonized_file)
    else:
        harmonized = pd.read_csv(harmonized_file.replace("-harmonized.csv", ".csv"))
        harmonized['HarmonizeCount'] = 0
        merged_harmonized[key] = harmonized

extracts_harmonized = {}
for key in merge_suffix:
    harmonized_file = merge_extract_file.replace(".csv", merge_suffix[key] + "-harmonized.csv")
    if os.path.exists(extract_file):
        extracts_harmonized[key] = pd.read_csv(harmonized_file)
    else:
        harmonized = pd.read_csv(harmonized_file.replace("-harmonized.csv", ".csv"))
        harmonized['HarmonizeCount'] = 0
        extracts_harmonized[key] = harmonized

if __name__ == '__main__':
    count = 0
    for key in merged_suffix:
        # Harmonize the merged summaries
        instructs = {col: [question] for col, question in merge_columns[key].items()}
        
        df = merged_harmonized[key]
        sumcount = df.SummaryCount
        result = harmonize_draw(df.drop('SummaryCount'), random.choice(summaries), instructs, "Please summarize the following features of the paper.")
        if result is not None:
            result['SummaryCount'] = sumcount
            merged_harmonized[key] = df
            harmonized_file = summary_file.replace(".csv", merge_suffix[key] + "-harmonized.csv")
            result.to_csv(harmonized_file, index=False)
        
        # Harmonize the merged extracts
        instructs = column_defs_extract[key]
        
        df = extracts_harmonized[key]
        extcount = df.ExtractCount
        result = harmonize_draw(df.drop('ExtractCount'), random.choice(detaileds), instructs, extract_request)
        if result is not None:
            result['ExtractCount'] = extcount
            merged_harmonized[key] = df
            harmonized_file = merge_extract_file.replace(".csv", merge_suffix[key] + "-harmonized.csv")
            result.to_csv(harmonized_file, index=False)

        count += 1

        if count >= harmonize_count:
            break
