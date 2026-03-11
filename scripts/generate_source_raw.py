from __future__ import annotations

import importlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from common.company_profile import get_company_ops_profile
from common.company_runtime import get_active_company_key, get_active_company_name


def main() -> None:
    company_key = get_active_company_key()
    company_name = get_active_company_name(company_key)
    profile = get_company_ops_profile(company_key)

    if not profile.raw_generator_module:
        raise ValueError(
            f"{company_name}({company_key})는 등록된 raw 생성 스크립트가 없습니다. "
            "기존 company_source 파일을 그대로 사용하거나 profile에 raw 생성 모듈을 등록해야 합니다."
        )

    generator_main = importlib.import_module(profile.raw_generator_module).main
    generator_main()


if __name__ == "__main__":
    main()
