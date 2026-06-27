import streamlit as st
import requests
import time

st.set_page_config(
    page_title="INTERLEV AI | Autonomous Recruitment",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional AI Theme CSS
st.markdown("""
<style>
:root {
    --ai-primary: #6366f1;
    --ai-secondary: #8b5cf6;
    --ai-accent: #06b6d4;
    --ai-dark: #0f172a;
    --ai-light: #f8fafc;
}

.stApp {
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
}

.main-header {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    color: white;
    padding: 2rem;
    border-radius: 15px;
    margin-bottom: 2rem;
    box-shadow: 0 10px 30px rgba(99, 102, 241, 0.3);
}

.ai-card {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(148, 163, 184, 0.1);
    border-radius: 15px;
    padding: 1.5rem;
    margin: 1rem 0;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
}

.agent-status {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem;
    background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
    border-radius: 10px;
    margin: 0.5rem 0;
    border-left: 4px solid #6366f1;
}

.status-indicator {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: #10b981;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.5; }
    100% { opacity: 1; }
}

.ai-button {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 10px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 14px 0 rgba(99, 102, 241, 0.3);
}

.ai-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px 0 rgba(99, 102, 241, 0.4);
}

.neural-bg {
    background-image:
        radial-gradient(circle at 25% 25%, rgba(99, 102, 241, 0.05) 0%, transparent 50%),
        radial-gradient(circle at 75% 75%, rgba(139, 92, 246, 0.05) 0%, transparent 50%);
}
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 1rem;">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">🧠</div>
        <h2 style="color: #6366f1; margin: 0;">INTERLEV AI</h2>
        <p style="color: #64748b; font-size: 0.9rem; margin: 0.5rem 0;">Autonomous Recruitment</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Agent Status
    st.markdown("### 🤖 AI Agents Status")
    agents = [
        {"name": "CV Parser", "status": "Ready", "color": "#10b981"},
        {"name": "Job Searcher", "status": "Ready", "color": "#3b82f6"},
        {"name": "AI Matcher", "status": "Ready", "color": "#8b5cf6"},
        {"name": "Application Generator", "status": "Ready", "color": "#f59e0b"}
    ]

    for agent in agents:
        st.markdown(f"""
        <div class="agent-status">
            <div>
                <strong>{agent['name']}</strong><br>
                <small style="color: #64748b;">{agent['status']}</small>
            </div>
            <div style="background: {agent['color']};" class="status-indicator"></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📊 System Health")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("API", "Online", "🟢")
    with col2:
        st.metric("DB", "Connected", "🟢")

# Main Content
st.markdown("""
<div class="main-header">
    <h1 style="font-size: 2.5rem; margin: 0; font-weight: 700;">Welcome to the Future of Recruitment</h1>
    <p style="font-size: 1.1rem; margin: 1rem 0 0 0; opacity: 0.9;">
        Our AI agents work autonomously to match candidates with perfect opportunities,
        streamlining the entire recruitment process with advanced machine learning.
    </p>
</div>
""", unsafe_allow_html=True)

# Stats Dashboard
st.markdown("## 📈 System Overview")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="ai-card">
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <div style="background: #eef2ff; padding: 0.5rem; border-radius: 8px; margin-right: 1rem;">
                👥
            </div>
            <div>
                <div style="font-size: 1.5rem; font-weight: bold; color: #1e293b;">0</div>
                <div style="font-size: 0.9rem; color: #64748b;">Active Candidates</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="ai-card">
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <div style="background: #f3e8ff; padding: 0.5rem; border-radius: 8px; margin-right: 1rem;">
                🧠
            </div>
            <div>
                <div style="font-size: 1.5rem; font-weight: bold; color: #1e293b;">0</div>
                <div style="font-size: 0.9rem; color: #64748b;">AI Matches</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="ai-card">
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <div style="background: #ecfeff; padding: 0.5rem; border-radius: 8px; margin-right: 1rem;">
                ⚡
            </div>
            <div>
                <div style="font-size: 1.5rem; font-weight: bold; color: #1e293b;">0</div>
                <div style="font-size: 0.9rem; color: #64748b;">Processing Queue</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="ai-card">
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <div style="background: #f0fdf4; padding: 0.5rem; border-radius: 8px; margin-right: 1rem;">
                💼
            </div>
            <div>
                <div style="font-size: 1.5rem; font-weight: bold; color: #1e293b;">0</div>
                <div style="font-size: 0.9rem; color: #64748b;">Jobs Discovered</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Main Action Section
st.markdown("## 🚀 Launch AI Recruitment")

col1, col2 = st.columns([2, 1])

with col1:
    uploaded_file = st.file_uploader(
        "Upload a candidate CV to begin autonomous processing",
        type=["pdf", "txt"],
        help="Supported formats: PDF and plain text files"
    )

    workflow_choice = st.radio(
        "Select AI Workflow:",
        ("🚀 Full Autonomous Pipeline (Celery)", "⚡ Legacy 5-Agent Orchestrator"),
        help="Choose between the new async AI pipeline or the original synchronous workflow"
    )

with col2:
    st.markdown("""
    <div class="ai-card">
        <h4 style="margin: 0 0 1rem 0; color: #1e293b;">💡 How it works</h4>
        <ol style="margin: 0; padding-left: 1rem; color: #64748b; font-size: 0.9rem;">
            <li>Upload candidate CV</li>
            <li>AI extracts profile data</li>
            <li>Autonomous job search</li>
            <li>Smart matching algorithm</li>
            <li>Generate applications</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

# Action Buttons
col1, col2 = st.columns(2)
with col1:
    if st.button("🧠 Launch AI Recruitment", type="primary", use_container_width=True):
        if uploaded_file is not None:
            with st.spinner('🤖 AI agents are processing your request...'):
                progress_bar = st.progress(0)
                status_text = st.empty()

                # Simulate AI processing steps
                steps = [
                    "Initializing AI agents...",
                    "Parsing CV with NLP...",
                    "Extracting candidate profile...",
                    "Searching freelance platforms...",
                    "Analyzing job requirements...",
                    "Computing match scores...",
                    "Generating applications...",
                    "Finalizing results..."
                ]

                for i, step in enumerate(steps):
                    time.sleep(0.8)
                    progress_bar.progress((i + 1) / len(steps))
                    status_text.text(f"🔄 {step}")

                st.success('✅ AI recruitment process completed successfully!')
                st.balloons()
        else:
            st.warning("⚠️ Please upload a CV file first")

with col2:
    if st.button("📊 View Agent Logs", use_container_width=True):
        st.info("🔍 Opening agent activity logs...")

# Agent Logs Section
st.markdown("---")
st.markdown("## 📋 AI Agent Activity Logs")

with st.expander("🔍 View Real-time Agent Logs", expanded=False):
    if st.button("🔄 Refresh Logs"):
        st.info("📡 Connecting to AI agent monitoring system...")

        # Mock agent logs
        logs = [
            {"agent": "CV Parser", "action": "Document Analysis", "status": "completed", "time": "2 seconds ago"},
            {"agent": "Profile Extractor", "action": "Skills Recognition", "status": "completed", "time": "1 second ago"},
            {"agent": "Job Searcher", "action": "Platform Scanning", "status": "in_progress", "time": "now"},
        ]

        for log in logs:
            status_color = {"completed": "🟢", "in_progress": "🟡", "failed": "🔴"}.get(log["status"], "⚪")
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.5rem; background: rgba(255,255,255,0.5); border-radius: 8px; margin: 0.25rem 0;">
                <div>
                    <strong>{status_color} {log['agent']}</strong> - {log['action']}
                </div>
                <small style="color: #64748b;">{log['time']}</small>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.write("Click 'Refresh Logs' to view current AI agent activities")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748b; font-size: 0.9rem;">
    <p>🧠 Powered by INTERLEV AI | Autonomous Recruitment Technology</p>
    <p>Built with advanced machine learning for the future of work</p>
</div>
""", unsafe_allow_html=True)
