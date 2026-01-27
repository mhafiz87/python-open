"""
1. Launch `OBS` with Web Socket Server enable.
  1.1 Tools > Web Socket Server Settings
  1.2 Enable Web Socket Server
  1.3 Show connect info to get password
  1.4 Store port and password in `.env` file

"""


# ruff: noqa: F401

import os
import time
from pathlib import Path

import obsws_python as obs
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chromium.webdriver import ChromiumDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

current_section: str = ""
element_data = {
    "title": r'//section[@class = "lecture-view--container--mrZSm"]',
    "pause_button": r'//button[@data-purpose = "pause-button"]',
    "play_button": r'//button[@data-purpose = "play-button"]',
    "cancel_button": r'//button[@data-purpose = "cancel-button"]',
    "goto_next_button": r'//div[@data-purpose = "go-to-next-button"]',
    "goto_next_right_button": r'//div[@data-purpose = "go-to-next"]',
    "rewind_button": r'//button[@data-purpose = "rewind-skip-button"]',
    "video_class": r'//video[@class = "video-player--video-player--HiAnq"]',
}
root_output_dir = Path(__file__).parent / "output"


def attach_chromedriver() -> ChromiumDriver:
    driver = None
    options = Options()
    # options.add_argument("--remote-debugging-port=9222")
    # options.add_argument("user-data-dir=C:\\selenium\\ChromeProfile")
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    # options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(options=options)
    print(driver.current_url)
    return driver


def connect_obs_socket() -> obs.ReqClient:
    obs_cl = obs.ReqClient(
        host="localhost",
        port=os.getenv("OBS_PORT"),
        password=os.getenv("OBS_PASSWORD"),
        timeout=3,
    )
    return obs_cl


def send_spacebar() -> None:
    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.SPACE)


def get_title() -> str:
    element = driver.find_element(
        by=By.XPATH, value='//h1[@data-purpose = "course-header-title"]'
    )
    # print(f"Title: {element.text.replace(': ', ' - ')}")
    return element.text.replace(": ", " - ")


def get_sections() -> list[str]:
    sections: list[str] = []
    elements = driver.find_elements(
        by=By.XPATH,
        value=(
            '//button[@class = "ud-btn ud-btn-medium ud-btn-link ud-heading-md '
            'js-panel-toggler accordion-panel-module--panel-toggler--WUiNu"]'
        ),
    )
    for element in elements:
        if "Section" in element.text:
            sections.append(element.text)
    return sections


def create_output_dir(title: str = "") -> None:
    # obs_cl.set_profile_parameter("SimpleOutput", "FilePath", root_output_dir.as_posix())
    output = root_output_dir
    if title:
        output = root_output_dir / title
    output.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {root_output_dir}")


def create_section_folder() -> None:
    for section in get_sections():
        dir = root_output_dir / get_title() / section
        dir = dir.as_posix().replace(": ", " - ")
        Path(dir).mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir}")


def set_output_dir(section: str) -> None:
    dir = root_output_dir / section
    obs_cl.set_profile_parameter("SimpleOutput", "FilePath", dir.as_posix())


def set_output_filename(name: str) -> None:
    obs_cl.set_profile_parameter("Output", "FilenameFormatting", name)


def is_current_page_video() -> bool:
    try:
        element = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.XPATH, element_data["video_class"]))
        )
        ActionChains(driver).move_to_element(element).perform()
        return True
    except Exception:
        return False


def get_current_media_info() -> tuple[str, str]:
    section = ""
    title = ""
    try:
        element = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.XPATH, element_data["title"]))
        )
        info = element.get_attribute("aria-label")
        section = info.split(", ", maxsplit=1)[0].replace(": ", " - ")
        title = info.split(", ", maxsplit=1)[1].replace(": ", " - ")
        print(section, title)
        return section, title
    except Exception:
        print("Unable to find media title.")
        return section, title


def is_next_right_button_exist() -> tuple[bool, WebElement | None]:
    try:
        element = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located(
                (By.XPATH, element_data["goto_next_right_button"])
            )
        )
        return True, element
    except Exception:
        return False, None


def is_media_paused() -> bool:
    try:
        WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.XPATH, element_data["play_button"]))
        )
        print("Media is paused.")
        return True
    except Exception:
        print("Media is playing.")
        return False


def is_media_ended() -> bool:
    try:
        WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.XPATH, element_data["cancel_button"]))
        )
        print("Media has ended.")
        return True
    except Exception:
        print("Media is playing...")
        return False


def restart_media() -> None:
    try:
        element = WebDriverWait(driver, 0.5).until(
            EC.presence_of_element_located((By.XPATH, element_data["video_class"]))
        )
        driver.execute_script("arguments[0].currentTime = 0;", element)
    except Exception:
        print("Unable to restart media.")


if __name__ == "__main__":
    load_dotenv()
    driver = attach_chromedriver()
    obs_cl = connect_obs_socket()
    create_output_dir()
    create_section_folder()
    while True:
        if is_current_page_video():
            section, title = get_current_media_info()
            set_output_dir(section)
            set_output_filename(title)
            if not is_media_paused():
                send_spacebar()  # pause
            restart_media()
            time.sleep(0.5)
            ActionChains(driver).move_by_offset(100, 100).perform()
            time.sleep(3)
            obs_cl.start_record()
            send_spacebar()  # play
            while not is_media_ended():
                time.sleep(0.5)
            obs_cl.stop_record()
        right_button = is_next_right_button_exist()
        if right_button[0]:
            right_button[1].click()
        else:
            break
    print("Done")
