# Automatic YT-DLP
Automatic YT-DLP uses Python to make a virtual environment, fetch required dependencies and then asks the user for a URL. Once the URL is delivered, a few things happen:
- It extracts an MP3 file.
- Uses `librosa` and `mutagen` to assume a BPM for the file and tags it.
