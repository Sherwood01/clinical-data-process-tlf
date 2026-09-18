"""
TOC Generator for TLF (Tables, Listings, Figures).
Extracts TLF information from SAP documents and generates a Table of Contents CSV.

Uses ICH E3 Guideline knowledge base to infer TLF IDs when SAP doesn't have explicit references.
"""

import re
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from docx import Document

# Import ICH E3 knowledge base
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.knowledge.ich_e3_knowledge import TLF_TEMPLATES, LISTING_TEMPLATES, FIGURE_TEMPLATES, POPULATIONS


class SAPReader:
    """Reads SAP documents (DOCX format)."""

    def __init__(self, sap_path: str):
        self.sap_path = Path(sap_path)

    def read_paragraphs(self) -> List[str]:
        """Extract all non-empty paragraphs and table texts from SAP document."""
        suffix = self.sap_path.suffix.lower()
        if suffix == ".docx":
            doc = Document(self.sap_path)
            paragraphs = []
            
            # 1. Extract regular paragraphs
            for para in doc.paragraphs:
                text = para.text.strip()
                if text:
                    paragraphs.append(text)
            
            # 2. Extract texts from tables (row by row) to capture tabular listings
            for table in doc.tables:
                for row in table.rows:
                    row_texts = []
                    for cell in row.cells:
                        cell_text = cell.text.strip()
                        if cell_text:
                            row_texts.append(cell_text)
                    if row_texts:
                        # Join cell texts in a row using space
                        paragraphs.append(" ".join(row_texts))
                        
            return paragraphs
        elif suffix == ".pdf":
            from pypdf import PdfReader
            paragraphs = []
            reader = PdfReader(self.sap_path)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    for line in text.split("\n"):
                        clean_line = line.strip()
                        if clean_line:
                            paragraphs.append(clean_line)
            return paragraphs
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

    def extract_full_text(self) -> str:
        """Extract full text content."""
        paragraphs = self.read_paragraphs()
        return "\n".join(paragraphs)


