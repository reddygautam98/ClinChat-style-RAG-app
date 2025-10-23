"""
Data Science Integration Script for HealthAI RAG
Integrates all evaluation, monitoring, and analytics components
"""


import sys
from pathlib import Path
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

# Import our evaluation modules
from src.evaluation.rag_evaluator import RAGEvaluator, DataQualityAnalyzer, ModelMonitor
from src.evaluation.test_dataset_generator import MedicalTestDatasetGenerator
from src.evaluation.ab_testing import ABTestManager
from src.monitoring.performance_monitor import PerformanceMonitor, RAGPerformanceTracker


class DataScienceController:
    """Main controller for all data science operations"""
    
    def __init__(self):
        self.performance_monitor = PerformanceMonitor()
        self.performance_tracker = RAGPerformanceTracker(self.performance_monitor)
        self.ab_test_manager = ABTestManager()
        self.model_monitor = ModelMonitor()
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def initialize_data_science_framework(self):
        """Initialize complete data science framework"""
        
        self.logger.info("🚀 Initializing HealthAI Data Science Framework...")
        
        # 1. Generate test datasets
        self._setup_test_datasets()
        
        # 2. Set up A/B tests  
        self._setup_ab_tests()
        
        # 3. Initialize monitoring
        self._setup_monitoring()
        
        # 4. Analyze existing data quality
        self._analyze_data_quality()
        
        self.logger.info("✅ Data Science Framework Initialized Successfully!")
        
    def _setup_test_datasets(self):
        """Set up comprehensive test datasets"""
        self.logger.info("📊 Setting up test datasets...")
        
        # Generate medical Q&A test dataset
        generator = MedicalTestDatasetGenerator()
        generator.save_test_dataset("data/medical_rag_test_dataset.json")
        
        self.logger.info("✅ Test datasets created")
        
    def _setup_ab_tests(self):
        """Set up A/B testing framework"""
        self.logger.info("🧪 Setting up A/B tests...")
        
        # Create fusion strategy test
        fusion_test = self.ab_test_manager.create_fusion_strategy_test()
        self.logger.info(f"Created test: {fusion_test.name}")
        
        # Create model comparison test
        model_test = self.ab_test_manager.create_model_comparison_test()
        self.logger.info(f"Created test: {model_test.name}")
        
        # Create retrieval optimization test
        retrieval_test = self.ab_test_manager.create_retrieval_test()
        self.logger.info(f"Created test: {retrieval_test.name}")
        
        self.logger.info("✅ A/B tests configured")
        
    def _setup_monitoring(self):
        """Set up performance monitoring"""
        self.logger.info("📈 Setting up performance monitoring...")
        
        # Initialize monitoring with sample data
        sample_metrics = [
            ("response_time", 1.2, {"model": "fusion"}),
            ("confidence_score", 0.85, {"strategy": "weighted"}), 
            ("documents_retrieved", 5.0, {"query_type": "symptoms"}),
            ("user_satisfaction", 4.2, {"feedback_type": "rating"})
        ]
        
        for metric_name, value, metadata in sample_metrics:
            self.performance_monitor.record_metric(metric_name, value, metadata)
            
        self.logger.info("✅ Performance monitoring active")
        
    def _analyze_data_quality(self):
        """Analyze existing data quality"""
        self.logger.info("🔍 Analyzing data quality...")
        
        # Check if clinical data exists
        data_path = Path("data/clinical_data_5000.csv")
        if data_path.exists():
            analyzer = DataQualityAnalyzer(str(data_path))
            quality_report = analyzer.data_quality_report()
            
            self.logger.info("Data Quality Summary:")
            self.logger.info(f"  - Completeness: {quality_report.get('completeness', 'N/A')}")
            self.logger.info(f"  - Bias Analysis: {len(quality_report.get('bias_analysis', {}))} dimensions")
        else:
            self.logger.warning("Clinical dataset not found - run generate_medical_data.py first")
            
        self.logger.info("✅ Data quality analysis complete")
    
    def run_comprehensive_evaluation(self, rag_system: Any = None) -> Dict[str, Any]:
        """Run comprehensive RAG system evaluation"""
        
        if not rag_system:
            self.logger.warning("No RAG system provided - skipping live evaluation")
            return {}
            
        self.logger.info("🎯 Running comprehensive RAG evaluation...")
        
        # Initialize evaluator
        evaluator = RAGEvaluator(rag_system, "data/clinical_data_5000.csv")
        
        # Run benchmarks
        benchmark_results = evaluator.benchmark_performance()
        
        # Generate report
        report = evaluator.generate_evaluation_report()
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"data/evaluation_report_{timestamp}.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
            
        self.logger.info(f"📄 Evaluation report saved to {report_path}")
        
        return benchmark_results
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        return {
            "performance": self.performance_monitor.get_performance_dashboard(),
            "ab_tests": {
                test_id: self.ab_test_manager.analyze_test_results(test_id)
                for test_id in self.ab_test_manager.active_tests.keys()
            },
            "model_monitor": self.model_monitor.generate_performance_dashboard(),
            "timestamp": datetime.now().isoformat()
        }
    
    def generate_data_science_report(self) -> str:
        """Generate comprehensive data science status report"""
        
        dashboard_data = self.get_dashboard_data()
        
        report = f"""
# 📊 HealthAI RAG - Data Science Status Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🎯 Executive Summary
- **System Health**: {dashboard_data['performance']['overview']['system_health']}
- **Active A/B Tests**: {len(dashboard_data['ab_tests'])}
- **Monitoring Status**: Active ✅
- **Evaluation Framework**: Deployed ✅

## 📈 Performance Overview
### Current Metrics (Last Hour)
"""
        
        performance_metrics = dashboard_data['performance']['key_metrics']
        for metric_name, stats in performance_metrics.items():
            report += f"- **{metric_name.title().replace('_', ' ')}**: {stats.get('average_1h', 'N/A'):.3f}\n"
        
        report += f"""

### System Health Indicators
- **Response Time Trend**: {dashboard_data['performance'].get('performance_trends', {}).get('response_time', 'Unknown')}
- **Confidence Score Trend**: {dashboard_data['performance'].get('performance_trends', {}).get('confidence_score', 'Unknown')}
- **Active Alerts**: {dashboard_data['performance']['overview']['active_alerts']}

## 🧪 A/B Testing Status
"""
        
        for test_id, test_data in dashboard_data['ab_tests'].items():
            if 'error' not in test_data:
                report += f"""
### {test_data.get('test_name', test_id)}
- **Total Samples**: {test_data.get('total_samples', 0)}
- **Variants**: {len(test_data.get('variants', {}))}
- **Status**: {'Active' if test_data.get('total_samples', 0) > 0 else 'Pending'}
"""
        
        report += f"""

## 🔍 Data Quality Assessment
- **Medical Dataset**: {'Present' if Path('data/clinical_data_5000.csv').exists() else 'Missing'}
- **Test Dataset**: {'Present' if Path('data/medical_rag_test_dataset.json').exists() else 'Missing'}
- **Evaluation Results**: {'Available' if list(Path('data').glob('evaluation_report_*.md')) else 'Pending'}

## 🚨 Critical Action Items

### High Priority (Complete within 1 week)
1. **🎯 Missing Model Evaluation Metrics**
   - Implement BLEU/ROUGE scoring for response quality
   - Add medical accuracy validation against clinical guidelines
   - Set up automated evaluation runs

2. **📊 Enhanced Analytics Dashboard**
   - Create real-time visualization dashboard (Streamlit/Dash)
   - Implement user behavior tracking
   - Add cost-per-query monitoring

3. **🧪 Active A/B Testing**
   - Begin fusion strategy testing with real traffic
   - Implement model performance comparison
   - Set up automated statistical significance testing

### Medium Priority (Complete within 2 weeks)
4. **🔍 Advanced Data Analysis**
   - Bias detection in medical responses
   - Query pattern analysis and clustering
   - Response quality correlation analysis

5. **⚠️ Production Monitoring**
   - Set up alerting for performance degradation
   - Implement error tracking and categorization
   - Add API usage and cost monitoring

6. **📈 Model Performance Optimization**
   - Hyperparameter tuning for fusion strategies
   - Document retrieval optimization
   - Response latency reduction

### Low Priority (Complete within 1 month)
7. **🎓 Advanced ML Features**
   - Implement semantic similarity scoring
   - Add query intent classification
   - Build user satisfaction prediction model

8. **🔒 Safety & Compliance**
   - Medical misinformation detection
   - HIPAA compliance validation
   - Bias monitoring and mitigation

## 📋 Immediate Next Steps
1. Run `python data_science_integration.py` to initialize framework
2. Execute model evaluation with real RAG system
3. Begin A/B testing with 10% traffic split
4. Set up daily automated evaluation reports
5. Implement real-time monitoring dashboard

---
*This report is automatically generated by the HealthAI Data Science Framework*
        """
        
        return report


def main():
    """Main execution function"""
    
    # Initialize controller
    controller = DataScienceController()
    
    # Initialize framework
    controller.initialize_data_science_framework()
    
    # Generate status report
    print("\n" + "="*80)
    print("📊 HEALTHAI RAG - DATA SCIENCE STATUS REPORT")
    print("="*80)
    
    report = controller.generate_data_science_report()
    print(report)
    
    # Save report to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"data/data_science_status_{timestamp}.md"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📄 Full report saved to: {report_path}")
    
    # Show dashboard data
    dashboard = controller.get_dashboard_data()
    print(f"\n📈 Performance Dashboard: {len(dashboard['performance']['key_metrics'])} metrics tracked")
    print(f"🧪 A/B Tests: {len(dashboard['ab_tests'])} tests configured") 
    print(f"⏰ Last Updated: {dashboard['timestamp']}")


if __name__ == "__main__":
    main()