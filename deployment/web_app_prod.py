#!/usr/bin/env python3
"""
Production-ready web server configuration for MP4 Banner Optimizer.
This is the production version with proper error handling and security.
"""

import os
import json
import uuid
import threading
import time
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename

# Import application modules
from mp4_optimizer.ffmpeg_config import get_ffmpeg_paths, is_ffmpeg_working
from mp4_optimizer.probe import probe_video
from mp4_optimizer.ladder import OptimizationLadder
from mp4_optimizer.encoder import FFmpegEncoder, get_file_size_kb
from mp4_optimizer.report import OptimizationReport
from mp4_optimizer.config import PRESETS, RESOLUTION_LADDER

# Configuration
class Config:
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    UPLOAD_FOLDER = 'uploads'
    OUTPUT_FOLDER = 'outputs'
    REPORT_FOLDER = 'reports'
    ALLOWED_EXTENSIONS = {'mp4'}

    @staticmethod
    def init_app(app):
        # Create required directories
        for folder in [Config.UPLOAD_FOLDER, Config.OUTPUT_FOLDER, Config.REPORT_FOLDER]:
            Path(folder).mkdir(exist_ok=True)

app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)

# Global storage for jobs
jobs = {}
jobs_lock = threading.Lock()


class OptimizationJob:
    """Represents an optimization job with production-ready features."""

    def __init__(self, job_id, input_path, output_path, report_path, options):
        self.job_id = job_id
        self.input_path = input_path
        self.output_path = output_path
        self.report_path = report_path
        self.options = options
        self.status = 'pending'
        self.progress = 0
        self.current_step = ''
        self.result = None
        self.error = None
        self.source_info = None
        self.created_at = time.time()
        self.started_at = None
        self.completed_at = None

    def update_progress(self, progress, step):
        """Thread-safe progress update."""
        with jobs_lock:
            self.progress = progress
            self.current_step = step
            jobs[self.job_id] = self


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def run_optimization(job_id):
    """Run optimization in background thread with production error handling."""
    job = jobs.get(job_id)
    if not job:
        print(f"ERROR: Job {job_id} not found")
        return

    try:
        job.status = 'running'
        job.started_at = time.time()
        job.update_progress(5, 'Initializing...')

        # Check FFmpeg availability
        if not is_ffmpeg_working():
            raise RuntimeError("FFmpeg is not available or not working. Please check server configuration.")

        # Get detected FFmpeg paths
        ffmpeg_path, ffprobe_path = get_ffmpeg_paths()

        # Probe source video
        source_info = probe_video(job.input_path, ffprobe_path=ffprobe_path)
        job.source_info = source_info

        # Determine target size
        max_kb = job.options.get('max_kb')
        if not max_kb:
            preset = job.options.get('preset', 'med')
            max_kb = PRESETS[preset]

        # Parse options
        keep_audio = job.options.get('keep_audio', False)
        fit_mode = job.options.get('fit_mode', 'crop')

        # Parse custom resolution ladder if provided
        resolution_ladder = job.options.get('resolution_ladder')
        if resolution_ladder:
            resolution_ladder = [r.strip() for r in resolution_ladder.split(',')]

        job.update_progress(15, 'Starting optimization...')

        # Run optimization
        encoder = FFmpegEncoder(ffmpeg_path=ffmpeg_path, ffprobe_path=ffprobe_path)
        ladder = OptimizationLadder(encoder)

        result = ladder.optimize(
            input_path=job.input_path,
            output_path=job.output_path,
            max_kb=max_kb,
            keep_audio=keep_audio,
            fit_mode=fit_mode,
            resolution_ladder=resolution_ladder
        )

        # Generate report
        job.update_progress(95, 'Generating report...')
        report = OptimizationReport()
        report.generate(
            input_file=job.input_path,
            source_info=source_info,
            target_max_kb=max_kb,
            result=result,
            output_file=job.output_path
        )
        report.save(job.report_path)

        # Update job with result
        job.result = {
            'status': result.get('status'),
            'final_size_kb': result.get('final_size_kb'),
            'final_resolution': result.get('final_resolution'),
            'iterations': result.get('iterations', []),
            'report_data': report.report_data
        }

        job.status = 'completed'
        job.completed_at = time.time()
        job.update_progress(100, 'Optimization complete')

        print(f"Job {job_id} completed: {result.get('status')}")

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR in job {job_id}: {str(e)}")
        print(f"Traceback: {error_details}")

        job.status = 'failed'
        job.error = str(e)
        job.update_progress(0, f'Error: {str(e)}')


