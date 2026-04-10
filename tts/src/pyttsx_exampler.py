import pyttsx3

engine = pyttsx3.init()
text = "Ok Google"
engine.setProperty("rate", 97)  # Adjust the speech rate (optional)
engine.setProperty("volume", 1)  # Adjust the volume (optional)
engine.say("Ok Google")
engine.say("Open Netflix")
engine.runAndWait()
engine.stop()
# engine.save_to_file("Open Netflix", "open-netflix.mp3")
