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
                 'RA': "Reports both economic costs and/or benefits (or related measures like ROI, NPV) of nation-wide adaptation"}
