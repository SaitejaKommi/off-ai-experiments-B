"""LLM Client for intelligent food pairings and suggestions."""

import json
import logging
from typing import Optional, List
from product_insights.llm_config import LLMConfig

# Configure logging
logger = logging.getLogger(__name__)


class LLMClient:
    """Client for interacting with LLM APIs (Gemini, Groq, etc.)."""
    
    def __init__(self):
        """Initialize the LLM client."""
        self.provider = LLMConfig.PROVIDER
        self.config = LLMConfig
        self._init_provider()
    
    def _init_provider(self):
        """Initialize the selected LLM provider."""
        if self.provider == "gemini":
            self._init_gemini()
        elif self.provider == "groq":
            self._init_groq()
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}")
    
    def _call_llm(self, prompt: str) -> str:
        """Call the LLM provider and return response text."""
        if self.provider == "gemini":
            response = self.client.generate_content(prompt)
            return response.text
        elif self.provider == "groq":
            response = self.client.chat.completions.create(
                model=self.config.GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    def _init_gemini(self):
        """Initialize Google Gemini API."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.config.GEMINI_API_KEY)
            self.client = genai.GenerativeModel(self.config.GEMINI_MODEL)
            logger.info(f"✓ Gemini API initialized ({self.config.GEMINI_MODEL})")
        except ImportError:
            logger.error("google-generativeai not installed. Install with: pip install google-generativeai")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Gemini API: {e}")
            raise
    
    def _init_groq(self):
        """Initialize Groq API."""
        try:
            from groq import Groq
            self.client = Groq(api_key=self.config.GROQ_API_KEY)
            logger.info(f"✓ Groq API initialized ({self.config.GROQ_MODEL})")
        except ImportError:
            logger.error("groq not installed. Install with: pip install groq")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Groq API: {e}")
            raise
    
    def get_food_pairings(
        self,
        product_name: str,
        category: str,
        nutrients: Optional[dict] = None,
        retries: int = 2
    ) -> List[str]:
        """Get intelligent food pairing suggestions using LLM.
        
        Parameters
        ----------
        product_name : str
            Name of the product (e.g., "Red Split Lentils")
        category : str
            Product category (e.g., "lentils")
        nutrients : dict, optional
            Nutritional information {protein, fat, fiber, etc.}
        retries : int
            Number of retries on failure
            
        Returns
        -------
        list of str
            Suggested food pairings
        """
        if not self.config.USE_LLM_PAIRINGS:
            return []
        
        prompt = self._build_pairing_prompt(product_name, category, nutrients)
        
        for attempt in range(retries):
            try:
                response_text = self._call_llm(prompt)
                
                # Parse JSON response
                pairings = self._parse_pairings_response(response_text)
                
                if pairings:
                    logger.info(f"Generated {len(pairings)} pairings for {product_name}")
                    return pairings
                    
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{retries} failed: {e}")
                if attempt < retries - 1:
                    continue
                else:
                    logger.error(f"Failed to get pairings for {product_name} after {retries} retries")
        
        return []
    
    def get_product_summary(
        self,
        product_name: str,
        category: str,
        nutriscore: Optional[str] = None,
        nova_group: Optional[int] = None
    ) -> str:
        """Get an AI-generated product summary.
        
        Parameters
        ----------
        product_name : str
            Name of the product
        category : str
            Product category
        nutriscore : str, optional
            NutriScore grade (A-E)
        nova_group : int, optional
            NOVA processing group (1-4)
            
        Returns
        -------
        str
            AI-generated summary
        """
        if not self.config.USE_LLM_PAIRINGS:
            return ""
        
        prompt = f"""Generate a brief, health-focused summary for this product:
Product: {product_name}
Category: {category}
NutriScore: {nutriscore if nutriscore else 'Unknown'}
NOVA Group: {nova_group if nova_group else 'Unknown'}

Summarize in 1-2 sentences focusing on nutritional quality and health implications.
Keep it factual and helpful for consumers."""
        
        try:
            response_text = self._call_llm(prompt)
            return response_text.strip()
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return ""
    
    def _build_pairing_prompt(
        self,
        product_name: str,
        category: str,
        nutrients: Optional[dict] = None
    ) -> str:
        """Build the prompt for pairing suggestions."""
        nutrient_info = ""
        if nutrients:
            parts = []
            for key, value in nutrients.items():
                if value and value > 0:
                    parts.append(f"  - {key.replace('_', ' ').title()}: {value:.1f}g/100g")
            if parts:
                nutrient_info = f"\nNutrients:\n" + "\n".join(parts)
        
        prompt = f"""As a food pairing expert, suggest 5 complementary foods for this product.

Product: {product_name}
Category: {category}{nutrient_info}

Return ONLY a JSON response with this exact format (no markdown, no explanation):
{{
  "pairings": ["food1", "food2", "food3", "food4", "food5"],
  "reasoning": "Brief explanation of why these foods pair well"
}}

Focus on:
1. Nutritional complementarity (e.g., protein with carbs)
2. Culinary tradition (how these foods are commonly eaten together)
3. Flavor and texture balance
4. Practical meal combinations

Only return valid JSON, nothing else."""
        
        return prompt
    
    def _parse_pairings_response(self, response_text: str) -> List[str]:
        """Parse JSON response from LLM.
        
        Parameters
        ----------
        response_text : str
            Raw response text from LLM
            
        Returns
        -------
        list of str
            Extracted pairings
        """
        try:
            # Extract JSON from response (may contain extra text)
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                logger.warning("No JSON found in response")
                return []
            
            json_str = json_match.group(0)
            data = json.loads(json_str)
            
            pairings = data.get("pairings", [])
            if isinstance(pairings, list):
                # Clean up pairing names
                return [p.lower().strip() for p in pairings if isinstance(p, str) and p.strip()]
            
            return []
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing pairings: {e}")
            return []


# Global LLM client instance
_llm_client = None


def get_llm_client() -> Optional[LLMClient]:
    """Get or create the global LLM client.
    
    Returns
    -------
    LLMClient or None
        The LLM client, or None if LLM is disabled or configuration is invalid.
    """
    global _llm_client
    
    if not LLMConfig.USE_LLM_PAIRINGS:
        return None
    
    if _llm_client is None:
        try:
            if LLMConfig.validate():
                _llm_client = LLMClient()
            else:
                logger.warning("LLM configuration invalid, LLM features disabled")
                return None
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}")
            return None
    
    return _llm_client
