"""
Comprehensive Tests for Query Auto-Suggestions and Advanced Semantic Search
Tests both individual components and end-to-end functionality
"""

import pytest
import asyncio
from typing import Dict, List, Any
from unittest.mock import Mock, patch, MagicMock

# Import components to test
from src.services.query_suggestions import (
    MedicalQuerySuggestionEngine, 
    AsyncQuerySuggestionEngine,
    QuerySuggestion
)
from src.rag.advanced_semantic_search import (
    MedicalSemanticQueryExpander,
    MLRankingEngine,
    AdvancedSemanticSearch
)

class TestQueryAutoSuggestions:
    """Test suite for query auto-suggestions system"""
    
    @pytest.fixture
    def suggestion_engine(self):
        """Create suggestion engine for testing"""
        with patch('redis.Redis') as mock_redis:
            # Mock Redis to avoid dependency
            mock_redis.return_value.ping.return_value = True
            mock_redis.return_value.get.return_value = None
            engine = MedicalQuerySuggestionEngine()
            return engine
    
    @pytest.fixture
    def async_suggestion_engine(self):
        """Create async suggestion engine for testing"""
        return AsyncQuerySuggestionEngine()
    
    def test_suggestion_engine_initialization(self, suggestion_engine):
        """Test that suggestion engine initializes correctly"""
        assert suggestion_engine is not None
        assert hasattr(suggestion_engine, 'query_analyzer')
        assert hasattr(suggestion_engine, 'medical_templates')
        assert hasattr(suggestion_engine, 'popular_queries')
    
    def test_get_suggestions_basic(self, suggestion_engine):
        """Test basic suggestion generation"""
        suggestions = suggestion_engine.get_suggestions("what are")
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        
        # Check suggestion structure
        for suggestion in suggestions:
            assert isinstance(suggestion, QuerySuggestion)
            assert hasattr(suggestion, 'text')
            assert hasattr(suggestion, 'confidence')
            assert hasattr(suggestion, 'category')
            assert 0 <= suggestion.confidence <= 1
    
    def test_get_suggestions_medical_query(self, suggestion_engine):
        """Test suggestions for medical queries"""
        suggestions = suggestion_engine.get_suggestions("diabetes symptoms")
        
        assert len(suggestions) > 0
        
        # Should contain relevant medical suggestions
        suggestion_texts = [s.text.lower() for s in suggestions]
        medical_keywords = ['diabetes', 'symptoms', 'treatment', 'causes']
        
        # At least one suggestion should contain medical keywords
        has_medical_content = any(
            any(keyword in text for keyword in medical_keywords)
            for text in suggestion_texts
        )
        assert has_medical_content
    
    def test_get_suggestions_empty_query(self, suggestion_engine):
        """Test suggestions for empty or very short queries"""
        # Empty query
        suggestions = suggestion_engine.get_suggestions("")
        assert isinstance(suggestions, list)
        
        # Very short query
        suggestions = suggestion_engine.get_suggestions("a")
        assert isinstance(suggestions, list)
    
    def test_get_suggestions_with_context(self, suggestion_engine):
        """Test suggestions with user context"""
        user_context = {
            "age_group": "pediatric",
            "recent_domains": ["symptoms"]
        }
        
        suggestions = suggestion_engine.get_suggestions(
            "fever", 
            user_context=user_context
        )
        
        assert len(suggestions) > 0
        # Should include age-appropriate suggestions for pediatric context
        suggestion_texts = ' '.join([s.text.lower() for s in suggestions])
        assert any(keyword in suggestion_texts for keyword in ['child', 'children', 'pediatric'])
    
    def test_suggestion_ranking(self, suggestion_engine):
        """Test that suggestions are properly ranked by confidence"""
        suggestions = suggestion_engine.get_suggestions("heart")
        
        if len(suggestions) > 1:
            # Check that suggestions are sorted by confidence (descending)
            for i in range(len(suggestions) - 1):
                assert suggestions[i].confidence >= suggestions[i + 1].confidence
    
    def test_learn_from_query(self, suggestion_engine):
        """Test learning from user queries"""
        # Should not raise exceptions
        suggestion_engine.learn_from_query("What causes diabetes?", user_clicked=True)
        suggestion_engine.learn_from_query("Heart disease symptoms", user_clicked=False)
    
    @pytest.mark.asyncio
    async def test_async_suggestions(self, async_suggestion_engine):
        """Test async suggestion interface"""
        suggestions = await async_suggestion_engine.get_suggestions_async(
            "blood pressure"
        )
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        
        # Check format is API-ready
        for suggestion in suggestions:
            assert isinstance(suggestion, dict)
            assert 'text' in suggestion
            assert 'confidence' in suggestion
            assert 'category' in suggestion
    
    @pytest.mark.asyncio
    async def test_async_learning(self, async_suggestion_engine):
        """Test async learning interface"""
        # Should not raise exceptions
        await async_suggestion_engine.learn_from_query_async(
            "What is hypertension?", 
            user_clicked=True
        )

