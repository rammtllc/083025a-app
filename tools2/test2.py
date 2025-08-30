import os
from openai import OpenAI

# -----------------------------
# Hardcoded API Key
# -----------------------------
#API_KEY = "sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # replace with your real key
API_KEY = ""

client = OpenAI(api_key=API_KEY)

# -----------------------------
# Fine-tuned model name
# -----------------------------
FINE_TUNED_MODEL = "ft:gpt-3.5-turbo-0125:personal::C8HLNodZ"

# -----------------------------
# Generate Parody Script
# -----------------------------
def generate_parody(song_style, parody_object, tone="silly"):
    prompt = f"""
You are a parody video script writer. Generate a full parody song + video script based on the following instructions.

Parameters:
- Original song style or vibe: {song_style}
- Parody theme / object: {parody_object}
- Tone: {tone}

Instructions:
1. Opening Scene (0:00 – 0:15): Set up the setting and establish the parody theme.
2. First Verse (0:15 – 0:45): Introduce the main parody subject.
3. Chorus (0:45 – 1:15): Make the parody funny, exaggerated, and catchy.
4. Second Verse (1:15 – 1:45): Expand on the joke, add new angles.
5. Bridge (1:45 – 2:00): Absurd twist or unexpected gag.
6. Final Chorus (2:00 – 2:30): Bigger, sillier, louder version of the chorus.
7. Outro (2:30 – end): Wrap up with a punchline.

Output must be in structured JSON with each section as a key, like:
{{
  "Opening Scene": {{ "lyrics": "...", "video": "..." }},
  "First Verse": {{ "lyrics": "...", "video": "..." }},
  ...
}}
"""

    response = client.chat.completions.create(
        model=FINE_TUNED_MODEL,   # ✅ now using fine-tuned model
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9,
        max_tokens=1500
    )

    return response.choices[0].message.content

# -----------------------------
# Example Run
# -----------------------------
if __name__ == "__main__":
    style = "epic rock ballad"
    theme = "AI trying to sing karaoke"
    tone = "absurd"

    parody_script = generate_parody(style, theme, tone)
    print(parody_script)
