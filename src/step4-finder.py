import os, io, re, contextlib
import pandas as pd
import asyncio, platform
from contextlib import redirect_stdout
from lib import finder
from pyppeteer import launch

from config import *

found_any = True

async def main():
    global found_any
    found_any = False
    
    if platform.system() == "Darwin":
        asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())

    count = 0
    verdicts = pd.read_csv(verdict_file)
    for index, row in verdicts.iterrows():
        if row.priority >= priority_limit:
            targetpath = os.path.join(pdfs_dir, re.sub(r'[^\w\.\-]', '_', row.DOI) + '.pdf')
            statuspath = targetpath[:-4] + '.txt'
            if os.path.exists(statuspath) or os.path.exists(targetpath):
                continue

            found_any = True
            
            print(row.DOI)
            count += 1
            with open(statuspath, 'w') as fp:
                with contextlib.redirect_stdout(fp):
                    browser = await launch(headless=True, args=['--no-sandbox'])
                    try:
                        result, link = await finder.finder_pdf(row.DOI, browser, targetpath, statuspath)
                        print(result)
                        if link is not None:
                            print(link)
                    finally:
                        try:
                            await browser.close()
                        except Exception as e:
                            print(f"Error closing browser: {e}")

            print([row.DOI, result])

    return count

if __name__ == '__main__':
    count = finder_count
    while count > 0 and found_any:
        try:
            count -= asyncio.run(main())
        except RuntimeError as ex:
            print(ex)
            break
        except Exception as ex:
            pass
        