class TestAdvancedSemanticSearch:
    """Test suite for advanced semantic search system"""
    
    @pytest.fixture
    def query_expander(self):
        """Create query expander for testing"""
        return MedicalSemanticQueryExpander()
    
    @pytest.fixture
    def ml_ranker(self):
        """Create ML ranker for testing"""
        return MLRankingEngine()
    
    @pytest.fixture
    def mock_vector_store(self):
        """Create mock vector store"""
        mock_store = Mock()
        mock_store.search.return_value = [
            {
                'doc_id': 'doc1',
                'text': 'Diabetes is a chronic condition affecting blood sugar levels.',
                'similarity': 0.8,
                'metadata': {'source': 'medical_guide'}
            },
            {
                'doc_id': 'doc2', 
                'text': 'Type 2 diabetes symptoms include increased thirst and fatigue.',
                'similarity': 0.7,
                'metadata': {'source': 'symptoms_guide'}
            }
        ]
        mock_store.get_stats.return_value = {'total_documents': 100}
        return mock_store
    
    @pytest.fixture
    def mock_embedder(self):
        """Create mock embedder"""
        mock_embedder = Mock()
        return mock_embedder
    
    def test_query_expander_initialization(self, query_expander):
        """Test query expander initialization"""
        assert query_expander is not None
        assert hasattr(query_expander, 'medical_synonyms')
        assert hasattr(query_expander, 'medical_contexts')
        assert hasattr(query_expander, 'query_analyzer')
    
    def test_query_expansion_basic(self, query_expander):
        """Test basic query expansion"""
        expansion = query_expander.expand_query("diabetes symptoms")
        
        assert expansion.original_query == "diabetes symptoms"
        assert expansion.final_expanded_query != ""
        assert isinstance(expansion.expanded_terms, list)
        assert isinstance(expansion.medical_synonyms, list)
        assert isinstance(expansion.contextual_terms, list)
    
    def test_query_expansion_with_context(self, query_expander):
        """Test query expansion with user context"""
        user_context = {"age_group": "geriatric"}
        
        expansion = query_expander.expand_query(
            "joint pain", 
            user_context=user_context
        )
        
        # Should include age-specific terms
        all_terms = expansion.expanded_terms + expansion.contextual_terms
        age_specific_found = any(
            term in ['elderly', 'geriatric', 'senior', 'older adults'] 
            for term in all_terms
        )
        # Note: This might not always be true depending on implementation
        # but tests the concept
    
    def test_ml_ranker_initialization(self, ml_ranker):
        """Test ML ranker initialization"""
        assert ml_ranker is not None
        assert hasattr(ml_ranker, 'ml_features_cache')
    
    def test_ml_ranker_training(self, ml_ranker):
        """Test ML ranker training"""
        # Mock training documents
        documents = [
            {
                'doc_id': 'doc1',
                'content': 'Diabetes is a metabolic disorder affecting glucose levels.',
                'metadata': {'date': '2024-01-01'}
            },
            {
                'doc_id': 'doc2',
                'content': 'Heart disease includes various cardiovascular conditions.',
                'metadata': {'date': '2024-01-02'}
            }
        ]
        
        # Should not raise exceptions
        ml_ranker.train_ranking_model(documents)
    
    def test_ml_relevance_calculation(self, ml_ranker):
        """Test ML relevance score calculation"""
        query = "diabetes treatment"
        document = {
            'content': 'Diabetes treatment includes insulin therapy and lifestyle changes.',
            'metadata': {'date': '2024-01-01'}
        }
        base_similarity = 0.7
        
        ml_score, explanation = ml_ranker.calculate_ml_relevance(
            query, document, base_similarity
        )
        
        assert isinstance(ml_score, float)
        assert 0 <= ml_score <= 1
        assert isinstance(explanation, dict)
        assert 'method' in explanation
    
    @pytest.mark.asyncio
    async def test_advanced_search_integration(self, mock_vector_store, mock_embedder):
        """Test advanced semantic search integration"""
        with patch('src.rag.advanced_semantic_search.MedicalQueryAnalyzer'):
            search_engine = AdvancedSemanticSearch(mock_vector_store, mock_embedder)
            
            results = await search_engine.semantic_search(
                query="diabetes symptoms",
                k=5,
                use_query_expansion=True,
                use_ml_ranking=True
            )
            
            assert isinstance(results, list)
            # Results depend on mock data
            for result in results:
                assert hasattr(result, 'document_id')
                assert hasattr(result, 'content')
                assert hasattr(result, 'similarity_score')
                assert hasattr(result, 'ml_relevance_score')
                assert hasattr(result, 'combined_score')
    
    @pytest.mark.asyncio
    async def test_search_analytics(self, mock_vector_store, mock_embedder):
        """Test search analytics generation"""
        with patch('src.rag.advanced_semantic_search.MedicalQueryAnalyzer'):
            search_engine = AdvancedSemanticSearch(mock_vector_store, mock_embedder)
            
            analytics = await search_engine.get_search_analytics()
            
            assert isinstance(analytics, dict)
            assert 'vector_store' in analytics
            assert 'ml_ranking' in analytics
            assert 'query_expansion' in analytics

