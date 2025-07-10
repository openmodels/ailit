import re
import copy
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
        matches = re.findall(r'\[([A-Za-z0-9./ ()]+)\]', response, re.DOTALL)
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

def get_internaltext(chat, nattempts):
    pattern = r'```(.*?)```'
    
    for attempt in range(nattempts):
        response = aiengine.chat_response(chat)
        matches = re.findall(pattern, response, re.DOTALL)
        if len(matches) == 0:
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
