from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.validation.main import app as validation_app
from modules.validation.workflow.execution_registry import get_execution_mode_modules
from ops_core.main import app as ops_core_app


def test_validation_bridge_main_uses_same_fastapi_app():
    # Keep one explicit legacy import test so compatibility stays visible.
    assert validation_app is ops_core_app


def test_validation_bridge_registry_exposes_execution_modes():
    assert get_execution_mode_modules("crm_to_sandbox") == ["crm", "sandbox", "radar"]
