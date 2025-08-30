import os

# Configuration
input_file = "TkiT1SLwxMg.mp3_fine_tune_data.jsonl"
output_folder = "jsonl"
max_lines_per_file = 100  # maximum lines per chunk/file

# Create output folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

chunk_start = 0
current_chunk_lines = []

def write_chunk(start_idx, lines):
    end_idx = start_idx + len(lines) - 1
    output_file = os.path.join(
        output_folder,
        f"fine_tune_data-{start_idx:04d}-{end_idx:04d}.jsonl"
    )
    with open(output_file, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"Created {output_file} with lines {start_idx}-{end_idx}")

with open(input_file, "r", encoding="utf-8") as f:
    for line_number, line in enumerate(f):
        current_chunk_lines.append(line)

        # If chunk reaches max size, write it to file
        if len(current_chunk_lines) >= max_lines_per_file:
            write_chunk(chunk_start, current_chunk_lines)
            chunk_start += max_lines_per_file
            current_chunk_lines = []

# Write any remaining lines as the last chunk
if current_chunk_lines:
    write_chunk(chunk_start, current_chunk_lines)

print("All chunks created successfully.")
