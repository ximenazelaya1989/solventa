from pathlib import Path
import sys

import imageio.v2 as imageio


def main():
    slides_dir = Path(sys.argv[1])
    output = Path(sys.argv[2])
    durations = [int(value) for value in sys.argv[3].split(",")]
    fps = 2
    output.parent.mkdir(parents=True, exist_ok=True)
    writer = imageio.get_writer(
        output,
        fps=fps,
        codec="libx264",
        format="FFMPEG",
        pixelformat="yuv420p",
        quality=8,
        macro_block_size=2,
        ffmpeg_params=["-movflags", "+faststart"],
    )
    try:
        for index, duration in enumerate(durations, start=1):
            frame = imageio.imread(slides_dir / f"slide-{index:02d}.png")
            for _ in range(duration * fps):
                writer.append_data(frame)
    finally:
        writer.close()
    print(output.resolve())


if __name__ == "__main__":
    main()