class TLFExtractor:
    """Extracts TLF (Table, Figure, Listing) information from SAP text."""

    # Regex patterns for TLF IDs
    PATTERNS = {
        'table': re.compile(
            r'Table\s+(14\.\d+\.\d+\.\d+|14\.\d+\.\d+\.\d+\.\d+|\d+)\s*:\s*([^\-]+?)(?:\s*[-–—]\s*(.+))?$|'
            r'Table\s+(14\.\d+\.\d+\.\d+)\s*[:-]?\s*([^\-]+?)(?:\s*[-–—]\s*(.+))?$',
            re.IGNORECASE | re.MULTILINE
        ),
        'figure': re.compile(
            r'Figure\s+(14\.\d+\.\d+\.\d+|14\.\d+\.\d+\.\d+\.\d+|\d+)\s*:\s*([^\-]+?)(?:\s*[-–—]\s*(.+))?$|'
            r'Figure\s+(14\.\d+\.\d+\.\d+)\s*[:-]?\s*([^\-]+?)(?:\s*[-–—]\s*(.+))?$',
            re.IGNORECASE | re.MULTILINE
        ),
        'listing': re.compile(
            r'Listing\s+(16\.\d+\.\d+\.\d+\.\d+|16\.\d+\.\d+\.\d+)\s*:\s*([^\-]+?)(?:\s*[-–—]\s*(.+))?$|'
            r'Listing\s+(16\.\d+\.\d+\.\d+)\s*[:-]?\s*([^\-]+?)(?:\s*[-–—]\s*(.+))?$',
            re.IGNORECASE | re.MULTILINE
        ),
        # Simpler pattern for cleaner matches
        'table_simple': re.compile(r'Table\s+(14\.\d+\.\d+\.\d+[\d\.]*)\s*[:\-]\s*([^\-]+?)(?:\s*[-–—]\s*(.+))?$', re.I),
        'figure_simple': re.compile(r'Figure\s+(14\.\d+\.\d+\.\d+[\d\.]*)\s*[:\-]\s*([^\-]+?)(?:\s*[-–—]\s*(.+))?$', re.I),
        'listing_simple': re.compile(r'Listing\s+(16\.\d+\.\d+\.\d+[\d\.]*)\s*[:\-]\s*([^\-]+?)(?:\s*[-–—]\s*(.+))?$', re.I),
    }

    def __init__(self, sap_text: str):
        self.sap_text = sap_text

    def extract_all(self) -> List[Dict]:
        """Extract all TLF entries."""
        results = []

        for line in self.sap_text.split('\n'):
            line = line.strip()
            if not line:
                continue

            # Normalize whitespace (replace multiple spaces with single space)
            line = re.sub(r'\s+', ' ', line)

            # Try to match Table
            table_match = self._match_tlf(line, 'table', 'Table')
            if table_match:
                # Filter out SAP internal tables (only keep 14.x.x.x and 16.x.x.x)
                tlf_id = table_match['tlf_id']
                if re.search(r'(14\.\d+|16\.\d+)', tlf_id, re.I):
                    results.append(table_match)
                continue

            # Try to match Figure
            figure_match = self._match_tlf(line, 'figure', 'Figure')
            if figure_match:
                # Filter to only Figure 14.x.x.x
                tlf_id = figure_match['tlf_id']
                if re.search(r'14\.\d+', tlf_id, re.I):
                    results.append(figure_match)
                continue

            # Try to match Listing
            listing_match = self._match_tlf(line, 'listing', 'Listing')
            if listing_match:
                # Filter to only Listing 16.x.x.x
                tlf_id = listing_match['tlf_id']
                if re.search(r'16\.\d+', tlf_id, re.I):
                    results.append(listing_match)

        return results

    def _match_tlf(self, line: str, tlf_type: str, type_prefix: str) -> Optional[Dict]:
        """Match a single TLF line."""
        # Determine ID pattern based on type: allow 2 to 5 levels (e.g. 14.2.1 or 16.2.1.1)
        if type_prefix == 'Listing':
            id_pattern = r'(16\.\d+(?:\.\d+){1,4}[\d\.]*)'
        else:
            id_pattern = r'(14\.\d+(?:\.\d+){1,4}[\d\.]*)'

        # Try colon/dash-based pattern first (Table, Listing, Figure)
        pattern = rf'{type_prefix}\s+{id_pattern}\s*[:\-\u2013\u2014]\s*(.+)$'

        match = re.search(pattern, line, re.IGNORECASE)
        if not match:
            # Try space-based pattern (often no colon for Figures)
            pattern = rf'{type_prefix}\s+{id_pattern}\s+(.+?)(?:\s*[-–—]\s+(.+))?$'
            match = re.search(pattern, line, re.IGNORECASE)

        if match:
            tlf_id = match.group(1).strip()
            rest = match.group(2).strip() if match.group(2) else ""

            # Try to split by common population markers
            # Population typically ends with "Analysis Set", "All Subjects", etc.
            pop_patterns = [
                r'(.+?)\s+(Enrolled Analysis Set)$',
                r'(.+?)\s+(Safety Analysis Set)$',
                r'(.+?)\s+(Response Evaluable Set)$',
                r'(.+?)\s+(PK Analysis Set)$',
                r'(.+?)\s+(Pharmacokinetic Analysis Set)$',
                r'(.+?)\s+(Full Analysis Set)$',
                r'(.+?)\s+(Per-Protocol Set)$',
                r'(.+?)\s+(Treated Set)$',
                r'(.+?)\s+(All Subjects)$',
                r'(.+?)\s+(All Screened Subjects)$',
                r'(.+?)\s+(Screened Subjects)$',
                r'(.+?)\s+(Subjects)$',
            ]

            tlf_name = rest
            population = ""

            for pop_pat in pop_patterns:
                pop_match = re.match(pop_pat, rest, re.IGNORECASE)
                if pop_match:
                    tlf_name = pop_match.group(1).strip()
                    population = pop_match.group(2).strip()
                    break

            # Clean up the name (remove trailing punctuation, etc.)
            tlf_name = re.sub(r'\s*[-–—\u2013\u2014:\s]+\s*$', '', tlf_name).strip()
            tlf_name = re.sub(r'\s+', ' ', tlf_name)

            # Standardize population names
            population = self._standardize_population(population)

            return {
                'tlf_type': tlf_type.capitalize(),
                'tlf_id': f"{type_prefix} {tlf_id}",
                'tlf_name': tlf_name,
                'population': population,
                'raw_line': line
            }

        return None

    def _standardize_population(self, population: str) -> str:
        """Standardize population names."""
        if not population:
            return ""

        population = population.strip()

        # Common population mappings
        mappings = {
            'enrolled analysis set': 'Enrolled Analysis Set',
            'safety analysis set': 'Safety Analysis Set',
            'response evaluable set': 'Response Evaluable Set',
            'pk analysis set': 'PK Analysis Set',
            'pharmacokinetic analysis set': 'PK Analysis Set',
            'full analysis set': 'Full Analysis Set',
            'per-protocol set': 'Per-Protocol Set',
            'treated set': 'Treated Set',
            'all subjects': 'All Subjects',
            'all screened subjects': 'All Screened Subjects',
        }

        population_lower = population.lower()
        for key, value in mappings.items():
            if key in population_lower:
                return value

        return population

    def extract_tables(self) -> List[Dict]:
        """Extract only Table entries."""
        return [r for r in self.extract_all() if r['tlf_type'] == 'Table']

    def extract_figures(self) -> List[Dict]:
        """Extract only Figure entries."""
        return [r for r in self.extract_all() if r['tlf_type'] == 'Figure']

    def extract_listings(self) -> List[Dict]:
        """Extract only Listing entries."""
        return [r for r in self.extract_all() if r['tlf_type'] == 'Listing']


