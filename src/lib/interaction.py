import re, csv, yaml
import copy
from io import StringIO
from chatwrap import selector, gemini, openaigpt

aiengine = selector.BayesSelector([openaigpt, gemini], debug=True)
aiengine_saved = aiengine

def chat_push(chat, role, content):
    chat2 = copy.copy(chat)
    chat2.append({"role": role, "content": content})
    return chat2

def get_action(chat, allowed):
    for attempt in range(3):
        response = aiengine.chat_response(chat)
        matches = re.findall(r'\[([A-Za-z0-9./ ()<>,-]+)\]', response, re.DOTALL)
        if len(matches) == 0:
            chat = chat_push(chat_push(chat, 'assistant', response), 'user', "Sorry, I could not find an action choice. Can you try again?")
            aiengine.failure()
            continue
        if len(matches) > 1:
            chat = chat_push(chat_push(chat, 'assistant', response), 'user', "Sorry, I see multiple actions within this response. Can you try again?")
            aiengine.failure()
            continue
        if matches[0] not in allowed:
            chat = chat_push(chat_push(chat, 'assistant', response), 'user', "Sorry, this action does not appear to be one of the allowed ones. Can you try again?")
            aiengine.failure()
            continue
        
        aiengine.success()
        return matches[0]

def get_stringcommand(chat, nattempts):
    pattern = r'```\s*(\w+)\("([^"\\]*(?:\\.[^"\\]*)*)"\)'
    
    for attempt in range(nattempts):
        response = aiengine.chat_response(chat)
        match = re.search(pattern, response)
        if match:
            aiengine.success()
            return match.group(1), match.group(2)
            
        chat = chat_push(chat_push(chat, 'assistant', response), 'user', 'Sorry, I could not find a valid ```command("text")``` block in this reponse. Can you try again?')
        aiengine.failure()
    
    aiengine.failure()
    return None, None

def get_internaltext(chat, nattempts, max_tokens=None, fallback_check=None):
    pattern = r'```(.*?)```'
    
    for attempt in range(nattempts):
        response = aiengine.chat_response(chat, max_tokens=max_tokens)
        matches = re.findall(pattern, response, re.DOTALL)
        if len(matches) == 0:
            if fallback_check is not None:
                if fallback_check(response) is None:
                    aiengine.success()
                    return response
            if max_tokens is not None and len(response) > max_tokens * 0.9:
                chat = chat_push(chat_push(chat, 'assistant', response), 'user', "Sorry, I could not find a ```text``` block in this reponse. It may have been cut off, because there's a limit on the response length. Can you try again?")
            else:
                chat = chat_push(chat_push(chat, 'assistant', response), 'user', "Sorry, I could not find a ```text``` block in this reponse. Can you try again?")
            aiengine.failure()
            continue
        if len(matches) > 1:
            chat = chat_push(chat_push(chat, 'assistant', response), 'user', "Sorry, I see multiple ```text``` blocks within this response. Can you try again?")
            aiengine.failure()
            continue
        
        aiengine.success()
        return matches[0]
    
    aiengine.failure()
    return None

def find_csvheader(response):
    csvfp = StringIO(response)
    reader = csv.reader(csvfp)
    header = []
    while not header:
        try:
            header = next(reader)
            if len(header) == 0:
                continue
            if len(header) == 1 and header[0] == 'csv':
                continue
        except:
            return None, None

    return header, reader

def make_csvcheck(required_header):
    def csvcheck(response):
        header, reader = find_csvheader(response)
        if not header:
            return "Sorry, I did not find a header. Can you try again?"
            
        if header != list(required_header):
            strheader = '"' + "\",\"".join(list(required_header)) + '"'
            return f"Sorry, the header did not match. It should read:\n{strheader}\nCan you try again?"

        return None

    return csvcheck

def get_csvtext(chat, nattempts, required_header, max_tokens=None):
    csvcheck = make_csvcheck(required_header)
    for attempts in range(nattempts):
        response = get_internaltext(chat, nattempts, max_tokens=4096*2, fallback_check=csvcheck)

        message = csvcheck(response)
        if message is not None:
            chat = chat_push(chat_push(chat, 'assistant', f"```{response}```"), 'user', message)
            continue

        header, reader = find_csvheader(response)
        return header, reader, response
    
    return None, None, response

def extract_yaml_dict(text):
    # Regex to match dictionary entries allowing for quoted or unquoted keys and values
    yaml_regex = r'^\s*-?\s*(\'[a-zA-Z0-9_/?() ]+\'|"[a-zA-Z0-9_/?() ]+"|[a-zA-Z0-9_/?() ]+)\s*:\s*("[^"\n]*"|\'[^\n]*\'|[^"\n]+)\s*$'
    
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
            return f"Error parsing YAML: {exc}"
    else:
        return "No YAML dictionary found."

def get_csvtext_validated(chat, nattempts, instructs):
    for attempts in range(nattempts):
        header, reader, response = get_csvtext(chat, nattempts, list(instructs.keys()), max_tokens=4096*2)
        if not header:
            return [] # Couldn't get through this step
        
        validrows = []
        errors = {} # rownum: [errors]
        rownum = 0
        for row in reader:
            rownum += 1
            for ii in range(len(header)):
                for check in instructs[header[ii]][1:]:
                    if len(row) <= ii:
                        if rownum not in errors:
                            errors[rownum] = []
                        errors[rownum].append(f"column {header[ii]}: entry missing")
                        continue
                    isinvalid = check(row[ii])
                    if isinvalid:
                        if rownum not in errors:
                            errors[rownum] = []
                        errors[rownum].append(f"column {header[ii]}: {isinvalid}")

            if len(row) < len(header):
                if rownum not in errors:
                    errors[rownum] = []
                errors[rownum].append(f"not all columns provided")
                
            if rownum not in errors:
                validrows.append({header[ii]: row[ii] for ii in range(len(header))})

        if errors:
            # Try to simplify
            allrows = set()
            if len(errors) == rownum and rownum > 2:
                candidates = set(errors[1])
                for rowii in range(2, rownum + 1):
                    candidates = candidates.intersection(set(errors[rowii]))
                if len(candidates) > 0:
                    for rowii in range(1, rownum + 1):
                        errors[rowii] = set(errors[rowii]) - candidates
                    allrows = candidates
            
            if allrows:
                errorstr = "All rows:\n - " + "\n - ".join(allrows) + "\n"
            else:
                errorstr = ""
            for rowii in errors:
                if errors[rowii]:
                    errorstr += f"Row {rowii}:\n - " + "\n - ".join(errors[rowii]) + "\n"
            chat = chat_push(chat_push(chat, 'assistant', f"```{response}```"), 'user', f"I got the following errors:\n{errorstr}\nCan you try again?")
            continue

        return validrows

    return [] # Failed
