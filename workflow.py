from langgraph.graph import StateGraph, END
from schema import PortfolioState
from agents import extractor_node, reflection_node, analyst_node, strategist_node

def build_workflow():
    workflow = StateGraph(PortfolioState)
    
    # Add nodes
    workflow.add_node("extractor", extractor_node)
    workflow.add_node("reflection", reflection_node)
    workflow.add_node("analyst", analyst_node)
    workflow.add_node("strategist", strategist_node)
    
    # Define edges
    workflow.set_entry_point("extractor")
    workflow.add_edge("extractor", "reflection")
    
    # Conditional logic based on reflection
    def reflection_router(state: PortfolioState):
        if state.get("errors"):
            return "end"
        return "continue"
        
    workflow.add_conditional_edges(
        "reflection",
        reflection_router,
        {
            "continue": "analyst",
            "end": END
        }
    )
    
    workflow.add_edge("analyst", "strategist")
    workflow.add_edge("strategist", END)
    
    return workflow.compile()
