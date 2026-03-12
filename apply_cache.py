import os
import glob

routes_dir = r"c:\Users\satwi\Downloads\final_energy_forecast\final_energy_forecast\smartgrid_ai\app\api\routes"
ws_file = r"c:\Users\satwi\Downloads\final_energy_forecast\final_energy_forecast\smartgrid_ai\app\api\websocket.py"
files = glob.glob(os.path.join(routes_dir, "*.py")) + [ws_file]

for f in files:
    with open(f, 'r', encoding='utf-8') as fr:
        content = fr.read()
    
    if "pd.read_csv" in content:
        # Add import if missing
        if "get_cached_dataframe" not in content:
            content = "from app.core.data_cache import get_cached_dataframe\n" + content
            
        # Replace the literal read_csv calls
        content = content.replace(
            "pd.read_csv(FORECAST_DATASET_PATH, index_col=0, parse_dates=True)",
            "get_cached_dataframe(FORECAST_DATASET_PATH)"
        )
        content = content.replace(
            "pd.read_csv(ANOMALY_DATASET_PATH, index_col=0, parse_dates=True)",
            "get_cached_dataframe(ANOMALY_DATASET_PATH)"
        )
        
        with open(f, 'w', encoding='utf-8') as fw:
            fw.write(content)
        print(f"Updated {f}")