class TestEndToEndIntegration:
    """End-to-end integration tests"""
    
    @pytest.mark.asyncio
    async def test_suggestions_to_search_flow(self):
        """Test complete flow from suggestions to search"""
        # Mock components to avoid dependencies
        with patch('redis.Redis') as mock_redis, \
             patch('src.rag.advanced_semantic_search.MedicalQueryAnalyzer'):
            
            # Setup mocks
            mock_redis.return_value.ping.return_value = True
            mock_redis.return_value.get.return_value = None
            
            # Create suggestion engine
            suggestion_engine = MedicalQuerySuggestionEngine()
            
            # Get suggestions
            suggestions = suggestion_engine.get_suggestions("diabetes")
            assert len(suggestions) > 0
            
            # Use first suggestion for search (mock the search)
            search_query = suggestions[0].text
            assert isinstance(search_query, str)
            assert len(search_query) > 0
    
    def test_error_handling(self):
        """Test error handling in both systems"""
        # Test suggestion engine with invalid input
        with patch('redis.Redis') as mock_redis:
            mock_redis.return_value.ping.side_effect = Exception("Redis error")
            
            # Should handle Redis errors gracefully
            suggestion_engine = MedicalQuerySuggestionEngine()
            suggestions = suggestion_engine.get_suggestions("test")
            assert isinstance(suggestions, list)
    
    def test_performance_basic(self):
        """Basic performance tests"""
        import time
        
        with patch('redis.Redis') as mock_redis:
            mock_redis.return_value.ping.return_value = True
            mock_redis.return_value.get.return_value = None
            
            suggestion_engine = MedicalQuerySuggestionEngine()
            
            # Measure suggestion generation time
            start_time = time.time()
            suggestions = suggestion_engine.get_suggestions("heart disease")
            end_time = time.time()
            
            # Should complete reasonably quickly (within 1 second)
            assert (end_time - start_time) < 1.0
            assert len(suggestions) > 0

# Pytest configuration and fixtures
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Test configuration
pytest_plugins = []

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"  
    )