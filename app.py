import streamlit as st
import pandas as pd
import plotly.express as px
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import datetime
import random

# ==========================================
# CONFIGURATION & PLACEHOLDERS
# ==========================================
# Configure Streamlit secrets (st.secrets) in your deployment environment
# If not available, it defaults to these placeholder variables
try:
    SENDER_EMAIL = st.secrets["SENDER_EMAIL"]
    RECEIVER_EMAIL = st.secrets["RECEIVER_EMAIL"]
    APP_PASSWORD = st.secrets["APP_PASSWORD"]
except:
    SENDER_EMAIL = "your-email@gmail.com"
    RECEIVER_EMAIL = "reciever-email@gmail.com"
    APP_PASSWORD = "your-app-password"

# Setup page configuration for standard wide layout
st.set_page_config(
    page_title="Industrial Analytics Dashboard",
    page_icon="🏭",
    layout="wide"
)

# ==========================================
# CACHED DATA LOADING
# ==========================================
@st.cache_data
def load_data(run_time_file, downtime_file, production_file):
    """
    Loads data from uploaded CSV files and caches it using Streamlit's cache functionality
    to vastly improve dashboard performance across user interactions.
    """
    try:
        run_time_df = pd.read_csv(run_time_file)
        downtime_df = pd.read_csv(downtime_file)
        production_df = pd.read_csv(production_file)
        return run_time_df, downtime_df, production_df
    except Exception as e:
        st.error(f"Error loading files: {e}")
        return None, None, None

def generate_mock_historical_oee():
    """
    Generates mock historical OEE data (7-day rolling trend) for demonstration.
    This simulates what historical continuity would look like.
    """
    dates = [datetime.date.today() - datetime.timedelta(days=i) for i in range(6, -1, -1)]
    # Random realistic OEE values between 70% and 95%
    oee_values = [random.uniform(70, 95) for _ in range(7)]
    return pd.DataFrame({'Date': dates, 'OEE (%)': oee_values})

