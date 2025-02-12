import concurrent.futures
import multiprocessing
import time
from datetime import datetime, timedelta
from pathlib import Path

import cv2
import imagehash
from PIL import Image

HAMMING_THRESHOLD = 5
VIDEO_PATH = Path(__file__).parent.joinpath("data", "video.mkv")
REF_IMG_PATH = Path(__file__).parent.joinpath("data", "ref.png")
STEPS = 15

if not VIDEO_PATH.is_file():
    raise FileExistsError(f"{VIDEO_PATH} does not exist !!!")


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


def main(split_mark) -> None:
    print(f"{'Number of CPU cores': <20}: {multiprocessing.cpu_count()}")
    max_processes = multiprocessing.cpu_count() - 2
    marks: list[list[int]] = []
    start_time = time.time()
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_processes) as executor:
        futures = [
            executor.submit(*item)
            for item in get_command_details(split_mark=split_mark)[:4]
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


if __name__ == "__main__":
    main(split_mark=2)
