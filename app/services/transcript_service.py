from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import logging
import traceback
import sys
import platform

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TranscriptService:
    @staticmethod
    def check_api_connection() -> Dict[str, str]:
        """Test the YouTube Transcript API with a known working video."""
        test_video_id = "EngW7tLk6R8"  # This is a popular video we know has transcripts
        try:
            logger.info(f"Testing API connection with video {test_video_id}")
            # Log environment details
            logger.info(f"Python Version: {sys.version}")
            logger.info(f"Platform: {platform.platform()}")
            logger.info(f"YouTube Transcript API Version: {YouTubeTranscriptApi.__version__}")
            
            transcript = YouTubeTranscriptApi.get_transcript(test_video_id)
            return {
                'status': 'success',
                'message': 'API connection successful',
                'transcript_length': len(transcript),
                'environment': {
                    'python_version': sys.version,
                    'platform': platform.platform(),
                    'api_version': YouTubeTranscriptApi.__version__
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
                    'api_version': getattr(YouTubeTranscriptApi, '__version__', 'unknown')
                }
            }
            logger.error(f"API connection test failed: {error_details}")
            return error_details

    @staticmethod
    def get_video_id(url: str) -> Optional[str]:
        """Extract video ID from YouTube URL."""
        logger.info(f"Extracting video ID from URL: {url}")
        if 'youtube.com' in url:
            if 'v=' in url:
                video_id = url.split('v=')[1].split('&')[0]
                logger.info(f"Extracted video ID: {video_id}")
                return video_id
        elif 'youtu.be' in url:
            video_id = url.split('/')[-1]
            logger.info(f"Extracted video ID: {video_id}")
            return video_id
        logger.warning(f"Could not extract video ID from URL: {url}")
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
    def get_transcript(video_id: str) -> List[Dict[str, str]]:
        """Fetch transcript for a video."""
        logger.info(f"Attempting to fetch transcript for video: {video_id}")
        try:
            # Log attempt details
            logger.info(f"Environment: Python {sys.version}, Platform: {platform.platform()}")
            logger.info(f"YouTube Transcript API Version: {YouTubeTranscriptApi.__version__}")
            
            # Try direct transcript fetch first
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            logger.info(f"Successfully fetched transcript for video {video_id}")
            return transcript
        except TranscriptsDisabled as e:
            error_msg = f"TranscriptsDisabled error: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise Exception(error_msg)
        except NoTranscriptFound as e:
            error_msg = f"NoTranscriptFound error: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Full traceback: {traceback.format_exc()}")
            try:
                # If no transcript found, try with language specification
                logger.info(f"Attempting to fetch English transcript for {video_id}")
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
                logger.info(f"Successfully fetched English transcript for {video_id}")
                return transcript
            except Exception as e2:
                error_msg2 = f"Second attempt failed: {str(e2)}"
                logger.error(error_msg2)
                logger.error(f"Full traceback: {traceback.format_exc()}")
                raise Exception(f"Could not retrieve transcript. First error: {error_msg}, Second error: {error_msg2}")
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise Exception(error_msg)

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
        video_id = self.get_video_id(url)
        if not video_id:
            logger.error(f"Invalid YouTube URL: {url}")
            raise ValueError("Invalid YouTube URL")

        metadata = self.get_video_metadata(video_id)
        transcript = self.get_transcript(video_id)
        formatted_transcript = self.format_transcript(transcript, metadata)
        
        logger.info(f"Successfully processed video: {metadata['title']}")
        return {
            'title': metadata['title'],
            'transcript': formatted_transcript
        }

    def process_multiple_videos(self, urls: List[str]) -> List[Dict[str, str]]:
        """Process multiple videos and return formatted transcripts."""
        logger.info(f"Processing multiple videos: {len(urls)} URLs")
        logger.info(f"Environment: Python {sys.version}, Platform: {platform.platform()}")
        logger.info(f"YouTube Transcript API Version: {YouTubeTranscriptApi.__version__}")
        
        results = []
        for url in urls:
            try:
                result = self.process_video(url.strip())
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing video {url}: {str(e)}")
                logger.error(f"Full traceback: {traceback.format_exc()}")
                results.append({
                    'title': url,
                    'error': str(e)
                })
        logger.info(f"Finished processing {len(urls)} videos")
        return results 