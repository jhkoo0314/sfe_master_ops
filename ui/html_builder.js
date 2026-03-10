// ── 전역 상태 ────────────────────────────
      const state = {
        currentLayer: "ops",
        selectedModule: "sandbox",
        selectedTheme: "B",
        currentPhase: "intake",
        loadedAsset: null,
        blueprints: [],
        generatedHtml: null,
        opsReportContent: null, // Layer1에서 가져올 내용
        opsRenderedHtml: null,
      };

      // ── 레이어 전환 ──────────────────────────
      function switchLayer(layer, el) {
        state.currentLayer = layer;
        document
          .querySelectorAll(".layer")
          .forEach((l) => l.classList.remove("active"));
        document
          .querySelectorAll(".tab-btn")
          .forEach((b) => b.classList.remove("active"));
        document.getElementById(`layer-${layer}`).classList.add("active");
        if (el) el.classList.add("active");

        if (layer === "ops" && state.selectedModule)
          renderOpsReport(state.selectedModule);
      }

      // ── Layer1: 모듈 선택 ────────────────────
      function selectModule(mod, el) {
        state.selectedModule = mod;
        document
          .querySelectorAll(".module-card")
          .forEach((c) => c.classList.remove("active"));
        el.classList.add("active");
        renderOpsReport(mod);
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
          document.getElementById("ops-template-frame").srcdoc =
            state.opsRenderedHtml;
          return;
        }

        if (mod === "territory") {
          state.opsRenderedHtml = renderTerritoryTemplateHtml(sampleData);
          main.innerHTML = buildTemplatePreviewShell(
            "Territory Template Preview",
            "templates/spatial_preview_template.html 기반 권역 지도 미리보기",
            "MAP TEMPLATE",
          );
          document.getElementById("ops-template-frame").srcdoc =
            state.opsRenderedHtml;
          return;
        }

        state.opsRenderedHtml = buildGenericExportHtml(sampleData, mod);
        main.innerHTML = buildOpsHtml(sampleData, mod);
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
              "⚠️ 전체 달성률 85.3% — 목표 대비 안정권이나 H005 집중 관리 필요",
              "🔗 H003(부산)이 최대 매출 병원으로 REP002의 핵심 거점",
              "✅ 6개 병원 중 5개 완전 조인 — 분석 신뢰도 높음",
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
              {
                hospital: "H001",
                rep: "REP001",
                date: "2025-02-03",
                month: "2025-02",
                seq: 1,
                sales: 7300000,
                target: 8200000,
                insight: "서울 핵심 거래처",
                lat: 37.5665,
                lng: 126.978,
                color: "yellow",
                size: "lg",
                tooltip: "H001\n매출: 7,300,000원\n달성률: 89%\n방문: 15건",
              },
              {
                hospital: "H002",
                rep: "REP001",
                date: "2025-02-03",
                month: "2025-02",
                seq: 2,
                sales: 2900000,
                target: 3500000,
                insight: "서울 보완 필요 거래처",
                lat: 37.57,
                lng: 127.0,
                color: "yellow",
                size: "md",
                tooltip: "H002\n매출: 2,900,000원\n달성률: 83%\n방문: 7건",
              },
              {
                hospital: "H003",
                rep: "REP002",
                date: "2025-02-05",
                month: "2025-02",
                seq: 1,
                sales: 8700000,
                target: 10200000,
                insight: "부산 최고 성과 병원",
                lat: 35.1796,
                lng: 129.0756,
                color: "yellow",
                size: "xl",
                tooltip: "H003\n매출: 8,700,000원\n달성률: 85%\n방문: 13건",
              },
              {
                hospital: "H004",
                rep: "REP002",
                date: "2025-02-05",
                month: "2025-02",
                seq: 2,
                sales: 1800000,
                target: 2000000,
                insight: "부산 안정 운영 병원",
                lat: 35.19,
                lng: 129.09,
                color: "green",
                size: "md",
                tooltip: "H004\n매출: 1,800,000원\n달성률: 90%\n방문: 5건",
              },
              {
                hospital: "H005",
                rep: "REP003",
                date: "2025-02-07",
                month: "2025-02",
                seq: 1,
                sales: 950000,
                target: 1200000,
                insight: "인천 집중 개선 필요",
                lat: 37.4563,
                lng: 126.7052,
                color: "red",
                size: "sm",
                tooltip: "H005\n매출: 950,000원\n달성률: 79%\n방문: 7건",
              },
              {
                hospital: "H006",
                rep: "REP003",
                date: "2025-02-07",
                month: "2025-02",
                seq: 2,
                sales: 0,
                target: 600000,
                insight: "미커버 병원",
                lat: 37.47,
                lng: 126.72,
                color: "gray",
                size: "sm",
                tooltip: "H006\n방문 없음 (미커버)",
              },
            ],
            routes: [
              {
                rep: "REP001",
                month: "2025-02",
                date: "2025-02-03",
                color: "#58a6ff",
                coords: [
                  { hospital: "H001", lat: 37.5665, lon: 126.978, seq: 1 },
                  { hospital: "H002", lat: 37.57, lon: 127.0, seq: 2 },
                ],
              },
              {
                rep: "REP002",
                month: "2025-02",
                date: "2025-02-05",
                color: "#3fb950",
                coords: [
                  { hospital: "H003", lat: 35.1796, lon: 129.0756, seq: 1 },
                  { hospital: "H004", lat: 35.19, lon: 129.09, seq: 2 },
                ],
              },
              {
                rep: "REP003",
                month: "2025-02",
                date: "2025-02-07",
                color: "#d29922",
                coords: [
                  { hospital: "H005", lat: 37.4563, lon: 126.7052, seq: 1 },
                  { hospital: "H006", lat: 37.47, lon: 126.72, seq: 2 },
                ],
              },
            ],
            insights: [
              "⚠️ 인천 커버리지 저조 — REP003 방문 전략 재검토",
              "✅ 부산 REP002 최고 성과 유지",
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
              "💡 REP001 서울권 활동 집중도 최우수",
              "⚠️ REP003 방문 건수 저조 — 지원 필요",
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
              [
                "WS_서울_한국약품",
                "PH_110110_서울약국_100",
                "H001",
                "PROD_A001",
                "100",
                "500,000",
              ],
              [
                "WS_부산_부산약품",
                "PH_260402_해운대약국_200",
                "H003",
                "PROD_A001",
                "150",
                "750,000",
              ],
            ],
            insights: ["✅ 도매→약국→병원 완전 연결 흐름 정상 작동"],
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

      function replaceSpatialPayload(template, markers, routes) {
        return template
          .replace(
            /window\.__INITIAL_MARKERS__ = \/\*INITIAL_MARKERS_PLACEHOLDER\*\/ \[\];/,
            `window.__INITIAL_MARKERS__ = ${JSON.stringify(markers, null, 2)};`,
          )
          .replace(
            /window\.__INITIAL_ROUTES__ = \/\*INITIAL_ROUTES_PLACEHOLDER\*\/ \[\];/,
            `window.__INITIAL_ROUTES__ = ${JSON.stringify(routes, null, 2)};`,
          );
      }

      function buildSandboxTemplatePayload(data) {
        const members = data.rows.map((row, idx) => {
          const hospitalId = row[0];
          const actual = parseNumber(row[1]);
          const achieve = parseFloat(row[2]) || 0;
          const calls = parseNumber(row[3]);
          const target = Math.round(actual / Math.max(achieve / 100, 0.01));
          const monthlyActual = buildMonthSeries([
            actual * 0.68,
            actual * 0.72,
            actual * 0.76,
            actual * 0.81,
            actual * 0.86,
            actual * 0.88,
            actual * 0.91,
            actual * 0.95,
            actual * 0.98,
            actual * 1.0,
            actual * 1.02,
            actual * 1.05,
          ]).map((v) => Math.round(v));
          const monthlyTarget = buildMonthSeries([
            target * 0.7,
            target * 0.74,
            target * 0.79,
            target * 0.83,
            target * 0.88,
            target * 0.9,
            target * 0.94,
            target * 0.97,
            target * 1.0,
            target * 1.02,
            target * 1.04,
            target * 1.06,
          ]).map((v) => Math.round(v));
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
            shap: {
              PT: 0.18,
              시연: 0.11,
              클로징: 0.15,
              니즈환기: 0.1,
              대면: 0.14,
              컨택: 0.12,
              접근: 0.1,
              피드백: 0.1,
            },
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
        const achieve =
          totalTarget.reduce((a, b) => a + b, 0) > 0
            ? (
                (totalActual.reduce((a, b) => a + b, 0) /
                  totalTarget.reduce((a, b) => a + b, 0)) *
                100
              ).toFixed(1)
            : "0.0";
        const branchName = "MASTER OPS HQ";

        return {
          branches: {
            [branchName]: {
              members,
              avg: {
                HIR: 73.1,
                RTR: 69.4,
                BCR: 71.8,
                PHR: 70.2,
                PI: parseFloat(achieve),
                FGR: 6.3,
              },
              achieve: parseFloat(achieve),
              monthly_actual: totalActual,
              monthly_target: totalTarget,
              analysis: {
                importance: {
                  PT: 0.22,
                  Demo: 0.14,
                  Closing: 0.18,
                  Needs: -0.06,
                  FaceToFace: 0.12,
                  Contact: -0.08,
                  Access: 0.11,
                  Feedback: 0.09,
                },
                correlation: {
                  HIR: { HIR: 1, RTR: 0.62, BCR: 0.44, PHR: 0.4 },
                  RTR: { HIR: 0.62, RTR: 1, BCR: 0.38, PHR: 0.31 },
                  BCR: { HIR: 0.44, RTR: 0.38, BCR: 1, PHR: 0.56 },
                  PHR: { HIR: 0.4, RTR: 0.31, BCR: 0.56, PHR: 1 },
                },
                adj_correlation: {
                  HIR: { HIR: 1, RTR: 0.7, BCR: 0.52, PHR: 0.48 },
                  RTR: { HIR: 0.7, RTR: 1, BCR: 0.41, PHR: 0.36 },
                  BCR: { HIR: 0.52, RTR: 0.41, BCR: 1, PHR: 0.61 },
                  PHR: { HIR: 0.48, RTR: 0.36, BCR: 0.61, PHR: 1 },
                },
                ccf: [0.03, 0.05, 0.06, 0.04, 0.02],
              },
              prod_analysis: {},
            },
          },
          products: [],
          total_prod_analysis: {},
          total: {
            achieve: parseFloat(achieve),
            avg: {
              HIR: 73.1,
              RTR: 69.4,
              BCR: 71.8,
              PHR: 70.2,
              PI: parseFloat(achieve),
              FGR: 6.3,
            },
            monthly_actual: totalActual,
            monthly_target: totalTarget,
            analysis: {
              importance: {
                PT: 0.22,
                Demo: 0.14,
                Closing: 0.18,
                Needs: -0.06,
                FaceToFace: 0.12,
                Contact: -0.08,
                Access: 0.11,
                Feedback: 0.09,
              },
              correlation: {},
              adj_correlation: {},
              ccf: [0.03, 0.05, 0.06, 0.04, 0.02],
            },
          },
          total_avg: {
            HIR: 73.1,
            RTR: 69.4,
            BCR: 71.8,
            PHR: 70.2,
            PI: parseFloat(achieve),
            FGR: 6.3,
          },
          data_health: {
            integrity_score: 96,
            mapped_fields: {
              병원ID: "sales.hospital_id",
              담당자ID: "crm.rep_id",
              목표금액: "target.target_amount",
              실적금액: "sales.actual_amount",
            },
            missing_fields: [],
          },
          missing_data: [],
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
        if (!template) {
          return buildGenericExportHtml(data, "sandbox");
        }
        return replaceReportPayload(template, buildSandboxTemplatePayload(data));
      }

      function renderTerritoryTemplateHtml(data) {
        const template = getTemplateStore().spatial;
        if (!template) {
          return buildGenericExportHtml(data, "territory");
        }
        const payload = buildTerritoryTemplatePayload(data);
        return replaceSpatialPayload(template, payload.markers, payload.routes);
      }

      function buildTemplatePreviewShell(title, subtitle, badge) {
        return `
    <div class="actions">
      <button class="btn btn-primary" onclick="downloadOpsReport()">⬇️ 템플릿 HTML 다운로드</button>
      <button class="btn btn-outline" onclick="sendToSlideStudio()">🎨 슬라이드로 변환</button>
    </div>
    <div class="report-section">
      <h3>📦 Template Builder</h3>
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
        return `<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><title>${escapeHtml(data.title)}</title>
<style>body{font-family:system-ui;background:#0d1117;color:#e6edf3;padding:32px}.kpi-row{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:24px}.kpi-card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:16px}.kv{font-size:22px;font-weight:700;color:#58a6ff}.kl{font-size:11px;color:#8b949e;margin-top:4px}table{width:100%;border-collapse:collapse;font-size:13px;margin-bottom:24px}th{background:#21262d;color:#8b949e;padding:8px 12px;text-align:left}td{padding:8px 12px;border-bottom:1px solid #30363d}h2{margin-bottom:8px}h3{font-size:12px;color:#8b949e;text-transform:uppercase;letter-spacing:.5px;margin:20px 0 10px}.insight-item{background:#21262d;border-left:3px solid #58a6ff;padding:10px 14px;border-radius:0 6px 6px 0;margin-bottom:8px;font-size:13px}</style></head><body><h2>${escapeHtml(data.title)}</h2><p>${escapeHtml(data.period)} · ${escapeHtml(mod)}</p>${kpiHtml}<div class="report-section"><h3>상세 데이터</h3>${tableHtml}</div><div class="report-section"><h3>전략 인사이트</h3>${insightHtml}</div></body></html>`;
      }

      function buildOpsHtml(data, mod) {
        const kpiHtml = `<div class="kpi-row">${data.kpis.map((k) => `<div class="kpi-card"><div class="kv">${k.value}</div><div class="kl">${k.label}</div></div>`).join("")}</div>`;
        const tableHtml = `<table class="data-table"><thead><tr>${data.headers.map((h) => `<th>${h}</th>`).join("")}</tr></thead><tbody>${data.rows.map((r) => `<tr>${r.map((c) => `<td>${c}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
        const insightHtml = `<div class="insight-list">${data.insights.map((i) => `<div class="insight-item">${i}</div>`).join("")}</div>`;
        const mapSection =
          mod === "territory"
            ? `<div class="report-section"><h3>📍 영업 권역 지도</h3><div id="ops-map"></div></div>`
            : "";

        return `
    <div class="actions">
      <button class="btn btn-primary" onclick="downloadOpsReport()">⬇️ HTML 다운로드</button>
      <button class="btn btn-outline" onclick="sendToSlideStudio()">🎨 슬라이드로 변환</button>
    </div>
    <div class="report-section"><h3>📊 핵심 KPI</h3>${kpiHtml}</div>
    ${mapSection}
    <div class="report-section"><h3>📋 상세 데이터</h3>${tableHtml}</div>
    <div class="report-section"><h3>💡 전략적 인사이트</h3>${insightHtml}</div>
  `;
      }

      function initMap(markers, routes) {
        setTimeout(() => {
          const mapEl = document.getElementById("ops-map");
          if (!mapEl || mapEl._leaflet_id) return;
          const map = L.map("ops-map").setView([36.5, 127.8], 7);
          L.tileLayer(
            "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
            {
              attribution: "© OpenStreetMap © CARTO",
              maxZoom: 18,
            },
          ).addTo(map);
          const colorMap = {
            green: "#3fb950",
            yellow: "#d29922",
            red: "#f85149",
            gray: "#6e7681",
          };
          markers.forEach((m) => {
            const icon = L.divIcon({
              className: "",
              html: `<div style="width:14px;height:14px;border-radius:50%;background:${colorMap[m.color] || "#8b949e"};border:2px solid #fff;box-shadow:0 0 6px ${colorMap[m.color] || "#8b949e"}"></div>`,
            });
            L.marker([m.lat, m.lng], { icon })
              .addTo(map)
              .bindPopup(
                `<pre style="font-size:11px;line-height:1.5">${m.tooltip}</pre>`,
              );
          });
          routes.forEach((r) => {
            L.polyline(
              r.points.map((p) => [p[0], p[1]]),
              { color: r.color, weight: 2, opacity: 0.7, dashArray: "6 4" },
            ).addTo(map);
          });
        }, 100);
      }

      function loadOpsAsset(evt) {
        const file = evt.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (e) => {
          try {
            state.loadedAsset = JSON.parse(e.target.result);
            addLog("system", `📂 ${file.name} 로드 완료`);
          } catch (err) {
            alert("JSON 파싱 오류: " + err.message);
          }
        };
        reader.readAsText(file);
      }

      function downloadOpsReport() {
        const html =
          state.opsRenderedHtml ||
          buildGenericExportHtml(
            state.opsReportContent || getSampleData(state.selectedModule),
            state.selectedModule,
          );
        const a = document.createElement("a");
        a.href = URL.createObjectURL(new Blob([html], { type: "text/html" }));
        a.download = `ops_report_${state.selectedModule}_${Date.now()}.html`;
        a.click();
      }

      function sendToSlideStudio() {
        const data = getSampleData(state.selectedModule);
        document.getElementById("slide-content-text").value =
          `[모듈: ${state.selectedModule}]\n${data.title} (${data.period})\n\n` +
          data.insights.join("\n") +
          "\n\n주요 데이터:\n" +
          data.rows.map((r) => r.join(" | ")).join("\n");
        switchLayer("slide");
        document.querySelector(".tab-btn:last-child").classList.add("active");
        document
          .querySelector(".tab-btn:first-child")
          .classList.remove("active");
        addLog(
          "system",
          `📊 OPS ${state.selectedModule} 데이터를 WebSlide Studio로 전송했습니다.`,
        );
      }

      // ── Layer2: WebSlide Studio ───────────────
      function switchInputTab(tab, el) {
        document
          .querySelectorAll(".input-tab")
          .forEach((t) => t.classList.remove("active"));
        document
          .querySelectorAll(".input-panel")
          .forEach((p) => p.classList.remove("active"));
        el.classList.add("active");
        document.getElementById(`panel-${tab}`).classList.add("active");
      }

      function selectTheme(theme, el) {
        state.selectedTheme = theme;
        document
          .querySelectorAll(".theme-chip")
          .forEach((c) => c.classList.remove("selected"));
        el.classList.add("selected");
        addLog(
          "architect",
          `테마 ${theme} 선택됨 — Blueprint 기반으로 적용 예정`,
        );
      }

      function setPhase(phase) {
        state.currentPhase = phase;
        document.querySelectorAll(".phase-item").forEach((p) => {
          p.classList.remove("current", "done");
          const phases = ["intake", "strategy", "blueprint", "build"];
          const pIdx = phases.indexOf(p.dataset.phase);
          const cIdx = phases.indexOf(phase);
          if (pIdx < cIdx) p.classList.add("done");
          else if (pIdx === cIdx) p.classList.add("current");
        });
      }

      function runAnalysis() {
        const content = document
          .getElementById("slide-content-text")
          .value.trim();
        if (!content) {
          alert("콘텐츠를 입력하세요.");
          return;
        }

        setPhase("strategy");
        addLog("analyst", "[PHASE 0 — Intake] 문서 분석 중...");

        setTimeout(() => {
          addLog(
            "analyst",
            `핵심 주제 파악 완료. 콘텐츠 길이: ${content.length}자`,
          );
          addLog("architect", "[PHASE 1 — Strategy] 테마 스코어링 시작...");

          setTimeout(() => {
            const themeNames = {
              A: "Signature Premium",
              B: "Enterprise Swiss",
              C: "Minimal Keynote",
              D: "Analytical Dashboard",
              E: "Deep Tech Dark",
            };
            addLog(
              "architect",
              `✅ 추천 테마: ${state.selectedTheme} | ${themeNames[state.selectedTheme]}`,
            );
            addLog(
              "architect",
              "[PHASE 2 — Blueprint] 슬라이드 구조 설계 중...",
            );

            const blueprints = generateBlueprint(content);
            state.blueprints = blueprints;
            renderBlueprint(blueprints);
            setPhase("blueprint");

            document.getElementById("btn-build").disabled = false;
            document.getElementById("slide-status").textContent =
              `Blueprint 완성 — ${blueprints.length}장 슬라이드 구성됨. HTML 생성 버튼을 클릭하세요.`;
            addLog(
              "architect",
              `Blueprint 완성: ${blueprints.length}장 슬라이드 — 승인 후 Build 진행`,
            );
          }, 800);
        }, 600);
      }

      function generateBlueprint(content) {
        const lines = content.split("\n").filter((l) => l.trim());
        const slides = [
          {
            num: 1,
            type: "message",
            purpose: "표지 / 핵심 메시지 전달",
            headline: lines[0] || "SFE 전략 보고서",
            supports: [],
            visual: "Full-bleed statement",
            layout: "centered hero",
            density: "low",
            bg: "monochrome solid",
            notes: "강한 타이포 중심",
          },
          {
            num: 2,
            type: "structure",
            purpose: "목차 / 전체 구조 안내",
            headline: "보고서 구성",
            supports: ["1. 핵심 성과 요약", "2. 분석 데이터", "3. 전략 제언"],
            visual: "Step blocks",
            layout: "centered grid",
            density: "medium",
            bg: "flat neutral",
            notes: "구조 시각화 우선",
          },
          {
            num: 3,
            type: "data",
            purpose: "핵심 KPI 데이터 전달",
            headline: "핵심 성과 지표",
            supports: lines.slice(1, 4),
            visual: "KPI cards + chart",
            layout: "KPI top + chart bottom",
            density: "high",
            bg: "subtle grid texture",
            notes: "Chart-first, takeaway 즉시 보이게",
          },
          {
            num: 4,
            type: "structure",
            purpose: "전략 방향 제시",
            headline: "핵심 전략 방향",
            supports: lines.slice(4, 7),
            visual: "Process flow",
            layout: "split left-right",
            density: "medium",
            bg: "subtle mesh",
            notes: "Diagram-first",
          },
          {
            num: 5,
            type: "message",
            purpose: "결론 / 다음 단계",
            headline: "결론 및 실행 계획",
            supports: ["즉시 실행 가능한 다음 단계 정의"],
            visual: "Callout + action cards",
            layout: "asymmetric editorial",
            density: "low",
            bg: "radial focus glow",
            notes: "메시지 전달 우선",
          },
        ];
        return slides;
      }

      function renderBlueprint(bps) {
        const preview = document.getElementById("slide-preview");
        preview.innerHTML =
          `<div class="blueprint-view">` +
          bps
            .map(
              (b) => `
      <div class="bp-slide">
        <div class="bp-num">SLIDE ${b.num}</div>
        <div class="bp-headline">${b.headline}</div>
        <div class="bp-meta">
          <span class="bp-tag type-${b.type}">${b.type}</span>
          <span class="bp-tag">${b.visual}</span>
          <span class="bp-tag">${b.layout}</span>
          <span class="bp-tag">밀도: ${b.density}</span>
          <span class="bp-tag">BG: ${b.bg}</span>
        </div>
        ${b.supports.length ? `<ul style="margin-top:8px;padding-left:16px;font-size:12px;color:var(--muted)">${b.supports.map((s) => `<li style="margin-bottom:3px">${s}</li>`).join("")}</ul>` : ""}
        <div style="font-size:11px;color:var(--primary);margin-top:8px">📝 ${b.notes}</div>
      </div>
    `,
            )
            .join("") +
          `</div>`;
      }

      function runBuild() {
        if (!state.blueprints.length) return;
        setPhase("build");
        document.getElementById("slide-status").textContent =
          "HTML 슬라이드 생성 중...";
        addLog("builder", "[PHASE 3 — Build] Blueprint 기반 HTML 생성 시작...");

        setTimeout(() => {
          const html = buildSlideHtml(state.blueprints, state.selectedTheme);
          state.generatedHtml = html;
          showGeneratedSlide(html);
          document.getElementById("btn-download").disabled = false;
          document.getElementById("slide-status").textContent =
            `✅ ${state.blueprints.length}장 슬라이드 생성 완료`;
          addLog(
            "builder",
            `✅ 단일 HTML 완성 — ${state.blueprints.length}장, 테마: ${state.selectedTheme}`,
          );
        }, 1200);
      }

      function buildSlideHtml(bps, theme) {
        const themes = {
          A: {
            bg: "#0a0a0f",
            surface: "#12121e",
            primary: "#c084fc",
            text: "#f5f3ff",
            accent: "#818cf8",
          },
          B: {
            bg: "#ffffff",
            surface: "#f8fafc",
            primary: "#1e40af",
            text: "#0f172a",
            accent: "#3b82f6",
          },
          C: {
            bg: "#fafafa",
            surface: "#ffffff",
            primary: "#18181b",
            text: "#09090b",
            accent: "#6366f1",
          },
          D: {
            bg: "#0f172a",
            surface: "#1e293b",
            primary: "#0ea5e9",
            text: "#f0f9ff",
            accent: "#38bdf8",
          },
          E: {
            bg: "#020617",
            surface: "#0f172a",
            primary: "#22d3ee",
            text: "#e0f2fe",
            accent: "#67e8f9",
          },
        };
        const t = themes[theme] || themes.B;
        const embeddedScriptOpen = "<scr" + "ipt>";
        const embeddedScriptClose = "</scr" + "ipt>";
        return `<!DOCTYPE html>
<html lang="ko"><head><meta charset="UTF-8"><title>WebSlide — ${bps[0]?.headline || ""}</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:${t.bg};--surface:${t.surface};--primary:${t.primary};--text:${t.text};--accent:${t.accent}}
body{background:var(--bg);font-family:'Segoe UI',system-ui,sans-serif;overflow:hidden}
.slide-container{width:100vw;height:100vh;position:relative}
.slide{position:absolute;inset:0;display:none;align-items:center;justify-content:center;flex-direction:column;padding:60px;background:var(--bg)}
.slide.active{display:flex}
.slide-title{font-size:clamp(28px,4vw,52px);font-weight:800;color:var(--text);letter-spacing:-1px;text-align:center;margin-bottom:20px}
.slide-sub{font-size:clamp(14px,1.5vw,18px);color:var(--primary);opacity:.8;text-align:center;margin-bottom:40px}
.kpi-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;width:100%;max-width:900px}
.kpi-box{background:var(--surface);border:1px solid rgba(255,255,255,.08);border-radius:12px;padding:24px 20px;text-align:center}
.kpi-val{font-size:2em;font-weight:800;color:var(--primary)}
.kpi-lbl{font-size:12px;color:var(--text);opacity:.6;margin-top:6px;text-transform:uppercase;letter-spacing:.5px}
.steps{display:flex;gap:16px;width:100%;max-width:900px;justify-content:center}
.step-box{flex:1;background:var(--surface);border:1px solid rgba(255,255,255,.08);border-radius:12px;padding:20px;text-align:center}
.step-num{font-size:11px;color:var(--primary);font-weight:700;text-transform:uppercase;margin-bottom:8px}
.step-content{font-size:14px;color:var(--text);opacity:.8;line-height:1.5}
.nav{position:fixed;bottom:28px;left:50%;transform:translateX(-50%);display:flex;align-items:center;gap:12px;background:rgba(0,0,0,.5);backdrop-filter:blur(10px);border-radius:28px;padding:10px 20px;border:1px solid rgba(255,255,255,.1)}
.nav button{background:none;border:none;color:var(--text);font-size:18px;cursor:pointer;opacity:.7;transition:opacity .2s}
.nav button:hover{opacity:1}
.nav span{color:var(--text);font-size:13px;opacity:.5;min-width:50px;text-align:center}
.callout{background:var(--surface);border-left:4px solid var(--primary);border-radius:0 12px 12px 0;padding:24px 28px;max-width:700px;font-size:16px;color:var(--text);line-height:1.6}
</style></head><body>
<div class="slide-container">
${bps
  .map(
    (b, i) => `
<div class="slide${i === 0 ? " active" : ""}" id="slide-${i + 1}">
  <div class="slide-sub">SLIDE ${b.num} · ${b.type.toUpperCase()} · ${b.visual}</div>
  <h1 class="slide-title">${b.headline}</h1>
  ${
    b.type === "data"
      ? `<div class="kpi-grid">${b.supports
          .slice(0, 3)
          .map(
            (s) =>
              `<div class="kpi-box"><div class="kpi-val">—</div><div class="kpi-lbl">${s}</div></div>`,
          )
          .join("")}</div>`
      : b.type === "structure"
        ? `<div class="steps">${b.supports.map((s, j) => `<div class="step-box"><div class="step-num">STEP ${j + 1}</div><div class="step-content">${s}</div></div>`).join("")}</div>`
        : b.supports.length
          ? `<div class="callout">${b.supports[0]}</div>`
          : ""
  }
</div>`,
  )
  .join("")}
</div>
<div class="nav">
  <button onclick="prevSlide()">←</button>
  <span id="page">1 / ${bps.length}</span>
  <button onclick="nextSlide()">→</button>
</div>
${embeddedScriptOpen}
let cur=1;const total=${bps.length};
function goTo(n){if(n<1||n>total)return;document.querySelector('.slide.active').classList.remove('active');document.getElementById('slide-'+n).classList.add('active');cur=n;document.getElementById('page').textContent=n+' / '+total;}
function nextSlide(){goTo(cur+1);}function prevSlide(){goTo(cur-1);}
document.addEventListener('keydown',e=>{if(e.key==='ArrowRight'||e.key==='Space')nextSlide();if(e.key==='ArrowLeft')prevSlide();});
${embeddedScriptClose}</body></html>`;
      }

      function showGeneratedSlide(html) {
        const preview = document.getElementById("slide-preview");
        preview.innerHTML = `
    <div style="width:100%;max-width:900px;aspect-ratio:16/9;border-radius:8px;overflow:hidden;border:1px solid var(--border);box-shadow:0 8px 32px rgba(0,0,0,.4)">
      <iframe srcdoc="" style="width:100%;height:100%;border:none" id="slide-iframe"></iframe>
    </div>
    <p style="font-size:12px;color:var(--muted);text-align:center">실제 슬라이드 미리보기 — HTML 다운로드 후 브라우저에서 키보드(←→) 또는 Space로 탐색</p>
  `;
        document.getElementById("slide-iframe").srcdoc = html;
      }

      function downloadSlide() {
        if (!state.generatedHtml) return;
        const a = document.createElement("a");
        a.href = URL.createObjectURL(
          new Blob([state.generatedHtml], { type: "text/html" }),
        );
        a.download = `webslide_${state.selectedTheme}_${Date.now()}.html`;
        a.click();
      }

      function loadSlideFile(evt) {
        const file = evt.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (e) => {
          document.getElementById("slide-content-text").value = e.target.result;
          switchInputTab("text", document.querySelector(".input-tab"));
          document.querySelectorAll(".input-tab")[0].classList.add("active");
          document.getElementById("panel-text").classList.add("active");
          document.getElementById("panel-file").classList.remove("active");
          addLog(
            "system",
            `📂 ${file.name} 로드 완료 (${file.size.toLocaleString()} bytes)`,
          );
        };
        reader.readAsText(file);
      }

      // 드래그앤드롭
      const dz = document.getElementById("drop-zone");
      dz.addEventListener("dragover", (e) => {
        e.preventDefault();
        dz.classList.add("over");
      });
      dz.addEventListener("dragleave", () => dz.classList.remove("over"));
      dz.addEventListener("drop", (e) => {
        e.preventDefault();
        dz.classList.remove("over");
        const file = e.dataTransfer.files[0];
        if (file) {
          document.getElementById("slide-file").files = e.dataTransfer.files;
          loadSlideFile({ target: { files: e.dataTransfer.files } });
        }
      });

      function importFromOps() {
        const data = getSampleData(state.selectedModule || "sandbox");
        document.getElementById("slide-content-text").value =
          `${data.title} (${data.period})\n\n` +
          data.insights.join("\n") +
          "\n\n" +
          data.rows.map((r) => r.join(" | ")).join("\n");
        switchInputTab("text", document.querySelector(".input-tab"));
        document.querySelectorAll(".input-tab")[0].classList.add("active");
        document.getElementById("panel-text").classList.add("active");
        document.getElementById("panel-ops").classList.remove("active");
        addLog("system", `OPS ${state.selectedModule} 데이터 임포트 완료`);
      }

      function addLog(type, msg) {
        const log = document.getElementById("log-entries");
        const entry = document.createElement("div");
        entry.className = `log-entry ${type}`;
        const roleMap = {
          system: "SYSTEM",
          analyst: "ANALYST",
          architect: "ARCHITECT",
          builder: "BUILDER",
        };
        entry.innerHTML = `<span class="log-role">[${roleMap[type] || type}]</span>${msg}`;
        log.appendChild(entry);
        log.scrollTop = log.scrollHeight;
      }

      function clearLog() {
        document.getElementById("log-entries").innerHTML =
          '<div class="log-entry system">Log cleared.</div>';
      }

      // 초기 렌더링
      renderOpsReport("sandbox");
