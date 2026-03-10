const state = {
  selectedModule: "sandbox",
  loadedAsset: null,
  opsReportContent: null,
  opsRenderedHtml: null,
};

function switchLayer(layer, el) {
  document.querySelectorAll(".layer").forEach((node) => {
    node.style.display = node.id === `layer-${layer}` ? "flex" : "none";
  });
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.classList.remove("active");
  });
  if (el) el.classList.add("active");
}

function selectModule(mod, el) {
  state.selectedModule = mod;
  document.querySelectorAll(".module-card").forEach((card) => {
    card.classList.remove("active");
  });
  el.classList.add("active");
  renderOpsReport(mod);
}

function getSampleData(mod) {
  const base = {
    sandbox: {
      title: "SFE 성과 분석 보고서",
      period: "202501~202502",
      kpis: [
        { label: "총 매출", value: "2,215만원" },
        { label: "평균 달성률", value: "85.3%" },
        { label: "분석 병원", value: "6개" },
        { label: "CRM×Sales 조인율", value: "83%" },
      ],
      rows: [
        ["H001", "7,300,000", "89.0%", "15"],
        ["H003", "8,700,000", "85.3%", "13"],
        ["H002", "2,900,000", "82.9%", "7"],
        ["H004", "1,800,000", "90.0%", "5"],
        ["H005", "950,000", "79.2%", "7"],
      ],
      headers: ["병원ID", "매출", "달성률", "방문수"],
      insights: [
        "전체 달성률 85.3% — 목표 대비 안정권이나 H005 집중 관리 필요",
        "H003(부산)이 최대 매출 병원으로 핵심 거점 역할 수행",
        "6개 병원 중 5개 완전 조인 — 분석 신뢰도 높음",
      ],
    },
    territory: {
      title: "SFE 권역별 영업 성과 지도",
      period: "2025년 1~2월",
      kpis: [
        { label: "전체 권역", value: "3개" },
        { label: "커버리지율", value: "100%" },
        { label: "미커버 병원", value: "1개" },
        { label: "담당자", value: "3명" },
      ],
      headers: ["권역", "병원수", "총 매출", "평균 달성률", "방문수"],
      rows: [
        ["부산", "2", "10,500,000", "87.7%", "18"],
        ["서울", "2", "10,200,000", "85.9%", "22"],
        ["인천", "2", "1,450,000", "39.6%", "7"],
      ],
      markers: [
        { hospital: "H001", rep: "REP001", date: "2025-02-03", month: "2025-02", seq: 1, sales: 7300000, target: 8200000, insight: "서울 핵심 거래처", lat: 37.5665, lng: 126.978, color: "yellow", tooltip: "H001" },
        { hospital: "H003", rep: "REP002", date: "2025-02-05", month: "2025-02", seq: 1, sales: 8700000, target: 10200000, insight: "부산 최고 성과 병원", lat: 35.1796, lng: 129.0756, color: "yellow", tooltip: "H003" },
        { hospital: "H005", rep: "REP003", date: "2025-02-07", month: "2025-02", seq: 1, sales: 950000, target: 1200000, insight: "인천 집중 개선 필요", lat: 37.4563, lng: 126.7052, color: "red", tooltip: "H005" },
      ],
      routes: [
        { rep: "REP001", month: "2025-02", date: "2025-02-03", coords: [{ hospital: "H001", lat: 37.5665, lon: 126.978, seq: 1 }] },
        { rep: "REP002", month: "2025-02", date: "2025-02-05", coords: [{ hospital: "H003", lat: 35.1796, lon: 129.0756, seq: 1 }] },
      ],
      insights: [
        "인천 커버리지 저조 — 방문 전략 재검토 필요",
        "부산 권역은 최고 성과 유지 중",
      ],
    },
    crm: {
      title: "CRM 활동 분석 보고서",
      period: "202501~202502",
      kpis: [
        { label: "총 활동", value: "57건" },
        { label: "평균 방문/병원", value: "9.5건" },
        { label: "디테일링율", value: "54%" },
        { label: "활성 담당자", value: "3명" },
      ],
      headers: ["담당자", "병원수", "총 방문", "디테일링", "주요 채널"],
      rows: [
        ["REP001", "2", "22", "12", "방문+이메일"],
        ["REP002", "2", "18", "8", "방문+전화"],
        ["REP003", "2", "7", "3", "전화+방문"],
      ],
      insights: [
        "REP001 서울권 활동 집중도 최우수",
        "REP003 방문 건수 저조 — 지원 필요",
      ],
    },
    prescription: {
      title: "Prescription 흐름 분석",
      period: "202501~202502",
      kpis: [
        { label: "완전 연결 흐름", value: "4건" },
        { label: "고유 도매상", value: "2개" },
        { label: "고유 약국", value: "3개" },
        { label: "UNMAPPED", value: "0건" },
      ],
      headers: ["도매상", "약국", "병원", "제품", "수량", "금액"],
      rows: [
        ["WS_서울_한국약품", "PH_110110_서울약국_100", "H001", "PROD_A001", "100", "500,000"],
        ["WS_부산_부산약품", "PH_260402_해운대약국_200", "H003", "PROD_A001", "150", "750,000"],
      ],
      insights: ["도매→약국→병원 완전 연결 흐름 정상 작동"],
    },
  };
  return base[mod];
}

