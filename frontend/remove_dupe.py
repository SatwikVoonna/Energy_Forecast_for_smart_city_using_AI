import os

path = r'c:\Users\satwi\Downloads\final_energy_forecast\final_energy_forecast\smartgrid_ai\frontend\src\pages\Dashboard.tsx'

with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# We know the duplicate starts with:
#   <div className="divider"></div>
# 
#   {/* ══ ALERTS ══ */}

start_idx = text.rfind('<div className="divider"></div>\n\n  {/* ══ ALERTS ══ */}')
if start_idx != -1 and text.find('══ FOOTER ══', start_idx) != -1:
    end_idx = text.find('  {/* ══ FOOTER ══ */}', start_idx)
    
    text = text[:start_idx] + "\n" + text[end_idx:]
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print("SUCCESS")
else:
    print("FAILED TO FIND")
