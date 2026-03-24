import os, re, random, copy
import numpy as np
import pandas as pd

from lib import interaction, helpers
from config import *

def harmonize_rows_subcols(rows, instructs2, request):
    datainfo = rows.to_csv(index=False)

    headerstr = ",".join([f"\"{column}\"" for column in rows.columns])
    columninfo = "  " + "\n  ".join([f"{column}: {question[0]}" for column, question in instructs2.items()])

    prompt = f"""{abstract_prompt} I now have entries from multiple reviewers looking at multiple papers, organized as CSV table rows. However, they sometimes use different conventions, making the interpretation of the whole corpus difficult. I would like you to harmonize their outputs, without losing any information.  This consists of:
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
Do not drop any rows, and be sure to keep the rows in the same order.

Specify the result as a CSV, provided in triple quotes. Your response should look like this:
```
{headerstr}
```
"""

    chat = [{"role": "user", "content": prompt}]
    for ii in range(3):
        newrows = interaction.get_csvtext_validated(chat, 3, instructs2, required_header=rows.columns, max_tokens=len(datainfo)*2)
        if len(newrows) == 0:
            return None
        newrows = pd.DataFrame(newrows)
        response = newrows.to_csv(index=False)
        if len(newrows) < len(df):
            chat = interaction.chat_push(interaction.chat_push(chat, 'assistant', f"```{response}```"), 'user', "Sorry, the number of rows does not match the original. Please include all rows.")
            newrows = None
            continue
        if np.any(newrows.DOI != df.DOI):
            chat = interaction.chat_push(interaction.chat_push(chat, 'assistant', f"```{response}```"), 'user', "Sorry, but the DOI column did not exactly match the original. Please do not change the order and keep the same formatting for this column.")
            newrows = None
            continue

    return newrows

def harmonize_rows(rows, instructs, request, columnsets, common_sourcematerial):
    allinsets = set()
    harmonized = []
    for columns in columnsets:
        if common_sourcematerial:
            instructs2 = {column: instructs[column] for column in columns}
            instructs2['sourcematerial'] = ["Provide quotes or evidence from the contributing source material that justifies or provides necessary context for the results you gave."]

            subcols = harmonize_rows_subcols(rows[['DOI'] + columns + ['sourcematerial']], instructs2, request)
            if subcols:
                subcols = subcols.drop(columns=['sourcematerial'])
        else:
            instructs2 = {}
            allcols = ['DOI']
            for column in columns:
                instructs2[column] = instructs[column]
                allcols.append(column)
                if columns + '-sourcematerial' in rows.columns:
                    instructs2[column + '-sourcematerial'] = f"Provide source material evidence for {column}."
                    allcols.append(column + '-sourcematerial')
                    
            subcols = harmonize_rows_subcols(rows[allcols], instructs2, request)
        if subcols is None:
            return None
        
        harmonized.append(subcols)
        allinsets.update(columns)
        
    if common_sourcematerial:
        harmonized.insert(0, rows[[col for col in rows.columns if col not in allinsets and col != 'sourcematerial']])
        harmonized.append([rows['sourcematerial']])
    else:
        harmonized.insert(0, rows[[col for col in rows.columns if '-sourcematerial' in col and col not in allinsets]])
    pd.concat(harmonized, axis=1)

def harmonize_draw_rows(df, passdf, maxrows):
    if maxrows <= 3:
        iis = np.random.randint(0, len(df), size=3)
        rows = df.iloc[iis].drop(columns=['HarmonizeCount'])
        return iis, rows
    
    if len(df) <= maxrows:
        iis = np.range(len(df))
        rows = df.drop(columns=['HarmonizeCount'])
    else:
        ## Throw in some single-pass results, then drop them, since these are more carefully checked
        bigdf = pd.concat([df, passdf.sample(n=int(len(df) / 2))], ignore_index=True)
        iis = np.random.randint(0, len(bigdf), size=maxrows)
        rows = bigdf.iloc[iis].drop(columns=['HarmonizeCount'])

    if len(rows.to_csv(index=False)) > harmonize_maxchars:
        return harmonize_draw_rows(df, passdf, int(maxrows / 2))
    else:
        return iis, rows

## NOTE: ExtractCount or SummaryCount should already be dropped, and HarmonizeCount should already be added
def harmonize_loop(df, passdf, instructs, request, columnsets, common_sourcematerial):
    if len(df) <= 1:
        return None # unchanged

    if len(df) <= 3:
        iis = np.random.randint(0, len(df), size=3)
        rows = df.iloc[iis].drop(columns=['HarmonizeCount'])
    else:
        iis, rows = harmonize_draw_rows(df, passdf, harmonize_maxrows)
        
    result = harmonize_rows(rows, instructs, request, columnsets, common_sourcematerial)
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

    if summaries_pass is not None:
        summaries.append(summaries_pass)
        knowndoi |= set(knowndoi_pass)
passdf_summaries = pd.concat(summaries, ignore_index=True)
        
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
    if passdetaileds:
        detaileds.append(pd.concat(passdetaileds, ignore_index=True))
passdf_detaileds = pd.concat(detaileds, ignore_index=True)

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
    if os.path.exists(harmonized_file):
        extracts_harmonized[key] = pd.read_csv(harmonized_file)
    else:
        harmonized = pd.read_csv(harmonized_file.replace("-harmonized.csv", ".csv"))
        harmonized['HarmonizeCount'] = 0
        extracts_harmonized[key] = harmonized

if __name__ == '__main__':
    count = 0
    for key in merge_suffix:
        # Harmonize the merged summaries
        instructs = {col: [question] for col, question in merge_columns[key].items()}
        
        df = merged_harmonized[key]
        sumcount = df.SummaryCount
        print(df.columns)
        result = harmonize_loop(df.drop(columns=['SummaryCount']), passdf_summaries, instructs, "Please summarize the following features of the paper.", summary_harmonize_columnsets, False)
        if result is not None:
            result['SummaryCount'] = sumcount
            merged_harmonized[key] = df
            harmonized_file = summary_file.replace(".csv", merge_suffix[key] + "-harmonized.csv")
            result.to_csv(harmonized_file, index=False)
        
        # Harmonize the merged extracts
        instructs = column_defs_extract[key]
        
        df = extracts_harmonized[key]
        extcount = df.ExtractCount
        result = harmonize_loop(df.drop(columns=['ExtractCount']), passdf_detaileds, instructs, extract_request, extract_harmonize_columnsets, True)
        if result is not None:
            result['ExtractCount'] = extcount
            merged_harmonized[key] = df
            harmonized_file = merge_extract_file.replace(".csv", merge_suffix[key] + "-harmonized.csv")
            result.to_csv(harmonized_file, index=False)

        count += 1

        if count >= harmonize_count:
            break