def infer_population_from_name(tlf_name: str, tlf_id: str = "") -> str:
    """
    Infer population from TLF name and ID.

    Looks for keywords in the name that indicate specific populations.

    Args:
        tlf_name: The TLF name/title
        tlf_id: The TLF ID (optional, for additional context)

    Returns:
        The inferred population string
    """
    name_lower = tlf_name.lower()

    # Check for Safety Analysis Set
    if '(safety' in name_lower or 'safety analysis set' in name_lower:
        return 'Safety Analysis Set'

    # Check for Response Evaluable Set
    if '(response evaluable' in name_lower or 'response evaluable' in name_lower:
        return 'Response Evaluable Set'

    # Check for PK/Pharmacokinetic
    if ' pk ' in name_lower or 'pharmacokinetic' in name_lower:
        return 'PK Analysis Set'

    # Check for Per-Protocol
    if 'per-protocol' in name_lower:
        return 'Per-Protocol Set'

    # Check for Full Analysis Set
    if 'full analysis' in name_lower:
        return 'Full Analysis Set'

    # Section-based defaults (E3 standard)
    # Section 14.1.x - Demographic (Enrolled Analysis Set)
    # Section 14.2.x - Efficacy (generally Response Evaluable or Enrolled)
    # Section 14.3.x - Safety (Safety Analysis Set)
    # Section 14.4.x - PK (PK Analysis Set)

    if tlf_id:
        section = tlf_id.split()[1] if ' ' in tlf_id else tlf_id  # e.g., "14.3.1" from "Table 14.3.1"
        if section.startswith('14.3'):  # Safety sections
            return 'Safety Analysis Set'
        elif section.startswith('14.4'):  # PK sections
            return 'PK Analysis Set'
        elif section.startswith('14.2'):  # Efficacy sections
            return 'Response Evaluable Set'

    # Default
    return 'Enrolled Analysis Set'


