"""
Confidence score calculation module for OCR benchmarking.

This module provides functionality to calculate confidence scores by comparing
OCR-generated markdown text with ground truth markdown text using multiple
similarity metrics.
"""

import math
import re
from typing import Dict, List, Optional, Tuple
from openai import OpenAI
import os
import json
from dotenv import load_dotenv
load_dotenv()

PROMPT = """
You are given two markdown documents: a *ground truth markdown* and an *actual markdown*. Compare them on three dimensions:

1. **Structural Score (0-1):** Evaluate whether the structural elements (headers, lists, bold/italic text, links, code blocks, tables) in the actual markdown match the ground truth markdown. A perfect score means the elements present in the actual markdown render similar to the ground truth markdown.

- Example: If 30% of the document has incorrect structure, assign a score of 0.7.
- Example: If 1% of the document has incorrect structure, assign a score of 0.99.

2. **Content Score (0-1):** Measure the similarity of the textual content (words, phrases, order of sentences) between the two markdowns. Ignore differences in formatting.

- Example: If 30% of the text content is missing or incorrect, assign a score of 0.7.
- Example: If 1% of the text content is missing or incorrect, assign a score of 0.99.

3. **Semantic Score (0-1):** Assess whether the two markdowns convey the same meaning, even if the wording differs. This should capture paraphrasing or reworded but equivalent meaning.

- Example: If 30% of the semantic meaning is lost or altered, assign a score of 0.7.
- Example: If 1% of the semantic meaning is lost or altered, assign a score of 0.99.

**Inputs:**

* Ground Truth Markdown: 
```markdown
{ground_truth_markdown}
```

**Analyze the above ground truth markdown**
Scores assigned to above ground truth markdown are:
1. Structural Score: 1.0
2. Content Score: 1.0
3. Semantic Score: 1.0

**Now based on the above ground truth markdown and its scores, analyze the actual markdown below and assign scores:**
**While Judging make sure the comparison should not be too strict, it should compare the essence of the content rather than exact wording.**

* Actual Markdown: 
```markdown
{actual_markdown}
```

"""

class LLMConfidenceCalculator:
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
        self.llm_client = OpenAI(
            api_key=os.getenv("CONFIDENCE_LLM_API_KEY"),
            base_url=os.getenv("CONFIDENCE_LLM_API_URL"),
        )
        self.llm_model_id = os.getenv("CONFIDENCE_LLM_MODEL_ID")
        self.llm_prompt = PROMPT
        
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
        # structural_score = self._calculate_structural_similarity(expected_markdown, extracted_markdown)
        # content_score = self._calculate_content_similarity(expected_markdown, extracted_markdown)
        # semantic_score = self._calculate_semantic_similarity(expected_markdown, extracted_markdown)
        
        structural_score, content_score, semantic_score = self._calculate_scores(expected_markdown, extracted_markdown)
        
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
        
    def _calculate_scores(self, expected: str, extracted: str) -> Tuple[float, float, float]:
        """
        Calculate individual similarity scores using LLM.
        
        Returns:
            Tuple of (structural_score, content_score, semantic_score)
        """
        
        response = self.llm_client.chat.completions.create(
            model=self.llm_model_id,
            messages=[
                {
                    "role": "user",
                    "content": self.llm_prompt.format(ground_truth_markdown=expected, actual_markdown=extracted)
                }
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "content_similarity",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "structural_similarity_score": { "type": "number", "min": 0, "max": 1 },
                            "content_similarity_score": { "type": "number", "min": 0, "max": 1 },
                            "semantic_similarity_score": { "type": "number", "min": 0, "max": 1 }
                        },
                        "required": ["structural_similarity_score", "content_similarity_score", "semantic_similarity_score"],
                        "additionalProperties": False
                    }  
                },
            }
        )
        
        structural_similarity_score = json.loads(response.choices[0].message.content)['structural_similarity_score']
        content_similarity_score = json.loads(response.choices[0].message.content)['content_similarity_score']
        semantic_similarity_score = json.loads(response.choices[0].message.content)['semantic_similarity_score']

        return structural_similarity_score, content_similarity_score, semantic_similarity_score
    
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
        response = self.llm_client.chat.completions.create(
            model=self.llm_model_id,
            messages=[
                {
                    "role": "user",
                    "content": json.dumps({
                        "ground_truth_markdown": expected,
                        "actual_markdown": extracted,
                        "task": "Validate the structures of the actual markdown against the ground truth markdown. Provide a similarity score between 0 and 1 based on the presence and correctness of structural elements like headers, lists, bold/italic text, links, code blocks, and tables."
                    })
                }
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "content_similarity",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "structural_similarity_score": { "type": "number", "min": 0, "max": 1 }
                        },
                        "required": ["structural_similarity_score"],
                        "additionalProperties": False
                    }  
                },
            }
        )
        
        structural_similarity_score = json.loads(response.choices[0].message.content)['structural_similarity_score']
        
        return structural_similarity_score
    
    def _calculate_content_similarity(self, expected: str, extracted: str) -> float:
        """
        Calculate content similarity.
        """
        response = self.llm_client.chat.completions.create(
            model=self.llm_model_id,
            messages=[
                {
                    "role": "user",
                    "content": json.dumps({
                        "ground_truth_markdown": expected,
                        "actual_markdown": extracted,
                        "task": "Evaluate the text content similarity between the actual markdown and the ground truth markdown. Provide a similarity score between 0 and 1 based on the accuracy and completeness of the text content."
                    })
                }
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "content_similarity",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "content_similarity_score": { "type": "number", "min": 0, "max": 1 }
                        },
                        "required": ["content_similarity_score"],
                        "additionalProperties": False
                    }  
                },
            }
        )

        content_similarity_score = json.loads(response.choices[0].message.content)['content_similarity_score']

        return content_similarity_score
    
    def _calculate_semantic_similarity(self, expected: str, extracted: str) -> float:
        """
        Calculate semantic similarity.
        """
        response = self.llm_client.chat.completions.create(
            model=self.llm_model_id,
            messages=[
                {
                    "role": "user",
                    "content": json.dumps({
                        "ground_truth_markdown": expected,
                        "actual_markdown": extracted,
                        "task": "Validate the structures of the actual markdown against the ground truth markdown. Provide a similarity score between 0 and 1 based on the semantic meaning and context of the text content."
                    })
                }
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "content_similarity",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "semantic_similarity_score": { "type": "number", "min": 0, "max": 1 }
                        },
                        "required": ["semantic_similarity_score"],
                        "additionalProperties": False
                    }  
                },
            }
        )
        
        semantic_similarity_score = json.loads(response.choices[0].message.content)['semantic_similarity_score']
        
        return semantic_similarity_score
    
    def _extract_words(self, text: str) -> List[str]:
        """Extract words from text, removing markdown formatting."""
        # Remove markdown formatting
        clean_text = re.sub(r'[#*_`\[\]()]', ' ', text)
        clean_text = re.sub(r'https?://\S+', ' ', clean_text)  # Remove URLs
        
        # Extract words (alphanumeric sequences)
        words = re.findall(r'\b\w+\b', clean_text.lower())
        return words
    
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