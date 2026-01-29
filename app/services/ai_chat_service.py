"""
AI Chat Service - LangChain + Gemini 2.0 Flash for workout consultation
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.core.config import settings
from app.core.database import get_database
from bson import ObjectId

logger = logging.getLogger(__name__)

class WorkoutAIChatService:
    """AI-powered workout consultation service"""
    
    def __init__(self):
        # Use Gemini 2.5 Flash - the latest stable model
        # Priority: 2.5-flash > 2.0-flash > fallbacks
        models_to_try = [
            "gemini-2.5-flash",          # Latest stable (June 2025)
            "gemini-2.5-pro",            # More capable 2.5 Pro
            "gemini-2.0-flash",          # Stable 2.0 Flash
            "gemini-flash-latest",       # Latest Flash (any version)
            "gemini-pro-latest"          # Latest Pro (fallback)
        ]
        
        model_name = "gemini-2.5-flash"  # Default to best available
        
        # Use the first model in priority list
        for model in models_to_try:
            try:
                logger.info(f"Attempting to initialize with model: {model}")
                self.llm = ChatGoogleGenerativeAI(
                    model=model,
                    google_api_key=settings.GOOGLE_API_KEY,
                    temperature=0.7,
                    max_tokens=2000,
                    convert_system_message_to_human=True
                )
                model_name = model
                logger.info(f"✅ Successfully initialized with model: {model}")
                break
            except Exception as e:
                logger.warning(f"Failed to initialize with {model}: {e}")
                continue
        
        # If all fail, use default configuration
        if not hasattr(self, 'llm'):
            logger.warning("Using default model configuration")
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=settings.GOOGLE_API_KEY,
                temperature=0.7,
                max_tokens=2000,
                convert_system_message_to_human=True
            )
        
        # System prompt for workout consultation
        self.system_prompt = """You are an expert fitness coach and workout analyst. You help users improve their workouts based on their exercise data and form analysis.

Your expertise includes:
- Exercise form analysis and correction
- Workout programming and progression
- Injury prevention and safety
- Motivation and goal setting
- Performance optimization

Guidelines:
1. Be encouraging and supportive
2. Provide specific, actionable advice
3. Reference the user's actual workout data when available
4. Focus on form quality over quantity
5. Suggest realistic improvements
6. Ask clarifying questions when needed
7. Keep responses concise but informative

When analyzing workout data:
- Comment on rep counts and accuracy scores
- Identify patterns in form feedback
- Suggest specific improvements
- Celebrate progress and achievements
- Provide context-appropriate recommendations

