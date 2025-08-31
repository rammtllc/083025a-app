import cv2
import hashlib
import os

# Path to your video file
video_path = "mouth.mov"

# Output folder for frames
output_folder = "mouth"
os.makedirs(output_folder, exist_ok=True)

# Open the video file
cap = cv2.VideoCapture(video_path)

# Set to store hashes of unique frames
unique_hashes = set()
frame_count = 0
saved_count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Convert frame to bytes and hash it
    frame_bytes = cv2.imencode(".png", frame)[1].tobytes()
    frame_hash = hashlib.md5(frame_bytes).hexdigest()

    # Save frame if it's unique
    if frame_hash not in unique_hashes:
        unique_hashes.add(frame_hash)
        saved_count += 1
        frame_filename = os.path.join(output_folder, f"mouth_{saved_count:05d}.png")
        cv2.imwrite(frame_filename, frame)

    frame_count += 1

cap.release()
print(f"Processed {frame_count} frames, saved {saved_count} unique frames to '{output_folder}'")
