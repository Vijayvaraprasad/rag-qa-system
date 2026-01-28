"""
Ensemble Embedding Models: Get 3 different perspectives!

Why 3 models?
- Model 1 (MiniLM): Fast, good general understanding
- Model 2 (MPNet): Better semantic understanding
- Model 3 (BGE): Optimized for retrieval

If all 3 agree: Result is HIGHLY confident ✓✓✓
If 2 agree: Good confidence ✓✓
If only 1: Lower confidence ✓

Real-world: Like asking 3 experts instead of 1!
"""

from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict

class EnsembleEmbedder:
    def __init__(self, device: str = "cuda"):
        """
        Load 3 different embedding models.
        """
        print("Loading ensemble embedding models...")
        
        # Model 1: Fast and good general purpose (your current)
        self.model1 = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2",
            device=device
        )
        print("✓ Loaded MiniLM model")
        
        # Model 2: Larger, better semantic understanding
        self.model2 = SentenceTransformer(
            "sentence-transformers/all-mpnet-base-v2",
            device=device
        )
        print("✓ Loaded MPNet model")
        
        # Model 3: Optimized for dense retrieval
        self.model3 = SentenceTransformer(
            "BAAI/bge-large-en-v1.5",
            device=device
        )
        print("✓ Loaded BGE model")
        
        self.models = [self.model1, self.model2, self.model3]
        self.model_names = ["MiniLM", "MPNet", "BGE"]
    
    def embed_texts_all_models(self, texts: List[str]) -> Dict[str, np.ndarray]:
        """
        Embed texts with all 3 models.
        
        Returns:
            {
                "minilm": [embeddings],
                "mpnet": [embeddings],
                "bge": [embeddings]
            }
        """
        embeddings = {}
        
        for model, name in zip(self.models, self.model_names):
            emb = model.encode(
                texts,
                batch_size=32,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            embeddings[name.lower()] = emb
        
        return embeddings
    
    def embedding_agreement(self, embeddings: Dict[str, np.ndarray]) -> Dict:
        """
        Check how much the models agree on the embeddings.
        
        High agreement = confident embeddings
        Low agreement = uncertain embeddings
        """
        # Calculate pairwise similarities between models
        minilm = embeddings["minilm"]
        mpnet = embeddings["mpnet"]
        bge = embeddings["bge"]
        
        # Cosine similarity
        def cosine_sim(v1, v2):
            return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        
        similarities = []
        for i in range(len(minilm)):
            sim1_2 = cosine_sim(minilm[i], mpnet[i])
            sim1_3 = cosine_sim(minilm[i], bge[i])
            sim2_3 = cosine_sim(mpnet[i], bge[i])
            
            avg_sim = (sim1_2 + sim1_3 + sim2_3) / 3
            similarities.append(avg_sim)
        
        return {
            "agreement_scores": similarities,
            "avg_agreement": np.mean(similarities),
            "min_agreement": np.min(similarities),
            "max_agreement": np.max(similarities)
        }
    
    def ensemble_embedding(self, text: str) -> Dict:
        """
        Get ensemble embedding for a single text.
        
        Returns:
            {
                "ensemble": final_embedding (average of 3),
                "individual": {model: embedding},
                "agreement": confidence_score,
                "summary": "All models agree" or "2 models agree"
            }
        """
        embeddings_dict = self.embed_texts_all_models([text])
        
        # Average the embeddings
        ensemble = np.mean([
            embeddings_dict["minilm"],
            embeddings_dict["mpnet"],
            embeddings_dict["bge"]
        ], axis=0)[0]
        
        # Normalize
        ensemble = ensemble / np.linalg.norm(ensemble)
        
        # Get agreement
        agreement_info = self.embedding_agreement(embeddings_dict)
        
        return {
            "ensemble": ensemble,
            "individual": {
                "minilm": embeddings_dict["minilm"][0],
                "mpnet": embeddings_dict["mpnet"][0],
                "bge": embeddings_dict["bge"][0]
            },
            "agreement": agreement_info["avg_agreement"],
            "summary": self._agreement_summary(agreement_info["avg_agreement"])
        }
    
    def ensemble_embeddings(self, texts: List[str]) -> Dict:
        """
        Get ensemble embeddings for multiple texts.
        
        Returns:
            {
                "ensemble_embeddings": np.array (N x 1024),
                "agreement_per_text": [scores],
                "overall_agreement": float
            }
        """
        embeddings_dict = self.embed_texts_all_models(texts)
        
        # Average
        ensemble = np.mean([
            embeddings_dict["minilm"],
            embeddings_dict["mpnet"],
            embeddings_dict["bge"]
        ], axis=0)
        
        # Normalize each
        for i in range(len(ensemble)):
            ensemble[i] = ensemble[i] / np.linalg.norm(ensemble[i])
        
        # Calculate agreement per text
        agreement_per_text = []
        for i in range(len(texts)):
            minilm_i = embeddings_dict["minilm"][i]
            mpnet_i = embeddings_dict["mpnet"][i]
            bge_i = embeddings_dict["bge"][i]
            
            sim1_2 = np.dot(minilm_i, mpnet_i)
            sim1_3 = np.dot(minilm_i, bge_i)
            sim2_3 = np.dot(mpnet_i, bge_i)
            
            avg_agreement = (sim1_2 + sim1_3 + sim2_3) / 3
            agreement_per_text.append(avg_agreement)
        
        return {
            "ensemble_embeddings": ensemble,
            "agreement_per_text": agreement_per_text,
            "overall_agreement": np.mean(agreement_per_text)
        }
    
    def _agreement_summary(self, agreement: float) -> str:
        """
        Convert agreement score to human-readable summary.
        """
        if agreement > 0.9:
            return "✓✓✓ All models strongly agree (very confident)"
        elif agreement > 0.8:
            return "✓✓ 2+ models agree (confident)"
        elif agreement > 0.7:
            return "✓ 2 models agree (moderate confidence)"
        else:
            return "⚠ Low agreement between models (less confident)"
