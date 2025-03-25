from flask import Blueprint, request, jsonify
from ..services.transcript_service import TranscriptService

api = Blueprint('api', __name__)
transcript_service = TranscriptService()

@api.route('/api/transcript', methods=['POST'])
def get_transcript():
    try:
        data = request.get_json()
        urls = data.get('urls', [])
        
        if not urls:
            return jsonify({'error': 'No URLs provided'}), 400
            
        results = transcript_service.process_multiple_videos(urls)
        return jsonify({'results': results})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500 