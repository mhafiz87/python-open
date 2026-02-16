"""
TODO: [x] Detect if media is not in fullscreen and switch to fullscreen, then
          switch back after recording
TODO: [x] Check if there's a freeze frame in the OBS recording
TODO: [ ] Create a finally block to ensure OBS recording is stopped on error
TODO: [ ] Add command line arguments for setting root output directory
TODO: [ ] Add command line arguments for settingsections to focus/stop, etc
"""
# ruff: noqa: F401
import base64
import json
import os
import re
import time
import traceback
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
import obsws_python as obs
from dotenv import load_dotenv
from obsws_python.error import OBSSDKRequestError
from PIL import Image
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


@dataclass
class Config:
    root_output_dir: str
    medias: tuple[str, ...]
    section_to_focus: tuple[tuple[str, ...], ...]
    section_to_stop: tuple[tuple[str, ...], ...]


CONFIG_FILE = "config.json"

image_1_name = "debug_screenshot_1.png"
image_2_name = "debug_screenshot_2.png"
frame_check_interval = 30  # seconds
frame_counter = 1

current_section: str = ""
element_data = {
    "course-title": r'//h1[@data-purpose = "course-header-title"]',
    "buy-now-button": r'//button[@data-purpose = "buy-now-button"]',
    "title": r'//section[@class = "lecture-view--container--mrZSm"]',
    "pause_button": r'//button[@data-purpose = "pause-button"]',
    "play_button": r'//button[@data-purpose = "play-button"]',
    "cancel_button": r'//button[@data-purpose = "cancel-button"]',
    "goto_next_button": r'//div[@data-purpose = "go-to-next-button"]',
    "goto_next_right_button": r'//div[@data-purpose = "go-to-next"]',
    "rewind_button": r'//button[@data-purpose = "rewind-skip-button"]',
    "video_class": r'//video[@class = "video-player--video-player--HiAnq"]',
    "fullscreen_button": r'//button[@class = "ud-btn ud-btn-small ud-btn-ghost ud-btn-text-sm control-bar-dropdown--trigger--FnmP- control-bar-dropdown--trigger-dark--ZK26r control-bar-dropdown--trigger-small--ogRJ4 "]',
    "fullscreen_svg": r"//*[name()='svg'][@aria-label='Fullscreen' or @aria-label='Exit fullscreen']",
    "text_viewer_class": r'//div[@data-purpose = "safely-set-inner-html:rich-text-viewer:html"]',
    "last-lesson": r'//h2[@data-purpose = "primary-message"]',
    "progress-bar": r'//div[@data-purpose="video-progress-buffer"]',
}


def get_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


root_output_dir = Path(Config(**get_config()).root_output_dir)
medias = Config(**get_config()).medias
sections_to_focus = Config(**get_config()).section_to_focus
sections_to_stop = Config(**get_config()).section_to_stop


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


def get_obs_screenshot(
    client: obs.ReqClient, file_path: str, source_name: str = "chrome"
) -> None:
    screenshot = client.get_source_screenshot(
        source_name, width=1920, height=1080, quality=100, img_format="png"
    )
    if screenshot:
        # Remove the base64 prefix ("data:image/png;base64,")
        base64_data = screenshot.image_data.split(",")[1]
        image_bytes = base64.b64decode(base64_data)

        with open(file_path, "wb") as f:
            f.write(image_bytes)
    else:
        logger.error("Failed to take screenshot")


def send_spacebar() -> None:
    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.SPACE)


def get_course_name() -> str:
    element = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, element_data["course-title"]))
    )
    course = re.sub(r"[^\w\s-]", "", element.text.replace(": ", " - "))
    logger.info(f"Course name: {course}")
    return course


def get_sections() -> list[str]:
    sections: list[str] = []
    elements = driver.find_elements(
        by=By.XPATH,
        value=('//span[@class = "truncate-with-tooltip--ellipsis--YJw4N "]'),
    )
    for element in elements:
        sections.append(element.text.replace(": ", " - "))
    return sections


