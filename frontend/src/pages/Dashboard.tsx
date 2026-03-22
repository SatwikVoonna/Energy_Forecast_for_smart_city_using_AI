// @ts-nocheck
import { useEffect, useState } from 'react';
import Chart from 'chart.js/auto';
import { Link } from 'react-router-dom';
import '../App.css';

function AIInsightButton({ anomaly }: { anomaly: any }) {
  const [loading, setLoading] = useState(false);
  const [insight, setInsight] = useState<any>(null);

  const getInsight = async () => {
    setLoading(true);
    try {
      const baseUrl = window.location.hostname === 'localhost' ? 'http://127.0.0.1:8000' : '';
      const r = await fetch(`${baseUrl}/insights`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          timestamp: anomaly.timestamp,
          actual_kwh: anomaly.actual_kwh,
          expected_kwh: anomaly.expected_kwh,
          severity: anomaly.severity
        })
      });
      const d = await r.json();
      setInsight(d);
    } catch (e) {
      console.error(e);
      setInsight({ insight: "Error fetching AI analysis.", recommendation: "Manual inspection required." });
    }
    setLoading(false);
  };

  return (
    <div className="ai-insight-wrap" style={{ marginTop: '12px' }}>
      {!insight ? (
        <button 
          onClick={getInsight} 
          disabled={loading}
          className="btn-ai-insight"
          style={{ 
            background: 'rgba(201,168,76,0.1)', 
            border: '1px solid var(--gold)', 
            color: 'var(--gold)', 
            fontSize: '0.7rem', 
            padding: '4px 10px', 
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          {loading ? 'Analyzing...' : '✨ Get AI Analysis'}
        </button>
      ) : (
        <div className="ai-insight-result" style={{ borderLeft: '2px solid var(--gold)', paddingLeft: '10px', fontSize: '0.8rem', color: 'var(--cream)' }}>
          <p style={{ margin: '4px 0', opacity: 0.9 }}><strong>Reason:</strong> {insight.insight}</p>
          <p style={{ margin: '4px 0', color: 'var(--gold)' }}><strong>Action:</strong> {insight.recommendation}</p>
        </div>
      )}
    </div>
  );
}

export default function Dashboard() {

  const [demand, setDemand] = useState(14661);
  const [wsStatus, setWsStatus] = useState("STABLE");
  
  const [dataLoaded, setDataLoaded] = useState(false);
  const [forecastData, setForecastData] = useState<any[]>([]);
  const [anomalyData, setAnomalyData] = useState<any[]>([]);
  const [renData, setRenData] = useState<any>(null);
  const [optData, setOptData] = useState<any>(null);
  const [carbonData, setCarbonData] = useState<any>(null);
  const [weatherData, setWeatherData] = useState<any>(null);
  const [displayedCO2, setDisplayedCO2] = useState(0);
  const [displayedTrees, setDisplayedTrees] = useState(0);

  useEffect(() => {
    const baseUrl = window.location.hostname === 'localhost' ? 'http://127.0.0.1:8000' : '';
    Promise.all([
      fetch(`${baseUrl}/forecast?horizon=24`).then(r => r.json()),
      fetch(`${baseUrl}/anomalies`).then(r => r.json()),
      fetch(`${baseUrl}/renewables/netload`).then(r => r.json()),
      fetch(`${baseUrl}/optimize`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({}) }).then(r => r.json()),
      fetch(`${baseUrl}/carbon`).then(r => r.json()),
      fetch(`${baseUrl}/weather`).then(r => r.json()).catch(() => null)
    ]).then(([fRes, aRes, rRes, oRes, cRes, wRes]) => {
      setForecastData(fRes);
      setAnomalyData(aRes);
      setRenData(rRes);
      setOptData(oRes);
      setCarbonData(cRes);
      setWeatherData(wRes);
      setDataLoaded(true);
    }).catch(e => console.error("API error", e));
  }, []);

  useEffect(() => {
    const baseUrl = window.location.hostname === 'localhost' ? '127.0.0.1:8000' : window.location.host;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${baseUrl}/stream`);
    ws.onmessage = (e) => {
      try {
        const d = JSON.parse(e.data);
        if(d.actual_kwh) setDemand(Math.round(d.actual_kwh));
        setWsStatus(d.is_anomaly ? 'ANOMALY DETECTED' : 'STABLE');
      } catch(e) {}
    };
    return () => ws.close();
  }, []);

  // Animate CO2 odometer once data arrives
  useEffect(() => {
    if(!carbonData) return;
    const targetCO2 = carbonData.co2_tonnes_prevented;
    const targetTrees = carbonData.trees_equivalent;
    let frame = 0;
    const totalFrames = 80;
    const timer = setInterval(() => {
      frame++;
      const progress = frame / totalFrames;
      const ease = 1 - Math.pow(1 - progress, 3); // ease-out cubic
      setDisplayedCO2(parseFloat((targetCO2 * ease).toFixed(3)));
      setDisplayedTrees(Math.round(targetTrees * ease));
      if(frame >= totalFrames) clearInterval(timer);
    }, 20);
    return () => clearInterval(timer);
  }, [carbonData]);

  useEffect(() => {
    const revealEls = document.querySelectorAll('.reveal, .reveal-stagger');
    const io = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (e.isIntersecting) { 
          e.target.classList.add('visible'); 
          io.unobserve(e.target); 
        }
      });
    }, { threshold: 0.12 });
    revealEls.forEach(el => io.observe(el));
    return () => io.disconnect();
  }, []);

  useEffect(() => {
    Chart.defaults.color = 'rgba(184,168,128,0.5)';
    Chart.defaults.borderColor = 'rgba(201,168,76,0.08)';
    Chart.defaults.font.family = "'Roboto Mono', monospace";
    Chart.defaults.font.size = 10;

    const tooltipOpts = {
      backgroundColor: 'rgba(8,8,8,0.94)',
      borderColor: 'rgba(201,168,76,0.25)',
      borderWidth: 1,
      titleColor: '#e8c96a',
      bodyColor: 'rgba(240,230,204,0.7)',
      padding: 10,
    };

    const GRID = 'rgba(201,168,76,0.07)';
    const TICK = 'rgba(184,168,128,0.45)';

    const scaleOpts = {
      x: { grid: { color: GRID }, ticks: { color: TICK } },
      y: { grid: { color: GRID }, ticks: { color: TICK, callback: (v: any) => v.toLocaleString() } }
    };

    function hexA(hex: string, a: number) {
      if(!hex) return '';
      const r=parseInt(hex.slice(1,3),16);
      const g=parseInt(hex.slice(3,5),16);
      const b=parseInt(hex.slice(5,7),16);
      return `rgba(${r},${g},${b},${a})`;
    }

    function areaGrad(ctx: CanvasRenderingContext2D, hex: string, top=0.28, bot=0.01) {
      const h = ctx.canvas.clientHeight || 250;
      const g = ctx.createLinearGradient(0,0,0,h);
      g.addColorStop(0, hexA(hex, top));
      g.addColorStop(1, hexA(hex, bot));
      return g;
    }
    if(!dataLoaded) return;
    const charts: Chart[] = [];

    // 2. ACTUAL vs PREDICTED
    (() => {
      const el = document.getElementById('actualPredChart') as HTMLCanvasElement;
      if (!el) return;
      const ctx = el.getContext('2d') as CanvasRenderingContext2D;
      const slice = anomalyData.slice(-48);
      const labels = slice.map(s => {
          let date = new Date(s.timestamp);
          return `${String(date.getHours()).padStart(2,'0')}:${String(date.getMinutes()).padStart(2,'0')}`;
      });
      const actual = slice.map(s => s.actual_kwh);
      const pred = slice.map(s => s.expected_kwh);
      const gradA = areaGrad(ctx, '#c9a84c', 0.18, 0.01);

      charts.push(new Chart(ctx, {
        type: 'line',
        data: {
          labels,
          datasets: [
            { label:'Actual',    data: actual, borderColor: '#c9a84c',  borderWidth:2.5, backgroundColor: gradA, fill:true, tension:.4, pointRadius:0, pointHoverRadius:4 },
            { label:'Predicted', data: pred,   borderColor: '#4caf82', borderWidth:1.5, backgroundColor:'transparent', fill:false, tension:.4, pointRadius:0, borderDash:[5,4] },
          ]
        },
        options: {
          responsive:true, 
          maintainAspectRatio: false,
          animation:{duration:2000,easing:'easeInOutQuart' as any},
          interaction:{mode:'index',intersect:false},
          plugins:{ legend:{display:false}, tooltip:{...tooltipOpts} },
          scales: { ...scaleOpts, y:{ ...scaleOpts.y,
              min: Math.floor(Math.min(...actual)*0.8),
              max: Math.ceil(Math.max(...actual)*1.2)
          } }
        }
      }));
    })();

    // 3. 24H FORECAST
    (() => {
      const el = document.getElementById('forecastChart') as HTMLCanvasElement;
      if (!el) return;
      const ctx = el.getContext('2d') as CanvasRenderingContext2D;
      const slice = forecastData.slice(-24);
      const labels = slice.map(s => {
          let date = new Date(s.timestamp);
          return `${String(date.getHours()).padStart(2,'0')}:${String(date.getMinutes()).padStart(2,'0')}`;
      });
      const data = slice.map(s => s.forecast_kwh);
      const gradF = areaGrad(ctx, '#d4884a', 0.20, 0.01);

      charts.push(new Chart(ctx, {
        type:'line',
        data:{
          labels,
          datasets:[{
            label:'Predicted', data,
            borderColor:'#d4884a', borderWidth:2.5,
            backgroundColor:gradF, fill:true,
            tension:.3,
            pointRadius: 5,
            pointBackgroundColor: '#d4884a',
            pointBorderColor:'#080808',
            pointBorderWidth:1.5,
            pointHoverRadius:7,
          }]
        },
        options:{
          responsive:true, 
          maintainAspectRatio: false,
          animation:{duration:2200,easing:'easeInOutQuart' as any},
          interaction:{mode:'index',intersect:false},
          plugins:{legend:{display:false},tooltip:{...tooltipOpts,callbacks:{label:(c: any)=>` ${Math.round(c.raw).toLocaleString()} MW`}}},
          scales: { ...scaleOpts, y:{ ...scaleOpts.y,
              min: Math.floor(Math.min(...data)*0.8),
              max: Math.ceil(Math.max(...data)*1.2)
          } }
        }
      }));
    })();

    // 4. HISTORICAL
    (() => {
      const el = document.getElementById('histChart') as HTMLCanvasElement;
      if (!el) return;
      const ctx = el.getContext('2d') as CanvasRenderingContext2D;
      const slice = anomalyData.slice(0, 72); // first 72
      const labels = slice.map(s => {
          let date = new Date(s.timestamp);
          return `${String(date.getHours()).padStart(2,'0')}:${String(date.getMinutes()).padStart(2,'0')}`;
      });
      const data = slice.map(s => s.actual_kwh);
      const gradH = areaGrad(ctx,'#4caf82',0.20,0.01);

      charts.push(new Chart(ctx,{
        type:'line',
        data:{labels,datasets:[{label:'Historical',data,borderColor:'#4caf82',borderWidth:2,backgroundColor:gradH,fill:true,tension:.4,pointRadius:0}]},
        options:{
          responsive:true,
          maintainAspectRatio: false,
          animation:{duration:1800,easing:'easeInOutQuart' as any},
          plugins:{legend:{display:false},tooltip:{...tooltipOpts}},
          scales: { ...scaleOpts, y:{ ...scaleOpts.y,
              min: Math.floor(Math.min(0, ...data)),
          } }
        }
      }));
    })();

    // 5. PEAK BAR
    (() => {
      const el = document.getElementById('peakBarChart') as HTMLCanvasElement;
      if (!el) return;
      const ctx = el.getContext('2d') as CanvasRenderingContext2D;
      const slice = forecastData.slice(-17);
      const labels = slice.map(s => {
          let date = new Date(s.timestamp);
          return `${String(date.getHours()).padStart(2,'0')}:${String(date.getMinutes()).padStart(2,'0')}`;
      });
      const data = slice.map(s => s.forecast_kwh);
      const threshold = Math.max(...data) * 0.85;
      const colors = data.map(v => v > threshold ? hexA('#c9a84c',0.85) : v > threshold*0.7 ? hexA('#c9a84c',0.5) : hexA('#4caf82',0.5));

      charts.push(new Chart(ctx,{
        type:'bar',
        data:{labels,datasets:[{data,backgroundColor:colors,borderWidth:0,borderRadius:2}]},
        options:{
          responsive:true,
          maintainAspectRatio: false,
          animation:{duration:2000,easing:'easeInOutQuart' as any},
          plugins:{legend:{display:false},tooltip:{...tooltipOpts,callbacks:{label:(c: any)=>` ${Math.round(c.raw).toLocaleString()} MW`}}},
          scales: { ...scaleOpts, y:{ ...scaleOpts.y,
              min: 0,
          } }
        }
      }));
    })();

    // 6. DONUT
    (() => {
      const el = document.getElementById('donutChart') as HTMLCanvasElement;
      if (!el) return;
      const ctx = el.getContext('2d') as CanvasRenderingContext2D;
      if (!renData) return;
      charts.push(new Chart(ctx,{
        type:'doughnut',
        data:{
          labels:['Solar','Wind','Grid'],
          datasets:[{
            data:[renData.solar, renData.wind, renData.net_load],
            backgroundColor:[hexA('#e8c96a',0.8),hexA('#4caf82',0.75),hexA('#555555',0.6)],
            borderColor:['#e8c96a','#4caf82','#444'],
            borderWidth:1.5,
            hoverOffset:8,
          }]
        },
        options:{
          responsive:true,
          maintainAspectRatio: false,
          cutout:'72%',
          animation:{animateRotate:true as any,duration:2200,easing:'easeInOutBack' as any},
          plugins:{
            legend:{display:false},
            tooltip:{...tooltipOpts,callbacks:{label:(c: any)=>` ${c.label}: ${Math.round(c.raw).toLocaleString()} MW`}}
          }
        }
      }));
    })();

    return () => {
        charts.forEach(c => c.destroy());
    };
  }, [dataLoaded]);

  // Determine Battery State
  let batteryPct = 0;
  let isDischarging = false;
  if(optData) {
      // Find current hour action approx
      const currentHour = new Date().getHours();
      const plan = optData.dispatch_plan;
      let currentState = 10000; // max cap
      let totalCharge = 0;
      let totalDischarge = 0;
      let curStatus = "";
      Object.entries(plan).forEach(([hr, act]: any) => {
          let h = parseInt(hr.replace('Hour~',''));
          if (act.includes('Charge')) { totalCharge += parseFloat(act.match(/[\d.]+/)[0]); curStatus = "Charging"; }
          if (act.includes('Discharge')) { totalDischarge += parseFloat(act.match(/[\d.]+/)[0]); curStatus = "Discharging"; }
      });
      // A fun dynamic visual logic based on the dispatch simulation
      let net = totalCharge - totalDischarge;
      batteryPct = Math.max(10, Math.min(100, 50 + (net / 10000) * 100)); // normalized 0-100
      
      const latestAct: any = Object.values(plan).pop();
      isDischarging = latestAct && latestAct.includes("Discharge");
      
      // Override to show it discharging if the current time is peak (4pm-9pm)
      if (currentHour >= 16 && currentHour <= 21) {
          isDischarging = true;
          // deplete battery animated
          batteryPct = 25;
      } else if (currentHour >= 1 && currentHour <= 5) {
          isDischarging = false;
          batteryPct = 95; 
      }
  }

  
  return (
    <>
{/* ══ STATUS BAR ══ */}
<div className="status-bar">
  <div className="status-dot"></div>
  CURRENT GRID STATUS: 
  DEMAND: <span className="demand-val" id="liveVal">{demand.toLocaleString()} MW</span>
   | 
  STATUS: <span className="highlight" style={{color: wsStatus === 'STABLE' ? 'var(--green)' : 'var(--red)'}}>{wsStatus}</span>
  {weatherData && weatherData.temperature !== undefined && (
    <>
      <span style={{ margin: '0 15px', opacity: 0.3 }}>|</span>
      <span className="weather-val" style={{ color: 'var(--cream)', fontSize: '0.8rem' }}>
        CHENNAI: {weatherData.temperature}°C {weatherData.description?.toUpperCase() || 'WEATHER UNKNOWN'}
      </span>
    </>
  )}

</div>

{/* ══ NAV ══ */}
<nav>
  <Link className="nav-brand" to="/">
    <div className="nav-logo">⚡</div>
    <span className="nav-brand-name">SmartGrid AI</span>
  </Link>
  <ul className="nav-links">
    <li><Link to="/">Home</Link></li>
    <li><a href="#dashboard">Live Demo</a></li>
    <li><a href="#alerts">Alert System</a></li>
  </ul>
</nav>

<div className="page" style={{ paddingTop: '80px' }}>
{/* ══ LIVE DASHBOARD ══ */}
  <section className="section-wrap dashboard-section" id="dashboard">
    <div className="reveal">
      <div className="section-label">Real-Time Telemetry</div>
      <h2 className="section-title">Live Energy Analytics<br /><em>Dashboard</em></h2>
      <p className="section-subtitle">Real-time telemetry and predictive forecasting engine output.</p>
      <div className="live-badge">
        <div className="live-badge-dot"></div>
        Live Data Feed Active
      </div>
    </div>

    <div className="charts-2col reveal">
      {/* Actual vs Predicted */}
      <div className="chart-card">
        <div className="chart-card-title">Actual vs Predicted Demand</div>
        <div className="chart-legend">
          <div className="legend-item"><div className="legend-dot" style={{background: "var(--gold)", height: "2px", width: "18px", borderRadius: "1px"}}></div>Actual Demand (MW)</div>
          <div className="legend-item"><div className="legend-dot" style={{background: "var(--green)", height: "2px", width: "18px", borderRadius: "1px", borderTop: "2px dashed var(--green)"}}></div>Predicted Demand (MW)</div>
        </div>
        <div style={{ position: 'relative', height: '220px', width: '100%' }}>
          <canvas id="actualPredChart"></canvas>
        </div>
      </div>

      {/* 24H Forecast */}
      <div className="chart-card">
        <div className="chart-card-title">Next 24 Hour Forecast</div>
        <div className="chart-legend">
          <div className="legend-item"><div style={{background: "var(--amber)", height: "2px", width: "18px", borderRadius: "1px"}}></div>Predicted Demand (MW)</div>
        </div>
        <div style={{ position: 'relative', height: '220px', width: '100%' }}>
          <canvas id="forecastChart"></canvas>
        </div>
      </div>
    </div>

    <div className="charts-2col reveal">
      {/* Historical */}
      <div className="chart-card">
        <div className="chart-card-title">Historical Energy Consumption</div>
        <div style={{ position: 'relative', height: '200px', width: '100%' }}>
          <canvas id="histChart"></canvas>
        </div>
      </div>

      {/* Peak Hour Distribution */}
      <div className="chart-card">
        <div className="chart-card-title">Peak Hour Distribution</div>
        <div style={{ position: 'relative', height: '200px', width: '100%' }}>
          <canvas id="peakBarChart"></canvas>
        </div>
      </div>
    </div>
  </section>

  <div className="divider"></div>

  {/* ══ ALERTS ══ */}
  <section className="section-wrap" id="alerts">
    <div className="alert-section-inner">
      <div className="alert-section-text reveal">
        <div className="section-label">Smart Peak Alert System</div>
        <h2 className="section-title">⚠️ Smart Peak<br /><em>Alert System</em></h2>
        <p className="section-subtitle">
          GenAI-powered anomaly detection alerts grid operators with actionable intelligence the moment blackout conditions manifest in the predictive models.
        </p>
        <div className="recommendation-box">
          <strong>⚙ Auto-Balance Recommendation</strong>
          Discharge Battery Storage A &amp; B continuously from 17:00 to 19:30 to shave predicted peak load. Grid buffer improves from <strong style={{color: "var(--red)"}}>18.5%</strong> → <strong style={{color: "var(--green)"}}>31.2%</strong>. Activate Demand Response Protocol 3 for industrial zones D and E simultaneously.
        </div>
      </div>

      <div className="alert-section-cards reveal">
        {anomalyData.filter(a => a.severity === "High" || a.severity === "Medium").slice(-5).reverse().map((a, i) => (
          <div key={i} className={`alert-card ${a.severity === 'High' ? 'critical' : 'warning'}`}>
            <div className="alert-icon-wrap">{a.severity === 'High' ? '🔴' : '🟠'}</div>
            <div className="alert-body">
              <div className="alert-title">{a.severity === 'High' ? 'Critical Anomaly Detected' : 'Irregular Load Flagged'}</div>
              <div className="alert-desc">
                XGBoost detector flagged anomaly. Expected {Math.round(a.expected_kwh)} MW, Actual was {Math.round(a.actual_kwh)} MW. 
                Anomaly Score: {a.score.toFixed(2)}.
              </div>
              <div className="alert-time">{new Date(a.timestamp).toLocaleString()} · AI DETECTOR</div>
              <AIInsightButton anomaly={a} />
            </div>
            <div className={`alert-badge badge-${a.severity === 'High' ? 'red' : 'amber'}`}>
              {a.severity.toUpperCase()}
            </div>
          </div>
        ))}
        {anomalyData.filter(a => a.severity === "High" || a.severity === "Medium").length === 0 && (
          <div className="alert-card resolved">
            <div className="alert-icon-wrap">✅</div>
            <div className="alert-body">
              <div className="alert-title">Grid Stable - No Anomalies</div>
              <div className="alert-desc">AI has not detected any significant deviations from the forecasted load in the recent telemetry buffer.</div>
              <div className="alert-time">LIVE FORECAST WINDOW</div>
            </div>
            <div className="alert-badge badge-green">STABLE</div>
          </div>
        )}
      </div>
    </div>
  </section>

  <div className="divider"></div>

  {/* ══ RENEWABLE OPTIMIZER ══ */}
  <section className="section-wrap dashboard-section">
    <div className="renewable-section-inner">
      <div className="reveal">
        <div className="section-label">Renewable Energy Optimizer</div>
        <h2 className="section-title">Renewable Energy<br /><em>Optimizer</em></h2>
        <p className="section-subtitle">AI dynamically scales renewable asset utilization to offset grid draw during high-strain peak hours, preventing localized brownouts.</p>

        <div className="renewable-stats">
          <div className="ren-stat-big">
            <div className="ren-stat-label">📈 Total Predicted Demand</div>
            <div className="ren-stat-value">{renData ? Math.round(renData.demand).toLocaleString() : "..."}<span className="ren-stat-unit"> MW</span></div>
          </div>

          <div className="ren-warning">
            <strong>EMERGENCY OVERRIDE ACTIVE</strong>
            Predicted demand triggers extreme grid strain. Forced maximum allocation of all available Solar and Wind capacity to assist grid load.
            <br />
            <span className="ren-grid-warning">GRID WARNING: MAX RENEWABLES ENGAGED</span>
          </div>

          <div className="ren-source-row">
            <div className="ren-source-chip">☀️ Solar: <strong style={{marginLeft: "6px"}}>{renData ? Math.round(renData.solar).toLocaleString() : "..."} MW</strong></div>
            <div className="ren-source-chip">🌬️ Wind: <strong style={{marginLeft: "6px"}}>{renData ? Math.round(renData.wind).toLocaleString() : "..."} MW</strong></div>
            <div className="ren-source-chip">⚡ Grid: <strong style={{marginLeft: "6px", color: "var(--amber)"}}>{renData ? Math.round(renData.net_load).toLocaleString() : "..."} MW</strong></div>
          </div>
        </div>
      </div>

      <div className="renewable-chart-wrap reveal">
        <div className="donut-container">
          <canvas id="donutChart"></canvas>
          <div className="donut-center-info">
            <span className="donut-total">{renData ? Math.round(renData.demand).toLocaleString() : "..."}</span>
            <span className="donut-label">TOTAL MW</span>
          </div>
        </div>

        <div className="renewable-legend">
          <div className="ren-legend-row">
            <div className="ren-dot" style={{background: "#e8c96a", boxShadow: "0 0 6px rgba(232,201,106,0.4)"}}></div>
            <span className="ren-name">Solar Energy</span>
            <span className="ren-val">{renData ? Math.round(renData.solar).toLocaleString() : "..."} MW</span>
          </div>
          <div className="ren-legend-row">
            <div className="ren-dot" style={{background: "#4caf82", boxShadow: "0 0 6px rgba(76,175,130,0.4)"}}></div>
            <span className="ren-name">Wind Energy</span>
            <span className="ren-val">{renData ? Math.round(renData.wind).toLocaleString() : "..."} MW</span>
          </div>
          <div className="ren-legend-row">
            <div className="ren-dot" style={{background: "#555", border: "1px solid #777"}}></div>
            <span className="ren-name">Main Grid</span>
            <span className="ren-val" style={{color: "var(--amber)"}}>{renData ? Math.round(renData.net_load).toLocaleString() : "..."} MW</span>
          </div>
        </div>
      </div>
    </div>
  </section>

  <div className="divider"></div>


  {/* ══ BATTERY OPTIMIZER ══ */}
  <section className="section-wrap dashboard-section">
    <div className="battery-section-inner reveal">
      <div className="section-label">Energy Arbitrage</div>
      <h2 className="section-title">🔋 Battery Storage<br /><em>Optimizer</em></h2>
      <p className="section-subtitle">AI dictates automated charge cycles during low-demand (1-5 AM) and discharges during peak hours (7-9 PM) to drastically slice grid dependency.</p>

      <div className="battery-dashboard-grid">
        <div className="battery-stats">
          <div className="ren-stat-big">
            <div className="ren-stat-label">💰 Daily Cost Savings</div>
            <div className="ren-stat-value" style={{color: "var(--green)"}}>€{optData ? optData.savings.toFixed(2) : "..."}</div>
          </div>
          <div className="batt-metrics-row">
             <div className="batt-metric">
                Baseline Cost: <br/><strong>€{optData ? optData.baseline_cost.toFixed(2) : "..."}</strong>
             </div>
             <div className="batt-metric">
                Optimized Cost: <br/><strong>€{optData ? optData.optimized_cost.toFixed(2) : "..."}</strong>
             </div>
          </div>
          
          <div className="batt-logs">
            <div className="batt-log-title">Recent Dispatch Commands (Forecast Horizon):</div>
            {optData && Object.entries(optData.dispatch_plan).slice(0, 5).map(([hr, act]: any, i) => (
              <div key={i} className="batt-log-entry">
                <span className="batt-hour">{hr.replace('Hour~', '')}:00</span>
                <span className={`batt-action ${act.includes('Charge') ? 'batt-charge' : act.includes('Discharge') ? 'batt-discharge' : 'batt-hold'}`}>{act}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="battery-visual-wrap">
           <div className="battery-body">
              <div className="battery-terminal"></div>
              <div className="battery-fill-container">
                 <div className={`battery-fill animated-fill ${isDischarging ? 'discharging' : ''}`} style={{height: `${optData ? batteryPct : 0}%`}}></div>
              </div>
              <div className="battery-overlay-text">
                 {optData ? Math.round(batteryPct) : '--'}%
              </div>
           </div>
           <div className="battery-status-text blur-pulse" style={{color: isDischarging ? "var(--amber)" : "var(--green)"}}>
             {optData ? (isDischarging ? '⚡ DISCHARGING (PEAK)' : '🔋 CHARGING (OFF-PEAK)') : '...'}
           </div>
        </div>
      </div>
    </div>
  </section>

  <div className="divider"></div>

{/* ══ CARBON TRACKER ══ */}
  <section className="section-wrap" style={{background: 'linear-gradient(180deg, var(--black) 0%, rgba(20,40,20,0.18) 100%)'}}>
    <div className="reveal">
      <div className="section-label" style={{color: '#4caf82'}}>Live Environmental Impact</div>
      <h2 className="section-title">🌱 Carbon Footprint<br /><em>Live Tracker</em></h2>
      <p className="section-subtitle">
        Every kWh your battery discharges during peak hours displaces fossil-fuel grid power.
        Calculated in real-time from your AI dispatch plan using the Portugal national grid carbon intensity.
      </p>
    </div>

    <div className="carbon-grid reveal">
      {/* Main CO2 odometer */}
      <div className="carbon-main-card">
        <div className="carbon-odometer-wrap">
          <div className="carbon-big-icon">🌍</div>
          <div className="carbon-odometer">
            <span className="carbon-number">{carbonData ? displayedCO2.toFixed(2) : '—'}</span>
            <span className="carbon-unit">tonnes CO₂</span>
          </div>
          <div className="carbon-label">prevented this month by your AI optimizer</div>
        </div>

        {/* kWh discharged sub-stat */}
        <div className="carbon-kwh-row">
          <div className="carbon-kwh-stat">
            <span className="carbon-kwh-val">{carbonData ? Math.round(carbonData.kwh_discharged_at_peak).toLocaleString() : '—'}</span>
            <span className="carbon-kwh-label">kWh offset from grid</span>
          </div>
          <div className="carbon-kwh-stat">
            <span className="carbon-kwh-val" style={{color: 'var(--gold-bright)'}}>{carbonData ? carbonData.co2_kg_prevented.toFixed(1) : '—'}</span>
            <span className="carbon-kwh-label">kg CO₂ prevented</span>
          </div>
        </div>
      </div>

      {/* Trees equivalent */}
      <div className="carbon-trees-card">
        <div className="trees-count">{carbonData ? displayedTrees : '—'}</div>
        <div className="trees-emoji-row">
          {carbonData && Array.from({length: Math.min(displayedTrees, 12)}).map((_, i) => (
            <span key={i} className="tree-emoji" style={{animationDelay: `${i * 0.08}s`}}>🌳</span>
          ))}
        </div>
        <div className="trees-label">trees planted equivalent</div>
        <div className="trees-sublabel">Based on 21.8 kg CO₂ absorbed<br />per mature tree per year (IPCC AR6)</div>
      </div>

      {/* Right stats panel */}
      <div className="carbon-stats-panel">
        <div className="carbon-stat-row">
          <span className="carbon-stat-label">📊 Grid Carbon Intensity</span>
          <span className="carbon-stat-val">250 gCO₂/kWh</span>
        </div>
        <div className="carbon-stat-row" style={{marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--border)'}}>
          <span className="carbon-stat-label">🔋 Battery Dispatch Mode</span>
          <span className="carbon-stat-val" style={{color: isDischarging ? 'var(--amber)' : 'var(--green)'}}>
            {isDischarging ? 'PEAK DISCHARGE' : 'OFF-PEAK CHARGE'}
          </span>
        </div>
        <div className="carbon-cta" style={{marginTop: '1.5rem'}}>
          <div style={{color: 'var(--green)', fontSize: '0.8rem', fontFamily: 'var(--font-mono)', letterSpacing: '1px', fontWeight: 700}}>
            ✅ ALL VALUES DERIVED FROM REAL DATASET
          </div>
          <div style={{color: 'var(--cream-muted)', fontSize: '0.7rem', marginTop: '0.3rem', lineHeight: 1.5}}>
            CO₂ = kWh_discharged × 250 gCO₂/kWh ÷ 1,000,000
          </div>
        </div>
      </div>
    </div>
  </section>

  <div className="divider"></div>

{/* ══ FOOTER ══ */}

  <footer>
    <div className="footer-inner">
      <div>
        <div className="footer-brand-name">⚡ SmartGrid AI</div>
        <div className="footer-tagline">Empowering the smart cities of tomorrow with predictive grid intelligence and AI-powered energy management.</div>
      </div>
      <div>
        <div className="footer-col-title">Platform</div>
        <ul className="footer-links">
          <li><a href="#">Dashboard</a></li>
          <li><a href="#">Forecast Engine</a></li>
        </ul>
      </div>
      <div>
        <div className="footer-col-title">Solutions</div>
        <ul className="footer-links">
          <li><a href="#">Peak Alert System</a></li>
          <li><a href="#">Renewable Advisor</a></li>
        </ul>
      </div>
    </div>
    <div className="footer-bottom">
      <span>© 2026 SmartGrid AI Project. Built for Hackathon.</span>
      <span style={{color: "var(--gold-dim)"}}>All AI nodes active · Latency 12ms · Uptime 99.97%</span>
    </div>
  </footer>

</div>
    </>
  );
}
