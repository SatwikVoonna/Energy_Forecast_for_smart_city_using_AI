import os

path = r'c:\Users\satwi\Downloads\final_energy_forecast\final_energy_forecast\smartgrid_ai\frontend\src\App.css'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

css_to_add = """
/* ════════════════════════════════════════════
   BATTERY OPTIMIZER 
════════════════════════════════════════════ */
.battery-dashboard-grid {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 2rem;
  margin-top: 2rem;
  align-items: center;
}
@media (max-width: 900px) { .battery-dashboard-grid { grid-template-columns: 1fr; } }
.battery-stats {
  background: var(--black-card);
  border: 1px solid var(--border);
  padding: 2rem;
  box-shadow: inset 0 0 40px rgba(0,0,0,0.5);
}
.batt-metrics-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 2rem;
}
.batt-metric {
  padding: 1rem;
  border: 1px dashed var(--border-mid);
  color: var(--cream-dim);
  font-family: var(--font-mono);
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 1px;
}
.batt-metric strong {
  color: var(--gold-bright);
  font-size: 1.25rem;
  display: block;
  margin-top: 0.25rem;
}
.batt-logs { margin-top: 1rem; }
.batt-log-title { color: var(--gold); text-transform: uppercase; letter-spacing: 1px; font-size: 0.75rem; margin-bottom: 0.75rem; font-weight: 700; }
.batt-log-entry { display: flex; align-items: center; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid var(--border); font-family: var(--font-mono); font-size: 0.85rem; }
.batt-hour { color: var(--cream-dim); }
.batt-action { padding: 0.15rem 0.6rem; border-radius: 2px; font-weight: 600; font-size: 0.75rem; }
.batt-charge { background: rgba(76,175,130,0.15); color: #4caf82; border: 1px solid #4caf82; }
.batt-discharge { background: rgba(200,80,80,0.15); color: #c85050; border: 1px solid #c85050; }
.batt-hold { background: rgba(201,168,76,0.1); color: var(--gold); border: 1px dashed var(--gold); }

/* SVG Battery Viz */
.battery-visual-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1.5rem;
}
.battery-body {
  position: relative;
  width: 140px;
  height: 280px;
  background: rgba(10,10,10,0.8);
  border: 3px solid var(--border-hi);
  border-radius: 12px;
  box-shadow: 0 0 20px rgba(0,0,0,0.8), inset 0 0 20px var(--gold-ghost);
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding: 6px;
}
.battery-terminal {
  position: absolute;
  top: -14px;
  left: 50%;
  transform: translateX(-50%);
  width: 46px;
  height: 12px;
  background: var(--border-hi);
  border-radius: 4px 4px 0 0;
}
.battery-fill-container {
  width: 100%;
  height: 100%;
  position: relative;
  background: rgba(20,20,20,0.5);
  border-radius: 6px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
}
.battery-fill {
  width: 100%;
  background: linear-gradient(0deg, #4caf82 0%, #a4e5c8 100%);
  box-shadow: inset 0 0 20px rgba(0,0,0,0.5), 0 -4px 12px rgba(76,175,130,0.6);
  transition: height 1.5s cubic-bezier(0.22, 1, 0.36, 1), background-color 1.5s ease;
  min-height: 4%;
}
.battery-fill.discharging {
  background: linear-gradient(0deg, #d4884a 0%, #f4c29c 100%);
  box-shadow: inset 0 0 20px rgba(0,0,0,0.5), 0 -4px 12px rgba(212,136,74,0.6);
}
.battery-overlay-text {
  position: absolute;
  top: 50%; left: 50%; transform: translate(-50%, -50%);
  font-family: var(--font-mono);
  font-size: 2rem;
  font-weight: 700;
  color: #fff;
  text-shadow: 0 2px 10px rgba(0,0,0,0.9);
  z-index: 10;
}
.battery-status-text {
  font-family: var(--font-mono);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 2px;
  font-size: 0.85rem;
  text-align: center;
}
.blur-pulse {
  animation: txtPulse 2s infinite alternate;
}
@keyframes txtPulse {
  0%   { opacity: 0.6; text-shadow: none; }
  100% { opacity: 1;   text-shadow: 0 0 10px currentColor; }
}
"""

if "BATTERY OPTIMIZER" not in content:
    content += css_to_add
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
