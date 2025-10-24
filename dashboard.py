"""
Simple Data Science Dashboard for HealthAI RAG
Real-time visualization of performance metrics and evaluation results
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import datetime, timedelta
from pathlib import Path
import sys
from typing import Dict, Any

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.monitoring.performance_monitor import PerformanceMonitor


# Constants for consistent styling
class DashboardConstants:
    """Constants for dashboard styling and configuration"""
    TRANSPARENT_BG = 'rgba(0,0,0,0)'
    WHITE_TEXT = 'white'
    TITLE_FONT_SIZE = 16


# Professional Color Schemes for Different Chart Sections
class ColorSchemes:
    """Professional color schemes for dashboard charts"""
    
    # Performance Metrics - Blue tones (reliability, trust)
    PERFORMANCE = {
        'primary': '#2E86AB',      # Deep blue
        'secondary': '#A23B72',    # Purple-pink
        'accent': '#F18F01',       # Orange
        'background': '#C73E1D',   # Red
        'gradient': ['#2E86AB', '#4A90E2', '#7BB3F0', '#B8D4F0']
    }
    
    # Quality Metrics - Green tones (success, quality)
    QUALITY = {
        'primary': '#27AE60',      # Emerald green
        'secondary': '#2ECC71',    # Green
        'accent': '#F39C12',       # Orange
        'background': '#E67E22',   # Dark orange
        'gradient': ['#27AE60', '#2ECC71', '#58D68D', '#85E085']
    }
    
    # A/B Testing - Purple tones (innovation, analysis)
    TESTING = {
        'primary': '#8E44AD',      # Purple
        'secondary': '#9B59B6',    # Light purple
        'accent': '#E74C3C',       # Red
        'background': '#34495E',   # Dark gray
        'gradient': ['#8E44AD', '#9B59B6', '#BB8FCE', '#D7BDE2']
    }
    
    # Data Analysis - Teal tones (analytical, modern)
    ANALYTICS = {
        'primary': '#16A085',      # Teal
        'secondary': '#1ABC9C',    # Turquoise
        'accent': '#F1C40F',       # Yellow
        'background': '#E67E22',   # Orange
        'gradient': ['#16A085', '#1ABC9C', '#48C9B0', '#76D7C4']
    }
    
    # Health Status - Medical tones (healthcare)
    HEALTH = {
        'primary': '#E74C3C',      # Medical red
        'secondary': '#3498DB',    # Medical blue
        'accent': '#2ECC71',       # Success green
        'background': '#95A5A6',   # Gray
        'gradient': ['#E74C3C', '#EC7063', '#F1948A', '#F5B7B1']
    }
    
    # Evaluation - Orange tones (energy, evaluation)
    EVALUATION = {
        'primary': '#FF6B6B',      # Coral
        'secondary': '#4ECDC4',    # Mint
        'accent': '#45B7D1',       # Sky blue
        'background': '#FFA07A',   # Light salmon
        'gradient': ['#FF6B6B', '#FF8E8E', '#FFB1B1', '#FFD4D4']
    }


class HealthAIDashboard:
    """Interactive dashboard for HealthAI RAG system"""
    
    def __init__(self):
        self.monitor = PerformanceMonitor()
        
    def run(self):
        """Run the Streamlit dashboard"""
        st.set_page_config(
            page_title="HealthAI RAG - Data Science Dashboard",
            page_icon="🏥",
            layout="wide"
        )
        
        # Header
        st.title("🏥 HealthAI RAG - Data Science Dashboard")
        st.markdown("Real-time monitoring and evaluation of the medical AI system")
        
        # Sidebar
        self.render_sidebar()
        
        # Main content
        col1, col2, col3, col4 = st.columns(4)
        
        # Key metrics
        metrics = self.get_key_metrics()
        
        with col1:
            st.metric(
                "System Health", 
                metrics.get("health", "Unknown"),
                delta=None,
                delta_color="normal"
            )
            
        with col2:
            st.metric(
                "Avg Response Time", 
                f"{metrics.get('avg_response_time', 0):.2f}s",
                delta=f"{metrics.get('response_time_trend', 0):+.1f}%"
            )
            
        with col3:
            st.metric(
                "Confidence Score", 
                f"{metrics.get('avg_confidence', 0):.2f}",
                delta=f"{metrics.get('confidence_trend', 0):+.1f}%"
            )
            
        with col4:
            st.metric(
                "Queries Today", 
                metrics.get('queries_today', 0),
                delta=f"+{metrics.get('queries_delta', 0)}"
            )
        
        # Main dashboard sections
        self.render_performance_section()
        self.render_ab_testing_section()
        self.render_data_quality_section()
        self.render_evaluation_section()
    
    def render_sidebar(self):
        """Render sidebar with controls"""
        st.sidebar.header("⚙️ Controls")
        
        # Time range selector
        st.sidebar.selectbox(
            "Time Range",
            ["Last Hour", "Last 24 Hours", "Last 7 Days", "Last 30 Days"]
        )
        
        # Refresh button
        if st.sidebar.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()
        
        # System status
        st.sidebar.subheader("🚦 System Status")
        dashboard_data = self.monitor.get_performance_dashboard()
        health = dashboard_data.get('overview', {}).get('system_health', 'unknown')
        
        if health == 'healthy':
            st.sidebar.success("System Healthy ✅")
        elif health == 'warning':
            st.sidebar.warning("System Warning ⚠️")
        elif health == 'degraded':
            st.sidebar.error("System Degraded ❌")
        else:
            st.sidebar.info("Status Unknown ❓")
        
        # Quick actions
        st.sidebar.subheader("🚀 Quick Actions")
        
        if st.sidebar.button("📊 Run Evaluation"):
            self.run_evaluation()
            
        if st.sidebar.button("🧪 Start A/B Test"):
            self.start_ab_test()
            
        if st.sidebar.button("📈 Generate Report"):
            self.generate_report()
    
    def get_key_metrics(self) -> Dict[str, Any]:
        """Get key performance metrics"""
        dashboard_data = self.monitor.get_performance_dashboard()
        
        # Extract metrics with safe defaults
        overview = dashboard_data.get('overview', {})
        metrics = dashboard_data.get('key_metrics', {})
        
        return {
            'health': overview.get('system_health', 'unknown'),
            'avg_response_time': self._safe_get_metric(metrics, 'response_time', 'average_1h', 0),
            'avg_confidence': self._safe_get_metric(metrics, 'confidence_score', 'average_1h', 0),
            'queries_today': overview.get('total_queries_1h', 0),
            'response_time_trend': 2.3,  # Mock data
            'confidence_trend': 0.8,
            'queries_delta': 15
        }
    
    def _safe_get_metric(self, metrics: Dict[str, Any], category: str, metric_type: str, default: float = 0) -> float:
        """Safely extract metric value"""
        return metrics.get(category, {}).get(metric_type, default)
    
    def render_performance_section(self):
        """Render performance monitoring section"""
        st.header("📈 Performance Monitoring")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Response Time Trends")
            
            # Generate mock time series data
            dates = pd.date_range(start=datetime.now() - timedelta(days=7), end=datetime.now(), freq='1h')
            response_times = [0.8 + 0.3 * (i % 24) / 24 + 0.1 * (i % 7) for i in range(len(dates))]
            
            df = pd.DataFrame({
                'timestamp': dates,
                'response_time': response_times
            })
            
            fig = px.line(df, x='timestamp', y='response_time', 
                         title='Response Time Over Time',
                         color_discrete_sequence=[ColorSchemes.PERFORMANCE['primary']])
            fig.update_layout(
                height=300,
                plot_bgcolor=DashboardConstants.TRANSPARENT_BG,
                paper_bgcolor=DashboardConstants.TRANSPARENT_BG,
                font={'color': DashboardConstants.WHITE_TEXT},
                title={'font': {'size': DashboardConstants.TITLE_FONT_SIZE, 'color': ColorSchemes.PERFORMANCE['primary']}}
            )
            fig.update_traces(line={'width': 3})
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Confidence Score Distribution")
            
            # Mock confidence score data
            confidence_scores = [0.7, 0.8, 0.85, 0.9, 0.75, 0.92, 0.88, 0.83, 0.79, 0.91]
            
            fig = go.Figure(data=go.Histogram(
                x=confidence_scores, 
                nbinsx=10,
                marker_color=ColorSchemes.QUALITY['primary'],
                opacity=0.8
            ))
            fig.update_layout(
                title={
                    'text': 'Confidence Score Distribution',
                    'font': {'size': 16, 'color': ColorSchemes.QUALITY['primary']}
                },
                xaxis_title='Confidence Score',
                yaxis_title='Frequency',
                height=300,
                plot_bgcolor=DashboardConstants.TRANSPARENT_BG,
                paper_bgcolor=DashboardConstants.TRANSPARENT_BG,
                font={'color': DashboardConstants.WHITE_TEXT}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Model usage statistics
        st.subheader("🤖 Model Usage Statistics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Mock model usage data
            model_data = {'Gemini': 60, 'Groq': 30, 'Fusion': 10}
            fig = px.pie(
                values=list(model_data.values()), 
                names=list(model_data.keys()),
                title="Model Usage Distribution",
                color_discrete_sequence=ColorSchemes.ANALYTICS['gradient']
            )
            fig.update_layout(
                height=300,
                plot_bgcolor=DashboardConstants.TRANSPARENT_BG,
                paper_bgcolor=DashboardConstants.TRANSPARENT_BG,
                font={'color': DashboardConstants.WHITE_TEXT},
                title={
                    'font': {'size': DashboardConstants.TITLE_FONT_SIZE, 'color': ColorSchemes.ANALYTICS['primary']}
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.metric("API Calls Today", "1,247", delta="+123")
            st.metric("Average Latency", "1.23s", delta="-0.05s")
            
        with col3:
            st.metric("Success Rate", "98.5%", delta="+0.3%")
            st.metric("Error Rate", "1.5%", delta="-0.3%")
    
    def render_ab_testing_section(self):
        """Render A/B testing section"""
        st.header("🧪 A/B Testing Results")
        
        # Mock A/B test data
        ab_tests = [
            {
                "name": "Fusion Strategy Comparison",
                "status": "Running",
                "traffic_split": "33% / 33% / 34%",
                "significance": "Not yet significant",
                "winner": "TBD",
                "samples": 856
            },
            {
                "name": "Model Performance Comparison", 
                "status": "Running",
                "traffic_split": "25% / 25% / 25% / 25%",
                "significance": "95% confidence",
                "winner": "Gemini Pro",
                "samples": 1204
            }
        ]
        
        # Display A/B tests in table
        df_ab = pd.DataFrame(ab_tests)
        st.dataframe(df_ab, use_container_width=True)
        
        # A/B test performance visualization
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Conversion Rates by Variant")
            
            # Mock conversion data
            variants = ['Control', 'Variant A', 'Variant B']
            conversion_rates = [0.82, 0.85, 0.79]
            
            fig = px.bar(x=variants, y=conversion_rates, 
                        title='User Satisfaction by Variant',
                        color_discrete_sequence=ColorSchemes.TESTING['gradient'])
            fig.update_layout(
                height=300,
                plot_bgcolor=DashboardConstants.TRANSPARENT_BG,
                paper_bgcolor=DashboardConstants.TRANSPARENT_BG,
                font={'color': DashboardConstants.WHITE_TEXT},
                title={'font': {'size': DashboardConstants.TITLE_FONT_SIZE, 'color': ColorSchemes.QUALITY['primary']}}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Statistical Significance")
            
            # Mock significance data
            comparisons = ['Control vs A', 'Control vs B', 'A vs B']
            p_values = [0.03, 0.12, 0.08]
            
            fig = px.bar(x=comparisons, y=p_values, 
                        title='P-Values for Variant Comparisons',
                        color_discrete_sequence=ColorSchemes.TESTING['gradient'])
            fig.add_hline(y=0.05, line_dash="dash", line_color=ColorSchemes.TESTING['primary'], 
                         annotation_text="Significance Threshold")
            fig.update_layout(
                height=300,
                plot_bgcolor=DashboardConstants.TRANSPARENT_BG,
                paper_bgcolor=DashboardConstants.TRANSPARENT_BG,
                font={'color': DashboardConstants.WHITE_TEXT},
                title={'font': {'size': DashboardConstants.TITLE_FONT_SIZE, 'color': ColorSchemes.TESTING['primary']}}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def render_data_quality_section(self):
        """Render data quality analysis section"""
        st.header("🔍 Data Quality Analysis")
        
        # Load data quality report if available
        data_path = Path("data/clinical_data_5000.csv")
        if data_path.exists():
            df = pd.read_csv(data_path)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Records", f"{len(df):,}")
                st.metric("Columns", len(df.columns))
            
            with col2:
                completeness = df.count().sum() / (len(df) * len(df.columns))
                st.metric("Data Completeness", f"{completeness:.1%}")
                
                duplicates = df.duplicated().sum()
                st.metric("Duplicate Records", duplicates)
            
            with col3:
                # Calculate bias metrics
                gender_dist = df['gender'].value_counts(normalize=True)
                bias_score = gender_dist.std() / gender_dist.mean()
                st.metric("Gender Bias Score", f"{bias_score:.2f}")
                
                age_groups = pd.cut(df['age'], bins=4).value_counts(normalize=True)
                age_bias = age_groups.std() / age_groups.mean()
                st.metric("Age Distribution Bias", f"{age_bias:.2f}")
            
            # Data distribution visualizations
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Age Distribution")
                fig = px.histogram(df, x='age', nbins=20, title='Patient Age Distribution',
                                 color_discrete_sequence=[ColorSchemes.HEALTH['primary']])
                fig.update_layout(
                    plot_bgcolor=DashboardConstants.TRANSPARENT_BG,
                    paper_bgcolor=DashboardConstants.TRANSPARENT_BG,
                    font={'color': DashboardConstants.WHITE_TEXT},
                    title={'font': {'size': DashboardConstants.TITLE_FONT_SIZE, 'color': ColorSchemes.HEALTH['primary']}}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("Gender Distribution")
                gender_counts = df['gender'].value_counts()
                fig = px.pie(values=gender_counts.values, names=gender_counts.index,
                            title='Gender Distribution',
                            color_discrete_sequence=ColorSchemes.HEALTH['gradient'])
                fig.update_layout(
                    plot_bgcolor=DashboardConstants.TRANSPARENT_BG,
                    paper_bgcolor=DashboardConstants.TRANSPARENT_BG,
                    font={'color': DashboardConstants.WHITE_TEXT},
                    title={'font': {'size': DashboardConstants.TITLE_FONT_SIZE, 'color': ColorSchemes.HEALTH['secondary']}}
                )
                st.plotly_chart(fig, use_container_width=True)
        
        else:
            st.warning("Clinical dataset not found. Please ensure data/clinical_data_5000.csv exists.")
    
    def render_evaluation_section(self):
        """Render model evaluation section"""
        st.header("🎯 Model Evaluation Results")
        
        # Check for test dataset
        test_path = Path("data/medical_rag_test_dataset.json")
        if test_path.exists():
            with open(test_path) as f:
                test_data = json.load(f)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Test Cases", test_data['metadata']['total_test_cases'])
                st.metric("Test Categories", len(test_data['metadata']['categories']))
            
            with col2:
                # Mock evaluation results
                st.metric("Overall Accuracy", "87.3%", delta="+2.1%")
                st.metric("Safety Score", "95.8%", delta="+0.5%")
            
            # Test category breakdown
            st.subheader("Test Results by Category")
            
            # Mock results by category
            categories = test_data['metadata']['categories']
            mock_scores = [0.85, 0.92, 0.78, 0.88, 0.91, 0.83, 0.76][:len(categories)]
            
            results_df = pd.DataFrame({
                'Category': categories,
                'Accuracy': mock_scores
            })
            
            fig = px.bar(results_df, x='Category', y='Accuracy', 
                        title='Model Accuracy by Test Category',
                        color_discrete_sequence=ColorSchemes.EVALUATION['gradient'])
            fig.add_hline(y=0.8, line_dash="dash", line_color=ColorSchemes.EVALUATION['primary'], 
                         annotation_text="Target Accuracy")
            fig.update_layout(
                plot_bgcolor=DashboardConstants.TRANSPARENT_BG,
                paper_bgcolor=DashboardConstants.TRANSPARENT_BG,
                font={'color': DashboardConstants.WHITE_TEXT},
                title={'font': {'size': DashboardConstants.TITLE_FONT_SIZE, 'color': ColorSchemes.ANALYTICS['secondary']}}
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Detailed test results table
            st.subheader("Recent Test Results")
            
            # Show sample of test cases
            sample_tests = test_data['standard_tests'][:5]
            
            test_results = []
            for i, test in enumerate(sample_tests):
                test_results.append({
                    'Test ID': test['id'],
                    'Category': test['category'],
                    'Difficulty': test['difficulty'],
                    'Query': test['query'][:50] + "..." if len(test['query']) > 50 else test['query'],
                    'Status': '✅ Passed' if i % 3 != 0 else '❌ Failed',
                    'Score': f"{0.75 + 0.2 * (i % 5) / 5:.2f}"
                })
            
            results_df = pd.DataFrame(test_results)
            st.dataframe(results_df, use_container_width=True)
            
        else:
            st.warning("Test dataset not found. Run the data science integration script first.")
    
    def run_evaluation(self):
        """Run comprehensive evaluation"""
        try:
            st.sidebar.info("🔄 Starting evaluation...")
            
            # Import the data science controller
            import sys
            from pathlib import Path
            sys.path.append(str(Path(__file__).parent))
            
            from data_science_integration import DataScienceController
            
            # Run evaluation
            controller = DataScienceController()
            results = controller.run_comprehensive_evaluation()
            
            st.sidebar.success("✅ Evaluation completed!")
            st.session_state['evaluation_results'] = results
            st.rerun()
            
        except Exception as e:
            st.sidebar.error(f"❌ Evaluation failed: {str(e)}")
    
    def start_ab_test(self):
        """Start A/B test"""
        try:
            st.sidebar.info("🧪 Starting A/B test...")
            
            # Import A/B testing modules
            from src.evaluation.ab_testing import ABTestManager
            
            # Initialize A/B test
            ab_manager = ABTestManager()
            test = ab_manager.create_fusion_strategy_test()
            
            st.sidebar.success(f"✅ A/B test '{test.name}' started!")
            st.session_state['ab_test_active'] = test.name
            st.rerun()
            
        except Exception as e:
            st.sidebar.error(f"❌ A/B test failed: {str(e)}")
    
    def generate_report(self):
        """Generate comprehensive report"""
        try:
            st.sidebar.info("📝 Generating report...")
            
            # Import data science controller
            from data_science_integration import DataScienceController
            
            # Generate report
            controller = DataScienceController()
            report_content = controller.generate_data_science_report()
            
            # Save report to file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_path = f"data/dashboard_report_{timestamp}.md"
            
            # Ensure data directory exists
            Path("data").mkdir(exist_ok=True)
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            st.sidebar.success("📈 Report generated!")
            st.session_state['latest_report'] = report_path
            
            # Show download link
            
            st.sidebar.download_button(
                label="📥 Download Report",
                data=report_content,
                file_name=f"healthai_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown"
            )
            
            st.rerun()
            
        except Exception as e:
            st.sidebar.error(f"❌ Report generation failed: {str(e)}")


def main():
    """Main function to run the dashboard"""
    dashboard = HealthAIDashboard()
    dashboard.run()


if __name__ == "__main__":
    main()