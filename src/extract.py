import csv
import pandas as pd

from config import *
from lib.helpers import *

verdict_file = "../brazil.csv"
verdicts = pd.read_csv(verdict_file)
toinclude = set(verdicts.DOI)

with open(verdict_file.replace(".csv", "-abstracts.csv"), 'w') as fp:
    writer = csv.writer(fp)
    writer.writerow(['DOI', 'Title', 'Abstract'])

    for search in searches:
        for row in iterate_search(search):
            if row['DOI'] in toinclude:
                writer.writerow([row['DOI'], row['Title'], row['Abstract']])
                toinclude.remove(row['DOI'])
