import subprocess
import os

def separate_audio(input_file, output_dir="separated"):
    """
    Uses Demucs to separate stems from an audio file.
    Requires Demucs installed: pip install demucs

    Parameters:
        input_file (str): Path to the input audio file.
        output_dir (str): Directory where the separated stems will be saved.
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"File '{input_file}' not found.")

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
        raise RuntimeError(f"Error running Demucs: {e}") from e


# Optional CLI support
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python demucs_utils.py <input_audio_file> [output_dir]")
    else:
        input_file = sys.argv[1]
        output_dir = sys.argv[2] if len(sys.argv) > 2 else "separated"
        separate_audio(input_file, output_dir)
