from __future__ import annotations

from importlib import import_module

from .configs import RawGenerationConfig


_TEMPLATE_MODULES = {
    "daon_like": "scripts.raw_generators.templates.daon_like",
    "hangyeol_like": "scripts.raw_generators.templates.hangyeol_like",
}


def run_raw_generation(config: RawGenerationConfig) -> None:
    template_module_path = _TEMPLATE_MODULES.get(config.template_type)
    if not template_module_path:
        raise ValueError(
            f"{config.company_name}({config.company_key})의 raw generation template `{config.template_type}` 는 아직 지원되지 않습니다."
        )

    template_module = import_module(template_module_path)
    run_template_name = "run_monthly_and_merged_template" if config.output_mode == "monthly_and_merged" else "run_template"
    run_template = getattr(template_module, run_template_name)
    run_template(config)


__all__ = ["run_raw_generation"]
