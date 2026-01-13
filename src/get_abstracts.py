import os, csv, time
import pandas as pd
from chatwrap import gemini, openaigpt, openai_batch

from config import *
from lib.helpers import *

with open("/Users/admin/research/currentloss/asreview/alldois.csv", 'r') as fp:
    reader = csv.reader(fp)
    dois = [row[0] for row in reader]
print(len(dois))
    
with open("allabstracts.csv", 'w') as fp:
    writer = csv.writer(fp)
    writer.writerow(["DOI", "Abstract"])

    for search in searches:
        for row in iterate_search(search):
            print(row['DOI'])
            if row['DOI'] in dois:
                writer.writerow([row['DOI'], row['Abstract']])

