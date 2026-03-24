# ruff: noqa: F401
import glob
import json
import os
import re
import time
import traceback
from enum import StrEnum
from pathlib import Path

import PyChromeDevTools
from rapidfuzz import fuzz, process
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from logger import logger
from src.config import (
    get_medias,
    get_obs_path,
    get_root_output_dir,
    get_section_to_focus,
    get_section_to_stop,
)


class Element(StrEnum):
    CourseTitle = r'//h1[@data-purpose = "course-header-title"]'
    BuyNowButton = r"//button[@data-purpose='buy-now-button'][.//*[contains(text(), 'Enroll now') or contains(text(), 'Go to course')]]"
    Title = r'//section[@class = "lecture-view--container--mrZSm"]'
    ProgressDisplay = r'//div[@data-purpose = "progress-display"]'
    CurrentTime = r'//span[@data-purpose = "current-time"]'
    Duration = r'//span[@data-purpose = "duration"]'
    Section = r'//span[@class = "ud-accordion-panel-title"]'
    Lecture = (
        r'//span[@class = "curriculum-item-link--curriculum-item-title-content--S-urg"]'
    )
    Lectures = r'//li[contains(@class, "curriculum-item-link--curriculum-item--OVP5S")]'
    LectureProgress = r'//input[@data-purpose = "progress-toggle-button"]'
    Caption = r'//div[@data-purpose = "captions-cue-text"]'
    DontAskButton = r'//button[@data-purpose = "dont-ask-button"]'
    PauseButton = r'//button[@data-purpose = "pause-button"]'
    PlayButton = r'//button[@data-purpose = "play-button"]'
    PlayButtonInitial = r'//button[@data-purpose = "video-play-button-initial"]'
    CancelButton = r'//button[@data-purpose = "cancel-button"]'
    GoToNextButton = r'//div[@data-purpose = "go-to-next-button"]'
    GoToNextRightButton = r'//div[@data-purpose = "go-to-next"]'
    RewindButton = r'//button[@data-purpose = "rewind-skip-button"]'
    # VideoClass = r'//video[@class = "video-player--video-player--HiAnq"]'
    VideoClass = r'//video[contains(@class, "video-player-module")]'
    # FullscreenButton = r'//button[@class = "ud-btn ud-btn-small ud-btn-ghost ud-btn-text-sm control-bar-dropdown--trigger--FnmP- control-bar-dropdown--trigger-dark--ZK26r control-bar-dropdown--trigger-small--ogRJ4 "]'
    FullscreenButton = r'//button[@data-purpose = "fullscreen-toggle"]'
    FullscreenSVG = r"//*[name()='svg'][@aria-label='Fullscreen' or @aria-label='Exit fullscreen' or @aria-label='Enter fullscreen']"
    TextViewerClass = (
        r'//div[@data-purpose = "safely-set-inner-html:rich-text-viewer:html"]'
    )
    LastLesson = r'//h2[@data-purpose = "primary-message"]'
    ProgressBar = r'//div[@data-purpose="video-progress-buffer"]'
    NextCurriculum = (
        r'//*[name()="svg"][@aria-label="Navigate to the next curriculum item"]'
    )
    NextCont = r'//div[contains(@class, "next-and-previous--next")]'
    PrevCont = r'//div[contains(@class, "next-and-previous--previous")]'
    UserInactivity = (
        r'//div[contains(@class, "user-activity-module--hide-when-user-inactive")]'
    )
    Resources = r'//a[@class="ud-btn ud-btn-medium ud-btn-ghost ud-text-sm resource--resource--ZGyBg ud-block-list-item ud-block-list-item-small ud-block-list-item-link"]'


class MediaType(StrEnum):
    VIDEO = "video"
    ARTICLE = "article"
    QUIZ = "quiz"
    UNKNOWN = "unknown"


