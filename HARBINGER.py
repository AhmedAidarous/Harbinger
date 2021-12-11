import requests
from bs4 import BeautifulSoup
import pandas as pd
from yahoo_fin import stock_info as si
from yahoofinancials import YahooFinancials

def getAllTickers():
    df2 = pd.DataFrame(si.tickers_S&P500())
    sym2 = set(symbol for symbol in df2[0].values.tolist())


    return sym2


print(getAllTickers())

# This ia rhw liar of stocks to rank and see how their magic formula score compares to one another
tickers = ['ESGRP', 'XOSWW', 'JOUT', 'RDI', 'CDZI']

# list of tickers whose financial data needs to be extracted
financial_dir = {}

for ticker in tickers:
    try:
        print(ticker)
        # getting balance sheet data from yahoo finance for the given ticker
        temp_dir = {}
        url = 'https://in.finance.yahoo.com/quote/' + ticker + '/balance-sheet?p=' + ticker
        headers = {'User-Agent': "Mozilla/5.0"}
        page = requests.get(url, headers=headers)
        page_content = page.content
        soup = BeautifulSoup(page_content, 'html.parser')
        tabl = soup.find_all("div", {"class": "M(0) Whs(n) BdEnd Bdc($seperatorColor) D(itb)"})
        for t in tabl:
            rows = t.find_all("div", {"class": "rw-expnded"})
            for row in rows:
                temp_dir[row.get_text(separator='|').split("|")[0]] = row.get_text(separator='|').split("|")[1]

        # getting income statement data from yahoo finance for the given ticker
        url = 'https://in.finance.yahoo.com/quote/' + ticker + '/financials?p=' + ticker
        headers = {'User-Agent': "Mozilla/5.0"}
        page = requests.get(url, headers=headers)
        page_content = page.content
        soup = BeautifulSoup(page_content, 'html.parser')
        tabl = soup.find_all("div", {"class": "M(0) Whs(n) BdEnd Bdc($seperatorColor) D(itb)"})
        for t in tabl:
            rows = t.find_all("div", {"class": "rw-expnded"})
            for row in rows:
                temp_dir[row.get_text(separator='|').split("|")[0]] = row.get_text(separator='|').split("|")[1]

        # getting cashflow statement data from yahoo finance for the given ticker
        url = 'https://in.finance.yahoo.com/quote/' + ticker + '/cash-flow?p=' + ticker
        headers = {'User-Agent': "Mozilla/5.0"}
        page = requests.get(url, headers=headers)
        page_content = page.content
        soup = BeautifulSoup(page_content, 'html.parser')
        tabl = soup.find_all("div", {"class": "M(0) Whs(n) BdEnd Bdc($seperatorColor) D(itb)"})
        for t in tabl:
            rows = t.find_all("div", {"class": "rw-expnded"})
            for row in rows:
                temp_dir[row.get_text(separator='|').split("|")[0]] = row.get_text(separator='|').split("|")[1]

        # getting key statistics data from yahoo finance for the given ticker
        url = 'https://in.finance.yahoo.com/quote/' + ticker + '/key-statistics?p=' + ticker
        headers = {'User-Agent': "Mozilla/5.0"}
        page = requests.get(url, headers=headers)
        page_content = page.content
        soup = BeautifulSoup(page_content, 'html.parser')
        tabl = soup.findAll("table",
                            {"class": "W(100%) Bdcl(c)"})  # try soup.findAll("table") if this line gives error
        for t in tabl:
            rows = t.find_all("tr")
            for row in rows:
                if len(row.get_text(separator='|').split("|")[0:2]) > 0:
                    temp_dir[row.get_text(separator='|').split("|")[0]] = row.get_text(separator='|').split("|")[-1]

                    # combining all extracted information with the corresponding ticker
        financial_dir[ticker] = temp_dir
    except:
        print("Problem scraping data for ", ticker)

# storing information in pandas dataframe
combined_financials = pd.DataFrame(financial_dir)
combined_financials.dropna(how='all', axis=1, inplace=True)  # dropping columns with all NaN values
tickers = combined_financials.columns  # updating the tickers list based on only those tickers whose values were successfully extracted
for ticker in tickers:
    combined_financials = combined_financials[~combined_financials[ticker].str.contains("[a-z]").fillna(False)]

print(combined_financials)

# creating dataframe with relevant financial information for each stock using fundamental data
stats = ["EBITDA",
         "Depreciation & amortisation",
         "Market cap (intra-day)",
         "Net income available to common shareholders",
         "Net cash provided by operating activities",
         "Capital expenditure",
         "Total current assets",
         "Total current liabilities",
         "Net property, plant and equipment",
         "Total stockholders' equity",
         "Long-term debt",
         "Forward annual dividend yield"]  # change as required

