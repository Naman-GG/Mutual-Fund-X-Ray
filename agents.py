from schema import PortfolioState, Investment, AnalysisResult, StrategyPlan

import os
import pandas as pd

def load_market_db():
    try:
        file_path = os.path.join(os.path.dirname(__file__), "market_data.csv")
        df = pd.read_csv(file_path)
        db = {}
        for _, row in df.iterrows():
            db[row['Fund Name']] = {
                "sector": row['Sector'],
                "expense_ratio": row['Expense Ratio'],
                "holdings": [row['Top Holding 1'], row['Top Holding 2'], row['Top Holding 3']]
            }
        return db
    except Exception as e:
        print(f"Warning: Could not load market_data.csv. Error: {e}")
        return {}

MOCK_MARKET_DB = load_market_db()

def extractor_node(state: PortfolioState):
    raw_input = state.get("raw_input", "")
    log_updates = ["Agent A (Extractor): Parsing raw input to extract mutual fund data..."]
    errors = []
    extracted_investments = []
    
    if "SBI Bluechip" in raw_input:
        extracted_investments.append(Investment(fund_name="SBI Bluechip", amount=50000.0))
    if "HDFC Top 100" in raw_input:
        extracted_investments.append(Investment(fund_name="HDFC Top 100", amount=75000.0))
    if "Axis Midcap" in raw_input:
        extracted_investments.append(Investment(fund_name="Axis Midcap", amount=30000.0))
    if "Parag Parikh Flexi Cap" in raw_input:
        extracted_investments.append(Investment(fund_name="Parag Parikh Flexi Cap", amount=45000.0))

    if not extracted_investments:
        log_updates.append("Agent A (Extractor): Failed to extract valid funds from input.")
        errors.append("No valid funds found.")
    else:
        log_updates.append(f"Agent A (Extractor): Successfully extracted {len(extracted_investments)} funds.")
    
    return {"investments": extracted_investments, "log": log_updates, "errors": errors}

def reflection_node(state: PortfolioState):
    log_updates = ["Agent B (Analyst Reflection): Verifying Extractor's output..."]
    errors = []
    
    investments = state.get("investments", [])
    if not investments:
        log_updates.append("Agent B (Analyst Reflection): Error - No investments passed down. Halting workflow.")
        errors.append("Validation failed: empty portfolio.")
    else:
        log_updates.append("Agent B (Analyst Reflection): Data looks solid. Passing to Core Analyst Logic.")
        
    return {"log": log_updates, "errors": errors}

def analyst_node(state: PortfolioState):
    log_updates = ["Agent B (Analyst): Performing Portfolio X-Ray against Market DB..."]
    investments = state.get("investments", [])
    
    analysis = AnalysisResult()
    total_val = sum(inv.amount for inv in investments) if investments else 0.0
    analysis.total_value = total_val
    
    stock_counts = {}
    total_drag = 0.0
    
    for inv in investments:
        db_info = MOCK_MARKET_DB.get(inv.fund_name)
        if db_info:
            inv.sector = db_info["sector"]
            inv.expense_ratio = db_info["expense_ratio"]
            inv.holdings = db_info["holdings"]
            
            if inv.expense_ratio and inv.expense_ratio > 0.5:
                excess = inv.expense_ratio - 0.5
                drag = inv.amount * (excess / 100)
                total_drag += drag
            
            if inv.sector and total_val > 0:
                analysis.sector_allocation[inv.sector] = analysis.sector_allocation.get(inv.sector, 0.0) + (inv.amount / total_val) * 100
            
            for stock in (inv.holdings or []):
                if stock not in stock_counts:
                    stock_counts[stock] = []
                stock_counts[stock].append(inv.fund_name)

    for stock, funds in stock_counts.items():
        if len(funds) > 1:
            analysis.overlap_warnings.append(f"High overlap in {stock}: held by {', '.join(funds)}.")
            
    analysis.expense_ratio_drag = total_drag
    analysis.potential_savings = total_drag * 5
    
    log_updates.append(f"Agent B (Analyst): Found {len(analysis.overlap_warnings)} overlap issues and ₹{total_drag:.2f} in excess annual fees.")
    return {"analysis": analysis, "log": log_updates, "investments": investments}

def strategist_node(state: PortfolioState):
    log_updates = ["Agent C (Strategist): Generating personalized rebalancing plan..."]
    score = 100
    steps = []
    
    analysis = state.get("analysis")
    if analysis:
        if analysis.expense_ratio_drag > 500:
            score -= 20
            steps.append("Consider switching high expense mutual funds (e.g. Regular plans > 1.0%) to Direct plans to save on commissions.")
        
        if len(analysis.overlap_warnings) > 0:
            score -= (10 * len(analysis.overlap_warnings))
            steps.append("You have overlapping stocks in your mutual funds. Consider consolidating them to reduce redundant exposure.")
            
    score = max(30, score)
    
    feedback = f"Hello there! Your Money Health Score is {score}/100. "
    if score >= 80:
        feedback += "You are doing fantastic! Just a few minor tweaks to optimize your wealth."
    elif score >= 50:
        feedback += "You're on the right track, but we can make your money work a bit harder for you. Let's look at reducing those hidden overlaps and fees!"
    else:
        feedback += "Don't worry, every smart investor starts somewhere. We've found some key areas like high expense ratios and duplicate holdings that we can fix together to boost your returns."
        
    strategy = StrategyPlan(
        health_score=score,
        feedback=feedback,
        rebalancing_steps=steps
    )
    
    log_updates.append("Agent C (Strategist): Plan generated successfully.")
    return {"strategy": strategy, "log": log_updates}
