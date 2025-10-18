from lib import commands, checks

count_perrun = 25
openai_config = 'slow' #'batch'
gemini_config = 'slow' #'fast'

searches = ["../test/macroecono.xlsx"]
response_file = "../test/responses.csv"
verdict_file = "../test/verdicts.csv"

abstract_prompt = "I am performing a meta-analysis of econometric models of temperature on economic growth. These papers use regression-based techniques to understand how variation in weather results in variation in GDP growth rates. I am only interested in papers that do this globally, with at least national-level resolution."
exclude_codes = {'XG': "Not GDP growth (studying a different dependent variable)",
                 'XE': "Not econometric (using non-causal or non-statistical methods)",
                 'XW': "Not global (region-specific)",
                 'XN': "No new empirics (using previously-published work)"}
include_codes = {'PG': "Plausibly includes global econometric results on GDP growth",
                 'PP': "Plausibly includes estimates of the persistence of GDP impacts"}

## Question
questionsource = verdict_file.replace(".csv", "-further.csv")
singlequestion = "Based on this information, does this paper describe outcomes driven by climate change (that is, all the effects that come from increased greenhouse gas concentrations, such as increased temperatures and other weather changes), as opposed to the effects of climate policy? I do *not* want to consider reductions in losses that are driven by mitigation policy alone."
question_file = "../test/question.csv"

## Find PDFs
priority_limit = 8
pdfs_dir = "../pdfs"
finder_count = 25

## Extract data from PDFs
extract_dir = "../test/extract"
collate_count = 25
column_defs_collate = {'Innovation': "What is the key innovation or academic contribution for this paper?"
                       'Econometric coefficients': "Are there econometric coefficients reported on this page?",
                       'Methodology': "How is the analysis performed and when are its results applicable?",
                       'More Notes': "Do you have any other notes?"}

## Summarized line for PDF
summary_count = 25
summary_file = "../test/summary.csv"
column_defs_summary = {'All': {
    'Author(s)': lambda row, xtt: commands.short_authors(row['Authors']),
    'Year': lambda row, xtt: row['Year'],
    'Paper Title': lambda row, xtt: row['Title'],
    'Link to paper': "LINK",
    'Paper ID': lambda row, xtt: row['DOI'],
    'Reviewer': "AI",
    'Status': "STATUS",
    'NEXT': lambda row, xtt: commands.ai_select(xtt, "Does this paper produce new econometric results describing GDP growth rates or the extent of persistence?", ['Methodology'], ['', 'Growth', 'Persistence', 'Both'], abstract_prompt)},
                       'Any': {
                           'Innovation': 'BRIEF',
                           'Methodology': "SUMMARIZE",
                           'More Notes': "SUMMARIZE",
                           'Concerns': lambda row, xtt: commands.ai_summary(xtt, "Are there any concerns in the robustness or credibility of this work?", ['Methodology', 'More Notes'], abstract_prompt)},
                           'Econometric Method': lambda row, xtt: commands.ai_select(xtt, "Was standard fixed-effects econometric used, or an alternative method?", ['Methodology'], ['Econometrics', 'Alternative', 'N/A'], abstract_prompt),
                       'Growth': {
                           'Applicability': "Growth",
                           'Adaptation considered': lambda row, xtt: commands.ai_summary(xtt, "How and to what extent is adaptation considered? Just provide brief notes, avoiding statements that start 'Adaptation is considered...'.", ['Methodology'], abstract_prompt)
                       },
                       'Persistence': {
                           'Applicability': "Persistence",
                       },
                       'Adaptation': {
                           'Applicability': "Growth & Persistence",
                           'Adaptation considered': lambda row, xtt: commands.ai_summary(xtt, "How and to what extent is adaptation considered? Just provide brief notes, avoiding statements that start 'Adaptation is considered...'.", ['Methodology'], abstract_prompt)
                       }}

extract_count = 25
extract_fromcollate = 'Econometric coefficients'
extract_fromsummary = 'Applicability'
extract_request = {'Growth': "Please summarize and extract the coefficients that describe the temperature-to-growth relationship.",
                   'Persistence': "Please summarize and extract the quantitative description of persistence.",
                   'Growth & Persitence': "Please summarize and extract both coefficients that describe the temperature-to-growth relationship and the quantitative description of persistence."}
