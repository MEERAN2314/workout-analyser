#!/usr/bin/env python3
"""
Celery worker script for background video processing
Run with: python celery_worker.py
"""
import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app.services.celery_app import celery_app

if __name__ == '__main__':
    # Start the Celery worker
    celery_app.worker_main([
        'worker',
        '--loglevel=info',
        '--concurrency=2',
        '--queues=default,video_processing,report_generation'
    ])