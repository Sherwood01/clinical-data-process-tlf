"""Anthropic API compatible tool definitions for the AI Agent."""

AGENT_TOOLS = [
    {
        "name": "switch_study",
        "description": (
            "Switch the active clinical study project. Use this when the user asks to open, "
            "switch to, or work on a different study database."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "study_id": {
                    "type": "string",
                    "description": "The UUID string of the study to switch to."
                }
            },
            "required": ["study_id"]
        }
    },
    {
        "name": "list_study_datasets",
        "description": (
            "List all uploaded ADaM datasets (e.g. adsl.sas7bdat, adae.sas7bdat) in the currently active study. "
            "Use this to check data availability before running reports."
        ),
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "generate_tlf_report",
        "description": (
            "Trigger the generation of a standard clinical TLF report (Table, Figure, or Listing) using the existing backend pipeline. "
            "Pass the report identifier/number (e.g., 'Table 14.1.1.1', '14.1.1.1', 'Listing 16.2.1') OR the specific TOC entry UUID if available."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "The report number/ID (e.g., 'Table 14.1.1.1', '14.1.1.1', 'Listing 16.2.1') OR report title OR the TOC entry UUID."
                },
                "toc_entry_id": {
                    "type": "string",
                    "description": "Alias for identifier. The report number or TOC entry UUID."
                },
                "tlf_id": {
                    "type": "string",
                    "description": "Report number identifier (e.g., '14.1.1.1')."
                }
            },
            "required": []
        }
    },
    {
        "name": "query_user_manual",
        "description": (
            "Search the User Manual knowledge base & Help/FAQ for platform usage instructions, how-to guides, "
            "and operational steps (e.g. 'how to generate TLF report', 'how to upload ADaM datasets', 'supported file formats', 'why big N is 0'). "
            "Always call this tool when the user asks how to perform an action, how to use platform features, or operational questions."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query or question about the platform."
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "create_custom_figure",
        "description": (
            "Create a custom clinical chart/figure (e.g. survival curve, waterfall, swimmer, or custom AE scatter plot) "
            "by dynamically executing AI-generated Python code in a safe container sandbox. "
            "The code should read local SAS datasets (e.g. './adsl.sas7bdat') and output 'output.pdf'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "figure_title": {
                    "type": "string",
                    "description": "Title of the custom chart."
                },
                "python_code": {
                    "type": "string",
                    "description": "Complete Python script to generate the plot. Must write to 'output.pdf' in the local workspace. Data is read from local directory, e.g. pd.read_sas('adsl.sas7bdat')."
                }
            },
            "required": ["figure_title", "python_code"]
        }
    },
    {
        "name": "list_study_tocs",
        "description": (
            "List all TOC (Table of Contents) entries configured for the currently active study. "
            "Each entry contains its 'id' (a UUID string required to generate the report), "
            "'tlf_id' (e.g. '14.1.1.1'), 'tlf_name' (e.g. 'Subject Disposition'), and 'tlf_type' ('table', 'figure', or 'listing'). "
            "Use this tool to find the 'id' (UUID) corresponding to a specific report number/name "
            "before calling generate_tlf_report."
        ),
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "delete_study_dataset",
        "description": (
            "Delete an uploaded ADaM dataset from the currently active study by its dataset UUID. "
            "Always query list_study_datasets first to locate the dataset's 'id' (UUID) before deleting."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "dataset_id": {
                    "type": "string",
                    "description": "The UUID of the dataset to be deleted."
                }
            },
            "required": ["dataset_id"]
        }
    },
    {
        "name": "query_billing_status",
        "description": (
            "Query the current user and tenant subscription plan level, monthly run limits, "
            "and this month's generated report usage count."
        ),
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "create_study",
        "description": (
            "Create a brand new clinical study project in the tenant workspace. "
            "Requires 'name' (string) and optional 'protocol_id' or 'description'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the new clinical study."
                },
                "protocol_id": {
                    "type": "string",
                    "description": "Optional protocol ID identifier for the study."
                },
                "description": {
                    "type": "string",
                    "description": "Optional textual description of the study purpose."
                }
            },
            "required": ["name"]
        }
    },
    {
        "name": "delete_study",
        "description": (
            "Delete an active study project by its study UUID. This will permanently remove all datasets and report history."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "target_study_id": {
                    "type": "string",
                    "description": "The UUID of the study project to be deleted."
                }
            },
            "required": ["target_study_id"]
        }
    },
    {
        "name": "delete_toc_entry",
        "description": (
            "Delete a configured Table, Figure, or Listing report row from the study's Table of Contents by its entry UUID. "
            "Always query list_study_tocs first to locate the entry's UUID."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "toc_entry_id": {
                    "type": "string",
                    "description": "The UUID of the TOC entry row to delete."
                }
            },
            "required": ["toc_entry_id"]
        }
    },
    {
        "name": "search_web",
        "description": (
            "Search clinical trial guidelines, regulatory compliance standards (CDISC SDTM/ADaM, FDA/EMA, ICH E9), "
            "or general industry questions online."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to look up."
                }
            },
            "required": ["query"]
        }
    }
]

# Read-only tools suitable for Chat / Q&A mode
READONLY_TOOL_NAMES = {
    "query_user_manual",
    "query_billing_status",
    "list_study_datasets",
    "query_adam_dataset",
    "list_study_tocs",
    "search_web"
}

READONLY_AGENT_TOOLS = [tool for tool in AGENT_TOOLS if tool["name"] in READONLY_TOOL_NAMES]

