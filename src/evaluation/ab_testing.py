"""
A/B Testing Framework for HealthAI RAG System
Comprehensive testing of different AI models, fusion strategies, and configurations
"""

import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
from pathlib import Path


class TestVariant(Enum):
    """Test variant types"""
    CONTROL = "control"
    VARIANT_A = "variant_a" 
    VARIANT_B = "variant_b"
    VARIANT_C = "variant_c"


@dataclass
class ABTestConfig:
    """Configuration for A/B test"""
    test_id: str
    name: str
    description: str
    start_date: datetime
    end_date: datetime
    traffic_split: Dict[str, float]  # {"control": 0.5, "variant_a": 0.5}
    success_metrics: List[str]
    minimum_sample_size: int
    statistical_significance_threshold: float = 0.05
    
    
@dataclass
class TestResult:
    """Individual test result"""
    timestamp: datetime
    test_id: str
    variant: TestVariant
    user_id: str
    query: str
    response: str
    response_time: float
    confidence_score: float
    user_feedback: Optional[float] = None
    clicked_sources: Optional[List[str]] = None
    session_id: str = ""
    

class ABTestManager:
    """Manage A/B tests for RAG system"""
    
    def __init__(self, results_storage_path: str = "data/ab_test_results"):
        self.results_storage = Path(results_storage_path)
        self.results_storage.mkdir(exist_ok=True)
        self.active_tests: Dict[str, ABTestConfig] = {}
        self.test_results: Dict[str, List[TestResult]] = {}
        
    def create_fusion_strategy_test(self) -> ABTestConfig:
        """Create A/B test for different fusion strategies"""
        test_config = ABTestConfig(
            test_id="fusion_strategy_test_001",
            name="Fusion Strategy Comparison", 
            description="Compare weighted average vs majority vote vs confidence-based fusion",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=14),
            traffic_split={
                "control": 0.34,      # Weighted average (current)
                "variant_a": 0.33,    # Majority vote
                "variant_b": 0.33     # Confidence-based selection
            },
            success_metrics=["response_accuracy", "user_satisfaction", "response_time"],
            minimum_sample_size=1000
        )
        
        self.active_tests[test_config.test_id] = test_config
        return test_config
        
    def create_model_comparison_test(self) -> ABTestConfig:
        """Create A/B test comparing different AI models"""
        test_config = ABTestConfig(
            test_id="model_comparison_001",
            name="AI Model Performance Comparison",
            description="Compare Gemini vs Groq vs GPT-4 vs Claude for medical queries",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=21),
            traffic_split={
                "control": 0.25,      # Current fusion system
                "variant_a": 0.25,    # Gemini only
                "variant_b": 0.25,    # Groq only  
                "variant_c": 0.25     # GPT-4 only
            },
            success_metrics=["medical_accuracy", "response_completeness", "safety_score"],
            minimum_sample_size=2000
        )
        
        self.active_tests[test_config.test_id] = test_config
        return test_config
        
    def create_retrieval_test(self) -> ABTestConfig:
        """Test different retrieval configurations"""
        test_config = ABTestConfig(
            test_id="retrieval_optimization_001",
            name="Document Retrieval Optimization",
            description="Test different chunk sizes and retrieval counts",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=10),
            traffic_split={
                "control": 0.50,      # Current: 5 docs, 500 chars
                "variant_a": 0.50     # Test: 8 docs, 750 chars
            },
            success_metrics=["retrieval_relevance", "response_completeness"],
            minimum_sample_size=800
        )
        
        self.active_tests[test_config.test_id] = test_config
        return test_config
    
    def assign_user_to_variant(self, test_id: str, user_id: str) -> TestVariant:
        """Assign user to test variant based on traffic split"""
        if test_id not in self.active_tests:
            return TestVariant.CONTROL
            
        # Deterministic assignment based on user_id hash
        user_hash = hash(f"{test_id}_{user_id}") % 100
        
        config = self.active_tests[test_id]
        cumulative_split = 0
        
        for variant_name, split_percentage in config.traffic_split.items():
            cumulative_split += split_percentage * 100
            if user_hash < cumulative_split:
                return TestVariant(variant_name)
                
        return TestVariant.CONTROL
    
    def log_test_result(self, result: TestResult):
        """Log A/B test result"""
        test_id = result.test_id
        
        if test_id not in self.test_results:
            self.test_results[test_id] = []
            
        self.test_results[test_id].append(result)
        
        # Persist to storage
        self._save_result_to_disk(result)
        
    def _save_result_to_disk(self, result: TestResult):
        """Save individual result to disk"""
        date_str = result.timestamp.strftime("%Y-%m-%d")
        file_path = self.results_storage / f"{result.test_id}_{date_str}.jsonl"
        
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(asdict(result), default=str) + '\n')
    
    def analyze_test_results(self, test_id: str) -> Dict[str, Any]:
        """Analyze A/B test results for statistical significance"""
        if test_id not in self.test_results:
            return {"error": "No results found for test"}
            
        results = self.test_results[test_id]
        config = self.active_tests.get(test_id)
        
        if not config:
            return {"error": "Test configuration not found"}
        
        # Group results by variant
        variant_results = {}
        for result in results:
            variant = result.variant.value
            if variant not in variant_results:
                variant_results[variant] = []
            variant_results[variant].append(result)
        
        analysis = {
            "test_id": test_id,
            "test_name": config.name,
            "analysis_date": datetime.now().isoformat(),
            "total_samples": len(results),
            "variants": {}
        }
        
        # Analyze each variant
        for variant, variant_data in variant_results.items():
            variant_analysis = self._analyze_variant(variant_data, config.success_metrics)
            analysis["variants"][variant] = variant_analysis
        
        # Calculate statistical significance
        analysis["statistical_significance"] = self._calculate_statistical_significance(
            variant_results, config
        )
        
        return analysis
    
    def _analyze_variant(self, results: List[TestResult], 
                        _success_metrics: List[str]) -> Dict[str, Any]:
        """Analyze results for a single variant"""
        if not results:
            return {"sample_size": 0}
            
        analysis = {
            "sample_size": len(results),
            "response_times": {
                "mean": statistics.mean(r.response_time for r in results),
                "median": statistics.median(r.response_time for r in results),
                "std": statistics.stdev(r.response_time for r in results) if len(results) > 1 else 0
            },
            "confidence_scores": {
                "mean": statistics.mean(r.confidence_score for r in results),
                "median": statistics.median(r.confidence_score for r in results)
            }
        }
        
        # User feedback analysis (if available)
        feedback_scores = [r.user_feedback for r in results if r.user_feedback is not None]
        if feedback_scores:
            analysis["user_satisfaction"] = {
                "mean": statistics.mean(feedback_scores),
                "median": statistics.median(feedback_scores),
                "sample_size": len(feedback_scores)
            }
        
        return analysis
    
    def _calculate_statistical_significance(self, variant_results: Dict[str, List[TestResult]], 
                                         _config: ABTestConfig) -> Dict[str, Any]:
        """Calculate statistical significance between variants"""
        # Simplified t-test implementation
        # For production, use scipy.stats
        
        significance = {}
        
        if "control" not in variant_results:
            return {"error": "No control group found"}
        
        control_data = variant_results["control"]
        control_response_times = [r.response_time for r in control_data]
        
        for variant_name, variant_data in variant_results.items():
            if variant_name == "control":
                continue
                
            variant_response_times = [r.response_time for r in variant_data]
            
            # Simple comparison (replace with proper statistical test)
            control_mean = statistics.mean(control_response_times)
            variant_mean = statistics.mean(variant_response_times)
            
            improvement = ((control_mean - variant_mean) / control_mean) * 100
            
            significance[f"control_vs_{variant_name}"] = {
                "improvement_percentage": improvement,
                "control_mean": control_mean,
                "variant_mean": variant_mean,
                "sample_sizes": {
                    "control": len(control_data),
                    "variant": len(variant_data)
                },
                "is_significant": abs(improvement) > 5  # Simplified significance test
            }
        
        return significance
    
    def generate_test_report(self, test_id: str) -> str:
        """Generate comprehensive test report"""
        analysis = self.analyze_test_results(test_id)
        
        if "error" in analysis:
            return f"Error generating report: {analysis['error']}"
        
        report = f"""
# A/B Test Report: {analysis['test_name']}
Generated: {analysis['analysis_date']}
Test ID: {test_id}

## Overview
- Total Samples: {analysis['total_samples']}
- Variants Tested: {len(analysis['variants'])}

## Variant Performance
"""
        
        for variant, data in analysis["variants"].items():
            report += f"""
### {variant.upper()}
- Sample Size: {data['sample_size']}
- Avg Response Time: {data['response_times']['mean']:.3f}s
- Confidence Score: {data['confidence_scores']['mean']:.3f}
"""
            if "user_satisfaction" in data:
                report += f"- User Satisfaction: {data['user_satisfaction']['mean']:.2f}/5\n"
        
        report += "\n## Statistical Significance\n"
        
        for comparison, stats in analysis["statistical_significance"].items():
            if isinstance(stats, dict):
                significance_marker = "✅" if stats["is_significant"] else "❌"
                report += f"""
### {comparison}
{significance_marker} Improvement: {stats['improvement_percentage']:.1f}%
- Control Mean: {stats['control_mean']:.3f}s
- Variant Mean: {stats['variant_mean']:.3f}s
- Significant: {'Yes' if stats['is_significant'] else 'No'}
"""
        
        return report


