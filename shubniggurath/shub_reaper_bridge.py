"""
SHUB-NIGGURATH v3.1 — REAPER Bridge Module (Real, not Virtual)

Real integration between REAPER DAW and Shub-Niggurath AI assistant.
Replaces the previous virtual simulator with actual REAPER project access.

Author: Shub-Niggurath Development Team
Date: 2025-12-02
Version: 3.1
"""

import os
import json
import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import xml.etree.ElementTree as ET

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class TrackType(Enum):
    """REAPER track types"""
    AUDIO = "audio"
    MIDI = "midi"
    FOLDER = "folder"
    MASTER = "master"


@dataclass
class AudioItem:
    """Audio item/clip in a REAPER track"""
    name: str
    start_time: float  # Position in project (seconds)
    duration: float    # Length (seconds)
    filename: str      # Source file path
    mute: bool = False
    lock: bool = False


@dataclass
class TrackFX:
    """FX chain element"""
    index: int
    name: str
    enabled: bool
    params: Dict[str, float] = None  # Param name → value


@dataclass
class ReaperTrack:
    """REAPER track representation"""
    index: int
    name: str
    track_type: TrackType
    volume_db: float
    pan: float  # -1.0 to 1.0
    mute: bool
    solo: bool
    fx_chain: List[TrackFX]
    items: List[AudioItem]
    height: int = 0


@dataclass
class ReaperProject:
    """REAPER project representation"""
    name: str
    path: str
    bpm: float
    sample_rate: int
    bit_depth: int
    tracks: List[ReaperTrack]
    regions: List[Dict[str, Any]]
    markers: List[Dict[str, Any]]


# ============================================================================
# REAPER Bridge - Core Implementation
# ============================================================================