column_defs_extract = {'Growth': {
    'Variable': ["What is the specific temperature variable for this coefficient?", checks.very_short],
    'Value': ["What is the value of the coefficient?", checks.numeric],
    'SE': ["What is the standard error of the coefficient? Specify a number or NA.", checks.numeric_or_na],
    'Result Source': ["Where is this coefficient reported in the paper? Include the page number and table if applicable.", checks.short],
    'More Notes': ["Do you have any other notes?"]
},
                       'Persistence': {
                           'Definition': ["How is persistence quantified?", checks.very_short],
                           'Units': ["What are the units of the persistence estimate?", checks.very_short],
                           'Value': ["What is the value of the persistence estimate?", checks.numeric],
                           'SE': ["What is the standard error of the persistence estimate? Specify a number or NA.", checks.numeric_or_na],
                           'Result Source': ["Where is this result reported in the paper? Include the page number and table if applicable.", checks.short],
                           'More Notes': ["Do you have any other notes?"]
                       },
                       'Growth & Persistence': {
                           'Variable': ["For temperature coefficients, what is the specific temperature variable for this coefficient?", checks.very_short],
                           'Definition': ["For persistence estimates, how is persistence quantified?", checks.very_short],
                           'Units': ["For persistence estimates, what are the units of the persistence estimate?", checks.very_short],
                           'Value': ["What is the value of the coefficient or persistence estimate?", checks.numeric],
                           'SE': ["What is the standard error of the coefficient or persistence estimate? Specify a number or NA.", checks.numeric_or_na],
                           'Result Source': ["Where is this result reported in the paper? Include the page number and table if applicable.", checks.short],
                           'More Notes': ["Do you have any other notes?"]
                       }}

## Multiple passes and reconciliation
dopass_count = 3
merge_count = 25
merge_suffix = {'Growth': '',
                'Persistence': '',
                'Growth & Persistence': ''}
merge_extract_file = "../test/extract.csv"
merge_columns = {'Growth': {
    'Author(s)': "Use an abbreviated format, like 'Last Name et al.' or 'First & Second'.",
    'Year': "Publication year.",
    'Paper Title': None,
    'Link to paper': None,
    'Paper ID': None,
    'Reviewer': None,
    'Status': None,
    'Innovation': "What is the key innovation or academic contribution for this paper?",
    'Methodology': "How is the analysis performed and when are its results applicable?",
    'Concerns': "Are there any concerns in the robustness or credibility of this work?",
    'Econometric Method': "Was standard fixed-effects econometric used, or an alternative method? Choose one of 'Econometrics', 'Alternative', or 'N/A'.",
    'Adaptation considered': "How and to what extent is adaptation considered? Just provide brief notes, avoiding statements that start 'Adaptation is considered...'.",
    'More Notes': "Do you have any other notes?"},
                 'Persistence': {
                     'Author(s)': "Use an abbreviated format, like 'Last Name et al.' or 'First & Second'.",
                     'Year': "Publication year.",
                     'Paper Title': None,
                     'Link to paper': None,
                     'Paper ID': None,
                     'Reviewer': None,
                     'Status': None,
                     'Innovation': "What is the key innovation or academic contribution for this paper?",
                     'Methodology': "How is the analysis performed and when are its results applicable?",
                     'Concerns': "Are there any concerns in the robustness or credibility of this work?",
                     'Econometric Method': "Was standard fixed-effects econometric used, or an alternative method? Choose one of 'Econometrics', 'Alternative', or 'N/A'.",
                     'More Notes': "Do you have any other notes?"},
                 'Growth & Persistence': {
                     'Author(s)': "Use an abbreviated format, like 'Last Name et al.' or 'First & Second'.",
                     'Year': "Publication year.",
                     'Paper Title': None,
                     'Link to paper': None,
                     'Paper ID': None,
                     'Reviewer': None,
                     'Status': None,
                     'Innovation': "What is the key innovation or academic contribution for this paper?",
                     'Methodology': "How is the analysis performed and when are its results applicable?",
                     'Concerns': "Are there any concerns in the robustness or credibility of this work?",
                     'Econometric Method': "Was standard fixed-effects econometric used, or an alternative method? Choose one of 'Econometrics', 'Alternative', or 'N/A'.",
                     'Adaptation considered': "How and to what extent is adaptation considered? Just provide brief notes, avoiding statements that start 'Adaptation is considered...'.",
                     'More Notes': "Do you have any other notes?"
                 }}
