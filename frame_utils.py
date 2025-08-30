import cv2
import os
import numpy as np

def extract_frames(video_path: str, temp_id: str, fps_sample: int = 10) -> list:
    """
    Extracts one frame per second from the video and
    returns a list of file paths to the saved JPEGs.

    Args:
      video_path: path to the input video file.
      temp_id:   unique prefix for naming output frames.
      fps_sample: number of frames per second to extract (default=1).

    Returns:
      List[str]: paths to the extracted frame images.
    """
    cap = cv2.VideoCapture(video_path)
    vid_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / vid_fps

    frame_paths = []
    # sample at 1 FPS: timestamps from 0 to duration
    timestamps = np.arange(0, int(duration), 1 / fps_sample)

    for idx, t in enumerate(timestamps):
        frame_no = int(t * vid_fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
        ret, frame = cap.read()
        if not ret:
            continue
        # path for this frame
        out_path = os.path.join(
            'temp', f"{temp_id}_frame_{idx}.jpg"
        )
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        cv2.imwrite(out_path, frame)
        frame_paths.append(out_path)

    cap.release()
    return frame_paths
