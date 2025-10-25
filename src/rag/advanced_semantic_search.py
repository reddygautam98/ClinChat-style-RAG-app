"""
Advanced Semantic Search Enhancement for HealthAI RAG
ML-based ranking, contextual query expansion, and intelligent retrieval
"""

import os
import json
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import asyncio
from collections import defaultdict, Counter
import math

# ML imports for advanced features
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.cluster import KMeans
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn not available, using basic similarity")

from src.vectorstore.faiss_store import HealthAIVectorStore
from src.embeddings.openai_embed import HealthAIEmbedding
from src.analytics.medical_query_analyzer import MedicalQueryAnalyzer

logger = logging.getLogger(__name__)

@dataclass
class SemanticSearchResult:
    """Enhanced search result with ML-based features"""
    document_id: str
    content: str
    similarity_score: float
    ml_relevance_score: float
    combined_score: float
    metadata: Dict[str, Any]
    explanation: Dict[str, Any]  # Why this document was ranked highly
    semantic_matches: List[str]  # Key semantic matches found

@dataclass
class QueryExpansion:
    """Query expansion result"""
    original_query: str
    expanded_terms: List[str]
    medical_synonyms: List[str]
    contextual_terms: List[str]
    final_expanded_query: str

class MedicalSemanticQueryExpander:
    """Intelligent medical query expansion"""
    
    def __init__(self):
        """Initialize query expander with medical knowledge"""
        self.medical_synonyms = self._load_medical_synonyms()
        self.medical_contexts = self._load_medical_contexts()
        self.query_analyzer = MedicalQueryAnalyzer()
    
    def expand_query(self, 
                    query: str,
                    user_context: Optional[Dict[str, Any]] = None,
                    max_expansions: int = 5) -> QueryExpansion:
        """
        Expand medical query with synonyms and context
        
        Args:
            query: Original user query
            user_context: Optional user context for personalization
            max_expansions: Maximum number of expansion terms
            
        Returns:
            QueryExpansion object with expanded terms
        """
        try:
            # Analyze the original query
            analysis = self.query_analyzer.analyze_query(query)
            
            expanded_terms = []
            medical_synonyms = []
            contextual_terms = []
            
            # 1. Add medical synonyms for key terms
            for entity in analysis.medical_entities:
                synonyms = self._get_medical_synonyms(entity.lower())
                medical_synonyms.extend(synonyms[:2])  # Limit to 2 per entity
            
            # 2. Add contextual medical terms based on query intent
            if analysis.query_intent == "symptoms":
                contextual_terms.extend(["signs", "manifestations", "presentations", "indicators"])
            elif analysis.query_intent == "treatment":
                contextual_terms.extend(["therapy", "management", "intervention", "care"])
            elif analysis.query_intent == "diagnosis":
                contextual_terms.extend(["detection", "identification", "screening", "evaluation"])
            
            # 3. Add domain-specific expansions
            for domain in analysis.medical_domains:
                domain_terms = self._get_domain_expansions(domain.value)
                contextual_terms.extend(domain_terms[:2])
            
            # 4. Add user context expansions
            if user_context:
                age_group = user_context.get("age_group")
                if age_group:
                    contextual_terms.extend(self._get_age_specific_terms(age_group))
            
            # Combine and deduplicate
            all_expansions = list(set(medical_synonyms + contextual_terms))
            expanded_terms = all_expansions[:max_expansions]
            
            # Create final expanded query
            final_query = query
            if expanded_terms:
                final_query = f"{query} {' '.join(expanded_terms)}"
            
            return QueryExpansion(
                original_query=query,
                expanded_terms=expanded_terms,
                medical_synonyms=medical_synonyms[:max_expansions//2],
                contextual_terms=contextual_terms[:max_expansions//2],
                final_expanded_query=final_query
            )
            
        except Exception as e:
            logger.error(f"Query expansion failed: {e}")
            return QueryExpansion(
                original_query=query,
                expanded_terms=[],
                medical_synonyms=[],
                contextual_terms=[],
                final_expanded_query=query
            )
    
    def _get_medical_synonyms(self, term: str) -> List[str]:
        """Get medical synonyms for a term"""
        return self.medical_synonyms.get(term, [])
    
    def _get_domain_expansions(self, domain: str) -> List[str]:
        """Get domain-specific expansion terms"""
        expansions = {
            "symptoms": ["signs", "manifestations", "symptoms", "presentations"],
            "diagnosis": ["diagnostic", "identification", "detection", "screening"],
            "treatment": ["therapy", "management", "intervention", "treatment"],
            "medication": ["drugs", "pharmaceuticals", "medicines", "medications"],
            "prevention": ["prophylaxis", "prevention", "avoidance", "protection"],
            "emergency": ["urgent", "acute", "critical", "emergency"]
        }
        return expansions.get(domain, [])
    
    def _get_age_specific_terms(self, age_group: str) -> List[str]:
        """Get age-specific medical terms"""
        age_terms = {
            "pediatric": ["children", "pediatric", "infant", "child"],
            "geriatric": ["elderly", "geriatric", "senior", "older adults"],
            "adult": ["adult", "grown-up"]
        }
        return age_terms.get(age_group, [])
    
    def _load_medical_synonyms(self) -> Dict[str, List[str]]:
        """Load medical synonym dictionary"""
        return {
            "diabetes": ["diabetes mellitus", "hyperglycemia", "blood sugar disorder"],
            "hypertension": ["high blood pressure", "elevated BP", "arterial hypertension"],
            "myocardial infarction": ["heart attack", "MI", "cardiac arrest"],
            "cerebrovascular accident": ["stroke", "CVA", "brain attack"],
            "pneumonia": ["lung infection", "pulmonary infection", "chest infection"],
            "asthma": ["bronchial asthma", "reactive airway", "breathing difficulty"],
            "depression": ["major depression", "depressive disorder", "mood disorder"],
            "anxiety": ["anxiety disorder", "nervousness", "worry", "panic"],
            "arthritis": ["joint inflammation", "joint pain", "rheumatoid arthritis"],
            "migraine": ["severe headache", "vascular headache", "migraine headache"],
            "pain": ["ache", "discomfort", "soreness", "tenderness"],
            "fever": ["pyrexia", "elevated temperature", "hyperthermia"],
            "fatigue": ["tiredness", "exhaustion", "weakness", "lethargy"],
            "nausea": ["queasiness", "stomach upset", "morning sickness"],
            "dizziness": ["vertigo", "lightheadedness", "spinning sensation"]
        }
    
    def _load_medical_contexts(self) -> Dict[str, List[str]]:
        """Load medical context mappings"""
        return {
            "cardiovascular": ["heart", "blood pressure", "circulation", "cardiac"],
            "respiratory": ["breathing", "lungs", "airways", "pulmonary"],
            "neurological": ["brain", "nervous system", "neurologic", "mental"],
            "gastrointestinal": ["stomach", "digestive", "intestinal", "gastric"],
            "endocrine": ["hormonal", "metabolic", "glandular", "endocrine"],
            "musculoskeletal": ["bone", "joint", "muscle", "skeletal"]
        }

class MLRankingEngine:
    """Machine Learning-based ranking for search results"""
    
    def __init__(self):
        """Initialize ML ranking components"""
        self.tfidf_vectorizer = None
        self.document_corpus = []
        self.ml_features_cache = {}
        
        if SKLEARN_AVAILABLE:
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2)
            )
        
    def train_ranking_model(self, documents: List[Dict[str, Any]]):
        """
        Train ML ranking model on document corpus
        
        Args:
            documents: List of documents for training
        """
        if not SKLEARN_AVAILABLE:
            logger.warning("scikit-learn not available, skipping ML training")
            return
        
        try:
            # Extract text content from documents
            self.document_corpus = [doc.get('content', '') for doc in documents]
            
            if len(self.document_corpus) < 2:
                logger.warning("Insufficient documents for ML training")
                return
            
            # Train TF-IDF vectorizer
            self.tfidf_vectorizer.fit(self.document_corpus)
            
            # Pre-compute document vectors for efficiency
            doc_vectors = self.tfidf_vectorizer.transform(self.document_corpus)
            
            # Cache document features
            for i, doc in enumerate(documents):
                doc_id = doc.get('doc_id', str(i))
                self.ml_features_cache[doc_id] = {
                    'tfidf_vector': doc_vectors[i],
                    'content_length': len(doc.get('content', '')),
                    'title_length': len(doc.get('title', '')),
                    'metadata': doc.get('metadata', {})
                }
            
            logger.info(f"Trained ML ranking model on {len(documents)} documents")
            
        except Exception as e:
            logger.error(f"ML ranking training failed: {e}")
    
    def calculate_ml_relevance(self, 
                              query: str, 
                              document: Dict[str, Any],
                              base_similarity: float) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate ML-based relevance score
        
        Args:
            query: User query
            document: Document to score
            base_similarity: Base similarity score from vector search
            
        Returns:
            Tuple of (ml_score, explanation_dict)
        """
        if not SKLEARN_AVAILABLE or not self.tfidf_vectorizer:
            return base_similarity, {"method": "fallback", "reason": "ML not available"}
        
        try:
            # Get TF-IDF similarity
            query_vector = self.tfidf_vectorizer.transform([query])
            doc_content = document.get('content', '')
            doc_vector = self.tfidf_vectorizer.transform([doc_content])
            
            tfidf_similarity = cosine_similarity(query_vector, doc_vector)[0][0]
            
            # Calculate feature scores
            features = self._calculate_document_features(query, document)
            
            # Weighted combination of features
            weights = {
                'tfidf_similarity': 0.4,
                'content_quality': 0.2,
                'freshness': 0.1,
                'medical_specificity': 0.2,
                'query_alignment': 0.1
            }
            
            ml_score = (
                tfidf_similarity * weights['tfidf_similarity'] +
                features['content_quality'] * weights['content_quality'] +
                features['freshness'] * weights['freshness'] +
                features['medical_specificity'] * weights['medical_specificity'] +
                features['query_alignment'] * weights['query_alignment']
            )
            
            # Combine with base similarity (ensemble approach)
            final_score = (base_similarity * 0.6) + (ml_score * 0.4)
            
            explanation = {
                "method": "ml_ranking",
                "tfidf_similarity": round(tfidf_similarity, 3),
                "features": features,
                "weights": weights,
                "final_score": round(final_score, 3)
            }
            
            return final_score, explanation
            
        except Exception as e:
            logger.error(f"ML relevance calculation failed: {e}")
            return base_similarity, {"method": "fallback", "error": str(e)}
    
    def _calculate_document_features(self, query: str, document: Dict[str, Any]) -> Dict[str, float]:
        """Calculate various document quality features"""
        content = document.get('content', '')
        metadata = document.get('metadata', {})
        
        features = {}
        
        # Content quality (based on length, structure, etc.)
        content_length = len(content)
        features['content_quality'] = min(1.0, content_length / 1000)  # Normalize by 1000 chars
        
        # Freshness (if date available)
        doc_date = metadata.get('date')
        if doc_date:
            try:
                doc_datetime = datetime.fromisoformat(doc_date)
                days_old = (datetime.now() - doc_datetime).days
                features['freshness'] = max(0.1, 1.0 - (days_old / 365))  # Decay over year
            except:
                features['freshness'] = 0.5  # Default for unparseable dates
        else:
            features['freshness'] = 0.5  # Default when no date
        
        # Medical specificity (count of medical terms)
        medical_terms = [
            'diagnosis', 'treatment', 'symptoms', 'medication', 'therapy',
            'disease', 'condition', 'patient', 'clinical', 'medical'
        ]
        medical_count = sum(1 for term in medical_terms if term in content.lower())
        features['medical_specificity'] = min(1.0, medical_count / 10)
        
        # Query alignment (simple keyword matching)
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())
        overlap = len(query_words.intersection(content_words))
        features['query_alignment'] = min(1.0, overlap / len(query_words)) if query_words else 0.0
        
        return features

class AdvancedSemanticSearch:
    """Advanced semantic search with ML ranking and query expansion"""
    
    def __init__(self, 
                 vector_store: HealthAIVectorStore,
                 embedder: HealthAIEmbedding):
        """
        Initialize advanced semantic search
        
        Args:
            vector_store: Vector store for similarity search
            embedder: Embedding model for query processing
        """
        self.vector_store = vector_store
        self.embedder = embedder
        self.query_expander = MedicalSemanticQueryExpander()
        self.ml_ranker = MLRankingEngine()
        
        # Search configuration
        self.default_k = 10  # Retrieve more for re-ranking
        self.final_k = 5     # Return fewer after ML ranking
        
        logger.info("Advanced semantic search initialized")
    
    async def semantic_search(self,
                            query: str,
                            k: int = 5,
                            use_query_expansion: bool = True,
                            use_ml_ranking: bool = True,
                            user_context: Optional[Dict[str, Any]] = None) -> List[SemanticSearchResult]:
        """
        Perform advanced semantic search with ML ranking
        
        Args:
            query: User query
            k: Number of results to return
            use_query_expansion: Whether to expand the query
            use_ml_ranking: Whether to use ML-based re-ranking
            user_context: Optional user context for personalization
            
        Returns:
            List of ranked semantic search results
        """
        try:
            # Step 1: Query expansion
            expanded_query = query
            query_expansion = None
            
            if use_query_expansion:
                query_expansion = self.query_expander.expand_query(
                    query, 
                    user_context=user_context
                )
                expanded_query = query_expansion.final_expanded_query
                logger.info(f"Expanded query: '{expanded_query}'")
            
            # Step 2: Vector similarity search (get more results for re-ranking)
            search_k = max(self.default_k, k * 2) if use_ml_ranking else k
            
            # Use expanded query for vector search
            vector_results = self.vector_store.search(
                query=expanded_query,
                embedder=self.embedder,
                k=search_k,
                threshold=0.1
            )
            
            if not vector_results:
                logger.info("No vector results found")
                return []
            
            # Step 3: ML-based re-ranking (if enabled)
            enhanced_results = []
            
            for i, result in enumerate(vector_results):
                try:
                    # Calculate ML relevance score
                    ml_score = result.get('similarity', 0.0)
                    explanation = {"method": "vector_only"}
                    
                    if use_ml_ranking:
                        ml_score, explanation = self.ml_ranker.calculate_ml_relevance(
                            query=query,  # Use original query for ML scoring
                            document=result,
                            base_similarity=result.get('similarity', 0.0)
                        )
                    
                    # Calculate combined score
                    vector_sim = result.get('similarity', 0.0)
                    combined_score = (vector_sim * 0.6) + (ml_score * 0.4)
                    
                    # Extract semantic matches
                    semantic_matches = self._extract_semantic_matches(
                        query, 
                        result.get('text', ''),
                        query_expansion
                    )
                    
                    # Create enhanced result
                    enhanced_result = SemanticSearchResult(
                        document_id=result.get('doc_id', str(i)),
                        content=result.get('text', ''),
                        similarity_score=vector_sim,
                        ml_relevance_score=ml_score,
                        combined_score=combined_score,
                        metadata=result.get('metadata', {}),
                        explanation=explanation,
                        semantic_matches=semantic_matches
                    )
                    
                    enhanced_results.append(enhanced_result)
                    
                except Exception as e:
                    logger.error(f"Error processing result {i}: {e}")
                    continue
            
            # Step 4: Sort by combined score and return top k
            enhanced_results.sort(key=lambda x: x.combined_score, reverse=True)
            final_results = enhanced_results[:k]
            
            logger.info(f"Returned {len(final_results)} enhanced semantic search results")
            
            return final_results
            
        except Exception as e:
            logger.error(f"Advanced semantic search failed: {e}")
            return []
    
    def _extract_semantic_matches(self, 
                                query: str, 
                                content: str,
                                query_expansion: Optional[QueryExpansion]) -> List[str]:
        """Extract key semantic matches between query and content"""
        matches = []
        
        query_words = set(query.lower().split())
        content_lower = content.lower()
        
        # Direct word matches
        for word in query_words:
            if word in content_lower:
                matches.append(f"Direct: {word}")
        
        # Expansion matches
        if query_expansion:
            for term in query_expansion.expanded_terms:
                if term.lower() in content_lower:
                    matches.append(f"Expanded: {term}")
        
        return matches[:5]  # Limit to top 5 matches
    
    async def train_ml_ranking(self, documents: List[Dict[str, Any]]):
        """
        Train ML ranking model on document corpus
        
        Args:
            documents: List of documents for training
        """
        try:
            logger.info(f"Training ML ranking model on {len(documents)} documents")
            
            # Run training in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, 
                self.ml_ranker.train_ranking_model, 
                documents
            )
            
            logger.info("ML ranking model training completed")
            
        except Exception as e:
            logger.error(f"ML ranking training failed: {e}")
    
    async def get_search_analytics(self) -> Dict[str, Any]:
        """Get analytics about search performance"""
        try:
            # Get vector store stats
            vector_stats = self.vector_store.get_stats()
            
            analytics = {
                "vector_store": vector_stats,
                "ml_ranking": {
                    "enabled": SKLEARN_AVAILABLE,
                    "trained": self.ml_ranker.tfidf_vectorizer is not None,
                    "features_cached": len(self.ml_ranker.ml_features_cache)
                },
                "query_expansion": {
                    "medical_synonyms": len(self.query_expander.medical_synonyms),
                    "medical_contexts": len(self.query_expander.medical_contexts)
                },
                "configuration": {
                    "default_retrieval_k": self.default_k,
                    "final_result_k": self.final_k
                }
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get search analytics: {e}")
            return {"error": str(e)}

# Factory function for easy initialization
def create_advanced_semantic_search(vectorstore_path: str = "data/vectorstore") -> AdvancedSemanticSearch:
    """
    Factory function to create advanced semantic search instance
    
    Args:
        vectorstore_path: Path to vector store data
        
    Returns:
        Configured AdvancedSemanticSearch instance
    """
    try:
        # Initialize components
        embedder = HealthAIEmbedding()
        vector_store = HealthAIVectorStore(vectorstore_path)
        
        # Create advanced search
        search_engine = AdvancedSemanticSearch(vector_store, embedder)
        
        logger.info(f"Advanced semantic search created with vectorstore at {vectorstore_path}")
        
        return search_engine
        
    except Exception as e:
        logger.error(f"Failed to create advanced semantic search: {e}")
        raise