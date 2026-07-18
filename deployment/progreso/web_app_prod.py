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
from flask import Flask, render_template, request, jsonify, send_file, make_response
from werkzeug.utils import secure_filename
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mp4_optimizer.probe import probe_video
from mp4_optimizer.ladder import OptimizationLadder
from mp4_optimizer.encoder import FFmpegEncoder, get_file_size_kb
from mp4_optimizer.report import OptimizationReport
from mp4_optimizer.config import PRESETS, RESOLUTION_LADDER

# Production FFmpeg configuration for Progreso.pl
for _binary, _env_key in [('ffmpeg', 'FFMPEG_PATH'), ('ffprobe', 'FFPROBE_PATH')]:
    _path = os.path.expanduser(f'~/bin/{_binary}')
    if os.path.exists(_path):
        os.environ[_env_key] = _path

# Prefer ~/bin binaries over system ones - the host's system ffmpeg/ffprobe
# can be broken (e.g. missing shared libraries), the static build works.
os.environ['PATH'] = os.path.expanduser('~/bin') + os.pathsep + os.environ.get('PATH', '')

# Force UTF-8 stdio: server locales can be latin-1/ASCII, which crashes
# print() on non-ASCII log output (optimizer logs use emojis).
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

app = Flask(__name__)

# Add custom timestamp filter
@app.template_filter('timestamp_format')
def timestamp_format(timestamp):
    """Format Unix timestamp to readable date/time"""
    if timestamp:
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    return 'N/A'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max upload
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['REPORT_FOLDER'] = 'reports'

