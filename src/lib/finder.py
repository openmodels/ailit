import os, re, json, requests, io
from lib import interaction
from pypdf import PdfReader
import markdownify
from bs4 import BeautifulSoup
import asyncio

from dotenv import load_dotenv

load_dotenv(".env")
api_key = os.getenv('SEARCH_API_KEY')
assert api_key
cse_id = "f179deb41d1a64339"

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

async def fetch_url(page, url):
    response = await page.goto(url, {'timeout': 30000})
    await page.waitForNavigation({'timeout': 10000})
    content = await page.content()

    content_type = response.headers.get('content-type', '')

    return content, content_type

def download_url(url, timeout=30, size_limit_mb=20):
    size_limit_bytes = size_limit_mb * 1024 * 1024  # Convert MB to bytes
    
    # Send a HEAD request to get the headers with a timeout
    response = requests.head(url, timeout=timeout)
    response.raise_for_status()  # Check for HTTP errors

    # Get the content type from headers
    content_type = response.headers.get('Content-Type')
    content_length = response.headers.get('Content-Length')

    # Check if the content length is provided and convert it to an integer
    if content_length is not None:
        content_length = int(content_length)

        # Check if the file size exceeds the limit
        if content_length > size_limit_bytes:
            raise OverflowError()

    response = requests.get(url, stream=True, timeout=timeout, allow_redirects=True)
    response.raise_for_status()  # Check for HTTP errors
    content = io.BytesIO()
    total_downloaded = 0

    for chunk in response.iter_content(chunk_size=8192):
        total_downloaded += len(chunk)
        content.write(chunk)
        
        # Abort if the total downloaded size exceeds the limit
        if total_downloaded > size_limit_bytes:
            raise OverflowError()
    content.seek(0)
        
    return content.getbuffer(), content_type
    
def google_search(query, num_results=10):
    service_url = 'https://www.googleapis.com/customsearch/v1'
    params = {
        'q': query,
        'key': api_key,
        'cx': cse_id,
        'num': num_results
    }
    response = requests.get(service_url, params=params, headers=headers)
    if response.status_code == 429:
        raise RuntimeError("Google search quota exceeded.")
    results = response.json()
    
    info = [{'title': result['title'],
             'link': result['link'],
             'snippet': result['snippet']}
            for result in results.get('items', [])]
    return info

async def finder_download(page, url, pathprefix):
    ## First, try a direct download
    try:
        content, content_type = await asyncio.get_event_loop().run_in_executor(None, download_url, url)
        if 'text/html' in content_type:
            soup = BeautifulSoup(content, 'html.parser')
            alltext = soup.get_text()
            if len(alltext) < 100:
                raise ValueError("Implausibly small webpage.") # kick over to fetch_url
    except OverflowError as ex:
        return "too big"
    except:
        try:
            content, content_type = await fetch_url(page, url)
        except requests.exceptions.RequestException as e:
            return "error"
        except Exception as e:
            print(str(e))
            return "error"
        
    # Determine content type and process accordingly
    if content_type is None:
        return "error"
    elif 'text/html' in content_type:
        with open(pathprefix + '.html', 'w') as fp:
            fp.write(content)
        return "finder_html"
    elif 'application/pdf' in content_type:
        with open(pathprefix + '.pdf', 'wb') as fp:
            fp.write(content)
        return "finder_pdf"
    else:
        print(content_type)
        return "unsupported"

def get_scholar_versions(query):
    search_url = f"https://scholar.google.com/scholar?q={query}"
    
    # Request search page
    response1 = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response1.content, 'html.parser')
    
    # Find the "all N versions" link
    link = soup.find('a', string=lambda x: x and 'all' in x.lower() and 'versions' in x.lower())
    if not link:
        return response1.content, None, []
    
    # Compose the absolute URL for all versions
    all_versions_url = "https://scholar.google.com" + link.get('href')
    
    # Request the all versions page
    response2 = requests.get(all_versions_url, headers=headers)
    soup = BeautifulSoup(response2.content, 'html.parser')
    
    # Extract PDFs from the results
    pdf_links = [a['href'] for a in soup.find_all('a', href=True) if 'pdf' in a['href'].lower()]
    return response1.content, response2.content, pdf_links
    
