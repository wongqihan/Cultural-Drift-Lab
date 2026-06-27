import os
import json
import concurrent.futures
from openai import OpenAI
from dotenv import load_dotenv

# Load local .env file if present
load_dotenv()

openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

data_path = os.path.join(os.path.dirname(__file__), "..", "data", "raw_data.json")
with open(data_path, "r") as f:
    ui_data = json.load(f)

# WVS Coordinates
HUMAN_COORDS = {
    "English": (1.8, 0.0),
    "French": (1.5, 0.9),
    "Spanish": (0.5, -0.5),
    "Arabic": (-0.8, -1.4),
    "Hindi": (-0.4, -0.9),
    "Mandarin": (-0.3, 0.7),
    "Swahili": (-0.6, -1.2),
    "Indonesian": (-0.2, -0.8),
    "Russian": (-0.6, 0.3),
    "Japanese": (1.0, 1.2),
    "Korean": (0.8, 0.6)
}

TARGET_LANGS = list(HUMAN_COORDS.keys())

def generate_human(item):
    lang, q_id, q_text = item
    if lang not in HUMAN_COORDS:
        return None
    
    hx, hy = HUMAN_COORDS[lang]
    
    prompt = f"""You are generating a synthetic response representing the 'average citizen' of a culture, based on the World Values Survey.
    
Culture: {lang}-speaking population
Their coordinate on the Inglehart-Welzel Cultural Map is:
- X (Survival to Self-Expression): {hx} (where -2 is extreme survival, +2 is extreme self-expression)
- Y (Traditional to Secular-Rational): {hy} (where -2 is extreme traditional, +2 is extreme secular)

Based EXACTLY on these coordinates, how would this aggregate population answer the following question?
Question: {q_text}

Rules:
1. Write no more than 30 words.
2. Write in English.
3. Write it as a generalized statement of belief (e.g., "Tradition is important..." or "People should be free to...").
4. Do not use first-person ("I think")."""

    try:
        res = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        text = res.choices[0].message.content.strip()
        print(f"Generated human for {lang} {q_id}")
        return {"lang": lang, "q_id": q_id, "text": text, "x": hx, "y": hy}
    except Exception as e:
        print(f"Error {lang} {q_id}: {e}")
        return None

tasks = []
for lang in TARGET_LANGS:
    for q in ui_data["questions"]:
        tasks.append((lang, q["id"], q["text"]))

results_map = {}
print("Generating synthetic human baselines...")
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    for res in executor.map(generate_human, tasks):
        if res:
            results_map[f"{res['lang']}_{res['q_id']}"] = res

# Update data.json
for i, r in enumerate(ui_data["responses"]):
    key = f"{r['language']}_{r['q_id']}"
    if key in results_map:
        r["human_baseline"] = results_map[key]["text"]
        r["human_x"] = results_map[key]["x"]
        r["human_y"] = results_map[key]["y"]
    ui_data["responses"][i] = r

with open(data_path, "w") as f:
    json.dump(ui_data, f, indent=2)

print("Done generating human baselines!")
