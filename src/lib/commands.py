import re
from lib import interaction

def extract_alphanumeric_and_spaces(s):
    # Using regex to find all alphanumeric characters and spaces
    result = re.sub(r'[^A-Za-z0-9\s]', '', s)
    # Convert to uppercase
    return result.upper()

def get_colmaterial(xtt, cols):
    namematches = list(map(extract_alphanumeric_and_spaces, cols))
    allpages = {}
    for key, values in xtt.items():
        if extract_alphanumeric_and_spaces(key) in namematches:
            for num, text in values.items():
                if num in allpages:
                    allpages[num] = allpages[num] + "; " + text
                else:
                    allpages[num] = text
    sourcematerials = {}
    for num, text in allpages.items():
        sourcematerials[num] = xtt['sourcematerial'][num]

    return allpages, sourcematerials

def short_authors(authors):
    if not isinstance(authors, str):
        return "NA", None
    
    # Split the string by semicolons
    author_list = [author.strip() for author in authors.split(';')]
    
    # Handle edge case for institutions (assuming only one name)
    if len(author_list) == 1 and ' ' not in author_list[0]:
        return author_list[0], None
    
    # Remove any potential middle names or initials (everything after the first comma)
    author_list = [author.split(',')[0] for author in author_list]
    
    # Check the number of authors and format appropriately
    if len(author_list) == 1:
        return author_list[0], None
    elif len(author_list) == 2:
        return f"{author_list[0]} & {author_list[1]}", None
    else:
        return f"{author_list[0]} et al.", None

def ai_select(row, xtt, question, cols, options, abstract_prompt):
    allpages, sourcematerials = get_colmaterial(xtt, cols)

    optiontexts = ' or '.join([f"[{option}]" for option in options + ['N/A']])

    if len(allpages) > 0:
        texts = '\n'.join([f"Page {num}: {text}" for num, text in allpages.items()])
        sourcematerials = '\n'.join([f"Page {num}: {text}" for num, text in sourcematerials.items()])

        prompt = f"""{abstract_prompt} I am currently reviewing a paper.

Here is an abstract of the paper: {row['Abstract']}

Right now, I want to get an answer to the following question: '{question}' The following notes were extracted from pages from a paper that is potentially relevant to my answer:
===
{texts}
===
For context, here is extracted source material from those pages:
===
{sourcematerials}
===

Specify the answer as one of the following: {optiontexts}. Put the answer in brackets, like this: [N/A]."""
    else:
        prompt = f"""{abstract_prompt}  I am currently reviewing a paper.

Right now, I want to get an answer to the following question: '{question}' I only have the abstract to provide material on this. Here it is:

{row['Abstract']}

Specify the answer as one of the following: {optiontexts}. Put the answer in brackets, like this: [N/A]."""
        
    chat = [{"role": "user", "content": prompt}]
    response = interaction.get_action(chat, options + ['N/A'])
    
    sourcematerial = interaction.get_sourcematerial(chat, "```" + response + "```", 3)
    return response, sourcematerial

def ai_summary(row, xtt, question, cols, abstract_prompt):
    allpages, sourcematerials = get_colmaterial(xtt, cols)

    if len(allpages) > 0:
        texts = '\n'.join([f"Page {num}: {text}" for num, text in allpages.items()])
        sourcematerials = '\n'.join([f"Page {num}: {text}" for num, text in sourcematerials.items()])

        prompt = f"""{abstract_prompt} I am currently reviewing a paper.

Here is an abstract of the paper: {row['Abstract']}

Right now, I want to get an answer to the following question: '{question}' The following notes were extracted from pages from a paper that is potentially relevant to my answer:
===
{texts}
===
For context, here is extracted source material from those pages:
===
{sourcematerials}
===

Please provide a short, concise answer. Specify the synopsis in triple backticks, like this: ```Answer here.```."""
    else:
        prompt = f"""{abstract_prompt} I am currently reviewing a paper.

Right now, I want to get an answer to the following question: '{question}' I only have the abstract to provide material on this. Here it is:

{row['Abstract']}

Please provide a short, concise answer. Specify the synopsis in triple backticks, like this: ```Answer here.```."""
        
    chat = [{"role": "user", "content": prompt}]
    response = interaction.get_internaltext(chat, 3).strip()

    sourcematerial = interaction.get_sourcematerial(chat, "```" + response + "```", 3)
    return response, sourcematerial
