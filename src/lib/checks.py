import re

def very_short(response):
    if len(response) > 30:
        return "Please provide a very short response less than 30 characters."
    return None

def short(response):
    if len(response) > 160:
        return "Please provide a short response less than 160 characters."
    return None

def year(response):
    match = re.match(r"^\d{4}$", response)
    if not match:
        return "Please specify a year."
    year = int(match.string)
    if year < 1 or year > 3000:
        return "Please specify a year between 1 and 3000."
    return None
    
def numeric(response):
    try:
        val = float(response)
        return None
    except:
        return "Please specify a simple numeric value."

def numeric_or_na(response):
    if response == 'NA':
        return None
    return numeric(response)

def percent_or_na(response):
    if response == 'NA':
        return None
    if response[-1] != '%':
        return "Please designate a percent, including a percent sign."
    return numeric(response)

def oneof(options):
    def checker(response):
        if response not in options:
            return "Please sepcify one of the valid responses: " + ", ".join(options)
        return None
    return checker
