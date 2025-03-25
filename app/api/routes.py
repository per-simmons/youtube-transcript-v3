from flask import Blueprint, request, jsonify
from ..services.transcript_service import TranscriptService
from youtube_transcript_api import YouTubeTranscriptApi
import sys
import platform

api = Blueprint('api', __name__)

@api.route('/debug/<video_id>', methods=['GET'])
def debug_video(video_id):
    """Debug endpoint that shows all available transcripts for a video."""
    try:
        # Get environment info
        env_info = {
            "python_version": sys.version,
            "platform": platform.platform(),
            "video_id": video_id
        }
        
        # List all available transcripts
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Get manual transcripts
        manual_transcripts = []
        for transcript in transcript_list.manual_transcripts:
            manual_transcripts.append({
                "language": transcript.language,
                "language_code": transcript.language_code,
                "is_generated": transcript.is_generated,
                "translation_languages": [lang.language_code for lang in transcript.translation_languages]
            })
            
        # Get generated transcripts
        generated_transcripts = []
        for transcript in transcript_list.generated_transcripts:
            generated_transcripts.append({
                "language": transcript.language,
                "language_code": transcript.language_code,
                "is_generated": transcript.is_generated,
                "translation_languages": [lang.language_code for lang in transcript.translation_languages]
            })
            
        return jsonify({
            "environment": env_info,
            "manual_transcripts": manual_transcripts,
            "generated_transcripts": generated_transcripts,
            "has_manual_transcripts": len(manual_transcripts) > 0,
            "has_generated_transcripts": len(generated_transcripts) > 0
        })
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "environment": env_info
        }), 500

@api.route('/process', methods=['POST'])
def process_videos():
    try:
        data = request.get_json()
        video_urls = data.get('urls', [])
        
        if not video_urls:
            return jsonify({"error": "No URLs provided"}), 400
            
        results = TranscriptService.process_multiple_videos(video_urls)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500 