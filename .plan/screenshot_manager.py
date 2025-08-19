#!/usr/bin/env python3
"""
Screenshot Manager - Screenshot integration for browser_use test cases

This script captures screenshots at each test step, links screenshots to test case steps,
manages screenshot storage efficiently, and provides screenshot comparison and analysis
capabilities for visual testing and debugging.

Author: Claude Code
Date: 2025-08-15
"""

import asyncio
import json
import hashlib
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from PIL import Image, ImageDraw, ImageFont
import base64
import io
from enum import Enum

# Browser_use imports
from browser_use import Agent, BrowserSession, BrowserProfile
from browser_use.browser.views import Page


class ScreenshotType(Enum):
    """Types of screenshots"""
    FULL_PAGE = "full_page"
    VIEWPORT = "viewport"
    ELEMENT = "element"
    REGION = "region"
    COMPARISON = "comparison"
    ANNOTATED = "annotated"


@dataclass
class ScreenshotMetadata:
    """Metadata for a screenshot"""
    screenshot_id: str
    screenshot_type: ScreenshotType
    timestamp: datetime
    page_url: str
    page_title: str
    viewport_size: Dict[str, int]
    file_path: str
    file_size_bytes: int
    dimensions: Dict[str, int]
    hash_value: str
    compression_quality: int = 85
    annotations: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ElementScreenshot:
    """Screenshot specific to an element"""
    element_selector: str
    bounding_box: Dict[str, float]
    element_text: str
    screenshot_metadata: ScreenshotMetadata
    context_padding: int = 20


@dataclass
class TestStepScreenshot:
    """Screenshot linked to a test step"""
    step_id: str
    step_description: str
    action_type: str
    before_screenshot: Optional[ScreenshotMetadata] = None
    after_screenshot: Optional[ScreenshotMetadata] = None
    element_screenshots: List[ElementScreenshot] = field(default_factory=list)
    diff_screenshot: Optional[ScreenshotMetadata] = None


@dataclass
class ScreenshotSession:
    """Collection of screenshots for a test session"""
    session_id: str
    test_case_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    base_url: str = ""
    screenshots: List[TestStepScreenshot] = field(default_factory=list)
    storage_stats: Dict[str, Any] = field(default_factory=dict)


