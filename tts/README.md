# Text To Speech

## Python Packages

- piper-tts
- sounddevice

## Pre-Requisites

- After installing piper-tts, you need to download the model and place it in the correct directory. This will download the file at the current directory. For example:

  ```bash
  python3 -m piper.download_voices en_US-lessac-medium
  ```

- Search for sounddevice

  ```bash
  import sounddevice as sd
  sd.query_devices()
  ```

## Suggestions

- You don't have to include the voice file in the project. You can download it at runtime and save it to a temporary directory. This way, you can avoid including large files in your project and also ensure that you have the latest version of the voice model.
