import streamlit as st
import pandas as pd
import plotly.express as px
from workflow import build_workflow
from schema import PortfolioState

# Economic Times Brand Colors Setup
ET_BLUE = "#003366"
ET_CRIMSON = "#DC143C"
ET_WHITE = "#FFFFFF"

st.set_page_config(page_title="ET MoneyMentor Pro", layout="wide", page_icon="📈")

# Custom CSS for Premium Dark Theme
st.markdown("""
    <style>
    .main-header {
        background: -webkit-linear-gradient(45deg, #00BFFF, #DC143C);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
        font-family: 'Inter', sans-serif;
        font-size: 3.5rem;
        margin-bottom: 0px;
    }
    .sub-header {
        color: #A0AEC0;
        font-family: 'Inter', sans-serif;
        font-weight: 300;
        margin-bottom: 2rem;
    }
    .metric-container {
        display: flex;
        gap: 1.5rem;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(145deg, #1A1C23, #121419);
        border: 1px solid #2A2D35;
        border-top: 4px solid #DC143C;
        border-radius: 12px;
        padding: 1.5rem;
        flex: 1;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        box-shadow: 0 10px 20px rgba(0,0,0,0.5);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 25px rgba(0,0,0,0.7);
    }
    .metric-title {
        color: #A0AEC0;
        font-size: 1rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin-bottom: 0.5rem;
    }
    .metric-value-score {
        color: #00BFFF;
        font-size: 3rem;
        font-weight: 800;
        line-height: 1.2;
    }
    .metric-value-money {
        color: #DC143C;
        font-size: 2.5rem;
        font-weight: 800;
        line-height: 1.2;
    }
    .metric-value-savings {
        color: #00FA9A;
        font-size: 2.5rem;
        font-weight: 800;
        line-height: 1.2;
    }
    .metric-subtitle {
        color: #718096;
        font-size: 0.8rem;
        margin-top: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-header'>ET MoneyMentor Pro</h1>", unsafe_allow_html=True)
st.markdown("<h3 class='sub-header'>Problem Statement 9: MF Portfolio X-Ray</h3>", unsafe_allow_html=True)

st.write("Welcome! This tool uses an Agentic Workflow to analyze your Mutual Fund portfolio, identify hidden overlaps, and suggest cost-saving rebalancing strategies.")

MOCK_TEXT = "I have invested ₹50,000 in SBI Bluechip, ₹75,000 in HDFC Top 100, and ₹30,000 in Axis Midcap. I also put ₹45,000 in Parag Parikh Flexi Cap."

raw_input = st.text_area("Paste your portfolio details or CAS text here:", value=MOCK_TEXT, height=100)

if st.button("Run Portfolio X-Ray"):
    workflow_app = build_workflow()
    initial_state = {"raw_input": raw_input, "investments": [], "errors": [], "log": []}
    
    with st.expander("🤖 Agent Thought Log", expanded=True):
        st.info("Executing LangGraph Multi-Agent Workflow...")
        # Execute workflow and trace logs
        final_state = workflow_app.invoke(initial_state)
        
        # Display logs
        for log_entry in final_state.get('log', []):
            parts = log_entry.split(':', 1)
            if len(parts) == 2:
                st.write(f"**{parts[0]}**:{parts[1]}")
            else:
                st.write(f"{log_entry}")
                
    if final_state and not final_state.get('errors', []):
        st.success("Analysis Complete!")
        
        # Dashboard Details using Flexbox Container
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-card">
                <div class="metric-title">Money Health Score</div>
                <div class="metric-value-score">{final_state['strategy'].health_score}<span style="font-size:1.5rem; color:#A0AEC0;">/100</span></div>
            </div>
            <div class="metric-card">
                <div class="metric-title">Total Portfolio Value</div>
                <div class="metric-value-money">₹{final_state['analysis'].total_value:,.0f}</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">5-Year Potential Savings</div>
                <div class="metric-value-savings">₹{final_state['analysis'].potential_savings:,.0f}</div>
                <div class="metric-subtitle">From optimizing expense ratios</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # Visuals
        st.subheader("Portfolio Composition & Overlap Analysis")
        vcol1, vcol2 = st.columns(2)
        
        with vcol1:
            # Sunburst Chart for Asset Allocation
            alloc_data = [{"Sector": k, "Allocation": v} for k, v in final_state['analysis'].sector_allocation.items()]
            if alloc_data:
                df_alloc = pd.DataFrame(alloc_data)
                fig_sunburst = px.sunburst(df_alloc, path=['Sector'], values='Allocation', 
                                           title="Sector Allocation",
                                           color_discrete_sequence=['#00BFFF', '#DC143C', '#4682B4', '#FFA07A'],
                                           template="plotly_dark")
                st.plotly_chart(fig_sunburst, use_container_width=True)
            
        with vcol2:
            # Bar Chart showing investments
            inv_data = [{"Fund": inv.fund_name, "Amount": inv.amount, "Sector": inv.sector} for inv in final_state['investments']]
            if inv_data:
                df_inv = pd.DataFrame(inv_data)
                fig_bar = px.bar(df_inv, x='Fund', y='Amount', color='Sector', 
                                 title="Fund Distribution",
                                 color_discrete_sequence=['#00BFFF', '#DC143C', '#4682B4', '#FFA07A'],
                                 template="plotly_dark")
                st.plotly_chart(fig_bar, use_container_width=True)
            
        # Overlap & Mentor Feedback
        st.divider()
        st.subheader("💡 Strategist Mentor Feedback")
        st.info(final_state['strategy'].feedback)
        
        if final_state['analysis'].overlap_warnings:
            st.warning("**Sector/Stock Overlap detected:**")
            for warning in final_state['analysis'].overlap_warnings:
                st.write(f"- ⚠️ {warning}")
                
        if final_state['strategy'].rebalancing_steps:
            st.markdown("### Suggested Rebalancing Steps")
            for step in final_state['strategy'].rebalancing_steps:
                st.write(f"- ✅ {step}")
                
    elif final_state and final_state.get('errors', []):
        st.error(f"Workflow halted with errors: {final_state.get('errors', [])}")
