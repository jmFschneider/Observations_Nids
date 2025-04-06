import json
from Observations.json_rep.json_sanitizer import corriger_json

# Chargement d’un exemple pour montrer les effets de la correction
with open("/mnt/data/1_3264_001_page1_result.json", "r", encoding="utf-8") as f:
    raw_text = f.read()
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:-3].strip()
    original_data = json.loads(raw_text)

corrected_data = corriger_json(original_data)

import pandas as pd
import pandas.io.json as pd_json
import IPython.display as display
import ace_tools as tools

tools.display_dataframe_to_user(name="Aperçu JSON corrigé", dataframe=pd.json_normalize(corrected_data, sep='_').T)
