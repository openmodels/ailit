import os, re
import pandas as pd

from config import *
from lib.helpers import *

doiinfo = {}

for search in searches:
    for row in iterate_search(search):
        if row['DOI'] not in doiinfo:
            doiinfo[row['DOI']] = {'search': [search]}
        else:
            doiinfo[row['DOI']]['search'].append(search)

responses = pd.read_csv(response_file)
for index, row in responses.iterrows():
    info = doiinfo[row['DOI']]
    if 'responses' not in info:
        info['responses'] = [row.Source]
    else:
        info['responses'].append(row.Source)
    
furthers = pd.read_csv(questionsource)
for index, row in furthers.iterrows():
    doiinfo[row['DOI']]['furthers'] = True

passfail = pd.read_csv(question_file)
for index, row in passfail.iterrows():
    doiinfo[row['DOI']]['passfail'] = row['Outcome']

verdicts = pd.read_csv(verdict_file)
for index, row in verdicts.iterrows():
    doiinfo[row['DOI']]['verdict'] = True

    if not isinstance(row.DOI, str):
        continue
    fileroot = re.sub(r'[^\w\.\-]', '_', row.DOI)
    transcriptpath = os.path.join(pdfs_dir, fileroot + '.txt')
    targetpath = os.path.join(pdfs_dir, fileroot + '.pdf')

    doiinfo[row['DOI']]['transcript'] = os.path.exists(transcriptpath)
    doiinfo[row['DOI']]['pdf'] = os.path.exists(targetpath)
    doiinfo[row['DOI']]['collation'] = 0
    doiinfo[row['DOI']]['details'] = 0
    
    for dopass in range(dopass_count):
        dopass_suffix = f"-pass{dopass}" if dopass > 0 else ""
        extractpath = os.path.join(extract_dir, fileroot + dopass_suffix + '.yml')
        detailpath = os.path.join(extract_dir, fileroot + dopass_suffix + '.csv')

        if os.path.exists(extractpath):
            doiinfo[row['DOI']]['collation'] += 1
        if os.path.exists(detailpath):
            doiinfo[row['DOI']]['details'] += 1
    
for dopass in range(dopass_count):
    dopass_suffix = f"-pass{dopass}" if dopass > 0 else ""
    dopass_summary_file = summary_file.replace('.csv', dopass_suffix + '.csv')

    if not os.path.exists(dopass_summary_file):
        continue
    summaries = pd.read_csv(dopass_summary_file)
    for doi in pd.unique(summaries.DOI):
        if 'summary' not in doiinfo[doi]:
            doiinfo[doi]['summary'] = []
        row = summaries[summaries.DOI == doi].iloc[0]
        if row[extract_fromsummary] in column_defs_extract:
            doiinfo[doi]['summary'].append("Summarized")
        else:
            doiinfo[doi]['summary'].append("Dropped")

for suffix in merge_suffix.values():
    if os.path.exists(summary_file.replace(".csv", suffix + ".csv")):
        summaries = pd.read_csv(summary_file.replace(".csv", suffix + ".csv"))
        for doi in pd.unique(summaries.DOI):
            doiinfo[doi]['mergesum'] = doiinfo[doi].get('mergesum', 0) + 1
    if os.path.exists(merge_extract_file.replace(".csv", suffix + ".csv")):
        extracts = pd.read_csv(merge_extract_file.replace(".csv", suffix + ".csv"))
        for doi in pd.unique(extracts.DOI):
            doiinfo[doi]['mergeext'] = doiinfo[doi].get('mergeext', 0) + 1

## Make counts
allinfo = []
suminfo = []
for doi, info in doiinfo.items():
    if len(info.get('summary', [])) > dopass_count:
        print(doi)
    lst = ["Search" if 'search' in info else "SourceUnknown", "Responses " + '+'.join(sorted(set(info['responses']))),
           "Verdict" if 'verdict' in info else "",
           "Furthered" if 'furthers' in info else "", info.get('passfail', 'Unasked'),
           "Transcript" if info.get('transcript', False) else "", "PDF" if info.get('pdf', False) else "",
           "Collated" + str(info['collation']) if info.get('collation', 0) > 0 else "",
           ("Summarized" + str(info.get('summary', []).count("Summarized")) if "Summarized" in info.get('summary', []) else "") +
           ("Dropped" + str(info.get('summary', []).count("Dropped")) if "Dropped" in info.get('summary', []) else ""),
           "Detailed" + str(info['details']) if info.get('details', 0) > 0 else "",
           "MergedSummary" + str(info['mergesum']) if info.get('mergesum', 0) > 0 else "",
           "MergedExtract" + str(info['mergeext']) if info.get('mergeext', 0) > 0 else ""]
    allinfo.append(" ".join(lst))
    lst = ["Search" if 'search' in info else "SourceUnknown",
           "Verdict" if 'verdict' in info else "",
           "Identified" if 'furthers' in info and info.get('passfail', 'Unasked') == 'Passed' else "",
           "Browsing" if info.get('transcript', False) else "",
           "Summarized" if "Summarized" in info.get('summary', []) else "",
           "Detailed" if info.get('details', 0) > 0 else "",
           "Merged" if info.get('mergeext', 0) > 0 else ""]
    suminfo.append(" ".join(lst))

print("Detailed Funnel:")
for oneinfo in sorted(set(allinfo)):
    count = len(list(filter(lambda info: info == oneinfo, allinfo)))
    print(f"{oneinfo}: {count}")

print("Simplified Funnel:")
for oneinfo in sorted(set(suminfo)):
    count = len(list(filter(lambda info: info == oneinfo, suminfo)))
    print(f"{oneinfo}: {count}")
    


