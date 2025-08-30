import requests
import json

# --------------------------
# Hard-coded API key
# --------------------------
OPENAI_API_KEY = ""

#OPENAI_API_KEY = "sk-your-api-key-here"  # <-- replace with your real key
API_URL = "https://api.openai.com/v1/chat/completions"

# --------------------------
# Fine-tuned model name
# --------------------------
fine_tuned_model = "ft:gpt-3.5-turbo-0125:personal::C8HLNodZ"

# --------------------------
# Parameters for parody
# --------------------------
song_style = "rock anthem"
parody_object = "rubber chicken"
owner_description = "the main character, overly dramatic"
rival_description = "a sneaky rival with bad taste"
extras_description = "random background characters doing silly dances"

# --------------------------
# Prompt payload
# --------------------------
payload = {
    "model": fine_tuned_model,
    "messages": [
        {
            "role": "system",
            "content": "You are a parody video script writer. Generate creative, absurd, and humorous parody scripts in a structured JSON format."
        },
        {
            "role": "user",
            "content": f"""Generate a full parody song + video script in JSON format. Each section should include scene description, visual/audio effects, cut-scenes/B-roll, and line templates. Each section must reference the previous section visually or thematically.

Parameters:
- Original song style or vibe: {song_style}
- Parody theme / object: {parody_object}
- Tone: neutral / silly / absurd
- Owner description: {owner_description}
- Rival description: {rival_description}
- Extras description: {extras_description}

Sections to include:
1. Opening Scene (0:00 – 0:10)
2. Verse 1 – Bragging (0:10 – 0:25)
3. Verse 2 – Superiority Claim (0:25 – 0:40)
4. Verse 3 – Absurd Uses (0:40 – 1:00)
5. Verse 4 – Mystic Power Fantasy (1:00 – 1:20)
6. Verse 5 – Over-the-Top Royalty Claim (1:20 – 1:40)
7. Comic Breakdown – The Rival (1:40 – 1:55)
8. Outro – Meta Call-to-Action (1:55 – 2:10)

Roles / Characters:
- Owner: {owner_description}
- Rival: {rival_description}
- Extras: {extras_description}

Style Notes:
- Repeat {parody_object} for humor.
- Escalation: Ordinary → Unique → Powerful → Legendary → Childish Breakdown.
- Visual absurdity: Treat {parody_object} as magical, priceless, and world-changing.
- Comedic payoff: Build hype then undercut with petty fighting + meta humor.

Output Format Example:
{{
  "opening_scene": {{"timestamp": "0:00-0:10", "scene_description": "...", "effects": "...", "line_template": "..."}},
  "verse_1": {{}},
  ...
}}"""
        }
    ],
    "temperature": 0.8,
    "max_tokens": 3000
}

# --------------------------
# API request
# --------------------------
response = requests.post(
    API_URL,
    headers={
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    },
    data=json.dumps(payload)
)

# --------------------------
# Handle response
# --------------------------
if response.status_code == 200:
    data = response.json()
    content = data["choices"][0]["message"]["content"]
    print("=== Generated Parody Script ===\n")
    print(content)

    # Save to file
    with open("parody_script.json", "w", encoding="utf-8") as f:
        f.write(content)
    print("\n✅ Saved to parody_script.json")
else:
    print("❌ Error:", response.status_code, response.text)