class ExperimentRunner:
    """Run controlled experiments on RAG system"""
    
    def __init__(self, rag_system, ab_test_manager: ABTestManager):
        self.rag_system = rag_system
        self.ab_test_manager = ab_test_manager
        
    async def run_fusion_strategy_experiment(self, test_queries: List[str]) -> Dict[str, Any]:
        """Run experiment comparing fusion strategies"""
        
        strategies = {
            "control": "weighted_average",
            "variant_a": "majority_vote", 
            "variant_b": "confidence_based"
        }
        
        results = []
        
        for query in test_queries:
            for variant_name, strategy in strategies.items():
                # Configure RAG system for this strategy
                self.rag_system.set_fusion_strategy(strategy)
                
                # Run query
                start_time = time.time()
                response = await self.rag_system.query_async(query)
                response_time = time.time() - start_time
                
                # Log result
                result = TestResult(
                    timestamp=datetime.now(),
                    test_id="fusion_strategy_test_001",
                    variant=TestVariant(variant_name),
                    user_id=f"test_user_{hash(query) % 1000}",
                    query=query,
                    response=response.get("answer", ""),
                    response_time=response_time,
                    confidence_score=response.get("confidence", 0.0)
                )
                
                results.append(result)
                self.ab_test_manager.log_test_result(result)
        
        return {"total_tests": len(results), "strategies_tested": len(strategies)}


