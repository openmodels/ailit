import os, csv, time, yaml, re
import pandas as pd
import openai
from pypdf import PdfReader

from lib import interaction, images
from config import *

def extract_yaml_dict(text):
    # Regex to match dictionary entries allowing for quoted or unquoted keys and values
    yaml_regex = r'^\s*-?\s*(\'[a-zA-Z0-9_() ]+\'|"[a-zA-Z0-9_() ]+"|[a-zA-Z0-9_() ]+)\s*:\s*("[^"\n]*"|\'[^\n]*\'|[^"\n]+)\s*$'
    
    # Find all matches for the entire block
    matches = re.findall(yaml_regex, text, re.MULTILINE)
    if matches:
        # Combine matched lines into a single string
        yaml_text = '\n'.join([f"{key}: {value}" for key, value in matches])
        
        # Parse the YAML text into a Python dictionary
        try:
            yaml_dict = yaml.safe_load(yaml_text)
            return yaml_dict
        except yaml.YAMLError as exc:
            print(f"Error parsing YAML: {exc}")
            return None
    else:
        print("No YAML dictionary found.")
        return None

def pass1_collate(pdfpath):
    reader = PdfReader(pdfpath)
    columninfo = {} # column: { page: text }
    pagenum = 0
    for page in reader.pages:
        pagenum += 1
        print(f"Page {pagenum}")
        text = page.extract_text(extraction_mode="layout", layout_mode_space_vertically=False, layout_mode_strip_rotated=False)

        ## Process images
        imagetexts = []
        for count, image_file_object in enumerate(page.images):
            response = images.get_image_description(pdfpath, image_file_object, 'low')
            if response:
                imagetexts.append(response)

        if len(imagetexts) > 0:
            image_text = "In addition, the page has the following images, as described below:\n===\n" + "\n===\n".join(imagetexts) + "\n===\n"
        else:
            image_text = ""

        columns = "  " + "\n  ".join([f"{key}: {value}" for key, value in column_defs_collate.items()])

        prompt = f"""{abstract_prompt} The following is a page from a paper that is potentially relevant to my review:
===
{text}
===
{image_text}

Please summarize and extract any relevant information from this page relevant to the following categories:
{columns}

Specify the results in a list with single lines of text in a YAML dictionary (each line should read "Category": "Extracted Information"), and only include those entries for this page where there is concrete relevant information. This page may have no relevant information, in which case report 'No relevant information'."""

        response = interaction.aiengine.chat_response([{"role": "user", "content": prompt}])
        columns = extract_yaml_dict(response)

        if columns:
            for column in columns:
                if column not in columninfo:
                    columninfo[column] = {}
                columninfo[column][pagenum] = columns[column]

    return columninfo

verdicts = pd.read_csv(verdict_file)
count = 0
for index, row in verdicts.iterrows():
    if row.priority >= priority_limit:
        fileroot = re.sub(r'[^\w\.\-]', '_', row.DOI)
        targetpath = os.path.join(pdfs_dir, fileroot + '.pdf')
        extractpath = os.path.join(extract_dir, fileroot + '.yml')
        if os.path.exists(targetpath) and not os.path.exists(extractpath):
            print(row.DOI)
            count += 1

            # Step 1: Extract relevant information from each page
            columninfo = pass1_collate(targetpath)

            with open(extractpath, 'w') as fp:
                yaml.safe_dump(columninfo, fp)

            if count >= collate_count:
                break
