import concurrent.futures
import multiprocessing
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from pprint import pprint

import cv2
import ffmpeg
import imagehash
from PIL import Image

video_extensions = ["mkv", "mp4"]
print(f"{'Current working directory': <20}: {Path.cwd()}")
detected_videos = [Path.cwd().glob(f"*.{ext}") for ext in video_extensions]
video_list = [str(item) for videos in detected_videos for item in videos]
# List comprehension for below 3 lines
# for videos in detected_videos:
#     for item in videos:
#         video_list.append(str(item))
print(f"{'Detected video in current folder': <20}:")
print(f"\n".join(video_list))
if not video_list:
    print("No video detected in current directory !!!")
    sys.exit()
VIDEO_PATH = video_list[0]
if len(video_list) > 1:
    print(f"Multiple videos detected. Use the first detected video. {VIDEO_PATH}")
VIDEO_LENGTH: str = ffmpeg.probe(str(VIDEO_PATH))["streams"][0]["tags"][
    "DURATION"
].split(".")[0]
print(f"{'Video length': <20}: {VIDEO_LENGTH}")

HAMMING_THRESHOLD = 5
REF_IMG_PATH = Path.cwd().joinpath("ref.png")
if not REF_IMG_PATH.is_file():
    print(f"Unable to find '{REF_IMG_PATH}' in current directory !!!")
    sys.exit()
STEPS = 15
print(f"Using '{str(REF_IMG_PATH)}' as reference image to split video.")
OUTPUT_FOLDER = Path.cwd().joinpath("split-video")
if not OUTPUT_FOLDER.is_dir():
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
    print(f"'{OUTPUT_FOLDER}' does not exist. Creating it...")


def temp() -> None:
    ref_img_cv2 = cv2.imread(REF_IMG_PATH, cv2.COLOR_BGR2RGB)
    ref_img_cvt = Image.fromarray(ref_img_cv2)
    ref_img_hash = imagehash.average_hash(ref_img_cvt)
    print(f"{'Reference image hash': <20}: {ref_img_hash}")


def process_video(
    start_frame: int, end_frame: int, steps: int, skip_first: bool = False
) -> list[list[int]]:
    marks: list[str] = []
    video = cv2.VideoCapture(VIDEO_PATH)
    ref_img_hash = imagehash.average_hash(Image.open(REF_IMG_PATH))
    print(f"{'Reference image hash': <20}: {ref_img_hash}")
    print(f"{'Video frame count': <20}: {video.get(cv2.CAP_PROP_FRAME_COUNT)}")
    print(f"{'Video fps': <20}: {video.get(cv2.CAP_PROP_FPS)}")
    print(f"{'Start frame': <20}: {start_frame}")
    print(f"{'End frame': <20}: {end_frame}")
    print(f"{'Skip every': <20}: {steps} frame(s)")
    print(
        f"{'Total playback': <20}: "
        f"{
            time.strftime('%H:%M:%S', time.gmtime(
                video.get(cv2.CAP_PROP_FRAME_COUNT) /
                video.get(cv2.CAP_PROP_FPS)
            ))
        }"
    )
    print("\n")
    start_time = time.time()
    point_1 = False
    # for current_frame in range(0, int(video.get(cv2.CAP_PROP_FRAME_COUNT)), 15):
    for current_frame in range(start_frame, end_frame, steps):
        success, frame = video.read()
        if int(video.get(cv2.CAP_PROP_POS_FRAMES)) < start_frame:
            print(
                f"Current frame ({video.get(cv2.CAP_PROP_POS_FRAMES)}) is less "
                f"than start frame ({start_frame}). Set it to start frame..."
            )
            video.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        else:
            video.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
        if success:
            frame_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            frame_hash = imagehash.average_hash(frame_image)
            hamming_distance = ref_img_hash - frame_hash
            if hamming_distance < HAMMING_THRESHOLD:
                if current_frame < 60 * 5 and skip_first:
                    print("Skip detection within first 5 seconds...")
                    continue
                if point_1:
                    continue
                current_time = time.strftime(
                    "%H:%M:%S",
                    time.gmtime(current_frame / video.get(cv2.CAP_PROP_FPS)),
                )
                print(f"{'Hamming distance': <20}: {hamming_distance}")
                print(f"{'Frame number': <20}: {current_frame}")
                print(f"{'Time': <20}: {current_time}")
                output = f"{Path(__file__).parent.joinpath('output', current_time)}"
                # output = f"{Path(__file__).parent.joinpath(
                #     'output', current_time.replace(':', '-'))}.jpg"
                print(f"{'Current frame': <20}: {output}")
                marks.append(f"{current_time}")
                # cv2.imwrite(str(output), frame)
                point_1 = True
            elif hamming_distance > HAMMING_THRESHOLD and point_1:
                current_time = time.strftime(
                    "%H:%M:%S",
                    time.gmtime(current_frame / video.get(cv2.CAP_PROP_FPS)),
                )
                print(f"{'Frame number': <20}: {current_frame}")
                print(f"{'Time': <20}: {current_time}")
                output = f"{Path(__file__).parent.joinpath('output', current_time)}"
                # output = f"{Path(__file__).parent.joinpath(
                #     'output', current_time.replace(':', '-'))}.jpg"
                print(f"{'Current frame': <20}: {output}")
                marks.append(f"{current_time}")
                # cv2.imwrite(output, frame)
                point_1 = False
    print(f"{'Result': <20}: {marks}")
    print(
        f"{'Process time': <20}: {str(timedelta(seconds=(time.time() - start_time)))}"
    )
    video.release()
    return marks


