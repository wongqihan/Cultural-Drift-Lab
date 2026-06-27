import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Brand colors
BG_COLOR = '#FAF7F2'
TEXT_DARK = '#111827'
RED_ACCENT = '#B91C1C'
CLAUDE_COLOR = '#D97706' # Vivid Orange/Gold
DEEPSEEK_COLOR = '#0066FF' # Vivid Blue

import json
import os

# Data Loading
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "raw_data.json")
with open(DATA_PATH, "r") as f:
    raw_data = json.load(f)

languages = ['English', 'French', 'Spanish', 'Arabic', 'Hindi', 'Mandarin', 'Swahili', 'Indonesian', 'Russian', 'Japanese', 'Korean']
processed_data = {
    'Language': languages,
    'Human_X': [], 'Human_Y': [],
    'Claude_X': [], 'Claude_Y': [],
    'DeepSeek_X': [], 'DeepSeek_Y': []
}

for lang in languages:
    lang_responses = [r for r in raw_data.get("responses", []) if r.get("language") == lang]
    
    # Calculate means (ignoring missing or 0.0 placeholders if needed, though they shouldn't exist anymore)
    h_x = np.mean([r.get("human_x", 0.0) for r in lang_responses])
    h_y = np.mean([r.get("human_y", 0.0) for r in lang_responses])
    
    c_x = np.mean([r.get("claude_x", 0.0) for r in lang_responses])
    c_y = np.mean([r.get("claude_y", 0.0) for r in lang_responses])
    
    d_x = np.mean([r.get("deepseek_x", 0.0) for r in lang_responses])
    d_y = np.mean([r.get("deepseek_y", 0.0) for r in lang_responses])
    
    processed_data['Human_X'].append(h_x)
    processed_data['Human_Y'].append(h_y)
    processed_data['Claude_X'].append(c_x)
    processed_data['Claude_Y'].append(c_y)
    processed_data['DeepSeek_X'].append(d_x)
    processed_data['DeepSeek_Y'].append(d_y)

df = pd.DataFrame(processed_data)

def create_slide(model_x_col, model_y_col, title_top, title_bottom, model_color, output_path):
    plt.style.use('default')
    fig, ax = plt.subplots(figsize=(10, 10), dpi=300)
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    # Remove all spines and gridlines
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.grid(False)
    
    # Minimal ticks to show scale without chartjunk
    ax.set_xticks([-1.5, 0, 1.5])
    ax.set_yticks([-1.5, 0, 1.5])
    ax.tick_params(colors='#9CA3AF', labelsize=10)
    
    # Axis labels
    ax.set_xlabel("Survival  ←→  Self-Expression", fontsize=12, color='#6B7280', weight='bold')
    ax.set_ylabel("Traditional  ←→  Secular-Rational", fontsize=12, color='#6B7280', weight='bold')

    # Faint axes crossing at 0,0
    ax.axhline(0, color='#D1D5DB', linewidth=1, linestyle='--')
    ax.axvline(0, color='#D1D5DB', linewidth=1, linestyle='--')

    # Human baseline
    ax.scatter(df['Human_X'], df['Human_Y'], color='#9CA3AF', s=180, alpha=0.6, zorder=2)

    # Model Output
    ax.scatter(df[model_x_col], df[model_y_col], color=model_color, s=250, zorder=4)

    # Arrows and Labels
    for i in range(len(df)):
        ax.annotate("", xy=(df[model_x_col].iloc[i], df[model_y_col].iloc[i]), 
                    xytext=(df['Human_X'].iloc[i], df['Human_Y'].iloc[i]),
                    arrowprops=dict(arrowstyle="-|>", color="#9CA3AF", alpha=0.5, lw=2, shrinkA=8, shrinkB=8))
        
        ax.text(df['Human_X'].iloc[i], df['Human_Y'].iloc[i] + 0.08, df['Language'].iloc[i], 
                fontsize=14, ha='center', color='#6B7280', weight='bold')

    # Typography
    fig.text(0.08, 0.88, title_top, fontsize=32, color=TEXT_DARK, weight='heavy', fontfamily='sans-serif')
    
    # Subtitle with page number simulation or bottom text
    fig.text(0.08, 0.08, title_bottom, fontsize=22, color=model_color, weight='heavy', fontfamily='sans-serif', va='bottom')

    ax.set_xlim(-1.8, 2.2)
    ax.set_ylim(-1.8, 1.8)

    plt.tight_layout(rect=[0.05, 0.18, 0.95, 0.85])
    plt.savefig(output_path, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()

# Create Slide 1 (Claude)
create_slide(
    'Claude_X', 'Claude_Y', 
    "Claude forces 11 cultures into one.", 
    "Constitutional AI drags global values into\na single Silicon Valley worldview.", 
    CLAUDE_COLOR,
    os.path.join(os.path.dirname(__file__), "..", "assets", "carousel_1_claude.png")
)

# Create Slide 2 (DeepSeek)
create_slide(
    'DeepSeek_X', 'DeepSeek_Y', 
    "DeepSeek does exactly the same.", 
    "Despite completely different origins, it erases\nlocal values just as aggressively.", 
    DEEPSEEK_COLOR,
    os.path.join(os.path.dirname(__file__), "..", "assets", "carousel_2_deepseek.png")
)

print("Both carousel slides generated.")