def cleanup_old_files():
    """Clean up old files older than 1 hour."""
    import shutil
    import time

    current_time = time.time()
    max_age = 3600  # 1 hour

    for folder in [app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER'], app.config['REPORT_FOLDER']]:
        folder_path = Path(folder)
        if folder_path.exists():
            for file_path in folder_path.glob('*'):
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age:
                        try:
                            file_path.unlink()
                            print(f"Cleaned up old file: {file_path.name}")
                        except Exception as e:
                            print(f"Error cleaning up {file_path.name}: {e}")


# Routes

@app.route('/')
def index():
    """Main page."""
    return render_template('index.html')


@app.route('/api/presets', methods=['GET'])
def get_presets():
    """Get available presets."""
    return jsonify(PRESETS)


@app.route('/api/resolutions', methods=['GET'])
def get_resolutions():
    """Get available resolutions."""
    return jsonify(RESOLUTION_LADDER)


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload video file for optimization."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Only MP4 files are supported'}), 400

    # Generate unique job ID
    job_id = str(uuid.uuid4())

    # Save uploaded file
    filename = secure_filename(f"{job_id}_{file.filename}")
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(input_path)

    # Create output and report paths
    output_filename = f"{job_id}_optimized.mp4"
    report_filename = f"{job_id}_report.json"

    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
    report_path = os.path.join(app.config['REPORT_FOLDER'], report_filename)

    # Get optimization options
    options = {
        'preset': request.form.get('preset', 'med'),
        'max_kb': int(request.form.get('max_kb')) if request.form.get('max_kb') else None,
        'fit_mode': request.form.get('fit_mode', 'crop'),
        'keep_audio': request.form.get('keep_audio') == 'true',
        'resolution_ladder': request.form.get('resolution_ladder')
    }

    # Create job
    job = OptimizationJob(job_id, input_path, output_path, report_path, options)

    with jobs_lock:
        jobs[job_id] = job

    # Start optimization in background thread
    thread = threading.Thread(target=run_optimization, args=(job_id,))
    thread.daemon = True
    thread.start()

    return jsonify({
        'job_id': job_id,
        'message': 'File uploaded successfully',
        'filename': file.filename
    })


@app.route('/api/status/<job_id>', methods=['GET'])
def get_status(job_id):
    """Get job status."""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    job = jobs[job_id]

    response = {
        'job_id': job_id,
        'status': job.status,
        'progress': job.progress,
        'current_step': job.current_step,
        'error': job.error
    }

    # Add timing info
    if job.created_at:
        response['created_at'] = job.created_at
    if job.started_at:
        response['started_at'] = job.started_at
    if job.completed_at:
        response['completed_at'] = job.completed_at
        response['duration'] = job.completed_at - job.started_at if job.started_at else 0

    # Add source info if available
    if job.source_info:
        response['source_info'] = {
            'filename': os.path.basename(job.input_path),
            'size_kb': job.source_info['size_kb'],
            'resolution': job.source_info['resolution'],
            'duration_s': job.source_info['duration_s'],
            'fps': job.source_info['fps'],
            'has_audio': job.source_info['has_audio']
        }

    # Add result if completed
    if job.result:
        response['result'] = {
            'status': job.result['status'],
            'final_size_kb': job.result['final_size_kb'],
            'final_resolution': job.result['final_resolution'],
            'iterations': job.result['iterations'],
            'report': job.result['report_data']
        }

    return jsonify(response)


@app.route('/api/download/<job_id>', methods=['GET'])
def download_file(job_id):
    """Download optimized file."""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    job = jobs[job_id]
    if job.status != 'completed' or not os.path.exists(job.output_path):
        return jsonify({'error': 'File not ready'}), 404

    return send_file(
        job.output_path,
        as_attachment=True,
        download_name=f"optimized_{os.path.basename(job.input_path)}"
    )


@app.route('/api/report/<job_id>', methods=['GET'])
def download_report(job_id):
    """Download optimization report."""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    job = jobs[job_id]
    if job.status != 'completed' or not os.path.exists(job.report_path):
        return jsonify({'error': 'Report not ready'}), 404

    return send_file(
        job.report_path,
        as_attachment=True,
        download_name=f"report_{job_id}.json"
    )


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for load balancers."""
    return jsonify({'status': 'healthy', 'timestamp': time.time()})


@app.route('/stats', methods=['GET'])
def get_stats():
    """Get basic statistics."""
    with jobs_lock:
        total_jobs = len(jobs)
        active_jobs = sum(1 for job in jobs.values() if job.status == 'running')
        completed_jobs = sum(1 for job in jobs.values() if job.status == 'completed')
        failed_jobs = sum(1 for job in jobs.values() if job.status == 'failed')

    return jsonify({
        'total_jobs': total_jobs,
        'active_jobs': active_jobs,
        'completed_jobs': completed_jobs,
        'failed_jobs': failed_jobs,
        'timestamp': time.time()
    })


if __name__ == '__main__':
    # Production configuration
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'

    print(f"Starting MP4 Banner Optimizer - Production Mode")
    print(f"Port: {port}")
    print(f"Debug mode: {debug}")

    # Start periodic cleanup
    if not debug:
        cleanup_thread = threading.Thread(target=lambda: [
            time.sleep(3600),  # Run every hour
            cleanup_old_files()
        ], daemon=True)
        cleanup_thread.start()

    app.run(debug=debug, host='0.0.0.0', port=port)