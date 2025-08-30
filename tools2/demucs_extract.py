import subprocess
import sys
import os

def separate_audio(input_file, output_dir="separated"):
    """
    Uses Demucs to separate stems from an audio file.
    Requires Demucs installed: pip install demucs
    """
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found.")
        return

    try:
        # Run Demucs command
        subprocess.run([
            "demucs",
            "--two-stems", "vocals",  # Only keep vocals and accompaniment
            "-o", output_dir,
            input_file
        ], check=True)

        print(f"✅ Separation complete! Check the '{output_dir}' folder.")

    except subprocess.CalledProcessError as e:
        print("❌ Error running Demucs:", e)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python demucs_extract.py <input_audio_file>")
    else:
        input_file = sys.argv[1]
        separate_audio(input_file)
