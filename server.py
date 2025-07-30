"""
AI Tutor Backend Server
FastAPI implementation for handling chat requests and file uploads
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import json
from datetime import datetime
import uuid
import asyncio
from pathlib import Path

# Import the distributed memory system
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from memory_api_phase1 import (
    DistributedMemoryAPI, 
    MemorySource, 
    SourceType,
    MemoryLevel
)

# Initialize FastAPI app
app = FastAPI(title="AI Tutor API", version="1.0.0")

# Configure CORS for GitHub Pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:*",
        "https://*.github.io",
        "https://*.githubpages.io",
        # Add your specific GitHub Pages URL here
        # "https://yourusername.github.io"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize distributed memory
memory_api = DistributedMemoryAPI()

# Request/Response Models
class ChatRequest(BaseModel):
    message: str
    session_id: str
    context: Optional[Dict[str, Any]] = {}
    mood: Optional[str] = "neutral"

class ChatResponse(BaseModel):
    response: str
    context: Dict[str, Any]
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    memory_active: bool

# Ethical tutoring responses based on query type
TUTOR_RESPONSES = {
    "homework_help": [
        "I can help guide you through this. What specific part are you finding challenging?",
        "Let's break this down step by step. What have you tried so far?",
        "Good question! Instead of giving you the answer, let me ask: what do you think the first step should be?"
    ],
    "concept_explanation": [
        "Let me help you understand this concept. Can you tell me what you already know about it?",
        "That's a great topic to explore. What aspects of it are unclear to you?",
        "I'll guide you to discover this yourself. What patterns do you notice?"
    ],
    "test_prep": [
        "Test preparation is about understanding, not memorization. What topics worry you most?",
        "Let's create a study strategy together. Which areas do you feel strongest and weakest in?",
        "Good thinking ahead! What type of questions do you typically struggle with?"
    ],
    "focus_help": [
        "Let's try the Pomodoro technique: 25 minutes focused work, then 5 minutes break.",
        "Breaking tasks into smaller pieces can help. What's one small thing we can tackle now?",
        "Sometimes movement helps focus. Take a quick stretch break, then we'll start with something easy."
    ],
    "general": [
        "That's interesting. Can you elaborate on what you're working on?",
        "I'm here to guide your learning journey. What would you like to explore?",
        "Good question! Let's think through this together."
    ]
}

def classify_message(message: str) -> str:
    """Classify the type of help needed based on the message"""
    lower_msg = message.lower()
    
    if any(word in lower_msg for word in ["homework", "assignment", "problem", "solve"]):
        return "homework_help"
    elif any(word in lower_msg for word in ["explain", "understand", "what is", "how does"]):
        return "concept_explanation"
    elif any(word in lower_msg for word in ["test", "exam", "quiz", "study"]):
        return "test_prep"
    elif any(word in lower_msg for word in ["focus", "distracted", "adhd", "concentrate"]):
        return "focus_help"
    else:
        return "general"

def generate_tutor_response(message: str, context: Dict[str, Any], mood: str) -> str:
    """Generate an appropriate tutoring response"""
    message_type = classify_message(message)
    responses = TUTOR_RESPONSES[message_type]
    
    # Select response based on context and mood
    import random
    base_response = random.choice(responses)
    
    # Adjust based on mood
    mood_adjustments = {
        "struggling": " Remember, it's okay to find things difficult. We'll work through this together.",
        "excited": " I love your enthusiasm! Let's dive in!",
        "focused": " Great mindset for learning!",
        "happy": " Wonderful energy! Let's make the most of it!"
    }
    
    if mood in mood_adjustments:
        base_response += mood_adjustments[mood]
    
    return base_response

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check if the API is running and memory system is active"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + 'Z',
        "memory_active": True
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Handle chat messages and return tutoring responses"""
    try:
        # Create memory source
        source = MemorySource(
            type=SourceType.API,
            id="tutor-api",
            session=request.session_id
        )
        
        # Store the message in memory
        memory_api.add_to_working_set(
            session_id=request.session_id,
            key=f"message_{datetime.utcnow().timestamp()}",
            value={
                "user": request.message,
                "mood": request.mood,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Generate response
        response_text = generate_tutor_response(
            request.message, 
            request.context, 
            request.mood
        )
        
        # Update context
        updated_context = request.context.copy()
        updated_context["last_interaction"] = datetime.utcnow().isoformat()
        updated_context["message_count"] = updated_context.get("message_count", 0) + 1
        
        # Store response in memory
        memory_api.add_to_working_set(
            session_id=request.session_id,
            key=f"response_{datetime.utcnow().timestamp()}",
            value={
                "tutor": response_text,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return {
            "response": response_text,
            "context": updated_context,
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    session_id: str = Form(...)
):
    """Handle file uploads and extract content"""
    try:
        # Create upload directory
        upload_dir = Path("uploads") / session_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = upload_dir / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Store file info in memory
        source = MemorySource(
            type=SourceType.API,
            id="tutor-api",
            session=session_id
        )
        
        memory_api.add_to_working_set(
            session_id=session_id,
            key=f"file_{file.filename}",
            value={
                "filename": file.filename,
                "size": len(content),
                "type": file.content_type,
                "path": str(file_path),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Extract text if possible (simplified for demo)
        extracted_text = None
        if file.content_type and "text" in file.content_type:
            extracted_text = content.decode('utf-8', errors='ignore')[:500]
        
        return {
            "success": True,
            "filename": file.filename,
            "size": len(content),
            "extracted_text": extracted_text
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/context/{session_id}")
async def get_context(session_id: str):
    """Retrieve the full context for a session"""
    try:
        context = memory_api.load_context(session_id)
        if not context:
            return {"context": {}, "message": "No context found for this session"}
        
        return {"context": context}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/memory/pattern")
async def save_pattern(
    pattern: Dict[str, Any],
    tags: List[str],
    session_id: str
):
    """Save a learning pattern discovered during tutoring"""
    try:
        source = MemorySource(
            type=SourceType.API,
            id="tutor-api",
            session=session_id
        )
        
        pattern_id = memory_api.save_pattern(
            source=source,
            pattern=pattern,
            tags=tags
        )
        
        return {"pattern_id": pattern_id, "success": True}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Run the server
if __name__ == "__main__":
    import uvicorn
    
    # For local development
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        reload=True
    )