Always prioritize safety and proper form over performance metrics."""

        # Create prompt template
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", "User Context:\n{user_context}\n\nRecent Workouts:\n{workout_context}\n\nUser Question: {user_message}")
        ])
    
    async def start_chat_session(self, user_id: str, workout_id: Optional[str] = None) -> str:
        """Start a new chat session"""
        db = get_database()
        if db is None:
            raise Exception("Database not available")
        
        # Create chat session
        session_data = {
            "user_id": ObjectId(user_id),
            "workout_id": ObjectId(workout_id) if workout_id else None,
            "title": "Workout Consultation",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "message_count": 0,
            "context_workouts": []
        }
        
        result = await db.chat_sessions.insert_one(session_data)
        session_id = str(result.inserted_id)
        
        logger.info(f"Started chat session {session_id} for user {user_id}")
        
        # Send welcome message
        welcome_message = await self._generate_welcome_message(user_id, workout_id)
        await self._save_message(session_id, "assistant", welcome_message, {})
        
        return session_id
    
    async def send_message(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """Send a message and get AI response"""
        db = get_database()
        if db is None:
            raise Exception("Database not available")
        
        # Get session
        session = await db.chat_sessions.find_one({"_id": ObjectId(session_id)})
        if not session:
            raise Exception("Chat session not found")
        
        user_id = str(session["user_id"])
        
        try:
            # Get user context
            user_context = await self._get_user_context(user_id)
            workout_context = await self._get_workout_context(user_id, limit=5)
            
            # Get conversation history
            messages = await self._get_conversation_history(session_id, limit=10)
            
            # Create conversation with memory
            conversation_messages = []
            
            # Add conversation history (system message will be auto-converted)
            for msg in messages:
                if msg["role"] == "user":
                    conversation_messages.append(HumanMessage(content=msg["content"]))
                else:
                    conversation_messages.append(AIMessage(content=msg["content"]))
            
            # Format the current message with context
            # Include system prompt in the first human message for better context
            if len(conversation_messages) == 0:
                # First message - include system prompt
                formatted_message = f"{self.system_prompt}\n\n---\n\nUser Context:\n{user_context}\n\nRecent Workouts:\n{workout_context}\n\nUser Question: {user_message}"
            else:
                # Subsequent messages - just context and question
                formatted_message = f"User Context:\n{user_context}\n\nRecent Workouts:\n{workout_context}\n\nUser Question: {user_message}"
            
            conversation_messages.append(HumanMessage(content=formatted_message))
            
            # Generate AI response
            response = await self.llm.ainvoke(conversation_messages)
            ai_response = response.content
            
            # Save messages
            await self._save_message(session_id, "user", user_message, {})
            context_used = {
                "user_context": user_context,
                "workout_context": workout_context
            }
            await self._save_message(session_id, "assistant", ai_response, context_used)
            
            # Update session
            await db.chat_sessions.update_one(
                {"_id": ObjectId(session_id)},
                {
                    "$set": {"updated_at": datetime.utcnow()},
                    "$inc": {"message_count": 2}
                }
            )
            
            logger.info(f"AI response generated for session {session_id}")
            
            return {
                "response": ai_response,
                "context_used": context_used,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            
            # Save user message even if AI fails
            await self._save_message(session_id, "user", user_message, {})
            
            # Return error response
            error_response = "I'm sorry, I'm having trouble processing your request right now. Please try again in a moment."
            await self._save_message(session_id, "assistant", error_response, {"error": str(e)})
            
            return {
                "response": error_response,
                "error": True,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_chat_history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get chat history for a session"""
        db = get_database()
        if db is None:
            raise Exception("Database not available")
        
        messages = await db.chat_messages.find(
            {"session_id": ObjectId(session_id)}
        ).sort("timestamp", 1).limit(limit).to_list(length=limit)
        
        # Convert ObjectId to string
        for message in messages:
            message["_id"] = str(message["_id"])
            message["session_id"] = str(message["session_id"])
            message["user_id"] = str(message["user_id"])
        
        return messages
    
    async def get_user_chat_sessions(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get user's chat sessions"""
        db = get_database()
        if db is None:
            raise Exception("Database not available")
        
        sessions = await db.chat_sessions.find(
            {"user_id": ObjectId(user_id)}
        ).sort("updated_at", -1).limit(limit).to_list(length=limit)
        
        # Convert ObjectId to string and add last message
        for session in sessions:
            session["_id"] = str(session["_id"])
            session["user_id"] = str(session["user_id"])
            if session.get("workout_id"):
                session["workout_id"] = str(session["workout_id"])
            
            # Get last message
            last_message = await db.chat_messages.find_one(
                {"session_id": session["_id"]},
                sort=[("timestamp", -1)]
            )
            
            if last_message:
                session["last_message"] = {
                    "content": last_message["content"][:100] + "..." if len(last_message["content"]) > 100 else last_message["content"],
                    "role": last_message["role"],
                    "timestamp": last_message["timestamp"]
                }
        
        return sessions
    
    async def delete_chat_session(self, session_id: str, user_id: str) -> bool:
        """Delete a chat session and its messages"""
        db = get_database()
        if db is None:
            raise Exception("Database not available")
        
        # Verify session belongs to user
        session = await db.chat_sessions.find_one({
            "_id": ObjectId(session_id),
            "user_id": ObjectId(user_id)
        })
        
        if not session:
            return False
        
        # Delete messages
        await db.chat_messages.delete_many({"session_id": ObjectId(session_id)})
        
        # Delete session
        result = await db.chat_sessions.delete_one({"_id": ObjectId(session_id)})
        
        logger.info(f"Deleted chat session {session_id}")
        return result.deleted_count > 0
    
    async def _generate_welcome_message(self, user_id: str, workout_id: Optional[str] = None) -> str:
        """Generate a personalized welcome message"""
        try:
            user_context = await self._get_user_context(user_id)
            recent_workouts = await self._get_workout_context(user_id, limit=3)
            
            if workout_id:
                # Specific workout consultation
                db = get_database()
                workout = await db.workouts.find_one({"_id": ObjectId(workout_id)})
                if workout:
                    return f"Hi! I've analyzed your recent {workout['exercise_name'].replace('_', ' ')} workout. I can help you improve your form, suggest progressions, or answer any questions about your performance. What would you like to know?"
            
            if recent_workouts and "No workouts" not in recent_workouts:
                return f"Hello! I'm your AI fitness coach. I can see you've been working out recently - great job! I'm here to help you improve your form, plan your workouts, and reach your fitness goals. What would you like to discuss?"
            else:
                return f"Welcome! I'm your AI fitness coach. I'm here to help you with workout planning, exercise form, and reaching your fitness goals. Whether you're just starting out or looking to improve, I'm here to support you. What can I help you with today?"
                
        except Exception as e:
            logger.error(f"Error generating welcome message: {e}")
            return "Hello! I'm your AI fitness coach. I'm here to help you with your workouts and fitness goals. What can I help you with today?"
    
    async def _get_user_context(self, user_id: str) -> str:
        """Get user profile context for AI"""
        try:
            db = get_database()
            if db is None:
                return "User profile not available"
            
            user = await db.users.find_one({"_id": ObjectId(user_id)})
            if not user:
                return "User profile not found"
            
            context_parts = []
            
            # Basic info
            if user.get("full_name"):
                context_parts.append(f"Name: {user['full_name']}")
            
            if user.get("age"):
                context_parts.append(f"Age: {user['age']}")
            
            if user.get("fitness_level"):
                context_parts.append(f"Fitness Level: {user['fitness_level'].title()}")
            
            if user.get("goals"):
                goals = [goal.replace('_', ' ').title() for goal in user['goals']]
                context_parts.append(f"Goals: {', '.join(goals)}")
            
            # Physical stats
            physical_stats = []
            if user.get("height"):
                physical_stats.append(f"Height: {user['height']} cm")
            if user.get("weight"):
                physical_stats.append(f"Weight: {user['weight']} kg")
            
            if physical_stats:
                context_parts.append(f"Physical Stats: {', '.join(physical_stats)}")
            
            return "\n".join(context_parts) if context_parts else "Basic user profile"
            
        except Exception as e:
            logger.error(f"Error getting user context: {e}")
            return "User context unavailable"
    
    async def _get_workout_context(self, user_id: str, limit: int = 5) -> str:
        """Get recent workout context for AI"""
        try:
            db = get_database()
            if db is None:
                return "Workout history not available"
            
            workouts = await db.workouts.find(
                {"user_id": ObjectId(user_id)}
            ).sort("created_at", -1).limit(limit).to_list(length=limit)
            
            if not workouts:
                return "No workouts found. User is new to the platform."
            
            workout_summaries = []
            for workout in workouts:
                exercise = workout.get("exercise_name", "unknown").replace('_', ' ').title()
                reps = workout.get("total_reps", 0)
                accuracy = workout.get("accuracy_score", 0) * 100
                session_type = workout.get("session_type", "unknown")
                date = workout.get("created_at", datetime.utcnow()).strftime("%Y-%m-%d")
                
                summary = f"- {date}: {exercise} ({session_type}) - {reps} reps, {accuracy:.1f}% accuracy"
                
                # Add form feedback if available
                feedback = workout.get("form_feedback", [])
                if feedback:
                    key_feedback = feedback[:2]  # First 2 feedback items
                    summary += f" | Feedback: {', '.join(key_feedback)}"
                
                workout_summaries.append(summary)
            
            return "\n".join(workout_summaries)
            
        except Exception as e:
            logger.error(f"Error getting workout context: {e}")
            return "Workout context unavailable"
    
    async def _get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation history"""
        try:
            db = get_database()
            if db is None:
                return []
            
            messages = await db.chat_messages.find(
                {"session_id": ObjectId(session_id)}
            ).sort("timestamp", -1).limit(limit).to_list(length=limit)
            
            # Reverse to get chronological order
            messages.reverse()
            
            return messages
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []
    
    async def _save_message(self, session_id: str, role: str, content: str, context_used: Dict[str, Any]):
        """Save a message to the database"""
        try:
            db = get_database()
            if db is None:
                return
            
            # Get session to get user_id
            session = await db.chat_sessions.find_one({"_id": ObjectId(session_id)})
            if not session:
                return
            
            message_data = {
                "session_id": ObjectId(session_id),
                "user_id": session["user_id"],
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow(),
                "context_used": context_used
            }
            
            await db.chat_messages.insert_one(message_data)
            
        except Exception as e:
            logger.error(f"Error saving message: {e}")

# Global instance
ai_chat_service = WorkoutAIChatService()