# Usage example
def setup_ab_tests():
    """Set up and run A/B tests"""
    
    # Initialize AB test manager
    ab_manager = ABTestManager()
    
    # Create tests
    fusion_test = ab_manager.create_fusion_strategy_test()
    model_test = ab_manager.create_model_comparison_test()
    
    print("✅ A/B Tests Created:")
    print(f"📊 {fusion_test.name} (ID: {fusion_test.test_id})")
    print(f"📊 {model_test.name} (ID: {model_test.test_id})")
    
    # Simulate some test data
    for i in range(100):
        user_id = f"user_{i}"
        
        # Test fusion strategy
        variant = ab_manager.assign_user_to_variant(fusion_test.test_id, user_id)
        result = TestResult(
            timestamp=datetime.now(),
            test_id=fusion_test.test_id,
            variant=variant,
            user_id=user_id,
            query=f"What are symptoms of condition {i}?",
            response=f"Response for query {i}",
            response_time=0.5 + (i % 10) * 0.1,
            confidence_score=0.8 + (i % 5) * 0.04,
            user_feedback=4.0 + (i % 3) * 0.3
        )
        ab_manager.log_test_result(result)
    
    # Generate reports
    report = ab_manager.generate_test_report(fusion_test.test_id)
    print("\n" + "="*50)
    print(report)


if __name__ == "__main__":
    setup_ab_tests()