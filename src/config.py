from lib import commands, checks

count_perrun = 21000
openai_config = 'batch'
gemini_config = 'fast'

searches = ["/Users/admin/Library/CloudStorage/GoogleDrive-jrising@udel.edu/My Drive/Research/COP30 Ada/AI Review/scopus.csv",
            "/Users/admin/Library/CloudStorage/GoogleDrive-jrising@udel.edu/My Drive/Research/COP30 Ada/AI Review/savedrecsII.xls"]
response_file = "../responses.csv"
verdict_file = "../verdicts.csv"
response_round2_file = "responses-round2.csv"

abstract_prompt = "I am performing a global review and analytical synthesis of the macroeconomic and macro-fiscal risks of climate change and the costs and benefits of adaptation at a national level."
exclude_codes = {'XC': "Not related to climate risks",
                 'XV': "Not valued in economic terms",
                 'XN': "Not nation-scale or multinational (not macroeconomic or related to nation-wide adaptation)",
                 'XA': "No new analysis (using previously-published work)",
                 'XO': "Excluded for another reason (please specify)"}
include_codes = {'RE': "Reports macroeconomic outcomes (GDP effects, productivity loss, interest, inflation, etc.)",
                 'RF': "Reports fiscal outcomes (budget balance, borrowing costs, public expenditure or revenue, etc.)",
                 'RA': "Reports both economic costs and/or benefits (or related measures like ROI, NPV) of nation-wide adaptationo"}
passfail_file = "../question.csv"

## Question
questionsource = verdict_file.replace(".csv", "-further.csv")
singlequestion = "Based on this information, does this paper describe outcomes driven by climate change (that is, all the effects that come from increased greenhouse gas concentrations, such as increased temperatures and other weather changes), as opposed to the effects of climate policy? I am also interested in adaptation and resilience, but again, I do *not* want to consider reductions in losses that are coming from reduced greenhouse gas emissions."
question_file = "../question.csv"

## Find PDFs
priority_limit = 10
pdfs_dir = "../pdfs"
finder_count = 100

## Extract data from PDFs
extract_dir = "../extract"
collate_count = 10
column_defs_collate = {'Outcome(s) of Interest': "Specific macroeconomic outcomes (GDP effects, productivity loss, interest, inflation, etc.) or fiscal outcomes (budget balance, borrowing costs, public expenditure or revenue, etc.) or measures of economic costs and/or benefits (or related measures like ROI, NPV) of nation-wide adaptation.",
                       'Drivers of Risk': "What shocks or changes are impacting the outcomes?",
                       'Quantitative material': "Is there quantitative information on the outcomes of interest on this page?",
                       'Methodology': "How is the analysis performed and when its results applicable?",
                       'Highlights': "What are the most important outcomes of the analysis?",
                       'More Notes': "Do you have any other notes?"}

