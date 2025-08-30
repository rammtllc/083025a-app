import whisper
import warnings
import threading
import time
import os
import sys

warnings.filterwarnings("ignore", message="FP16 is not supported on CPU*")

# -----------------------------
# Get input file and generate output file
# -----------------------------
if len(sys.argv) >= 2:
    input_file = sys.argv[1]
else:
    input_file = input("Enter the input video/audio file path: ").strip()

if not input_file:
    print("❌ Input file path is required.")
    sys.exit(1)

if not os.path.exists(input_file):
    raise FileNotFoundError(f"❌ The file '{input_file}' was not found.")

# Generate output file name based on input file
base_name, _ = os.path.splitext(input_file)
output_file = f"{base_name}-word.txt"

# -----------------------------
# Spinner animation
# -----------------------------
def show_spinner(stop_event):
    spinner = ["|", "/", "-", "\\"]
    idx = 0
    print("🔄 Transcription in progress... ", end="", flush=True)
    while not stop_event.is_set():
        print(spinner[idx % len(spinner)], end="\r", flush=True)
        time.sleep(0.2)
        idx += 1
    print("✅ Transcription finished. Writing to file...")

# -----------------------------
# Run Whisper transcription
# -----------------------------
try:
    print(f"📦 Loading Whisper model... ", end="", flush=True)
    model = whisper.load_model("medium")
    print("✅ Done")

    # Start spinner in background
    stop_event = threading.Event()
    spinner_thread = threading.Thread(target=show_spinner, args=(stop_event,))
    spinner_thread.start()

    # Perform transcription with word timestamps
    result = model.transcribe(input_file, word_timestamps=True)

    # Stop spinner
    stop_event.set()
    spinner_thread.join()

    # Save timestamps and words to file
    with open(output_file, "w", encoding="utf-8") as f:
        for segment in result["segments"]:
            for word_info in segment["words"]:
                start = word_info["start"]
                word = word_info["word"]
                f.write(f"{start:.3f} {word}\n")

    print(f"📄 Transcript with timestamps saved as: {output_file}")

except Exception as e:
    print(f"❌ An error occurred: {e}")
