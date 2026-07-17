#!/usr/bin/env python3
"""
Web interface for mp4-banner-optimizer.
Provides upload, preview, and progress tracking through browser.
"""

import os
import json
import uuid
import threading
import time
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mp4_optimizer.probe import probe_video
from mp4_optimizer.ladder import OptimizationLadder
from mp4_optimizer.encoder import FFmpegEncoder, get_file_size_kb
from mp4_optimizer.report import OptimizationReport
from mp4_optimizer.config import PRESETS, RESOLUTION_LADDER

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max upload
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['REPORT_FOLDER'] = 'reports'

# Create necessary directories
for folder in [app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER'], app.config['REPORT_FOLDER']]:
    os.makedirs(folder, exist_ok=True)

# Store job status in memory
jobs = {}


class OptimizationJob:
    """Represents an optimization job with progress tracking."""

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

    def update_progress(self, progress, step):
        """Update job progress."""
        self.progress = progress
        self.current_step = step
        jobs[self.job_id] = self


def run_optimization(job_id):
    """Run optimization in background thread with progress updates."""
    job = jobs[job_id]

    try:
        job.status = 'running'
        job.update_progress(5, 'Initializing...')

        # Probe source video
        job.update_progress(10, 'Probing source video...')
        source_info = probe_video(job.input_path)
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

        # Create custom progress callback
        class ProgressCallback:
            def __init__(self, job):
                self.job = job
                self.step_count = 0
                self.total_steps = 15  # Estimated total steps

            def __call__(self, progress, step):
                self.step_count += 1
                # Map step count to progress percentage (15% to 95%)
                progress_percent = 15 + (progress * 80 / 100)
                self.job.update_progress(progress_percent, step)

        # Run optimization
        encoder = FFmpegEncoder()
        ladder = OptimizationLadder(encoder)

        # Monkey patch the ladder to add progress tracking
        original_record = ladder._record_iteration

        def progress_record(step, size_kb, target_kbps=None):
            progress = (ladder.iterations[-1]['step'] if ladder.iterations else step)
            job.update_progress(
                min(95, 15 + len(ladder.iterations) * 5),
                f"Optimization: {step}"
            )
            original_record(step, size_kb, target_kbps)

        ladder._record_iteration = progress_record

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
        job.update_progress(100, 'Optimization complete')

    except Exception as e:
        job.status = 'failed'
        job.error = str(e)
        job.update_progress(0, f'Error: {str(e)}')


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

    if not file.filename.lower().endswith('.mp4'):
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
    jobs[job_id] = job

    # Start optimization in background thread
    thread = threading.Thread(target=run_optimization, args=(job_id,))
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


if __name__ == '__main__':
    print("Starting MP4 Banner Optimizer Web Interface...")
    print("Open your browser to: http://localhost:5001")
    app.run(debug=True, host='0.0.0.0', port=5001)