from typing import List, Dict, Optional, TypedDict, Annotated
import operator
from pydantic import BaseModel, Field

class Investment(BaseModel):
    fund_name: str = Field(description="Name of the mutual fund")
    amount: float = Field(description="Invested amount")
    sector: Optional[str] = Field(default=None, description="Primary sector, e.g., Financials, Technology")
    expense_ratio: Optional[float] = Field(default=None, description="Expense ratio percentage")
    holdings: Optional[List[str]] = Field(default=None, description="Top stock holdings")

class AnalysisResult(BaseModel):
    overlap_warnings: List[str] = Field(default_factory=list, description="Warnings about sector or stock overlap")
    expense_ratio_drag: float = Field(default=0.0, description="Estimated drag due to high expense ratios")
    potential_savings: float = Field(default=0.0, description="Potential savings if moved to lower expense ratio funds")
    total_value: float = Field(default=0.0, description="Total portfolio value")
    sector_allocation: Dict[str, float] = Field(default_factory=dict, description="Allocation percentage per sector")

class StrategyPlan(BaseModel):
    health_score: int = Field(description="Money Health Score out of 100")
    feedback: str = Field(description="Encouraging mentor feedback")
    rebalancing_steps: List[str] = Field(description="Actionable steps to rebalance the portfolio")

class PortfolioState(TypedDict):
    raw_input: str
    investments: List[Investment]
    analysis: Optional[AnalysisResult]
    strategy: Optional[StrategyPlan]
    errors: Annotated[List[str], operator.add]
    log: Annotated[List[str], operator.add]
