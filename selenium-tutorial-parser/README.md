# Selenium Tutorial Parser

## Chrome Setup

1. Add chrome path to environment variables. Then refresh current terminal environment variables or open new terminal.

   ```powershell
   [System.Environment]::SetEnvironmentVariable('path', "C:\Program Files\Google\Chrome\Application;" + [System.Environment]::GetEnvironmentVariable('path', "User"),"User")
   ```

2. Launch browser with remote debugging.

   ```powershell
   chrome --remote-debugging-port=9222 --user-data-dir="$HOME/temp/chrome_profile"
   chrome --remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir="$HOME/temp/chrome_profile" &
   # or for always fullscreen
   chrome --kiosk --remote-debugging-port=9222 --user-data-dir="$HOME/temp/chrome_profile"
   chrome --kiosk --remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir="$HOME/temp/chrome_profile" &
   ```

3. Login into website and go into the target url.
4. Go to settings > privacy and security > security > safe browsing > no protection (not recommended) to disable safe browsing. This is required to allow Selenium to interact with the browser.

## OBS Setup

1. Enable `OBS` with Web Socket Server enable.
   1.1 Tools > Web Socket Server Settings
   1.2 Enable Web Socket Server
   1.3 Show connect info to get password
   1.4 Store port and password in `.env` file
2. Launch OBS with `admin` if using Windows.

## .env File

1. Create a `.env` file with these keys:

   ```text
   OBS_PORT=
   OBS_PASSWORD=
   ```

## Config File

1. Create a config file name `config.json` with this key value:

   ```json
   {
     "root_output_dir": "",
     "medias": [],
     "section_to_focus": [],
     "section_to_stop": []
   }
   ```

2. Details:

   | key                | type                   | example                              |
   | ------------------ | ---------------------- | ------------------------------------ |
   | "medias"           | list of strings        | ["url1", "url2"]                     |
   | "section_to_focus" | list of list of string | [["url1_section"], ["url1_section"]] |
   | "section_to_stop"  | list of list of string | [["url1_section"], ["url1_section"]] |

## References

1. [Can Selenium interact with an existing browser session?](https://stackoverflow.com/a/70088095)
