import os, csv, json
import pandas as pd

def add_response(response_file, doi, source, response):
    if not os.path.exists(response_file):
        with open(response_file, 'w') as fp:
            fp.write("DOI,Source,Response\n")
            
    with open(response_file, 'a') as fp:
        writer = csv.writer(fp)
        writer.writerow([doi, source, response.replace("\n", " ")])

def iterate_search(source, filter_config={}):
    for row in iterate_search_helper(source):
        if 'MinYear' in filter_config:
            if row['Year'] >= filter_config['MinYear']:
                yield row
        
def iterate_search_helper(source):
    if source[-4:] == '.csv':
        df = pd.read_csv(source)
        for index, row in df.iterrows():
            yield row
    elif 'savedrecs.xls' in source:
        df = pd.read_excel(source)
        df['Title'] = df['Article Title']
        df['Year'] = df['Publication Year']
        for index, row in df.iterrows():
            yield row
    elif 'savedrecsII.xls' in source:
        for i in range(1, 37):
            file_name = source.replace('savedrecsII.xls', f'savedrecs{i}.xls')
            df = pd.read_excel(file_name)
            df['Title'] = df['Article Title']
            df['Year'] = df['Publication Year']
            for index, row in df.iterrows():
                yield row

def get_knowns(response_file):
    if not os.path.exists(response_file):
        knowndoi_gemini = set()
        knowndoi_openai = set()
    else:
        responses = pd.read_csv(response_file)
        knowndoi_gemini = set(responses.DOI[responses.Source == 'gemini'])
        knowndoi_openai = set(responses.DOI[responses.Source == 'openai'])

        ## Add existing batch to knowndoi_openai
        if os.path.exists(response_file + "-batch.jsonl"):
            with open(response_file + "-batch.jsonl", 'r') as fp:
                for line in fp:
                    query = json.loads(line.strip())
                    knowndoi_openai.add(query['custom_id'])
                    
    return knowndoi_gemini, knowndoi_openai

def get_summaries(summary_file, dopass):
    dopass_suffix = f"-pass{dopass}" if dopass > 0 else ""
    dopass_summary_file = summary_file.replace('.csv', dopass_suffix + '.csv')
    
    if os.path.exists(dopass_summary_file):
        done = pd.read_csv(dopass_summary_file)

        # done = done.loc[:, ~done.columns.str.startswith('Unnamed')]
        # done = done.drop_duplicates(['DOI'])

        knowndoi = list(map(str, done.DOI))
    else:
        done = None
        knowndoi = []

    return done, knowndoi

def determine_passfail(outcomes):
    # Convert outcomes to a list and make it a set for easy checks
    outcomes_set = set(outcomes)
    
    if 'Passed' in outcomes_set and 'Failed' not in outcomes_set:
        return 'Passed'
    if 'Failed' in outcomes_set and 'Passed' not in outcomes_set:
        return 'Failed'
    if 'Passed' in outcomes_set and 'Failed' in outcomes_set:
        return 'Ambiguous'
    
    # Calculate modal outcome if possible
    value_counts = outcomes.value_counts()

    if value_counts.iloc[0] > (value_counts.iloc[1] if len(value_counts) > 1 else 0):
        return value_counts.index[0]
    
    # If no modal, default to Unknown
    return 'Unknown'
