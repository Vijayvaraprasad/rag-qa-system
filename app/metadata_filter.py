"""
Metadata Filtering: Search with constraints!

Example:
Instead of searching all documents, search only:
- Documents from 2024-2026
- From source "official_docs"
- By author "verified_expert"

This prevents old/irrelevant docs from contaminating results.
"""

from datetime import datetime
from typing import Optional, List

class MetadataFilter:
    """
    Build filter queries for ChromaDB based on metadata.
    """
    
    @staticmethod
    def date_range_filter(start_date: str, end_date: str) -> dict:
        """
        Filter by date range.
        
        Args:
            start_date: "2024-01-01"
            end_date: "2026-12-31"
        
        Returns:
            Filter dict for ChromaDB
        """
        return {
            "date": {
                "$gte": start_date,
                "$lte": end_date
            }
        }
    
    @staticmethod
    def source_filter(allowed_sources: List[str]) -> dict:
        """
        Filter by document source.
        
        Args:
            allowed_sources: ["official_docs", "research_papers"]
        
        Returns:
            Filter dict for ChromaDB
        """
        if len(allowed_sources) == 1:
            return {"source": {"$eq": allowed_sources[0]}}
        else:
            return {"source": {"$in": allowed_sources}}
    
    @staticmethod
    def author_filter(allowed_authors: List[str]) -> dict:
        """
        Filter by author.
        
        Args:
            allowed_authors: ["Jane Doe", "John Smith"]
        
        Returns:
            Filter dict for ChromaDB
        """
        if len(allowed_authors) == 1:
            return {"author": {"$eq": allowed_authors[0]}}
        else:
            return {"author": {"$in": allowed_authors}}
    
    @staticmethod
    def combine_filters(*filters) -> dict:
        """
        Combine multiple filters with AND logic.
        
        Usage:
            combined = combine_filters(
                date_range_filter("2024-01-01", "2026-12-31"),
                source_filter(["official"]),
                author_filter(["Expert"])
            )
        """
        combined = {}
        for filter_dict in filters:
            if filter_dict:
                combined.update(filter_dict)
        return combined
    
    @staticmethod
    def custom_filter(field: str, operator: str, value) -> dict:
        """
        Create custom filter for any metadata field.
        
        Args:
            field: "priority", "category", "verified", etc.
            operator: "$eq", "$gt", "$gte", "$lt", "$lte", "$in", "$ne"
            value: The value to filter by
        
        Example:
            custom_filter("priority", "$gte", 8)
            custom_filter("verified", "$eq", True)
            custom_filter("category", "$in", ["news", "research"])
        """
        return {field: {operator: value}}


def add_metadata_to_chunk(chunk: str, metadata: dict) -> dict:
    """
    Helper to format chunk with metadata during ingestion.
    
    Args:
        chunk: The text chunk
        metadata: {"source": "...", "date": "...", "author": "...", "verified": True}
    
    Returns:
        Dict with chunk and metadata
    """
    return {
        "chunk": chunk,
        "metadata": metadata
    }


def example_filter_scenarios():
    """
    Real-world filtering examples.
    """
    
    # Scenario 1: Only recent, official docs
    filters_recent_official = MetadataFilter.combine_filters(
        MetadataFilter.date_range_filter("2025-01-01", "2026-12-31"),
        MetadataFilter.source_filter(["official_docs"])
    )
    # Result: {"date": {...}, "source": {...}}
    
    # Scenario 2: Expert-verified research only
    filters_expert = MetadataFilter.combine_filters(
        MetadataFilter.author_filter(["Dr. Jane Doe", "Dr. John Smith"]),
        MetadataFilter.custom_filter("verified", "$eq", True),
        MetadataFilter.custom_filter("reliability_score", "$gte", 8)
    )
    # Result: {"author": {...}, "verified": {...}, "reliability_score": {...}}
    
    # Scenario 3: Exclude outdated info
    filters_exclude_old = MetadataFilter.custom_filter(
        "deprecated",
        "$ne",
        True
    )
    # Result: {"deprecated": {"$ne": True}}
    
    return {
        "recent_official": filters_recent_official,
        "expert_verified": filters_expert,
        "exclude_outdated": filters_exclude_old
    }
