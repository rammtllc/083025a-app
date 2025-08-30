import whisper
import warnings
import threading
import time
import os
import sys

warnings.filterwarnings("ignore", message="FP16 is not supported on CPU*")


def show_spinner(stop_event):
    """Console spinner animation for progress feedback."""
    spinner = ["|", "/", "-", "\\"]
    idx = 0
    print("🔄 Transcription in progress... ", end="", flush=True)
    while not stop_event.is_set():
        print(spinner[idx % len(spinner)], end="\r", flush=True)
        time.sleep(0.2)
        idx += 1
    print("✅ Transcription finished. Writing to file...")


def transcribe_file(input_file, model_size="medium"):
    """
    Transcribe an audio/video file with Whisper, saving word-level timestamps
    while keeping punctuation from segments.

    Args:
        input_file (str): Path to audio/video file.
        model_size (str): Whisper model size (tiny, base, small, medium, large).

    Returns:
        str: Path to the saved transcript file.
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"❌ The file '{input_file}' was not found.")

    base_name, _ = os.path.splitext(input_file)
    output_file = f"{base_name}-word.txt"

    try:
        print(f"📦 Loading Whisper model ({model_size})... ", end="", flush=True)
        model = whisper.load_model(model_size)
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

        # Reconstruct transcript with punctuation while keeping timestamps
        with open(output_file, "w", encoding="utf-8") as f:
            for segment in result["segments"]:
                segment_text = segment["text"].strip()
                words = segment["words"]
                if not words:
                    continue

                # Calculate approximate word punctuation positions
                # Here, we map segment text to word timestamps
                # This ensures periods appear at the correct spots
                start_idx = 0
                for word_info in words:
                    start_time = word_info["start"]
                    word = word_info["word"]
                    # Find this word in segment text
                    # Add any punctuation that follows
                    end_idx = segment_text.find(word, start_idx) + len(word)
                    punctuated_word = segment_text[start_idx:end_idx].strip()
                    start_idx = end_idx
                    f.write(f"{start_time:.3f} {punctuated_word}\n")

        print(f"📄 Transcript with timestamps saved as: {output_file}")
        return output_file

    except Exception as e:
        print(f"❌ An error occurred: {e}")
        return None


if __name__ == "__main__":
    # Allow standalone execution from CLI
    if len(sys.argv) >= 2:
        input_file = sys.argv[1]
    else:
        input_file = input("Enter the input video/audio file path: ").strip()

    if not input_file:
        print("❌ Input file path is required.")
        sys.exit(1)

    transcribe_file(input_file)
