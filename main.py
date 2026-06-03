"""
Main CLI entry point for the TLF generation system.

Architecture:
    - reference/: Stable reference knowledge (SAS Macros, TLF templates, ADaM specs)
    - input/: Project-specific data (ADaM datasets, SAP documents)
    - knowledge/: RAG index cache
    - output/: Generated TLF programs
"""

import argparse
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.agents import OrchestratorAgent
from src.rag import RAGRetriever


def get_default_paths():
    """Get default paths based on directory structure."""
    base_dir = os.path.dirname(os.path.abspath(__file__))

    return {
        'reference': os.path.join(base_dir, 'reference'),
        'input': os.path.join(base_dir, 'input'),
        'knowledge': os.path.join(base_dir, 'knowledge'),
        'output': os.path.join(base_dir, 'output'),
    }


def main():
    parser = argparse.ArgumentParser(
        description="AI Agent for generating TLF reports from ADaM datasets"
    )

    # Path arguments
    parser.add_argument(
        "--reference-dir",
        type=str,
        default=None,
        help="Path to reference directory (SAS Macros, TLF templates)"
    )

    parser.add_argument(
        "--input-dir",
        type=str,
        default=None,
        help="Path to input directory (ADaM datasets, SAP)"
    )

    parser.add_argument(
        "--knowledge-dir",
        type=str,
        default=None,
        help="Path to knowledge/cache directory"
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Path to output directory"
    )

    # TLF generation arguments
    parser.add_argument(
        "--table-id",
        type=str,
        default="14.1.1.1",
        help="Table ID (e.g., 14.1.1.1)"
    )

    parser.add_argument(
        "--analysis-type",
        type=str,
        default="disposition",
        choices=["disposition", "protocol_deviation", "exclusion", "demographics", "ae_summary", "efficacy", "survival", "response"],
        help="Type of analysis"
    )

    parser.add_argument(
        "--dataset",
        type=str,
        default="adsl",
        help="ADaM dataset name (e.g., adsl, adae)"
    )

    parser.add_argument(
        "--sap-file",
        type=str,
        default=None,
        help="Path to SAP file (PDF or DOCX)"
    )

    parser.add_argument(
        "--adam-dir",
        type=str,
        default=None,
        help="Path to ADaM datasets directory"
    )

    # Utility arguments
    parser.add_argument(
        "--build-index",
        action="store_true",
        help="Rebuild the RAG indexes from reference"
    )

    parser.add_argument(
        "--list-tables",
        action="store_true",
        help="List available table IDs"
    )

    parser.add_argument(
        "--show-paths",
        action="store_true",
        help="Show default paths"
    )

    # Direct report generation (Python-based, no SAS)
    parser.add_argument(
        "--direct",
        action="store_true",
        help="Generate PDF directly using Python (pyreadstat + reportlab)"
    )

    # TOC generation
    parser.add_argument(
        "--generate-toc",
        action="store_true",
        help="Generate Table of Contents from SAP document"
    )

    parser.add_argument(
        "--full-toc",
        action="store_true",
        help="Generate full TOC from ICH E3 knowledge base (all possible TLF entries)"
    )

    parser.add_argument(
        "--toc-limit",
        type=int,
        default=None,
        help="Limit number of TLF entries in TOC (default: all)"
    )

    parser.add_argument(
        "--toc-type",
        type=str,
        choices=["table", "figure", "listing"],
        help="Filter TOC by TLF type"
    )

    parser.add_argument(
        "--toc-output",
        type=str,
        default=None,
        help="Output path for TOC CSV file"
    )

    args = parser.parse_args()

    # Get paths
    paths = get_default_paths()

    reference_dir = args.reference_dir or paths['reference']
    input_dir = args.input_dir or paths['input']
    knowledge_dir = args.knowledge_dir or paths['knowledge']
    output_dir = args.output_dir or paths['output']

    # Show paths if requested
    if args.show_paths:
        print("\nDefault Paths:")
        print("-" * 50)
        for name, path in paths.items():
            exists = "EXISTS" if os.path.exists(path) else "NOT FOUND"
            print(f"  {name}: {path} [{exists}]")
        print("-" * 50)
        return 0

    # List tables if requested
    if args.list_tables:
        tables = [
            ("14.1.1.1", "Subject Disposition", "ADaM.ADSL"),
            ("14.1.1.2", "Major Protocol Deviation", "ADaM.ADSL"),
            ("14.1.2.1", "Demographic and Baseline Characteristics", "ADaM.ADSL"),
            ("14.1.3.1", "Medical History", "ADaM.ADSL"),
            ("14.1.4.1", "Prior/Concomitant Therapy", "ADaM.ADSL"),
            ("14.1.5.1", "Exposure", "ADaM.ADEX"),
            ("14.2.1.1", "Best Overall Response", "ADaM.ADRS"),
            ("14.2.2.2", "Efficacy Analysis", "ADaM.ADRS"),
            ("14.2.4.1", "Survival Analysis", "ADaM.ADRS"),
            ("14.3.1.1", "Overall Summary of TEAE", "ADaM.ADAE"),
            ("14.3.2.1", "Adverse Event Analysis", "ADaM.ADAE"),
        ]
        print("\nAvailable Tables:")
        print("-" * 60)
        for tid, name, ds in tables:
            print(f"  {tid}: {name} ({ds})")
        print("-" * 60)
        return 0

    # Validate reference directory
    if not os.path.exists(reference_dir):
        print(f"\nError: Reference directory not found: {reference_dir}")
        print("Please specify --reference-dir or ensure the directory exists.")
        return 1

    # Set up paths
    macro_dir = os.path.join(reference_dir, "SAS Macros")
    tlf_template_dir = os.path.join(reference_dir, "TLF")
    adam_specs_dir = os.path.join(reference_dir, "ADaM Specs")

    # Determine ADaM data directory and SAP file from input directory
    adam_data_dir = args.adam_dir
    if not adam_data_dir and os.path.exists(os.path.join(input_dir, "ADaM")):
        adam_data_dir = os.path.join(input_dir, "ADaM")
        # Check for subdirectory
        if os.path.exists(os.path.join(adam_data_dir, "Data")):
            adam_data_dir = os.path.join(adam_data_dir, "Data")

    sap_file = args.sap_file
    if not sap_file and os.path.exists(os.path.join(input_dir, "SAP")):
        sap_files = []
        for f in os.listdir(os.path.join(input_dir, "SAP")):
            if f.endswith(('.pdf', '.docx')):
                sap_files.append(os.path.join(input_dir, "SAP", f))
        if sap_files:
            sap_file = sap_files[0]  # Use first found SAP file

    # Direct PDF generation (Python-based) - Real statistical analysis
    if args.direct:
        from src.report.direct_generator import (
            generate_disposition_report,
            generate_protocol_deviation_report
        )

        os.makedirs(output_dir, exist_ok=True)

        print(f"\nGenerating Table {args.table_id} with real statistical analysis...")
        print(f"  Output directory: {output_dir}")

        if args.analysis_type == "disposition":
            # Find ADaM dataset
            adam_dataset = f"{args.dataset}.sas7bdat"
            if adam_data_dir and os.path.exists(os.path.join(adam_data_dir, adam_dataset)):
                adsl_path = os.path.join(adam_data_dir, adam_dataset)
            elif os.path.exists(os.path.join(input_dir, "ADaM", "Data", adam_dataset)):
                adsl_path = os.path.join(input_dir, "ADaM", "Data", adam_dataset)
            else:
                print(f"\nError: ADaM dataset not found: {adam_dataset}")
                print(f"Searched in: {adam_data_dir}")
                return 1

            print(f"  Input: {adsl_path}")

            result = generate_disposition_report(
                adsl_path=adsl_path,
                output_dir=output_dir,
                table_id=args.table_id
            )
            print(f"\nGenerated files:")
            print(f"  CSV output: {result['sas_output']}")
            print(f"  PDF: {result['pdf']}")

        elif args.analysis_type == "protocol_deviation":
            # Find ADDV and ADSL datasets
            addv_path = os.path.join(input_dir, "ADaM", "Data", "addv.sas7bdat")
            adsl_path = os.path.join(input_dir, "ADaM", "Data", "adsl.sas7bdat")

            if not os.path.exists(addv_path):
                print(f"\nError: ADDV dataset not found: {addv_path}")
                return 1
            if not os.path.exists(adsl_path):
                print(f"\nError: ADSL dataset not found: {adsl_path}")
                return 1

            print(f"  ADDV Input: {addv_path}")
            print(f"  ADSL Input: {adsl_path}")

            result = generate_protocol_deviation_report(
                addv_path=addv_path,
                adsl_path=adsl_path,
                output_dir=output_dir,
                table_id=args.table_id
            )
            print(f"\nGenerated files:")
            print(f"  CSV output: {result['csv_output']}")
            print(f"  PDF: {result['pdf']}")

        elif args.analysis_type == "exclusion":
            # Find ADSL dataset
            adsl_path = os.path.join(input_dir, "ADaM", "Data", "adsl.sas7bdat")

            if not os.path.exists(adsl_path):
                print(f"\nError: ADSL dataset not found: {adsl_path}")
                return 1

            print(f"  ADSL Input: {adsl_path}")

            from src.report.direct_generator import generate_exclusion_report
            result = generate_exclusion_report(
                adsl_path=adsl_path,
                output_dir=output_dir,
                table_id=args.table_id
            )
            print(f"\nGenerated files:")
            print(f"  CSV output: {result['csv_output']}")
            print(f"  PDF: {result['pdf']}")

        elif args.analysis_type == "demographics":
            # Find ADSL dataset
            adsl_path = os.path.join(input_dir, "ADaM", "Data", "adsl.sas7bdat")

            if not os.path.exists(adsl_path):
                print(f"\nError: ADSL dataset not found: {adsl_path}")
                return 1

            print(f"  ADSL Input: {adsl_path}")

            from src.report.direct_generator import generate_demographic_report
            result = generate_demographic_report(
                adsl_path=adsl_path,
                output_dir=output_dir,
                table_id=args.table_id
            )
            print(f"\nGenerated files:")
            print(f"  CSV output: {result['csv_output']}")
            print(f"  PDF: {result['pdf']}")

        else:
            print(f"\nError: Unknown analysis type: {args.analysis_type}")
            print(f"Available: disposition, protocol_deviation, exclusion, demographics")
            return 1

        return 0

    # Generate full TOC from ICH E3 knowledge base
    if args.full_toc:
        from src.report.toc_generator import generate_full_toc_from_ich_e3

        os.makedirs(output_dir, exist_ok=True)

        toc_output = args.toc_output or os.path.join(output_dir, "tlf_toc_full.csv")

        print(f"\nGenerating full TOC from ICH E3 knowledge base...")
        print(f"  Output: {toc_output}")

        result = generate_full_toc_from_ich_e3(
            output_path=toc_output,
            output_format='csv'
        )

        print(f"\nTOC generated: {result}")

        import pandas as pd
        df = pd.read_csv(result)
        print(f"\nSummary:")
        print(f"  Total entries: {len(df)}")
        print(df['tlf_type'].value_counts().to_string())

        return 0

    # Generate TOC from SAP
    if args.generate_toc:
        from src.report.toc_generator import generate_toc_from_sap

        os.makedirs(output_dir, exist_ok=True)

        # Determine SAP file
        sap_file = args.sap_file
        if not sap_file and os.path.exists(os.path.join(input_dir, "SAP")):
            # Prefer SAP.docx if it exists, otherwise use first .docx found
            sap_dir = os.path.join(input_dir, "SAP")
            sap_docx = os.path.join(sap_dir, "SAP.docx")
            if os.path.exists(sap_docx):
                sap_file = sap_docx
            else:
                for f in os.listdir(sap_dir):
                    if f.endswith('.docx'):
                        sap_file = os.path.join(sap_dir, f)
                        break

        if not sap_file or not os.path.exists(sap_file):
            print(f"\nError: SAP file not found")
            print(f"Searched: {sap_file or os.path.join(input_dir, 'SAP')}")
            return 1

        # Determine output path
        toc_output = args.toc_output
        if not toc_output:
            toc_output = os.path.join(output_dir, "tlf_toc.csv")

        print(f"\nGenerating TOC from SAP...")
        print(f"  SAP: {sap_file}")
        print(f"  Output: {toc_output}")

        result = generate_toc_from_sap(
            sap_path=sap_file,
            output_path=toc_output,
            limit=args.toc_limit,
            tlf_type=args.toc_type,
            output_format='csv'
        )

        print(f"\nTOC generated: {result}")

        # Show summary
        import pandas as pd
        df = pd.read_csv(result)
        print(f"\nSummary:")
        print(f"  Total entries: {len(df)}")
        print(df['tlf_type'].value_counts().to_string())

        return 0

    # Initialize RAG retriever for SAS program generation
    print(f"\nInitializing TLF Generation System...")
    print(f"  Reference: {reference_dir}")
    print(f"  Input: {input_dir}")

    try:
        rag = RAGRetriever(
            macro_dir=macro_dir,
            adam_specs_dir=adam_specs_dir,
            macro_cache=os.path.join(knowledge_dir, "macros.json"),
            adam_cache=os.path.join(knowledge_dir, "adam_specs.json")
        )

        # Build indexes if requested or if not cached
        cache_exists = os.path.exists(os.path.join(knowledge_dir, "macros.json"))
        if args.build_index or not cache_exists:
            print("\nBuilding RAG indexes from reference...")
            rag.build_indexes()
            os.makedirs(knowledge_dir, exist_ok=True)
            rag.save_caches(
                os.path.join(knowledge_dir, "macros.json"),
                os.path.join(knowledge_dir, "adam_specs.json")
            )
            print("Indexes built and cached.")

        # Initialize orchestrator
        orchestrator = OrchestratorAgent(rag)

        # Generate TLF
        print(f"\nGenerating Table {args.table_id}...")
        print(f"  Analysis type: {args.analysis_type}")
        print(f"  Dataset: {args.dataset}")
        if sap_file:
            print(f"  SAP: {sap_file}")
        if adam_data_dir:
            print(f"  ADaM data: {adam_data_dir}")

        result = orchestrator.generate_tlf(
            table_id=args.table_id,
            analysis_type=args.analysis_type,
            dataset_name=args.dataset
        )

        generated_code = result.get("generated_code", "")

        if generated_code:
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"Table {args.table_id}.sas")

            with open(output_path, 'w') as f:
                f.write(generated_code)

            print(f"\nGenerated SAS program saved to: {output_path}")
            print(f"Code length: {len(generated_code)} characters")

            # Print validation results
            validation = result.get("validation_result", {})
            if validation:
                print(f"\nValidation: {'PASSED' if validation.get('valid') else 'FAILED'}")
                if not validation.get("valid"):
                    print(f"  Error: {validation.get('error', 'Unknown error')}")

        else:
            print("\nError: No code was generated")
            print(f"Error: {result.get('error', 'Unknown error')}")
            return 1

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
