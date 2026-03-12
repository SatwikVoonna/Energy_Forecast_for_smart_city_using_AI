import re

app_tsx_path = r'c:\Users\satwi\Downloads\final_energy_forecast\final_energy_forecast\smartgrid_ai\frontend\src\App.tsx'

with open(app_tsx_path, 'r', encoding='utf-8') as f:
    content = f.read()

# I will write Landing.tsx, Dashboard.tsx, and rewrite App.tsx

landing_imports = """// @ts-nocheck
import { useEffect, useState } from 'react';
import Chart from 'chart.js/auto';
import { Link } from 'react-router-dom';
import '../App.css';

export default function Landing() {
"""

dashboard_imports = """// @ts-nocheck
import { useEffect, useState } from 'react';
import Chart from 'chart.js/auto';
import { Link } from 'react-router-dom';
import '../App.css';

export default function Dashboard() {
"""

app_imports = """// @ts-nocheck
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Landing from './pages/Landing';
import Dashboard from './pages/Dashboard';
import './App.css';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </BrowserRouter>
  );
}
"""

with open(r'c:\Users\satwi\Downloads\final_energy_forecast\final_energy_forecast\smartgrid_ai\frontend\src\App.tsx', 'w', encoding='utf-8') as f:
    f.write(app_imports)

# We will just write the basic string replacements manually in the python script.

def extract_block(content, start_str, end_str):
    start = content.find(start_str)
    end = content.find(end_str, start)
    return content[start:end] if start != -1 and end != -1 else ""

# The structure of App.tsx:
# App setup (line 7-15) - metrics state, demand state
# useEffect for IO and demand (line 17-42)
# useEffect for Chart Setup (line 44 - 297) -> split into landing charts and dash charts
# Return JSX (line 299 - 622) -> split

# ---- Common helpers inside charts useEffect ----
chart_helpers = """    Chart.defaults.color = 'rgba(184,168,128,0.5)';
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
"""

landing_chart = """    const charts: Chart[] = [];
""" + extract_block(content, "// 1. HERO MINI REAL-TIME FREQUENCY CHART", "    // 2. ACTUAL vs PREDICTED")

dashboard_charts = """    const charts: Chart[] = [];
""" + content[content.find("// 2. ACTUAL vs PREDICTED"): content.find("    return () => {")]

common_hooks = """
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
"""

landing_tsx = landing_imports + """
  const [metrics, setMetrics] = useState<any>(null);

  useEffect(() => {
    fetch('http://127.0.0.1:8000/metrics')
      .then(r => r.json())
      .then(d => setMetrics(d))
      .catch(e => console.error(e));
  }, []);

""" + common_hooks + """
  useEffect(() => {
""" + chart_helpers + landing_chart + """
    return () => {
        charts.forEach(c => c.destroy());
    };
  }, []);
  
  return (
    <>
      {/* ══ NAV ══ */}
<nav>
  <Link className="nav-brand" to="/">
    <div className="nav-logo">⚡</div>
    <span className="nav-brand-name">SmartGrid AI</span>
  </Link>
  <ul className="nav-links">
    <li><a href="#features">Features</a></li>
    <li><Link to="/dashboard">Live Dashboard</Link></li>
  </ul>
</nav>
<div className="page">
""" + extract_block(content, "{/* ══ HERO ══ */}", "{/* ══ LIVE DASHBOARD ══ */}") + """

  <div className="divider"></div>
""" + extract_block(content, "{/* ══ FOOTER ══ */}", "</div>{/* /page */}") + """
</div>
    </>
  );
}
"""

# fix hrefs in landing
landing_tsx = landing_tsx.replace('href="#dashboard"', 'to="/dashboard"')
landing_tsx = landing_tsx.replace('<a to="/dashboard"', '<Link to="/dashboard"')
landing_tsx = landing_tsx.replace('</a>', '</Link>', 1) # Wait, simple replace is fine if we are careful, let's substitute more precisely

landing_tsx = landing_tsx.replace('<a to="/dashboard" className="btn-primary">View Live Dashboard</a>', '<Link to="/dashboard" className="btn-primary">View Live Dashboard</Link>')

dashboard_tsx = dashboard_imports + """
  const [demand, setDemand] = useState(14661);

  useEffect(() => {
    const interval = setInterval(() => {
        setDemand(prev => {
            let next = prev + Math.round((Math.random() - 0.48) * 120);
            return Math.max(13800, Math.min(15500, next));
        });
    }, 3000);
    return () => clearInterval(interval);
  }, []);
""" + common_hooks + """
  useEffect(() => {
""" + chart_helpers + dashboard_charts + """
    return () => {
        charts.forEach(c => c.destroy());
    };
  }, []);
  
  return (
    <>
""" + extract_block(content, "{/* ══ STATUS BAR ══ */}", "{/* ══ NAV ══ */}") + """
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
""" + extract_block(content, "{/* ══ LIVE DASHBOARD ══ */}", "{/* ══ FOOTER ══ */}") + """

""" + extract_block(content, "{/* ══ FOOTER ══ */}", "</div>{/* /page */}") + """
</div>
    </>
  );
}
"""

import os
os.makedirs(r'c:\Users\satwi\Downloads\final_energy_forecast\final_energy_forecast\smartgrid_ai\frontend\src\pages', exist_ok=True)

with open(r'c:\Users\satwi\Downloads\final_energy_forecast\final_energy_forecast\smartgrid_ai\frontend\src\pages\Landing.tsx', 'w', encoding='utf-8') as f:
    f.write(landing_tsx)

with open(r'c:\Users\satwi\Downloads\final_energy_forecast\final_energy_forecast\smartgrid_ai\frontend\src\pages\Dashboard.tsx', 'w', encoding='utf-8') as f:
    f.write(dashboard_tsx)

