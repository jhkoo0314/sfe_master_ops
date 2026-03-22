from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from common.company_runtime import get_active_company_key, get_active_company_name
from scripts.raw_generators import get_raw_generation_config, run_raw_generation


def main() -> None:
    company_key = get_active_company_key()
    company_name = get_active_company_name(company_key)
    generation_config = get_raw_generation_config(company_key)

    if generation_config is None:
        raise ValueError(
            f"{company_name}({company_key})는 등록된 raw generation config가 없습니다. "
            "테스트용 raw를 새로 만들려면 scripts/raw_generators/configs.py에 설정을 추가해야 합니다."
        )

    run_raw_generation(generation_config)


if __name__ == "__main__":
    main()
