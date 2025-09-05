# app_updated.py
import streamlit as st
import requests
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# === CONFIGURATION ===
API_BASE_URL = "http://127.0.0.1:8000"  # URL of your Flask API

# === PAGE CONFIGURATION ===
st.set_page_config(
    page_title="HR Sentiment Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === API HELPER FUNCTIONS ===
def get_api_status():
    """Check the status of the backend API."""
    try:
        response = requests.get(f"{API_BASE_URL}/status")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.sidebar.error(f"API connection failed: {e}")
        return None

def fetch_summary_data():
    """Fetch analytics summary from the API."""
    try:
        response = requests.get(f"{API_BASE_URL}/summary")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None

def fetch_employees_by_quadrant(quadrant_name):
    """Fetch employees filtered by quadrant from the API."""
    try:
        response = requests.get(f"{API_BASE_URL}/employees", params={'quadrant': quadrant_name})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        st.error(f"Failed to fetch employees for quadrant: {quadrant_name}")
        return []
        
def trigger_ai_analysis(query):
    """Send a query to the AI analysis endpoint."""
    try:
        response = requests.post(f"{API_BASE_URL}/analyze", json={'query': query})
        response.raise_for_status()
        return response.json().get('analysis', "No analysis content returned.")
    except requests.exceptions.RequestException as e:
        return f"❌ AI analysis failed: {e}"

# === UI HELPER FUNCTIONS ===
def display_employees(employees):
    """Display employees in a formatted table."""
    if not employees:
        st.info("No employees found in this category.")
        return
    
    for emp in employees:
        cols = st.columns([1, 2, 1, 6])
        cols[0].markdown(f"**ID:** {emp.get('id','-')}")
        cols[1].markdown(f"**Role:** {emp.get('role','-')}")
        cols[2].markdown(f"**Sentiment:** {emp.get('sentiment_score',0):.1f}%")
        cols[3].write(emp.get('content','-'))

# === MAIN APPLICATION ===
def main():
    st.title("📊 HR Sentiment Analysis with AI")
    st.markdown("**Advanced employee feedback analysis using API-driven insights**")

    # --- Sidebar and Initial Data Load ---
    with st.sidebar:
        st.subheader("🔧 System Status")
        status = get_api_status()
        if status and status.get("status") == "online":
            st.success("✅ API Connected")
            st.info(f"👥 {status.get('total_employees', 0)} employees loaded on server.")
        else:
            st.error("❌ API Offline. Please start the Flask server.")
            st.stop() # Stop the app if API is not available

    # --- Main Tabs ---
    tab1, tab2, tab3 = st.tabs(["📂 Data Management", "📊 Analytics Dashboard", "🤖 AI Analysis"])
    
    # --- Data Management Tab ---
    with tab1:
        st.header("📂 Data Management")
        summary = fetch_summary_data()
        if summary:
            col1, col2, col3 = st.columns(3)
            col1.metric("📊 Records Loaded", summary.get("total_employees", 0))
            col2.metric("😊 Average Sentiment", f"{summary.get('average_sentiment', 0):.1f}%")
            at_risk = summary.get("quadrant_distribution", {}).get("At Risk", 0)
            col3.metric("⚠️ At Risk Employees", at_risk)
        
        st.subheader("🔄 Refresh Data from MySQL")
        if st.button("🔄 Reload Data", type="primary", use_container_width=True):
            with st.spinner("Requesting data reload from server..."):
                try:
                    response = requests.post(f"{API_BASE_URL}/reload-data")
                    response.raise_for_status()
                    result = response.json()
                    if result.get("status") == "success":
                        st.success(result.get("message"))
                        st.rerun() # Rerun to refresh all data on the page
                    else:
                        st.warning(result.get("message"))
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Failed to reload: {e}")

    # --- Analytics Dashboard Tab ---
    with tab2:
        st.header("📊 Analytics Dashboard")
        summary = fetch_summary_data()
        if not summary:
            st.warning("Could not fetch summary data from API.")
        else:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("👥 Total Employees", summary['total_employees'])
            avg_sent = summary['average_sentiment']
            col2.metric("😊 Average Sentiment", f"{avg_sent:.1f}%", "Healthy" if avg_sent > 60 else "Needs Attention")
            col3.metric("🏆 Champions", summary['quadrant_distribution'].get('Champion', 0))
            col4.metric("⚠️ At Risk", summary['quadrant_distribution'].get('At Risk', 0))

            c1, c2 = st.columns(2)
            with c1:
                st.subheader("🥧 Employee Quadrant Distribution")
                quad_data = summary['quadrant_distribution']
                fig = px.pie(values=list(quad_data.values()), names=list(quad_data.keys()),
                             color_discrete_map={'Champion': '#28a745', 'Concerned but active': '#ffc107',
                                                 'Potentially Isolated': '#fd7e14', 'At Risk': '#dc3545'}, hole=0.4)
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)

            with c2:
                st.subheader("📊 Sentiment by Role")
                role_data = pd.DataFrame(list(summary['sentiment_by_role'].items()), columns=['Role', 'Sentiment'])
                sentiments = role_data['Sentiment']
                colors = ['#28a745' if s > 70 else '#ffc107' if s > 50 else '#dc3545' for s in sentiments]
                fig = go.Figure(go.Bar(x=role_data['Role'], y=sentiments, marker_color=colors, text=[f"{s:.1f}%" for s in sentiments], textposition='auto'))
                fig.update_layout(yaxis=dict(range=[0, 100]), height=400)
                st.plotly_chart(fig, use_container_width=True)

    # --- AI Analysis Tab ---
    with tab3:
        st.header("🤖 AI-Powered Analysis")
        button_cols = st.columns(4)
        
        if button_cols[0].button("🏆 Show Champions", key="qa_champions"):
            employees = fetch_employees_by_quadrant("Champion")
            st.subheader(f"🏆 Champion Employees ({len(employees)})")
            display_employees(employees)
            
        if button_cols[1].button("⚠️ Show At Risk", key="qa_at_risk"):
            employees = fetch_employees_by_quadrant("At Risk")
            st.subheader(f"⚠️ At Risk Employees ({len(employees)})")
            display_employees(employees)
            
        if button_cols[2].button("📈 Engagement Summary", key="qa_engagement"):
            with st.spinner("🧠 Analyzing engagement..."):
                query = "What is the overall employee engagement status and key factors affecting it?"
                result = trigger_ai_analysis(query)
                st.subheader("📈 Engagement Analysis")
                st.markdown(result)
                
        if button_cols[3].button("🎯 Retention Insights", key="qa_retention"):
            with st.spinner("🧠 Analyzing retention factors..."):
                query = "What factors might affect employee retention and what are your recommendations?"
                result = trigger_ai_analysis(query)
                st.subheader("🎯 Retention Analysis")
                st.markdown(result)

        st.subheader("💬 Ask Custom Questions")
        user_query = st.text_area("Enter your question:", height=100)
        if user_query and st.button("🤖 Analyze", key="custom_analysis"):
            with st.spinner("🤖 Generating AI insights..."):
                result = trigger_ai_analysis(user_query)
                st.subheader("🎯 AI Analysis Results")
                st.markdown(result)

if __name__ == "__main__":
    main()