class ICH3TLFInferencer:
    """
    Infers TLF IDs from SAP section headings using ICH E3 knowledge base.

    When SAP doesn't have explicit 'Table 14.x.x.x:' references, this class
    maps SAP section names to appropriate TLF
    """
    SECTION_KEYWORDS = [
        # Section 14.1 / 16.2.1 - Demographic / Disposition Data & Listings
        ('disposition', '14.1.1', 'Table', 'Subject Disposition'),
        ('disposition', '16.2.1', 'Listing', 'Subject Disposition'),
        ('subject disposition', '14.1.1', 'Table', 'Subject Disposition'),
        ('subject disposition', '16.2.1', 'Listing', 'Subject Disposition'),
        ('protocol deviation', '14.1.1.2', 'Table', 'Major Protocol Deviations'),
        ('protocol deviation', '16.2.2.4', 'Listing', 'Protocol Deviations'),
        ('major protocol deviation', '14.1.1.2', 'Table', 'Major Protocol Deviations'),
        ('major protocol deviation', '16.2.2.4', 'Listing', 'Protocol Deviations'),
        ('exclusion', '14.1.1.3', 'Table', 'Subjects Excluded from Analysis Sets'),
        ('excluded from analysis', '14.1.1.3', 'Table', 'Subjects Excluded from Analysis Sets'),
        ('demographic', '14.1.2', 'Table', 'Demographic and Baseline Characteristics'),
        ('demographic', '16.2.4.1', 'Listing', 'Demographics'),
        ('baseline characteristic', '14.1.2', 'Table', 'Demographic and Baseline Characteristics'),
        ('baseline characteristic', '16.2.4.1', 'Listing', 'Demographics'),
        ('medical history', '14.1.3', 'Table', 'Medical History / Prior Disease'),
        ('medical history', '16.2.4.3.1', 'Listing', 'Medical/Surgical History'),
        ('prior disease', '14.1.3', 'Table', 'Medical History / Prior Disease'),
        ('prior disease', '16.2.4.3.1', 'Listing', 'Medical/Surgical History'),
        ('prior medication', '14.1.4', 'Table', 'Prior/Concomitant Medications'),
        ('prior medication', '16.2.4.5', 'Listing', 'Prior/Concomitant Medications'),
        ('concomitant medication', '14.1.4', 'Table', 'Prior/Concomitant Medications'),
        ('concomitant medication', '16.2.4.5', 'Listing', 'Prior/Concomitant Medications'),
        ('exposure', '14.1.5', 'Table', 'Study Drug Exposure'),
        ('exposure', '16.2.5.1.2', 'Listing', 'Study Drug Exposure'),

        # Section 14.2 / 16.2.6 - Efficacy Data, Listings & Figures
        ('best overall response', '14.2.1', 'Table', 'Best Overall Response'),
        ('overall response', '14.2.1', 'Table', 'Best Overall Response'),
        ('orr', '14.2.1', 'Table', 'Best Overall Response'),
        ('duration of response', '14.2.2', 'Table', 'Duration of Response / Survival'),
        ('survival', '14.2.2', 'Table', 'Duration of Response / Survival'),
        ('progression-free survival', '14.2.2.2', 'Table', 'Progression-Free Survival (PFS)'),
        ('progression-free survival', '14.2.2', 'Figure', 'Kaplan-Meier Plot of Progression-Free Survival (PFS)'),
        ('pfs', '14.2.2.2', 'Table', 'Progression-Free Survival (PFS)'),
        ('pfs', '14.2.2', 'Figure', 'Kaplan-Meier Plot of Progression-Free Survival (PFS)'),
        ('overall survival', '14.2.2.3', 'Table', 'Overall Survival (OS)'),
        ('overall survival', '14.2.1', 'Figure', 'Kaplan-Meier Plot of Overall Survival'),
        ('os', '14.2.2.3', 'Table', 'Overall Survival (OS)'),
        ('os', '14.2.1', 'Figure', 'Kaplan-Meier Plot of Overall Survival'),
        ('tumor response', '14.2.3', 'Table', 'Tumor Response - Change from Baseline'),
        ('change from baseline', '14.2.3', 'Table', 'Tumor Response - Change from Baseline'),
        ('disease control rate', '14.2.4', 'Table', 'Disease Control Rate'),
        ('dcr', '14.2.4', 'Table', 'Disease Control Rate'),
        ('cbr', '14.2.4', 'Table', 'Disease Control Rate'),
        ('clinical benefit rate', '14.2.4', 'Table', 'Disease Control Rate'),
        ('subgroup analysis', '14.2.5', 'Table', 'Subgroup Analyses'),

        # Section 14.3 / 16.2.7 / 16.2.8 - Safety Data, Listings & Figures
        ('treatment-emergent adverse event', '14.3.1', 'Table', 'Treatment-Emergent Adverse Events (TEAE)'),
        ('treatment-emergent adverse event', '16.2.7.1', 'Listing', 'Adverse Events'),
        ('tea', '14.3.1', 'Table', 'Treatment-Emergent Adverse Events (TEAE)'),
        ('tea', '16.2.7.1', 'Listing', 'Adverse Events'),
        ('adverse event', '14.3.1', 'Table', 'Treatment-Emergent Adverse Events (TEAE)'),
        ('adverse event', '16.2.7.1', 'Listing', 'Adverse Events'),
        ('ae', '14.3.1', 'Table', 'Treatment-Emergent Adverse Events (TEAE)'),
        ('ae', '16.2.7.1', 'Listing', 'Adverse Events'),
        ('serious adverse event', '14.3.1.3.1', 'Table', 'Treatment-emergent SAEs by SOC, PT and Worst CTCAE Grade'),
        ('serious adverse event', '16.2.7.2', 'Listing', 'Serious Adverse Events'),
        ('sae', '14.3.1.3.1', 'Table', 'Treatment-emergent SAEs by SOC, PT and Worst CTCAE Grade'),
        ('sae', '16.2.7.2', 'Listing', 'Serious Adverse Events'),
        ('death', '14.3.2.1', 'Table', 'Death by Primary Cause and Preferred Term'),
        ('death', '16.2.1.4', 'Listing', 'Death by Subject'),
        ('laboratory', '14.3.4', 'Table', 'Laboratory Values'),
        ('laboratory', '16.2.8.1.1', 'Listing', 'Laboratory Parameters - Hematology'),
        ('vital sign', '14.3.5', 'Table', 'Vital Signs and ECG'),
        ('vital sign', '16.2.8.3.1', 'Listing', 'Vital Signs'),
        ('ecg', '14.3.5', 'Table', 'Vital Signs and ECG'),
        ('electrocardiogram', '14.3.5', 'Table', 'Vital Signs and ECG'),
        ('physical examination', '14.3.6', 'Table', 'Physical Examination'),
        ('physical examination', '16.2.8.3.3', 'Listing', 'Physical Examination'),
        ('cardiac safety', '14.3.7', 'Table', 'Cardiac Safety / Imaging'),
        ('imaging', '14.3.7', 'Table', 'Cardiac Safety / Imaging'),

        # Section 14.4 - PK Data
        ('pharmacokinetic', '14.4.1', 'Table', 'Serum Concentrations'),
        ('pk', '14.4.1', 'Table', 'Serum Concentrations'),
        ('serum concentration', '14.4.1', 'Table', 'Serum Concentrations'),
        ('immunogenicity', '14.4.7', 'Table', 'Immunogenicity (ADA)'),
        ('ada', '14.4.7', 'Table', 'Immunogenicity (ADA)'),
        ('biomarker', '14.4.8', 'Table', 'Biomarkers'),

        # Section 14.2/14.3 Figures
        ('kaplan-meier', '14.2.1', 'Figure', 'Kaplan-Meier Plot of Overall Survival'),
        ('km plot', '14.2.1', 'Figure', 'Kaplan-Meier Plot of Overall Survival'),
        ('waterfall', '14.2.4.1', 'Figure', 'Waterfall Plot of Best Percentage Change from Baseline'),
        ('swimmer', '14.2.4.3', 'Figure', 'Swimmer Plot of Treatment Duration'),
        ('box plot', '14.3.3', 'Figure', 'Box-Whisker Plot of Laboratory Parameters'),
        ('box-whisker', '14.3.3', 'Figure', 'Box-Whisker Plot of Laboratory Parameters'),

        # Section 16.2 Listings
        ('subject disposition listing', '16.2.1', 'Listing', 'Subject Disposition'),
        ('death listing', '16.2.1', 'Listing', 'Death by Subject'),
        ('demographics listing', '16.2.4', 'Listing', 'Demographics'),
        ('pregnancy listing', '16.2.4', 'Listing', 'Pregnancy Test Results'),
        ('adverse event listing', '16.2.7', 'Listing', 'Adverse Events'),
        ('ae listing', '16.2.7', 'Listing', 'Adverse Events'),
        ('laboratory listing', '16.2.8', 'Listing', 'Laboratory and Vital Signs'),
        ('vital sign listing', '16.2.8', 'Listing', 'Laboratory and Vital Signs'),
    ]

    def __init__(self, sap_text: str):
        self.sap_text = sap_text
        self._build_keyword_index()

    def _build_keyword_index(self):
        """Build an inverted index mapping keywords to ICH E3 sections."""
        self.keyword_to_section = {}
        for keyword, section, tlf_type, name in self.SECTION_KEYWORDS:
            if keyword not in self.keyword_to_section:
                self.keyword_to_section[keyword] = []
            self.keyword_to_section[keyword].append({
                'section': section,
                'tlf_type': tlf_type,
                'name': name
            })

    def infer_tlf_ids(self) -> List[Dict]:
        """
        Infer TLF IDs from SAP text using ICH E3 knowledge base.

        Returns:
            List of dicts with tlf_id, tlf_name, tlf_type, population, inferred
        """
        results = []
        seen_ids = set()

        # First, try to extract explicit TLF references
        explicit_extractor = TLFExtractor(self.sap_text)
        explicit_entries = explicit_extractor.extract_all()

        for entry in explicit_entries:
            tlf_id = entry['tlf_id']
            if tlf_id not in seen_ids:
                seen_ids.add(tlf_id)
                entry['inferred'] = False
                results.append(entry)

        # Then, infer from section headings using ICH E3 knowledge base
        inferred_entries = self._infer_from_ich_e3()

        for entry in inferred_entries:
            tlf_id = entry['tlf_id']
            if tlf_id not in seen_ids:
                seen_ids.add(tlf_id)
                entry['inferred'] = True
                results.append(entry)

        return results

    def _infer_from_ich_e3(self) -> List[Dict]:
        """Infer TLF entries from SAP text using ICH E3 knowledge base."""
        results = []
        sap_lower = self.sap_text.lower()

        # Check each keyword against SAP text
        for keyword, entries in self.keyword_to_section.items():
            if keyword in sap_lower:
                for entry_info in entries:
                    section = entry_info['section']
                    tlf_type = entry_info['tlf_type']
                    name = entry_info['name']

                    # Get sub-items from ICH E3 templates
                    if tlf_type == 'Listing':
                        template = LISTING_TEMPLATES.get(section, {})
                    elif tlf_type == 'Figure':
                        template = FIGURE_TEMPLATES.get(section, {})
                    else:
                        template = TLF_TEMPLATES.get(section, {})

                    sub_items = template.get('sub_items', {})

                    if not sub_items:
                        # Use base section
                        tlf_id = f'{tlf_type} {section}'
                        results.append({
                            'tlf_type': tlf_type,
                            'tlf_id': tlf_id,
                            'tlf_name': name,
                            'population': infer_population_from_name(name, tlf_id),
                            'raw_line': f'Inferred from keyword: {keyword}'
                        })
                    else:
                        # Add all sub-items
                        for sub_key, sub_name in sub_items.items():
                            tlf_id = f'{tlf_type} {section}.{sub_key}'
                            results.append({
                                'tlf_type': tlf_type,
                                'tlf_id': tlf_id,
                                'tlf_name': sub_name,
                                'population': infer_population_from_name(sub_name, tlf_id),
                                'raw_line': f'Inferred from keyword: {keyword}'
                            })

        return results


