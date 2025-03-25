from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import logging
import traceback
import sys
import platform
import pkg_resources
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TranscriptService:
    @staticmethod
    def get_package_version(package_name: str) -> str:
        """Get package version safely."""
        try:
            return pkg_resources.get_distribution(package_name).version
        except Exception:
            return "unknown"

    @staticmethod
    def check_api_connection() -> Dict[str, str]:
        """Test the YouTube Transcript API with a known working video."""
        test_video_id = "EngW7tLk6R8"  # This is a popular video we know has transcripts
        try:
            logger.info(f"Testing API connection with video {test_video_id}")
            # Log environment details
            api_version = TranscriptService.get_package_version('youtube_transcript_api')
            logger.info(f"Python Version: {sys.version}")
            logger.info(f"Platform: {platform.platform()}")
            logger.info(f"YouTube Transcript API Version: {api_version}")
            
            transcript = YouTubeTranscriptApi.get_transcript(test_video_id)
            return {
                'status': 'success',
                'message': 'API connection successful',
                'transcript_length': len(transcript),
                'environment': {
                    'python_version': sys.version,
                    'platform': platform.platform(),
                    'api_version': api_version
                }
            }
        except Exception as e:
            error_details = {
                'status': 'error',
                'message': str(e),
                'traceback': traceback.format_exc(),
                'environment': {
                    'python_version': sys.version,
                    'platform': platform.platform(),
                    'api_version': TranscriptService.get_package_version('youtube_transcript_api')
                }
            }
            logger.error(f"API connection test failed: {error_details}")
            return error_details

    @staticmethod
    def extract_video_id(url):
        """Extract video ID from YouTube URL."""
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed\/)([0-9A-Za-z_-]{11})',
            r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    @staticmethod
    def get_video_metadata(video_id: str) -> Dict[str, str]:
        """Fetch video metadata using the video ID."""
        logger.info(f"Fetching metadata for video: {video_id}")
        url = f'https://www.youtube.com/watch?v={video_id}'
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            title_tag = soup.find('meta', property='og:title')
            title = title_tag['content'] if title_tag else f"Video {video_id}"
            
            channel_tag = soup.find('meta', property='og:site_name')
            channel = channel_tag['content'] if channel_tag else "Unknown Channel"
            
            metadata = {
                'title': title,
                'channel': channel,
                'url': url
            }
            logger.info(f"Successfully fetched metadata: {metadata}")
            return metadata
        except Exception as e:
            logger.error(f"Error fetching metadata: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return {
                'title': f"Video {video_id}",
                'channel': "Unknown Channel",
                'url': url
            }

    @staticmethod
    def get_transcript(url):
        """Get transcript for a single video."""
        video_id = TranscriptService.extract_video_id(url)
        if not video_id:
            return {"error": "Invalid YouTube URL format"}

        logger.info(f"Attempting to fetch transcript for video ID: {video_id}")
        try:
            # First try: Direct transcript fetch
            try:
                logger.info("Attempt 1: Direct transcript fetch")
                transcript = YouTubeTranscriptApi.get_transcript(video_id)
                logger.info("Direct transcript fetch successful")
                return transcript
            except Exception as e:
                logger.info(f"Direct transcript fetch failed: {str(e)}")

            # Second try: List transcripts and try different approaches
            logger.info("Attempt 2: Listing all available transcripts")
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # Log available transcripts
            logger.info("Available manual transcripts: " + 
                       ", ".join([f"{t.language_code} ({t.language})" 
                                for t in transcript_list.manual_transcripts]))
            logger.info("Available generated transcripts: " + 
                       ", ".join([f"{t.language_code} ({t.language})" 
                                for t in transcript_list.generated_transcripts]))
            
            # Try different methods in sequence
            try:
                logger.info("Attempting to find English transcript")
                transcript = transcript_list.find_transcript(['en'])
                logger.info("Found English transcript")
                return transcript.fetch()
            except NoTranscriptFound:
                try:
                    logger.info("Attempting to find auto-generated English transcript")
                    transcript = transcript_list.find_generated_transcript(['en'])
                    logger.info("Found auto-generated English transcript")
                    return transcript.fetch()
                except NoTranscriptFound:
                    try:
                        logger.info("Attempting to find any manually created transcript")
                        transcript = transcript_list.find_manually_created_transcript()
                        logger.info(f"Found manual transcript in {transcript.language_code}")
                        translated = transcript.translate('en')
                        logger.info("Successfully translated to English")
                        return translated.fetch()
                    except NoTranscriptFound:
                        try:
                            logger.info("Attempting to find any generated transcript")
                            transcript = transcript_list.find_generated_transcript()
                            logger.info(f"Found generated transcript in {transcript.language_code}")
                            translated = transcript.translate('en')
                            logger.info("Successfully translated to English")
                            return translated.fetch()
                        except NoTranscriptFound:
                            logger.info("Attempting last resort: any available transcript")
                            transcripts = transcript_list.manual_transcripts + transcript_list.generated_transcripts
                            if transcripts:
                                transcript = transcripts[0]
                                logger.info(f"Found transcript in {transcript.language_code}")
                                translated = transcript.translate('en')
                                logger.info("Successfully translated to English")
                                return translated.fetch()
                            
            logger.error("No transcript found after trying all methods")
            raise NoTranscriptFound("No transcript found after trying all methods")
            
        except TranscriptsDisabled as e:
            logger.error(f"TranscriptsDisabled error for video {video_id}: {str(e)}")
            return {
                "error": "Transcripts are disabled for this video",
                "details": "The video owner has disabled subtitles/closed captions. Please try a different video that has captions enabled."
            }
        except NoTranscriptFound as e:
            logger.error(f"NoTranscriptFound error for video {video_id}: {str(e)}")
            return {
                "error": "No transcript found",
                "details": "Could not find any transcripts for this video after trying multiple methods. Please verify that the video has captions available."
            }
        except Exception as e:
            logger.error(f"Unexpected error for video {video_id}: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return {"error": f"Error fetching transcript: {str(e)}"}

    @staticmethod
    def format_transcript(transcript: List[Dict[str, str]], metadata: Dict[str, str]) -> str:
        """Format transcript with metadata and branding."""
        formatted_text = "Brought to you by Podflare\n\n"
        formatted_text += f"Video: {metadata['title']}\n"
        formatted_text += f"Channel: {metadata['channel']}\n"
        formatted_text += f"URL: {metadata['url']}\n\n"
        formatted_text += "Transcript:\n\n"

        for entry in transcript:
            minutes = int(entry['start'] // 60)
            seconds = int(entry['start'] % 60)
            timestamp = f"{minutes:02d}:{seconds:02d}"
            formatted_text += f"[{timestamp}] {entry['text']}\n"

        return formatted_text

    def process_video(self, url: str) -> Dict[str, str]:
        """Process a single video URL and return formatted transcript."""
        logger.info(f"Processing video URL: {url}")
        video_id = self.extract_video_id(url)
        if not video_id:
            logger.error(f"Invalid YouTube URL: {url}")
            raise ValueError("Invalid YouTube URL")

        metadata = self.get_video_metadata(video_id)
        transcript = self.get_transcript(url)
        formatted_transcript = self.format_transcript(transcript, metadata)
        
        logger.info(f"Successfully processed video: {metadata['title']}")
        return {
            'title': metadata['title'],
            'transcript': formatted_transcript
        }

    @staticmethod
    def process_multiple_videos(urls):
        """Process multiple video URLs and return their transcripts."""
        results = {}
        for url in urls:
            transcript = TranscriptService.get_transcript(url)
            if isinstance(transcript, list):  # Successful transcript
                results[url] = {
                    "status": "success",
                    "transcript": transcript
                }
            else:  # Error occurred
                results[url] = {
                    "status": "error",
                    "error": transcript.get("error", "Unknown error"),
                    "details": transcript.get("details", "")
                }
        return results 