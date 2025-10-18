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
include_codes = {'PL': "Plausibly appropriate: Unlikely",
                 'PM': "Plausibly appropriate: Somewhat likely",
                 'PH': "Plausibly appropriate: Very likely"}

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
column_defs_collate = {'Quantitative material': "Is there quantitative information on the outcomes of interest on this page?",
                       'Methodology': "How is the analysis performed and when are its results applicable?",
                       'Highlights': "What are the most important outcomes of the analysis?",
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
    'NEXT': lambda row, xtt: commands.ai_select(xtt, "Does this paper produce new econometric results describing GDP growth rates or the extent of persistence?", ['Quantitative material', 'Methodology'], ['Macroeconomic', 'Fiscal', 'Adaptation'], abstract_prompt)},
                       'Any': {
                           'Country(ies)': lambda row, xtt: commands.ai_summary(xtt, "What specific country or group of countries was considered? Just provide the country names or group.", ['Methodology'], abstract_prompt),
                           'Outcome(s) of Interest': "BRIEF",
                           'Drivers of Risk': "BRIEF",
                           'Scenario(s)': lambda row, xtt: commands.ai_summary(xtt, "Under what socioeconomic or climate scenarios were the outcomes analyzed? Just provide technical scenario names.", ['Methodology'], abstract_prompt),
                           'Methodology': "SUMMARIZE",
                           'Highlights': "SUMMARIZE",
                           'More Notes': "SUMMARIZE"},
                       'Macroeconomic': { # Duplicated in "Fiscal"
                           'Applicability': "Macroeconomic/Fiscal",
                           'Calibration Approach': lambda row, xtt: commands.ai_select(xtt, "What calibration or modeling approach was used in the analysis?", ['Methodology'], ['Econometric', 'Macro-model', 'Stylised', 'N/A'], abstract_prompt),
                           'Hazard definition': lambda row, xtt: commands.ai_select(xtt, "What kind of hazards were analyzed in the paper?", ['Methodology'], ['Acute shocks', 'Chronic trends', 'Stylised changes', 'N/A'], abstract_prompt),
                           'Impact persistence': lambda row, xtt: commands.ai_select(xtt, "To what degree is persistence in impacts considered?", ['Methodology'], ['None', 'Permanent', 'Adaptive'], abstract_prompt),
                           'Space disaggregation': lambda row, xtt: commands.ai_select(xtt, "What level of disaggregation was used in the analysis?", ['Methodology'], ['Global', 'Regional', 'Local'], abstract_prompt),
                           'Impact interactions': lambda row, xtt: commands.ai_select(xtt, "Were interactions between impacts considered in the analysis?", ['Methodology'], ['None', 'Sequential Interactions', 'Spatial Interactions', 'Sectoral Interactions'], abstract_prompt),
                           'Economic dynamics': lambda row, xtt: commands.ai_select(xtt, "Was the dynamic nature of the economy considered in the analysis?", ['Methodology'], ['Static', 'Transitional (accounting for changes over time)', 'Adaptive (reflecting shifts in economic behavior in response to impacts)'], abstract_prompt),
                           'Climate features': lambda row, xtt: commands.ai_select(xtt, "Were tipping points or other notable climate complexities included?", ['Methodology'], ['Tipping Points', 'Other'], abstract_prompt),
                           'Adaptation considered': lambda row, xtt: commands.ai_summary(xtt, "How and to what extent is adaptation considered? Just provide brief notes, avoiding statements that start 'Adaptation is considered...'.", ['Methodology'], abstract_prompt)
                       },
                       'Fiscal': { # Duplicated in "Macroeconomic"
                           'Applicability': "Macroeconomic/Fiscal",
                           'Calibration Approach': lambda row, xtt: commands.ai_select(xtt, "What calibration or modeling approach was used in the analysis?", ['Methodology'], ['Econometric', 'Macro-model', 'Stylised', 'N/A'], abstract_prompt),
                           'Hazard definition': lambda row, xtt: commands.ai_select(xtt, "What kind of hazards were analyzed in the paper?", ['Methodology'], ['Acute shocks', 'Chronic trends', 'Stylised changes', 'N/A'], abstract_prompt),
                           'Impact persistence': lambda row, xtt: commands.ai_select(xtt, "To what degree is persistence in impacts considered?", ['Methodology'], ['None', 'Permanent', 'Adaptive'], abstract_prompt),
                           'Space disaggregation': lambda row, xtt: commands.ai_select(xtt, "What level of disaggregation was used in the analysis?", ['Methodology'], ['Global', 'Regional', 'Local'], abstract_prompt),
                           'Impact interactions': lambda row, xtt: commands.ai_select(xtt, "Were interactions between impacts considered in the analysis?", ['Methodology'], ['None', 'Sequential Interactions', 'Spatial Interactions', 'Sectoral Interactions'], abstract_prompt),
                           'Economic dynamics': lambda row, xtt: commands.ai_select(xtt, "Was the dynamic nature of the economy considered in the analysis?", ['Methodology'], ['Static', 'Transitional (accounting for changes over time)', 'Adaptive (reflecting shifts in economic behavior in response to impacts)'], abstract_prompt),
                           'Climate features': lambda row, xtt: commands.ai_select(xtt, "Were tipping points or other notable climate complexities included?", ['Methodology'], ['Tipping Points', 'Other', 'None'], abstract_prompt),
                           'Adaptation considered': lambda row, xtt: commands.ai_summary(xtt, "How and to what extent is adaptation considered? Just provide brief notes, avoiding statements that start 'Adaptation is considered...'.", ['Methodology'], abstract_prompt)
                       },
                       'Adaptation': {
                           'Applicability': "Adaptation",
                           'Impacted Sector': lambda row, xtt: commands.ai_summary(xtt, "Is there a specific sector of the economy that is impacted?", ['Methodology'], abstract_prompt),
                           'Benefits of Adaptation': lambda row, xtt: commands.ai_summary(xtt, "How are benefits of adaptation quantified?", ['Methodology'], abstract_prompt),
                           'Costs of Adaptation': lambda row, xtt: commands.ai_summary(xtt, "How are costs of adaptation quantified?", ['Methodology'], abstract_prompt),
                           'Ante/Post?': lambda row, xtt: commands.ai_summary(xtt, "Does the analysis rely on ex-ante modeling or ex-post observations?", ['Methodology'], abstract_prompt),
                           'Planning Process': lambda row, xtt: commands.ai_summary(xtt, "What is discussed about the adaptation planning/decision-making process?", ['Methodology'], abstract_prompt),
                           'Soft Options': lambda row, xtt: commands.ai_summary(xtt, "What is the benefit of \"soft options\" (e.g., informational and institutional interventions)?", ['Methodology'], abstract_prompt),
                           'Sufficiency Definition': lambda row, xtt: commands.ai_summary(xtt, "How do different papers understand sufficient adaptation levels (i.e., what does it mean to be well-adapted)?", ['Methodology'], abstract_prompt)
                       }}

