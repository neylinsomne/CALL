"""
Audio Data Preparation for F5-TTS Fine-tuning
Academic standards processing with LUFS normalization and text normalization
"""

import os
import json
import click
from pathlib import Path
from typing import List, Tuple
import tempfile

import numpy as np
import soundfile as sf
from tqdm import tqdm

# Local imports
from audio_processor import AudioProcessor, validate_audio, STANDARDS
from text_normalizer import normalize_text, check_phonetic_coverage
from sharvard_corpus import get_all_training_sentences


# ===========================================
# Whisper Integration
# ===========================================
def load_whisper(model_size: str = "large-v3", device: str = "cuda"):
    """Load Faster Whisper model"""
    try:
        from faster_whisper import WhisperModel
        print(f"Loading Whisper {model_size}...")
        model = WhisperModel(model_size, device=device, compute_type="float16")
        return model
    except Exception as e:
        print(f"Error loading Whisper: {e}")
        print("Falling back to CPU...")
        from faster_whisper import WhisperModel
        return WhisperModel(model_size, device="cpu", compute_type="int8")


def transcribe_audio(audio_path: str, whisper_model) -> str:
    """Transcribe audio using Whisper"""
    segments, _ = whisper_model.transcribe(
        audio_path,
        language="es",
        vad_filter=True,
        vad_parameters=dict(
            min_silence_duration_ms=500,
            speech_pad_ms=200
        )
    )
    return " ".join([seg.text for seg in segments]).strip()


# ===========================================
# Segmentation
# ===========================================
def segment_audio_on_silence(
    audio: np.ndarray,
    sample_rate: int,
    min_duration: float = STANDARDS["min_duration"],
    max_duration: float = STANDARDS["max_duration"],
    silence_threshold_db: float = STANDARDS["silence_threshold_db"]
) -> List[Tuple[np.ndarray, float, float]]:
    """
    Segment audio on silence
    Returns list of (audio_segment, start_time, end_time)
    """
    # Convert threshold to linear
    threshold_linear = 10 ** (silence_threshold_db / 20)
    
    # Calculate RMS in windows
    window_size = int(0.025 * sample_rate)  # 25ms windows
    hop_size = int(0.010 * sample_rate)     # 10ms hop
    
    rms = []
    for i in range(0, len(audio) - window_size, hop_size):
        window = audio[i:i + window_size]
        rms.append(np.sqrt(np.mean(window ** 2)))
    
    rms = np.array(rms)
    
    # Find silence regions
    is_silence = rms < threshold_linear
    
    # Find segment boundaries
    segments = []
    segment_start = 0
    in_speech = False
    
    for i, silence in enumerate(is_silence):
        time = i * hop_size / sample_rate
        
        if not silence and not in_speech:
            # Start of speech
            segment_start = max(0, int((time - 0.1) * sample_rate))
            in_speech = True
            
        elif silence and in_speech:
            # End of speech - check duration
            segment_end = min(len(audio), int((time + 0.1) * sample_rate))
            duration = (segment_end - segment_start) / sample_rate
            
            if min_duration <= duration <= max_duration:
                segment_audio = audio[segment_start:segment_end]
                start_time = segment_start / sample_rate
                end_time = segment_end / sample_rate
                segments.append((segment_audio, start_time, end_time))
            elif duration > max_duration:
                # Split long segment
                for chunk_start in range(segment_start, segment_end, int(max_duration * sample_rate)):
                    chunk_end = min(chunk_start + int(max_duration * sample_rate), segment_end)
                    chunk_duration = (chunk_end - chunk_start) / sample_rate
                    if chunk_duration >= min_duration:
                        chunk_audio = audio[chunk_start:chunk_end]
                        segments.append((chunk_audio, chunk_start / sample_rate, chunk_end / sample_rate))
            
            in_speech = False
    
    return segments


