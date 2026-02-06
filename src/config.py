from lib import commands, checks

abstract_count = 10000
openai_config = 'skip' #'batch'
gemini_config = 'fast'

searches = ["/Users/admin/Library/CloudStorage/GoogleDrive-jrising@udel.edu/My Drive/Research/COP30 Ada/AI Review/scopus.csv",
            "/Users/admin/Library/CloudStorage/GoogleDrive-jrising@udel.edu/My Drive/Research/COP30 Ada/AI Review/savedrecsII.xls"]
response_file = "../responses.csv"
verdict_file = "../verdicts.csv"

abstract_prompt = "I am performing a review of direct climate impacts for the U.S. National Climate Assessment."
exclude_codes = {'XC': "Not related to climate impacts",
                 'XV': "Not valued in economic terms",
                 'XU': "No United States specific information",
                 'XA': "No new analysis (using previously-published work)",
                 'XO': "Excluded for another reason (please specify)"}
include_codes = {'RO': "Reports observed direct impacts (e.g., infrastructure damage, worker injuries, crop loss, human health, ecosystems)",
                 'RP': "Reports projected direct impacts (e.g., in 2050)"}

filter_config = {'MinYear': 2022}

## Question
questionsource = verdict_file.replace(".csv", "-further.csv")
singlequestion = "Based on this information, does this paper describe outcomes that are relevant to a chapter on economic impacts of climate change? This includes outcomes that are socioeconomically relevant, such as health impacts, and papers that include economic valuations, such as valued ecosystem service loss. However, other chapters will cover non-economic topics, such as temperature changes. I am particularly interested in filling out content for the Economics chapter."
question_file = "../question.csv"

## Find PDFs
priority_limit = 8
pdfs_dir = "../pdfs"
finder_count = 100
refresh_days = 60

## Extract data from PDFs
extract_dir = "../extract"
collate_count = 100
column_defs_collate = {
    'Evaluation overview': "Does this provide an overview of the outcome being evaluated (e.g., mortality, productivity loss)?",
    'Drivers of Risk': "What shocks or changes are impacting the outcomes (e.g., summer temperatures, floods)?",
    'Quantitative material': "Is there quantitative information produced by the analysis on this page (e.g., percent changes)?",
    'Methodology': "How is the analysis performed and when are its results applicable?",
    'Highlights': "What are the most important outcomes of the analysis?",
    'More Notes': "Do you have any other notes?"}

## Summarized line for PDF
summary_count = 100
summary_file = "../summary.csv"
column_defs_summary = {'All': {
    'Author(s)': lambda row, xtt: commands.short_authors(row['Authors']),
    'Year': lambda row, xtt: row['Year'],
    'Paper Title': lambda row, xtt: row['Title'],
    'Link to paper': "LINK",
    'Paper ID': lambda row, xtt: row['DOI'],
    'Reviewer': "AI",
    'Status': "STATUS",
    'Outcome(s) of Interest': "BRIEF2",
    'Drivers of Risk': "BRIEF2",
    'Category': lambda row, xtt: commands.ai_select2(row, xtt, "Please classify this paper as relevant to one of the following categories? If more than one match, choose the most appropriate.", ['Abstract', 'Evaluation overview'], ['Agriculture', 'Climate Amenities', 'Climate Hazards (Flooding, Storms, etc.)', 'Ecosystems', 'Energy', 'Fisheries', 'Forestry', 'Fresh-Water', 'Health > Climate-Air Pollution Interactions', 'Health > Diarrheal', 'Health > Heat and Cold (Cardiovascular, Respiratory, etc.)', 'Health > Vectore Borne Disease', 'Health > Wildfire Smoke', 'Health > Other', 'Indigenous Communities', 'Island Regions', 'Productivity > Capital Productivity and Depreciation', 'Productivity > Labour Productivity', 'Productivity > TFP', 'Recreation / Tourism', 'Sea-level Rise / Coastal', 'Tipping points / Feedback Effects', 'Total', 'Transportation', 'Other'], abstract_prompt),
    'Approach': lambda row, xtt: commands.ai_select(xtt, "What kind of modeling or analysis approach was used in the analysis?", ['Methodology'], ['Econometric', 'Macro-model', 'Stylised', 'Other'], abstract_prompt),
    'Methodology': "SUMMARIZE2",
    'Highlights': "SUMMARIZE2",
    'More Notes': "SUMMARIZE2",
    'Hazard definition': lambda row, xtt: commands.ai_select(xtt, "What kind of hazards were analyzed in the paper?", ['Methodology'], ['Acute shocks', 'Chronic trends', 'Stylised changes', 'N/A'], abstract_prompt),
    'Impact persistence': lambda row, xtt: commands.ai_select(xtt, "To what degree is persistence in impacts considered?", ['Methodology'], ['None', 'Permanent', 'Adaptive'], abstract_prompt),
    'Space disaggregation': lambda row, xtt: commands.ai_select(xtt, "What level of disaggregation was used in the analysis?", ['Methodology'], ['Global', 'Regional', 'Local'], abstract_prompt),
    'Impact interactions': lambda row, xtt: commands.ai_select(xtt, "Were interactions between impacts considered in the analysis?", ['Methodology'], ['None', 'Sequential Interactions', 'Spatial Interactions', 'Sectoral Interactions'], abstract_prompt),
    'Economic dynamics': lambda row, xtt: commands.ai_select(xtt, "Was the dynamic nature of the economy considered in the analysis?", ['Methodology'], ['Static', 'Transitional (accounting for changes over time)', 'Adaptive (reflecting shifts in economic behavior in response to impacts)'], abstract_prompt),
    'Climate features': lambda row, xtt: commands.ai_select(xtt, "Were tipping points or other notable climate complexities included?", ['Methodology'], ['Tipping Points', 'Other'], abstract_prompt),
    'Adaptation considered': lambda row, xtt: commands.ai_summary(xtt, "How and to what extent is adaptation considered? Just provide brief notes, avoiding statements that start with redundant text like 'Adaptation is considered...'.", ['Methodology'], abstract_prompt)
}}

