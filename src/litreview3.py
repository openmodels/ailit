import os, io, re, contextlib
import pandas as pd
import asyncio, platform
from contextlib import redirect_stdout
from logic import finder
from pyppeteer import launch

from litreview0 import *

async def main():
    if platform.system() == "Darwin":
        asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())

    verdicts = pd.read_csv(verdict_file)
    for index, row in verdicts.iterrows():
        if row.common in ["Code failure", "Ambiguous"] or any([key in row.common for key in include_codes.keys()]):
            targetpath = os.path.join("pdfs", re.sub(r'[^\w\.\-]', '_', row.DOI) + '.pdf')
            statuspath = targetpath[:-4] + '.txt'
            if os.path.exists(statuspath) or os.path.exists(targetpath):
                continue

            print(row.DOI)
            with open(statuspath, 'w') as fp:
               with contextlib.redirect_stdout(fp):
                   browser = await launch(headless=True, args=['--no-sandbox'])
                   try:
                       result = await finder.finder_pdf(row.DOI, browser, targetpath, statuspath)
                       print(result)
                       if result == 'break':
                           break
                   finally:
                       try:
                           await browser.close()
                       except Exception as e:
                           print(f"Error closing browser: {e}")

            print([row.DOI, result])

if __name__ == '__main__':
    asyncio.run(main())
