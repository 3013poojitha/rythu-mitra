"""Photos and videos sent for crop diagnosis (Crop Doctor and the chat).

A farmer can send any number of photos and videos. The AI looks at pictures,
so each video is turned into a few still frames (from the start, middle and
end). The frames and the photos are then checked together as one case.
"""
import os
import tempfile

MAX_PHOTO_MB = 8
MAX_VIDEO_MB = 50
FRAMES_PER_VIDEO = 3
MAX_PICTURES_FOR_AI = 8  # the AI looks at up to this many pictures (spread across everything sent)
VIDEO_EXT = (".mp4", ".mov", ".webm", ".mkv", ".3gp", ".avi", ".m4v")


class MediaError(Exception):
    pass


def is_video(content_type, filename=""):
    return (content_type or "").startswith("video/") or (filename or "").lower().endswith(VIDEO_EXT)


def video_frames(video_bytes, filename="video.mp4", count=FRAMES_PER_VIDEO):
    """A few JPEG stills from a video, spread from start to end."""
    import cv2  # opencv-python-headless
    suffix = os.path.splitext(filename or "")[1] or ".mp4"
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(video_bytes)
        cap = cv2.VideoCapture(path)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        spots = [int(total * (i + 1) / (count + 1)) for i in range(count)] if total > 0 else [0]
        frames = []
        for spot in spots:
            cap.set(cv2.CAP_PROP_POS_FRAMES, spot)
            ok, frame = cap.read()
            if ok:
                h, w = frame.shape[:2]
                scale = min(1.0, 1280 / max(h, w))
                if scale < 1:
                    frame = cv2.resize(frame, (int(w * scale), int(h * scale)))
                ok, jpg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                if ok:
                    frames.append(jpg.tobytes())
        cap.release()
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
    if not frames:
        raise MediaError("Could not read the video. Please send an MP4 video or photos.")
    return frames


def pictures(uploads):
    """uploads: [(bytes, content_type, filename)] -> (pictures for the AI as [(bytes, mime)], counts).
    Checks sizes; turns videos into frames."""
    if not uploads:
        raise MediaError("Please add at least one photo or video.")
    pics, photos, videos = [], 0, 0
    for data, ctype, name in uploads:
        if is_video(ctype, name):
            if len(data) > MAX_VIDEO_MB * 1024 * 1024:
                raise MediaError(f"Video too large (max {MAX_VIDEO_MB} MB)")
            pics += [(f, "image/jpeg") for f in video_frames(data, name)]
            videos += 1
        else:
            if len(data) > MAX_PHOTO_MB * 1024 * 1024:
                raise MediaError("Image too large (max 8 MB)")
            pics.append((data, ctype or "image/jpeg"))
            photos += 1
    return pics, {"photos": photos, "videos": videos}


def for_ai(pics, limit=MAX_PICTURES_FOR_AI):
    """At most `limit` pictures, picked evenly so every photo/video is represented."""
    if len(pics) <= limit:
        return pics
    step = len(pics) / limit
    return [pics[int(i * step)] for i in range(limit)]
