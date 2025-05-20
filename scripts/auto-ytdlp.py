import os
import subprocess
import sys
from pathlib import Path
import json

def run(cmd, shell=True, capture_output=False):
    result = subprocess.run(cmd, shell=shell, text=True,
                            stdout=subprocess.PIPE if capture_output else None,
                            stderr=subprocess.PIPE if capture_output else None)
    if result.returncode != 0:
        print(f"Command failed: {cmd}")
        if capture_output:
            print(result.stderr)
        sys.exit(1)
    return result.stdout if capture_output else None

def create_virtualenv():
    print("[*] Creating virtual environment...")
    run(f"{sys.executable} -m venv venv")

def install_dependencies():
    print("[*] Installing dependencies inside virtual environment...")
    pip_path = os.path.abspath("venv\\Scripts\\pip")
    run(f"{pip_path} install --upgrade pip")
    run(f"{pip_path} install yt-dlp librosa mutagen soundfile tqdm")

def get_playlist_entries(yt_dlp_path, url):
    print("[*] Fetching playlist entries...")
    json_out = run(
        f'"{yt_dlp_path}" --flat-playlist --print-json "{url}"',
        capture_output=True
    )
    entries = [json.loads(line) for line in json_out.strip().splitlines()]
    return entries

def download_entry(yt_dlp_path, video_url):
    print(f"\n\n[*] Downloading audio from: {video_url}")
    json_out = run(
        f'"{yt_dlp_path}" -f bestaudio -t mp3 '
        f'-o "%(title)s.%(ext)s" --print-json "{video_url}"',
        capture_output=True
    )
    info = json.loads(json_out)
    return Path(f"{info['title']}.mp3"), info

def analyze_bpm(file_path):
    print(f"[*] Analyzing BPM of {file_path.name}...")
    import librosa
    y, sr = librosa.load(str(file_path))
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    if hasattr(tempo, "item"):
        tempo = tempo.item()
    bpm = int(round(float(tempo)))
    print(f"[+] BPM: {bpm}")
    return bpm

def tag_metadata(file_path, bpm, genre=None):
    print(f"[*] Tagging BPM and genre metadata...")
    from mutagen.easyid3 import EasyID3
    try:
        audio = EasyID3(str(file_path))
    except Exception:
        from mutagen.id3 import ID3
        audio = EasyID3()
    audio["bpm"] = str(bpm)
    if genre:
        audio["genre"] = genre
    audio.save()
    print(f"[+] Metadata saved to {file_path.name}\n")

def main():
    if not os.path.exists("venv"):
        create_virtualenv()
        install_dependencies()
    else:
        print("[*] Virtual environment already exists.")

    python_in_venv = os.path.abspath("venv\\Scripts\\python.exe")
    if os.path.abspath(sys.executable) != python_in_venv:
        print("[*] Restarting inside virtual environment...")
        subprocess.run([python_in_venv, __file__])
        sys.exit(0)

    from tqdm import tqdm

    yt_dlp_path = os.path.abspath("venv\\Scripts\\yt-dlp")
    url = input("Enter a YouTube video or playlist URL: ").strip()
    overwrite = input("Overwrite existing MP3 files? (y/N): ").strip().lower() == "y"

    entries = get_playlist_entries(yt_dlp_path, url)

    if not entries:
        print("[*] Processing single video...")
        mp3, info = download_entry(yt_dlp_path, url)
        bpm = analyze_bpm(mp3)
        genre = info["tags"][0] if info.get("tags") else None
        tag_metadata(mp3, bpm, genre)
    else:
        print(f"[*] Processing playlist with {len(entries)} entries...\n")
        for entry in tqdm(entries, desc="Processing tracks", unit="track"):
            video_url = f"https://www.youtube.com/watch?v={entry['id']}"
            try:
                temp_title = entry.get('title') or entry['id']
                estimated_file = Path(f"{temp_title}.mp3")

                if estimated_file.exists() and not overwrite:
                    print(f"[-] Skipping existing file: {estimated_file.name}")
                    continue

                mp3, info = download_entry(yt_dlp_path, video_url)
                bpm = analyze_bpm(mp3)
                genre = info["tags"][0] if info.get("tags") else None
                tag_metadata(mp3, bpm, genre)

            except Exception as e:
                print(f"[!] Error with {entry['id']}: {e}")
                continue

    print("\n[✓] All done.")

if __name__ == "__main__":
    main()
