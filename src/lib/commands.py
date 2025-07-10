import re
from lib import interaction

def extract_alphanumeric_and_spaces(s):
    # Using regex to find all alphanumeric characters and spaces
    result = re.sub(r'[^A-Za-z0-9\s]', '', s)
    # Convert to uppercase
    return result.upper()

def short_authors(authors):
    # Split the string by semicolons
    author_list = [author.strip() for author in authors.split(';')]
    
    # Handle edge case for institutions (assuming only one name)
    if len(author_list) == 1 and ' ' not in author_list[0]:
        return author_list[0]
    
    # Remove any potential middle names or initials (everything after the first comma)
    author_list = [author.split(',')[0] for author in author_list]
    
    # Check the number of authors and format appropriately
    if len(author_list) == 1:
        return author_list[0]
    elif len(author_list) == 2:
        return f"{author_list[0]} & {author_list[1]}"
    else:
        return f"{author_list[0]} et al."

def ai_select(xtt, question, cols, options, abstract_prompt):
    namematches = list(map(extract_alphanumeric_and_spaces, cols))
    allpages = {}
    for key, values in xtt.items():
        if extract_alphanumeric_and_spaces(key) in namematches:
            allpages.update(values)
    
    texts = '\n'.join([f"Page {num}: {text}" for num, text in allpages.items()])
    optiontexts = ' or '.join([f"[{option}]" for option in options + ['N/A']])

    prompt = f"""{abstract_prompt} Right now, I want to get an answer to the following question: '{question}' The following notes were extracted from pages from a paper that is potentially relevant to my answer:
===
{texts}
===

Specify the answer as one of the following: {optiontexts}. Put the answer in brackets, like this: [N/A]."""

    return interaction.get_action([{"role": "user", "content": prompt}], options + ['N/A'])

def ai_summary(xtt, question, cols, abstract_prompt):
    namematches = list(map(extract_alphanumeric_and_spaces, cols))
    allpages = {}
    for key, values in xtt.items():
        if extract_alphanumeric_and_spaces(key) in namematches:
            allpages.update(values)

    texts = '\n'.join([f"Page {num}: {text}" for num, text in allpages.items()])

    prompt = f"""{abstract_prompt} Right now, I want to get an answer to the following question: '{question}' The following notes were extracted from pages from a paper that is potentially relevant to my answer:
===
{texts}
===

Please provide a short, concise answer. Specify the synopsis in triple backticks, like this: ```Answer here.```."""

    return interaction.get_internaltext([{"role": "user", "content": prompt}], 3).strip()
