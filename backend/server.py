from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
import asyncio

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Enhanced dictionary database with Bengali translations
OFFLINE_DICTIONARY = {
    # Common words
    "hello": {
        "bengali": "হ্যালো / নমস্কার",
        "pronunciation": "hæloʊ",
        "definition": "A greeting; an expression of welcome or salutation",
        "part_of_speech": "interjection",
        "examples": [
            "Hello, how are you today?",
            "She said hello to everyone at the party."
        ]
    },
    "book": {
        "bengali": "বই / পুস্তক",
        "pronunciation": "bʊk",
        "definition": "A written or printed work consisting of pages bound together",
        "part_of_speech": "noun",
        "examples": [
            "I love reading a good book before bed.",
            "The library has thousands of books."
        ]
    },
    "water": {
        "bengali": "পানি / জল",
        "pronunciation": "ˈwɔːtər",
        "definition": "A clear, colorless, odorless liquid essential for life",
        "part_of_speech": "noun",
        "examples": [
            "Drink plenty of water to stay hydrated.",
            "The water in the lake is crystal clear."
        ]
    },
    "food": {
        "bengali": "খাবার / আহার",
        "pronunciation": "fuːd",
        "definition": "Any nutritious substance consumed to sustain life and growth",
        "part_of_speech": "noun",
        "examples": [
            "The food at this restaurant is delicious.",
            "We need to buy food for dinner."
        ]
    },
    "home": {
        "bengali": "বাড়ি / ঘর",
        "pronunciation": "hoʊm",
        "definition": "The place where one lives permanently",
        "part_of_speech": "noun",
        "examples": [
            "There's no place like home.",
            "I'm going home after work."
        ]
    },
    "love": {
        "bengali": "ভালোবাসা / প্রেম",
        "pronunciation": "lʌv",
        "definition": "An intense feeling of deep affection",
        "part_of_speech": "noun/verb",
        "examples": [
            "I love spending time with my family.",
            "Love conquers all obstacles."
        ]
    },
    "friend": {
        "bengali": "বন্ধু / বান্ধব",
        "pronunciation": "frend",
        "definition": "A person whom one knows and with whom one has a bond of mutual affection",
        "part_of_speech": "noun",
        "examples": [
            "She is my best friend since childhood.",
            "A true friend is always there for you."
        ]
    },
    "school": {
        "bengali": "স্কুল / বিদ্যালয়",
        "pronunciation": "skuːl",
        "definition": "An institution for educating children",
        "part_of_speech": "noun",
        "examples": [
            "Children go to school to learn.",
            "My school has excellent teachers."
        ]
    },
    "work": {
        "bengali": "কাজ / শ্রম",
        "pronunciation": "wɜːrk",
        "definition": "Activity involving mental or physical effort to achieve a purpose",
        "part_of_speech": "noun/verb",
        "examples": [
            "I have a lot of work to finish today.",
            "Hard work pays off in the end."
        ]
    },
    "happy": {
        "bengali": "খুশি / আনন্দিত",
        "pronunciation": "ˈhæpi",
        "definition": "Feeling or showing pleasure or contentment",
        "part_of_speech": "adjective",
        "examples": [
            "I am happy to see you again.",
            "The children look happy playing in the park."
        ]
    },
    "beautiful": {
        "bengali": "সুন্দর / রূপবান",
        "pronunciation": "ˈbjuːtɪfəl",
        "definition": "Pleasing the senses or mind aesthetically",
        "part_of_speech": "adjective",
        "examples": [
            "The sunset is absolutely beautiful.",
            "She has a beautiful voice."
        ]
    },
    "time": {
        "bengali": "সময় / কাল",
        "pronunciation": "taɪm",
        "definition": "The indefinite continued progress of existence",
        "part_of_speech": "noun",
        "examples": [
            "Time flies when you're having fun.",
            "What time is it now?"
        ]
    },
    "money": {
        "bengali": "টাকা / অর্থ",
        "pronunciation": "ˈmʌni",
        "definition": "A current medium of exchange in the form of coins and banknotes",
        "part_of_speech": "noun",
        "examples": [
            "Money can't buy happiness.",
            "I need to save money for my vacation."
        ]
    },
    "family": {
        "bengali": "পরিবার / কুটুম্ব",
        "pronunciation": "ˈfæməli",
        "definition": "A group consisting of parents and children living together",
        "part_of_speech": "noun",
        "examples": [
            "Family is the most important thing in life.",
            "We're having a family dinner tonight."
        ]
    },
    "health": {
        "bengali": "স্বাস্থ্য / আরোগ্য",
        "pronunciation": "helθ",
        "definition": "The state of being free from illness or injury",
        "part_of_speech": "noun",
        "examples": [
            "Good health is more valuable than wealth.",
            "Regular exercise improves your health."
        ]
    }
}

# Define Models
class TranslationRequest(BaseModel):
    word: str