indx = ["EBITDA", "D&A", "MarketCap", "NetIncome", "CashFlowOps", "Capex", "CurrAsset",
        "CurrLiab", "PPE", "BookValue", "TotDebt", "DivYield"]
all_stats = {}
for ticker in tickers:
    try:
        temp = combined_financials[ticker]
        ticker_stats = []
        for stat in stats:
            ticker_stats.append(temp.loc[stat])
        all_stats['{}'.format(ticker)] = ticker_stats
    except:
        print("can't read data for ", ticker)

# cleansing of fundamental data imported in dataframe
all_stats_df = pd.DataFrame(all_stats, index=indx)
all_stats_df[tickers] = all_stats_df[tickers].replace({',': ''}, regex=True)
all_stats_df[tickers] = all_stats_df[tickers].replace({'M': 'E+03'}, regex=True)
all_stats_df[tickers] = all_stats_df[tickers].replace({'B': 'E+06'}, regex=True)
all_stats_df[tickers] = all_stats_df[tickers].replace({'T': 'E+09'}, regex=True)
all_stats_df[tickers] = all_stats_df[tickers].replace({'%': 'E-02'}, regex=True)
for ticker in all_stats_df.columns:
    all_stats_df[ticker] = pd.to_numeric(all_stats_df[ticker].values, errors='coerce')
all_stats_df.dropna(axis=1, inplace=True)
tickers = all_stats_df.columns

# calculating relevant financial metrics for each stock
transpose_df = all_stats_df.transpose()
final_stats_df = pd.DataFrame()
final_stats_df["EBIT"] = transpose_df["EBITDA"] - transpose_df["D&A"]
final_stats_df["TEV"] = transpose_df["MarketCap"].fillna(0) \
                        + transpose_df["TotDebt"].fillna(0) \
                        - (transpose_df["CurrAsset"].fillna(0) - transpose_df["CurrLiab"].fillna(0))
final_stats_df["EarningYield"] = final_stats_df["EBIT"] / final_stats_df["TEV"]
final_stats_df["FCFYield"] = (transpose_df["CashFlowOps"] - transpose_df["Capex"]) / transpose_df["MarketCap"]
final_stats_df["ROC"] = (transpose_df["EBITDA"] - transpose_df["D&A"]) / (
            transpose_df["PPE"] + transpose_df["CurrAsset"] - transpose_df["CurrLiab"])
final_stats_df["BookToMkt"] = transpose_df["BookValue"] / transpose_df["MarketCap"]
final_stats_df["DivYield"] = transpose_df["DivYield"]

################################Output Dataframes##############################

# finding value stocks based on Magic Formula
final_stats_val_df = final_stats_df.loc[tickers, :]
final_stats_val_df["CombRank"] = final_stats_val_df["EarningYield"].rank(ascending=False, na_option='bottom') + \
                                 final_stats_val_df["ROC"].rank(ascending=False, na_option='bottom')
final_stats_val_df["MagicFormulaRank"] = final_stats_val_df["CombRank"].rank(method='first')
value_stocks = final_stats_val_df.sort_values("MagicFormulaRank").iloc[:, [2, 4, 8]]
print("------------------------------------------------")
print("Value stocks based on Greenblatt's Magic Formula")
print(value_stocks)

# finding highest dividend yield stocks
high_dividend_stocks = final_stats_df.sort_values("DivYield", ascending=False).iloc[:, 6]
print("------------------------------------------------")
print("Highest dividend paying stocks")
print(high_dividend_stocks)

# # Magic Formula & Dividend yield combined
final_stats_df["CombRank"] = final_stats_df["EarningYield"].rank(ascending=False, method='first') \
                             + final_stats_df["ROC"].rank(ascending=False, method='first') \
                             + final_stats_df["DivYield"].rank(ascending=False, method='first')
final_stats_df["CombinedRank"] = final_stats_df["CombRank"].rank(method='first')
value_high_div_stocks = final_stats_df.sort_values("CombinedRank").iloc[:, [2, 4, 6, 8]]
print("------------------------------------------------")
print("Magic Formula and Dividend Yield combined")
print(value_high_div_stocks)

# Modules imported..
from yahoofinancials import YahooFinancials
import json
import pandas as pd
from yahoo_fin import stock_info as si


def readableJson(data):
    """Converts the returned yahooFinancials into readable Json Data"""
    return json.dumps(data, indent=4)


def getAllTickers():
    # gather stock symbols from major US exchanges
#    df1 = pd.DataFrame(si.tickers_sp500())
    df2 = pd.DataFrame(si.tickers_nasdaq())