extract_count = 100
extract_fromcollate = 'Quantitative material'
extract_fromsummary = 'Applicability'
extract_request = {'Macroeconomic/Fiscal': "Please summarize and extract any quantitative results that are either macroeconomic outcomes (GDP effects, productivity loss, interest, inflation, etc.) or fiscal outcomes (budget balance, borrowing costs, public expenditure or revenue, etc.) impacted by climate change.",
                   'Adaptation': "Please summarize and extract any quantitative results that are economic costs and/or benefits (or related measures like ROI, NPV) of national-scale adaptation to climate change."}
column_defs_extract = {'Macroeconomic/Fiscal': {
    'Outcome': ["What is the outcome that is affected by climate change? Just provide a single term. If reductions in the outcome are described, do not include 'losses' or similar in the outcome name, since we will report these as negative. ", checks.very_short],
    'Country(ies)': ["What specific country or group of countries was considered? Just provide the country names or group.", checks.very_short],
    'Scenario': ["Under what socioeconomic or climate scenario were the outcomes analyzed? Just provide a technical scenario name.", checks.very_short],
    'Year': ["Under what future or past year is the outcome evaluated? Just specify a single year.", checks.year],
    'Relative to': ["What comparison scenario are quantitative outcomes reported relative to? For example, specify a baseline year or if it is relative to no climate change, write 'No CC'.", checks.very_short],
    'Units': ["What are the units of the quantitative outcome?", checks.very_short],
    'Value': ["What is the value of the quantitative outcome? Specify this as positive if the affected outcome is greater than the comparison scenario, so (for example) losses in the outcome will be negative.", checks.numeric],
    'SD': ["What is the standard error or standard deviation of the result? Specify a number or NA.", checks.numeric_or_na],
    'Low Quantile': ["If a lower quantile value is specified, what is the percent value of that quantile, or NA.", checks.percent_or_na],
    'Low Value': ["If a lower quantile value is specified, what is the value at that quantile, or NA.", checks.numeric_or_na],
    'High Quantile': ["If a lower quantile value is specified, what is the percent value of that quantile, or NA.", checks.percent_or_na],
    'High Value': ["If a lower quantile value is specified, what is the value at that quantile, or NA.", checks.numeric_or_na],
    'Result Source': ["Where is this quantitative result reported in the paper? Include the page number.", checks.short],
    'More Notes': ["Do you have any other notes?"]
},
                       'Adaptation': {
                           'Impacted Sector': ["What economic sector or group is being impacted by climate change? Just provide a single term or All or NA.", checks.very_short],
                           'Solution': ["What type of solution is being evaluated? Just provide a single term or Any or NA.", checks.very_short],
                           'Country(ies)': ["What specific country or group of countries was considered? Just provide the country names or group.", checks.very_short],
                           'Scenario': ["Under what socioeconomic or climate scenario were the outcomes analyzed? Just provide a technical scenario name.", checks.very_short],
                           'Quantification': ["How are the effects of adaptation being quantified? Just provide a technical term.", checks.very_short],
                           'Expression': ["As a simple mathematical expression, what does the quantification express? Valid terms (common units in brackets) include AvoidedImpact [million USD / yr, % of GDP], MonetaryBenefits [million USD / yr, % of GDP], NonMonetaryBenefits [million USD / yr, % of GDP], BaselineImpact [million USD / yr, % of GDP], AdaptationCost [million USD / yr, % of GDP], CapExCost [million USD], OpExCost [million USD / yr], and functions like DiscountedSum() [million USD] and RateOfReturn() [%]", checks.short],
                           'Type of Value': ["What is being included in the costs or benefits? Specify 'Monetary' (cash flows), 'Fiscal' (government balances), 'Economic' (monetary and nonmonetary), 'Various' (not clearly distinguished), or 'N/A'.", checks.oneof(['Monetary', 'Fiscal', 'Economic', 'Various','N/A'])],
                           'Sample': ["Is this a description of the reporting sample, reflecting just those leaders who likely have good results (Lead), or is this an analysis across the whole range of needed adaptation (Need)? Specify 'Lead', 'Need', or 'N/A'.", checks.oneof(['Lead', 'Need', 'N/A'])],
                           'Units': ["What are the units of the quantitative outcome?", checks.very_short],
                           'Value': ["What is the value of the quantitative outcome?", checks.numeric],
                           'SD': ["What is the standard error or standard deviation of the result? Specify a number or NA.", checks.numeric_or_na],
                           'Low Quantile': ["If a lower quantile value is specified, what is the percent value of that quantile, or NA.", checks.percent_or_na],
                           'Low Value': ["If a lower quantile value is specified, what is the value at that quantile, or NA.", checks.numeric_or_na],
                           'High Quantile': ["If a lower quantile value is specified, what is the percent value of that quantile, or NA.", checks.percent_or_na],
                           'High Value': ["If a lower quantile value is specified, what is the value at that quantile, or NA.", checks.numeric_or_na],
                           'Result Source': ["Where is this quantitative result reported in the paper?", checks.short],
                           'More Notes': ["Do you have any other notes?"]
                       }}