def get_command_details(split_mark: int) -> list:
    commands: list[list[any]] = []
    video = cv2.VideoCapture(VIDEO_PATH)
    fps = video.get(cv2.CAP_PROP_FPS)
    print(f"{'fps': <20}: {fps}")
    frame_total = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"{'frame total': <20}: {frame_total}")
    frame_per_mark = int(fps * 60 * split_mark)
    print(f"{'frame per mark': <20}: {frame_per_mark}")
    process_count = int(frame_total // frame_per_mark)
    print(f"{'process count': <20}: {process_count}")
    last_process_frames = int(frame_total % frame_per_mark)
    print(f"{'last process frames': <20}: {frame_total % frame_per_mark}")
    video.release()
    for count in range(0, int(process_count)):
        items = []
        items.append(process_video)
        items.append((frame_per_mark * count) + 1)
        items.append((frame_per_mark * (count + 1)))
        items.append(STEPS)
        commands.append(items)
    if last_process_frames != 0:
        items = []
        items.append(process_video)
        items.append((frame_per_mark * process_count) + 1)
        items.append((frame_per_mark * process_count) + last_process_frames)
        items.append(STEPS)
        commands.append(items)
    commands[0].append(True)
    return commands


def get_marks(split_mark: int) -> list[str]:
    print(f"{'Number of CPU cores': <20}: {multiprocessing.cpu_count()}")
    max_processes = multiprocessing.cpu_count() - 2
    marks: list[str] = []
    start_time = time.time()
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_processes) as executor:
        futures = [
            executor.submit(*item)
            for item in get_command_details(split_mark=split_mark)
        ]
        # Leave code below as an example
        # futures.append(
        #     executor.submit(
        #         process_video,
        #         start_frame=1,
        #         end_frame=60 * 60 * 5,
        #         steps=15,
        #     )
        # )
        for future in concurrent.futures.as_completed(futures):
            print(
                f"{'future result': <20}: {future.result()} | {type(future.result())}"
            )
            if future.result():
                marks.extend(future.result())

    print(
        f"{'Total main time': <20}: {str(timedelta(seconds=(time.time() - start_time)))}"
    )
    print(f"{'marks': <20}: {marks}")
    marks_datetime = [datetime.strptime(item, "%H:%M:%S") for item in marks]
    marks_datetime.sort()
    print(f"{'marks_datetime': <20}: {marks_datetime}")
    marks_sorted = [datetime.strftime(item, "%H:%M:%S") for item in marks_datetime]
    print(f"{'marks_sorted': <20}: {marks_sorted}")
    marks = marks_sorted.copy()
    marks.insert(0, "00:00:00")
    if len(marks) % 2 != 0:
        marks.append(VIDEO_LENGTH)
    print(f"{'Num of marks': <20}: {len(marks)}")
    print(f"{'Marks': <20}: {marks}")
    return marks


def _split_video(video: str, start_time: str, end_time: str, output: str) -> None:
    ffmpeg.input(filename=video, ss=start_time, to=end_time).output(
        output, vcodec="copy", acodec="copy"
    ).run()


def multi_split(marks: list[str]) -> None:
    for index in range(0, len(marks), 2):
        _split_video(
            video=VIDEO_PATH,
            start_time=marks[index],
            end_time=marks[index + 1],
            output=str(OUTPUT_FOLDER.joinpath(f"split_{(index + 1) / 2}.mkv")),
        )


def main() -> None:
    pass


if __name__ == "__main__":
    pass
    # get_marks(split_mark=10)
    # split_video(
    #     video=VIDEO_PATH,
    #     start_time="03:19:00",
    #     end_time=None,
    #     output=str(Path(__file__).parent.joinpath("output", "output.mkv")),
    # )
    test_mark = [
        "00:00:00",
        "00:07:13",
        "00:07:14",
        "00:13:13",
        "00:13:13",
        "00:18:21",
        "00:18:21",
        "00:24:35",
        "00:24:35",
        "00:28:50",
        "00:28:50",
        "00:36:50",
        "00:36:51",
        "00:40:48",
        "00:40:49",
        "00:44:11",
        "00:44:11",
        "00:50:53",
        "00:50:54",
        "00:55:07",
        "00:55:07",
        "01:00:56",
        "01:00:57",
        "01:09:29",
        "01:09:29",
        "01:12:10",
        "01:12:11",
        "01:19:44",
        "01:19:44",
        "01:26:35",
        "01:26:35",
        "01:31:43",
        "01:31:45",
        "01:39:09",
        "01:39:09",
        "01:46:44",
        "01:46:45",
        "01:50:49",
        "01:50:49",
        "01:54:52",
        "01:55:01",
        "01:55:31",
        "01:55:33",
        "02:00:22",
        "02:00:25",
        "02:15:00",
    ]
    # multi_split(marks=temp)
