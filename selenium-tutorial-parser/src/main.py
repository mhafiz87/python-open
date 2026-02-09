# ruff: noqa: F401

import os
import re
import time
import traceback
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import obsws_python as obs
from dotenv import load_dotenv
from obsws_python.error import OBSSDKRequestError
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chromium.webdriver import ChromiumDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from logger import log_file_handler, logger

load_dotenv()

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
    "fullscreen_button": r'//button[@aria-label = "Fullscreen"]',
    "exit_fullscreen_button": r'//button[@aria-label = "Exit fullscreen"]',
}


root_output_dir = Path("D:/_u")
# root_output_dir = Path(__file__).parent / "output"
# root_output_dir = Path("/home/autouser/output")


def attach_chromedriver() -> ChromiumDriver:
    driver = None
    options = Options()
    # options.add_argument("--remote-debugging-port=9222")
    # options.add_argument("user-data-dir=C:\\selenium\\ChromeProfile")
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    # options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(options=options)
    logger.info(
        f"Attached to existing Chrome session. Current URL: \033[4;34m{driver.current_url}\033[0m"
    )
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


def get_course_name() -> str:
    element = driver.find_element(
        by=By.XPATH, value='//h1[@data-purpose = "course-header-title"]'
    )
    return element.text.replace(": ", " - ")


def get_sections() -> tuple[str]:
    sections: list[str] = []
    elements = driver.find_elements(
        by=By.XPATH,
        value=('//span[@class = "truncate-with-tooltip--ellipsis--YJw4N "]'),
    )
    for element in elements:
        sections.append(element.text.replace(": ", " - "))
    return tuple(sections)


def get_current_media_info(split_pattern: tuple[str]) -> tuple[str, str]:
    section = ""
    title = ""
    try:
        element = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.XPATH, element_data["title"]))
        )
        info = element.get_attribute("aria-label")
        for item in split_pattern:
            if item in info.replace(": ", " - ").replace("/", ","):
                section = item
                title = (
                    info.split(", ", maxsplit=1)[1]
                    .replace(": ", " - ")
                    .replace("/", ",")
                )
        # print(f"{'Section':<8}: {section}\n{'Title':<8}: {title}")
        return section, title
    except Exception:
        traceback.print_exc()
        print("Unable to find media title.")
        return section, title


def create_output_dir(title: str = "") -> None:
    # obs_cl.set_profile_parameter("SimpleOutput", "FilePath", root_output_dir.as_posix())
    output = root_output_dir
    if title:
        output = root_output_dir / title
    if not output.is_dir():
        output.mkdir(parents=True, exist_ok=True)
    print(f"Created output directory: {root_output_dir}")


def set_output_dir(name: str) -> None:
    print(f"Setting output directory to: {name}")
    obs_cl.set_profile_parameter("SimpleOutput", "FilePath", name)


def set_output_filename(name: str) -> None:
    print(f"Setting output filename to: {name}")
    obs_cl.set_profile_parameter("Output", "FilenameFormatting", name)


def is_current_page_video() -> bool:
    try:
        element = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.XPATH, element_data["video_class"]))
        )
        # Move mouse to make UI invisible
        ActionChains(driver).move_to_element(element).perform()
        return True
    except Exception:
        return False


def is_fullscreen() -> tuple[bool, WebElement | None]:
    try:
        element = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located(
                (By.XPATH, element_data["exit_fullscreen_button"])
            )
        )
        return (True, element)
    except Exception:
        element = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located(
                (By.XPATH, element_data["fullscreen_button"])
            )
        )
        return (False, element)


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


def is_media_playing() -> bool:
    try:
        WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.XPATH, element_data["pause_button"]))
        )
        print("Media is playing.")
        return True
    except Exception:
        print("Media is paused.")
        return False


def is_media_ended() -> bool:
    try:
        WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.XPATH, element_data["cancel_button"]))
        )
        print("Media has ended.")
        return True
    except Exception:
        # print("Media is playing...")
        return False


