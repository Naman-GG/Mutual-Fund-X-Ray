from schema import PortfolioState, Investment, AnalysisResult, StrategyPlan
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from typing import List, Dict
import os
import io
import pandas as pd
from datetime import datetime

try:
    import pyxirr
except ImportError:
    pyxirr = None

try:
    import casparser
except ImportError:
    casparser = None

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
    pdf_bytes = state.get("pdf_bytes")
    pdf_password = state.get("pdf_password")
    
    log_updates = ["Agent A (Extractor): Parsing input using Gemini LLM..."]
    errors = []
    extracted_investments = []
    transactions = []
    
    # 1. CAS Parsing if PDF Uploaded
    if pdf_bytes and pdf_password and casparser:
        log_updates.append("Agent A (Extractor): CAS PDF detected. Decrypting and parsing via CAMS/KFintech engine...")
        try:
            data = casparser.read_cas_pdf(io.BytesIO(pdf_bytes), pdf_password)
            parsed_texts = []
            
            for folio in data.get("folios", []):
                for scheme in folio.get("schemes", []):
                    scheme_name = scheme.get("scheme", "")
                    curr_val = scheme.get("valuation", {}).get("value", 0.0)
                    
                    inv_amt = 0.0
                    for txn in scheme.get("transactions", []):
                        amt = txn.get("amount", 0.0)
                        if amt:
                            inv_amt += abs(amt)
                            transactions.append({"date": txn.get("date"), "amount": amt})
                            
                    parsed_texts.append(f"Invested {inv_amt} in {scheme_name}. Current valuation is {curr_val}.")
            
            raw_input = " ".join(parsed_texts)
            log_updates.append("Agent A (Extractor): PDF Decrypted Successfully. Sending scheme names to LLM for exact market mapping.")
        except Exception as e:
            errors.append(f"Failed to parse CAS PDF. Ensure password (PAN) is correct. Error: {str(e)}")
            return {"errors": errors, "log": log_updates}

    # 2. LLM Extraction
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
        structured_llm = llm.with_structured_output(PortfolioExtract)
        
        known_funds = ", ".join(MOCK_MARKET_DB.keys())
        prompt = f"""
        Extract the mutual fund investments from the following user portfolio text.
        For each investment, identify the exact fund name, invested amount, and current_value (if present).
        
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
    
    return {"investments": extracted_investments, "log": log_updates, "errors": errors, "transactions": transactions}

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
    transactions = state.get("transactions", [])
    
    analysis = AnalysisResult()
    
    total_invested = sum(inv.amount for inv in investments) if investments else 0.0
    current_val = sum((inv.current_value if inv.current_value else inv.amount * 1.25) for inv in investments) # Mock growth if no valuation
    
    analysis.total_value = total_invested
    analysis.current_valuation = current_val
    analysis.benchmark_xirr = 14.5 # Hardcoded NIFTY 50 5-Year Average Benchmark
    
    # XIRR Calculation
    if transactions and pyxirr:
        log_updates.append("Agent B (Analyst): Calculating exact XIRR using CAS transaction history...")
        try:
            dates = []
            amounts = []
            for t in transactions:
                if t.get("date") and t.get("amount"):
                    dates.append(pd.to_datetime(t["date"]).date())
                    amounts.append(-abs(float(t["amount"]))) # Outflow
            
            # Add current valuation as positive inflow today
            dates.append(datetime.now().date())
            amounts.append(current_val)
            
            xirr_val = pyxirr.xirr(dates, amounts)
            if xirr_val:
                analysis.portfolio_xirr = xirr_val * 100
        except Exception as e:
            log_updates.append(f"Agent B (Analyst): XIRR Math failed, falling back. Error: {e}")
            
    if analysis.portfolio_xirr is None and total_invested > 0:
        log_updates.append("Agent B (Analyst): Estimating XIRR from current valuation...")
        returns = current_val / total_invested
        analysis.portfolio_xirr = ((returns ** (1/3)) - 1) * 100 # Assuming roughly 3 years average hold
    
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
            
            if inv.sector and current_val > 0:
                allocation_weight = (inv.current_value if inv.current_value else (inv.amount * 1.25)) / current_val
                analysis.sector_allocation[inv.sector] = analysis.sector_allocation.get(inv.sector, 0.0) + (allocation_weight * 100)
            
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
        - Total Invested: ₹{analysis.total_value}
        - Current Valuation: ₹{analysis.current_valuation}
        - Portfolio XIRR: {analysis.portfolio_xirr:.2f}%
        - Benchmark NIFTY 50 XIRR: {analysis.benchmark_xirr:.2f}%
        - Total 5-Year Drag from High Expense Ratios: ₹{analysis.potential_savings}
        - Overlap Warnings:
        {overlap_info if overlap_info else "- None"}
        
        Task:
        1. Calculate a realistic 'Money Health Score' out of 100. Lower it if overlaps exist, if fees are high, or if Portfolio XIRR significantly underperforms the Benchmark 14.5% XIRR (minor penalty for underperformance).
        2. Write exactly 2-3 sentences of 'feedback' that sets a clear, trusted mentor tone. Explicitly reference their exact Portfolio XIRR vs the Benchmark if relevant!
        3. Provide 2-4 actionable 'rebalancing_steps' in simple language. If overlaps exist, tell them which funds to consolidate. If fees are high, suggest moving to specific Direct plans.
        """
        
        strategy = structured_llm.invoke(prompt)
        log_updates.append("Agent C (Strategist): Real-time Plan generated successfully.")
        
    except Exception as e:
        log_updates.append(f"Agent C (Strategist): LLM failed. Error: {str(e)}")
        strategy = StrategyPlan(
            health_score=50,
            feedback="We encountered a technical hurdle generating your mentor feedback. Please check your API keys.",
            rebalancing_steps=["Ensure your CAS PDF is valid and password protected."]
        )
        
    return {"strategy": strategy, "log": log_updates}
