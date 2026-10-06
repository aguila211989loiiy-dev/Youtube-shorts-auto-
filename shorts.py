"""Generador local gratuito: eSpeak NG + FFmpeg. Falla sin medios válidos."""
import argparse
import datetime as dt
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import urllib.request
from zoneinfo import ZoneInfo


def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def probe(path):
    if not path.is_file() or not path.stat().st_size:
        raise ValueError(f'Medio ausente o vacío: {path}')
    return json.loads(run('ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)))


def validate_image(path):
    if not any(s['codec_type'] == 'video' for s in probe(path)['streams']):
        raise ValueError('La imagen no contiene un flujo visual')
    run('ffmpeg', '-v', 'error', '-i', str(path), '-frames:v', '1', '-f', 'null', '-')


def validate_audio(path):
    data = probe(path)
    if not any(s['codec_type'] == 'audio' for s in data['streams']):
        raise ValueError('Falta el flujo de audio')
    duration = float(data['format']['duration'])
    if not math.isfinite(duration) or not 0.1 < duration <= 60:
        raise ValueError('Duración de audio inválida; máximo 60 segundos')
    result = subprocess.run(['ffmpeg', '-v', 'info', '-i', str(path), '-af', 'volumedetect', '-f', 'null', '-'], check=True, capture_output=True, text=True)
    import re
    match = re.search(r'max_volume: ([-\w.]+) dB', result.stderr)
    if not match or float(match[1]) < -50:
        raise ValueError('Audio vacío o silencioso')
    return duration


def stamp(seconds):
    ms = round(seconds * 1000)
    return f'{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}'


def generate(episode, output):
    output = Path(output)
    # Quitar cualquier resultado previo para impedir reutilizarlo después de un fallo.
    for stale in (output, output.with_suffix('.srt'), output.with_suffix('.json')):
        stale.unlink(missing_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = episode.get('sentences', [])
    if not lines or any(not isinstance(s, str) or not s.strip() or len(s) > 180 for s in lines):
        raise ValueError('Se requieren frases no vacías de hasta 180 caracteres')
    with tempfile.TemporaryDirectory(prefix='short-') as directory:
        work = Path(directory)
        image = work / 'image.jpg'
        if episode.get('image_path'):
            shutil.copyfile(episode['image_path'], image)
        else:
            url = episode.get('image_url', '')
            if not url.startswith('https://'):
                raise ValueError('Falta imagen local o URL HTTPS')
            req = urllib.request.Request(url, headers={'User-Agent': 'YoutubeShortsAuto/1.0 (educational video generator)'})
            with urllib.request.urlopen(req, timeout=60) as response:
                data = response.read(20 * 1024 * 1024 + 1)
            if len(data) > 20 * 1024 * 1024:
                raise ValueError('Imagen demasiado grande')
            image.write_bytes(data)
        validate_image(image)
        parts, captions, elapsed = [], [], 0.0
        for index, sentence in enumerate(lines):
            part = work / f'voice-{index}.wav'
            run('espeak-ng', '-v', 'es', '-s', '150', '-w', str(part), '--', sentence)
            duration = validate_audio(part)
            captions.append(f'{index + 1}\n{stamp(elapsed)} --> {stamp(elapsed + duration)}\n{sentence}\n')
            elapsed += duration
            parts.append(part)
        manifest = work / 'audio.txt'
        manifest.write_text(''.join(f"file '{p.name}'\n" for p in parts))
        audio = work / 'voice.wav'
        run('ffmpeg', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', str(manifest), '-c:a', 'pcm_s16le', str(audio))
        duration = validate_audio(audio)
        (work / 'captions.srt').write_text('\n'.join(captions), encoding='utf-8')
        # Trabajar en el directorio temporal evita escapado de rutas en el filtro.
        filters = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,subtitles=captions.srt:force_style='FontName=DejaVu Sans,FontSize=18,Alignment=2,MarginV=65,Outline=2'"
        subprocess.run(['ffmpeg', '-v', 'error', '-loop', '1', '-i', 'image.jpg', '-i', 'voice.wav', '-vf', filters, '-map', '0:v:0', '-map', '1:a:0', '-t', str(duration), '-r', '30', '-c:v', 'libx264', '-preset', 'fast', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', 'result.mp4'], cwd=work, check=True)
        result = work / 'result.mp4'
        streams = probe(result)['streams']
        if not any(s.get('width') == 1080 and s.get('height') == 1920 for s in streams):
            raise ValueError('MP4 sin vídeo vertical válido')
        validate_audio(result)
        run('ffmpeg', '-v', 'error', '-i', str(result), '-f', 'null', '-')
        staged = output.with_suffix('.mp4.partial')
        try:
            shutil.copyfile(result, staged)
            os.replace(staged, output)
        finally:
            staged.unlink(missing_ok=True)
        shutil.copyfile(work / 'captions.srt', output.with_suffix('.srt'))
        output.with_suffix('.json').write_text(json.dumps(episode, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--catalog', default='content.json')
    parser.add_argument('--output', default='output/short.mp4')
    args = parser.parse_args()
    catalog = json.loads(Path(args.catalog).read_text())
    if not catalog:
        raise ValueError('Catálogo vacío')
    today = dt.datetime.now(ZoneInfo('America/Sao_Paulo')).date()
    generate(catalog[today.toordinal() % len(catalog)], args.output)


if __name__ == '__main__':
    main()
