import threading
import pygame
import os
import json
from utils import media_and_assets as utils
from utils.transcriber import transcribe_file
from utils.transcript_capitals_utils import parse_transcript1
from utils.transcript_sentences_utils import parse_transcript2
from utils.demucs_utils import separate_audio

# -----------------------------
# Background Tasks
# -----------------------------
def conversion_task(input_file, output_mp4, output_mp3, done_flag):
    print("⚙️ Starting conversion...")
    try:
        utils.convert_mkv_to_mp4_and_mp3(input_file, output_mp4, output_mp3)
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
    done_flag["conversion_done"] = True
    print("✅ Conversion finished.")

def transcription_task(output_mp3, done_flag, word_file_holder):
    if output_mp3:
        print("📝 Starting transcription...")
        try:
            transcribe_file(output_mp3)
            word_file_holder["word_file"] = output_mp3.rsplit(".", 1)[0] + "-word.txt"
        except Exception as e:
            print(f"❌ Transcription failed: {e}")
    else:
        print("⚠️ No MP3 file generated, skipping transcription.")
    done_flag["transcription_done"] = True
    print("✅ Transcription finished.")

def separate_audio_task(output_mp3, done_flag, separated_files_holder):
    if output_mp3 and os.path.exists(output_mp3):
        print("🎚️ Starting audio separation (Demucs)...")
        try:
            separate_audio(output_mp3)
            base_name = os.path.splitext(os.path.basename(output_mp3))[0]
            sep_dir = os.path.join("separated", "htdemucs", base_name)

            vocals_file = None
            no_audio_file = None

            if os.path.isdir(sep_dir):
                for fname in os.listdir(sep_dir):
                    fpath = os.path.join(sep_dir, fname)
                    if "vocals" in fname.lower():
                        vocals_file = fpath
                    elif any(tag in fname.lower() for tag in ["other", "accompaniment", "no_audio", "instrumental"]):
                        no_audio_file = fpath

            separated_files_holder["vocals"] = vocals_file
            separated_files_holder["no_audio"] = no_audio_file

            print(f"✅ Demucs vocals: {vocals_file}")
            print(f"✅ Demucs no-audio: {no_audio_file}")

        except Exception as e:
            print(f"❌ Audio separation failed: {e}")
    else:
        print("⚠️ MP3 file not found, skipping audio separation.")
    done_flag["demucs_done"] = True
    print("✅ Audio separation finished.")

# -----------------------------
# Main Program
# -----------------------------
def main():
    done_flag = {
        "conversion_done": False,
        "transcription_done": False,
        "demucs_done": False
    }
    status_message = ["Waiting for input..."]
    word_file_holder = {"word_file": None}
    separated_files_holder = {"vocals": None, "no_audio": None}
    transcripts = {"word": None, "sentence": None, "capitals": None}

    # Pygame setup
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Gear Converter + Transcriber")
    font = pygame.font.Font(None, 32)
    large_gear = utils.load_large_gear()
    small_gear = utils.load_small_gear()

    if large_gear is None or small_gear is None:
        print("❌ Failed to load gear images.")
        pygame.quit()
        return

    angle_large = 0
    angle_small = 0
    clock = pygame.time.Clock()

    # User input
    input_data = {}

    def get_user_input():
        input_file = input("Enter path to .mkv file: ").strip()
        output_mp4 = input("Enter output MP4 filename (or leave blank): ").strip() or None
        output_mp3 = input("Enter output MP3 filename (or leave blank): ").strip() or None
        if not output_mp3:
            output_mp3 = input_file.rsplit(".", 1)[0] + ".mp3"

        input_data.update({
            "input_file": input_file,
            "output_mp4": output_mp4,
            "output_mp3": output_mp3
        })

        status_message[0] = "Converting..."
        threading.Thread(
            target=conversion_task,
            args=(input_file, output_mp4, output_mp3, done_flag),
            daemon=True
        ).start()

    threading.Thread(target=get_user_input, daemon=True).start()

    # Main loop
    transcription_started = False
    demucs_started = False
    transcripts_generated = False
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                for k in done_flag:
                    done_flag[k] = True

        # Spin gears
        angle_large = (angle_large + 1) % 360
        angle_small = (angle_small - 3) % 360

        rotated_large = pygame.transform.rotate(large_gear, angle_large)
        rotated_small = pygame.transform.rotate(small_gear, angle_small)

        rect_large = rotated_large.get_rect(center=(200, 300))
        rect_small = rotated_small.get_rect(center=(500, 300))

        screen.fill((20, 20, 20))
        screen.blit(rotated_large, rect_large)
        screen.blit(rotated_small, rect_small)

        # Render status
        text_surface = font.render(status_message[0], True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(400, 100))
        screen.blit(text_surface, text_rect)

        pygame.display.flip()
        clock.tick(60)

        # Start transcription after conversion
        if done_flag["conversion_done"] and not transcription_started and "output_mp3" in input_data:
            status_message[0] = "Transcribing..."
            threading.Thread(
                target=transcription_task,
                args=(input_data["output_mp3"], done_flag, word_file_holder),
                daemon=True
            ).start()
            transcription_started = True

        # Generate transcripts once after transcription
        if done_flag["transcription_done"] and word_file_holder["word_file"] and not transcripts_generated:
            base_name = word_file_holder["word_file"].rsplit("-word.txt", 1)[0]

            word_file = word_file_holder["word_file"]
            capital_file = f"{base_name}-capitals.txt"
            parse_transcript1(word_file, capital_file)

            sentence_file = f"{base_name}-sentence.txt"
            parse_transcript2(word_file, sentence_file)

            print(f"✅ Word transcript: {word_file}")
            print(f"✅ Capital transcript: {capital_file}")
            print(f"✅ Sentence transcript: {sentence_file}")

            transcripts.update({
                "word": word_file,
                "capitals": capital_file,
                "sentence": sentence_file
            })
            transcripts_generated = True

        # Start Demucs after transcription
        if done_flag["transcription_done"] and not demucs_started and "output_mp3" in input_data:
            status_message[0] = "Separating audio..."
            threading.Thread(
                target=separate_audio_task,
                args=(input_data["output_mp3"], done_flag, separated_files_holder),
                daemon=True
            ).start()
            demucs_started = True

        # Stop loop when all tasks finish
        if done_flag["conversion_done"] and done_flag["transcription_done"] and done_flag["demucs_done"]:
            status_message[0] = "All tasks done!"
            pygame.time.delay(2000)
            running = False

    pygame.quit()
    print("🎉 All tasks completed! Gears stopped.")

    # -----------------------------
    # Write JSON Config
    # -----------------------------
    config = {
        "font_name": os.path.join(os.path.dirname(__file__), "LuckiestGuy-Regular.ttf"),
        "font_size": 24,
        "show_timestamp": True,
        "record_video": False,
        "timestamp_mode": "word",
        "timestamps_file_word": transcripts["word"],
        "timestamps_file_sentence": transcripts["sentence"],
        "timestamps_file_capitals": transcripts["capitals"],
        "event_schedule_path": os.path.join(os.path.dirname(__file__), "event_schedule.json"),
        "voiceover_path": input_data.get("output_mp3"),
        "vocals_file": separated_files_holder["vocals"],
        "no_audio_file": separated_files_holder["no_audio"]
    }

    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"📝 Config saved to {config_path}")

if __name__ == "__main__":
    main()