def get_current_media_info() -> tuple[str, str]:
    section = ""
    title = ""
    section_pattern = r"^(Section \d{1,3}.*), (Lecture \d{1,3}.*).*"
    try:
        element = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.XPATH, element_data["title"]))
        )
        info = element.get_attribute("aria-label")
        result = re.match(section_pattern, info)
        for index, item in enumerate(result.groups()):
            if index == 0:
                section = re.sub(r"[^\w\s-]", "", item.replace(": ", " - "))
            elif index == 1:
                title = re.sub(r"[^\w\s-]", "", item.replace(": ", " - "))
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


def is_fullscreen() -> bool:
    try:
        element = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.XPATH, element_data["fullscreen_svg"]))
        )
        aria_label = element.get_attribute("aria-label")
        if aria_label == "Fullscreen":
            logger.info("Currently not in fullscreen mode.")
            return False
        else:
            logger.info("Currently in fullscreen mode.")
            return True
    except Exception:
        traceback.print_exc()
        logger.error("Unable to determine fullscreen mode. Assuming in fullscreen.")
        return True


def toggle_fullscreen() -> None:
    try:
        child = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.XPATH, element_data["fullscreen_svg"]))
        )
        element = child.find_element(By.XPATH, "./..")
        element.click()
        logger.info("Toggled fullscreen mode.")
    except Exception:
        traceback.print_exc()
        logger.error("Unable to toggle fullscreen mode.")


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


def is_buy_now_button_exist() -> tuple[bool, WebElement | None]:
    try:
        element = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, element_data["buy-now-button"]))
        )
        logger.info("Enroll Now / Go to course button found.")
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


def is_last_screen() -> bool:
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, element_data["last-lesson"]))
        )
        print("This is the last lesson screen.")
        return True
    except Exception:
        # print("This is not the last lesson screen.")
        return False


def is_ui_visible() -> bool:
    try:
        element = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.XPATH, element_data["progress-bar"]))
        )
        logger.info(f"Progress bar visibility: {element.is_displayed()}")
        return element.is_displayed()
    except Exception:
        logger.info("Progress bar visibility: False")
        return False


def make_video_ui_invisible() -> None:
    video_element = WebDriverWait(driver, 2).until(
        EC.presence_of_element_located((By.XPATH, element_data["video_class"]))
    )
    logger.info("Moving mouse to make video UI invisible...")
    ActionChains(driver).move_to_element(video_element).perform()
    # ActionChains(driver).move_by_offset(200, 200).perform()
    time.sleep(5)


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