class ScreenshotManager:
    """
    Advanced screenshot management for browser_use testing
    
    Features:
    - Step-by-step screenshot capture
    - Element-specific screenshots with highlighting
    - Visual diff generation
    - Screenshot compression and optimization
    - Annotation and markup capabilities
    - Storage management and cleanup
    - Screenshot comparison and analysis
    """
    
    def __init__(self,
                 storage_dir: str = "./screenshots",
                 max_storage_mb: int = 500,
                 compression_quality: int = 85,
                 enable_diffs: bool = True,
                 auto_cleanup: bool = True):
        """
        Initialize the screenshot manager
        
        Args:
            storage_dir: Directory for screenshot storage
            max_storage_mb: Maximum storage space in MB
            compression_quality: JPEG compression quality (1-100)
            enable_diffs: Whether to generate visual diffs
            auto_cleanup: Automatically cleanup old screenshots
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.storage_dir / "full_page").mkdir(exist_ok=True)
        (self.storage_dir / "viewport").mkdir(exist_ok=True)
        (self.storage_dir / "elements").mkdir(exist_ok=True)
        (self.storage_dir / "diffs").mkdir(exist_ok=True)
        (self.storage_dir / "annotated").mkdir(exist_ok=True)
        
        self.max_storage_bytes = max_storage_mb * 1024 * 1024
        self.compression_quality = compression_quality
        self.enable_diffs = enable_diffs
        self.auto_cleanup = auto_cleanup
        
        # Current session
        self.current_session: Optional[ScreenshotSession] = None
        self.screenshot_cache: Dict[str, Image.Image] = {}
        
        # Statistics
        self.stats = {
            "total_screenshots": 0,
            "total_size_bytes": 0,
            "sessions_count": 0,
            "last_cleanup": None
        }

    async def start_session(self, test_case_id: str, base_url: str = "") -> str:
        """
        Start a new screenshot session
        
        Args:
            test_case_id: ID of the test case
            base_url: Base URL being tested
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        
        self.current_session = ScreenshotSession(
            session_id=session_id,
            test_case_id=test_case_id,
            start_time=datetime.now(),
            base_url=base_url
        )
        
        self.stats["sessions_count"] += 1
        return session_id

    async def end_session(self) -> Optional[ScreenshotSession]:
        """End the current session and save metadata"""
        if not self.current_session:
            return None
        
        self.current_session.end_time = datetime.now()
        
        # Calculate storage stats
        self.current_session.storage_stats = await self._calculate_session_stats()
        
        # Save session metadata
        await self._save_session_metadata()
        
        session = self.current_session
        self.current_session = None
        
        # Auto cleanup if enabled
        if self.auto_cleanup:
            await self._auto_cleanup()
        
        return session

    async def capture_step_screenshots(self,
                                     page: Page,
                                     step_id: str,
                                     step_description: str,
                                     action_type: str,
                                     target_elements: List[str] = None) -> TestStepScreenshot:
        """
        Capture screenshots for a test step
        
        Args:
            page: Browser page
            step_id: Unique step identifier
            step_description: Description of the step
            action_type: Type of action being performed
            target_elements: List of element selectors to capture
            
        Returns:
            TestStepScreenshot with all captured screenshots
        """
        if not self.current_session:
            raise ValueError("No active session. Call start_session() first.")
        
        step_screenshot = TestStepScreenshot(
            step_id=step_id,
            step_description=step_description,
            action_type=action_type
        )
        
        # Capture before screenshot
        step_screenshot.before_screenshot = await self._capture_viewport_screenshot(
            page, f"{step_id}_before"
        )
        
        # Capture element screenshots if specified
        if target_elements:
            for selector in target_elements:
                element_screenshot = await self._capture_element_screenshot(
                    page, selector, f"{step_id}_element_{len(step_screenshot.element_screenshots)}"
                )
                if element_screenshot:
                    step_screenshot.element_screenshots.append(element_screenshot)
        
        # Store in current session
        self.current_session.screenshots.append(step_screenshot)
        
        return step_screenshot

    async def capture_after_screenshot(self, page: Page, step_id: str) -> Optional[ScreenshotMetadata]:
        """Capture after screenshot for a step and generate diff"""
        if not self.current_session:
            return None
        
        # Find the step
        step_screenshot = None
        for screenshot in self.current_session.screenshots:
            if screenshot.step_id == step_id:
                step_screenshot = screenshot
                break
        
        if not step_screenshot:
            return None
        
        # Capture after screenshot
        after_screenshot = await self._capture_viewport_screenshot(
            page, f"{step_id}_after"
        )
        step_screenshot.after_screenshot = after_screenshot
        
        # Generate diff if enabled and before screenshot exists
        if self.enable_diffs and step_screenshot.before_screenshot:
            diff_screenshot = await self._generate_diff_screenshot(
                step_screenshot.before_screenshot,
                after_screenshot,
                f"{step_id}_diff"
            )
            step_screenshot.diff_screenshot = diff_screenshot
        
        return after_screenshot

    async def _capture_viewport_screenshot(self, page: Page, screenshot_id: str) -> ScreenshotMetadata:
        """Capture viewport screenshot"""
        try:
            # Get page info
            page_url = page.url
            page_title = await page.title()
            viewport_size = await page.evaluate("() => ({width: window.innerWidth, height: window.innerHeight})")
            
            # Capture screenshot
            screenshot_bytes = await page.screenshot(type='png')
            
            # Save screenshot
            filename = f"{screenshot_id}_{datetime.now().strftime('%H%M%S')}.png"
            file_path = self.storage_dir / "viewport" / filename
            
            with open(file_path, 'wb') as f:
                f.write(screenshot_bytes)
            
            # Calculate hash and dimensions
            image = Image.open(io.BytesIO(screenshot_bytes))
            dimensions = {"width": image.width, "height": image.height}
            hash_value = hashlib.md5(screenshot_bytes).hexdigest()
            
            # Cache image for diff generation
            self.screenshot_cache[screenshot_id] = image
            
            metadata = ScreenshotMetadata(
                screenshot_id=screenshot_id,
                screenshot_type=ScreenshotType.VIEWPORT,
                timestamp=datetime.now(),
                page_url=page_url,
                page_title=page_title,
                viewport_size=viewport_size,
                file_path=str(file_path),
                file_size_bytes=len(screenshot_bytes),
                dimensions=dimensions,
                hash_value=hash_value,
                compression_quality=self.compression_quality
            )
            
            self.stats["total_screenshots"] += 1
            self.stats["total_size_bytes"] += len(screenshot_bytes)
            
            return metadata
            
        except Exception as e:
            print(f"Error capturing viewport screenshot: {e}")
            raise

    async def _capture_element_screenshot(self, page: Page, selector: str, screenshot_id: str) -> Optional[ElementScreenshot]:
        """Capture screenshot of specific element with highlighting"""
        try:
            # Find element
            element = await page.query_selector(selector)
            if not element:
                print(f"Element not found: {selector}")
                return None
            
            # Get element properties
            bounding_box = await element.bounding_box()
            if not bounding_box:
                print(f"Element has no bounding box: {selector}")
                return None
            
            element_text = await element.text_content() or ""
            
            # Capture element screenshot with padding
            padding = 20
            clip = {
                "x": max(0, bounding_box["x"] - padding),
                "y": max(0, bounding_box["y"] - padding),
                "width": bounding_box["width"] + (padding * 2),
                "height": bounding_box["height"] + (padding * 2)
            }
            
            screenshot_bytes = await page.screenshot(type='png', clip=clip)
            
            # Save screenshot
            filename = f"{screenshot_id}_{datetime.now().strftime('%H%M%S')}.png"
            file_path = self.storage_dir / "elements" / filename
            
            with open(file_path, 'wb') as f:
                f.write(screenshot_bytes)
            
            # Create annotated version with highlighting
            annotated_screenshot = await self._create_annotated_screenshot(
                screenshot_bytes, bounding_box, padding, f"{screenshot_id}_annotated"
            )
            
            # Create metadata
            image = Image.open(io.BytesIO(screenshot_bytes))
            dimensions = {"width": image.width, "height": image.height}
            hash_value = hashlib.md5(screenshot_bytes).hexdigest()
            
            metadata = ScreenshotMetadata(
                screenshot_id=screenshot_id,
                screenshot_type=ScreenshotType.ELEMENT,
                timestamp=datetime.now(),
                page_url=page.url,
                page_title=await page.title(),
                viewport_size=await page.evaluate("() => ({width: window.innerWidth, height: window.innerHeight})"),
                file_path=str(file_path),
                file_size_bytes=len(screenshot_bytes),
                dimensions=dimensions,
                hash_value=hash_value,
                annotations=[{
                    "type": "highlight",
                    "element_selector": selector,
                    "bounding_box": bounding_box
                }]
            )
            
            self.stats["total_screenshots"] += 1
            self.stats["total_size_bytes"] += len(screenshot_bytes)
            
            return ElementScreenshot(
                element_selector=selector,
                bounding_box=bounding_box,
                element_text=element_text,
                screenshot_metadata=metadata,
                context_padding=padding
            )
            
        except Exception as e:
            print(f"Error capturing element screenshot: {e}")
            return None

    async def _create_annotated_screenshot(self,
                                         screenshot_bytes: bytes,
                                         element_bbox: Dict[str, float],
                                         padding: int,
                                         screenshot_id: str) -> ScreenshotMetadata:
        """Create annotated screenshot with element highlighting"""
        try:
            # Load image
            image = Image.open(io.BytesIO(screenshot_bytes))
            draw = ImageDraw.Draw(image)
            
            # Calculate element position in cropped screenshot
            highlight_rect = [
                padding,  # x
                padding,  # y
                padding + element_bbox["width"],  # x + width
                padding + element_bbox["height"]  # y + height
            ]
            
            # Draw highlight rectangle
            draw.rectangle(highlight_rect, outline="red", width=3)
            
            # Add corner markers
            corner_size = 10
            for x, y in [(highlight_rect[0], highlight_rect[1]),  # top-left
                        (highlight_rect[2], highlight_rect[1]),  # top-right
                        (highlight_rect[0], highlight_rect[3]),  # bottom-left
                        (highlight_rect[2], highlight_rect[3])]: # bottom-right
                draw.rectangle([x-corner_size//2, y-corner_size//2, 
                              x+corner_size//2, y+corner_size//2], 
                             fill="red")
            
            # Save annotated screenshot
            filename = f"{screenshot_id}_{datetime.now().strftime('%H%M%S')}.png"
            file_path = self.storage_dir / "annotated" / filename
            
            image.save(file_path, 'PNG')
            
            # Get file size
            file_size = file_path.stat().st_size
            
            metadata = ScreenshotMetadata(
                screenshot_id=screenshot_id,
                screenshot_type=ScreenshotType.ANNOTATED,
                timestamp=datetime.now(),
                page_url="",  # Not available in this context
                page_title="",
                viewport_size={},
                file_path=str(file_path),
                file_size_bytes=file_size,
                dimensions={"width": image.width, "height": image.height},
                hash_value=hashlib.md5(screenshot_bytes).hexdigest(),
                annotations=[{
                    "type": "element_highlight",
                    "highlight_rect": highlight_rect,
                    "corner_markers": True
                }]
            )
            
            self.stats["total_screenshots"] += 1
            self.stats["total_size_bytes"] += file_size
            
            return metadata
            
        except Exception as e:
            print(f"Error creating annotated screenshot: {e}")
            raise

    async def _generate_diff_screenshot(self,
                                      before_metadata: ScreenshotMetadata,
                                      after_metadata: ScreenshotMetadata,
                                      diff_id: str) -> Optional[ScreenshotMetadata]:
        """Generate visual diff between two screenshots"""
        try:
            # Load images
            before_image = Image.open(before_metadata.file_path)
            after_image = Image.open(after_metadata.file_path)
            
            # Ensure images are same size
            if before_image.size != after_image.size:
                # Resize to smaller dimensions
                min_width = min(before_image.width, after_image.width)
                min_height = min(before_image.height, after_image.height)
                before_image = before_image.resize((min_width, min_height))
                after_image = after_image.resize((min_width, min_height))
            
            # Create diff image
            diff_image = Image.new('RGB', before_image.size, (255, 255, 255))
            
            # Convert to RGB for pixel comparison
            before_rgb = before_image.convert('RGB')
            after_rgb = after_image.convert('RGB')
            
            # Calculate pixel differences
            diff_pixels = []
            for x in range(before_image.width):
                for y in range(before_image.height):
                    before_pixel = before_rgb.getpixel((x, y))
                    after_pixel = after_rgb.getpixel((x, y))
                    
                    # Calculate difference
                    diff = sum(abs(b - a) for b, a in zip(before_pixel, after_pixel))
                    
                    if diff > 30:  # Threshold for visible difference
                        # Highlight difference in red
                        diff_image.putpixel((x, y), (255, 0, 0))
                        diff_pixels.append((x, y))
                    else:
                        # Keep original pixel but fade it
                        faded_pixel = tuple(int(p * 0.7) for p in after_pixel)
                        diff_image.putpixel((x, y), faded_pixel)
            
            # Save diff image
            filename = f"{diff_id}_{datetime.now().strftime('%H%M%S')}.png"
            file_path = self.storage_dir / "diffs" / filename
            diff_image.save(file_path, 'PNG')
            
            # Get file size
            file_size = file_path.stat().st_size
            
            metadata = ScreenshotMetadata(
                screenshot_id=diff_id,
                screenshot_type=ScreenshotType.COMPARISON,
                timestamp=datetime.now(),
                page_url=after_metadata.page_url,
                page_title=after_metadata.page_title,
                viewport_size=after_metadata.viewport_size,
                file_path=str(file_path),
                file_size_bytes=file_size,
                dimensions={"width": diff_image.width, "height": diff_image.height},
                hash_value=hashlib.md5(file_path.read_bytes()).hexdigest(),
                annotations=[{
                    "type": "visual_diff",
                    "before_screenshot": before_metadata.screenshot_id,
                    "after_screenshot": after_metadata.screenshot_id,
                    "diff_pixels_count": len(diff_pixels),
                    "total_pixels": before_image.width * before_image.height,
                    "difference_percentage": len(diff_pixels) / (before_image.width * before_image.height) * 100
                }]
            )
            
            self.stats["total_screenshots"] += 1
            self.stats["total_size_bytes"] += file_size
            
            return metadata
            
        except Exception as e:
            print(f"Error generating diff screenshot: {e}")
            return None

    async def capture_full_page_screenshot(self, page: Page, screenshot_id: str) -> ScreenshotMetadata:
        """Capture full page screenshot"""
        try:
            # Capture full page
            screenshot_bytes = await page.screenshot(type='png', full_page=True)
            
            # Save screenshot
            filename = f"{screenshot_id}_{datetime.now().strftime('%H%M%S')}.png"
            file_path = self.storage_dir / "full_page" / filename
            
            with open(file_path, 'wb') as f:
                f.write(screenshot_bytes)
            
            # Get metadata
            image = Image.open(io.BytesIO(screenshot_bytes))
            dimensions = {"width": image.width, "height": image.height}
            hash_value = hashlib.md5(screenshot_bytes).hexdigest()
            
            metadata = ScreenshotMetadata(
                screenshot_id=screenshot_id,
                screenshot_type=ScreenshotType.FULL_PAGE,
                timestamp=datetime.now(),
                page_url=page.url,
                page_title=await page.title(),
                viewport_size=await page.evaluate("() => ({width: window.innerWidth, height: window.innerHeight})"),
                file_path=str(file_path),
                file_size_bytes=len(screenshot_bytes),
                dimensions=dimensions,
                hash_value=hash_value
            )
            
            self.stats["total_screenshots"] += 1
            self.stats["total_size_bytes"] += len(screenshot_bytes)
            
            return metadata
            
        except Exception as e:
            print(f"Error capturing full page screenshot: {e}")
            raise

    async def _calculate_session_stats(self) -> Dict[str, Any]:
        """Calculate statistics for current session"""
        if not self.current_session:
            return {}
        
        total_screenshots = 0
        total_size = 0
        screenshot_types = {}
        
        for step_screenshot in self.current_session.screenshots:
            # Count before/after screenshots
            if step_screenshot.before_screenshot:
                total_screenshots += 1
                total_size += step_screenshot.before_screenshot.file_size_bytes
                screenshot_types["before"] = screenshot_types.get("before", 0) + 1
            
            if step_screenshot.after_screenshot:
                total_screenshots += 1
                total_size += step_screenshot.after_screenshot.file_size_bytes
                screenshot_types["after"] = screenshot_types.get("after", 0) + 1
            
            # Count element screenshots
            total_screenshots += len(step_screenshot.element_screenshots)
            for elem_screenshot in step_screenshot.element_screenshots:
                total_size += elem_screenshot.screenshot_metadata.file_size_bytes
                screenshot_types["element"] = screenshot_types.get("element", 0) + 1
            
            # Count diff screenshots
            if step_screenshot.diff_screenshot:
                total_screenshots += 1
                total_size += step_screenshot.diff_screenshot.file_size_bytes
                screenshot_types["diff"] = screenshot_types.get("diff", 0) + 1
        
        return {
            "total_screenshots": total_screenshots,
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "screenshot_types": screenshot_types,
            "steps_count": len(self.current_session.screenshots),
            "avg_screenshots_per_step": total_screenshots / max(len(self.current_session.screenshots), 1)
        }

    async def _save_session_metadata(self):
        """Save session metadata to file"""
        if not self.current_session:
            return
        
        metadata_file = self.storage_dir / f"session_{self.current_session.session_id}.json"
        
        # Convert to serializable format
        session_dict = asdict(self.current_session)
        session_dict["start_time"] = self.current_session.start_time.isoformat()
        if self.current_session.end_time:
            session_dict["end_time"] = self.current_session.end_time.isoformat()
        
        # Convert datetime fields in screenshots
        for step in session_dict["screenshots"]:
            for screenshot_field in ["before_screenshot", "after_screenshot", "diff_screenshot"]:
                if step[screenshot_field]:
                    step[screenshot_field]["timestamp"] = datetime.fromisoformat(
                        step[screenshot_field]["timestamp"]
                    ).isoformat()
            
            for elem_screenshot in step["element_screenshots"]:
                elem_screenshot["screenshot_metadata"]["timestamp"] = datetime.fromisoformat(
                    elem_screenshot["screenshot_metadata"]["timestamp"]
                ).isoformat()
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(session_dict, f, indent=2, ensure_ascii=False)
        
        print(f"Session metadata saved to: {metadata_file}")

    async def _auto_cleanup(self):
        """Automatic cleanup of old screenshots"""
        current_size = await self._calculate_total_storage_size()
        
        if current_size > self.max_storage_bytes:
            print(f"Storage limit exceeded ({current_size / (1024*1024):.1f} MB), cleaning up...")
            await self.cleanup_old_screenshots(days_old=7)
        
        self.stats["last_cleanup"] = datetime.now().isoformat()

    async def _calculate_total_storage_size(self) -> int:
        """Calculate total storage size"""
        total_size = 0
        for file_path in self.storage_dir.rglob("*.png"):
            total_size += file_path.stat().st_size
        return total_size

    async def cleanup_old_screenshots(self, days_old: int = 30):
        """Clean up screenshots older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        cleaned_files = 0
        cleaned_size = 0
        
        for file_path in self.storage_dir.rglob("*.png"):
            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            if file_time < cutoff_date:
                file_size = file_path.stat().st_size
                file_path.unlink()
                cleaned_files += 1
                cleaned_size += file_size
        
        # Also clean up metadata files
        for file_path in self.storage_dir.rglob("session_*.json"):
            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            if file_time < cutoff_date:
                file_path.unlink()
                cleaned_files += 1
        
        print(f"Cleaned up {cleaned_files} files, freed {cleaned_size / (1024*1024):.1f} MB")

    async def get_session_screenshots(self, session_id: str) -> Optional[ScreenshotSession]:
        """Retrieve screenshots for a specific session"""
        metadata_file = self.storage_dir / f"session_{session_id}.json"
        
        if not metadata_file.exists():
            return None
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Convert back from JSON
            session_data["start_time"] = datetime.fromisoformat(session_data["start_time"])
            if session_data.get("end_time"):
                session_data["end_time"] = datetime.fromisoformat(session_data["end_time"])
            
            # Reconstruct session object (simplified)
            return ScreenshotSession(**session_data)
            
        except Exception as e:
            print(f"Error loading session {session_id}: {e}")
            return None

    async def generate_report(self, session_id: str = None) -> Dict[str, Any]:
        """Generate a comprehensive screenshot report"""
        if session_id:
            session = await self.get_session_screenshots(session_id)
            if not session:
                return {"error": f"Session {session_id} not found"}
            
            sessions = [session]
        else:
            # Load all sessions
            sessions = []
            for metadata_file in self.storage_dir.glob("session_*.json"):
                session_id = metadata_file.stem.replace("session_", "")
                session = await self.get_session_screenshots(session_id)
                if session:
                    sessions.append(session)
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "total_sessions": len(sessions),
            "total_screenshots": 0,
            "total_storage_mb": 0,
            "screenshot_types": {},
            "quality_metrics": {},
            "sessions": []
        }
        
        for session in sessions:
            session_report = {
                "session_id": session.session_id,
                "test_case_id": session.test_case_id,
                "start_time": session.start_time.isoformat(),
                "end_time": session.end_time.isoformat() if session.end_time else None,
                "storage_stats": session.storage_stats,
                "steps_count": len(session.screenshots)
            }
            
            report["sessions"].append(session_report)
            report["total_screenshots"] += session.storage_stats.get("total_screenshots", 0)
            report["total_storage_mb"] += session.storage_stats.get("total_size_mb", 0)
        
        return report


# Example usage
async def example_usage():
    """Example usage of ScreenshotManager"""
    
    # Initialize screenshot manager
    screenshot_manager = ScreenshotManager(
        storage_dir="./test_screenshots",
        max_storage_mb=100,
        compression_quality=85,
        enable_diffs=True,
        auto_cleanup=True
    )
    
    # Create browser session
    browser_profile = BrowserProfile()
    browser_session = BrowserSession(browser_profile)
    
    try:
        # Start screenshot session
        session_id = await screenshot_manager.start_session(
            test_case_id="test_login_flow",
            base_url="https://example.com"
        )
        print(f"Started screenshot session: {session_id}")
        
        # Get page
        page = await browser_session.get_current_page()
        await page.goto("https://example.com")
        
        # Capture step screenshots
        step1 = await screenshot_manager.capture_step_screenshots(
            page=page,
            step_id="step_1",
            step_description="Navigate to login page",
            action_type="navigate"
        )
        print(f"Captured step 1 screenshots: {len(step1.element_screenshots)} elements")
        
        # Simulate user action (click login button)
        login_button = await page.query_selector("button")
        if login_button:
            await login_button.click()
        
        # Capture after screenshot with diff
        after_screenshot = await screenshot_manager.capture_after_screenshot(page, "step_1")
        if after_screenshot:
            print(f"Captured after screenshot: {after_screenshot.screenshot_id}")
        
        # Capture another step with element focus
        step2 = await screenshot_manager.capture_step_screenshots(
            page=page,
            step_id="step_2",
            step_description="Fill login form",
            action_type="type",
            target_elements=["input[type='email']", "input[type='password']"]
        )
        print(f"Captured step 2 with {len(step2.element_screenshots)} element screenshots")
        
        # Capture full page screenshot
        full_page = await screenshot_manager.capture_full_page_screenshot(page, "full_page_final")
        print(f"Captured full page screenshot: {full_page.dimensions}")
        
        # End session
        completed_session = await screenshot_manager.end_session()
        if completed_session:
            print(f"Session completed. Total screenshots: {completed_session.storage_stats.get('total_screenshots', 0)}")
        
        # Generate report
        report = await screenshot_manager.generate_report()
        print(f"Report: {report['total_sessions']} sessions, {report['total_screenshots']} screenshots")
        
    finally:
        await browser_session.close()


if __name__ == "__main__":
    print("Screenshot Manager - Example Usage")
    print("=" * 40)
    
    asyncio.run(example_usage())