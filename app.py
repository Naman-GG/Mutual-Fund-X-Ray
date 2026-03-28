import streamlit as st
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
from workflow import build_workflow
from schema import PortfolioState

load_dotenv(override=True)

# SVG Icons (Lucide) replacing unprofessional emojis
SVG_WARN = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#F59E0B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px;"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>'
SVG_CHECK = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px;"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>'
SVG_INFO = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#8B5CF6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px;"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>'

st.set_page_config(page_title="ET MoneyMentor Pro", layout="wide", page_icon="📈")

# Pro-Max Design System: Glassmorphism, Fira Typings, Zero Emojis, No Layout Shifts
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Fira+Sans:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Fira Sans', sans-serif;
    }
    
    .main-header {
        background: -webkit-linear-gradient(45deg, #F59E0B, #DC143C);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
        font-size: 3.5rem;
        margin-bottom: 0px;
    }
    .sub-header {
        color: #94A3B8;
        font-weight: 300;
        margin-bottom: 2rem;
    }
    .metric-container {
        display: flex;
        gap: 1.5rem;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: rgba(15, 23, 42, 0.6);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-top: 4px solid #DC143C;
        border-radius: 12px;
        padding: 1.5rem;
        flex: 1;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        transition: all 0.25s ease;
        cursor: pointer;
    }
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.7);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-top: 4px solid #F59E0B;
    }
    .metric-title {
        color: #94A3B8;
        font-size: 1rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin-bottom: 0.5rem;
    }
    .metric-value-score, .metric-value-money, .metric-value-savings {
        font-family: 'Fira Code', monospace;
        font-size: 3rem;
        font-weight: 700;
        line-height: 1.2;
    }
    .metric-value-score { color: #8B5CF6; } /* Purple accent for score */
    .metric-value-money { color: #DC143C; } /* ET Crimson */
    .metric-value-savings { color: #10B981; } /* Emerald */
    
    .metric-subtitle {
        color: #64748B;
        font-size: 0.85rem;
        margin-top: 0.5rem;
    }
    
    .svg-container {
        display: flex;
        align-items: center;
        margin-bottom: 0.5rem;
        color: #F8FAFC;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-header'>ET MoneyMentor Pro</h1>", unsafe_allow_html=True)
st.markdown("<h3 class='sub-header'>Problem Statement 9: Modern Mutual Fund X-Ray Engine</h3>", unsafe_allow_html=True)

st.write("Welcome. This tool securely analyzes CAMS/KFintech parameters or raw text to reconstruct portfolios, calculate absolute True XIRR, and generate benchmark-adjusted strategies.")

tab1, tab2 = st.tabs(["Upload CAS PDF", "Paste Text Input"])

run_workflow = False
initial_state = {"raw_input": "", "pdf_bytes": None, "pdf_password": None, "investments": [], "errors": [], "log": [], "transactions": []}

with tab1:
    st.markdown(f"<div class='svg-container'>{SVG_INFO} <span>Securely encrypt your local CAMS or KFintech CAS PDF statement.</span></div>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload Statement Archive (.pdf)", type=["pdf"], label_visibility="collapsed")
    pdf_password = st.text_input("Decrypt Key (PAN Hash)", type="password")
    if st.button("Initialize PDF Protocol"):
        if uploaded_file and pdf_password:
            initial_state["pdf_bytes"] = uploaded_file.getvalue()
            initial_state["pdf_password"] = pdf_password
            run_workflow = True
        else:
            st.error("Authentication halted: File and Key required.")

with tab2:
    MOCK_TEXT = "I have invested ₹100,000 in UTI Mastershare , ₹75,000 in UTI Flexicap, and ₹30,000 in Axis Midcap. I also put ₹45,000 in Tata Smallcap."
    raw_input = st.text_area("Provide raw string context:", value=MOCK_TEXT, height=100)
    if st.button("Initialize Text Protocol"):
        if raw_input:
            initial_state["raw_input"] = raw_input
            run_workflow = True

if run_workflow:
    workflow_app = build_workflow()
    
    with st.expander("System Diagnostic Logs", expanded=True):
        st.info("Agentic pipeline active. Tracing node calls...")
        final_state = workflow_app.invoke(initial_state)
        
        for log_entry in final_state.get('log', []):
            parts = log_entry.split(':', 1)
            if len(parts) == 2:
                st.write(f"**{parts[0]}**:{parts[1]}")
            else:
                st.write(f"{log_entry}")
                
    if final_state and not final_state.get('errors', []):
        st.success("Reconstruction Complete.")
        
        analysis = final_state['analysis']
        strategy = final_state['strategy']
        
        xirr_display = f"{analysis.portfolio_xirr:,.2f}%" if analysis.portfolio_xirr is not None else "N/A"
        
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-card">
                <div class="metric-title">Money Health Score</div>
                <div class="metric-value-score">{strategy.health_score}<span style="font-size:1.5rem; color:#64748B;">/100</span></div>
            </div>
            <div class="metric-card">
                <div class="metric-title">Portfolio Valuation</div>
                <div class="metric-value-money">₹{analysis.current_valuation:,.0f}</div>
                <div class="metric-subtitle">Invested roughly ₹{analysis.total_value:,.0f}</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">True Portfolio XIRR</div>
                <div class="metric-value-savings">{xirr_display}</div>
                <div class="metric-subtitle">vs {analysis.benchmark_xirr:.1f}% Target Benchmark</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        st.subheader("Asset Reconstruction & Overlaps")
        vcol1, vcol2 = st.columns(2)
        
        with vcol1:
            alloc_data = [{"Sector": k, "Allocation": v} for k, v in analysis.sector_allocation.items()]
            if alloc_data:
                df_alloc = pd.DataFrame(alloc_data)
                fig_sunburst = px.sunburst(df_alloc, path=['Sector'], values='Allocation', 
                                           title="Sector Allocation Weighting",
                                           color_discrete_sequence=['#F59E0B', '#8B5CF6', '#DC143C', '#10B981'],
                                           template="plotly_dark")
                st.plotly_chart(fig_sunburst, use_container_width=True)
            
        with vcol2:
            inv_data = [{"Fund": inv.fund_name, "Amount": inv.amount, "Sector": inv.sector} for inv in final_state['investments']]
            if inv_data:
                df_inv = pd.DataFrame(inv_data)
                fig_bar = px.bar(df_inv, x='Fund', y='Amount', color='Sector', 
                                 title="Capital Deployment by Scheme",
                                 color_discrete_sequence=['#F59E0B', '#8B5CF6', '#DC143C', '#10B981'],
                                 template="plotly_dark")
                st.plotly_chart(fig_bar, use_container_width=True)
            
        st.divider()
        st.subheader("Strategist Recommendation Engine")
        
        # Inject custom SVG box for primary feedback instead of standard st.info matching new UI rules
        st.markdown(f"""
        <div style="background: rgba(139, 92, 246, 0.1); border-left: 4px solid #8B5CF6; padding: 1rem; border-radius: 4px; margin-bottom: 1.5rem;">
            {SVG_INFO} <span style="font-family: 'Fira Sans', sans-serif; color: #E2E8F0;">{strategy.feedback}</span>
        </div>
        """, unsafe_allow_html=True)
        
        col_warn, col_steps = st.columns(2)
        with col_warn:
            if analysis.overlap_warnings:
                st.markdown("<h4 style='color: #F8FAFC;'>Detected Overlaps & Overheads</h4>", unsafe_allow_html=True)
                for warning in analysis.overlap_warnings:
                    st.markdown(f"<div class='svg-container'>{SVG_WARN} <span>{warning}</span></div>", unsafe_allow_html=True)
            elif analysis.potential_savings > 1000:
                st.markdown(f"<div class='svg-container'>{SVG_WARN} <span>High Expense Ratio Overheads Detected! (~₹{analysis.potential_savings:,.0f} 5-year drag)</span></div>", unsafe_allow_html=True)
        
        with col_steps:
            if strategy.rebalancing_steps:
                st.markdown("<h4 style='color: #F8FAFC;'>Suggested Action Plan</h4>", unsafe_allow_html=True)
                for step in strategy.rebalancing_steps:
                    st.markdown(f"<div class='svg-container'>{SVG_CHECK} <span>{step}</span></div>", unsafe_allow_html=True)
                
    elif final_state and final_state.get('errors', []):
        st.error(f"Execution Terminated: {final_state.get('errors', [])}")
