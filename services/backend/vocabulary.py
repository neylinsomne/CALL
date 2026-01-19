"""
Voice Vocabulary Management API
Backend for managing custom vocabulary audio samples
"""

import os
import uuid
import shutil
from datetime import datetime
from typing import Optional, List
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
import aiofiles

# Database imports (will use same DB as main backend)
from database import Database


# ===========================================
# Configuration
# ===========================================
VOCABULARY_AUDIO_DIR = Path(os.getenv("VOCABULARY_DIR", "/app/vocabulary"))
VOCABULARY_AUDIO_DIR.mkdir(parents=True, exist_ok=True)


# ===========================================
# Router
# ===========================================
router = APIRouter(prefix="/vocabulary", tags=["Voice Vocabulary"])
db = Database()


# ===========================================
# Models
# ===========================================
class VocabularyCategory(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    parent_id: Optional[str] = None  # For subcategories

class VocabularyWord(BaseModel):
    id: Optional[str] = None
    word: str
    phonetic: Optional[str] = None  # IPA pronunciation
    category_id: Optional[str] = None
    audio_path: Optional[str] = None
    duration_seconds: Optional[float] = None
    sample_count: int = 0
    notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class VocabularyPhrase(BaseModel):
    id: Optional[str] = None
    phrase: str
    category_id: Optional[str] = None
    audio_path: Optional[str] = None
    duration_seconds: Optional[float] = None
    context: Optional[str] = None  # Usage context
    notes: Optional[str] = None

class RecordingGuide(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    items: List[str]  # Words or phrases to record
    category_id: Optional[str] = None
    estimated_duration_minutes: Optional[float] = None


# ===========================================
# Category Endpoints
# ===========================================
@router.post("/categories", response_model=dict)
async def create_category(category: VocabularyCategory):
    """Create a new vocabulary category"""
    category_id = str(uuid.uuid4())
    
    await db.execute("""
        INSERT INTO vocabulary_categories (id, name, description, parent_id, created_at)
        VALUES ($1, $2, $3, $4, $5)
    """, category_id, category.name, category.description, category.parent_id, datetime.utcnow())
    
    return {"id": category_id, "name": category.name}


@router.get("/categories")
async def list_categories():
    """List all vocabulary categories"""
    categories = await db.fetch("""
        SELECT c.*, 
               (SELECT COUNT(*) FROM vocabulary_words WHERE category_id = c.id) as word_count,
               (SELECT COUNT(*) FROM vocabulary_phrases WHERE category_id = c.id) as phrase_count
        FROM vocabulary_categories c
        ORDER BY c.name
    """)
    return {"categories": categories}


@router.get("/categories/{category_id}")
async def get_category(category_id: str):
    """Get category with its words and phrases"""
    category = await db.fetchrow(
        "SELECT * FROM vocabulary_categories WHERE id = $1", category_id
    )
    if not category:
        raise HTTPException(404, "Category not found")
    
    words = await db.fetch(
        "SELECT * FROM vocabulary_words WHERE category_id = $1 ORDER BY word", category_id
    )
    phrases = await db.fetch(
        "SELECT * FROM vocabulary_phrases WHERE category_id = $1 ORDER BY phrase", category_id
    )
    
    return {
        "category": dict(category),
        "words": [dict(w) for w in words],
        "phrases": [dict(p) for p in phrases]
    }


@router.delete("/categories/{category_id}")
async def delete_category(category_id: str):
    """Delete a category and its contents"""
    await db.execute("DELETE FROM vocabulary_words WHERE category_id = $1", category_id)
    await db.execute("DELETE FROM vocabulary_phrases WHERE category_id = $1", category_id)
    await db.execute("DELETE FROM vocabulary_categories WHERE id = $1", category_id)
    return {"status": "deleted"}


# ===========================================
# Word Endpoints
# ===========================================
@router.post("/words", response_model=dict)
async def create_word(
    word: str = Form(...),
    phonetic: Optional[str] = Form(None),
    category_id: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    audio: Optional[UploadFile] = File(None)
):
    """Create a new vocabulary word with optional audio"""
    word_id = str(uuid.uuid4())
    audio_path = None
    duration = None
    
    if audio:
        # Save audio file
        audio_filename = f"{word_id}_{word.replace(' ', '_')}.wav"
        audio_path = VOCABULARY_AUDIO_DIR / "words" / audio_filename
        audio_path.parent.mkdir(parents=True, exist_ok=True)
        
        async with aiofiles.open(audio_path, 'wb') as f:
            content = await audio.read()
            await f.write(content)
        
        # Calculate duration (simplified)
        import soundfile as sf
        try:
            data, sr = sf.read(str(audio_path))
            duration = len(data) / sr
        except:
            pass
    
    await db.execute("""
        INSERT INTO vocabulary_words 
        (id, word, phonetic, category_id, audio_path, duration_seconds, notes, sample_count, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, 1, $8, $8)
    """, word_id, word, phonetic, category_id, str(audio_path) if audio_path else None, 
        duration, notes, datetime.utcnow())
    
    return {"id": word_id, "word": word, "audio_path": str(audio_path) if audio_path else None}


@router.get("/words")
async def list_words(
    category_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    has_audio: Optional[bool] = Query(None)
):
    """List vocabulary words with filters"""
    query = "SELECT * FROM vocabulary_words WHERE 1=1"
    params = []
    
    if category_id:
        params.append(category_id)
        query += f" AND category_id = ${len(params)}"
    
    if search:
        params.append(f"%{search}%")
        query += f" AND word ILIKE ${len(params)}"
    
    if has_audio is not None:
        if has_audio:
            query += " AND audio_path IS NOT NULL"
        else:
            query += " AND audio_path IS NULL"
    
    query += " ORDER BY word"
    
    words = await db.fetch(query, *params)
    return {"words": [dict(w) for w in words], "total": len(words)}


@router.get("/words/{word_id}")
async def get_word(word_id: str):
    """Get a specific word"""
    word = await db.fetchrow("SELECT * FROM vocabulary_words WHERE id = $1", word_id)
    if not word:
        raise HTTPException(404, "Word not found")
    return dict(word)


@router.post("/words/{word_id}/audio")
async def upload_word_audio(word_id: str, audio: UploadFile = File(...)):
    """Upload or replace audio for a word"""
    word = await db.fetchrow("SELECT * FROM vocabulary_words WHERE id = $1", word_id)
    if not word:
        raise HTTPException(404, "Word not found")
    
    # Save new audio
    audio_filename = f"{word_id}_{word['word'].replace(' ', '_')}.wav"
    audio_path = VOCABULARY_AUDIO_DIR / "words" / audio_filename
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    
    async with aiofiles.open(audio_path, 'wb') as f:
        content = await audio.read()
        await f.write(content)
    
    # Calculate duration
    import soundfile as sf
    duration = None
    try:
        data, sr = sf.read(str(audio_path))
        duration = len(data) / sr
    except:
        pass
    
    # Update database
    await db.execute("""
        UPDATE vocabulary_words 
        SET audio_path = $1, duration_seconds = $2, sample_count = sample_count + 1, updated_at = $3
        WHERE id = $4
    """, str(audio_path), duration, datetime.utcnow(), word_id)
    
    return {"status": "uploaded", "audio_path": str(audio_path), "duration": duration}


@router.get("/words/{word_id}/audio")
async def get_word_audio(word_id: str):
    """Download word audio"""
    word = await db.fetchrow("SELECT * FROM vocabulary_words WHERE id = $1", word_id)
    if not word or not word['audio_path']:
        raise HTTPException(404, "Audio not found")
    
    return FileResponse(word['audio_path'], media_type="audio/wav")


@router.delete("/words/{word_id}")
async def delete_word(word_id: str):
    """Delete a word and its audio"""
    word = await db.fetchrow("SELECT * FROM vocabulary_words WHERE id = $1", word_id)
    if word and word['audio_path']:
        Path(word['audio_path']).unlink(missing_ok=True)
    
    await db.execute("DELETE FROM vocabulary_words WHERE id = $1", word_id)
    return {"status": "deleted"}


# ===========================================
# Phrase Endpoints
# ===========================================
@router.post("/phrases", response_model=dict)
async def create_phrase(
    phrase: str = Form(...),
    category_id: Optional[str] = Form(None),
    context: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    audio: Optional[UploadFile] = File(None)
):
    """Create a new vocabulary phrase"""
    phrase_id = str(uuid.uuid4())
    audio_path = None
    duration = None
    
    if audio:
        audio_filename = f"{phrase_id}.wav"
        audio_path = VOCABULARY_AUDIO_DIR / "phrases" / audio_filename
        audio_path.parent.mkdir(parents=True, exist_ok=True)
        
        async with aiofiles.open(audio_path, 'wb') as f:
            content = await audio.read()
            await f.write(content)
        
        import soundfile as sf
        try:
            data, sr = sf.read(str(audio_path))
            duration = len(data) / sr
        except:
            pass
    
    await db.execute("""
        INSERT INTO vocabulary_phrases 
        (id, phrase, category_id, audio_path, duration_seconds, context, notes, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    """, phrase_id, phrase, category_id, str(audio_path) if audio_path else None,
        duration, context, notes, datetime.utcnow())
    
    return {"id": phrase_id, "phrase": phrase}


@router.get("/phrases")
async def list_phrases(
    category_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    """List vocabulary phrases"""
    query = "SELECT * FROM vocabulary_phrases WHERE 1=1"
    params = []
    
    if category_id:
        params.append(category_id)
        query += f" AND category_id = ${len(params)}"
    
    if search:
        params.append(f"%{search}%")
        query += f" AND phrase ILIKE ${len(params)}"
    
    query += " ORDER BY phrase"
    
    phrases = await db.fetch(query, *params)
    return {"phrases": [dict(p) for p in phrases]}


# ===========================================
# Recording Guide Endpoints
# ===========================================
@router.post("/guides")
async def create_recording_guide(guide: RecordingGuide):
    """Create a recording guide/script"""
    guide_id = str(uuid.uuid4())
    
    # Calculate estimated duration (avg 5 seconds per item)
    estimated_duration = len(guide.items) * 5 / 60  # minutes
    
    await db.execute("""
        INSERT INTO recording_guides 
        (id, name, description, items, category_id, estimated_duration_minutes, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """, guide_id, guide.name, guide.description, guide.items, 
        guide.category_id, estimated_duration, datetime.utcnow())
    
    return {"id": guide_id, "name": guide.name, "estimated_duration": estimated_duration}


@router.get("/guides")
async def list_guides():
    """List all recording guides"""
    guides = await db.fetch("SELECT * FROM recording_guides ORDER BY created_at DESC")
    return {"guides": [dict(g) for g in guides]}


@router.get("/guides/{guide_id}")
async def get_guide(guide_id: str):
    """Get a recording guide"""
    guide = await db.fetchrow("SELECT * FROM recording_guides WHERE id = $1", guide_id)
    if not guide:
        raise HTTPException(404, "Guide not found")
    return dict(guide)


@router.get("/guides/{guide_id}/export")
async def export_guide(guide_id: str, format: str = Query("txt")):
    """Export recording guide as text file"""
    guide = await db.fetchrow("SELECT * FROM recording_guides WHERE id = $1", guide_id)
    if not guide:
        raise HTTPException(404, "Guide not found")
    
    content = f"# {guide['name']}\n"
    if guide['description']:
        content += f"# {guide['description']}\n"
    content += f"# Total items: {len(guide['items'])}\n"
    content += f"# Estimated duration: {guide['estimated_duration_minutes']:.1f} minutes\n\n"
    
    for i, item in enumerate(guide['items'], 1):
        content += f"{i:03d}. {item}\n"
    
    return {"content": content, "filename": f"{guide['name']}.txt"}


# ===========================================
# Bulk Operations
# ===========================================
@router.post("/bulk/words")
async def bulk_create_words(
    words: List[str] = Form(...),
    category_id: Optional[str] = Form(None)
):
    """Create multiple words at once (without audio)"""
    created = []
    for word in words:
        word_id = str(uuid.uuid4())
        await db.execute("""
            INSERT INTO vocabulary_words 
            (id, word, category_id, sample_count, created_at, updated_at)
            VALUES ($1, $2, $3, 0, $4, $4)
            ON CONFLICT (word) DO NOTHING
        """, word_id, word.strip(), category_id, datetime.utcnow())
        created.append({"id": word_id, "word": word})
    
    return {"created": len(created), "words": created}


@router.get("/export/corpus")
async def export_corpus(category_id: Optional[str] = Query(None)):
    """Export all vocabulary as corpus for training"""
    query = """
        SELECT w.word, w.audio_path, w.phonetic, c.name as category
        FROM vocabulary_words w
        LEFT JOIN vocabulary_categories c ON w.category_id = c.id
        WHERE w.audio_path IS NOT NULL
    """
    if category_id:
        query += f" AND w.category_id = '{category_id}'"
    
    words = await db.fetch(query)
    
    # Generate metadata.json format
    metadata = []
    for w in words:
        metadata.append({
            "audio_file": Path(w['audio_path']).name,
            "text": w['word'],
            "category": w['category'],
            "phonetic": w['phonetic']
        })
    
    return {"metadata": metadata, "total": len(metadata)}


# ===========================================
# Statistics
# ===========================================
@router.get("/stats")
async def get_vocabulary_stats():
    """Get vocabulary statistics"""
    total_words = await db.fetchval("SELECT COUNT(*) FROM vocabulary_words")
    words_with_audio = await db.fetchval(
        "SELECT COUNT(*) FROM vocabulary_words WHERE audio_path IS NOT NULL"
    )
    total_phrases = await db.fetchval("SELECT COUNT(*) FROM vocabulary_phrases")
    total_categories = await db.fetchval("SELECT COUNT(*) FROM vocabulary_categories")
    total_duration = await db.fetchval(
        "SELECT COALESCE(SUM(duration_seconds), 0) FROM vocabulary_words"
    ) or 0
    
    return {
        "total_words": total_words,
        "words_with_audio": words_with_audio,
        "words_without_audio": total_words - words_with_audio,
        "total_phrases": total_phrases,
        "total_categories": total_categories,
        "total_audio_duration_minutes": total_duration / 60,
        "coverage_percent": (words_with_audio / total_words * 100) if total_words > 0 else 0
    }
