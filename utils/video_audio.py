def load_timestamps(path):
    """
    Load a timestamp file where each line is:
        <second> <text>
    Returns a list of dicts: [{"time": int, "text": str}, ...]
    """
    timestamps = []
    try:
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(" ", 1)
                if len(parts) != 2:
                    continue
                time_str, text = parts
                try:
                    time_sec = int(time_str)
                    timestamps.append({"time": time_sec, "text": text})
                except ValueError:
                    continue
    except Exception as e:
        print(f"[ERROR] Could not load timestamps: {e}")
    return timestamps

