import os, io, re, contextlib
from datetime import datetime, timedelta
import time
import pandas as pd
import asyncio, platform
from contextlib import redirect_stdout
from lib import finder
from pyppeteer import launch

from config import *

found_any = True

def is_file_older_than_days(filepath, days_old):
    """
    Checks if a file's last modification time is older than a specified number of days.

    Args:
        filepath (str): The path to the file.
        days_old (int/float): The age threshold in days.

    Returns:
        bool: True if the file is older, False otherwise or if file doesn't exist.
    """
    if not os.path.exists(filepath):
        print(f"Error: File not found at {filepath}")
        return False

    # Get the file's last modification time in seconds since the epoch
    file_mtime_timestamp = os.path.getmtime(filepath)

    # Calculate the cutoff time (current time minus the age threshold)
    cutoff_time_datetime = datetime.now() - timedelta(days=days_old)
    
    # Convert the file modification timestamp to a datetime object for comparison
    file_mtime_datetime = datetime.fromtimestamp(file_mtime_timestamp)

    # Compare the file's time to the cutoff time
    if file_mtime_datetime < cutoff_time_datetime:
        return True
    else:
        return False

async def main():
    global found_any
    found_any = False
    
    if platform.system() == "Darwin":
        asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())

    count = 0
    verdicts = pd.read_csv(verdict_file.replace(".csv", "-further.csv"))
    for index, row in verdicts.iterrows():
        if row.Priority >= priority_limit:
            targetpath = os.path.join(pdfs_dir, re.sub(r'[^\w\.\-]', '_', row.DOI) + '.pdf')
            statuspath = targetpath[:-4] + '.txt'
            print(targetpath)
            if os.path.exists(statuspath):
                if not is_file_older_than_days(statuspath, refresh_days):
                    print("Recent attempt.")
                    continue
            if os.path.exists(targetpath):
                print("Exists.")
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
        
