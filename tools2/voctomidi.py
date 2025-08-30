#!/usr/bin/env python3
"""
vocal_to_midi.py

Analyze a solo vocal track and export a monophonic MIDI melody inferred from it.

Usage:
  python vocal_to_midi.py input_audio.(wav|mp3|m4a|flac) output.mid \
      --sr 22050 --frame_hop_ms 10 --min_note_ms 60 --min_silence_ms 40 \
      --pitch_conf 0.8 --quantize 0 --instrument 54

Notes:
- Uses librosa.pyin (monophonic pitch tracker) to estimate F0 over time.
- Segments notes when pitch changes enough or there is unvoiced/silence.
- Velocity is derived from RMS energy of the audio at each frame.
- Optional beat tracking (to write estimated tempo into the MIDI).
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import librosa
import pretty_midi

def hz_to_midi_safe(f0_hz: float) -> float:
    """Convert Hz to MIDI; return np.nan if invalid."""
    if f0_hz is None or np.isnan(f0_hz) or f0_hz <= 0:
        return np.nan
    return librosa.hz_to_midi(f0_hz)

def median_smooth(x, win):
    if win <= 1:
        return x
    pad = win // 2
    xpad = np.pad(x, (pad, pad), mode='edge')
    out = np.array([np.median(xpad[i:i+win]) for i in range(len(x))], dtype=float)
    return out

def segment_notes(times,
                  midi_contour,
                  voiced_flag,
                  rms_norm,
                  min_note_s=0.06,
                  min_silence_s=0.04,
                  pitch_jump_semitones=1.0):
    """
    Turn frame-level pitch into note segments.
    - Start a new note when:
        * unvoiced->voiced OR voiced->unvoiced (silence gap >= min_silence_s)
        * pitch jump between adjacent frames exceeds threshold
    - Merge super-short notes with neighbors when possible.
    """
    N = len(times)
    notes = []  # list of dicts with onset_idx, offset_idx (exclusive)
    in_note = False
    start_idx = 0

    def close_note(end_idx):
        if end_idx <= start_idx:
            return
        notes.append({"onset": start_idx, "offset": end_idx})

    # identify segments
    for i in range(1, N):
        prev_v = bool(voiced_flag[i-1])
        curr_v = bool(voiced_flag[i])
        boundary = False

        if not in_note and curr_v:
            # start a note
            in_note = True
            start_idx = i - 1

        if in_note:
            # check voiced->unvoiced boundary
            if prev_v and not curr_v:
                # ensure the silence is *real* (longer than min_silence_s)
                # we'll close note now, and next voiced will open a new one
                boundary = True
            else:
                # check big pitch jump
                p_prev = midi_contour[i-1]
                p_curr = midi_contour[i]
                if not (np.isnan(p_prev) or np.isnan(p_curr)):
                    if abs(p_curr - p_prev) >= pitch_jump_semitones:
                        boundary = True

            if boundary:
                in_note = False
                close_note(i)

    if in_note:
        close_note(N)

    # prune short notes and merge if needed
    pruned = []
    for seg in notes:
        onset_t = times[seg["onset"]]
        offset_t = times[seg["offset"]-1] if seg["offset"] < N else times[-1]
        dur = max(0.0, offset_t - onset_t)
        if dur >= min_note_s:
            pruned.append(seg)

    # Optionally, merge tiny gaps between consecutive notes (if shorter than min_silence_s)
    merged = []
    for seg in pruned:
        if not merged:
            merged.append(seg)
            continue
        prev = merged[-1]
        gap = times[seg["onset"]] - times[prev["offset"]-1]
        if gap < min_silence_s:
            # merge by extending previous offset
            prev["offset"] = seg["offset"]
        else:
            merged.append(seg)

    # Build final notes with pitch = median over segment (robust to vibrato)
    final = []
    for seg in merged:
        i0, i1 = seg["onset"], seg["offset"]
        pitch_vals = midi_contour[i0:i1]
        pitch_vals = pitch_vals[~np.isnan(pitch_vals)]
        if len(pitch_vals) == 0:
            continue
        note_pitch = float(np.median(pitch_vals))
        # velocity from RMS energy (0..1) mapped to 30..110
        vel_slice = rms_norm[i0:i1]
        if len(vel_slice) == 0:
            velocity = 80
        else:
            v = float(np.mean(vel_slice))
            velocity = int(np.clip(30 + v * 80, 30, 127))
        onset_s = float(times[i0])
        # exclusive index -> get time for last frame, add hop as small epsilon
        offset_s = float(times[min(i1, len(times)-1)])
        if offset_s <= onset_s:
            continue
        final.append((onset_s, offset_s, note_pitch, velocity))
    return final

def quantize_time(value, grid_s):
    if grid_s <= 0:
        return value
    return round(value / grid_s) * grid_s

def main():
    ap = argparse.ArgumentParser(description="Convert a solo vocal track to monophonic MIDI.")
    ap.add_argument("input_audio", type=str, help="Path to vocal audio (wav/mp3/etc.)")
    ap.add_argument("output_midi", type=str, help="Path to write MIDI file")
    ap.add_argument("--sr", type=int, default=22050, help="Resample rate for analysis")
    ap.add_argument("--frame_hop_ms", type=float, default=10.0, help="Hop size in milliseconds")
    ap.add_argument("--fmin", type=float, default=65.41, help="Min pitch Hz (default ≈ C2)")
    ap.add_argument("--fmax", type=float, default=987.77, help="Max pitch Hz (default ≈ B5)")
    ap.add_argument("--pitch_conf", type=float, default=0.80, help="PYIN voiced probability threshold")
    ap.add_argument("--median_win", type=int, default=5, help="Median smoothing window (frames)")
    ap.add_argument("--min_note_ms", type=float, default=60.0, help="Minimum note length (ms)")
    ap.add_argument("--min_silence_ms", type=float, default=40.0, help="Minimum gap to split notes (ms)")
    ap.add_argument("--pitch_jump_st", type=float, default=1.0, help="Split if frame-to-frame jump ≥ this many semitones")
    ap.add_argument("--quantize", type=int, default=0, help="Quantize to N notes per beat (0 disables)")
    ap.add_argument("--instrument", type=int, default=54, help="GM program number (0-127). 54 = Voice Oohs")
    ap.add_argument("--write_tempo", action="store_true", help="Estimate tempo and write to MIDI")
    args = ap.parse_args()

    in_path = Path(args.input_audio)
    if not in_path.exists():
        print(f"Input file not found: {in_path}", file=sys.stderr)
        sys.exit(1)

    hop_length = int(round(args.sr * (args.frame_hop_ms / 1000.0)))
    y, sr = librosa.load(str(in_path), sr=args.sr, mono=True)

    # Loudness (RMS) per frame for velocity shaping
    rms = librosa.feature.rms(y=y, frame_length=hop_length*2, hop_length=hop_length, center=True)[0]
    # Normalize RMS to 0..1
    if np.max(rms) > 0:
        rms_norm = rms / np.max(rms)
    else:
        rms_norm = rms

    # PYIN pitch tracking
    f0, voiced_flag, voiced_prob = librosa.pyin(
        y,
        fmin=args.fmin,
        fmax=args.fmax,
        sr=sr,
        frame_length=hop_length*4,  # big-ish for stability
        hop_length=hop_length,
        fill_na=np.nan
    )

    # Time stamps for frames
    times = librosa.frames_to_time(np.arange(len(f0)), sr=sr, hop_length=hop_length)

    # Apply confidence threshold to voiced_flag
    if voiced_prob is not None:
        vmask = (voiced_prob >= args.pitch_conf)
    else:
        vmask = voiced_flag.astype(bool)

    # Convert to MIDI numbers and smooth a bit
    midi_contour = np.array([hz_to_midi_safe(h) for h in f0], dtype=float)
    midi_contour = median_smooth(midi_contour, args.median_win)

    # Segment into notes
    notes = segment_notes(
        times=times,
        midi_contour=midi_contour,
        voiced_flag=vmask,
        rms_norm=rms_norm,
        min_note_s=args.min_note_ms / 1000.0,
        min_silence_s=args.min_silence_ms / 1000.0,
        pitch_jump_semitones=args.pitch_jump_st
    )

    if not notes:
        print("No notes were detected—try lowering --pitch_conf, widening --fmin/--fmax, or using a cleaner audio file.", file=sys.stderr)

    # Build MIDI
    pm = pretty_midi.PrettyMIDI()

    # Optional tempo estimate
    if args.write_tempo:
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        # pretty_midi stores tempo changes via downbeat/beat timing; set a global tempo
        pm._PrettyMIDI__tempo_changes = (np.array([0.0]), np.array([tempo], dtype=float))

    inst = pretty_midi.Instrument(program=int(np.clip(args.instrument, 0, 127)))
    pm.instruments.append(inst)

    # Optional quantization grid (seconds), e.g., 16th-notes
    if args.quantize and args.write_tempo:
        if pm._PrettyMIDI__tempo_changes is None:
            q_grid = 0.0
        else:
            bpm = pm._PrettyMIDI__tempo_changes[1][0]
            beat_s = 60.0 / bpm
            q_grid = beat_s / args.quantize
    else:
        q_grid = 0.0

    for onset_s, offset_s, pitch, vel in notes:
        # Round pitch to nearest semitone (integer) for symbolic MIDI
        pitch_int = int(np.clip(round(pitch), 0, 127))
        start = quantize_time(onset_s, q_grid) if q_grid > 0 else onset_s
        end = quantize_time(offset_s, q_grid) if q_grid > 0 else offset_s
        if end <= start:
            end = start + 0.02  # ensure nonzero duration
        note = pretty_midi.Note(velocity=int(np.clip(vel, 1, 127)),
                                pitch=pitch_int,
                                start=float(start),
                                end=float(end))
        inst.notes.append(note)

    # Write file
    out_path = Path(args.output_midi)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pm.write(str(out_path))
    print(f"Wrote MIDI to: {out_path}")

if __name__ == "__main__":
    main()
