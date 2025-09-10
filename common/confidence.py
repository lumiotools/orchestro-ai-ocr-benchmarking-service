"""
Confidence score calculation module for OCR benchmarking.

This module provides functionality to calculate confidence scores by comparing
OCR-generated markdown text with ground truth markdown text using multiple
similarity metrics.
"""

import re
import math
from typing import Dict, List, Optional
from collections import Counter
from difflib import SequenceMatcher


class ConfidenceCalculator:
    """
    A class to calculate confidence scores between expected and extracted markdown texts
    using multiple similarity metrics including structural, content, and semantic analysis.
    """
    
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        Initialize the confidence calculator with optional custom weights.
        
        Args:
            weights: Dictionary with keys 'structural', 'content', 'semantic' 
                    Default weights: structural=0.3, content=0.5, semantic=0.2
        """
        self.weights = weights or {
            'structural': 0.3,
            'content': 0.5,
            'semantic': 0.2
        }
        
        # Validate weights sum to 1.0
        total_weight = sum(self.weights.values())
        if not math.isclose(total_weight, 1.0, rel_tol=1e-9):
            raise ValueError(f"Weights must sum to 1.0, got {total_weight}")
    
    def calculate_confidence_score(self, expected_markdown: str, extracted_markdown: str) -> Dict[str, float]:
        """
        Calculate the overall confidence score comparing extracted_markdown to expected_markdown.
        
        Args:
            expected_markdown: The ground truth markdown text
            extracted_markdown: The OCR-generated markdown text to evaluate
            
        Returns:
            Dictionary containing:
            - overall_score: Weighted combination of all metrics (0-1)
            - structural_score: Markdown structure similarity (0-1)
            - content_score: Text content similarity (0-1)
            - semantic_score: Semantic similarity (0-1)
            - detailed_metrics: Additional detailed metrics
        """
        
        # Calculate individual similarity scores
        structural_score = self._calculate_structural_similarity(expected_markdown, extracted_markdown)
        content_score = self._calculate_content_similarity(expected_markdown, extracted_markdown)
        semantic_score = self._calculate_semantic_similarity(expected_markdown, extracted_markdown)
        
        # Calculate weighted overall score
        overall_score = (
            self.weights['structural'] * structural_score +
            self.weights['content'] * content_score +
            self.weights['semantic'] * semantic_score
        )
        
        # Get detailed metrics for analysis
        detailed_metrics = self._get_detailed_metrics(expected_markdown, extracted_markdown)
        
        return {
            'overall_score': round(overall_score, 4),
            'structural_score': round(structural_score, 4),
            'content_score': round(content_score, 4),
            'semantic_score': round(semantic_score, 4),
            'detailed_metrics': detailed_metrics
        }
    
    def _calculate_structural_similarity(self, expected: str, extracted: str) -> float:
        """
        Calculate similarity based on markdown structural elements.
        
        Compares:
        - Headers (# ## ###)
        - Lists (- * +)
        - Bold/Italic formatting
        - Links and images
        - Code blocks
        - Tables
        """
        expected_structure = self._extract_markdown_structure(expected)
        extracted_structure = self._extract_markdown_structure(extracted)
        
        total_score = 0.0
        total_weight = 0.0
        
        # Compare each structural element type
        for element_type in expected_structure:
            expected_elements = expected_structure[element_type]
            extracted_elements = extracted_structure.get(element_type, [])
            
            if not expected_elements:  # Skip empty element types
                continue
                
            # Calculate similarity for this element type
            element_similarity = self._calculate_list_similarity(expected_elements, extracted_elements)
            
            # Weight by importance (headers more important than formatting)
            weight = self._get_structural_weight(element_type)
            total_score += element_similarity * weight
            total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    def _extract_markdown_structure(self, text: str) -> Dict[str, List[str]]:
        """Extract structural elements from markdown text."""
        structure = {
            'headers': [],
            'lists': [],
            'bold': [],
            'italic': [],
            'links': [],
            'code_blocks': [],
            'tables': []
        }
        
        lines = text.split('\n')
        
        for line in lines:
            # Headers
            header_match = re.match(r'^(#{1,6})\s+(.+)', line.strip())
            if header_match:
                level = len(header_match.group(1))
                content = header_match.group(2)
                structure['headers'].append(f"h{level}: {content}")
            
            # Lists
            if re.match(r'^\s*[-*+]\s+', line):
                structure['lists'].append(line.strip())
            
            # Tables
            if '|' in line and line.strip():
                structure['tables'].append(line.strip())
        
        # Extract inline formatting
        structure['bold'].extend(re.findall(r'\*\*(.*?)\*\*', text))
        structure['italic'].extend(re.findall(r'\*(.*?)\*', text))
        structure['links'].extend(re.findall(r'\[([^\]]+)\]\([^)]+\)', text))
        structure['code_blocks'].extend(re.findall(r'```[\s\S]*?```', text))
        
        return structure
    
    def _get_structural_weight(self, element_type: str) -> float:
        """Get importance weight for different structural elements."""
        weights = {
            'headers': 0.3,
            'lists': 0.2,
            'tables': 0.25,
            'links': 0.1,
            'code_blocks': 0.1,
            'bold': 0.025,
            'italic': 0.025
        }
        return weights.get(element_type, 0.1)
    
    def _calculate_content_similarity(self, expected: str, extracted: str) -> float:
        """
        Calculate content similarity using ROUGE-like metrics.
        
        Combines word-level precision, recall, and F1 score.
        """
        expected_words = self._extract_words(expected)
        extracted_words = self._extract_words(extracted)
        
        if not expected_words:
            return 1.0 if not extracted_words else 0.0
        
        if not extracted_words:
            return 0.0
        
        # Calculate word-level metrics
        expected_counter = Counter(expected_words)
        extracted_counter = Counter(extracted_words)
        
        # Precision: What fraction of extracted words are in expected
        common_words = sum((expected_counter & extracted_counter).values())
        precision = common_words / len(extracted_words)
        
        # Recall: What fraction of expected words are in extracted
        recall = common_words / len(expected_words)
        
        # F1 Score
        if precision + recall == 0:
            f1_score = 0.0
        else:
            f1_score = 2 * (precision * recall) / (precision + recall)
        
        # Sequence similarity (order matters)
        sequence_similarity = SequenceMatcher(None, expected_words, extracted_words).ratio()
        
        # Combine metrics (70% F1, 30% sequence)
        content_score = 0.7 * f1_score + 0.3 * sequence_similarity
        
        return content_score
    
    def _calculate_semantic_similarity(self, expected: str, extracted: str) -> float:
        """
        Calculate semantic similarity using simple text-based methods.
        
        This is a placeholder for semantic similarity. For production use,
        consider integrating sentence transformers or other NLP models.
        """
        # Simple character-level similarity as baseline
        expected_clean = self._clean_text(expected)
        extracted_clean = self._clean_text(extracted)
        
        if not expected_clean:
            return 1.0 if not extracted_clean else 0.0
        
        if not extracted_clean:
            return 0.0
        
        # Use sequence matcher on cleaned text
        similarity = SequenceMatcher(None, expected_clean, extracted_clean).ratio()
        
        return similarity
    
    def _extract_words(self, text: str) -> List[str]:
        """Extract words from text, removing markdown formatting."""
        # Remove markdown formatting
        clean_text = re.sub(r'[#*_`\[\]()]', ' ', text)
        clean_text = re.sub(r'https?://\S+', ' ', clean_text)  # Remove URLs
        
        # Extract words (alphanumeric sequences)
        words = re.findall(r'\b\w+\b', clean_text.lower())
        return words
    
    def _clean_text(self, text: str) -> str:
        """Clean text for semantic comparison."""
        # Remove markdown formatting
        clean = re.sub(r'[#*_`\[\]()]', ' ', text)
        clean = re.sub(r'https?://\S+', ' ', clean)
        clean = re.sub(r'\s+', ' ', clean)
        return clean.strip().lower()
    
    def _calculate_list_similarity(self, list1: List[str], list2: List[str]) -> float:
        """Calculate similarity between two lists of strings."""
        if not list1:
            return 1.0 if not list2 else 0.0
        
        if not list2:
            return 0.0
        
        # Use Jaccard similarity
        set1 = set(list1)
        set2 = set(list2)
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def _get_detailed_metrics(self, expected: str, extracted: str) -> Dict[str, float]:
        """Calculate additional detailed metrics for analysis."""
        expected_words = self._extract_words(expected)
        extracted_words = self._extract_words(extracted)
        
        return {
            'word_count_expected': len(expected_words),
            'word_count_extracted': len(extracted_words),
            'character_count_expected': len(expected),
            'character_count_extracted': len(extracted),
            'word_count_ratio': len(extracted_words) / len(expected_words) if expected_words else 0.0,
            'character_count_ratio': len(extracted) / len(expected) if expected else 0.0,
        }