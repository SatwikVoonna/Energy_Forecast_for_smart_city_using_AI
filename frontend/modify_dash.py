import os

path = r'c:\Users\satwi\Downloads\final_energy_forecast\final_energy_forecast\smartgrid_ai\frontend\src\pages\Dashboard.tsx'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# I will replace the state section up to the Common Hooks section.
# Specifically lines from export default function Dashboard() { ... to useEffect(() => { revealEls ...

replacement_head = """export default function Dashboard() {

  const [demand, setDemand] = useState(14661);
  const [wsStatus, setWsStatus] = useState("STABLE");
  
  const [dataLoaded, setDataLoaded] = useState(false);
  const [forecastData, setForecastData] = useState<any[]>([]);
  const [anomalyData, setAnomalyData] = useState<any[]>([]);
  const [renData, setRenData] = useState<any>(null);

  useEffect(() => {
    Promise.all([
      fetch('http://127.0.0.1:8000/forecast?horizon=24').then(r => r.json()),
      fetch('http://127.0.0.1:8000/anomalies').then(r => r.json()),
      fetch('http://127.0.0.1:8000/renewables/netload').then(r => r.json())
    ]).then(([fRes, aRes, rRes]) => {
      setForecastData(fRes);
      setAnomalyData(aRes);
      setRenData(rRes);
      setDataLoaded(true);
    }).catch(e => console.error("API error", e));
  }, []);

  useEffect(() => {
    const ws = new WebSocket('ws://127.0.0.1:8000/stream');
    ws.onmessage = (e) => {
      try {
        const d = JSON.parse(e.data);
        if(d.actual_kwh) setDemand(Math.round(d.actual_kwh));
        setWsStatus(d.is_anomaly ? 'ANOMALY DETECTED' : 'STABLE');
      } catch(e) {}
    };
    return () => ws.close();
  }, []);

  useEffect(() => {
    const revealEls = document.querySelectorAll('.reveal, .reveal-stagger');"""

target_head_start = """export default function Dashboard() {"""
target_head_end = """useEffect(() => {
    const revealEls = document.querySelectorAll('.reveal, .reveal-stagger');"""

# The chart logic
replacement_charts = """    if(!dataLoaded) return;
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
  }, [dataLoaded]);"""

target_charts_start = """    const charts: Chart[] = [];

    // 2. ACTUAL vs PREDICTED"""

target_charts_end = """    return () => {
        charts.forEach(c => c.destroy());
    };
  }, []);"""

# In JSX, update the values dynamically
replacement_jsx = """{/* ══ STATUS BAR ══ */}
<div className="status-bar">
  <div className="status-dot"></div>
  CURRENT GRID STATUS: 
  DEMAND: <span className="demand-val" id="liveVal">{demand.toLocaleString()} MW</span>
   | 
  STATUS: <span className="highlight" style={{color: wsStatus === 'STABLE' ? 'var(--green)' : 'var(--red)'}}>{wsStatus}</span>
</div>"""

target_jsx_start = """{/* ══ STATUS BAR ══ */}"""
target_jsx_end = """{/* ══ NAV ══ */}"""

ren_jsx = """<div className="renewable-stats">
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
        </div>"""

target_ren_start = """<div className="renewable-stats">
          <div className="ren-stat-big">
            <div className="ren-stat-label">📈 Total Predicted Demand</div>"""
target_ren_end = """      </div>
    </div>
  </section>

  <div className="divider"></div>"""


c1 = content[:content.find(target_head_start)] + replacement_head + content[content.find(target_head_end) + len("useEffect(() => {\n    const revealEls = document.querySelectorAll('.reveal, .reveal-stagger');"):]

# Using string searches robustly for the next parts
c2 = c1[:c1.find(target_charts_start)] + replacement_charts + c1[c1.find(target_charts_end) + len(target_charts_end):]

c3 = c2[:c2.find(target_jsx_start)] + replacement_jsx + "\n\n" + c2[c2.find(target_jsx_end):]

c4 = c3[:c3.find(target_ren_start)] + ren_jsx + "\n" + c3[c3.find(target_ren_end):]

with open(path, 'w', encoding='utf-8') as f:
    f.write(c4)