commandprompt = """
 - Google search: Perform a google search by writing ```google("google search terms here")```
 - Direct URL retrieval: Get a URL by writing ```geturl("full-url-here")```
Please include the triple-backticks."""

finalcommandprompt = """
 - Direct URL retrieval: Get a URL by writing ```geturl("full-url-here")```
Please include the triple-backticks. This is the final attempt, so try to retrieve the PDF by a direct URL."""

ignoredcommandrompt = "No commands available; this was the final attempt."

numattempts = 10

async def finder_pdf(document, browser, targetpath, statuspath):
    page = await browser.newPage()  # Create a new page
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

    try:
        result, link = await finder_pdf_helper(document, page)
        try:
            os.remove("downloaded.html")
        except FileNotFoundError:
            pass
    
        if result == "found":
            os.rename("downloaded.pdf", targetpath)
        else:
            try:
                os.remove("downloaded.pdf")
            except FileNotFoundError:
                pass

        return result, link
    finally:
        try:
            await page.close()
        except:
            pass

    return "unknown", None

def check_pdf(filepath, chat2):
    with open(filepath, 'rb') as fp:
        reader = PdfReader(fp)
        page1 = reader.pages[0].extract_text(extraction_mode="layout", layout_mode_space_vertically=False, layout_mode_strip_rotated=False)
        content = "Here is the first page of this PDF formatted as text:\n===\n" + page1 + "\n===\n"
        chat3 = interaction.chat_push(chat2, 'user', f"{content}\nIs this the requested document? Specify the answer '[yes]' or '[no]' in brackets.")
        action = interaction.get_action(chat3, ['yes', 'no'])
        if action == 'yes':
            return True
    return False

def extract_middle_differences(str1, str2):
    # Find common prefix
    i = 0
    while i < min(len(str1), len(str2)) and str1[i] == str2[i]:
        i += 1
    common_prefix_length = i

    # Find common suffix
    j = 0
    while (j < min(len(str1), len(str2)) - common_prefix_length and
           str1[-j - 1] == str2[-j - 1]):
        j += 1
    common_suffix_length = j

    # Extract differing middle parts
    middle_part1 = str1[common_prefix_length:len(str1) - common_suffix_length]
    middle_part2 = str2[common_prefix_length:len(str2) - common_suffix_length]

    return middle_part1, middle_part2

