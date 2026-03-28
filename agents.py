from schema import PortfolioState, Investment, AnalysisResult, StrategyPlan
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from typing import List
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

class PortfolioExtract(BaseModel):
    investments: List[Investment] = Field(description="List of extracted investments")

def extractor_node(state: PortfolioState):
    raw_input = state.get("raw_input", "")
    log_updates = ["Agent A (Extractor): Parsing raw input using Gemini LLM..."]
    errors = []
    extracted_investments = []
    
    try:
        # Initialize Gemini LLM
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
        
        # Use structured output to force the LLM to return our Pydantic schema
        structured_llm = llm.with_structured_output(PortfolioExtract)
        
        known_funds = ", ".join(MOCK_MARKET_DB.keys())
        prompt = f"""
        Extract the mutual fund investments from the following user portfolio text.
        For each investment, identify the exact fund name and the invested amount.
        
        IMPORTANT: Your extracted 'fund_name' MUST exactly match the spelling and casing of one of our known database funds if it is a close match.
        Known Funds: {known_funds}
        
        User Text: {raw_input}
        """
        
        result = structured_llm.invoke(prompt)
        extracted_investments = result.investments
        
        if not extracted_investments:
            log_updates.append("Agent A (Extractor): Failed to extract valid funds from input.")
            errors.append("No valid funds found.")
        else:
            log_updates.append(f"Agent A (Extractor): Successfully extracted {len(extracted_investments)} funds.")
            
    except Exception as e:
        log_updates.append(f"Agent A (Extractor): LLM parsing failed: {str(e)}")
        errors.append(f"LLM Error: {str(e)}")
    
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
    log_updates = ["Agent C (Strategist): Generating personalized rebalancing plan using Gemini LLM..."]
    
    analysis = state.get("analysis")
    investments = state.get("investments", [])
    
    if not analysis:
        return {"log": log_updates + ["Agent C (Strategist): No analysis available."]}

    try:
        # Lowered temperature to 0.0 for deterministic scoring
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.0)
        structured_llm = llm.with_structured_output(StrategyPlan)
        
        portfolio_summary = "\n".join([f"- {inv.fund_name}: ₹{inv.amount}" for inv in investments])
        overlap_info = "\n".join([f"- {warn}" for warn in analysis.overlap_warnings])
        
        prompt = f"""
        You are an expert Financial Mentor for The Economic Times (ET MoneyMentor Pro).
        Review the following portfolio analysis and generate a personalized, encouraging strategy plan.
        
        Portfolio Details:
        {portfolio_summary}
        
        Analysis Insights:
        - Total Value: ₹{analysis.total_value}
        - Total 5-Year Drag from High Expense Ratios (Regular Plans): ₹{analysis.potential_savings}
        - Overlap Warnings:
        {overlap_info if overlap_info else "- None"}
        
        Task:
        1. Calculate a realistic 'Money Health Score' out of 100 based on the overlaps and expense drag. (Lower score if high overlaps and fees).
        2. Write exactly 2-3 sentences of 'feedback' that is highly encouraging but sets a clear mentor tone. Act as a trusted advisor.
        3. Provide 2-4 actionable 'rebalancing_steps' in simple language. If there are overlaps, explicitly suggest consolidating those specific funds. If there is high drag, suggest direct plans.
        """
        
        strategy = structured_llm.invoke(prompt)
        log_updates.append("Agent C (Strategist): Real-time Plan generated successfully.")
        
    except Exception as e:
        log_updates.append(f"Agent C (Strategist): LLM failed, falling back to basic strategy. Error: {str(e)}")
        strategy = StrategyPlan(
            health_score=50,
            feedback="We encountered a technical hurdle generating your mentor feedback, but saving on expense ratios is always a smart move.",
            rebalancing_steps=["Consider moving from Regular to Direct plans."]
        )
        
    return {"strategy": strategy, "log": log_updates}
