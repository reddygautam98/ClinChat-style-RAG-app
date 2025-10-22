"""
PDF Parser Module for ClinChat RAG Application
Extracts text from PDF files and creates text chunks for embeddings
"""

import fitz  # PyMuPDF
import re
from typing import List, Dict, Optional
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFParser:
    """Handles PDF text extraction and chunking"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize PDF parser
        
        Args:
            chunk_size: Maximum number of characters per chunk
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract all text from a PDF file
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text as a single string
        """
        try:
            # Open the PDF document
            doc = fitz.open(pdf_path)
            text = ""
            
            # Extract text from each page
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_text = page.get_text()
                text += page_text + "\n"
            
            doc.close()
            
            # Clean up the text
            text = self._clean_text(text)
            
            logger.info(f"Extracted {len(text)} characters from {pdf_path}")
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {str(e)}")
            raise
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text by removing extra whitespace and formatting
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page numbers and headers/footers (basic patterns)
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
        text = re.sub(r'\n\s*Page \d+.*\n', '\n', text)
        
        # Remove extra newlines
        text = re.sub(r'\n+', '\n', text)
        
        return text.strip()
    
    def create_chunks(self, text: str, source: str = "") -> List[Dict[str, str]]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Text to chunk
            source: Source identifier (e.g., filename)
            
        Returns:
            List of text chunks with metadata
        """
        chunks = []
        
        # Split text by sentences first to avoid breaking mid-sentence
        sentences = self._split_into_sentences(text)
        
        current_chunk = ""
        current_length = 0
        chunk_index = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            # If adding this sentence would exceed chunk size, save current chunk
            if current_length + sentence_length > self.chunk_size and current_chunk:
                chunk_data = {
                    "text": current_chunk.strip(),
                    "source": source,
                    "chunk_index": chunk_index,
                    "character_count": len(current_chunk.strip())
                }
                chunks.append(chunk_data)
                
                # Start new chunk with overlap from previous chunk
                overlap_text = self._get_overlap_text(current_chunk, self.chunk_overlap)
                current_chunk = overlap_text + " " + sentence
                current_length = len(current_chunk)
                chunk_index += 1
            else:
                # Add sentence to current chunk
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
                current_length = len(current_chunk)
        
        # Add the last chunk if it has content
        if current_chunk.strip():
            chunk_data = {
                "text": current_chunk.strip(),
                "source": source,
                "chunk_index": chunk_index,
                "character_count": len(current_chunk.strip())
            }
            chunks.append(chunk_data)
        
        logger.info(f"Created {len(chunks)} chunks from text (source: {source})")
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences
        
        Args:
            text: Input text
            
        Returns:
            List of sentences
        """
        # Simple sentence splitting (can be enhanced with nltk or spaCy)
        sentences = re.split(r'[.!?]+\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _get_overlap_text(self, text: str, overlap_size: int) -> str:
        """
        Get the last N characters from text for overlap
        
        Args:
            text: Source text
            overlap_size: Number of characters to extract
            
        Returns:
            Overlap text
        """
        if len(text) <= overlap_size:
            return text
        
        # Try to break at word boundaries
        overlap_text = text[-overlap_size:]
        space_index = overlap_text.find(' ')
        
        if space_index > 0:
            return overlap_text[space_index:].strip()
        
        return overlap_text
    
    def process_pdf(self, pdf_path: str) -> List[Dict[str, str]]:
        """
        Complete PDF processing: extract text and create chunks
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of text chunks with metadata
        """
        # Validate file exists
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Extract text
        text = self.extract_text_from_pdf(pdf_path)
        
        if not text.strip():
            logger.warning(f"No text extracted from {pdf_path}")
            return []
        
        # Create chunks
        source_name = Path(pdf_path).name
        chunks = self.create_chunks(text, source_name)
        
        return chunks
    
    def process_multiple_pdfs(self, pdf_directory: str) -> List[Dict[str, str]]:
        """
        Process all PDF files in a directory
        
        Args:
            pdf_directory: Directory containing PDF files
            
        Returns:
            Combined list of chunks from all PDFs
        """
        pdf_dir = Path(pdf_directory)
        
        if not pdf_dir.exists():
            raise FileNotFoundError(f"Directory not found: {pdf_directory}")
        
        all_chunks = []
        pdf_files = list(pdf_dir.glob("*.pdf"))
        
        if not pdf_files:
            logger.warning(f"No PDF files found in {pdf_directory}")
            return []
        
        logger.info(f"Processing {len(pdf_files)} PDF files")
        
        for pdf_file in pdf_files:
            try:
                chunks = self.process_pdf(str(pdf_file))
                all_chunks.extend(chunks)
                logger.info(f"Processed {pdf_file.name}: {len(chunks)} chunks")
            except Exception as e:
                logger.error(f"Failed to process {pdf_file.name}: {str(e)}")
                continue
        
        logger.info(f"Total chunks created: {len(all_chunks)}")
        return all_chunks


def create_sample_medical_pdf_content() -> str:
    """Create sample medical content for testing"""
    return """
    MEDICAL RESEARCH: DIABETES MANAGEMENT
    
    Introduction
    Diabetes mellitus is a chronic metabolic disorder characterized by elevated blood glucose levels. 
    Proper management requires a comprehensive approach including medication, diet, and lifestyle modifications.
    
    Types of Diabetes
    Type 1 diabetes is an autoimmune condition where the pancreas produces little to no insulin.
    Type 2 diabetes is characterized by insulin resistance and relative insulin deficiency.
    Gestational diabetes occurs during pregnancy and usually resolves after delivery.
    
    Treatment Approaches
    Medication management includes insulin therapy, metformin, and other oral hypoglycemic agents.
    Dietary interventions focus on carbohydrate counting and portion control.
    Regular physical activity helps improve insulin sensitivity and glucose control.
    
    Monitoring and Complications
    Blood glucose monitoring is essential for optimal diabetes management.
    Long-term complications include cardiovascular disease, nephropathy, retinopathy, and neuropathy.
    Regular screening and preventive care can help reduce the risk of complications.
    
    Conclusion
    Effective diabetes management requires patient education, regular monitoring, and a multidisciplinary approach.
    Healthcare providers should work closely with patients to develop individualized treatment plans.
    """


if __name__ == "__main__":
    # Test the PDF parser
    parser = PDFParser(chunk_size=500, chunk_overlap=100)
    
    # Test with sample content
    sample_text = create_sample_medical_pdf_content()
    chunks = parser.create_chunks(sample_text, "sample_medical_content")
    
    print(f"Created {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i+1}:")
        print(f"Source: {chunk['source']}")
        print(f"Characters: {chunk['character_count']}")
        print(f"Text: {chunk['text'][:200]}...")