class Translation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    word: str
    bengaliTranslation: str
    pronunciation: str
    definition: str
    examples: List[str]
    partOfSpeech: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str = "offline"  # offline or ai

class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

# AI Translation function using Emergent LLM
async def get_ai_translation(word: str) -> Optional[dict]:
    """Get AI-powered translation with enhanced context"""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        # Initialize LLM chat
        chat = LlmChat(
            api_key=os.environ.get('EMERGENT_LLM_KEY'),
            session_id=f"dictionary-{uuid.uuid4()}",
            system_message="""You are an expert English to Bengali dictionary and language assistant. 
            Provide accurate translations with context, pronunciation guide, definitions, and examples.
            Always respond in JSON format with these exact fields:
            {
                "bengali": "Bengali translation (include multiple variations if applicable)",
                "pronunciation": "IPA pronunciation guide",
                "definition": "Clear English definition",
                "part_of_speech": "grammatical category",
                "examples": ["example sentence 1", "example sentence 2"]
            }
            
            For Bengali translations, use proper Bengali script and include common variations.
            Keep examples practical and commonly used."""
        ).with_model("openai", "gpt-4o-mini")
        
        # Create user message
        user_message = UserMessage(
            text=f"Translate the English word '{word}' to Bengali. Provide a comprehensive dictionary entry with pronunciation, definition, part of speech, and 2-3 practical example sentences."
        )
        
        # Get AI response
        response = await chat.send_message(user_message)
        
        # Parse JSON response
        import json
        try:
            ai_data = json.loads(response)
            return ai_data
        except json.JSONDecodeError:
            # If response is not JSON, try to extract information manually
            return None
            
    except Exception as e:
        logging.error(f"AI translation error: {e}")
        return None

# API Routes
@api_router.get("/")
async def root():
    return {"message": "English to Bengali AI Dictionary API"}

@api_router.post("/translate")
async def translate_word(request: TranslationRequest):
    """Translate English word to Bengali with AI enhancement"""
    word = request.word.lower().strip()
    
    if not word:
        raise HTTPException(status_code=400, detail="Word cannot be empty")
    
    try:
        # First, check offline dictionary
        if word in OFFLINE_DICTIONARY:
            offline_data = OFFLINE_DICTIONARY[word]
            translation = Translation(
                word=request.word,
                bengaliTranslation=offline_data["bengali"],
                pronunciation=offline_data["pronunciation"],
                definition=offline_data["definition"],
                examples=offline_data["examples"],
                partOfSpeech=offline_data["part_of_speech"],
                source="offline"
            )
            
            # Save to database
            await db.translations.insert_one(translation.dict())
            return translation.dict()
        
        # If not in offline dictionary, try AI translation
        ai_result = await get_ai_translation(word)
        
        if ai_result:
            translation = Translation(
                word=request.word,
                bengaliTranslation=ai_result.get("bengali", "অনুবাদ পাওয়া যায়নি"),
                pronunciation=ai_result.get("pronunciation", ""),
                definition=ai_result.get("definition", "No definition available"),
                examples=ai_result.get("examples", []),
                partOfSpeech=ai_result.get("part_of_speech", "unknown"),
                source="ai"
            )
            
            # Save to database
            await db.translations.insert_one(translation.dict())
            return translation.dict()
        
        # Fallback: Basic translation attempt
        translation = Translation(
            word=request.word,
            bengaliTranslation=f"'{word}' এর বাংলা অনুবাদ",
            pronunciation="",
            definition=f"Translation for the word '{word}'",
            examples=[f"Example with {word}"],
            partOfSpeech="unknown",
            source="fallback"
        )
        
        return translation.dict()
        
    except Exception as e:
        logging.error(f"Translation error for word '{word}': {e}")
        raise HTTPException(status_code=500, detail="Translation service temporarily unavailable")

@api_router.get("/translations")
async def get_recent_translations(limit: int = 50):
    """Get recent translations from database"""
    try:
        translations = await db.translations.find().sort("timestamp", -1).limit(limit).to_list(limit)
        return [Translation(**translation) for translation in translations]
    except Exception as e:
        logging.error(f"Error fetching translations: {e}")
        raise HTTPException(status_code=500, detail="Unable to fetch translations")

@api_router.get("/dictionary/stats")
async def get_dictionary_stats():
    """Get dictionary usage statistics"""
    try:
        total_translations = await db.translations.count_documents({})
        offline_count = len(OFFLINE_DICTIONARY)
        ai_translations = await db.translations.count_documents({"source": "ai"})
        
        return {
            "total_translations": total_translations,
            "offline_words": offline_count,
            "ai_enhanced_translations": ai_translations,
            "total_unique_words": offline_count + ai_translations
        }
    except Exception as e:
        logging.error(f"Error fetching stats: {e}")
        return {"error": "Unable to fetch statistics"}

# Legacy status check endpoints
@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)