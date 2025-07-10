import os, re, yaml
import pandas as pd

from lib import interaction, commands
from lib.helpers import *
from config import *

# Step 2: Summarize certain columns (we will pass these on to other calls)
def pass2_summarize(targetpath, row, columninfo, coldefs, results):
    for col, command in coldefs.items():
        results[col] = [pass2_summarize_one(targetpath, row, columninfo, coldefs, col, command)] # wrap in a list for Pandas

def pass2_summarize_one(targetpath, row, columninfo, coldefs, col, command):
    # Special commands
    if isinstance(command, str):
        if command == "LINK":
            with open(targetpath.replace('.pdf', '.txt'), 'r') as f:
                for line in f:
                    pass
                return line.strip()
        if command == "STATUS":
            return "Step 5"
        if command in ["SUMMARIZE", "BRIEF"]:
            namematch = commands.extract_alphanumeric_and_spaces(col)
            allpages = {}
            for key, values in columninfo.items():
                if commands.extract_alphanumeric_and_spaces(key) == namematch:
                    allpages.update(values)
                               
            if len(allpages) == 1:
                return allpages[next(allpages.keys())]

            texts = '\n'.join([f"Page {num}: {text}" for num, text in allpages.items()])
            if command == "SUMMARIZE":
                instruct = "Please summarize this information as a single concise notes, avoiding phrases like 'This paper ...'."
            else:
                instruct = "Please provide a brief keywords as the summary, rather than full sentences."
            
            prompt = f"""{abstract_prompt} Right now, I want to summarize material related to '{col}'. The following notes were extracted from pages from a paper that is potentially relevant to my review:
===
{texts}
===

{instruct} Specify the summary in triple backticks, like this: ```Synopsis here.```."""

            return interaction.get_internaltext([{"role": "user", "content": prompt}], 3).strip()

        return command

    ## Run the command
    return command(row, columninfo)

verdicts = pd.read_csv(verdict_file)
if os.path.exists(summary_file):
    done = pd.read_csv(summary_file)
    knowndoi = done.DOI
else:
    done = None
    knowndoi = []

allcols = []
for key in column_defs_summary:
    allcols.extend(column_defs_summary[key].keys())
    
count = 0
getout = False
for search in searches:
    if getout:
        break
    for row in iterate_search(search):
        if row.DOI in knowndoi:
            continue
        verdictrow = verdicts[verdicts.DOI == row.DOI]
        if len(verdictrow) == 0:
            continue
        if verdictrow.priority.iloc[0] < priority_limit:
            continue

        fileroot = re.sub(r'[^\w\.\-]', '_', row.DOI)
        targetpath = os.path.join(pdfs_dir, fileroot + '.pdf')
        extractpath = os.path.join(extract_dir, fileroot + '.yml')
        if os.path.exists(targetpath) and os.path.exists(extractpath) and row.DOI not in knowndoi:
            print(row.DOI)
            print(targetpath)
            print(extractpath)
            count += 1

            with open(extractpath, 'r') as fp:
                columninfo = yaml.safe_load(fp)
            
            # Step 2: Produce summary rows
            results = {'DOI': row.DOI}
            pass2_summarize(targetpath, row, columninfo, column_defs_summary['All'], results)
            if results['NEXT'][0] != "N/A":
                nextset = results['NEXT'][0]
                del results['NEXT']
                if 'Any' in column_defs_summary:
                    pass2_summarize(targetpath, row, columninfo, column_defs_summary['Any'], results)
                    
                while nextset:
                    pass2_summarize(targetpath, row, columninfo, column_defs_summary[nextset], results)
                    if results.get('NEXT', ['N/A'])[0] != 'N/A':
                        nextset = results['NEXT'][0]
                        del results['NEXT']
                    else:
                        nextset = None
            else:
                del results['NEXT']

            for col in allcols:
                if col != 'NEXT' and col not in results:
                    results[col] = [""]

            print(results)
                    
            if done is None:
                done = pd.DataFrame(results)
            else:
                done = pd.concat([done, pd.DataFrame(results)], ignore_index=True)
            done.to_csv(summary_file)
                        
            if count >= summary_count:
                break
