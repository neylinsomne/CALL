"""
Sentiment Analysis API Router
Provides endpoints for sentiment metrics: NPS, CSAT, CES, emotion rubrics
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import random

router = APIRouter(prefix="/sentiment", tags=["Sentiment Analysis"])


# ===========================================
# Models
# ===========================================

class EmotionData(BaseModel):
    emotion: str
    confidence: float
    timestamp: float

class SentimentScore(BaseModel):
    score: float
    label: str  # positive, negative, neutral
    confidence: float

class NPSData(BaseModel):
    score: int  # -100 to 100
    promoters: float
    passives: float
    detractors: float

class CSATData(BaseModel):
    score: float  # 1-5
    distribution: Dict[int, int]  # rating -> count

class CESData(BaseModel):
    score: float  # 1-7, lower is better
    effort_levels: Dict[str, int]

class VocalRubric(BaseModel):
    tone: float  # 0-100
    pace: float
    clarity: float
    energy: float

class LinguisticRubric(BaseModel):
    politeness: float  # 0-100
    empathy: float
    professionalism: float
    resolution_focus: float

class BehavioralRubric(BaseModel):
    patience: float  # 0-100
    engagement: float
    frustration_tolerance: float
    rapport: float

class CallSentimentAnalysis(BaseModel):
    call_id: str
    overall_sentiment: SentimentScore
    emotion_timeline: List[EmotionData]
    emotion_summary: Dict[str, float]
    vocal_rubric: VocalRubric
    linguistic_rubric: LinguisticRubric
    behavioral_rubric: BehavioralRubric
    nps_prediction: int
    csat_prediction: float


# ===========================================
# Emotion Labels
# ===========================================

EMOTIONS = {
    "happy": {"label": "Feliz", "valence": 1.0},
    "satisfied": {"label": "Satisfecho", "valence": 0.8},
    "neutral": {"label": "Neutral", "valence": 0.0},
    "frustrated": {"label": "Frustrado", "valence": -0.6},
    "angry": {"label": "Enojado", "valence": -1.0},
    "sad": {"label": "Triste", "valence": -0.7}
}


# ===========================================
# Mock Data Generation
# ===========================================

def generate_mock_metrics():
    """Generate mock sentiment metrics for demo"""
    return {
        "nps": {
            "score": random.randint(30, 60),
            "promoters": random.randint(50, 65),
            "passives": random.randint(20, 30),
            "detractors": random.randint(10, 20)
        },
        "csat": {
            "score": round(random.uniform(4.2, 4.8), 2),
            "distribution": {
                5: random.randint(50, 70),
                4: random.randint(20, 35),
                3: random.randint(5, 15),
                2: random.randint(2, 8),
                1: random.randint(1, 5)
            }
        },
        "ces": {
            "score": round(random.uniform(2.0, 3.5), 2),
            "effort_levels": {
                "very_easy": random.randint(35, 50),
                "easy": random.randint(25, 40),
                "neutral": random.randint(10, 20),
                "difficult": random.randint(5, 15),
                "very_difficult": random.randint(1, 5)
            }
        },
        "pta_ratio": round(random.uniform(2.5, 5.0), 2),
        "emotion_distribution": {
            "happy": random.randint(30, 45),
            "neutral": random.randint(35, 50),
            "frustrated": random.randint(10, 20),
            "angry": random.randint(2, 8),
            "sad": random.randint(1, 5)
        },
        "rubrics": {
            "vocal": {
                "tone": random.randint(65, 85),
                "pace": random.randint(60, 80),
                "clarity": random.randint(75, 95),
                "energy": random.randint(60, 80)
            },
            "linguistic": {
                "politeness": random.randint(75, 95),
                "empathy": random.randint(65, 85),
                "professionalism": random.randint(80, 98),
                "resolution_focus": random.randint(70, 90)
            },
            "behavioral": {
                "patience": random.randint(65, 85),
                "engagement": random.randint(70, 90),
                "frustration_tolerance": random.randint(60, 80),
                "rapport": random.randint(65, 85)
            }
        }
    }


def analyze_call_sentiment(transcript: List[Dict], audio_features: Optional[Dict] = None) -> Dict:
    """
    Analyze sentiment from call transcript and audio features
    Returns comprehensive sentiment analysis with rubrics
    """
    # Mock analysis - in production, use ML models
    emotions = list(EMOTIONS.keys())
    
    # Generate emotion timeline
    timeline = []
    for i in range(0, 300, 30):  # Every 30 seconds for 5 minutes
        emotion = random.choice(emotions)
        timeline.append({
            "emotion": emotion,
            "confidence": round(random.uniform(0.6, 0.95), 2),
            "timestamp": i
        })
    
    # Calculate summary
    emotion_counts = {e: 0 for e in emotions}
    for point in timeline:
        emotion_counts[point["emotion"]] += 1
    total = len(timeline)
    summary = {e: round(c / total * 100, 1) for e, c in emotion_counts.items()}
    
    # Calculate overall sentiment
    positive = summary.get("happy", 0) + summary.get("satisfied", 0)
    negative = summary.get("angry", 0) + summary.get("frustrated", 0) + summary.get("sad", 0)
    
    if positive > negative + 20:
        label = "positive"
        score = round(random.uniform(0.5, 1.0), 2)
    elif negative > positive + 20:
        label = "negative"
        score = round(random.uniform(-1.0, -0.3), 2)
    else:
        label = "neutral"
        score = round(random.uniform(-0.2, 0.3), 2)
    
    return {
        "overall_sentiment": {
            "score": score,
            "label": label,
            "confidence": round(random.uniform(0.7, 0.95), 2)
        },
        "emotion_timeline": timeline,
        "emotion_summary": summary,
        "vocal_rubric": {
            "tone": random.randint(60, 90),
            "pace": random.randint(55, 85),
            "clarity": random.randint(70, 95),
            "energy": random.randint(55, 85)
        },
        "linguistic_rubric": {
            "politeness": random.randint(70, 95),
            "empathy": random.randint(60, 90),
            "professionalism": random.randint(75, 98),
            "resolution_focus": random.randint(65, 90)
        },
        "behavioral_rubric": {
            "patience": random.randint(60, 90),
            "engagement": random.randint(65, 90),
            "frustration_tolerance": random.randint(55, 85),
            "rapport": random.randint(60, 85)
        },
        "nps_prediction": random.randint(6, 10),
        "csat_prediction": round(random.uniform(3.5, 5.0), 1)
    }


# ===========================================
# API Endpoints
# ===========================================

@router.get("/metrics")
async def get_sentiment_metrics():
    """Get overall sentiment metrics for the dashboard"""
    return generate_mock_metrics()


@router.get("/metrics/nps")
async def get_nps_details():
    """Get detailed NPS breakdown and trends"""
    base = generate_mock_metrics()["nps"]
    
    # Generate trend data
    trend = []
    for i in range(7):
        date = (datetime.now() - timedelta(days=6-i)).strftime("%Y-%m-%d")
        trend.append({
            "date": date,
            "score": random.randint(30, 60)
        })
    
    return {
        **base,
        "trend": trend,
        "benchmark": 45,  # Industry benchmark
        "goal": 50
    }


@router.get("/metrics/csat")
async def get_csat_details():
    """Get detailed CSAT breakdown and trends"""
    base = generate_mock_metrics()["csat"]
    
    trend = []
    for i in range(7):
        date = (datetime.now() - timedelta(days=6-i)).strftime("%Y-%m-%d")
        trend.append({
            "date": date,
            "score": round(random.uniform(4.2, 4.8), 2)
        })
    
    return {
        **base,
        "trend": trend,
        "benchmark": 4.5,
        "goal": 4.7
    }


@router.get("/metrics/ces")
async def get_ces_details():
    """Get detailed CES (Customer Effort Score) breakdown"""
    return {
        **generate_mock_metrics()["ces"],
        "benchmark": 3.0,
        "goal": 2.5  # Lower is better
    }


@router.get("/rubrics")
async def get_rubrics():
    """Get sentiment rubrics (vocal, linguistic, behavioral)"""
    return generate_mock_metrics()["rubrics"]


@router.post("/analyze/call/{call_id}")
async def analyze_call(call_id: str, transcript: Optional[List[Dict]] = None):
    """
    Analyze sentiment for a specific call
    Returns full sentiment analysis with emotion timeline and rubrics
    """
    # In production, fetch transcript from database and analyze
    analysis = analyze_call_sentiment(transcript or [])
    
    return {
        "call_id": call_id,
        "analyzed_at": datetime.now().isoformat(),
        **analysis
    }


@router.get("/emotions")
async def get_emotion_definitions():
    """Get emotion definitions and labels"""
    return EMOTIONS


@router.get("/trends/emotions")
async def get_emotion_trends():
    """Get emotion distribution trends over time"""
    trends = []
    emotions = ["happy", "neutral", "frustrated", "angry", "sad"]
    
    for i in range(7):
        date = (datetime.now() - timedelta(days=6-i)).strftime("%Y-%m-%d")
        entry = {"date": date}
        remaining = 100
        for j, emotion in enumerate(emotions[:-1]):
            val = random.randint(5, min(remaining - len(emotions) + j + 1, 50))
            entry[emotion] = val
            remaining -= val
        entry[emotions[-1]] = remaining
        trends.append(entry)
    
    return trends


@router.get("/fcr-impact")
async def get_fcr_sentiment_impact():
    """Get First Call Resolution impact on sentiment"""
    return {
        "resolved": {
            "avg_sentiment": round(random.uniform(0.6, 0.9), 2),
            "avg_csat": round(random.uniform(4.3, 4.8), 1),
            "count": random.randint(100, 150)
        },
        "escalated": {
            "avg_sentiment": round(random.uniform(-0.4, 0.1), 2),
            "avg_csat": round(random.uniform(2.8, 3.5), 1),
            "count": random.randint(10, 30)
        }
    }
