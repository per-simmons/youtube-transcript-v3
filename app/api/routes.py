from flask import Blueprint, request, jsonify
from ..services.transcript_service import TranscriptService
import sys
import logging
from youtube_transcript_api import YouTubeTranscriptApi

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api = Blueprint('api', __name__)
transcript_service = TranscriptService()

@api.route('/api/debug', methods=['GET'])
def debug_info():
    """Endpoint to check environment and dependencies."""
    try:
        return jsonify({
            'python_version': sys.version,
            'youtube_transcript_api_version': YouTubeTranscriptApi.__version__,
            'platform': sys.platform,
            'test_video_check': transcript_service.check_api_connection()
        })
    except Exception as e:
        logger.error(f"Debug endpoint error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api.route('/api/transcript', methods=['POST'])
def get_transcript():
    try:
        logger.info("Received transcript request")
        data = request.get_json()
        urls = data.get('urls', [])
        
        if not urls:
            logger.warning("No URLs provided in request")
            return jsonify({'error': 'No URLs provided'}), 400
        
        logger.info(f"Processing {len(urls)} URLs")
        results = transcript_service.process_multiple_videos(urls)
        logger.info("Finished processing URLs")
        return jsonify({'results': results})
        
    except Exception as e:
        logger.error(f"Error in transcript endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500 