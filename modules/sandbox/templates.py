"""
Report Template Contracts - 보고서 템플릿 규격 정의

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"Template-First" 원칙:
1. 우리가 보고 싶은 HTML 대시보드의 '틀(Slot)'을 먼저 정의한다.
2. Sandbox는 이 틀을 채우기 위해 필요한 데이터 소스를 역으로 추적하여 분석한다.
3. 최종적으로 틀에 데이터를 주입(Injection)하여 HTML을 완성한다.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from typing import Optional, Any
from pydantic import BaseModel, Field

# ────────────────────────────────────────
# 1. 대시보드 구성 요소(Component) 규격
# ────────────────────────────────────────

class SummaryCard(BaseModel):
    """상단 요약 카드 1개 세트"""
    label: str               # "총 매출", "달성률" 등
    value: Optional[str] = None  # 엔진이 채울 값
    sub_text: Optional[str] = None
    status: str = "normal"
    
    # 자동 주입을 위한 엔진 타겟팅 태그
    # 예: "total_sales_amount", "avg_attainment_rate" 등
    metric_key: Optional[str] = Field(None, description="분석 엔진에서 가져올 지표 키")

class ChartSlot(BaseModel):
    """차트 영역 1개 세트"""
    title: str
    chart_type: str
    labels: list[str] = Field(default_factory=list)
    datasets: list[dict[str, Any]] = Field(default_factory=list)
    metric_key: Optional[str] = Field(None, description="차트용 데이터 소스 키")

class TableSlot(BaseModel):
    """데이터 테이블 영역"""
    title: str
    columns: list[str]
    rows: list[list[Any]]


# ────────────────────────────────────────
# 2. 마스터 대시보드 템플릿 계약 (Contract)
# ────────────────────────────────────────

class PerformanceDashboardContract(BaseModel):
    """
    SFE 성과 대시보드 (월간/분기/연간 공용) 템플릿 규격.
    이 규격이 정의되면 Sandbox는 이를 채우는 것을 목표로 동작한다.
    """
    report_title: str
    period_label: str        # "2025년 1분기", "2025년 03월" 등
    
    # 템플릿 슬롯들
    summary_cards: list[SummaryCard] = Field(default_factory=list, max_length=4)
    main_trend_chart: Optional[ChartSlot] = None
    regional_performance_map: Optional[ChartSlot] = None
    top_efficiency_hospitals: Optional[TableSlot] = None
    
    # 전략적 인사이트 (엔진이 생성)
    executive_summary: list[str] = Field(default_factory=list)

    @classmethod
    def get_standard_template(cls) -> "PerformanceDashboardContract":
        """표준 성과 보고서 틀 (태그 포함)"""
        return cls(
            report_title="SFE 성과 보고서",
            period_label="자동 생성",
            summary_cards=[
                SummaryCard(label="총 실적", metric_key="total_sales_amount"),
                SummaryCard(label="목표 달성률", metric_key="avg_attainment_rate"),
                SummaryCard(label="영업 활동력", metric_key="total_visits"),
                SummaryCard(label="Rx 연결성", metric_key="rx_linked_hospitals"),
            ]
        )