## Summarized line for PDF
summary_count = 10
summary_file = "../summary.csv"
column_defs_summary = {'All': {
    'Author(s)': lambda row, xtt: commands.short_authors(row['Authors']),
    'Year': lambda row, xtt: row['Year'],
    'Paper Title': lambda row, xtt: row['Title'],
    'Link to paper': "LINK",
    'Paper ID': lambda row, xtt: row['DOI'],
    'Reviewer': "AI",
    'Status': "STATUS",
    'NEXT': lambda row, xtt: commands.ai_select(xtt, "Does this paper produce new quantitative results on specific macroeconomic outcomes (GDP effects, productivity loss, interest, inflation, etc.) or fiscal outcomes (budget balance, borrowing costs, public expenditure or revenue, etc.) or measures of economic costs and/or benefits (or related measures like ROI, NPV) of nation-wide adaptation?", ['Quantitative material', 'Methodology'], ['Macroeconomic/Fiscal', 'Adaptation'], abstract_prompt)},
                       'Any': {
                           'Country(ies)': lambda row, xtt: commands.ai_summary(xtt, "What specific country or group of countries was considered? Just provide the country names or group.", ['Methodology'], abstract_prompt),
                           'Outcome(s) of Interest': "BRIEF",
                           'Drivers of Risk': "BRIEF",
                           'Scenario(s)': lambda row, xtt: commands.ai_summary(xtt, "Under what socioeconomic or climate scenarios were the outcomes analyzed? Just provide technical scenario names.", ['Methodology'], abstract_prompt),
                           'Methodology': "SUMMARIZE",
                           'Highlights': "SUMMARIZE",
                           'More Notes': "SUMMARIZE"},
                       'Macroeconomic/Fiscal': {
                           'Applicability': "Macroeconomic/Fiscal",
                           'Calibration Approach': lambda row, xtt: commands.ai_select(xtt, "What calibration or modeling approach was used in the analysis?", ['Methodology'], ['Econometric', 'Macro-model', 'Stylised', 'N/A'], abstract_prompt),
                           'Hazard definition': lambda row, xtt: commands.ai_select(xtt, "What kind of hazards were analyzed in the paper?", ['Methodology'], ['Acute shocks', 'Chronic trends', 'Stylised changes', 'N/A'], abstract_prompt),
                           'Impact persistence': lambda row, xtt: commands.ai_select(xtt, "To what degree what persistence in impacts condidered?", ['Methodology'], ['None', 'Permanent', 'Adaptive'], abstract_prompt),
                           'Space disaggregation': lambda row, xtt: commands.ai_select(xtt, "What level of disaggregation was used in the analysis?", ['Methodology'], ['Global', 'Regional', 'Local'], abstract_prompt),
                           'Impact interactions': lambda row, xtt: commands.ai_select(xtt, "Where interactions between impacts considered in the analysis?", ['Methodology'], ['None', 'Sequential Interactions', 'Spatial Interactions', 'Sequential and Spatial'], abstract_prompt),
                           'Economic dynamics': lambda row, xtt: commands.ai_select(xtt, "Was the dynamic nature of the economy considered in the analysis?", ['Methodology'], ['Static', 'Transitional (accounting for changes over time)', 'Adaptive (reflecting shifts in economic behavior in response to impacts)'], abstract_prompt),
                           'Climate features': lambda row, xtt: commands.ai_select(xtt, "Were tipping points included?", ['Methodology'], ['Tipping Points', 'Other'], abstract_prompt),
                           'Adaptation considered': lambda row, xtt: commands.ai_summary(xtt, "How and to what extent is adaptation considered? Just provide brief notes, avoiding statements that start 'Adaptation is considered...'.", ['Methodology'], abstract_prompt)
                       },
                       'Adaptation': {
                           'Applicability': "Adaptation",
                           'Impacted Sector': lambda row, xtt: commands.ai_summary(xtt, "Is there a specific sector of the economy that is impacted?", ['Methodology'], abstract_prompt),
                           'Benefits of Adaptation': lambda row, xtt: commands.ai_summary(xtt, "How are benefits of adaptation quantified?", ['Methodology'], abstract_prompt),
                           'Costs of Adaptation': lambda row, xtt: commands.ai_summary(xtt, "How are costs of adaptation quantified?", ['Methodology'], abstract_prompt),
                           'Ante/Post?': lambda row, xtt: commands.ai_summary(xtt, "Does the analysis rely on ex-ante modeling or ex-post observations?", ['Methodology'], abstract_prompt),
                           'Planning Process': lambda row, xtt: commands.ai_summary(xtt, "What is discussed about the adaptation planning/decision-making process?", ['Methodology'], abstract_prompt),
                           '"Soft Options"': lambda row, xtt: commands.ai_summary(xtt, "What is the benefit of \"soft options\" (e.g., informational and institutional interventions)?", ['Methodology'], abstract_prompt),
                           'Sufficiency Definition': lambda row, xtt: commands.ai_summary(xtt, "How do different papers understand sufficient adaptation levels (i.e., what does it mean to be well-adapted)?", ['Methodology'], abstract_prompt)
                       }}

extract_count = 1
extract_fromcollate = 'Quantitative material'
extract_fromsummary = 'Applicability'
column_defs_extract = {'Macroeconomic/Fiscal': {
    'Outcome': ["What is the outcome that is affected by climate change? Just provide a single term.", checks.very_short],
    'Country(ies)': ["What specific country or group of countries was considered? Just provide the country names or group.", checks.very_short],
    'Scenario': ["Under what socioeconomic or climate scenario were the outcomes analyzed? Just provide a technical scenario name.", checks.very_short],
    'Year': ["Under what future or past year is the outcome evaluated? Just specify a single year.", checks.year],
    'Relative to': ["What comparison scenario are quantitative outcomes reported relative to? For example, specify a baseline year or if it is relative to no climate change, write 'No CC'.", checks.very_short],
    'Units': ["What are the units of the quantitative outcome?", checks.very_short],
    'Value': ["What is the value of the quantitative outcome?", checks.numeric],
    'SD': ["What is the standard error or standard deviation of the result? Specify a number or NA.", checks.numeric_or_na],
    'Low Quantile': ["If a lower quantile value is specified, what is the percent value of that quantile, or NA.", checks.percent_or_na],
    'Low Value': ["If a lower quantile value is specified, what is the value at that quantile, or NA.", checks.numeric_or_na],
    'High Quantile': ["If a lower quantile value is specified, what is the percent value of that quantile, or NA.", checks.percent_or_na],
    'High Value': ["If a lower quantile value is specified, what is the value at that quantile, or NA.", checks.numeric_or_na],
    'Result Source': ["Where is this quantitative result reported in the paper?", checks.short],
    'More Notes': ["Do you have any other notes?"]
},
                       'Adaptation': {
                           'Impacted Sector': ["What economic sector or group is being impacted by climate change? Just provide a single term or All or NA.", checks.very_short],
                           'Solution': ["What type of solution is being evaluated? Just provide a single term or Any or NA.", checks.very_short],
                           'Country(ies)': ["What specific country or group of countries was considered? Just provide the country names or group.", checks.very_short],
                           'Scenario': ["Under what socioeconomic or climate scenario were the outcomes analyzed? Just provide a technical scenario name.", checks.very_short],
                           'Quantification': ["How are the effects of adaptation being quantified? Just provide a technical term.", checks.very_short],
                           'Expression': ["As a simple mathematical expression, what does the quantification express? Valid terms include AvoidedImpact, MonetaryBenefits, NonMonetaryBenefits, BaselineImpact, AdaptationCost, CapExCost, OpExCost, and functions like DiscountedSum() and RateOfReturn()", checks.short],
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
