import argparse
import base64
from dataclasses import dataclass
from typing import Generator, Iterable, Tuple

import cv2
from openai import OpenAI


@dataclass
class FrameDescription:
    index: int
    timestamp: float
    description: str


def iter_frames(video_path: str, interval_seconds: float) -> Generator[Tuple[int, float, "cv2.Mat"], None, None]:
    """Yield frames from the video every ``interval_seconds`` along with metadata."""
    capture = cv2.VideoCapture(video_path)
    if not capture.isOpened():
        raise ValueError(f"Não foi possível abrir o vídeo: {video_path}")

    fps = capture.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        raise ValueError("FPS do vídeo não pôde ser determinado.")

    frame_interval = max(int(fps * interval_seconds), 1)
    frame_index = 0

    while True:
        success, frame = capture.read()
        if not success:
            break

        timestamp = frame_index / fps
        yield frame_index, timestamp, frame

        # Avança para o próximo frame desejado
        capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index + frame_interval)
        frame_index += frame_interval

    capture.release()


def frame_to_base64(frame: "cv2.Mat") -> str:
    """Encode a frame as a base64 JPEG string."""
    success, buffer = cv2.imencode(".jpg", frame)
    if not success:
        raise ValueError("Falha ao converter frame para JPEG.")
    return base64.b64encode(buffer).decode("ascii")


def describe_frame(client: OpenAI, frame: "cv2.Mat", prompt: str, model: str) -> str:
    image_data = frame_to_base64(frame)
    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}},
                ],
            }
        ],
    )
    return response.output_text


def describe_video_frames(
    video_path: str,
    interval_seconds: float,
    prompt: str = "Descreva a imagem de forma concisa.",
    model: str = "gpt-4.1-mini",
    client: OpenAI | None = None,
) -> Iterable[FrameDescription]:
    """
    Process video frames with the OpenAI completions API to generate descriptions.

    Args:
        video_path: Caminho para o arquivo MP4.
        interval_seconds: Intervalo em segundos entre frames analisados.
        prompt: Instrução enviada ao modelo para descrever a imagem.
        model: Modelo usado na API de completions.
        client: Instância do cliente OpenAI. Se não for fornecida, uma nova será criada.
    """
    effective_client = client or OpenAI()

    for index, timestamp, frame in iter_frames(video_path, interval_seconds):
        description = describe_frame(effective_client, frame, prompt, model)
        yield FrameDescription(index=index, timestamp=timestamp, description=description)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Descreve frames de um vídeo via API da OpenAI.")
    parser.add_argument("video", help="Caminho para o vídeo MP4.")
    parser.add_argument(
        "-t",
        "--interval",
        type=float,
        default=1.0,
        help="Intervalo em segundos entre frames processados (padrão: 1s).",
    )
    parser.add_argument(
        "-m",
        "--model",
        default="gpt-4.1-mini",
        help="Modelo da API de completions a ser usado (padrão: gpt-4.1-mini).",
    )
    parser.add_argument(
        "-p",
        "--prompt",
        default="Descreva a imagem de forma concisa.",
        help="Prompt enviado ao modelo para descrever cada frame.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    client = OpenAI()

    for description in describe_video_frames(
        video_path=args.video,
        interval_seconds=args.interval,
        prompt=args.prompt,
        model=args.model,
        client=client,
    ):
        timestamp_seconds = round(description.timestamp, 2)
        print(f"Frame {description.index} (@ {timestamp_seconds}s): {description.description}")


if __name__ == "__main__":
    main()
