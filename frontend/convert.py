import re

html_file = r'C:\Users\satwi\Downloads\smartgrid-landing.html'
app_css_file = r'C:\Users\satwi\Downloads\final_energy_forecast\final_energy_forecast\smartgrid_ai\frontend\src\App.css'
app_tsx_file = r'C:\Users\satwi\Downloads\final_energy_forecast\final_energy_forecast\smartgrid_ai\frontend\src\App.tsx'

with open(html_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Extract CSS
css_match = re.search(r'<style>(.*?)</style>', content, re.DOTALL)
css_content = css_match.group(1) if css_match else ""

# Replace fonts in CSS to make it professional
css_content = css_content.replace("'Cormorant Garamond', Georgia, serif", "'Inter', system-ui, sans-serif")
css_content = css_content.replace("'Josefin Sans', sans-serif", "'Inter', system-ui, sans-serif")
css_content = css_content.replace("'Share Tech Mono', monospace", "'Roboto Mono', monospace")
css_content = "@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Roboto+Mono:wght@400;500;700&display=swap');\n" + css_content
css_content = css_content.replace("body {\n  background: var(--black);\n  color: var(--cream);\n  font-family: var(--font-sans);\n  line-height: 1.65;\n  overflow-x: hidden;\n}", "body {\n  background: var(--black);\n  color: var(--cream);\n  font-family: var(--font-sans);\n  line-height: 1.65;\n  overflow-x: hidden;\n  margin: 0;\n  padding: 0;\n}")

with open(app_css_file, 'w', encoding='utf-8') as f:
    f.write(css_content)


# Extract HTML Body
body_start = content.find('<!-- ══ STATUS BAR ══ -->')
body_end = content.find('<!-- /page -->') + len('<!-- /page -->')
html_body = content[body_start:body_end]

# Convert HTML to JSX
html_body = html_body.replace('class=', 'className=')
html_body = html_body.replace('<br>', '<br />')
html_body = html_body.replace('&nbsp;', ' ')
html_body = html_body.replace('<!-- /page -->', '{/* /page */}')
html_body = html_body.replace('<!--', '{/*').replace('-->', '*/}')

# Cover any unclosed tags or attributes with issues like style=""
def style_replacer(match):
    style_str = match.group(1)
    pairs = style_str.split(';')
    jsx_style = []
    for p in pairs:
        if not p.strip(): continue
        k, v = p.split(':', 1)
        k = k.strip()
        k = re.sub(r'-([a-z])', lambda m: m.group(1).upper(), k)
        jsx_style.append(f'{k}: "{v.strip()}"')
    return 'style={{' + ', '.join(jsx_style) + '}}'

html_body = re.sub(r'style="([^"]*)"', style_replacer, html_body)

tsx_content = """import { useEffect, useState } from 'react';
import Chart, { ChartTypeRegistry, TooltipItem } from 'chart.js/auto';
import './App.css';

export default function App() {
  const [demand, setDemand] = useState(14661);

  useEffect(() => {
    // Scroll reveal observer
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

    // Live Demand update
    const interval = setInterval(() => {
        setDemand(prev => {
            let next = prev + Math.round((Math.random() - 0.48) * 120);
            return Math.max(13800, Math.min(15500, next));
        });
    }, 3000);

    return () => {
        io.disconnect();
        clearInterval(interval);
    };
  }, []);

  useEffect(() => {
    // Chart Default Setup
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

    const charts: Chart[] = [];

    // 1. HERO MINI BAR CHART
    (() => {
      const el = document.getElementById('heroChart') as HTMLCanvasElement;
      if (!el) return;
      const ctx = el.getContext('2d') as CanvasRenderingContext2D;
      const labels = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug'];
      const data   = [12000,13200,13800,15200,16800,17500,18900,19945];
      const colors = data.map((v,i) => i === data.length-1 ? hexA('#c9a84c',0.9) : hexA('#c9a84c', 0.3 + i*0.08));
      charts.push(new Chart(ctx, {
        type: 'bar',
        data: {
          labels,
          datasets: [{
            data,
            backgroundColor: colors,
            borderColor: colors.map(c => c.replace(/[\d.]+\)$/, '1)')),
            borderWidth: 1,
            borderRadius: 3,
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: { duration: 1600, easing: 'easeInOutQuart' as any },
          plugins: { legend: { display: false }, tooltip: { ...tooltipOpts, callbacks: { label: (c: any) => ` ${c.raw.toLocaleString()} MW` } } },
          scales: {
            x: { grid: { display: false }, ticks: { color: TICK } },
            y: { grid: { color: GRID }, ticks: { color: TICK, callback: (v: any) => (v/1000).toFixed(0)+'K' }, min: 10000 }
          }
        }
      }));
    })();

    // 2. ACTUAL vs PREDICTED
    (() => {
      const el = document.getElementById('actualPredChart') as HTMLCanvasElement;
      if (!el) return;
      const ctx = el.getContext('2d') as CanvasRenderingContext2D;
      const labels: string[] = [];
      for(let i=0;i<24;i++) labels.push(`${String(i).padStart(2,'0')}:00`);
      function genWave(base: number, amp: number, noise: number) {
        return labels.map((_,i) => Math.round(base + amp*Math.sin((i-6)*Math.PI/14) + (Math.random()-.5)*noise));
      }
      const actual = genWave(15000, 4500, 600);
      const pred   = actual.map(v => Math.round(v + (Math.random()-.5)*300));
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
          scales: { ...scaleOpts, y:{ ...scaleOpts.y, min:10000, max:22000 } }
        }
      }));
    })();

    // 3. 24H FORECAST
    (() => {
      const el = document.getElementById('forecastChart') as HTMLCanvasElement;
      if (!el) return;
      const ctx = el.getContext('2d') as CanvasRenderingContext2D;
      const now = new Date();
      const labels = Array.from({length:10},(_,i)=>{
        const t = new Date(now.getTime()+i*2*3600000);
        return `${String(t.getHours()).padStart(2,'0')}:${String(t.getMinutes()).padStart(2,'0')}`;
      });
      const data = [20000,20500,20200,19800,19500,18900,18500,18600,18500,18500];
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
          plugins:{legend:{display:false},tooltip:{...tooltipOpts,callbacks:{label:(c: any)=>` ${c.raw.toLocaleString()} MW`}}},
          scales:{ ...scaleOpts, y:{...scaleOpts.y,min:16000,max:22000} }
        }
      }));
    })();

    // 4. HISTORICAL
    (() => {
      const el = document.getElementById('histChart') as HTMLCanvasElement;
      if (!el) return;
      const ctx = el.getContext('2d') as CanvasRenderingContext2D;
      const labels: string[] = [];
      for(let i=0;i<24;i++) labels.push(`${String(i).padStart(2,'0')}:00`);
      const data = labels.map((_,i)=>Math.round(12000+6000*Math.sin((i-5)*Math.PI/15)+(Math.random()-.5)*400));
      const gradH = areaGrad(ctx,'#4caf82',0.20,0.01);

      charts.push(new Chart(ctx,{
        type:'line',
        data:{labels,datasets:[{label:'Historical',data,borderColor:'#4caf82',borderWidth:2,backgroundColor:gradH,fill:true,tension:.4,pointRadius:0}]},
        options:{
          responsive:true,
          maintainAspectRatio: false,
          animation:{duration:1800,easing:'easeInOutQuart' as any},
          plugins:{legend:{display:false},tooltip:{...tooltipOpts}},
          scales:{...scaleOpts,y:{...scaleOpts.y,min:10000,max:21000}}
        }
      }));
    })();

    // 5. PEAK BAR
    (() => {
      const el = document.getElementById('peakBarChart') as HTMLCanvasElement;
      if (!el) return;
      const ctx = el.getContext('2d') as CanvasRenderingContext2D;
      const labels = Array.from({length:17},(_,i)=>`${String(i).padStart(2,'0')}:00`);
      const data   = [0,0,0,0,500,2000,6000,10000,13000,15000,16500,16000,16500,17000,17500,17500,17000];
      const colors = data.map(v => v > 15000 ? hexA('#c9a84c',0.85) : v > 10000 ? hexA('#c9a84c',0.5) : hexA('#4caf82',0.5));

      charts.push(new Chart(ctx,{
        type:'bar',
        data:{labels,datasets:[{data,backgroundColor:colors,borderWidth:0,borderRadius:2}]},
        options:{
          responsive:true,
          maintainAspectRatio: false,
          animation:{duration:2000,easing:'easeInOutQuart' as any},
          plugins:{legend:{display:false},tooltip:{...tooltipOpts,callbacks:{label:(c: any)=>` ${c.raw.toLocaleString()} MW`}}},
          scales:{...scaleOpts,y:{...scaleOpts.y,min:0,max:19000}}
        }
      }));
    })();

    // 6. DONUT
    (() => {
      const el = document.getElementById('donutChart') as HTMLCanvasElement;
      if (!el) return;
      const ctx = el.getContext('2d') as CanvasRenderingContext2D;
      charts.push(new Chart(ctx,{
        type:'doughnut',
        data:{
          labels:['Solar','Wind','Grid'],
          datasets:[{
            data:[13297,6648,0.5],
            backgroundColor:[hexA('#e8c96a',0.8),hexA('#4caf82',0.75),hexA('#555555',0.3)],
            borderColor:['#e8c96a','#4caf82','#333'],
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
            tooltip:{...tooltipOpts,callbacks:{label:(c: any)=>` ${c.label}: ${c.raw.toLocaleString()} MW`}}
          }
        }
      }));
    })();

    return () => {
        charts.forEach(c => c.destroy());
    };
  }, []);

  return (
    <>
      {HTML_CONTENT_HERE}
    </>
  );
}
"""

html_body = html_body.replace('<span className="demand-val" id="liveVal">14,661 MW</span>', '<span className="demand-val" id="liveVal">{demand.toLocaleString()} MW</span>')

# Handle random unclosed inputs if they exist (though we didn't see any earlier, just in case)
html_body = re.sub(r'(<hr[^>]*)>', r'\1 />', html_body)
html_body = re.sub(r'(<img[^>]*)>', r'\1 />', html_body)

tsx_content = tsx_content.replace('{HTML_CONTENT_HERE}', html_body)

with open(app_tsx_file, 'w', encoding='utf-8') as f:
    f.write(tsx_content)
