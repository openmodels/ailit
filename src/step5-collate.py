import os, csv, time, yaml, re
import pandas as pd
import openai
from pypdf import PdfReader

from lib import interaction, images
from config import *

def pass1_collate(pdfpath):
    reader = PdfReader(pdfpath)
    columninfo = {} # column: { page: text }
    pagenum = 0
    for page in reader.pages:
        pagenum += 1
        print(f"Page {pagenum}")
        pagetext = images.textify_page(pdfpath, page, 'low')

        columns = "  " + "\n  ".join([f"{key}: {value}" for key, value in column_defs_collate.items()])

        prompt = f"""{abstract_prompt} The following is a page from a paper that is potentially relevant to my review:
{pagetext}

Please summarize and extract any relevant information from this page relevant to the following categories:
{columns}

Only include information specifically contributed by this paper, not material referenced from other studies.

Specify the results in a list with single lines of text in a YAML dictionary (each line should read "Category": "Extracted Information"), and only include those entries for this page where there is concrete relevant information. This page may have no relevant information, in which case report 'No relevant information'."""

        response = interaction.aiengine.chat_response([{"role": "user", "content": prompt}])
        columns = interaction.extract_yaml_dict(response)

        if isinstance(columns, dict):
            for column in columns:
                if column not in columninfo:
                    columninfo[column] = {}
                columninfo[column][pagenum] = columns[column]

    return columninfo

if not os.path.exists(extract_dir):
    os.makedirs(extract_dir)

verdicts = pd.read_csv(verdict_file.replace(".csv", "-further.csv"))
count = 0
for dopass in range(dopass_count):
    print(f"Pass {dopass+1}")
    dopass_suffix = f"-pass{dopass}" if dopass > 0 else ""
    for index, row in verdicts.iterrows():
        if row.Priority >= priority_limit:
            fileroot = re.sub(r'[^\w\.\-]', '_', row.DOI)
            targetpath = os.path.join(pdfs_dir, fileroot + '.pdf')
            extractpath = os.path.join(extract_dir, fileroot + dopass_suffix + '.yml')
            if os.path.exists(targetpath) and not os.path.exists(extractpath):
                print(row.DOI)
                count += 1

                # Step 1: Extract relevant information from each page
                columninfo = pass1_collate(targetpath)

                with open(extractpath, 'w') as fp:
                    yaml.safe_dump(columninfo, fp)

                if count >= collate_count:
                    break