def save_text_content(output: str) -> None:
    try:
        element = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located(
                (By.XPATH, element_data["text_viewer_class"])
            )
        )
        logger.info("Media contains text content. Saving...")
        inner_html = element.get_attribute("innerHTML")
        text_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{output.split("/")[-1]}</title>
        </head>
        <body>
            {inner_html}
        </body>
        </html>
        """
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        with open(f"{output}.html", "w", encoding="utf-8") as f:
            f.write(text_content)
        logger.info(f"Saved text content to {output}.html")
    except Exception as error:
        # print(traceback.format_exc())
        logger.error("Unable to save text content.")
        logger.error(f"{type(error).__name__}: {error}")


def check_media_ended(section: str, title: str) -> bool:
    new_media = True
    frame_counter = 1
    old_current_time = ""
    frame_check_initial_time = time.monotonic()
    # Check for frame freeze every frame_check_interval seconds or
    # when time position does not change
    get_obs_screenshot(obs_cl, image_2_name)
    while not is_media_ended():
        current_time, duration = show_time_position(clear_line=not new_media)
        if current_time != old_current_time:
            old_current_time = current_time
        else:
            # No change in time position, possibly stalled
            logger.warning("Time position not changing, possible stall detected.")
            logger.warning(f"Stopping {section}, {title} due to stall.")
            break
        frame_check_time = time.monotonic()
        if frame_check_time - frame_check_initial_time >= frame_check_interval:
            # Take screenshot for frame freeze detection
            if frame_counter % 2 == 1:
                get_obs_screenshot(obs_cl, image_1_name)
                frame_counter = 2
            else:
                get_obs_screenshot(obs_cl, image_2_name)
                frame_counter = 1
            img1 = Image.open(image_1_name)
            img2 = Image.open(image_2_name)
            img1_array = np.array(img1)
            img2_array = np.array(img2)
            freeze = np.array_equal(img1_array, img2_array)
            if freeze:
                logger.warning("Frame freeze detected in OBS.")
                logger.warning(f"Stopping {section}, {title} due to freeze.")
                logger.warning("Stopping process.")
                obs_cl.stop_record()
                exit()
            frame_check_initial_time = frame_check_time
        new_media = False


def go_to_next_media() -> bool:
    right_button = is_next_right_button_exist()
    if right_button[0]:
        right_button[1].click()
        logger.info("Navigated to next media.")
        time.sleep(10)
        return True
    else:
        if is_last_screen():
            logger.info("Reached the last lesson screen. Stopping process.")
            return False
        else:
            logger.warning("Next button not found. Possibly reached the end.")
            return False


def main(index: int) -> None:
    section_to_focus = ()
    section_to_stop = ()
    course = get_course_name()
    create_output_dir((root_output_dir / course).as_posix())
    # There's a possibility that course name is too long and causes OBS
    # recording error, so set output dir to root dir first, then manually copy
    # and paste to course dir after recording is done
    set_output_dir((root_output_dir).as_posix())
    if sections_to_focus:
        section_to_focus = sections_to_focus[index]
        logger.info(f"Sections to focus: {section_to_focus}")
    if sections_to_stop:
        section_to_stop = sections_to_stop[index]
        logger.info(f"Sections to stop: {section_to_stop}")
    if not is_fullscreen():
        toggle_fullscreen()
    while True:
        section, title = get_current_media_info()
        if is_current_page_video():
            if section_to_stop and section[:10] in section_to_stop:
                logger.info(f"Stop process at {section[:10]}")
                break
            if section[:10] in section_to_focus or not section_to_focus:
                set_output_filename(f"{section}/{title}")
                logger.info(
                    f"Output media to: {(root_output_dir / section / title).as_posix()}"
                )
                logger.info(f"Watching media: {section} - {title}")
                logger.info(f"Media duration: {get_media_duration()}")
                for _ in range(5):
                    make_video_ui_invisible()
                    if not is_ui_visible():
                        break
                if not is_media_playing():
                    print("Media is paused, resuming...")
                    send_spacebar()  # play
                    make_video_ui_invisible()
                restart_media()
                obs_cl.start_record()
                logger.info("Recording started.")
                check_media_ended(section, title)
                obs_cl.stop_record()
                logger.info("Recording stopped.")
                time.sleep(0.5)
        else:
            logger.warning("Current page is not a video media.")
            try:
                save_text_content(output=(root_output_dir / section / title).as_posix())
            except Exception:
                logger.error("This is not a text media. Skipping...")
        if not go_to_next_media():
            break


if __name__ == "__main__":
    timestamp = datetime.now().strftime("%Y%m%d_%H:%M:%S")
    log_file_handler.write_header(f"Web Parser: Start At {timestamp}")
    new_media = True
    driver = attach_chromedriver()
    obs_cl = connect_obs_socket()
    try:
        for media_index, media in enumerate(medias):
            logger.info(f"Processing media {media_index + 1}/{len(medias)}: {media}")
            current_url = driver.current_url
            if media not in current_url:
                driver.get(media)
                course_button_exists, course_button = is_buy_now_button_exist()
                if course_button_exists:
                    course_button.click()
                    time.sleep(30)  # Wait for navigation to course page
                else:
                    logger.warning(
                        "Enroll Now / Go to course button not found. Please enroll in /"
                        " buy the course and navigate to the first lecture,"
                        " then restart the program."
                    )
                    exit()
            main(index=media_index)
        else:
            logger.info("No more media URLs found in configuration.")
            log_file_handler.write_separator()
            exit()
    except Exception:
        logger.error("Encounter error while processing media.")
        recording_status = obs_cl.get_record_status()
        if recording_status.output_active:
            obs_cl.stop_record()
            logger.warning("Stopped OBS recording due to error.")
        traceback.print_exc()
        log_file_handler.write_separator()
        exit()
