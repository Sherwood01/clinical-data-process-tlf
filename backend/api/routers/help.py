"""User Support and FAQ metadata router."""
from fastapi import APIRouter

router = APIRouter(prefix="/help", tags=["Help"])


@router.get("")
async def get_support_metadata():
    """Retrieve support email and SLA metadata for the help documentation."""
    return {
        "support_email": "info@xwqin.com",
        "working_hours": "Monday - Friday, 9:00 AM - 6:00 PM UTC+8",
        "sla_hours": 24,
        "platform_status": "operational",
        "compliance": {
            "sandbox_isolated": True,
            "cfr_compliant": True,
            "data_isolated": True
        }
    }
