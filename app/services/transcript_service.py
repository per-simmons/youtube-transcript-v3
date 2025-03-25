from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import logging

class TranscriptService:
    @staticmethod
    def get_video_id(url: str) -> Optional[str]:
        """Extract video ID from YouTube URL."""
        if 'youtube.com' in url:
            if 'v=' in url:
                return url.split('v=')[1].split('&')[0]
        elif 'youtu.be' in url:
            return url.split('/')[-1]
        return None

    @staticmethod
    def get_video_metadata(video_id: str) -> Dict[str, str]:
        """Fetch video metadata using the video ID."""
        url = f'https://www.youtube.com/watch?v={video_id}'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Get title from meta tag or fallback to video ID
        title_tag = soup.find('meta', property='og:title')
        title = title_tag['content'] if title_tag else f"Video {video_id}"
        
        # Get channel from meta tag or fallback to "Unknown Channel"
        channel_tag = soup.find('meta', property='og:site_name')
        channel = channel_tag['content'] if channel_tag else "Unknown Channel"
        
        return {
            'title': title,
            'channel': channel,
            'url': url
        }

    @staticmethod
    def get_transcript(video_id: str) -> List[Dict[str, str]]:
        """Fetch transcript for a video."""
        try:
            # First try to list available transcripts
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # Try to get any available transcript
            transcript = transcript_list.find_manually_created_transcript()
            return transcript.fetch()
        except NoTranscriptFound:
            try:
                # If no manual transcript, try auto-generated
                transcript = transcript_list.find_generated_transcript()
                return transcript.fetch()
            except NoTranscriptFound:
                try:
                    # If still no transcript, try any available language
                    transcript = transcript_list.find_transcript(['en'])
                    return transcript.fetch()
                except NoTranscriptFound:
                    raise Exception(f"No transcript found for video {video_id}. Please check if the video has subtitles enabled.")
        except TranscriptsDisabled:
            raise Exception(f"Transcripts are disabled for video {video_id}. Please check if the video has subtitles enabled.")
        except Exception as e:
            raise Exception(f"Error fetching transcript: {str(e)}")

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
        video_id = self.get_video_id(url)
        if not video_id:
            raise ValueError("Invalid YouTube URL")

        metadata = self.get_video_metadata(video_id)
        transcript = self.get_transcript(video_id)
        formatted_transcript = self.format_transcript(transcript, metadata)
        
        return {
            'title': metadata['title'],
            'transcript': formatted_transcript
        }

    def process_multiple_videos(self, urls: List[str]) -> List[Dict[str, str]]:
        """Process multiple video URLs and return formatted transcripts."""
        results = []
        for url in urls:
            try:
                result = self.process_video(url.strip())
                results.append(result)
            except Exception as e:
                results.append({
                    'title': url,
                    'error': str(e)
                })
        return results 