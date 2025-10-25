"""
Analytics Dashboard for HealthAI
Real-time healthcare analytics with privacy protection
"""
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, Any, List
import streamlit as st
from src.analytics.user_analytics import UserAnalytics, EventType

class HealthAIAnalyticsDashboard:
    """Interactive analytics dashboard for healthcare application"""
    
    def __init__(self):
        self.analytics = UserAnalytics()
    
    def create_dashboard(self):
        """Create Streamlit analytics dashboard"""
        
        st.set_page_config(
            page_title="HealthAI Analytics Dashboard",
            page_icon="🏥",
            layout="wide"
        )
        
        st.title("🏥 HealthAI Analytics Dashboard")
        st.markdown("*Privacy-first analytics for healthcare GenAI application*")
        
        # Date range selector
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
        with col2:
            end_date = st.date_input("End Date", datetime.now())
        
        # Get analytics data
        analytics_data = self.analytics.get_user_analytics(
            start_date=datetime.combine(start_date, datetime.min.time()),
            end_date=datetime.combine(end_date, datetime.max.time()),
            aggregation="daily"
        )
        
        # Key Metrics Row
        st.subheader("📊 Key Performance Indicators")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Total Sessions",
                value=analytics_data.get('metrics', {}).get('total_sessions', 0),
                delta="12% vs last period"
            )
        
        with col2:
            st.metric(
                label="Medical Queries",
                value=analytics_data.get('metrics', {}).get('total_queries', 0),
                delta="8% vs last period"
            )
        
        with col3:
            avg_duration = analytics_data.get('metrics', {}).get('avg_session_duration_ms', 0)
            st.metric(
                label="Avg Session (min)",
                value=f"{avg_duration / 60000:.1f}",
                delta="-5% vs last period"
            )
        
        with col4:
            success_rate = analytics_data.get('metrics', {}).get('success_rate', 0)
            st.metric(
                label="Success Rate",
                value=f"{success_rate:.1%}",
                delta="2% vs last period"
            )
        
        # Charts Row 1
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("👥 Daily Active Users")
            self._create_daily_users_chart()
        
        with col2:
            st.subheader("📈 Query Volume Trend")
            self._create_query_volume_chart()
        
        # Charts Row 2
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("⚡ Response Time Distribution")
            self._create_response_time_chart()
        
        with col2:
            st.subheader("🛡️ Security Incidents")
            self._create_security_incidents_chart()
        
        # Medical Query Analysis
        st.subheader("🩺 Medical Query Analytics")
        self._create_medical_query_analysis()
        
        # User Journey Analysis
        st.subheader("🗺️ User Journey Analysis")
        self._create_user_journey_funnel()
        
    def _create_daily_users_chart(self):
        """Create daily active users chart"""
        # Sample data - would come from analytics
        dates = pd.date_range(start="2024-10-01", end="2024-10-24", freq='D')
        users = [45, 52, 48, 67, 71, 89, 95, 88, 92, 78, 85, 91, 97, 103, 89, 94, 98, 102, 87, 93, 99, 105, 91, 96]
        
        fig = px.line(
            x=dates, 
            y=users,
            title="Daily Active Users",
            labels={'x': 'Date', 'y': 'Active Users'}
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    def _create_query_volume_chart(self):
        """Create query volume trend chart"""
        # Sample data - would come from analytics
        hours = list(range(24))
        queries = [12, 8, 5, 3, 4, 6, 15, 28, 45, 52, 48, 55, 62, 58, 51, 47, 53, 49, 42, 35, 28, 22, 18, 14]
        
        fig = px.bar(
            x=hours,
            y=queries,
            title="Queries by Hour of Day",
            labels={'x': 'Hour', 'y': 'Query Count'}
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    def _create_response_time_chart(self):
        """Create response time distribution chart"""
        # Sample data - would come from analytics
        response_times = [1200, 1500, 980, 2100, 1800, 1400, 1600, 1300, 1700, 1900, 
                         1100, 1350, 1450, 1550, 1650, 1750, 1850, 1950, 2050, 1250]
        
        fig = px.histogram(
            x=response_times,
            nbins=10,
            title="Response Time Distribution (ms)",
            labels={'x': 'Response Time (ms)', 'y': 'Frequency'}
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    def _create_security_incidents_chart(self):
        """Create security incidents chart"""
        # Sample data - would come from analytics
        incident_types = ['PII Detected', 'Prompt Injection', 'Rate Limit', 'Invalid Input']
        counts = [5, 3, 12, 8]
        colors = ['red', 'orange', 'yellow', 'blue']
        
        fig = px.pie(
            values=counts,
            names=incident_types,
            title="Security Incidents (Last 7 Days)",
            color_discrete_sequence=colors
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    def _create_medical_query_analysis(self):
        """Create medical query analysis"""
        col1, col2 = st.columns(2)
        
        with col1:
            # Top medical topics
            topics = ['Diabetes', 'Hypertension', 'Symptoms', 'Medication', 'Prevention']
            counts = [45, 38, 52, 29, 34]
            
            fig = px.bar(
                x=counts,
                y=topics,
                orientation='h',
                title="Top Medical Topics",
                labels={'x': 'Query Count', 'y': 'Topic'}
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Query complexity distribution
            complexity = ['Simple', 'Moderate', 'Complex', 'Very Complex']
            percentages = [35, 40, 20, 5]
            
            fig = px.pie(
                values=percentages,
                names=complexity,
                title="Query Complexity Distribution"
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
    
    def _create_user_journey_funnel(self):
        """Create user journey funnel analysis"""
        stages = ['Session Start', 'Query Submitted', 'Response Received', 'Rating Given', 'Session End']
        users = [1000, 850, 820, 340, 780]
        
        fig = go.Figure(go.Funnel(
            y=stages,
            x=users,
            textinfo="value+percent initial"
        ))
        
        fig.update_layout(
            title="User Journey Funnel",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

def run_dashboard():
    """Run the analytics dashboard"""
    dashboard = HealthAIAnalyticsDashboard()
    dashboard.create_dashboard()

if __name__ == "__main__":
    run_dashboard()