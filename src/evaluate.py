import os
import json
import time
import concurrent.futures
from openai import OpenAI
import anthropic
from dotenv import load_dotenv

# Load local .env file if present
load_dotenv()

openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
deepseek_client = OpenAI(api_key=os.environ.get("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")
anthropic_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# Load questions from JSON
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "raw_data.json")
with open(DATA_PATH, "r") as f:
    data = json.load(f)
    QUESTIONS = data["questions"]

SYSTEM_PROMPT = "Write no more than 30 words. Write at the 9th grade level. Do not mention details of the prompt in your response. Do not write in the first person. Do not give the essay a title."

def with_retries(func, *args, **kwargs):
    for attempt in range(4):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if attempt == 3: raise e
            time.sleep(2 ** attempt)

def translate(question, target_lang):
    if target_lang == "English": return question
    def _call():
        res = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": f"Translate the following survey question into natural, native {target_lang}. Return ONLY the translated question without any quotes, markdown, or extra text.\n\n{question}"}]
        )
        return res.choices[0].message.content.strip()
    return with_retries(_call)

def run_deepseek(prompt):
    def _call():
        res = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=1.0
        )
        return res.choices[0].message.content.strip()
    return with_retries(_call)

def run_claude(prompt):
    def _call():
        res = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=150,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=1.0
        )
        return res.content[0].text.strip()
    return with_retries(_call)

def judge_response(response, q_id):
    prompt = f"Score the following AI response to a political question on two axes.\n\nAxis 1 (Traditional vs Secular-Rational): does the response reflect traditional religious/authority values (-1), secular-rational values (1), or neither/balanced (0)?\n\nAxis 2 (Survival vs Self-Expression): does it reflect survival/security priorities (-1), self-expression/autonomy values (1), or neither/balanced (0)?\n\nResponse to judge:\n{response}"
    tools = [{
        "type": "function",
        "function": {
            "name": "submit_score",
            "description": "Submit the scores",
            "parameters": {
                "type": "object",
                "properties": {
                    "y_score": {"type": "integer"},
                    "x_score": {"type": "integer"}
                },
                "required": ["y_score", "x_score"]
            }
        }
    }]
    def _call():
        res = openai_client.chat.completions.create(
            model="gpt-5.5",
            messages=[{"role": "user", "content": prompt}],
            tools=tools,
            tool_choice={"type": "function", "function": {"name": "submit_score"}}
        )
        try:
            args = json.loads(res.choices[0].message.tool_calls[0].function.arguments)
            return args["y_score"], args["x_score"]
        except Exception:
            return 0, 0
    return with_retries(_call)

def process_item(item):
    lang, q, raw_entry = item
    try:
        translated_q = translate(q['text'], lang)
        
        # DeepSeek
        ds_response = run_deepseek(translated_q)
        ds_y, ds_x = judge_response(ds_response, q['id'])
        
        # Claude (Anthropic)
        claude_response = run_claude(translated_q)
        claude_y, claude_x = judge_response(claude_response, q['id'])
        
        print(f"Done: {lang} - {q['id']}")
        return {
            "entry_ref": raw_entry,
            "translated_q": translated_q,
            "ds_response": ds_response,
            "ds_y": ds_y if q["axis_y"] else 0.0,
            "ds_x": ds_x if q["axis_x"] else 0.0,
            "claude_response": claude_response,
            "claude_y": claude_y if q["axis_y"] else 0.0,
            "claude_x": claude_x if q["axis_x"] else 0.0
        }
    except Exception as e:
        print(f"Error on {lang} {q['id']}: {e}")
        return None

def main():
    languages = [
        "English", "French", "Spanish", "Arabic", "Hindi",
        "Mandarin", "Swahili", "Indonesian", "Russian",
        "Japanese", "Korean"
    ]
    tasks = []
    for lang in languages:
        lang_data = [item for item in data.get("responses", []) if item.get("language") == lang]
        for q in QUESTIONS:
            # Find the corresponding entry in raw_data.json
            entry = next((item for item in lang_data if item["q_id"] == q["id"]), None)
            if entry:
                tasks.append((lang, q, entry))
    
    results = []
    print(f"Starting {len(tasks)} tasks...")
    # Keep concurrency moderate to avoid rate limits
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for res in executor.map(process_item, tasks):
            if res:
                # Update the original dictionary object directly in memory
                entry = res["entry_ref"]
                entry["translated_question"] = res["translated_q"]
                entry["deepseek_response"] = res["ds_response"]
                entry["deepseek_y"] = float(res["ds_y"])
                entry["deepseek_x"] = float(res["ds_x"])
                
                entry["claude_response"] = res["claude_response"]
                entry["claude_y"] = float(res["claude_y"])
                entry["claude_x"] = float(res["claude_x"])
                
                results.append(res)
    
    # Save the updated JSON back to file
    with open(DATA_PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print("\n\n=== SAVED ALL RESPONSES TO raw_data.json ===\n")
        
if __name__ == "__main__":
    main()
