import os, csv, time, yaml, re
import argparse
import pandas as pd
import openai
from pypdf import PdfReader

from lib import interaction, images
from config import *

def pass3_extract(pdfpath, instructs, request, xtt, paperinfo):
    reader = PdfReader(pdfpath)

    columninfo = "  " + "\n  ".join([f"{column}: {question[0]}" for column, question in instructs.items()])
    headerstr = ",".join([f"\"{column}\"" for column in instructs.keys()])

    allrows = []
    for pagenum, info in xtt[extract_fromcollate].items():
        page = reader.pages[pagenum - 1]
        print(f"Page {pagenum}")
        rows = pass3_extract_page(pdfpath, page, instructs, request, columninfo, headerstr, paperinfo, pagenum)
        
        if rows:
            allrows.append(pd.DataFrame(rows))

    if allrows:
        return pd.concat(allrows, ignore_index=True)
    return None
    
def pass3_extract_page(pdfpath, page, instructs, request, columninfo, headerstr, paperinfo, pagenum):
    pagetext = images.textify_page(pdfpath, page, 'high')

    prompt = f"""{abstract_prompt} Here is some information about a pager identified as relevant to the search:
{paperinfo}

The following is the text of page {pagenum}, which may have detailed information we want to extract:
{pagetext}

{request}

Report this information under the following columns:
{columninfo}

Specify the result as a CSV, provided in triple quotes. Your response should start:
```
{headerstr}
...
```

This page may have no relevant information, in which case report the header with no following rows."""

    chat = [{"role": "user", "content": prompt}]

    return interaction.get_csvtext_validated(chat, 3, instructs)
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='Step 7: Extraction',
        description='Extracts detailed information from a summarized PDF.')
    parser.add_argument('-d', '--dryrun', action='store_true')

    args = parser.parse_args()

    count = 0
    for dopass in range(dopass_count):
        dopass_suffix = f"-pass{dopass}" if dopass > 0 else ""
        dopass_summary_file = summary_file.replace('.csv', dopass_suffix + '.csv')

        summaries = pd.read_csv(dopass_summary_file)
        for index, row in summaries.iterrows():
            if row[extract_fromsummary] in column_defs_extract:
                fileroot = re.sub(r'[^\w\.\-]', '_', row.DOI)
                targetpath = os.path.join(pdfs_dir, fileroot + '.pdf')
                extractpath = os.path.join(extract_dir, fileroot + dopass_suffix + '.yml')
                detailpath = os.path.join(extract_dir, fileroot + dopass_suffix + '.csv')
                if os.path.exists(targetpath) and os.path.exists(extractpath) and not os.path.exists(detailpath):
                    print(row.DOI)
                    if args.dryrun:
                        continue
                    count += 1

                    with open(extractpath, 'r') as fp:
                        xtt = yaml.safe_load(fp)

                    if extract_fromcollate not in xtt:
                        continue
                        
                    paperinfo = [f"  {key}: {value}" for key, value in row.items() if not pd.isna(value) and not key[:7] == "Unnamed"]
                
                    df = pass3_extract(targetpath, column_defs_extract[row[extract_fromsummary]], extract_request[row[extract_fromsummary]], xtt, "\n".join(paperinfo))
                    if df is not None:
                        df.to_csv(detailpath)
                    else:
                        with open(detailpath, 'w') as fp:
                            fp.write("\n") # No data found.
            
                    if count >= extract_count:
                        break