def seconds_to_time(seconds, precision=2):
    """
    Convert seconds to formatted HH:MM:SS string with customizable decimal precision.

    Args:
        seconds (float): Time in seconds
        precision (int): Number of decimal places (default: 6)

    Returns:
        str: Formatted time string in HH:MM:SS.xxxxxx format
    """
    hours = int(seconds // 3600)
    remaining = seconds % 3600
    minutes = int(remaining // 60)
    remaining_seconds = remaining % 60

    # Calculate width for seconds (2 digits + decimal point + precision)
    sec_width = 3 + precision if precision > 0 else 2

    if precision > 0:
        return (
            f"{hours:02d}:{minutes:02d}:{remaining_seconds:0{sec_width}.{precision}f}"
        )
    else:
        return f"{hours:02d}:{minutes:02d}:{int(remaining_seconds):02d}"


def show_time_position(clear_line: bool = True) -> tuple[str, str]:
    LINE_UP = "\033[1A"
    LINE_CLEAR = "\x1b[2K"
    try:
        element = WebDriverWait(driver, 0.25).until(
            EC.presence_of_element_located((By.XPATH, element_data["video_class"]))
        )
        current_time = driver.execute_script(
            "return arguments[0].currentTime;", element
        )
        duration = driver.execute_script("return arguments[0].duration;", element)
        if clear_line:
            print(LINE_UP, end=LINE_CLEAR)
        print(
            f"Current Time: {seconds_to_time(current_time)} / "
            f"{seconds_to_time(duration)}"
        )
        return seconds_to_time(current_time), seconds_to_time(duration)
    except Exception:
        print("Unable to get time position.")
        return "", ""


def get_media_duration() -> str | None:
    try:
        element = WebDriverWait(driver, 0.5).until(
            EC.presence_of_element_located((By.XPATH, element_data["video_class"]))
        )
        duration = driver.execute_script("return arguments[0].duration;", element)
        return seconds_to_time(duration)
    except Exception:
        logger.error("Unable to get media duration.")
        return None


def restart_media() -> None:
    try:
        element = WebDriverWait(driver, 0.5).until(
            EC.presence_of_element_located((By.XPATH, element_data["video_class"]))
        )
        driver.execute_script("arguments[0].currentTime = 0;", element)
        logger.info("Media has been restarted to the beginning.")
    except Exception:
        logger.error("Unable to restart media.")


if __name__ == "__main__":
    timestamp = datetime.now().strftime("%Y%m%d_%H:%M:%S")
    log_file_handler.write_header(f"Web Parser: Start At {timestamp}")
    new_media = True
    driver = attach_chromedriver()
    obs_cl = connect_obs_socket()
    course = get_course_name()
    sections = get_sections()
    section_to_skip: tuple[str, ...] = ()
    print("Course name:", course)
    print("Sections:", sections)
    print("Current media info:", get_current_media_info(sections))
    print(get_current_media_info(sections))
    # fullscreen_status, fullscreen_element = is_fullscreen()
    # if not fullscreen_status:
    #     fullscreen_element.click()
    while True:
        if is_current_page_video():
            section, title = get_current_media_info(sections)
            if section in section_to_skip:
                print(f"Skip section: {section}")
                continue
            # To stop at specific section
            # if "Section 6" in section:
            #     print("Stop process at Section 16.")
            #     break
            set_output_filename(f"{section}/{title}")
            # print( obs_cl.get_profile_parameter( "Output", "FilenameFormatting").__dict__.keys())
            # print( obs_cl.get_profile_parameter( "SimpleOutput", "FilePath").parameter_value)
            # print( obs_cl.get_profile_parameter( "Output", "FilenameFormatting").parameter_value)
            filename = obs_cl.get_profile_parameter(
                "Output", "FilenameFormatting"
            ).parameter_value
            Path(root_output_dir / get_course_name()).mkdir(parents=True, exist_ok=True)
            root_output_dir.mkdir(parents=True, exist_ok=True)
            create_output_dir(root_output_dir.as_posix())
            set_output_dir(root_output_dir.as_posix())
            logger.info(
                f"Output media to: {(root_output_dir / section / title).as_posix()}"
            )
            logger.info(f"Watching media: {section} - {title}")
            logger.info(f"Media duration: {get_media_duration()}")
            if not is_media_paused():
                send_spacebar()  # pause
            time.sleep(0.5)
            # Move mouse to make UI invisible
            video_element = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.XPATH, element_data["video_class"]))
            )
            ActionChains(driver).move_to_element(video_element).perform()
            ActionChains(driver).move_by_offset(200, 200).perform()
            time.sleep(3)
            send_spacebar()  # play
            print("Media is playing...")
            if not is_media_playing():
                print("Media is paused, resuming...")
                send_spacebar()  # play
                print("Media is playing...")
            ActionChains(driver).move_to_element(video_element).perform()
            ActionChains(driver).move_by_offset(200, 200).perform()
            time.sleep(3)
            restart_media()
            obs_cl.start_record()
            logger.info("Recording started.")
            old_current_time = ""
            while not is_media_ended():
                current_time, duration = show_time_position(clear_line=not new_media)
                if current_time != old_current_time:
                    old_current_time = current_time
                else:
                    # No change in time position, possibly stalled
                    logger.warning(
                        "Time position not changing, possible stall detected."
                    )
                    logger.warning(f"Stopping {section}, {title} due to stall.")
                    break
                new_media = False
            obs_cl.stop_record()
            logger.info("Recording stopped.")
            time.sleep(0.5)
        else:
            logger.warning("Current page is not a video media.")
        right_button = is_next_right_button_exist()
        if right_button[0]:
            right_button[1].click()
            logger.info("Navigated to next media.")
            new_media = True
            time.sleep(10)
        else:
            break
    log_file_handler.write_separator()
    print("Done")
