"""Local memory-based Knowledge Base (RAG) for the User Manual.

Provides semantic keyword matching over user guide chapters (ADaM schemas,
N-value troubleshooting, billing, zip downloading, support sla) to feed the Agent context.
"""
import re
from typing import List, Dict, Any

# Structured knowledge sections mapping directly to the User Manual and Creem compliance guides
KNOWLEDGE_DATA = [
    {
        "title": "SAP Parsing & TOC Generation",
        "category": "TOC",
        "keywords": ["sap", "toc", "protocol", "extract", "parse", "outline", "word", "upload"],
        "content": (
            "The system supports uploading statistical analysis plan (SAP) protocol documents in Word format (.docx). "
            "Our parsing engine scans the document to find tables, figures, and listings (TFLs) outline indexes starting with "
            "Section 14 or Appendix 16. It automatically extracts TFL IDs, titles, and populations into dynamic TOC entries."
        )
    },
    {
        "title": "ADaM Dataset Formatting & Naming Requirements",
        "category": "Datasets",
        "keywords": ["adam", "datasets", "sas7bdat", "lowercase", "files", "naming", "format", "upload"],
        "content": (
            "The backend analysis pipeline accepts SAS dataset files (.sas7bdat). To allow successful dependency matching, "
            "filenames must be in lowercase (e.g. adsl.sas7bdat, adae.sas7bdat, adtte.sas7bdat). Demographic disposition "
            "reports require 'adsl.sas7bdat'; adverse events summaries require 'adae.sas7bdat'; and KM survival figures "
            "require both 'adtte.sas7bdat' and 'adsl.sas7bdat'."
        )
    },
    {
        "title": "Fixing Table Header N=0 Counts",
        "category": "Troubleshooting",
        "keywords": ["header", "n=0", "total", "count", "arms", "treatment", "groups", "0"],
        "content": (
            "We implement adaptive treatment group scanning. During table generations, the analyzer extracts the planned "
            "treatment variable (TRT01PN or TRT01P) from your ADSL dataset and computes treatment-specific N values dynamically. "
            "If your table headers show N=0, please double-check that your ADSL dataset contains one of these treatment variables "
            "and that records are populated."
        )
    },
    {
        "title": "Double ZIP Archive Downloads & Auditing",
        "category": "Archive",
        "keywords": ["download", "zip", "archive", "source", "code.py", "run.log", "audit", "compliance"],
        "content": (
            "The platform provides double ZIP archiving to support regulatory audits:\n"
            "1. Job-level Archive: Click 'Download Source ZIP' in the preview page to export a ZIP containing the generated PDF, "
            "reproducible python code (code.py), and execution environment logs (run.log).\n"
            "2. Study-level Archive: Click 'Download Study ZIP' on the Study overview to download all generated reports organized "
            "by Tables, Figures, and Listings."
        )
    },
    {
        "title": "Subscription Limits & Upgrades",
        "category": "Billing",
        "keywords": ["billing", "upgrade", "pro", "plus", "subscription", "runs", "limit", "checkout"],
        "content": (
            "The system supports three subscription plans:\n"
            "- Free: up to 10 runs per month.\n"
            "- Pro: up to 500 runs per month.\n"
            "- Plus/Enterprise: up to 5000 runs per month.\n"
            "You can go to the 'Billing' tab in the sidebar to subscribe or manage payments securely. Generation counts update immediately."
        )
    },
    {
        "title": "Contact Technical Support & SLA info@xwqin.com",
        "category": "Support",
        "keywords": ["support", "email", "contact", "sla", "help", "info@xwqin.com", "info"],
        "content": (
            "For payment, data mapping issues, or general support, you can send an email to our helpdesk at info@xwqin.com. "
            "We guarantee responses within 24 business hours on weekdays (Monday - Friday, 9:00 AM - 6:00 PM UTC+8)."
        )
    }
]


def search_knowledge_base(query: str, study_id: Any = None, limit: int = 3) -> List[Dict[str, Any]]:
    """Simple keyword matching TF-IDF-like semantic search over user manual memory and custom document summaries."""
    if not query:
        return []

    # Clean and tokenize query
    words = re.findall(r"\w+", query.lower())
    if not words:
        return []

    scored_sections = []
    
    # 1. Search built-in user guide sections
    for section in KNOWLEDGE_DATA:
        score = 0
        # Title match weighting
        title_lower = section["title"].lower()
        for w in words:
            if w in title_lower:
                score += 5
                
        # Keywords match weighting
        for kw in section["keywords"]:
            if kw.lower() in words:
                score += 3
                
        # Content match weighting
        content_lower = section["content"].lower()
        for w in words:
            if w in content_lower:
                score += 1
                
        if score > 0:
            scored_sections.append((score, section))

    # 2. Search uploaded reference custom documents summaries (RAG)
    import os
    import json
    KNOWLEDGE_DIR = "/app/knowledge"
    summary_path = os.path.join(KNOWLEDGE_DIR, "documents_summary.json")
    if not os.path.exists(summary_path):
        summary_path = "knowledge/documents_summary.json"

    if os.path.exists(summary_path):
        try:
            with open(summary_path, "r", encoding="utf-8") as f:
                summaries = json.load(f)
                
            for fname, info in summaries.items():
                doc_study_id = info.get("study_id")
                
                # RAG Study Isolation: If study-specific doc, only retrieve if active study matches
                if doc_study_id:
                    if not study_id or str(doc_study_id) != str(study_id):
                        continue
                        
                score = 0
                # Match keywords
                for kw in info.get("keywords", []):
                    if kw.lower() in words:
                        score += 5
                # Match summary content
                summary_lower = info.get("summary", "").lower()
                for w in words:
                    if w in summary_lower:
                        score += 2
                        
                if score > 0:
                    scored_sections.append((score, {
                        "title": f"Document: {fname} ({'Global' if not doc_study_id else 'Study-Specific'})",
                        "category": "Reference Document",
                        "content": f"Summary: {info.get('summary')}\nKeywords: {', '.join(info.get('keywords', []))}"
                    }))
        except Exception as e:
            print(f"Error searching custom documents in knowledge base: {e}")

    # Sort by score descending
    scored_sections.sort(key=lambda x: x[0], reverse=True)
    
    # Return matched slices
    return [
        {
            "title": item["title"],
            "category": item["category"],
            "content": item["content"],
            "match_score": score
        }
        for score, item in scored_sections[:limit]
    ]