class ReaperBridge:
    """
    Bridge between REAPER DAW and Shub-Niggurath.
    
    Handles:
    - Project file parsing (.RPP format)
    - Track and item enumeration
    - FX chain analysis
    - Data export to Shub database
    """

    def __init__(self, reaper_home: Optional[str] = None, config_path: Optional[str] = None):
        """
        Initialize REAPER bridge.

        Args:
            reaper_home: Path to REAPER installation (default: /opt/REAPER)
            config_path: Path to REAPER config (default: ~/.config/REAPER)
        """
        self.reaper_home = Path(reaper_home or "/opt/REAPER")
        self.config_path = Path(config_path or os.path.expanduser("~/.config/REAPER"))
        self.projects_path = Path(os.path.expanduser("~/REAPER-Projects"))
        
        # Verify installation
        self.reaper_exe = self.reaper_home / "reaper"
        if not self.reaper_exe.exists():
            # Fallback to system reaper
            import shutil
            reaper_bin = shutil.which("reaper")
            if reaper_bin:
                self.reaper_exe = Path(reaper_bin)
            else:
                raise FileNotFoundError("REAPER executable not found")
        
        logger.info(f"REAPER Bridge initialized: {self.reaper_exe}")

    async def get_projects_list(self) -> List[str]:
        """
        Get list of available REAPER projects.

        Returns:
            List of .RPP file paths
        """
        if not self.projects_path.exists():
            return []
        
        rpp_files = list(self.projects_path.glob("*.rpp"))
        logger.info(f"Found {len(rpp_files)} projects")
        return [str(f) for f in rpp_files]

    async def parse_project_file(self, project_path: str) -> Optional[ReaperProject]:
        """
        Parse REAPER .RPP project file.

        Args:
            project_path: Path to .RPP file

        Returns:
            ReaperProject object or None if parsing fails
        """
        project_file = Path(project_path)
        if not project_file.exists():
            logger.error(f"Project file not found: {project_path}")
            return None

        try:
            # Read RPP file (text format)
            with open(project_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Parse basic project info
            name = project_file.stem
            bpm = self._extract_value(content, "TEMPO", 120.0)
            sample_rate = int(self._extract_value(content, "SRATE", 44100))

            # Parse tracks
            tracks = self._parse_tracks(content)

            # Parse regions and markers
            regions = self._parse_regions(content)
            markers = self._parse_markers(content)

            project = ReaperProject(
                name=name,
                path=project_path,
                bpm=bpm,
                sample_rate=sample_rate,
                bit_depth=24,  # Default assumption
                tracks=tracks,
                regions=regions,
                markers=markers,
            )

            logger.info(f"Parsed project: {name} ({len(tracks)} tracks)")
            return project

        except Exception as e:
            logger.error(f"Error parsing project: {e}")
            return None

    def _parse_tracks(self, content: str) -> List[ReaperTrack]:
        """Parse tracks from RPP content"""
        tracks = []
        track_blocks = content.split("<TRACK")
        
        for idx, block in enumerate(track_blocks[1:]):  # Skip header
            try:
                track_lines = block.split("\n", 20)  # Get first 20 lines
                
                # Extract basic track info
                track_name = self._extract_field(block, "NAME", f"Track {idx+1}")
                volume = self._extract_value(block, "VOLPAN", 0.0, index=0)
                pan = self._extract_value(block, "VOLPAN", 0.0, index=1)
                mute = "MUTE 1" in block
                solo = "SOLO 1" in block

                # Determine track type
                if "MASTERTRACK" in block:
                    track_type = TrackType.MASTER
                elif "TRACKHEIGHT" in block:
                    track_type = TrackType.AUDIO
                else:
                    track_type = TrackType.AUDIO

                # Parse FX chain
                fx_chain = self._parse_fx_chain(block)

                # Parse items (clips/regions)
                items = self._parse_items(block)

                track = ReaperTrack(
                    index=idx,
                    name=track_name,
                    track_type=track_type,
                    volume_db=volume,
                    pan=pan,
                    mute=mute,
                    solo=solo,
                    fx_chain=fx_chain,
                    items=items,
                )
                
                tracks.append(track)

            except Exception as e:
                logger.debug(f"Error parsing track {idx}: {e}")
                continue

        return tracks

    def _parse_fx_chain(self, track_block: str) -> List[TrackFX]:
        """Parse FX chain from track block"""
        fx_list = []
        fx_count = 0

        # Extract FX count
        for line in track_block.split("\n"):
            if "NFXCH" in line or "FXEN" in line:
                try:
                    fx_count = int(line.split()[-1])
                    break
                except:
                    pass

        # Parse individual FX
        for fx_idx in range(min(fx_count, 20)):  # Limit to 20 FX
            fx_name = f"FX{fx_idx}"
            try:
                fx = TrackFX(
                    index=fx_idx,
                    name=fx_name,
                    enabled=True,
                    params={}
                )
                fx_list.append(fx)
            except Exception as e:
                logger.debug(f"Error parsing FX {fx_idx}: {e}")

        return fx_list

    def _parse_items(self, track_block: str) -> List[AudioItem]:
        """Parse audio items/clips from track block"""
        items = []
        
        # Find all ITEM blocks
        item_blocks = track_block.split("<ITEM")
        
        for item_block in item_blocks[1:]:
            try:
                lines = item_block.split("\n", 15)
                
                # Extract item info
                name = self._extract_field(item_block, "NAME", "Item")
                start = self._extract_value(item_block, "POSITION", 0.0)
                duration = self._extract_value(item_block, "LENGTH", 1.0)
                filename = self._extract_field(item_block, "FILE", "")
                
                item = AudioItem(
                    name=name,
                    start_time=start,
                    duration=duration,
                    filename=filename,
                )
                items.append(item)
            except Exception as e:
                logger.debug(f"Error parsing item: {e}")

        return items

    def _parse_regions(self, content: str) -> List[Dict[str, Any]]:
        """Parse regions from project"""
        regions = []
        
        for line in content.split("\n"):
            if line.startswith("MARKER"):
                try:
                    parts = line.split()
                    if len(parts) >= 2:
                        position = float(parts[1])
                        name = parts[-1] if len(parts) > 2 else "Region"
                        regions.append({
                            "position": position,
                            "name": name,
                            "type": "region"
                        })
                except Exception as e:
                    logger.debug(f"Error parsing region: {e}")

        return regions

    def _parse_markers(self, content: str) -> List[Dict[str, Any]]:
        """Parse markers from project"""
        markers = []
        
        for line in content.split("\n"):
            if line.startswith("MARKER"):
                try:
                    parts = line.split()
                    if len(parts) >= 2:
                        position = float(parts[1])
                        name = parts[-1] if len(parts) > 2 else "Marker"
                        markers.append({
                            "position": position,
                            "name": name,
                            "type": "marker"
                        })
                except Exception as e:
                    logger.debug(f"Error parsing marker: {e}")

        return markers

    # Helper methods
    def _extract_value(self, text: str, key: str, default: float, index: int = None) -> float:
        """Extract numeric value from RPP content"""
        try:
            for line in text.split("\n"):
                if key in line:
                    parts = line.split()
                    if index is not None and len(parts) > index:
                        return float(parts[index])
                    elif len(parts) > 1:
                        return float(parts[-1])
            return default
        except:
            return default

    def _extract_field(self, text: str, key: str, default: str) -> str:
        """Extract string field from RPP content"""
        try:
            for line in text.split("\n"):
                if f"{key}" in line:
                    # Handle quoted strings
                    if '"' in line:
                        parts = line.split('"')
                        if len(parts) >= 2:
                            return parts[1]
                    # Fallback
                    parts = line.split()
                    if len(parts) > 1:
                        return " ".join(parts[1:])
            return default
        except:
            return default


# ============================================================================
# Shub Integration
# ============================================================================

class ShubReaperIntegration:
    """Integration layer between Shub and REAPER bridge"""

    def __init__(self, bridge: ReaperBridge, db_session=None):
        """
        Initialize integration.

        Args:
            bridge: ReaperBridge instance
            db_session: SQLAlchemy database session
        """
        self.bridge = bridge
        self.db_session = db_session

    async def analyze_project(self, project_path: str) -> Dict[str, Any]:
        """
        Analyze a REAPER project for Shub processing.

        Args:
            project_path: Path to .RPP file

        Returns:
            Analysis result dictionary
        """
        project = await self.bridge.parse_project_file(project_path)
        
        if not project:
            return {"error": "Failed to parse project"}

        analysis = {
            "project_name": project.name,
            "project_path": project.path,
            "bpm": project.bpm,
            "sample_rate": project.sample_rate,
            "track_count": len(project.tracks),
            "item_count": sum(len(t.items) for t in project.tracks),
            "avg_volume": sum(t.volume_db for t in project.tracks) / len(project.tracks) if project.tracks else 0.0,
            "tracks": [
                {
                    "index": t.index,
                    "name": t.name,
                    "type": t.track_type.value,
                    "volume_db": t.volume_db,
                    "pan": t.pan,
                    "mute": t.mute,
                    "solo": t.solo,
                    "fx_count": len(t.fx_chain),
                    "item_count": len(t.items),
                    "items": [
                        {
                            "name": item.name,
                            "start": item.start_time,
                            "duration": item.duration,
                            "filename": item.filename,
                            "mute": item.mute,
                        }
                        for item in t.items
                    ],
                }
                for t in project.tracks
            ],
            "region_count": len(project.regions),
            "marker_count": len(project.markers),
        }

        logger.info(f"Analysis complete: {project.name}")
        return analysis

    async def export_to_database(self, project: ReaperProject):
        """
        Export project data to Shub database.

        Args:
            project: ReaperProject object
        """
        if not self.db_session:
            logger.warning("No database session provided, skipping export")
            return

        # TODO: Implement database export
        # This will depend on the actual Shub database schema
        # (shub_db_schema.py tables)
        logger.info(f"Exporting {project.name} to database...")


# ============================================================================
# Test/Example Usage
# ============================================================================

async def test_reaper_bridge():
    """Test the REAPER bridge"""
    
    # Initialize bridge
    bridge = ReaperBridge()

    # List projects
    projects = await bridge.get_projects_list()
    print(f"Found {len(projects)} projects:")
    for proj in projects[:5]:  # Show first 5
        print(f"  - {proj}")

    # Parse a project (if available)
    if projects:
        project = await bridge.parse_project_file(projects[0])
        if project:
            print(f"\nProject: {project.name}")
            print(f"  BPM: {project.bpm}")
            print(f"  Sample Rate: {project.sample_rate} Hz")
            print(f"  Tracks: {len(project.tracks)}")
            for track in project.tracks[:3]:  # Show first 3 tracks
                print(f"    - {track.name} ({track.track_type.value})")


if __name__ == "__main__":
    # Run test
    asyncio.run(test_reaper_bridge())
