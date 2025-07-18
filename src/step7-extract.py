import os, csv, time, yaml, re
from io import StringIO
import pandas as pd
import openai
from pypdf import PdfReader

from lib import interaction, images
from config import *

def pass3_extract(pdfpath, instructs, xtt, paperinfo):
    reader = PdfReader(pdfpath)

    columninfo = "  " + "\n  ".join([f"{column}: {question[0]}" for column, question in instructs.items()])
    headerstr = ",".join([f"\"{column}\"" for column in instructs.keys()])

    allrows = []
    for pagenum, info in xtt[extract_fromcollate].items():
        page = reader.pages[pagenum - 1]
        print(f"Page {pagenum}")
        rows = pass3_extract_page(pdfpath, page, instructs, columninfo, headerstr, paperinfo, pagenum)
        
        if rows:
            allrows.append(pd.DataFrame(rows))

    if allrows:
        return pd.concat(allrows, ignore_index=True)
    return None
    
def pass3_extract_page(pdfpath, page, instructs, columninfo, headerstr, paperinfo, pagenum):
    pagetext = images.textify_page(pdfpath, page, 'high')

    prompt = f"""{abstract_prompt} Here is some information about a pager identified as relevant to the search:
{paperinfo}

The following is the text of page {pagenum}, which may have detailed information we want to extract:
{pagetext}

Please summarize and extract any relevant information from this page under the following columns:
{columninfo}

Specify the result as a CSV, provided in triple quotes. Your response should start:
```
{headerstr}
...
```

This page may have no relevant information, in which case report the header with no following rows."""

    chat = [{"role": "user", "content": prompt}]

    for attempts in range(3):
        response = interaction.get_internaltext(chat, 3)

        csvfp = StringIO(response)
        reader = csv.reader(csvfp)
        header = []
        while not header:
            try:
                header = next(reader)
            except:
                return [] # Never got a header
        if header != list(instructs.keys()):
            chat = interaction.chat_push(interaction.chat_push(chat, 'assistant', f"```{response}```"), 'user', "Sorry, the header did not match. Can you try again?")
            continue

        validrows = []
        errors = []
        rownum = 0
        for row in reader:
            rownum += 1
            anyinvalid = False
            for ii in range(len(header)):
                for check in instructs[header[ii]][1:]:
                    isinvalid = check(row[ii])
                    if isinvalid:
                        errors.append(f"Row {rownum}, column {header[ii]}: {isinvalid}")
                        anyinvalid = True

            if not anyinvalid:
                validrows.append({header[ii]: row[ii] for ii in range(len(header))})
                
        if errors:
            errorstr = "\n".join(errors)
            chat = interaction.chat_push(interaction.chat_push(chat, 'assistant', f"```{response}```"), 'user', f"I got the following errors:\n{errorstr}\nCan you try again?")
            continue

        return validrows

    return [] # Failed
    
count = 0
summaries = pd.read_csv(summary_file)
for index, row in summaries.iterrows():
    if row[extract_fromsummary] in column_defs_extract:
        fileroot = re.sub(r'[^\w\.\-]', '_', row.DOI)
        targetpath = os.path.join(pdfs_dir, fileroot + '.pdf')
        extractpath = os.path.join(extract_dir, fileroot + '.yml')
        detailpath = os.path.join(extract_dir, fileroot + '.csv')
        if os.path.exists(targetpath) and os.path.exists(extractpath) and not os.path.exists(detailpath):
            print(row.DOI)
            count += 1

            with open(extractpath, 'r') as fp:
                xtt = yaml.safe_load(fp)

            paperinfo = [f"  {key}: {value}" for key, value in row.items() if not pd.isna(value) and not key[:7] == "Unnamed"]
                
            df = pass3_extract(targetpath, column_defs_extract[row[extract_fromsummary]], xtt, "\n".join(paperinfo))
            if df is not None:
                df.to_csv(detailpath)
            else:
                with open(detailpath, 'w') as fp:
                    fp.write("\n") # No data found.
            
            if count >= extract_count:
                break
