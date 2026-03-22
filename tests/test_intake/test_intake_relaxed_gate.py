from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.intake.models import IntakeRequest, IntakeSourceInput
from modules.intake.service import CommonIntakeEngine


def test_required_candidate_warning_does_not_block_intake():
    request = IntakeRequest(
        project_root=str(ROOT),
        company_key="demo_company",
        company_name="Demo Company",
        sources=[
            IntakeSourceInput(
                source_key="crm_activity",
                original_path=str(ROOT / "dummy_crm_activity.xlsx"),
                target_path=str(ROOT / "dummy_crm_activity.xlsx"),
                columns=["방문일정", "영업사원이름", "영업사원코드", "방문기관명", "방문유형"],
                is_required=True,
                upload_present=True,
            )
        ],
        execution_mode=None,
    )

    result = CommonIntakeEngine().inspect(request)

    assert result.ready_for_adapter is True
    assert result.status == "ready"
    assert any(
        finding.issue_code == "candidate_review_recommended"
        for finding in result.findings
    )