extract_count = 100
extract_fromcollate = 'Quantitative material'
extract_fromsummary = 'All'
extract_request = "Please summarize and extract any quantitative results that are either observed direct impacts (present/historical) or projected direct impacts (e.g., in 2050)."
column_defs_extract = {'All': {
    'Outcome': ["What is the outcome that is affected by climate change? Just provide a single term. If reductions in the outcome are described, do not include 'losses' or similar in the outcome name, since we will report these as negative.", checks.very_short],
    'Region': ["What specific region was considered, or was the whole country? Just provide the region name.", checks.very_short],
    'Scenario': ["Under what socioeconomic or climate scenario were the outcomes analyzed? Just provide a technical scenario name.", checks.very_short],
    'Year': ["Under what future or past year is the outcome evaluated? Just specify a single year.", checks.year],
    'Relative to': ["What comparison scenario are quantitative outcomes reported relative to? For example, specify a baseline year or if it is relative to no climate change, write 'No CC'.", checks.very_short],
    'Units': ["What are the units of the quantitative outcome? For example, if this is a change in the dependent variable relative to a certain shock, give the ratio of the dependent divided by the independent units (e.g., deaths / degree C).", checks.very_short],
    'Value': ["What is the value of the quantitative outcome? Specify this as positive if the affected outcome is greater than the comparison scenario, so (for example) losses in the outcome will be negative.", checks.numeric],
    'SD': ["What is the standard error or standard deviation of the result? Specify a number or NA.", checks.numeric_or_na],
    'Low Quantile': ["If a lower quantile value is specified, what is the percent value of that quantile, or NA.", checks.percent_or_na],
    'Low Value': ["If a lower quantile value is specified, what is the value at that quantile, or NA.", checks.numeric_or_na],
    'High Quantile': ["If a lower quantile value is specified, what is the percent value of that quantile, or NA.", checks.percent_or_na],
    'High Value': ["If a lower quantile value is specified, what is the value at that quantile, or NA.", checks.numeric_or_na],
    'Result Source': ["Where is this quantitative result reported in the paper? Include the page number.", checks.short],
    'More Notes': ["Do you have any other notes?"]
}}

## Multiple passes and reconciliation
dopass_count = 3
merge_count = 10
merge_suffix = {'All': '-merged'} #{'Macroeconomic/Fiscal': '-macro', 'Adaptation': '-adapt'}
merge_extract_file = "../extract.csv"
merge_columns = {'All': {
    'Author(s)': "Use an abbreviated format, like 'Last Name et al.' or 'First & Second'.",
    'Year': "Publication year.",
    'Paper Title': None,
    'Link to paper': None,
    'Paper ID': None,
    'Reviewer': None,
    'Status': None,
    'Outcome(s) of Interest': "What is the outcome that is affected by climate change (e.g., mortality, productivity loss)?",
    'Drivers of Risk': "What shocks or changes are impacting the outcomes (e.g., summer temperatures, floods)?",
    'Category': "Which of the following categories is this paper relevant to? 'Agriculture', 'Climate Amenities', 'Climate Hazards (Flooding, Storms, etc.)', 'Ecosystems', 'Energy', 'Fisheries', 'Forestry', 'Fresh-Water', 'Health > Climate-Air Pollution Interactions', 'Health > Diarrheal', 'Health > Heat and Cold (Cardiovascular, Respiratory, etc.)', 'Health > Vectore Borne Disease', 'Health > Wildfire Smoke', 'Health > Other', 'Indigenous Communities', 'Island Regions', 'Productivity > Capital Productivity and Depreciation', 'Productivity > Labour Productivity', 'Productivity > TFP', 'Recreation / Tourism', 'Sea-level Rise / Coastal', 'Tipping points / Feedback Effects', 'Total', 'Transportation', or 'Other'. If more than one match, choose the most appropriate.",
    'Approach': "What kind of modeling or analysis approach was used in the analysis? Choose one of 'Econometric', 'Macro-model', 'Stylised', or 'N/A'.",
    'Methodology': "How is the analysis performed and when are its results applicable?",
    'Hazard definition': "What kind of hazards were analyzed in the paper? Choose one of 'Acute shocks', 'Chronic trends', 'Stylised changes', or 'N/A'.",
    'Impact persistence': "To what degree is persistence in impacts condidered? Choose one of 'None', 'Permanent', or 'Adaptive'.",
    'Space disaggregation': "What level of disaggregation was used in the analysis? Choose one of 'Global', 'Regional', or 'Local'.",
    'Impact interactions': "Where interactions between impacts considered in the analysis? Choose one of 'None', 'Sequential Interactions', 'Spatial Interactions', or 'Sectoral Interactions'.",
    'Economic dynamics': "Was the dynamic nature of the economy considered in the analysis? Choose one of 'Static', 'Transitional (accounting for changes over time)', or 'Adaptive (reflecting shifts in economic behavior in response to impacts)'.",
    'Climate features': "Were tipping points or other notable climate complexities included? Choose one of 'Tipping Points', 'Other', or 'None'.",
    'Adaptation considered': "How and to what extent is adaptation considered? Just provide brief notes, avoiding statements that start with redundant text like 'Adaptation is considered...'",
    'Highlights': "What are the most important outcomes of the analysis?",
    'More Notes': "Do you have any other notes?"}}