class Automate:
    def __init__(self) -> None:
        self.driver: WebDriver = None

    def attach_driver(self) -> None:
        options = Options()
        # options.add_argument("--remote-debugging-port=9222")
        # options.add_argument("user-data-dir=C:\\selenium\\ChromeProfile")
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        options.add_experimental_option(
            "prefs",
            {
                "download.default_directory": str(get_root_output_dir()),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
            },
        )
        # options.add_experimental_option("detach", True)
        self.driver = webdriver.Chrome(options=options)
        logger.info(
            f"Attached to existing Chrome session. Current URL: "
            f"\033[4;34m{self.driver.current_url}\033[0m"
        )
        self.chromePCD = PyChromeDevTools.ChromeInterface()
        self.chromePCD.Network.enable()
        self.chromePCD.Page.enable()

    def get_course_name(self) -> str:
        """
        Retrieves and sanitizes the course name from the web page.

        This method waits for the course title element to be present on the page,
        extracts its text, sanitizes it by removing special characters (except
        hyphens and spaces), and replaces colons with hyphens for better
        file system compatibility.

        Returns:
            str: The sanitized course name with special characters removed and
                 colons replaced with hyphens.

        Raises:
            TimeoutException: If the course title element is not found within 30 seconds.

        Example:
            >>> course_name = self.get_course_name()
            >>> print(course_name)  # "Python Programming - Advanced Techniques"
        """
        element = WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.XPATH, Element.CourseTitle))
        )
        course = re.sub(r"[^\w\s-]", "", element.text.replace(": ", " - "))
        logger.info(f"Course name: {course}")
        return course

    def get_sections(self) -> list[str]:
        sections: list[str] = []
        elements = self.driver.find_elements(
            by=By.XPATH,
            value=Element.Section,
        )
        for element in elements:
            sections.append(element.text.replace(": ", " - "))
        return sections

    def open_all_sections(self) -> None:
        sections = WebDriverWait(self.driver, 30).until(
            EC.presence_of_all_elements_located((By.XPATH, Element.Section))
        )
        for section in sections:
            button = section.find_element(By.XPATH, "..")
            try:
                if button.get_attribute("aria-expanded") == "false":
                    logger.info(f"{section.text} is collapsed. Expanding...")
                    button.click()
                    logger.info(f"Opened section: {section.text}")
                    time.sleep(1)
                else:
                    logger.info(f"{section.text} is already expanded.")
            except Exception as error:
                logger.error(f"Unable to open section: {section.text}")
                logger.error(f"{type(error).__name__}")
                # traceback.print_exc()

    def get_current_media_info(self) -> tuple[str, str]:
        """
        Retrieves the current media section and lecture title from the web page.

        This method waits for the title element to be present on the page, extracts
        the aria-label attribute, and parses it to get the section and lecture information.
        The parsed information is cleaned by removing special characters and replacing
        colons with hyphens.

        Returns:
            tuple[str, str]: A tuple containing:
                - section (str): The section information (e.g., "Section 1 - Introduction").
                                Empty string if unable to retrieve.
                - title (str): The lecture title (e.g., "Lecture 1 - Getting Started").
                              Empty string if unable to retrieve.

        Raises:
            No exceptions are raised. All exceptions are caught and logged as warnings.

        Example:
            >>> section, title = self.get_current_media_info()
            >>> print(f"Section: {section}, Title: {title}")
            Section: Section 1 - Introduction, Title: Lecture 1 - Getting Started

        Note:
            - The method expects the aria-label to match the pattern:
              "Section {number}..., Lecture {number}..."
            - Special characters (except word characters, spaces, and hyphens) are removed
              from the section and title strings.
            - Waits up to 2 seconds for the element to be present before timing out.
        """
        section = ""
        title = ""
        section_pattern = r"^(Section \d{1,3}.*), (Lecture \d{1,3}.*).*"
        try:
            element = WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.XPATH, Element.Title))
            )
            info = element.get_attribute("aria-label")
            result = re.match(section_pattern, info)
            for index, item in enumerate(result.groups()):
                if index == 0:
                    section = re.sub(r"[^\w\s-]", "", item.replace(": ", " - "))
                elif index == 1:
                    title = re.sub(r"[^\w\s-]", "", item.replace(": ", " - "))
            logger.info(f"Current media info - Section: {section}, Title: {title}")
            return section, title
        except Exception as error:
            # traceback.print_exc()
            logger.warning("Unable to find media title.")
            logger.warning(f"{type(error).__name__}")
            return section, title

    def get_all_lectures(self) -> list[str]:
        """
        Retrieve all lecture titles from the current page.

        This method finds all lecture elements on the page using the configured XPath selector,
        extracts their text content, and formats them by replacing ": " with " - ".

        Returns:
            list[str]: A list of formatted lecture titles as strings.

        Example:
            >>> lectures = self.get_all_lectures()
            >>> print(lectures)
            ['1. Introduction', '2. Advanced Topics']
        """
        lectures: list[str] = []
        elements = self.driver.find_elements(
            by=By.XPATH,
            value=Element.Lecture,
        )
        for element in elements:
            lectures.append(element.text.replace(": ", " - "))
        return lectures

    def get_current_lecture_element(self) -> WebElement | None:
        try:
            elements = self.driver.find_elements(
                by=By.XPATH,
                value=Element.Lectures,
            )
            for element in elements:
                if "is-current" in element.get_attribute("class"):
                    # print(element.text)
                    return element
            return None
        except Exception as error:
            # traceback.print_exc()
            logger.warning("Unable to find current lecture element.")
            # logger.error(f"{type(error).__name__}: {error}")
            logger.warning(f"{type(error).__name__}")
            return None

    def get_current_media_type(self) -> MediaType:
        """
        Determines the media type of the current lecture element.

        Extracts the media type by finding the SVG use element within the current
        lecture's bottom row and examining its 'xlink:href' attribute. Identifies
        whether the current content is a video, article, or unknown media type.

        Returns:
            MediaType: The type of media for the current lecture. Can be:
                - MediaType.VIDEO if the xlink:href contains 'video'
                - MediaType.ARTICLE if the xlink:href contains 'article'
                - MediaType.UNKNOWN if the media type cannot be determined or
                  an exception occurs during detection

        Logs:
            - info: The detected media type icon name extracted from the xlink:href
            - warning: Error details if the media type cannot be determined
        """
        try:
            temp = self.get_current_lecture_element()
            child = temp.find_element(
                By.XPATH,
                ".//*[div[contains(@class, 'curriculum-item-link--bottom-row--AVBnl')]]//*[local-name()='use']",
            )
            logger.info(
                f"Current media type: {child.get_attribute('xlink:href').split('#icon-')[-1]}"
            )
            if "video" in child.get_attribute("xlink:href").lower():
                return MediaType.VIDEO
            elif "article" in child.get_attribute("xlink:href").lower():
                return MediaType.ARTICLE
            return MediaType.UNKNOWN
        except Exception as error:
            # traceback.print_exc()
            logger.warning("Unable to determine current media type.")
            # logger.warning(f"{type(error).__name__}: {error}")
            logger.warning(f"{type(error).__name__}")
            return MediaType.UNKNOWN

    def get_lecture_element_by_title(self, title: str) -> WebElement | None:
        try:
            lectures = self.driver.find_elements(
                by=By.XPATH,
                value=Element.Lecture,
            )
            target_lecture, score, index = process.extractOne(
                title,
                [lecture.text for lecture in lectures],
                scorer=fuzz.token_sort_ratio,
            )
            logger.info(
                f"Target lecture: {target_lecture}, Score: {score}, Index: {index}"
            )
            for element in lectures:
                if element.text == target_lecture:
                    return element
            return None
        except Exception as error:
            # traceback.print_exc()
            logger.error(f"Unable to find lecture element by title: {title}")
            logger.error(f"{type(error).__name__}: {error}")
            return None

    def is_lecture_completed(self, lecture: str) -> bool:
        try:
            element = self.get_lecture_element_by_title(lecture)
            check_label = self.driver.find_element(
                By.XPATH,
                rf'//input[contains(@aria-label, "Mark lecture {element.text.split(". ")[1]}")]',
            )
            logger.info(check_label.get_attribute("aria-label"))
            if "incomplete" in check_label.get_attribute("aria-label").lower():
                logger.info(f"{lecture} is completed.")
                return True
            logger.info(f"{lecture} is not completed.")
            return False
        except Exception:
            traceback.print_exc()
            logger.error(f"Unable to determine {lecture} progress.")
            return False

    def is_current_page_video(self) -> bool:
        try:
            element = WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.XPATH, Element.VideoClass))
            )
            # Move mouse to make UI invisible
            ActionChains(self.driver).move_to_element(element).perform()
            return True
        except Exception:
            return False

    def is_fullscreen(self) -> bool:
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, Element.FullscreenSVG))
            )
            aria_label = element.get_attribute("aria-label")
            if aria_label == "Fullscreen":
                logger.info("Currently not in fullscreen mode.")
                return False
            else:
                logger.info("Currently in fullscreen mode.")
                return True
        except Exception:
            # traceback.print_exc()
            logger.error("Unable to determine fullscreen mode. Assuming in fullscreen.")
            return True

    def toggle_fullscreen(self) -> None:
        try:
            child = WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.XPATH, Element.FullscreenSVG))
            )
            element = child.find_element(By.XPATH, "./..")
            element.click()
            logger.info("Toggled fullscreen mode.")
        except Exception:
            # traceback.print_exc()
            logger.error("Unable to toggle fullscreen mode.")

    def is_next_right_button_exist(self) -> tuple[bool, WebElement | None]:
        try:
            element = WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.XPATH, Element.GoToNextRightButton))
            )
            logger.info("Next right button found.")
            return True, element
        except Exception:
            try:
                temp_element = WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located((By.XPATH, Element.NextCurriculum))
                )
                element = temp_element.find_element(By.XPATH, "..")
                logger.info("Next curriculum button found.")
                return True, element
            except Exception:
                logger.error("Unable to find next button or next curriculum button.")
        return False, None

    def is_buy_now_button_exist(self) -> tuple[bool, WebElement | None]:
        try:
            element = WebDriverWait(self.driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, Element.BuyNowButton))
            )
            logger.info("Enroll Now / Go to course button found.")
            return True, element
        except Exception:
            return False, None

    def is_media_paused(self) -> bool:
        try:
            WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.XPATH, Element.PlayButton))
            )
            print("Media is paused.")
            return True
        except Exception:
            print("Media is playing.")
            return False

    def is_media_playing(self) -> bool:
        try:
            WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.XPATH, Element.PauseButton))
            )
            print("Media is playing.")
            return True
        except Exception:
            print("Media is paused.")
            return False

    def is_media_ended(self) -> bool:
        try:
            WebDriverWait(self.driver, 0.1).until(
                EC.presence_of_element_located((By.XPATH, Element.CancelButton))
            )
            logger.info("Media has ended.")
            return True
        except Exception:
            # print("Unable to find cancel button...")
            try:
                WebDriverWait(self.driver, 0.1).until(
                    EC.presence_of_element_located((By.XPATH, Element.DontAskButton))
                )
                logger.info("Media has ended.")
                return True
            except Exception:
                pass
                # logger.info(
                #     "Unable to find end of media indicators. Assuming media is still playing."
                # )
        return False

    def is_last_screen(self) -> bool:
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, Element.LastLesson))
            )
            print("This is the last lesson screen.")
            return True
        except Exception:
            # print("This is not the last lesson screen.")
            return False

    def is_ui_visible(self) -> bool:
        try:
            element = WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.XPATH, Element.ProgressBar))
            )
            logger.info(f"Progress bar visibility: {element.is_displayed()}")
            return element.is_displayed()
        except Exception:
            logger.info("Progress bar visibility: False")
            return False

    def make_video_ui_invisible(self) -> None:
        video_element = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, Element.VideoClass))
        )
        logger.info("Moving mouse to make video UI invisible...")
        ActionChains(self.driver).move_to_element(video_element).perform()
        # ActionChains(self.driver).move_by_offset(200, 200).perform()
        time.sleep(5)

    def show_time_position(self, clear_line: bool = True) -> tuple[str, str]:
        LINE_UP = "\033[1A"
        LINE_CLEAR = "\x1b[2K"
        try:
            times = self.get_media_time()
            if times is not None:
                current_time, duration = times
                if clear_line:
                    print(LINE_UP + LINE_CLEAR, end="")
                print(f"Current Time: {current_time} / Duration: {duration}")
                return current_time, duration
            return "", ""
        except Exception:
            logger.warning("Unable to get time position.")
            return "", ""

    def get_media_time(self) -> tuple[str, str] | None:
        """
        Retrieve the current playback time and total duration from the media player UI.

        This method reads the text content of the elements identified by
        `Element.CurrentTime` and `Element.Duration` using Selenium.

        Returns:
            tuple[str, str] | None:
                A tuple containing `(current_time, duration)` when both values are
                successfully retrieved; otherwise `None` if any error occurs.

        Side Effects:
            Logs a warning message ("Unable to get media time.") when retrieval fails.
        """
        try:
            element = WebDriverWait(self.driver, 0.25).until(
                EC.presence_of_element_located((By.XPATH, Element.VideoClass))
            )
            current_time = self.seconds_to_time(
                self.driver.execute_script("return arguments[0].currentTime;", element)
            )
            duration = self.seconds_to_time(
                self.driver.execute_script("return arguments[0].duration;", element)
            )
            return current_time, duration
        except Exception:
            logger.warning("Unable to get media time.")
            return None

    def restart_media(self) -> None:
        try:
            element = WebDriverWait(self.driver, 0.5).until(
                EC.presence_of_element_located((By.XPATH, Element.VideoClass))
            )
            self.driver.execute_script("arguments[0].currentTime = 0;", element)
            logger.info("Media has been restarted to the beginning.")
        except Exception:
            logger.error("Unable to restart media.")

    def save_text_content(self, output: str) -> None:
        try:
            element = WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.XPATH, Element.TextViewerClass))
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

    def go_to_next_media(self) -> int:
        right_button = self.is_next_right_button_exist()
        if right_button[0]:
            right_button[1].click()
            logger.info("Navigated to next media.")
            time.sleep(10)
            return 0
        else:
            if self.is_last_screen():
                logger.info("Reached the last lesson screen. Stopping process.")
                return 1
            else:
                logger.warning("Next button not found. Possibly reached the end.")
                return 2

    def download_resources(self, section: str, lecture: str) -> None:
        try:
            for _ in range(3):
                self.driver.execute_script("window.scrollTo(0, 0);")
                current_lecture = self.get_current_lecture_element()
                self.driver.execute_script(
                    "arguments[0].scrollIntoView(true)", current_lecture
                )
                time.sleep(2.5)
                resource_button = current_lecture.find_element(
                    By.XPATH, ".//button[contains(@aria-label, 'Resource list')]"
                )
                if not resource_button:
                    logger.info("This lecture has resource")
                    return
                resource_button.click()
                time.sleep(2.5)
                temp = self.get_current_lecture_element()
                resources = temp.find_elements(By.XPATH, ".//a")
                if not resources:
                    logger.warning("Resources empty, retry again")
                    url = self.driver.current_url.split("lecture")[0]
                    self.driver.get(url)
                    time.sleep(15)
                    continue
                print(resources)
                resource_button.click()
                break
            else:
                logger.warning("Unable to get resources.")
                return
            time.sleep(1)
            for resource in resources:
                if "cdn" in resource.get_attribute("href"):
                    resource_button.click()
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView(true)", resource
                    )
                    resource.click()
                    time.sleep(2.5)
                    logger.info(f"Downloaded {resource.get_attribute('download')}")
                    files = glob.glob(str(get_root_output_dir()) + "/*")
                    latest_file = max(files, key=os.path.getmtime)
                    output = (
                        get_root_output_dir()
                        / f"{section}/{lecture.split(' - ')[0]} - {resource.get_attribute('download')}"
                    )
                    logger.info(f"Moving {latest_file} -> {output}")
                    Path(latest_file).replace(output)
            else:
                pass
                # logger.info("This lecture does not have any downloadable resources.")
            # resource_button.click()
        except NoSuchElementException as error:
            logger.error(f"{type(error).__name__}")
        except Exception as error:
            traceback.print_exc()
            logger.error(f"{type(error).__name__} : {error}")
            logger.error("This lecture does not have any resources.")

    def send_spacebar(self) -> None:
        self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.SPACE)

    def send_f(self) -> None:
        self.driver.find_element(By.TAG_NAME, "body").send_keys("f")

    def hide_next_prev_cont(self) -> None:
        try:
            next = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, Element.NextCont))
            )
            prev = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, Element.PrevCont))
            )
            self.driver.execute_script(
                "arguments[0].style.visibility = 'hidden';", next
            )
            self.driver.execute_script(
                "arguments[0].style.visibility = 'hidden';", prev
            )
        except Exception:
            pass

    def toggle_hide_inactivity(self, hide: bool) -> None:
        try:
            inactivities = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, Element.UserInactivity))
            )
            if hide:
                for inactivity in inactivities:
                    self.driver.execute_script(
                        "arguments[0].style.visibility = 'hidden';", inactivity
                    )
                    time.sleep(0.5)
            else:
                for inactivity in inactivities:
                    self.driver.execute_script(
                        "arguments[0].style.visibility = 'visible';", inactivity
                    )
                    time.sleep(0.5)
        except Exception:
            pass

    def get_caption(self, filename: str) -> None:
        self.driver.refresh()
        time.sleep(5)
        try:
            WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, Element.PlayButtonInitial))
            )
            logger.info("Found initial play button.")
        except Exception:
            pass
        messages = self.chromePCD.pop_messages()

        for m in messages:
            # print(m)
            if "method" in m and m["method"] == "Network.responseReceived":
                try:
                    url = m["params"]["response"]["url"]
                    if ".vtt" in url:
                        # print(f"{m['params']['requestId']}")
                        requestId = m["params"]["requestId"]
                        body_response = self.chromePCD.Network.getResponseBody(
                            requestId=requestId
                        )
                        # print(body_response[0].get("result", {}).get("body", ""))
                        if body_response[0] is None:
                            logger.warning(
                                "Received empty response body for caption request."
                            )
                            continue
                        with open(filename, "w", encoding="utf-8") as f:
                            f.write(body_response[0].get("result", {}).get("body", ""))
                            logger.info(f"Saved caption to {filename}")
                        break
                except Exception as error:
                    logger.error(
                        f"Error while processing network response: {type(error).__name__}: {error}"
                    )
                    traceback.print_exc()
        else:
            logger.warning("Unable to find subtitle file in network responses.")

    @staticmethod
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
            return f"{hours:02d}:{minutes:02d}:{remaining_seconds:0{sec_width}.{precision}f}"
        else:
            return f"{hours:02d}:{minutes:02d}:{int(remaining_seconds):02d}"

if __name__ == "__main__":
    automate = Automate()
    automate.attach_driver()
    temp = automate.get_current_lecture_element()
    resource_button = temp.find_element(
        By.XPATH, ".//button[contains(@aria-label, 'Resource list')]"
    )
    print(resource_button.tag_name)
    print(resource_button.text)
    resource_button.click()
    time.sleep(2.5)
    for _ in range(5):
        temp = automate.driver.find_element(
            By.XPATH,
            r'//body[@id = "udemy"]',
        )
        temp1 = temp.find_elements(By.XPATH, r".//a")
        print(len(temp1))
        for link in temp1:
            print(link.get_attribute("href"))
        if len(temp1) > 0:
            break
        time.sleep(1)
    else:
        print("Unable to find href")