#    df3 = pd.DataFrame(si.tickers_dow())
#    df4 = pd.DataFrame(si.tickers_other())

    # convert DataFrame to list, then to sets
#    sym1 = list(symbol for symbol in df1[0].values.tolist())
    sym2 = set(symbol for symbol in df2[0].values.tolist())
#    sym3 = set(symbol for symbol in df3[0].values.tolist())
#    sym4 = set(symbol for symbol in df4[0].values.tolist())

    # join the 4 sets into one. Because it's a set, there will be no duplicate symbols
#    symbols = set.union(sym1)

    # Some stocks are 5 characters. Those stocks with the suffixes listed below are not of interest.
#    my_list = ['W', 'R', 'P', 'Q']
#    del_set = set()
#    sav_set = set()

 #   for symbol in symbols:
 #       if len(symbol) > 4 and symbol[-1] in my_list:
 #           del_set.add(symbol)
 #       else:
 #           sav_set.add(symbol)

    return sym2


def getBalanceSheet(ticker , duration):

    """
    This method returns the quarterly balance sheet of a company, given the ticker
    and the following are the fields that are returned in the balance sheet in a
    readable Json Format:
"""
    yahooFinancialObj = YahooFinancials(ticker)
    # Get the Quarterly Balance Sheet which would display the following
    balanceSheetQuarterly = yahooFinancialObj.get_financial_stmts(duration , 'balance')
    return (readableJson(balanceSheetQuarterly))


def getincomeStatement(ticker , duration):

    yahooFinancialObj = YahooFinancials(ticker)

    # Get the Quarterly income Sheet which would display the following
    incomeSheetQuarterly = yahooFinancialObj.get_financial_stmts(duration , 'income')
    return (readableJson(incomeSheetQuarterly))


def getStockEarningsData(ticker):
    "Given the ticker, would return the stock earnings data"
    yahoofinancialsObj = YahooFinancials(ticker)

    return(readableJson(yahoofinancialsObj.get_stock_earnings_data()))



def getNetIncome(ticker):
    yahoofinancialsObj = YahooFinancials(ticker)
    return yahoofinancialsObj.get_net_income()

def getDicKeys(dic):
    return [*dic][0]


def getKeyStats(ticker):
    yahoofinancialsObj = YahooFinancials(ticker)
    return yahoofinancialsObj.get_key_statistics_data()


def getCurrentSharePrice (ticker):
    yahoofinancialsObj = YahooFinancials(ticker)
    return yahoofinancialsObj.get_current_price()


# The Quick Ratio
# QuickRatio = (Current Assets - Inventory) / Current Liabilities

sp_Tickers = getAllTickers()

for ticker in sp_Tickers:
    try:

        balanceSheet = json.loads(getBalanceSheet(ticker, "annual"))
        incomeStatement = json.loads(getincomeStatement(ticker , 'annual'))
        keyStats = ((getKeyStats(ticker))[ticker])

        print("Analyzing NASDAQ " + ticker)        
        
        

        balanceSheet = balanceSheet["balanceSheetHistory"][ticker]
        incomeStatement = incomeStatement['incomeStatementHistory'][ticker]


        # Gather balance sheet latest date
        date = getDicKeys(balanceSheet[0])
        date2 = getDicKeys(incomeStatement[0])

        # Retrieving the fields
        totalCurrentAssets = (balanceSheet[0][date]["totalCurrentAssets"])
        inventory = (balanceSheet[0][date]["inventory"])
        currentLiabilities = (balanceSheet[0][date]["totalCurrentLiabilities"])
        totalStockHolderEquity = (balanceSheet[0][date]['totalStockholderEquity'])
        totalLiabilities = (balanceSheet[0][date]['totalCurrentLiabilities'])

        
        operatingIncome = (incomeStatement[0][date2]['operatingIncome'])
        totalRevenue = (incomeStatement[0][date2]['totalRevenue'])

        currentOutstandingShares = (keyStats["sharesOutstanding"])

        # Calculating the Financial Metrics
        quickRatio = (totalCurrentAssets - inventory) / currentLiabilities
        d_eRatio = totalLiabilities / totalStockHolderEquity
        operatingMargin = (operatingIncome / totalRevenue) * 100
        profitMargin = 100 * (keyStats["profitMargins"])

        if (quickRatio > 1 and d_eRatio < 2 and d_eRatio > 0 and operatingMargin > 15 and profitMargin >= 15):
            print("""
            
            
            Financial Fundamental Analysis
             * Ticker : %s
             * Quick Ratio : % s
             * D/E Ratio : % s
             * Operating Margin : %s
             * Profit Margin : %s
             
            
            """ % (ticker , quickRatio, d_eRatio , operatingMargin, profitMargin))

    except:
        print("Cannot Access "+ ticker)