class TOCGenerator:
    """Generates Table of Contents for TLF documents."""

    def __init__(self, tlf_entries: List[Dict]):
        self.entries = tlf_entries

    def to_dataframe(self) -> pd.DataFrame:
        """Convert to pandas DataFrame."""
        df = pd.DataFrame(self.entries)
        # Select and reorder columns
        if 'tlf_id' in df.columns and 'tlf_name' in df.columns and 'population' in df.columns and 'tlf_type' in df.columns:
            df = df[['tlf_id', 'tlf_name', 'population', 'tlf_type']]
        return df

    def to_csv(self, output_path: str, include_type: bool = True):
        """Save to CSV file."""
        df = self.to_dataframe()
        if not include_type:
            df = df[['tlf_id', 'tlf_name', 'population']]
        df.to_csv(output_path, index=False)
        return output_path

    def to_excel(self, output_path: str):
        """Save to Excel file."""
        df = self.to_dataframe()
        df.to_excel(output_path, index=False)
        return output_path

    def filter_by_type(self, tlf_type: str) -> 'TOCGenerator':
        """Filter by TLF type (Table, Figure, Listing)."""
        filtered = [e for e in self.entries if e['tlf_type'].lower() == tlf_type.lower()]
        return TOCGenerator(filtered)

    def filter_by_count(self, limit: int) -> 'TOCGenerator':
        """Limit to first N entries."""
        return TOCGenerator(self.entries[:limit])

    def summary(self) -> Dict:
        """Get summary statistics."""
        return {
            'total': len(self.entries),
            'tables': len([e for e in self.entries if e['tlf_type'] == 'Table']),
            'figures': len([e for e in self.entries if e['tlf_type'] == 'Figure']),
            'listings': len([e for e in self.entries if e['tlf_type'] == 'Listing']),
        }