function getTemplateStore() {
  return window.SFE_TEMPLATE_STORE || {};
}

function escapeHtml(text) {
  return String(text || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function parseNumber(value) {
  return Number(String(value || "0").replace(/[^0-9.-]/g, "")) || 0;
}

function buildMonthSeries(values) {
  const base = values.slice(0, 12);
  while (base.length < 12) base.push(base[base.length - 1] || 0);
  return base;
}

function replaceReportPayload(template, payload) {
  return template.replace(
    /const db = \/\*DATA_JSON_PLACEHOLDER\*\/[\s\S]*?\n\s*let charts = \{\};/,
    `const db = ${JSON.stringify(payload, null, 2)};\n        let charts = {};`,
  );
}

function replaceSpatialPayload(template, markers, routes, mode = "hospital") {
  return template
    .replace(/window\.__INITIAL_MODE__ = "[^"]*";/, `window.__INITIAL_MODE__ = "${mode}";`)
    .replace(/window\.__INITIAL_MARKERS__ = [\s\S]*?;/, `window.__INITIAL_MARKERS__ = ${JSON.stringify(markers, null, 2)};`)
    .replace(/window\.__INITIAL_ROUTES__ = [\s\S]*?;/, `window.__INITIAL_ROUTES__ = ${JSON.stringify(routes, null, 2)};`);
}

function buildSandboxTemplatePayload(data) {
  const members = data.rows.map((row, idx) => {
    const hospitalId = row[0];
    const actual = parseNumber(row[1]);
    const achieve = parseFloat(row[2]) || 0;
    const calls = parseNumber(row[3]);
    const target = Math.round(actual / Math.max(achieve / 100, 0.01));
    const monthlyActual = buildMonthSeries([actual * 0.68, actual * 0.72, actual * 0.76, actual * 0.81, actual * 0.86, actual * 0.88, actual * 0.91, actual * 0.95, actual * 0.98, actual * 1.0, actual * 1.02, actual * 1.05]).map((v) => Math.round(v));
    const monthlyTarget = buildMonthSeries([target * 0.7, target * 0.74, target * 0.79, target * 0.83, target * 0.88, target * 0.9, target * 0.94, target * 0.97, target * 1.0, target * 1.02, target * 1.04, target * 1.06]).map((v) => Math.round(v));
    return {
      성명: `REP00${idx + 1}`,
      HIR: 68 + idx * 4,
      RTR: 66 + idx * 3,
      BCR: 70 + idx * 2,
      PHR: 67 + idx * 3,
      PI: achieve,
      FGR: 4.2 + idx * 1.4,
      처방금액: actual * 12,
      목표금액: target * 12,
      지점순위: idx + 1,
      efficiency: Math.round(actual / Math.max(calls, 1)),
      sustainability: 74 + idx * 3,
      gini: 0.28 + idx * 0.04,
      coach_scenario: idx === 0 ? "Lead Driver" : "Growth Builder",
      coach_action: `${hospitalId} 관리 전략을 강화하고 핵심 행동 지표를 유지하세요.`,
      shap: { PT: 0.18, 시연: 0.11, 클로징: 0.15, 니즈환기: 0.1, 대면: 0.14, 컨택: 0.12, 접근: 0.1, 피드백: 0.1 },
      prod_matrix: [
        { name: "PROD_A001", ms: 42 - idx * 2, growth: 8.1 - idx * 0.6 },
        { name: "PROD_B002", ms: 31 + idx, growth: 5.2 + idx * 0.4 },
        { name: "PROD_C003", ms: 27 + idx, growth: 3.6 + idx * 0.3 },
      ],
      monthly_actual: monthlyActual,
      monthly_target: monthlyTarget,
    };
  });

  const totalActual = Array.from({ length: 12 }, (_, i) =>
    members.reduce((sum, member) => sum + Number(member.monthly_actual[i] || 0), 0),
  );
  const totalTarget = Array.from({ length: 12 }, (_, i) =>
    members.reduce((sum, member) => sum + Number(member.monthly_target[i] || 0), 0),
  );
  const achieve = totalTarget.reduce((a, b) => a + b, 0) > 0
    ? (totalActual.reduce((a, b) => a + b, 0) / totalTarget.reduce((a, b) => a + b, 0)) * 100
    : 0;

  return {
    as_of_date: "2025.02",
    products: ["PROD_A001", "PROD_B002", "PROD_C003"],
    total: {
      actual_sum: totalActual.reduce((a, b) => a + b, 0),
      target_sum: totalTarget.reduce((a, b) => a + b, 0),
      PI: Number(achieve.toFixed(1)),
      FGR: 6.8,
      monthly_actual: totalActual,
      monthly_target: totalTarget,
    },
    total_prod_analysis: {
      PROD_A001: { monthly_actual: totalActual.map((v) => Math.round(v * 0.42)), monthly_target: totalTarget.map((v) => Math.round(v * 0.4)) },
      PROD_B002: { monthly_actual: totalActual.map((v) => Math.round(v * 0.33)), monthly_target: totalTarget.map((v) => Math.round(v * 0.35)) },
      PROD_C003: { monthly_actual: totalActual.map((v) => Math.round(v * 0.25)), monthly_target: totalTarget.map((v) => Math.round(v * 0.25)) },
    },
    branches: {
      서울지점: {
        monthly_actual: totalActual,
        monthly_target: totalTarget,
        avg: { PI: Number(achieve.toFixed(1)), FGR: 6.8 },
        analysis: { importance: {}, correlation: {}, adj_correlation: {}, ccf: [0, 0, 0, 0, 0] },
        members,
        prod_analysis: {
          PROD_A001: { monthly_actual: totalActual.map((v) => Math.round(v * 0.42)), monthly_target: totalTarget.map((v) => Math.round(v * 0.4)), avg: { PI: 86.1, FGR: 5.4 } },
          PROD_B002: { monthly_actual: totalActual.map((v) => Math.round(v * 0.33)), monthly_target: totalTarget.map((v) => Math.round(v * 0.35)), avg: { PI: 81.4, FGR: 4.9 } },
          PROD_C003: { monthly_actual: totalActual.map((v) => Math.round(v * 0.25)), monthly_target: totalTarget.map((v) => Math.round(v * 0.25)), avg: { PI: 88.7, FGR: 7.1 } },
        },
      },
    },
    missing_data: [],
    data_health: { operational_notes: [] },
  };
}

function buildTerritoryTemplatePayload(data) {
  const markers = (data.markers || []).map((marker) => ({
    hospital: marker.hospital,
    rep: marker.rep,
    date: marker.date,
    month: marker.month,
    lat: marker.lat,
    lon: marker.lng,
    target: marker.target,
    sales: marker.sales,
    insight: marker.insight,
    seq: marker.seq,
  }));
  const routes = (data.routes || []).map((route) => ({
    rep: route.rep,
    month: route.month,
    date: route.date,
    coords: route.coords || [],
  }));
  return { markers, routes };
}

function renderSandboxTemplateHtml(data) {
  const template = getTemplateStore().report;
  if (!template) return buildGenericExportHtml(data, "sandbox");
  return replaceReportPayload(template, buildSandboxTemplatePayload(data));
}

function renderTerritoryTemplateHtml(data) {
  const template = getTemplateStore().spatial;
  if (!template) return buildGenericExportHtml(data, "territory");
  const payload = buildTerritoryTemplatePayload(data);
  return replaceSpatialPayload(template, payload.markers, payload.routes, "hospital");
}

function buildTemplatePreviewShell(title, subtitle, badge) {
  return `
    <div class="actions">
      <button class="btn btn-primary" onclick="downloadOpsReport()">⬇️ 템플릿 HTML 다운로드</button>
    </div>
    <div class="report-section">
      <h3>Template Builder</h3>
      <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:12px">
        <div>
          <div style="font-size:18px;font-weight:700">${escapeHtml(title)}</div>
          <div style="font-size:12px;color:var(--muted);margin-top:4px">${escapeHtml(subtitle)}</div>
        </div>
        <div style="font-size:11px;color:var(--primary);border:1px solid rgba(88,166,255,.25);background:rgba(88,166,255,.08);padding:6px 10px;border-radius:999px">${escapeHtml(badge)}</div>
      </div>
      <div style="width:100%;min-height:780px;border:1px solid var(--border);border-radius:12px;overflow:hidden;background:#fff">
        <iframe srcdoc="" style="width:100%;height:780px;border:none;background:#fff" id="ops-template-frame"></iframe>
      </div>
      <p style="font-size:12px;color:var(--muted);margin-top:10px">templates 폴더의 실제 HTML 템플릿에 샘플 데이터를 주입해 미리보는 화면입니다.</p>
    </div>
  `;
}

function buildGenericExportHtml(data, mod) {
  const kpiHtml = `<div class="kpi-row">${data.kpis.map((k) => `<div class="kpi-card"><div class="kv">${k.value}</div><div class="kl">${k.label}</div></div>`).join("")}</div>`;
  const tableHtml = `<table class="data-table"><thead><tr>${data.headers.map((h) => `<th>${h}</th>`).join("")}</tr></thead><tbody>${data.rows.map((r) => `<tr>${r.map((c) => `<td>${c}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
  const insightHtml = `<div class="insight-list">${data.insights.map((i) => `<div class="insight-item">${i}</div>`).join("")}</div>`;
  return `<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><title>${escapeHtml(data.title)}</title><style>body{font-family:system-ui;background:#0d1117;color:#e6edf3;padding:32px}.kpi-row{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:24px}.kpi-card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:16px}.kv{font-size:22px;font-weight:700;color:#58a6ff}.kl{font-size:11px;color:#8b949e;margin-top:4px}table{width:100%;border-collapse:collapse;font-size:13px;margin-bottom:24px}th{background:#21262d;color:#8b949e;padding:8px 12px;text-align:left}td{padding:8px 12px;border-bottom:1px solid #30363d}h2{margin-bottom:8px}h3{font-size:12px;color:#8b949e;text-transform:uppercase;letter-spacing:.5px;margin:20px 0 10px}.insight-item{background:#21262d;border-left:3px solid #58a6ff;padding:10px 14px;border-radius:0 6px 6px 0;margin-bottom:8px;font-size:13px}</style></head><body><h2>${escapeHtml(data.title)}</h2><p>${escapeHtml(data.period)} · ${escapeHtml(mod)}</p>${kpiHtml}<div class="report-section"><h3>상세 데이터</h3>${tableHtml}</div><div class="report-section"><h3>전략 인사이트</h3>${insightHtml}</div></body></html>`;
}

function buildOpsHtml(data, mod) {
  const kpiHtml = `<div class="kpi-row">${data.kpis.map((k) => `<div class="kpi-card"><div class="kv">${k.value}</div><div class="kl">${k.label}</div></div>`).join("")}</div>`;
  const tableHtml = `<table class="data-table"><thead><tr>${data.headers.map((h) => `<th>${h}</th>`).join("")}</tr></thead><tbody>${data.rows.map((r) => `<tr>${r.map((c) => `<td>${c}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
  const insightHtml = `<div class="insight-list">${data.insights.map((i) => `<div class="insight-item">${i}</div>`).join("")}</div>`;
  const mapSection = mod === "territory"
    ? `<div class="report-section"><h3>영업 권역 지도</h3><div id="ops-map"></div></div>`
    : "";
  return `
    <div class="actions">
      <button class="btn btn-primary" onclick="downloadOpsReport()">⬇️ HTML 다운로드</button>
    </div>
    <div class="report-section"><h3>핵심 KPI</h3>${kpiHtml}</div>
    ${mapSection}
    <div class="report-section"><h3>상세 데이터</h3>${tableHtml}</div>
    <div class="report-section"><h3>전략 인사이트</h3>${insightHtml}</div>
  `;
}

function initMap(markers, routes) {
  setTimeout(() => {
    const mapEl = document.getElementById("ops-map");
    if (!mapEl || mapEl._leaflet_id) return;
    const map = L.map("ops-map").setView([36.5, 127.8], 7);
    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
      attribution: "© OpenStreetMap © CARTO",
      maxZoom: 18,
    }).addTo(map);
    markers.forEach((m) => {
      L.marker([m.lat, m.lng]).addTo(map).bindPopup(`<pre style="font-size:11px;line-height:1.5">${m.tooltip || m.hospital}</pre>`);
    });
    routes.forEach((r) => {
      const coords = (r.points || r.coords || []).map((p) => [p[0] || p.lat, p[1] || p.lng || p.lon]);
      if (coords.length) {
        L.polyline(coords, { color: "#58a6ff", weight: 2, opacity: 0.7, dashArray: "6 4" }).addTo(map);
      }
    });
  }, 100);
}

function renderOpsReport(mod) {
  const main = document.getElementById("ops-main");
  const sampleData = getSampleData(mod);
  state.opsReportContent = sampleData;

  if (mod === "sandbox") {
    state.opsRenderedHtml = renderSandboxTemplateHtml(sampleData);
    main.innerHTML = buildTemplatePreviewShell(
      "Sandbox Template Preview",
      "templates/report_template.html 기반 결과 보고서 미리보기",
      "REPORT TEMPLATE",
    );
    document.getElementById("ops-template-frame").srcdoc = state.opsRenderedHtml;
    return;
  }

  if (mod === "territory") {
    state.opsRenderedHtml = renderTerritoryTemplateHtml(sampleData);
    main.innerHTML = buildTemplatePreviewShell(
      "Territory Template Preview",
      "templates/spatial_preview_template.html 기반 권역 지도 미리보기",
      "MAP TEMPLATE",
    );
    document.getElementById("ops-template-frame").srcdoc = state.opsRenderedHtml;
    return;
  }

  state.opsRenderedHtml = buildGenericExportHtml(sampleData, mod);
  main.innerHTML = buildOpsHtml(sampleData, mod);
  if (mod === "territory") initMap(sampleData.markers || [], sampleData.routes || []);
}

function loadOpsAsset(evt) {
  const file = evt.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = (e) => {
    try {
      state.loadedAsset = JSON.parse(e.target.result);
      console.info(`${file.name} 로드 완료`);
    } catch (err) {
      alert(`JSON 파싱 오류: ${err.message}`);
    }
  };
  reader.readAsText(file);
}

function downloadOpsReport() {
  const html = state.opsRenderedHtml || buildGenericExportHtml(
    state.opsReportContent || getSampleData(state.selectedModule),
    state.selectedModule,
  );
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([html], { type: "text/html" }));
  a.download = `ops_report_${state.selectedModule}_${Date.now()}.html`;
  a.click();
}

renderOpsReport("sandbox");