# Create necessary directories
for folder in [app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER'], app.config['REPORT_FOLDER']]:
    os.makedirs(folder, exist_ok=True)

# Store job status in memory
jobs = {}


@app.after_request
def add_no_cache_headers(response):
    """Add no-cache headers to prevent browser caching."""
    # Don't cache video files or other static content
    if response.content_type and 'text/html' in response.content_type:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response


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
    """Portal page with links to main app and admin panel."""
    return render_template('portal.html')


@app.route('/app')
def main_app():
    """Main application page."""
    return render_template('index.html')


@app.route('/api/presets', methods=['GET'])
def get_presets():
    """Get available presets."""
    return jsonify(PRESETS)


@app.route('/api/resolutions', methods=['GET'])
def get_resolutions():
    """Get available resolutions."""
    return jsonify(RESOLUTION_LADDER)


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check: FFmpeg/FFprobe binaries and working directories."""
    import subprocess

    checks = {}
    details = {}

    for name, env_key in [('ffmpeg', 'FFMPEG_PATH'), ('ffprobe', 'FFPROBE_PATH')]:
        binary = os.environ.get(env_key, name)
        try:
            result = subprocess.run([binary, '-version'], capture_output=True, timeout=5)
            checks[name] = result.returncode == 0
            if result.returncode != 0:
                details[name] = f"{binary} exited with code {result.returncode}"
        except Exception as e:
            checks[name] = False
            details[name] = f"{binary}: {type(e).__name__}: {e}"

    checks['directories'] = all(
        os.path.isdir(app.config[key]) and os.access(app.config[key], os.W_OK)
        for key in ['UPLOAD_FOLDER', 'OUTPUT_FOLDER', 'REPORT_FOLDER']
    )

    healthy = all(checks.values())
    return jsonify({
        'status': 'ok' if healthy else 'degraded',
        'checks': checks,
        'details': details,
        'timestamp': time.time()
    }), 200 if healthy else 503


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
        'preset': request.form.get('preset', 'high'),
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
    output_dir = app.config['OUTPUT_FOLDER']
    output_file = os.path.join(output_dir, f"{job_id}_optimized.mp4")

    # Check if file exists (works even after server restart)
    if not os.path.exists(output_file):
        return jsonify({'error': 'File not found'}), 404

    return send_file(
        output_file,
        as_attachment=True,
        download_name=f"optimized_{job_id}.mp4"
    )


@app.route('/api/report/<job_id>', methods=['GET'])
def download_report(job_id):
    """Download optimization report."""
    report_dir = app.config['REPORT_FOLDER']
    report_file = os.path.join(report_dir, f"{job_id}_report.json")

    # Check if file exists (works even after server restart)
    if not os.path.exists(report_file):
        return jsonify({'error': 'Report not found'}), 404

    return send_file(
        report_file,
        as_attachment=True,
        download_name=f"report_{job_id}.json"
    )


@app.route('/admin/uploads', methods=['GET'])
def admin_uploads():
    """Admin panel showing complete upload history."""
    upload_dir = app.config['UPLOAD_FOLDER']
    output_dir = app.config['OUTPUT_FOLDER']
    report_dir = app.config['REPORT_FOLDER']

    # Get all upload files
    uploads = []
    try:

        for file in os.listdir(upload_dir):
            if file.endswith('.mp4'):
                file_path = os.path.join(upload_dir, file)
                # Extract job_id from filename (handle UUID format)
                # Filename format: {job_id}_{timestamp}_{random}.mp4 or similar
                parts = file.replace('.mp4', '').split('_')
                job_id = parts[0] if len(parts) > 1 else file.replace('.mp4', '')


                # Get file info
                size_kb = os.path.getsize(file_path) / 1024
                upload_time = os.path.getmtime(file_path)

                # Check if processing was completed
                output_file = os.path.join(output_dir, f"{job_id}_optimized.mp4")
                report_file = os.path.join(report_dir, f"{job_id}_report.json")

                has_output = os.path.exists(output_file)
                has_report = os.path.exists(report_file)

                # Get output size if available
                output_size_kb = 0
                if has_output:
                    output_size_kb = os.path.getsize(output_file) / 1024

                # Read report data if available
                report_data = None
                if has_report:
                    try:
                        import json
                        with open(report_file, 'r') as f:
                            report_data = json.load(f)
                    except:
                        pass

                uploads.append({
                    'job_id': job_id,
                    'filename': file,
                    'size_kb': round(size_kb, 2),
                    'upload_time': upload_time,
                    'has_output': has_output,
                    'output_size_kb': round(output_size_kb, 2) if has_output else 0,
                    'has_report': has_report,
                    'report_data': report_data
                })

                # Auto-generate thumbnail if output exists but thumbnail doesn't
                if has_output:
                    thumbnail_path = os.path.join(report_dir, 'thumbnails', f"{job_id}_thumb.jpg")
                    if not os.path.exists(thumbnail_path):
                        try:
                            os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
                            import subprocess
                            ffmpeg_path = os.environ.get('FFMPEG_PATH', 'ffmpeg')
                            subprocess.run([
                                ffmpeg_path, '-i', output_file,
                                '-ss', '00:00:01', '-vframes', '1',
                                '-vf', 'scale=320:180',
                                '-y', thumbnail_path
                            ], capture_output=True, timeout=10)
                        except:
                            pass  # Silently fail if thumbnail generation fails

        # Sort by upload time (newest first)
        uploads.sort(key=lambda x: x['upload_time'], reverse=True)

    except Exception as e:
        return f"Error loading uploads: {str(e)}", 500

    return render_template('admin_uploads.html', uploads=uploads)


@app.route('/admin/files', methods=['GET'])
def admin_files():
    """Direct file listing API endpoint."""
    upload_dir = app.config['UPLOAD_FOLDER']
    output_dir = app.config['OUTPUT_FOLDER']
    report_dir = app.config['REPORT_FOLDER']

    files = {
        'uploads': [],
        'outputs': [],
        'reports': []
    }

    try:
        # List uploads
        for file in os.listdir(upload_dir):
            if file.endswith('.mp4'):
                file_path = os.path.join(upload_dir, file)
                files['uploads'].append({
                    'name': file,
                    'size_kb': round(os.path.getsize(file_path) / 1024, 2),
                    'modified': os.path.getmtime(file_path)
                })

        # List outputs
        for file in os.listdir(output_dir):
            if file.endswith('.mp4'):
                file_path = os.path.join(output_dir, file)
                files['outputs'].append({
                    'name': file,
                    'size_kb': round(os.path.getsize(file_path) / 1024, 2),
                    'modified': os.path.getmtime(file_path)
                })

        # List reports
        for file in os.listdir(report_dir):
            if file.endswith('.json'):
                file_path = os.path.join(report_dir, file)
                files['reports'].append({
                    'name': file,
                    'size_kb': round(os.path.getsize(file_path) / 1024, 2),
                    'modified': os.path.getmtime(file_path)
                })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify(files)


@app.route('/admin/preview/<job_id>', methods=['GET'])
def admin_preview(job_id):
    """Generate video preview/thumbnail for admin panel."""
    output_dir = app.config['OUTPUT_FOLDER']
    upload_dir = app.config['UPLOAD_FOLDER']

    # Determine which file to preview (output or upload)
    output_file = os.path.join(output_dir, f"{job_id}_optimized.mp4")
    upload_file = os.path.join(upload_dir, f"{job_id}_*.mp4")

    # Prefer output file, fallback to upload
    if os.path.exists(output_file):
        video_file = output_file
    else:
        # Find upload file
        import glob
        upload_files = glob.glob(upload_file)
        if upload_files:
            video_file = upload_files[0]
        else:
            return jsonify({'error': 'Video file not found'}), 404

    # Generate thumbnail if not exists
    thumbnail_dir = os.path.join(app.config['REPORT_FOLDER'], 'thumbnails')
    os.makedirs(thumbnail_dir, exist_ok=True)
    thumbnail_path = os.path.join(thumbnail_dir, f"{job_id}_thumb.jpg")

    if not os.path.exists(thumbnail_path):
        try:
            # Use FFmpeg to generate thumbnail
            import subprocess
            ffmpeg_path = os.environ.get('FFMPEG_PATH', 'ffmpeg')
            result = subprocess.run([
                ffmpeg_path, '-i', video_file,
                '-ss', '00:00:01', '-vframes', '1',
                '-vf', 'scale=320:180',
                '-y', thumbnail_path
            ], capture_output=True, text=True)

            if result.returncode != 0:
                # Fallback: use placeholder
                return jsonify({
                    'thumbnail': None,
                    'video_url': f'/api/download/{job_id}',
                    'error': 'Could not generate thumbnail'
                })
        except Exception as e:
            return jsonify({'error': f'Thumbnail generation failed: {str(e)}'}), 500

    # Return thumbnail info
    return jsonify({
        'thumbnail_url': f'/admin/thumbnail/{job_id}',
        'video_url': f'/api/download/{job_id}',
        'exists': True
    })


@app.route('/admin/thumbnail/<job_id>', methods=['GET'])
def admin_thumbnail(job_id):
    """Serve video thumbnail."""
    thumbnail_dir = os.path.join(app.config['REPORT_FOLDER'], 'thumbnails')
    thumbnail_path = os.path.join(thumbnail_dir, f"{job_id}_thumb.jpg")

    if os.path.exists(thumbnail_path):
        return send_file(thumbnail_path, mimetype='image/jpeg')
    else:
        # Return default placeholder
        return jsonify({'error': 'Thumbnail not found'}), 404


@app.route('/admin/compare/<job_id>', methods=['GET'])
def admin_compare(job_id):
    """Compare original vs optimized video."""
    upload_dir = app.config['UPLOAD_FOLDER']
    output_dir = app.config['OUTPUT_FOLDER']

    # Find files
    output_file = os.path.join(output_dir, f"{job_id}_optimized.mp4")

    import glob
    upload_files = glob.glob(os.path.join(upload_dir, f"{job_id}_*.mp4"))

    if not os.path.exists(output_file) or not upload_files:
        return jsonify({'error': 'Files not found for comparison'}), 404

    upload_file = upload_files[0]

    # Get file info
    original_size = os.path.getsize(upload_file) / 1024
    optimized_size = os.path.getsize(output_file) / 1024
    compression_ratio = ((original_size - optimized_size) / original_size) * 100

    # Get video duration for comparison
    try:
        from mp4_optimizer.probe import probe_video
        original_info = probe_video(upload_file)
        optimized_info = probe_video(output_file)

        return jsonify({
            'original': {
                'size_kb': round(original_size, 2),
                'duration_s': original_info.get('duration_s', 0),
                'resolution': original_info.get('resolution', 'Unknown'),
                'fps': original_info.get('fps', 0)
            },
            'optimized': {
                'size_kb': round(optimized_size, 2),
                'duration_s': optimized_info.get('duration_s', 0),
                'resolution': optimized_info.get('resolution', 'Unknown'),
                'fps': optimized_info.get('fps', 0)
            },
            'compression': {
                'ratio_percent': round(compression_ratio, 2),
                'saved_kb': round(original_size - optimized_size, 2)
            }
        })
    except Exception as e:
        return jsonify({'error': f'Comparison failed: {str(e)}'}), 500


@app.route('/admin/delete/<job_id>', methods=['DELETE'])
def admin_delete(job_id):
    """Delete upload entry and all associated files."""
    try:
        upload_dir = app.config['UPLOAD_FOLDER']
        output_dir = app.config['OUTPUT_FOLDER']
        report_dir = app.config['REPORT_FOLDER']

        # Find and remove upload file
        import glob
        upload_files = glob.glob(os.path.join(upload_dir, f"{job_id}_*.mp4"))
        for upload_file in upload_files:
            os.remove(upload_file)

        # Remove output file
        output_file = os.path.join(output_dir, f"{job_id}_optimized.mp4")
        if os.path.exists(output_file):
            os.remove(output_file)

        # Remove report file
        report_file = os.path.join(report_dir, f"{job_id}_report.json")
        if os.path.exists(report_file):
            os.remove(report_file)

        # Remove thumbnail
        thumbnail_file = os.path.join(report_dir, 'thumbnails', f"{job_id}_thumb.jpg")
        if os.path.exists(thumbnail_file):
            os.remove(thumbnail_file)

        # Remove from jobs dictionary if present
        if job_id in jobs:
            del jobs[job_id]

        return jsonify({'success': True, 'message': 'Entry deleted successfully'})

    except Exception as e:
        return jsonify({'error': f'Delete failed: {str(e)}'}), 500


@app.route('/admin/delete-all', methods=['DELETE'])
def admin_delete_all():
    """Delete all uploads, outputs, reports, and thumbnails."""
    try:
        upload_dir = app.config['UPLOAD_FOLDER']
        output_dir = app.config['OUTPUT_FOLDER']
        report_dir = app.config['REPORT_FOLDER']
        thumbnail_dir = os.path.join(report_dir, 'thumbnails')

        # Count files before deletion
        import glob
        upload_count = len(glob.glob(os.path.join(upload_dir, '*.mp4')))
        output_count = len(glob.glob(os.path.join(output_dir, '*.mp4')))
        report_count = len(glob.glob(os.path.join(report_dir, '*.json')))
        thumbnail_count = len(glob.glob(os.path.join(thumbnail_dir, '*.jpg'))) if os.path.exists(thumbnail_dir) else 0

        # Remove all upload files
        for file in os.listdir(upload_dir):
            if file.endswith('.mp4'):
                os.remove(os.path.join(upload_dir, file))

        # Remove all output files
        for file in os.listdir(output_dir):
            if file.endswith('.mp4'):
                os.remove(os.path.join(output_dir, file))

        # Remove all report files
        for file in os.listdir(report_dir):
            if file.endswith('.json'):
                os.remove(os.path.join(report_dir, file))

        # Remove all thumbnails
        if os.path.exists(thumbnail_dir):
            for file in os.listdir(thumbnail_dir):
                if file.endswith('.jpg'):
                    os.remove(os.path.join(thumbnail_dir, file))

        # Clear all jobs from memory
        jobs.clear()

        return jsonify({
            'success': True,
            'message': f'All entries deleted successfully!',
            'deleted': {
                'uploads': upload_count,
                'outputs': output_count,
                'reports': report_count,
                'thumbnails': thumbnail_count
            }
        })

    except Exception as e:
        return jsonify({'error': f'Delete all failed: {str(e)}'}), 500


if __name__ == '__main__':
    # Production configuration for Progreso.pl
    port = int(os.environ.get('PORT', 5000))

    print("=" * 60)
    print("MP4 Banner Optimizer - Production Mode")
    print("=" * 60)
    print(f"Server running at: http://0.0.0.0:{port}")
    print(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"Output folder: {app.config['OUTPUT_FOLDER']}")
    print(f"FFmpeg: ~/bin/ffmpeg")
    print("=" * 60)
    print("Starting Flask app...", flush=True)

    try:
        app.run(debug=False, host='0.0.0.0', port=port, threaded=True)
    except Exception as e:
        print(f"Flask error: {e}", flush=True)
        raise