def generate_toc_from_sap(
    sap_path: str,
    output_path: str,
    limit: Optional[int] = None,
    tlf_type: Optional[str] = None,
    output_format: str = 'csv',
    use_ich_e3_inference: bool = True
) -> str:
    """
    Generate TOC from SAP document.

    Args:
        sap_path: Path to SAP document (DOCX)
        output_path: Path for output file
        limit: Optional limit on number of entries
        tlf_type: Optional filter ('table', 'figure', 'listing')
        output_format: 'csv' or 'excel'
        use_ich_e3_inference: Whether to use ICH E3 knowledge base for inference

    Returns:
        Path to generated output file
    """
    # Read SAP
    reader = SAPReader(sap_path)
    sap_text = reader.extract_full_text()

    # Extract or infer TLF entries
    if use_ich_e3_inference:
        inferencer = ICH3TLFInferencer(sap_text)
        entries = inferencer.infer_tlf_ids()
    else:
        extractor = TLFExtractor(sap_text)
        entries = extractor.extract_all()

    # Filter by type if specified
    if tlf_type:
        entries = [e for e in entries if e['tlf_type'].lower() == tlf_type.lower()]

    # Apply limit if specified
    if limit:
        entries = entries[:limit]

    # Generate TOC
    generator = TOCGenerator(entries)

    # Save output
    if output_format == 'excel':
        result_path = generator.to_excel(output_path)
    else:
        result_path = generator.to_csv(output_path)

    return result_path