# ===========================================
# Main Processing
# ===========================================
def process_audio_directory(
    input_dir: str,
    output_dir: str,
    whisper_size: str = "large-v3",
    device: str = "cuda",
    normalize_transcripts: bool = True
) -> dict:
    """
    Process all audio files with academic standards
    
    Pipeline:
    1. Load and validate audio
    2. Normalize to LUFS -23
    3. Segment on silence
    4. Transcribe with Whisper
    5. Normalize transcription text
    6. Validate phonetic coverage
    7. Generate metadata
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize processors
    audio_processor = AudioProcessor(target_sr=STANDARDS["sample_rate"])
    whisper = load_whisper(whisper_size, device)
    
    # Find audio files
    audio_extensions = {'.wav', '.mp3', '.flac', '.ogg', '.m4a'}
    audio_files = [
        f for f in input_path.iterdir()
        if f.suffix.lower() in audio_extensions
    ]
    
    print(f"\n{'='*60}")
    print(f"Processing {len(audio_files)} audio files")
    print(f"Standards: {STANDARDS['sample_rate']}Hz, {STANDARDS['target_lufs']} LUFS")
    print(f"{'='*60}\n")
    
    metadata = []
    all_texts = []
    stats = {
        "total_files": len(audio_files),
        "total_segments": 0,
        "total_duration": 0.0,
        "skipped": 0,
        "issues": []
    }
    
    for idx, audio_file in enumerate(tqdm(audio_files, desc="Processing")):
        try:
            # Load audio
            audio, sr = sf.read(str(audio_file))
            
            # Convert to mono
            if len(audio.shape) > 1:
                audio = np.mean(audio, axis=1)
            
            # Process through academic pipeline
            temp_path = output_path / f"temp_{audio_file.stem}.wav"
            result = audio_processor.process_file(str(audio_file), str(temp_path))
            
            if not result["validation"]["valid"]:
                print(f"\n  ⚠ {audio_file.name}: {result['validation']['issues']}")
                stats["issues"].extend(result["validation"]["issues"])
            
            # Load normalized audio
            audio_norm, sr = sf.read(str(temp_path))
            
            # Segment if too long
            duration = len(audio_norm) / sr
            if duration > STANDARDS["max_duration"]:
                segments = segment_audio_on_silence(audio_norm, sr)
            else:
                segments = [(audio_norm, 0, duration)] if duration >= STANDARDS["min_duration"] else []
            
            if not segments:
                stats["skipped"] += 1
                temp_path.unlink(missing_ok=True)
                continue
            
            # Process each segment
            for seg_idx, (segment_audio, start_time, end_time) in enumerate(segments):
                duration = end_time - start_time
                segment_name = f"{audio_file.stem}_{seg_idx:03d}.wav"
                segment_path = output_path / segment_name
                
                # Validate segment
                validation = validate_audio(segment_audio, sr)
                if not validation["valid"]:
                    continue
                
                # Save segment
                sf.write(str(segment_path), segment_audio, sr, subtype='PCM_16')
                
                # Transcribe
                transcription = transcribe_audio(str(segment_path), whisper)
                
                if not transcription.strip():
                    segment_path.unlink()
                    continue
                
                # Normalize text if enabled
                if normalize_transcripts:
                    transcription_normalized = normalize_text(transcription)
                else:
                    transcription_normalized = transcription
                
                all_texts.append(transcription_normalized)
                
                metadata.append({
                    "audio_file": segment_name,
                    "text": transcription_normalized,
                    "text_original": transcription if normalize_transcripts else None,
                    "duration": duration,
                    "source": audio_file.name,
                    "lufs": validation["lufs"],
                    "true_peak_db": validation["true_peak_db"]
                })
                
                stats["total_segments"] += 1
                stats["total_duration"] += duration
            
            # Cleanup temp file
            temp_path.unlink(missing_ok=True)
        
        except Exception as e:
            print(f"\n  ✗ {audio_file.name}: {str(e)}")
            stats["skipped"] += 1
    
    # Check phonetic coverage
    print("\n" + "="*60)
    print("Checking phonetic coverage...")
    coverage = check_phonetic_coverage(all_texts)
    print(f"Coverage: {coverage['coverage_percent']:.1f}%")
    if coverage['missing_vowels']:
        print(f"  Missing vowels: {coverage['missing_vowels']}")
    if coverage['missing_consonants']:
        print(f"  Missing consonants: {coverage['missing_consonants']}")
    if coverage['missing_special']:
        print(f"  Missing digraphs: {coverage['missing_special']}")
    
    # Save metadata
    metadata_path = output_path / "metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump({
            "samples": metadata,
            "statistics": stats,
            "phonetic_coverage": coverage,
            "standards": STANDARDS
        }, f, ensure_ascii=False, indent=2)
    
    # Save filelist for F5-TTS
    filelist_path = output_path / "filelist.txt"
    with open(filelist_path, "w", encoding="utf-8") as f:
        for item in metadata:
            f.write(f"{item['audio_file']}|{item['text']}\n")
    
    # Print summary
    print("\n" + "="*60)
    print("Processing Complete!")
    print(f"  Total segments: {stats['total_segments']}")
    print(f"  Total duration: {stats['total_duration']/60:.1f} minutes ({stats['total_duration']/3600:.2f} hours)")
    print(f"  Skipped files: {stats['skipped']}")
    print(f"  Phonetic coverage: {coverage['coverage_percent']:.1f}%")
    print(f"  Output directory: {output_path}")
    print("="*60)
    
    return stats


# ===========================================
# CLI
# ===========================================
@click.command()
@click.option(
    '--input', '-i', 'input_dir',
    required=True,
    type=click.Path(exists=True),
    help='Input directory with audio files'
)
@click.option(
    '--output', '-o', 'output_dir',
    required=True,
    type=click.Path(),
    help='Output directory for processed files'
)
@click.option(
    '--whisper', '-w', 'whisper_size',
    default='large-v3',
    type=click.Choice(['tiny', 'base', 'small', 'medium', 'large-v3']),
    help='Whisper model size for transcription'
)
@click.option(
    '--device', '-d',
    default='cuda',
    type=click.Choice(['cuda', 'cpu']),
    help='Device for processing'
)
@click.option(
    '--normalize-text/--no-normalize-text',
    default=True,
    help='Normalize transcriptions (numbers, abbreviations)'
)
def main(input_dir: str, output_dir: str, whisper_size: str, device: str, normalize_text: bool):
    """
    Prepare audio data for F5-TTS fine-tuning with academic standards
    
    This script:
    1. Normalizes audio to LUFS -23 (EBU R128)
    2. Segments on silence (5-15 seconds)
    3. Transcribes with Whisper
    4. Normalizes Spanish text
    5. Validates phonetic coverage
    """
    process_audio_directory(
        input_dir, 
        output_dir, 
        whisper_size, 
        device,
        normalize_text
    )


if __name__ == "__main__":
    main()
