import subprocess
import os

def separate_audio(input_file):
    """
    Uses Demucs to separate stems from an audio file.
    Output will be saved in the same folder as the input file.
    Requires Demucs installed: pip install demucs
    """
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found.")
        return

    output_dir = os.path.dirname(os.path.abspath(input_file))  # same folder as input

    try:
        # Run Demucs command
        subprocess.run([
            "demucs",
            "--two-stems", "vocals",  # Only keep vocals and accompaniment
            "-o", output_dir,
            input_file
        ], check=True)

        print(f"✅ Separation complete! Check the folder: '{output_dir}'")

    except subprocess.CalledProcessError as e:
        print("❌ Error running Demucs:", e)