def generate_full_toc_from_ich_e3(output_path: str, output_format: str = 'csv') -> str:
    """
    Generate complete TOC from ICH E3 knowledge base.

    This generates all possible TLF entries based on the ICH E3 guideline,
    regardless of what content is found in the SAP.

    Args:
        output_path: Path for output file
        output_format: 'csv' or 'excel'

    Returns:
        Path to generated output file
    """
    entries = []

    # Section 14 Tables
    for section, info in TLF_TEMPLATES.items():
        sub_items = info.get('sub_items', {})
        if not sub_items:
            tlf_id = f'Table {section}'
            entries.append({
                'tlf_type': 'Table',
                'tlf_id': tlf_id,
                'tlf_name': info['name'],
                'population': infer_population_from_name(info['name'], tlf_id)
            })
        else:
            for sub_key, sub_name in sub_items.items():
                tlf_id = f'Table {section}.{sub_key}'
                entries.append({
                    'tlf_type': 'Table',
                    'tlf_id': tlf_id,
                    'tlf_name': sub_name,
                    'population': infer_population_from_name(sub_name, tlf_id)
                })

    # Section 14 Figures
    for section, info in FIGURE_TEMPLATES.items():
        sub_items = info.get('sub_items', {})
        if not sub_items:
            tlf_id = f'Figure {section}'
            entries.append({
                'tlf_type': 'Figure',
                'tlf_id': tlf_id,
                'tlf_name': info['name'],
                'population': infer_population_from_name(info['name'], tlf_id)
            })
        else:
            for sub_key, sub_name in sub_items.items():
                tlf_id = f'Figure {section}.{sub_key}'
                entries.append({
                    'tlf_type': 'Figure',
                    'tlf_id': tlf_id,
                    'tlf_name': sub_name,
                    'population': infer_population_from_name(sub_name, tlf_id)
                })

    # Section 16.2 Listings
    for section, info in LISTING_TEMPLATES.items():
        sub_items = info.get('sub_items', {})
        if not sub_items:
            tlf_id = f'Listing {section}'
            entries.append({
                'tlf_type': 'Listing',
                'tlf_id': tlf_id,
                'tlf_name': info['name'],
                'population': infer_population_from_name(info['name'], tlf_id)
            })
        else:
            for sub_key, sub_name in sub_items.items():
                tlf_id = f'Listing {section}.{sub_key}'
                entries.append({
                    'tlf_type': 'Listing',
                    'tlf_id': tlf_id,
                    'tlf_name': sub_name,
                    'population': infer_population_from_name(sub_name, tlf_id)
                })

    generator = TOCGenerator(entries)

    if output_format == 'excel':
        result_path = generator.to_excel(output_path)
    else:
        result_path = generator.to_csv(output_path)

    return result_path


