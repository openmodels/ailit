import os, csv, time, yaml, re, copy
import argparse
import pandas as pd
import openai
from pypdf import PdfReader

from lib import interaction, images
from config import *

def pass3_extract(abstract, pdfpath, instructs, request, xtt, paperinfo):
    if pdfpath:
        reader = PdfReader(pdfpath)

    instructs2 = copy.copy(instructs)
    instructs2['sourcematerial'] = ["Please write quotes or evidence from the material provided above that justifies or provides necessary context for material in the other columns."]
    
    columninfo = "  " + "\n  ".join([f"{column}: {question[0]}" for column, question in instructs2.items()])
    headerstr = ",".join([f"\"{column}\"" for column in instructs2.keys()])

    allrows = []
    if xtt is not None:
        for pagenum, info in xtt[extract_fromcollate].items():
            page = reader.pages[pagenum - 1]
            print(f"Page {pagenum}")
            rows = pass3_extract_page(abstract, pdfpath, page, instructs2, request, columninfo, headerstr, paperinfo, pagenum)
        
            if rows:
                df = pd.DataFrame(rows)
                allrows.append(df)
    else:
        print("Abstract")
        rows = pass3_extract_abstract(abstract, instructs2, request, columninfo, headerstr)

    if allrows:
        return pd.concat(allrows, ignore_index=True)
    return None
    
def pass3_extract_page(abstract, pdfpath, page, instructs2, request, columninfo, headerstr, paperinfo, pagenum):
    pagetext = images.textify_page(pdfpath, page, 'high')

    prompt = f"""{abstract_prompt} Here is the abstract of a pager identified as relevant to the search:
{abstract}

And here is some additional information extracted:
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
    return interaction.get_csvtext_validated(chat, 3, instructs2)

def pass3_extract_abstract(abstract, instructs2, request, columninfo, headerstr):
    prompt = f"""{abstract_prompt} 
The following is the abstract of the paper, which may have detailed information we want to extract:
{abstract}

{request}

Report this information under the following columns:
{columninfo}

Specify the result as a CSV, provided in triple quotes. Your response should start:
```
{headerstr}
...
```

This abstract may have no relevant information, in which case report the header with no following rows."""

    chat = [{"role": "user", "content": prompt}]
    return interaction.get_csvtext_validated(chat, 3, instructs2)
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='Step 7: Extraction',
        description='Extracts detailed information from a summarized PDF.')
    parser.add_argument('dois', nargs='*', default=None, help='The DOI(s) to process.')
    parser.add_argument('-d', '--dryrun', action='store_true')

    args = parser.parse_args()

    verdicts = pd.read_csv(verdict_file.replace(".csv", "-further.csv"))

    count = 0
    for dopass in range(dopass_count):
        dopass_suffix = f"-pass{dopass}" if dopass > 0 else ""
        dopass_summary_file = summary_file.replace('.csv', dopass_suffix + '.csv')

        if not os.path.exists(dopass_summary_file):
            break
        summaries = pd.read_csv(dopass_summary_file)
        for index, row in summaries.iterrows():
            if extract_fromsummary == 'All' or row[extract_fromsummary] in column_defs_extract:
                fileroot = re.sub(r'[^\w\.\-]', '_', row.DOI)
                detailpath = os.path.join(extract_dir, fileroot + dopass_suffix + '.csv')
                extractpath = os.path.join(extract_dir, fileroot + dopass_suffix + '.yml')
                if args.dois:
                    if row.DOI not in args.dois:
                        continue
                else:
                    if os.path.exists(detailpath) and os.path.getmtime(detailpath) > os.path.getmtime(extractpath):
                        continue
                
                print(row.DOI)
                if args.dryrun:
                    continue
                    
                targetpath = os.path.join(pdfs_dir, fileroot + '.pdf')
                if os.path.exists(targetpath) and os.path.exists(extractpath):
                    with open(extractpath, 'r') as fp:
                        xtt = yaml.safe_load(fp)

                    if extract_fromcollate not in xtt:
                        continue
                else:
                    xtt = None
                    targetpath = None
                        
                count += 1
                        
                paperinfo = [f"  {key}: {value}" for key, value in row.items() if not pd.isna(value) and not key[:7] == "Unnamed"]

                if extract_fromsummary == 'All':
                    column_defs = column_defs_extract['All']
                    request = extract_request
                else:
                    column_defs = column_defs_extract[row[extract_fromsummary]]
                    request = extract_request[row[extract_fromsummary]]

                abstract = verdicts[verdicts['DOI'] == row.DOI].Abstract.iloc[0]
                        
                df = pass3_extract(abstract, targetpath, column_defs, request, xtt, "\n".join(paperinfo))
                if df is not None:
                    df.to_csv(detailpath)
                else:
                    with open(detailpath, 'w') as fp:
                        fp.write("\n") # No data found.
            
                if count >= extract_count:
                    break
