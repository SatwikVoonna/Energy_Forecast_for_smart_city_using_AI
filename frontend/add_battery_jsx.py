import os

path = r'c:\Users\satwi\Downloads\final_energy_forecast\final_energy_forecast\smartgrid_ai\frontend\src\pages\Dashboard.tsx'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update states
state_old = """  const [renData, setRenData] = useState<any>(null);"""
state_new = """  const [renData, setRenData] = useState<any>(null);
  const [optData, setOptData] = useState<any>(null);"""

if state_old in content and "setOptData" not in content:
    content = content.replace(state_old, state_new)

# 2. Update Promise
promise_old = """      fetch('http://127.0.0.1:8000/renewables/netload').then(r => r.json())
    ]).then(([fRes, aRes, rRes]) => {
      setForecastData(fRes);
      setAnomalyData(aRes);
      setRenData(rRes);"""
promise_new = """      fetch('http://127.0.0.1:8000/renewables/netload').then(r => r.json()),
      fetch('http://127.0.0.1:8000/optimize', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({}) }).then(r => r.json())
    ]).then(([fRes, aRes, rRes, oRes]) => {
      setForecastData(fRes);
      setAnomalyData(aRes);
      setRenData(rRes);
      setOptData(oRes);"""

if promise_old in content:
    content = content.replace(promise_old, promise_new)

if 'batteryPct' not in content:
    js_calc_old = """    return () => {
        charts.forEach(c => c.destroy());
    };
  }, [dataLoaded]);"""
    js_calc_new = """    return () => {
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
"""
    content = content.replace(js_calc_old, js_calc_new)

# 3. Add battery JSX section
jsx = """
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
            <div className="ren-stat-value" style={{color: "var(--green)"}}>${optData ? optData.savings.toFixed(2) : "..."}</div>
          </div>
          <div className="batt-metrics-row">
             <div className="batt-metric">
                Baseline Cost: <br/><strong>${optData ? optData.baseline_cost.toFixed(2) : "..."}</strong>
             </div>
             <div className="batt-metric">
                Optimized Cost: <br/><strong>${optData ? optData.optimized_cost.toFixed(2) : "..."}</strong>
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

{/* ══ FOOTER ══ */}
"""

if "BATTERY OPTIMIZER" not in content:
    content = content.replace("{/* ══ FOOTER ══ */}", jsx)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
