from celery import current_task
from app.services.celery_app import celery_app
from app.services.video_processor import video_processor
from app.core.database import get_database
from bson import ObjectId
import logging
import asyncio

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name='app.services.celery_tasks.process_video_task')
def process_video_task(self, session_id: str, video_url: str, exercise_name: str, user_id: str):
    """
    Celery task to process uploaded video with comprehensive analysis
    """
    try:
        logger.info(f"🚀 CELERY TASK STARTED - Session: {session_id}, Exercise: {exercise_name}")
        logger.info(f"   Video URL: {video_url}")
        logger.info(f"   User ID: {user_id}")
        
        # Update task status immediately
        self.update_state(
            state='PROGRESS',
            meta={'progress': 5, 'status': 'Task started - initializing video analysis...'}
        )
        
        # Process video using async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            logger.info(f"📥 Starting video download and processing...")
            
            # Update progress
            self.update_state(
                state='PROGRESS',
                meta={'progress': 10, 'status': 'Downloading video for analysis...'}
            )
            
            # Process the video
            result = loop.run_until_complete(
                video_processor.process_video_from_url(video_url, exercise_name, session_id)
            )
            
            logger.info(f"✅ Video processing completed successfully")
            
            # Update progress
            self.update_state(
                state='PROGRESS',
                meta={'progress': 90, 'status': 'Saving analysis results...'}
            )
            
            # Save results to database
            loop.run_until_complete(
                _save_analysis_results(session_id, result)
            )
            
            # Generate summary
            summary = loop.run_until_complete(
                video_processor.generate_analysis_summary(result)
            )
            
            logger.info(f"🎉 Video processing completed for session {session_id}")
            
            return {
                'status': 'completed',
                'progress': 100,
                'session_id': session_id,
                'results': result.to_dict(),
                'summary': summary
            }
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"❌ Error in video processing task: {e}")
        
        # Update database with error status
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                _update_session_error(session_id, str(e))
            )
            loop.close()
        except:
            pass
        
        self.update_state(
            state='FAILURE',
            meta={
                'error': str(e), 
                'session_id': session_id,
                'exc_type': type(e).__name__
            }
        )
        raise Exception(f"Video processing failed: {str(e)}")

@celery_app.task(bind=True, name='app.services.celery_tasks.generate_report_task')
def generate_report_task(self, session_id: str):
    """
    Celery task to generate PDF report for analysis results
    """
    try:
        logger.info(f"Starting report generation for session {session_id}")
        
        self.update_state(
            state='PROGRESS',
            meta={'progress': 0, 'status': 'Generating PDF report...'}
        )
        
        # TODO: Implement PDF report generation with ReportLab
        # This is a placeholder for now
        
        self.update_state(
            state='PROGRESS',
            meta={'progress': 100, 'status': 'Report generated successfully'}
        )
        
        return {
            'status': 'completed',
            'session_id': session_id,
            'report_url': f'/recording/report/{session_id}/download'
        }
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        self.update_state(
            state='FAILURE',
            meta={'error': str(e), 'session_id': session_id}
        )
        raise

async def _save_analysis_results(session_id: str, result):
    """Save analysis results to database"""
    try:
        db = get_database()
        if db is not None:
            # Convert session_id to ObjectId format
            object_id = ObjectId(session_id.replace('-', '')[:24])
            
            # Update workout session with results
            update_data = result.to_dict()
            
            await db.workouts.update_one(
                {"_id": object_id},
                {"$set": update_data}
            )
            
            logger.info(f"Analysis results saved for session {session_id}")
        
    except Exception as e:
        logger.error(f"Error saving analysis results: {e}")
        raise

async def _update_session_error(session_id: str, error_message: str):
    """Update session with error status"""
    try:
        db = get_database()
        if db is not None:
            object_id = ObjectId(session_id.replace('-', '')[:24])
            
            await db.workouts.update_one(
                {"_id": object_id},
                {
                    "$set": {
                        "status": "failed",
                        "error_message": error_message,
                        "analysis_completed": False
                    }
                }
            )
            
    except Exception as e:
        logger.error(f"Error updating session error: {e}")

# Task monitoring functions
@celery_app.task(name='app.services.celery_tasks.get_task_status')
def get_task_status(task_id: str):
    """Get status of a Celery task"""
    result = celery_app.AsyncResult(task_id)
    
    if result.state == 'PENDING':
        response = {
            'state': result.state,
            'progress': 0,
            'status': 'Task is waiting to be processed...'
        }
    elif result.state == 'PROGRESS':
        response = {
            'state': result.state,
            'progress': result.info.get('progress', 0),
            'status': result.info.get('status', 'Processing...')
        }
    elif result.state == 'SUCCESS':
        response = {
            'state': result.state,
            'progress': 100,
            'status': 'Task completed successfully',
            'result': result.info
        }
    else:  # FAILURE
        response = {
            'state': result.state,
            'progress': 0,
            'status': 'Task failed',
            'error': str(result.info)
        }
    
    return response