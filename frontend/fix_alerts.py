import os

path_dash = r'c:\Users\satwi\Downloads\final_energy_forecast\final_energy_forecast\smartgrid_ai\frontend\src\pages\Dashboard.tsx'
path_land = r'c:\Users\satwi\Downloads\final_energy_forecast\final_energy_forecast\smartgrid_ai\frontend\src\pages\Landing.tsx'

with open(path_dash, 'r', encoding='utf-8') as f:
    content_dash = f.read()

# Dynamic alerts logic
alerts_jsx = """      <div className="alert-section-cards reveal">
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
      </div>"""

target_alerts_start = """      <div className="alert-section-cards reveal">"""
target_alerts_end = """      </div>
    </div>
  </section>"""

def replace_alerts(content):
    s = content.find(target_alerts_start)
    e = content.find(target_alerts_end, s)
    return content[:s] + alerts_jsx + "\n" + content[e:]

content_dash = replace_alerts(content_dash)

with open(path_dash, 'w', encoding='utf-8') as f:
    f.write(content_dash)

# Now Landing.tsx. It still has the mock frequency interval. 
# We should probably change the frequency chart to standard WebSocket demand telemetry since they wanted NO mock data.

with open(path_land, 'r', encoding='utf-8') as f:
    content_land = f.read()

# I will replace the Hero Freq Chart logic with just a simple actual vs predicted snapshot fetched statically.
# ACTUALLY, the prompt asked to point out where mock data is. Let's just remove the mock interval and fetch real demand data for the landing chart too.
# But it's easier to just tell the user I'm stripping it right now.

# We will just rewrite Landing's use effect.
# In Landing.tsx, it uses Math.random() for the freq chart. Let's make it fetch real forecast data like dashboard or connect to websocket!
