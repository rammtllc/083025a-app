from openai import OpenAI
import time
import json
import os
import requests

# ---------- Hard-coded API key ----------
OPENAI_API_KEY = ""  # <-- Replace with your key

API_BASE = "https://api.openai.com/v1"
HEADERS = {"Authorization": f"Bearer {OPENAI_API_KEY}"}

# ---------- 1) Validate JSONL ----------
def validate_jsonl(path):
    valid_roles = {"system", "user", "assistant"}
    errors = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                errors.append(f"Line {i}: JSONDecodeError: {e}")
                continue
            if "messages" not in obj or not isinstance(obj["messages"], list):
                errors.append(f"Line {i}: missing or invalid 'messages' array")
                continue
            for m in obj["messages"]:
                role = m.get("role")
                if role not in valid_roles:
                    errors.append(f"Line {i}: invalid role '{role}'")
                content = m.get("content")
                if not isinstance(content, str):
                    errors.append(f"Line {i}: invalid content type (must be str)")
    if errors:
        print("❌ Validation errors:")
        for e in errors[:200]:
            print(" -", e)
        return False
    print("✅ Validation passed.")
    return True

# ---------- 2) Upload file ----------
def upload_file(path):
    url = f"{API_BASE}/files"
    with open(path, "rb") as f:
        files = {"file": (os.path.basename(path), f, "application/jsonl")}
        data = {"purpose": "fine-tune"}
        resp = requests.post(url, headers=HEADERS, data=data, files=files)
    resp.raise_for_status()
    return resp.json()  # contains 'id' field

# ---------- 3) Create fine-tuning job ----------
def create_fine_tune_job(file_id, model="gpt-3.5-turbo"):
    url = f"{API_BASE}/fine_tuning/jobs"
    payload = {"training_file": file_id, "model": model}
    resp = requests.post(url, headers={**HEADERS, "Content-Type": "application/json"}, json=payload)
    resp.raise_for_status()
    return resp.json()  # contains 'id' for the job

# ---------- 4) Poll job ----------
def poll_job(job_id, poll_interval=10):
    url = f"{API_BASE}/fine_tuning/jobs/{job_id}"
    print(f"Polling job {job_id} every {poll_interval}s...")
    while True:
        resp = requests.get(url, headers=HEADERS)
        resp.raise_for_status()
        info = resp.json()
        status = info.get("status")
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] status: {status}")
        if status in ("succeeded", "failed"):
            return info
        time.sleep(poll_interval)

# ---------- 5) Test the fine-tuned model ----------
def test_fine_tuned_model(model_name, test_prompt="Write a short funny parody line."):
    url = f"{API_BASE}/chat/completions"
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": test_prompt}],
        "max_tokens": 200,
        "temperature": 0.7,
    }
    resp = requests.post(url, headers={**HEADERS, "Content-Type": "application/json"}, json=payload)
    resp.raise_for_status()
    return resp.json()

# ---------- main ----------
def main():
    DATA_PATH = input("Enter the path to your JSONL file for fine-tuning: ").strip()
    if not DATA_PATH or not os.path.exists(DATA_PATH):
        print(f"❌ File not found: {DATA_PATH}")
        return

    # Validate JSONL
    if not validate_jsonl(DATA_PATH):
        print("Fix JSONL issues and retry.")
        return

    # Upload file
    print("Uploading file...")
    upload_resp = upload_file(DATA_PATH)
    file_id = upload_resp.get("id")
    print("Uploaded file id:", file_id)

    # Create fine-tune job
    print("Creating fine-tune job...")
    job_resp = create_fine_tune_job(file_id, model="gpt-3.5-turbo")
    job_id = job_resp.get("id")
    print("Fine-tune job id:", job_id)

    # Poll job
    job_info = poll_job(job_id, poll_interval=15)

    if job_info.get("status") == "succeeded":
        fine_tuned_model = job_info.get("fine_tuned_model") or job_info.get("result", {}).get("fine_tuned_model")
        if not fine_tuned_model:
            print("Job succeeded but fine_tuned_model not found. Full job info:")
            print(json.dumps(job_info, indent=2))
            return
        print("✅ Fine-tune succeeded. Model name:", fine_tuned_model)
        print("Running quick test...")
        test = test_fine_tuned_model(fine_tuned_model)
        choice = test["choices"][0]
        content = choice["message"]["content"] if "message" in choice else choice.get("text")
        print("\n--- Test output ---\n", content)
    else:
        print("Fine-tune failed. Full job info:")
        print(json.dumps(job_info, indent=2))

if __name__ == "__main__":
    main()
