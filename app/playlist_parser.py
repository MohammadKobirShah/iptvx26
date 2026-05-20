import re
import logging
import requests
from typing import List, Dict
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class M3UParser:
    def __init__(self, source: str):
        """
        source can be:
        - URL to M3U file
        - Direct M3U content
        """
        self.source = source
        self.channels = []
    
    def parse(self) -> List[Dict]:
        """Parse M3U content"""
        try:
            content = self._get_content()
            if not content:
                logger.error("No M3U content to parse")
                return []
            
            self.channels = self._parse_content(content)
            logger.info(f"Parsed {len(self.channels)} channels")
            return self.channels
            
        except Exception as e:
            logger.error(f"Error parsing M3U: {e}")
            return []
    
    def _get_content(self) -> str:
        """Get M3U content from URL or direct input"""
        if self.source.startswith('http://') or self.source.startswith('https://'):
            # Download from URL
            try:
                response = requests.get(self.source, timeout=30)
                response.raise_for_status()
                return response.text
            except Exception as e:
                logger.error(f"Error downloading M3U: {e}")
                return ""
        else:
            # Direct content
            return self.source
    
    def _parse_content(self, content: str) -> List[Dict]:
        """Parse M3U content"""
        channels = []
        lines = content.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if line.startswith('#EXTINF:'):
                channel_info = self._parse_extinf(line)
                
                i += 1
                while i < len(lines):
                    url_line = lines[i].strip()
                    if url_line and not url_line.startswith('#'):
                        channel_info['url'] = url_line
                        channel_info['stream_id'] = self._generate_stream_id(
                            channel_info['name'], len(channels)
                        )
                        
                        if self._is_valid_url(url_line):
                            channels.append(channel_info)
                        break
                    i += 1
            
            i += 1
        
        return channels
    
    def _parse_extinf(self, line: str) -> Dict:
        """Parse EXTINF line"""
        info = {
            'name': 'Unknown Channel',
            'tvg_id': '',
            'tvg_name': '',
            'tvg_logo': '',
            'group_title': 'General'
        }
        
        tvg_id_match = re.search(r'tvg-id="([^"]*)"', line, re.IGNORECASE)
        if tvg_id_match:
            info['tvg_id'] = tvg_id_match.group(1)
        
        tvg_name_match = re.search(r'tvg-name="([^"]*)"', line, re.IGNORECASE)
        if tvg_name_match:
            info['tvg_name'] = tvg_name_match.group(1)
        
        tvg_logo_match = re.search(r'tvg-logo="([^"]*)"', line, re.IGNORECASE)
        if tvg_logo_match:
            info['tvg_logo'] = tvg_logo_match.group(1)
        
        group_match = re.search(r'group-title="([^"]*)"', line, re.IGNORECASE)
        if group_match:
            info['group_title'] = group_match.group(1)
        
        name_match = re.search(r',(.+)$', line)
        if name_match:
            info['name'] = name_match.group(1).strip()
        
        return info
    
    def _generate_stream_id(self, name: str, index: int) -> str:
        """Generate unique stream ID"""
        stream_id = re.sub(r'[^a-zA-Z0-9]', '_', name.lower())
        stream_id = re.sub(r'_+', '_', stream_id).strip('_')
        return f"{stream_id}_{index}"
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def get_all_groups(self) -> List[str]:
        """Get all unique groups"""
        groups = set(ch['group_title'] for ch in self.channels)
        return sorted(list(groups))
