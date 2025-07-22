import dspy
import json
import os
from typing import List, Dict, Optional
import logging

class RAGService:
    """RAG service for CTI (Cyber Threat Intelligence) data retrieval using STIX bundles."""
    
    def __init__(self, stix_bundle_path: Optional[str] = None, api_key: Optional[str] = None, log: Optional[logging.Logger] = None):
        self.max_characters = 6000
        self.topk_objects_to_retrieve = 5
        self.corpus = []
        self.adv_step = {}
        self.search = None
        self.api_key = api_key
        self.log = log or logging.getLogger("plugins.mcp")
        
        dspy.configure(lm=dspy.LM(
            model="gpt-4o",
            api_key=self.api_key,
            temperature=0.5,
        ))
        
        self.log.info(f"[RAG] Loading STIX bundle from: {stix_bundle_path}")
        
        # Initialize with STIX bundle if provided
        if stix_bundle_path:
            self.load_stix_bundle(stix_bundle_path)
    
    def load_stix_bundle(self, stix_bundle_path: str):
        """Load STIX bundle from file path."""
        try:
            with open(stix_bundle_path, 'r') as f:
                stix_bundle = json.load(f)
            self.initialize_from_bundle(stix_bundle)
        except FileNotFoundError:
            raise FileNotFoundError(f"STIX bundle not found at: {stix_bundle_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in STIX bundle: {stix_bundle_path}")
    
    def initialize_from_bundle(self, stix_bundle: dict):
        """Initialize the RAG service with a STIX bundle."""
        self.corpus, self.adv_step = self.extract_text_chunks(stix_bundle)
        
        self.log.info("[RAG] Initializing STIX bundle")
        self.log.debug("[RAG] " + "="*50)
        
        embedder = dspy.Embedder('openai/text-embedding-3-small', api_key=self.api_key)
        self.log.info(f"[RAG] Created embedder: {embedder}")
        self.search = dspy.retrievers.Embeddings(
            corpus=self.corpus,
            embedder=embedder, 
            k=self.topk_objects_to_retrieve,
        )
        self.log.info(f"[RAG] Initialized search retriever: {self.search}")
    
    def extract_text_chunks(self, stix_bundle: dict) -> tuple[List[str], Dict[str, str]]:
        """Extract text chunks from STIX bundle objects."""
        text_chunks = []
        adv_step = {}
        
        for obj in stix_bundle.get("objects", []):
            if obj.get("type") in [
                "attack-pattern", "malware", "tool", "threat-actor", 
                "intrusion-set", "identity", "indicator", "report"
            ]:
                name = obj.get("name", "")
                description = obj.get("description", "")
                
                if name or description:
                    adv_step[name] = description
                    text_chunks.append(f"{name} | {description}")
        
        return text_chunks, adv_step
    
    def search_cti_title(self, query: str) -> List[str]:
        """Returns top-5 results and then the names of the top-5 to top-30 results."""
        self.log.info(f"[RAG] Searching CTI title with query: {query}")
        
        if not self.search:
            self.log.warning("[RAG] Search attempted but RAG service not initialized with STIX data")
            return ["RAG service not initialized with STIX data"]
            
        self.log.debug(f"[RAG] Using search retriever: {self.search}")
        
        topK = self.search(query)
        self.log.debug(f"[RAG] Retrieved top {len(topK)} results")
        self.log.info(f"topK: {topK}")
        names = []
        if len(topK) > 5:
            names = [f"{x.split(' | ')[0]}" for x in topK.passages[5:30]]
            topK = topK[:5]
            self.log.info(f"names: {names}")
        else:
            names = [f"{x.split(' | ')[0]}" for x in topK.passages]
            topK = topK
            self.log.info(f"names: {names}")
        return topK.passages
    
    def search_cti_data_by_title(self, name: str) -> str:
        """Returns the full CTI data for a given name."""
        self.log.info(f"[RAG] Searching CTI data for title: {name}")
        
        if name in self.adv_step:
            self.log.debug("[RAG] Found title in adv_step cache")
            return self.adv_step[name]
        
        if not self.search:
            self.log.warning("[RAG] Search attempted but RAG service not initialized with STIX data")
            return "RAG service not initialized with STIX data"
        
        results = [x for x in self.search(name, 10) if x.startswith(name + " | ")]
        if not results:
            self.log.warning(f"[RAG] No CTI data found for name: {name}")
            return f"No CTI data found for name: {name}"
            
        self.log.debug(f"[RAG] Found {len(results)} matching results")
        return results[0]
    
    def get_context_for_task(self, task: str) -> Dict[str, any]:
        """Get relevant CTI context for a given task."""
        self.log.info(f"[RAG] Getting context for task: {task}")
        
        cti_results = self.search_cti_title(task)
        self.log.debug(f"[RAG] Retrieved {len(cti_results)} CTI results")
        
        # Extract detailed information for top results
        detailed_context = []
        for result in cti_results[:3]:  # Get details for top 3 results
            if " | " in result:
                name = result.split(" | ")[0]
                detail = self.search_cti_data_by_title(name)
                detailed_context.append({
                    "name": name,
                    "description": detail
                })
        
        self.log.info(f"[RAG] Generated context with {len(detailed_context)} detailed entries")
        return {
            "search_results": cti_results,
            "detailed_context": detailed_context,
            "query": task
        }


# Legacy functions for backward compatibility
def search_cti_title(query: str) -> list[str]:
    """Legacy function - use RAGService instead."""
    # This will only work if a global RAG service is initialized
    if 'global_rag_service' in globals():
        return global_rag_service.search_cti_title(query)
    return ["RAG service not initialized"]

def search_cti_data_by_title(name: str) -> str:
    """Legacy function - use RAGService instead."""
    # This will only work if a global RAG service is initialized
    if 'global_rag_service' in globals():
        return global_rag_service.search_cti_data_by_title(name)
    return "RAG service not initialized"