class AITOCInferencer:
    """临床试验统计分析计划（SAP）大语言模型智能 TOC 提炼引擎。"""

    def __init__(self, sap_path: str):
        self.sap_path = sap_path

    async def infer_with_ai(self) -> List[Dict]:
        """
        通过大模型智能解析 SAP.docx 正文，提取标准的 TOC 报表清单。
        自动过滤无关目录页干扰，双分段并发调用以规避 Token 溢出与截断。
        """
        import os
        import re
        import json
        import asyncio
        from docx import Document
        
        # 1. 读取并分段 Word 文档（使用增强的 SAPReader 提取段落与表格）
        try:
            reader = SAPReader(self.sap_path)
            paragraphs = reader.read_paragraphs()
        except Exception as e:
            print(f"Failed to read docx in AITOCInferencer: {e}")
            return []

        # 2. 清除大纲目录（TABLE OF CONTENTS）所在块
        toc_start = -1
        for idx, p in enumerate(paragraphs):
            if "TABLE OF CONTENTS" in p.upper():
                toc_start = idx
                break
                
        intro_start = -1
        if toc_start != -1:
            for idx, p in enumerate(paragraphs[toc_start + 1:], toc_start + 1):
                p_upper = p.upper()
                if "INTRODUCTION" in p_upper and not re.search(r'[\t\.\s_]+\d+$', p):
                    intro_start = idx
                    break
            if intro_start == -1:
                for idx, p in enumerate(paragraphs[toc_start + 1:], toc_start + 1):
                    p_upper = p.upper()
                    if "STUDY OBJECTIVES" in p_upper and not re.search(r'[\t\.\s_]+\d+$', p):
                        intro_start = idx
                        break

        if intro_start != -1:
            body_paras = paragraphs[intro_start:]
        elif toc_start != -1:
            body_paras = paragraphs[toc_start:]
        else:
            body_paras = paragraphs

        # 3. 规避 Token 截断，将纯净正文均匀切为前后两大段并发执行，确保全量召回 80+ 条目
        total_paras = len(body_paras)
        half = total_paras // 2
        chunk1_text = "\n".join(body_paras[:half])
        chunk2_text = "\n".join(body_paras[half:])

        # 4. 动态导入系统统一初始化的 LLM 客户端与模型配置，防止底层工具库引起循环导入
        try:
            from backend.services.ai.config import deepseek_client, MODEL_NAME
            model_to_use = MODEL_NAME
        except ImportError:
            try:
                from services.ai.config import deepseek_client, MODEL_NAME
                model_to_use = MODEL_NAME
            except ImportError:
                from openai import AsyncOpenAI
                deepseek_client = AsyncOpenAI(
                    api_key=os.environ.get("DEEPSEEK_API_KEY", "mock-key-for-local-testing"),
                    base_url="https://api.deepseek.com"
                )
                model_to_use = "deepseek-v4-flash"

        system_prompt = """你是一位资深的临床试验医学统计师（Clinical Biostatistician）。
你的任务是阅读给定的临床试验统计分析计划（SAP）文档正文片段，并根据统计学描述推导出应该生成的标准 TOC（Table of Contents）目录清单。

**你需要遵守以下提取准则**：
1. **识别范围**：提取出所有正文叙述中明确要求总结、分析、绘制的数据报表（包含 Table 14.x.x.x, Figure 14.x.x.x, Listing 16.x.x.x 等类型）。
2. **推导 ID 规范**：
   - 表格 ID 通常归类在 Section 14.1 (受受试者特征/方案偏离)、Section 14.3 (安全性如不良事件AE和实验室指标Lab)、Section 14.4 (PK 参数汇总)。例如: Table 14.1.1.1, Table 14.3.4.2。
   - 图表 Figure ID 通常包含疗效图表（瀑布图、蜘蛛图、生存KM曲线图），如 Figure 14.2.4.1。
   - 列表 Listing ID 属于患者明细列表，如 Listing 16.2.1.1, Listing 16.2.7.1。
3. **提取字段**：
   - `tlf_id`: 生成规范的 ID，例如 "Table 14.1.1.1"（包含类型前缀，用点号连接）。
   - `tlf_name`: 报告表的官方英文名称，如 "Subject Disposition", "Demographic and Baseline Characteristics"。
   - `tlf_type`: 必须为以下三者之一: "Table", "Figure", "Listing"。
   - `population`: 识别分析时所用的患者分析人群，如 "Safety Analysis Set", "Enrolled Analysis Set", "Pharmacokinetic Analysis Set"。如果文中没有提到，可留空。
4. **输出格式**：你必须且只能以 JSON 格式输出，不要包含任何额外的 markdown 标记（不要包裹在 ```json 这样的块中）或说明解释。输出结构为 JSON 数组：
[
  {"tlf_id": "Table 14.1.1.1", "tlf_name": "Subject Disposition", "tlf_type": "Table", "population": "All Screened Subjects"},
  ...
]
"""

        async def call_llm(chunk_text):
            if len(chunk_text.split()) < 10:
                return []
            user_prompt = f"以下是 SAP 文档正文内容片段。请仔细阅读并提取所有需要生成的 TOC 条目：\n\n{chunk_text}"
            try:
                response = await deepseek_client.chat.completions.create(
                    model=model_to_use,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.1,
                    timeout=60.0
                )
                raw_content = response.choices[0].message.content.strip()
                if raw_content.startswith("```json"):
                    raw_content = raw_content[7:]
                if raw_content.endswith("```"):
                    raw_content = raw_content[:-3]
                raw_content = raw_content.strip()
                return json.loads(raw_content)
            except Exception as exc:
                print(f"Error in call_llm for chunk: {exc}")
                raise exc

        # 并发发起请求，确保分段全量提取出 80 多个条目
        results = await asyncio.gather(
            call_llm(chunk1_text),
            call_llm(chunk2_text)
        )

        # 合并去重并整理
        combined = []
        seen_ids = set()
        for res in results:
            if not isinstance(res, list):
                continue
            for entry in res:
                tid = entry.get("tlf_id", "").strip()
                if tid and tid.lower() not in seen_ids:
                    seen_ids.add(tid.lower())
                    combined.append(entry)

        # 升序排序
        combined.sort(key=lambda x: x.get("tlf_id", ""))
        return combined


if __name__ == "__main__":
    # Test with sample SAP
    base = Path("d:/hello world/clinical-data-process")
    sap_path = base / "input/SAP/SAP.docx"
    output_path = base / "output/toc_test.csv"

    # Generate full TOC
    result = generate_toc_from_sap(
        sap_path=str(sap_path),
        output_path=str(output_path),
        output_format='csv',
        use_ich_e3_inference=True
    )

    print(f"TOC generated: {result}")

    # Load and display
    df = pd.read_csv(result)
    print(f"\nTotal entries: {len(df)}")
    print(f"\nSummary:")
    print(df['tlf_type'].value_counts())
    print(f"\nFirst 10 rows:")
    print(df.head(10))