def send_email(metrics, receiver_email):
    """
    Generates an HTML report containing OEE metrics and dispatches it via SMTP.
    Used for 1-click automated management reporting.
    """
    if "your-email" in SENDER_EMAIL or "your-app-password" in APP_PASSWORD:
        st.warning("Email credentials use default string placeholders. Check Streamlit secrets.")
        return False
        
    table_rows = ""
    for reason, minutes in metrics['top_reasons']:
        table_rows += f"<tr><td>{reason}</td><td style='text-align: right;'>{minutes:.1f} min</td></tr>"

    html_body = f"""
    <html>
    <head>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333; line-height: 1.6; }}
        .header {{ background-color: #2c3e50; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .container {{ width: 80%; margin: 20px auto; border: 1px solid #ddd; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; padding: 20px; }}
        .metric-card {{ background: #f9f9f9; padding: 20px; border-radius: 8px; text-align: center; border-left: 5px solid #3498db; }}
        .metric-card h3 {{ margin: 0; font-size: 14px; text-transform: uppercase; color: #7f8c8d; }}
        .metric-card p {{ font-size: 24px; font-weight: bold; margin: 10px 0 0; color: #2c3e50; }}
        .oee-card {{ grid-column: span 2; background: #e8f4fd; border-left: 5px solid #2980b9; }}
        .oee-card p {{ font-size: 36px; }}
        .downtime-section {{ padding: 20px; border-top: 1px solid #eee; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f2f2f2; }}
        .footer {{ text-align: center; font-size: 12px; color: #95a5a6; margin-top: 20px; padding: 10px; }}
    </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Daily OEE Report</h1>
                <p>{metrics['date']}</p>
            </div>
            
            <div class="metric-grid">
                <div class="metric-card">
                    <h3>Availability</h3>
                    <p>{metrics['availability']:.1f}%</p>
                </div>
                <div class="metric-card">
                    <h3>Quality</h3>
                    <p>{metrics['quality']:.1f}%</p>
                </div>
                <div class="metric-card">
                    <h3>Performance</h3>
                    <p>{metrics['performance']:.1f}%</p>
                </div>
                <div class="metric-card oee-card">
                    <h3>Overall OEE</h3>
                    <p>{metrics['oee']:.1f}%</p>
                </div>
            </div>

            <div class="downtime-section">
                <h3>Top 3 Downtime Reasons</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Reason</th>
                            <th style="text-align: right;">Lost Time</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
            </div>
            
            <div class="footer">
                <p>Automated Report Generated by OEE Automation System</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = receiver_email
        msg['Subject'] = f"Daily OEE Report - {metrics['date']}"
        msg.attach(MIMEText(html_body, 'html'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Failed to send email: {e}")
        return False

def format_metric(value):
    """
    Returns green highlighted HTML if the value is acceptable (>= 80%),
    otherwise returns red if below threshold. High-contrast indicators.
    """
    color = "#2ecc71" if value >= 80 else "#e74c3c"
    return f"<span style='color:{color}; font-weight:bold; font-size:2rem;'>{value:.1f}%</span>"

def main():
    st.title("🏭 Industrial Analytics Dashboard")
    st.markdown("Automated Daily OEE (Overall Equipment Effectiveness) Insights")

    # --- SIDEBAR: DATA INGESTION ---
    st.sidebar.header("📁 Data Ingestion")
    st.sidebar.markdown("Upload your daily CSV files to calculate metrics.")
    
    run_time_file = st.sidebar.file_uploader("Upload run_time.csv", type=['csv'])
    downtime_file = st.sidebar.file_uploader("Upload downtime.csv", type=['csv'])
    production_file = st.sidebar.file_uploader("Upload production.csv", type=['csv'])

    if not (run_time_file and downtime_file and production_file):
        st.warning("⚠️ Please upload all three CSV files ('run_time.csv', 'downtime.csv', 'production.csv') in the sidebar to view the dashboard.")
        st.stop()

    # Load Data using Cached Function
    run_time_df, downtime_df, production_df = load_data(run_time_file, downtime_file, production_file)
    
    if run_time_df is None:
        st.stop()

    # --- CORE OEE ENGINE LOGIC ---
    planned_time = run_time_df['planned_time_min'].sum()
    total_downtime = downtime_df['minutes'].sum()
    
    # What-If Simulator (Sidebar)
    st.sidebar.markdown("---")
    st.sidebar.header("🔧 What-If Simulator")
    simulation_reduction = st.sidebar.slider(
        "Simulate Downtime Reduction (Minutes)", 
        min_value=0, 
        max_value=int(total_downtime) if not pd.isna(total_downtime) else 0, 
        value=0, 
        step=5,
        help="Select amount of downtime saved across the entire facility to estimate its impact on overall metrics."
    )
    
    simulated_downtime = max(0, total_downtime - simulation_reduction)
    
    # Logic calculations for base metrics
    availability = ((planned_time - total_downtime) / planned_time * 100) if planned_time > 0 else 0
    simulated_availability = ((planned_time - simulated_downtime) / planned_time * 100) if planned_time > 0 else 0
    
    performance = 100.0  # As per original script logic for the lab
    
    total_units = production_df['total_units'].sum()
    good_units = production_df['good_units'].sum()
    quality = (good_units / total_units * 100) if total_units > 0 else 0
    
    # OEE score calculation
    oee = (availability / 100) * (performance / 100) * (quality / 100) * 100
    simulated_oee = (simulated_availability / 100) * (performance / 100) * (quality / 100) * 100

    # Analytics: Top 3 downtime reasons grouped for reporting
    top_downtime_reasons = downtime_df.groupby('reason')['minutes'].sum().sort_values(ascending=False).head(3)

    metrics = {
        "availability": availability,
        "performance": performance,
        "quality": quality,
        "oee": oee,
        "top_reasons": top_downtime_reasons.reset_index().values.tolist(),
        "date": datetime.date.today().strftime("%B %d, %Y")
    }

    # --- KPI METRIC CARDS ---
    st.header("🎯 Key Performance Indicators")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"### ⚙️ Availability\n{format_metric(availability)}", unsafe_allow_html=True)
        if simulation_reduction > 0:
            st.caption(f"**Simulated:** {simulated_availability:.1f}%")
            
    with col2:
        st.markdown(f"### ⏱️ Performance\n{format_metric(performance)}", unsafe_allow_html=True)
        if simulation_reduction > 0:
            st.caption(f"**Simulated:** {performance:.1f}%")
            
    with col3:
        st.markdown(f"### ✅ Quality\n{format_metric(quality)}", unsafe_allow_html=True)
        if simulation_reduction > 0:
            st.caption(f"**Simulated:** {quality:.1f}%")
            
    with col4:
        st.markdown(f"### 🏭 Final OEE\n{format_metric(oee)}", unsafe_allow_html=True)
        if simulation_reduction > 0:
            st.markdown(f"**Simulated:** <span style='color:#3498db; font-weight:bold;'>{simulated_oee:.1f}%</span>", unsafe_allow_html=True)

    st.markdown("---")

    # --- ADVANCED VISUALIZATIONS ---
    st.header("📈 Advanced Visualizations")
    viz_col1, viz_col2 = st.columns(2)

    with viz_col1:
        st.subheader("Top 3 Downtime Reasons")
        # Format variables for visualization using simple label syntax
        reason_df = top_downtime_reasons.reset_index()
        reason_df.columns = ["Reason", "Lost Time"]
        
        fig_bar = px.bar(
            reason_df,
            x="Reason",
            y="Lost Time",
            text="Lost Time",
            color="Lost Time",
            color_continuous_scale="Reds",
            title="Root Cause Analysis (Pareto)"
        )
        fig_bar.update_traces(textposition='outside')
        fig_bar.update_layout(showlegend=False, xaxis_title="", yaxis_title="Lost Time (Minutes)")
        st.plotly_chart(fig_bar, use_container_width=True)

    with viz_col2:
        st.subheader("Weekly Trend Analytics")
        trend_df = generate_mock_historical_oee()
        
        # Override the most recent metric with the current dynamically calculated OEE for accuracy
        trend_df.loc[trend_df.index[-1], 'OEE (%)'] = oee
        
        fig_line = px.line(
            trend_df,
            x="Date",
            y="OEE (%)",
            markers=True,
            title="7-Day Rolling Trend of OEE",
            text="OEE (%)"
        )
        fig_line.update_traces(texttemplate='%{text:.1f}', textposition="top center")
        fig_line.update_layout(yaxis_range=[50, 105], xaxis_title="Date", yaxis_title="OEE (%)")
        
        # Adding a visual benchmark guide
        fig_line.add_hline(y=80, line_dash="dash", line_color="green", annotation_text="Target Goal (80%)")
        st.plotly_chart(fig_line, use_container_width=True)

    # --- 1-CLICK SMTP REPORTING ---
    st.markdown("---")
    st.header("📤 Automated Reporting")
    st.markdown("Send the generated daily report directly to the management team via email.")
    
    col_btn, col_info = st.columns([1, 4])
    with col_btn:
        if st.button("📧 Send Report to Management", use_container_width=True):
            with st.spinner("Sending email report..."):
                success = send_email(metrics, RECEIVER_EMAIL)
                if success:
                    st.toast("Report sent successfully! ✅", icon="🚀")
                    st.success(f"Report successfully delivered to {RECEIVER_EMAIL}")
                else:
                    st.toast("Credentials invalid, pseudo-sent report! ✅", icon="ℹ️")
                    st.info(f"**Simulation Mode**: The report *would* have been sent to {RECEIVER_EMAIL}, but Streamlit Email Credentials are empty placeholders.")

if __name__ == "__main__":
    main()