async def finder_pdf_helper(document, page):
    urls_attempted = set()
    
    # First, try the predefined Google Scholar logic
    html1, html2, links = get_scholar_versions(document)
    if links:
        for link in links:
            if link in urls_attempted:
                continue
            nextstep = await finder_download(page, link, "downloaded")
            urls_attempted.add(link)
            if nextstep == 'finder_pdf':
                if check_pdf("downloaded.pdf", interaction.chat_push(interaction.chat_push([], 'user', f'I would like you to find the document `{document}` (or a recent pre-print) on the internet.'),
                                                               'assistant', "I have downloaded a candidate document, which may be the one you are looking for.")):
                    return "found", link

    markdown1 = markdownify.markdownify(html1, heading_style="ATX")

    if html2:
        markdown2 = markdownify.markdownify(html2, heading_style="ATX")
        markdown1, markdown2 = extract_middle_differences(markdown1, markdown2)

        try:
            markdown1 = markdown1[markdown1.index('###'):]
            markdown2 = markdown2[markdown2.index('###'):]
        except:
            pass

        chat2 = interaction.chat_push([], 'user', f'I would like you to find the document `{document}` (or a recent pre-print) on the internet. I started with a Google Scholar search and got the following:\n===\n{markdown1}\n===\nAnd when I went into the link for multiple versions I got:\n===\n{markdown2}\n===\nPlease continue the search. To do this, please direct me to perform one of the following actions: {commandprompt}')
    else:
        try:
            markdown1 = markdown1[markdown1.index('###'):]
        except:
            pass

        chat2 = interaction.chat_push([], 'user', f'I would like you to find the document `{document}` (or a recent pre-print) on the internet. I started with a Google Scholar search and got the following:\n===\n{markdown1}\n===\nPlease continue the search. To do this, please direct me to perform one of the following actions: {commandprompt}')

    for attempt in range(numattempts):
        command, text = interaction.get_stringcommand(chat2, 3)
        if command is None:
            return "nocommand", None

        if attempt == numattempts - 1:
            nextcommandprompt = ignoredcommandrompt
        elif attempt == numattempts - 2:
            nextcommandprompt = finalcommandprompt
        else:
            nextcommandprompt = commandprompt
        
        if command == 'geturl':
            if text in urls_attempted:
                chat2 = interaction.chat_push(interaction.chat_push(chat2, 'assistant', f'```{command}("{text}")```'), 'user', "That URL was already tried." + f' Please try again by performing one of the following actions: {nextcommandprompt}')
                continue
            nextstep = await finder_download(page, text, "downloaded")
            urls_attempted.add(text)
            if nextstep == 'finder_html':
                with open("downloaded.html", "r", encoding="utf-8") as file:
                    content = file.read()
                markdown = markdownify.markdownify(content, heading_style="ATX")
                if len(markdown) > 2000:
                    markdown = markdown[:2000]
                    content = "Here is the first page of this webpage formatted as Markdown:\n===\n" + markdown + "\n===\n"
                else:
                    markdown_rest = ""
                    content = "Here is the webpage formatted as Markdown:\n===\n" + markdown + "\n===\n"
                chat2 = interaction.chat_push(interaction.chat_push(chat2, 'assistant', f"```geturl({text})```"), 'user', f'{content} Now, you can choose to follow a link or perform another search. Please specify one of the following actions: {nextcommandprompt}')
                continue
            elif nextstep == 'finder_pdf':
                if check_pdf("downloaded.pdf", interaction.chat_push(chat2, 'assistant', f'```{command}("{text}")```')):
                    return "found", text
                else:
                    chat2 = interaction.chat_push(interaction.chat_push(chat2, 'assistant', f'```{command}("{text}")```'), 'user', "The file was downloaded, but turned out to be the wrong PDF." + f' Please try again by performing one of the following actions: {nextcommandprompt}')
                    continue
            elif nextstep == 'unsupported':
                explained = 'That retrieved a file that was neither an HTML nor PDF file and so is unsupported.'
            elif nextstep == 'error':
                explained = 'That request returned an error, perhaps because of a timeout.'
            elif nextstep == 'toobig':
                explained = 'That request returned a document that was too big to be processed.'
                
            chat2 = interaction.chat_push(interaction.chat_push(chat2, 'assistant', f'```{command}("{text}")```'), 'user', explained + f' Please try again by performing one of the following actions: {nextcommandprompt}')
            
        if command == 'google':
            results = await asyncio.get_event_loop().run_in_executor(None, google_search, text)
            if len(results) == 0:
                chat2 = interaction.chat_push(interaction.chat_push(chat2, 'assistant', f"```google({text})```"), 'user', 'I did that google search but it returned no results. Please specify one of the following actions: {nextcommandprompt}')
            else:
                restext = "\n\n".join([result['title'] + "\n" + result['link'] + "\n" + result['snippet'] for result in results])
                chat2 = interaction.chat_push(interaction.chat_push(chat2, 'assistant', f"```google({text})```"), 'user', 'Here are the google results:\n===\n' + restext + f'\n===\nNow, you can choose to follow one of those links or perform another search. Please specify one of the following actions: {nextcommandprompt}')

    return "maxattempt", None