## Multiple passes and reconciliation
dopass_count = 3
merge_count = 10
merge_suffix = {'Macroeconomic/Fiscal': '-macro',
                'Adaptation': '-adapt'}
merge_extract_file = "../extract.csv"
merge_columns = {'Macroeconomic/Fiscal': {
    'Author(s)': "Use an abbreviated format, like 'Last Name et al.' or 'First & Second'.",
    'Year': "Publication year.",
    'Paper Title': None,
    'Link to paper': None,
    'Paper ID': None,
    'Reviewer': None,
    'Status': None,
    'Country(ies)': "What specific country or group of countries was considered? Just provide the country names as ISO3 codes or a short group name.",
    'Outcome(s) of Interest': "Specific macroeconomic outcomes (GDP effects, productivity loss, interest, inflation, etc.) or fiscal outcomes (budget balance, borrowing costs, public expenditure or revenue, etc.) or measures of economic costs and/or benefits (or related measures like ROI, NPV) of nation-wide adaptation.",
    'Drivers of Risk': "What shocks or changes are impacting the outcomes?",
    'Scenario(s)': "Under what socioeconomic or climate scenarios were the outcomes analyzed? Just provide technical scenario names.",
    'Methodology': "How is the analysis performed and when are its results applicable?",
    'Calibration Approach': "What calibration or modeling approach was used in the analysis? Choose one of 'Econometric', 'Macro-model', 'Stylised', or 'N/A'.",
    'Hazard definition': "What kind of hazards were analyzed in the paper? Choose one of 'Acute shocks', 'Chronic trends', 'Stylised changes', or 'N/A'.",
    'Impact persistence': "To what degree is persistence in impacts condidered? Choose one of 'None', 'Permanent', or 'Adaptive'.",
    'Space disaggregation': "What level of disaggregation was used in the analysis? Choose one of 'Global', 'Regional', or 'Local'.",
    'Impact interactions': "Where interactions between impacts considered in the analysis? Choose one of 'None', 'Sequential Interactions', 'Spatial Interactions', or 'Sectoral Interactions'.",
    'Economic dynamics': "Was the dynamic nature of the economy considered in the analysis? Choose one of 'Static', 'Transitional (accounting for changes over time)', or 'Adaptive (reflecting shifts in economic behavior in response to impacts)'.",
    'Climate features': "Were tipping points or other notable climate complexities included? Choose one of 'Tipping Points', 'Other', or 'None'.",
    'Adaptation considered': "How and to what extent is adaptation considered? Just provide brief notes, avoiding statements that start 'Adaptation is considered...'.",
    'Highlights': "What are the most important outcomes of the analysis?",
    'More Notes': "Do you have any other notes?"},
                 'Adaptation': {
                     'Author(s)': "Use an abbreviated format, like 'Last Name et al.' or 'First & Second'.",
                     'Year': "Publication year.",
                     'Paper Title': None,
                     'Link to paper': None,
                     'Paper ID': None,
                     'Reviewer': None,
                     'Status': None,
                     'Country(ies)': "What specific country or group of countries was considered? Just provide the country names as ISO3 codes or a short group name.",
                     'Impacted Sector': "Is there a specific sector of the economy that is impacted?",
                     'Scenario(s)': "Under what socioeconomic or climate scenarios were the outcomes analyzed? Just provide technical scenario names.",
                     'Methodology': "How is the analysis performed and when are its results applicable?",
                     'Benefits of Adaptation': "How are benefits of adaptation quantified, if at all?",
                     'Costs of Adaptation': "How are costs of adaptation quantified, if at all?",
                     'Ante/Post?': "Does the analysis rely on ex-ante modeling or ex-post observations? Choose one of 'Ex-Ante', 'Ex-Post', or 'N/A'.",
                     'Planning Process': "What is discussed about the adaptation planning/decision-making process?",
                     'Soft Options': "What is the benefit of \"soft options\" (e.g., informational and institutional interventions)?",
                     'Sufficiency Definition': "How do different papers understand sufficient adaptation levels (i.e., what does it mean to be well-adapted)?",
                     'Highlights': "What are the most important outcomes of the analysis?",
                     'More Notes': "Do you have any other notes?"}}
