#!/usr/bin/env python3
"""
Multi Selector Extractor - Component selector extraction with multiple strategies

This script captures multiple selector strategies per element (CSS, XPath, text),
provides fallback selectors for reliability, and includes comprehensive
element attributes and properties for robust test automation.

Author: Claude Code
Date: 2025-08-15
"""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib

# Browser_use imports  
from browser_use import Agent, BrowserSession, BrowserProfile
from browser_use.browser.views import Page


class SelectorType(Enum):
    """Types of selectors available"""
    CSS = "css"
    XPATH = "xpath"
    TEXT = "text"
    ID = "id"
    CLASS = "class"
    NAME = "name"
    TAG = "tag"
    ARIA_LABEL = "aria-label"
    DATA_TESTID = "data-testid"
    PLACEHOLDER = "placeholder"


@dataclass
class ElementSelector:
    """Represents a single selector for an element"""
    selector_type: SelectorType
    value: str
    specificity_score: float
    reliability_score: float
    is_unique: bool
    validation_status: str = "untested"  # untested, valid, invalid, flaky


@dataclass
class ElementProperties:
    """Comprehensive element properties and attributes"""
    tag_name: str
    text_content: str
    inner_html: str
    attributes: Dict[str, str]
    computed_styles: Dict[str, str]
    bounding_box: Dict[str, float]
    is_visible: bool
    is_enabled: bool
    is_clickable: bool
    parent_chain: List[str]
    child_count: int
    sibling_index: int


@dataclass  
class ExtractedElement:
    """Complete element information with multiple selectors"""
    element_id: str
    selectors: List[ElementSelector]
    properties: ElementProperties
    context: Dict[str, Any]
    timestamp: datetime
    page_url: str
    screenshot_region: Optional[Dict[str, float]] = None
    reliability_rank: float = 0.0


@dataclass
class ExtractionResult:
    """Result of element extraction from a page"""
    page_url: str
    page_title: str
    extraction_timestamp: datetime
    elements: List[ExtractedElement]
    total_elements: int
    extraction_duration_ms: float
    quality_metrics: Dict[str, float]


class MultiSelectorExtractor:
    """
    Advanced element selector extraction with multiple strategies
    
    Features:
    - Multiple selector types (CSS, XPath, text, ARIA, etc.)
    - Fallback selector generation
    - Reliability scoring and validation
    - Element property extraction
    - Context-aware selector optimization
    """
    
    def __init__(self, 
                 output_dir: str = "./selector_output",
                 enable_validation: bool = True,
                 max_selectors_per_element: int = 8):
        """
        Initialize the multi-selector extractor
        
        Args:
            output_dir: Directory to save extraction results
            enable_validation: Whether to validate selectors
            max_selectors_per_element: Maximum selectors per element
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.enable_validation = enable_validation
        self.max_selectors_per_element = max_selectors_per_element
        
        # Selector generation strategies
        self.selector_strategies = {
            SelectorType.CSS: self._generate_css_selectors,
            SelectorType.XPATH: self._generate_xpath_selectors,
            SelectorType.TEXT: self._generate_text_selectors,
            SelectorType.ID: self._generate_id_selector,
            SelectorType.CLASS: self._generate_class_selectors,
            SelectorType.NAME: self._generate_name_selector,
            SelectorType.ARIA_LABEL: self._generate_aria_selectors,
            SelectorType.DATA_TESTID: self._generate_testid_selector,
            SelectorType.PLACEHOLDER: self._generate_placeholder_selector,
        }

    async def extract_from_page(self, page: Page, 
                              element_filter: callable = None) -> ExtractionResult:
        """
        Extract elements and selectors from a page
        
        Args:
            page: Browser page to extract from
            element_filter: Optional filter for elements
            
        Returns:
            ExtractionResult with extracted elements
        """
        start_time = datetime.now()
        
        # Get page information
        page_url = page.url
        page_title = await page.title()
        
        # Extract all interactive elements
        elements_data = await self._get_page_elements(page)
        
        # Process each element
        extracted_elements = []
        for element_data in elements_data:
            if element_filter and not element_filter(element_data):
                continue
                
            extracted_element = await self._process_element(element_data, page)
            if extracted_element:
                extracted_elements.append(extracted_element)
        
        # Calculate quality metrics
        end_time = datetime.now()
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        quality_metrics = await self._calculate_quality_metrics(extracted_elements)
        
        result = ExtractionResult(
            page_url=page_url,
            page_title=page_title,
            extraction_timestamp=start_time,
            elements=extracted_elements,
            total_elements=len(extracted_elements),
            extraction_duration_ms=duration_ms,
            quality_metrics=quality_metrics
        )
        
        # Save results
        await self._save_extraction_result(result)
        
        return result

    async def _get_page_elements(self, page: Page) -> List[Dict[str, Any]]:
        """Get all interactive elements from the page"""
        script = """
        () => {
            const elements = [];
            const interactiveSelectors = [
                'button', 'input', 'select', 'textarea', 'a[href]',
                '[onclick]', '[role="button"]', '[role="link"]',
                '[role="tab"]', '[role="menuitem"]', '[tabindex]',
                'form', 'label', '[contenteditable="true"]'
            ];
            
            // Get all potentially interactive elements
            const allElements = document.querySelectorAll(interactiveSelectors.join(', '));
            
            allElements.forEach((element, index) => {
                if (!element.offsetParent && element.tagName !== 'INPUT') {
                    return; // Skip hidden elements (except inputs which might be hidden but functional)
                }
                
                const rect = element.getBoundingClientRect();
                const computedStyle = window.getComputedStyle(element);
                
                // Get all attributes
                const attributes = {};
                for (let attr of element.attributes) {
                    attributes[attr.name] = attr.value;
                }
                
                // Get parent chain
                const parentChain = [];
                let parent = element.parentElement;
                let depth = 0;
                while (parent && depth < 5) {
                    const parentSelector = parent.tagName.toLowerCase();
                    if (parent.id) parentSelector += '#' + parent.id;
                    if (parent.className) parentSelector += '.' + parent.className.split(' ')[0];
                    parentChain.push(parentSelector);
                    parent = parent.parentElement;
                    depth++;
                }
                
                elements.push({
                    index: index,
                    tagName: element.tagName.toLowerCase(),
                    textContent: element.textContent ? element.textContent.trim().substring(0, 200) : '',
                    innerHTML: element.innerHTML ? element.innerHTML.substring(0, 500) : '',
                    attributes: attributes,
                    computedStyles: {
                        display: computedStyle.display,
                        visibility: computedStyle.visibility,
                        position: computedStyle.position,
                        zIndex: computedStyle.zIndex,
                        backgroundColor: computedStyle.backgroundColor,
                        color: computedStyle.color,
                        fontSize: computedStyle.fontSize,
                        fontFamily: computedStyle.fontFamily
                    },
                    boundingBox: {
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height,
                        top: rect.top,
                        left: rect.left,
                        right: rect.right,
                        bottom: rect.bottom
                    },
                    isVisible: rect.width > 0 && rect.height > 0 && computedStyle.visibility !== 'hidden',
                    isEnabled: !element.disabled,
                    parentChain: parentChain,
                    childCount: element.children.length,
                    siblingIndex: Array.from(element.parentElement?.children || []).indexOf(element)
                });
            });
            
            return elements;
        }
        """
        
        return await page.evaluate(script)

    async def _process_element(self, element_data: Dict[str, Any], page: Page) -> Optional[ExtractedElement]:
        """Process a single element and generate multiple selectors"""
        try:
            # Generate element ID
            element_id = self._generate_element_id(element_data)
            
            # Create element properties
            properties = ElementProperties(
                tag_name=element_data['tagName'],
                text_content=element_data['textContent'],
                inner_html=element_data['innerHTML'],
                attributes=element_data['attributes'],
                computed_styles=element_data['computedStyles'],
                bounding_box=element_data['boundingBox'],
                is_visible=element_data['isVisible'],
                is_enabled=element_data['isEnabled'],
                is_clickable=self._is_clickable_element(element_data),
                parent_chain=element_data['parentChain'],
                child_count=element_data['childCount'],
                sibling_index=element_data['siblingIndex']
            )
            
            # Generate multiple selectors
            selectors = await self._generate_all_selectors(element_data, page)
            
            # Rank selectors by reliability
            ranked_selectors = await self._rank_selectors(selectors, element_data)
            
            # Take top selectors
            final_selectors = ranked_selectors[:self.max_selectors_per_element]
            
            # Calculate overall reliability
            reliability_rank = sum(s.reliability_score for s in final_selectors) / len(final_selectors) if final_selectors else 0
            
            return ExtractedElement(
                element_id=element_id,
                selectors=final_selectors,
                properties=properties,
                context=self._extract_context(element_data),
                timestamp=datetime.now(),
                page_url=page.url,
                reliability_rank=reliability_rank
            )
            
        except Exception as e:
            print(f"Error processing element: {e}")
            return None

    def _generate_element_id(self, element_data: Dict[str, Any]) -> str:
        """Generate a unique ID for the element"""
        # Create hash from element characteristics
        identifier_parts = [
            element_data['tagName'],
            element_data.get('attributes', {}).get('id', ''),
            element_data.get('attributes', {}).get('class', ''),
            element_data['textContent'][:50],
            str(element_data['boundingBox']),
            str(element_data['siblingIndex'])
        ]
        
        identifier_string = '|'.join(identifier_parts)
        return hashlib.md5(identifier_string.encode()).hexdigest()[:12]

    def _is_clickable_element(self, element_data: Dict[str, Any]) -> bool:
        """Determine if element is clickable"""
        tag_name = element_data['tagName']
        attributes = element_data.get('attributes', {})
        
        # Standard clickable elements
        clickable_tags = ['button', 'a', 'input', 'select', 'textarea']
        if tag_name in clickable_tags:
            return True
        
        # Elements with click handlers or roles
        if any(attr in attributes for attr in ['onclick', 'role']):
            return True
        
        # Elements with tabindex
        if 'tabindex' in attributes:
            return True
        
        return False

    async def _generate_all_selectors(self, element_data: Dict[str, Any], page: Page) -> List[ElementSelector]:
        """Generate all types of selectors for an element"""
        all_selectors = []
        
        for selector_type, generator_func in self.selector_strategies.items():
            try:
                selectors = await generator_func(element_data, page)
                all_selectors.extend(selectors)
            except Exception as e:
                print(f"Error generating {selector_type.value} selectors: {e}")
        
        return all_selectors

    async def _generate_css_selectors(self, element_data: Dict[str, Any], page: Page) -> List[ElementSelector]:
        """Generate CSS selectors with varying specificity"""
        selectors = []
        tag_name = element_data['tagName']
        attributes = element_data.get('attributes', {})
        
        # ID selector (highest specificity)
        if 'id' in attributes and attributes['id']:
            selectors.append(ElementSelector(
                selector_type=SelectorType.CSS,
                value=f"#{attributes['id']}",
                specificity_score=1.0,
                reliability_score=0.95,
                is_unique=True
            ))
        
        # Class selectors
        if 'class' in attributes and attributes['class']:
            classes = attributes['class'].split()
            for class_name in classes[:3]:  # Limit to first 3 classes
                selector_value = f".{class_name}"
                selectors.append(ElementSelector(
                    selector_type=SelectorType.CSS,
                    value=selector_value,
                    specificity_score=0.7,
                    reliability_score=0.6,
                    is_unique=False
                ))
                
                # Tag + class combination
                selectors.append(ElementSelector(
                    selector_type=SelectorType.CSS,
                    value=f"{tag_name}.{class_name}",
                    specificity_score=0.8,
                    reliability_score=0.75,
                    is_unique=False
                ))
        
        # Attribute selectors
        for attr_name, attr_value in attributes.items():
            if attr_name in ['name', 'type', 'value', 'placeholder'] and attr_value:
                selectors.append(ElementSelector(
                    selector_type=SelectorType.CSS,
                    value=f"{tag_name}[{attr_name}='{attr_value}']",
                    specificity_score=0.8,
                    reliability_score=0.8,
                    is_unique=False
                ))
        
        # Nth-child selectors
        sibling_index = element_data.get('siblingIndex', 0)
        if sibling_index >= 0:
            selectors.append(ElementSelector(
                selector_type=SelectorType.CSS,
                value=f"{tag_name}:nth-child({sibling_index + 1})",
                specificity_score=0.6,
                reliability_score=0.4,  # Low reliability due to DOM changes
                is_unique=False
            ))
        
        return selectors

    async def _generate_xpath_selectors(self, element_data: Dict[str, Any], page: Page) -> List[ElementSelector]:
        """Generate XPath selectors"""
        selectors = []
        tag_name = element_data['tagName']
        attributes = element_data.get('attributes', {})
        text_content = element_data.get('textContent', '').strip()
        
        # ID-based XPath
        if 'id' in attributes and attributes['id']:
            selectors.append(ElementSelector(
                selector_type=SelectorType.XPATH,
                value=f"//{tag_name}[@id='{attributes['id']}']",
                specificity_score=1.0,
                reliability_score=0.95,
                is_unique=True
            ))
        
        # Class-based XPath
        if 'class' in attributes and attributes['class']:
            selectors.append(ElementSelector(
                selector_type=SelectorType.XPATH,
                value=f"//{tag_name}[@class='{attributes['class']}']",
                specificity_score=0.8,
                reliability_score=0.7,
                is_unique=False
            ))
        
        # Text-based XPath
        if text_content and len(text_content) > 0:
            # Exact text match
            selectors.append(ElementSelector(
                selector_type=SelectorType.XPATH,
                value=f"//{tag_name}[text()='{text_content[:50]}']",
                specificity_score=0.9,
                reliability_score=0.8,
                is_unique=False
            ))
            
            # Contains text
            selectors.append(ElementSelector(
                selector_type=SelectorType.XPATH,
                value=f"//{tag_name}[contains(text(), '{text_content[:30]}')]",
                specificity_score=0.7,
                reliability_score=0.6,
                is_unique=False
            ))
        
        # Attribute-based XPath
        for attr_name, attr_value in attributes.items():
            if attr_name in ['name', 'type', 'value'] and attr_value:
                selectors.append(ElementSelector(
                    selector_type=SelectorType.XPATH,
                    value=f"//{tag_name}[@{attr_name}='{attr_value}']",
                    specificity_score=0.8,
                    reliability_score=0.8,
                    is_unique=False
                ))
        
        return selectors

    async def _generate_text_selectors(self, element_data: Dict[str, Any], page: Page) -> List[ElementSelector]:
        """Generate text-based selectors"""
        selectors = []
        text_content = element_data.get('textContent', '').strip()
        
        if text_content:
            # Exact text match
            selectors.append(ElementSelector(
                selector_type=SelectorType.TEXT,
                value=text_content,
                specificity_score=0.9,
                reliability_score=0.7,
                is_unique=False
            ))
            
            # Partial text match for longer text
            if len(text_content) > 20:
                partial_text = text_content[:20]
                selectors.append(ElementSelector(
                    selector_type=SelectorType.TEXT,
                    value=f"*{partial_text}*",
                    specificity_score=0.6,
                    reliability_score=0.5,
                    is_unique=False
                ))
        
        return selectors

    async def _generate_id_selector(self, element_data: Dict[str, Any], page: Page) -> List[ElementSelector]:
        """Generate ID-based selector"""
        attributes = element_data.get('attributes', {})
        
        if 'id' in attributes and attributes['id']:
            return [ElementSelector(
                selector_type=SelectorType.ID,
                value=attributes['id'],
                specificity_score=1.0,
                reliability_score=0.95,
                is_unique=True
            )]
        
        return []

    async def _generate_class_selectors(self, element_data: Dict[str, Any], page: Page) -> List[ElementSelector]:
        """Generate class-based selectors"""
        selectors = []
        attributes = element_data.get('attributes', {})
        
        if 'class' in attributes and attributes['class']:
            classes = attributes['class'].split()
            for class_name in classes:
                selectors.append(ElementSelector(
                    selector_type=SelectorType.CLASS,
                    value=class_name,
                    specificity_score=0.7,
                    reliability_score=0.6,
                    is_unique=False
                ))
        
        return selectors

    async def _generate_name_selector(self, element_data: Dict[str, Any], page: Page) -> List[ElementSelector]:
        """Generate name attribute selector"""
        attributes = element_data.get('attributes', {})
        
        if 'name' in attributes and attributes['name']:
            return [ElementSelector(
                selector_type=SelectorType.NAME,
                value=attributes['name'],
                specificity_score=0.8,
                reliability_score=0.8,
                is_unique=False
            )]
        
        return []

    async def _generate_aria_selectors(self, element_data: Dict[str, Any], page: Page) -> List[ElementSelector]:
        """Generate ARIA-based selectors"""
        selectors = []
        attributes = element_data.get('attributes', {})
        
        aria_attributes = ['aria-label', 'aria-labelledby', 'aria-describedby', 'role']
        
        for aria_attr in aria_attributes:
            if aria_attr in attributes and attributes[aria_attr]:
                selectors.append(ElementSelector(
                    selector_type=SelectorType.ARIA_LABEL,
                    value=f"{aria_attr}={attributes[aria_attr]}",
                    specificity_score=0.8,
                    reliability_score=0.85,
                    is_unique=False
                ))
        
        return selectors

    async def _generate_testid_selector(self, element_data: Dict[str, Any], page: Page) -> List[ElementSelector]:
        """Generate data-testid selector"""
        attributes = element_data.get('attributes', {})
        
        test_id_attrs = ['data-testid', 'data-test-id', 'data-cy', 'data-selenium']
        
        selectors = []
        for test_attr in test_id_attrs:
            if test_attr in attributes and attributes[test_attr]:
                selectors.append(ElementSelector(
                    selector_type=SelectorType.DATA_TESTID,
                    value=f"{test_attr}={attributes[test_attr]}",
                    specificity_score=0.9,
                    reliability_score=0.9,
                    is_unique=True
                ))
        
        return selectors

    async def _generate_placeholder_selector(self, element_data: Dict[str, Any], page: Page) -> List[ElementSelector]:
        """Generate placeholder-based selector"""
        attributes = element_data.get('attributes', {})
        
        if 'placeholder' in attributes and attributes['placeholder']:
            return [ElementSelector(
                selector_type=SelectorType.PLACEHOLDER,
                value=attributes['placeholder'],
                specificity_score=0.7,
                reliability_score=0.6,
                is_unique=False
            )]
        
        return []

    async def _rank_selectors(self, selectors: List[ElementSelector], element_data: Dict[str, Any]) -> List[ElementSelector]:
        """Rank selectors by reliability and specificity"""
        def calculate_score(selector: ElementSelector) -> float:
            # Weighted scoring
            specificity_weight = 0.4
            reliability_weight = 0.6
            
            score = (selector.specificity_score * specificity_weight + 
                    selector.reliability_score * reliability_weight)
            
            # Bonus for unique selectors
            if selector.is_unique:
                score += 0.1
            
            # Bonus for certain selector types
            type_bonuses = {
                SelectorType.DATA_TESTID: 0.2,
                SelectorType.ID: 0.15,
                SelectorType.ARIA_LABEL: 0.1
            }
            
            score += type_bonuses.get(selector.selector_type, 0)
            
            return min(score, 1.0)  # Cap at 1.0
        
        # Calculate scores and sort
        for selector in selectors:
            selector.reliability_score = calculate_score(selector)
        
        return sorted(selectors, key=lambda s: s.reliability_score, reverse=True)

    def _extract_context(self, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract contextual information about the element"""
        return {
            "form_context": self._get_form_context(element_data),
            "navigation_context": self._get_navigation_context(element_data),
            "interaction_context": self._get_interaction_context(element_data),
            "visual_context": self._get_visual_context(element_data)
        }

    def _get_form_context(self, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get form-related context"""
        attributes = element_data.get('attributes', {})
        
        return {
            "is_form_element": element_data['tagName'] in ['input', 'select', 'textarea', 'button'],
            "form_type": attributes.get('type', ''),
            "is_required": 'required' in attributes,
            "has_validation": any(attr.startswith('pattern') or attr.startswith('min') or attr.startswith('max') 
                                for attr in attributes.keys())
        }

    def _get_navigation_context(self, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get navigation-related context"""
        attributes = element_data.get('attributes', {})
        
        return {
            "is_link": element_data['tagName'] == 'a' and 'href' in attributes,
            "is_external_link": attributes.get('href', '').startswith('http'),
            "has_target": 'target' in attributes,
            "is_navigation": 'nav' in element_data.get('parentChain', [])
        }

    def _get_interaction_context(self, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get interaction-related context"""
        attributes = element_data.get('attributes', {})
        
        return {
            "is_clickable": self._is_clickable_element(element_data),
            "has_events": any(attr.startswith('on') for attr in attributes.keys()),
            "is_focusable": 'tabindex' in attributes or element_data['tagName'] in ['input', 'button', 'select', 'textarea', 'a'],
            "interaction_type": self._determine_interaction_type(element_data)
        }

    def _get_visual_context(self, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get visual context"""
        bbox = element_data.get('boundingBox', {})
        styles = element_data.get('computedStyles', {})
        
        return {
            "size_category": self._categorize_size(bbox),
            "position_category": self._categorize_position(bbox),
            "visibility_status": styles.get('visibility', 'visible'),
            "z_index": styles.get('zIndex', 'auto')
        }

    def _determine_interaction_type(self, element_data: Dict[str, Any]) -> str:
        """Determine the primary interaction type for an element"""
        tag_name = element_data['tagName']
        attributes = element_data.get('attributes', {})
        
        if tag_name == 'button' or attributes.get('type') == 'submit':
            return 'submit'
        elif tag_name == 'input':
            input_type = attributes.get('type', 'text')
            return f'input_{input_type}'
        elif tag_name == 'a':
            return 'navigation'
        elif tag_name == 'select':
            return 'selection'
        elif 'onclick' in attributes:
            return 'click'
        else:
            return 'unknown'

    def _categorize_size(self, bbox: Dict[str, float]) -> str:
        """Categorize element size"""
        area = bbox.get('width', 0) * bbox.get('height', 0)
        
        if area < 100:
            return 'small'
        elif area < 1000:
            return 'medium'
        else:
            return 'large'

    def _categorize_position(self, bbox: Dict[str, float]) -> str:
        """Categorize element position on page"""
        y = bbox.get('y', 0)
        
        if y < 100:
            return 'top'
        elif y < 500:
            return 'middle'
        else:
            return 'bottom'

    async def _calculate_quality_metrics(self, elements: List[ExtractedElement]) -> Dict[str, float]:
        """Calculate quality metrics for the extraction"""
        if not elements:
            return {"coverage": 0.0, "selector_diversity": 0.0, "reliability": 0.0}
        
        # Coverage: percentage of elements with multiple selectors
        multi_selector_count = sum(1 for elem in elements if len(elem.selectors) > 1)
        coverage = multi_selector_count / len(elements)
        
        # Selector diversity: variety of selector types used
        all_selector_types = set()
        for elem in elements:
            for selector in elem.selectors:
                all_selector_types.add(selector.selector_type)
        
        selector_diversity = len(all_selector_types) / len(SelectorType)
        
        # Average reliability
        all_reliabilities = []
        for elem in elements:
            all_reliabilities.extend(s.reliability_score for s in elem.selectors)
        
        reliability = sum(all_reliabilities) / len(all_reliabilities) if all_reliabilities else 0
        
        return {
            "coverage": coverage,
            "selector_diversity": selector_diversity,
            "reliability": reliability,
            "total_elements": len(elements),
            "avg_selectors_per_element": sum(len(e.selectors) for e in elements) / len(elements)
        }

    async def _save_extraction_result(self, result: ExtractionResult):
        """Save extraction result to file"""
        timestamp = result.extraction_timestamp.strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"extraction_{timestamp}.json"
        
        # Convert to serializable format
        result_dict = asdict(result)
        result_dict['extraction_timestamp'] = result.extraction_timestamp.isoformat()
        
        # Convert datetime fields in elements
        for element in result_dict['elements']:
            element['timestamp'] = datetime.fromisoformat(element['timestamp']).isoformat()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, indent=2, ensure_ascii=False)
        
        print(f"Extraction result saved to: {output_file}")

    async def validate_selectors(self, page: Page, elements: List[ExtractedElement]) -> Dict[str, Any]:
        """Validate all selectors against the current page"""
        validation_results = {}
        
        for element in elements:
            element_results = {}
            
            for selector in element.selectors:
                try:
                    is_valid = await self._validate_single_selector(page, selector)
                    element_results[f"{selector.selector_type.value}_{selector.value[:50]}"] = is_valid
                    selector.validation_status = "valid" if is_valid else "invalid"
                except Exception as e:
                    element_results[f"{selector.selector_type.value}_{selector.value[:50]}"] = False
                    selector.validation_status = "error"
            
            validation_results[element.element_id] = element_results
        
        return validation_results

    async def _validate_single_selector(self, page: Page, selector: ElementSelector) -> bool:
        """Validate a single selector"""
        try:
            if selector.selector_type == SelectorType.CSS:
                elements = await page.query_selector_all(selector.value)
                return len(elements) > 0
            elif selector.selector_type == SelectorType.XPATH:
                elements = await page.query_selector_all(f"xpath={selector.value}")
                return len(elements) > 0
            elif selector.selector_type == SelectorType.TEXT:
                # Text selector validation
                script = f"""
                () => {{
                    const walker = document.createTreeWalker(
                        document.body,
                        NodeFilter.SHOW_TEXT,
                        null,
                        false
                    );
                    
                    let node;
                    while (node = walker.nextNode()) {{
                        if (node.textContent.includes('{selector.value}')) {{
                            return true;
                        }}
                    }}
                    return false;
                }}
                """
                return await page.evaluate(script)
            else:
                # For other selector types, try as CSS attribute selector
                css_selector = f"[{selector.value}]"
                elements = await page.query_selector_all(css_selector)
                return len(elements) > 0
                
        except Exception:
            return False


# Example usage
async def example_usage():
    """Example usage of MultiSelectorExtractor"""
    
    # Initialize extractor
    extractor = MultiSelectorExtractor(
        output_dir="./selector_output",
        enable_validation=True,
        max_selectors_per_element=6
    )
    
    # Create browser session
    browser_profile = BrowserProfile()
    browser_session = BrowserSession(browser_profile)
    
    try:
        # Get page
        page = await browser_session.get_current_page()
        await page.goto("https://example.com")
        
        # Extract elements and selectors
        result = await extractor.extract_from_page(page)
        
        print(f"Extracted {result.total_elements} elements")
        print(f"Quality metrics: {result.quality_metrics}")
        
        # Show some examples
        for i, element in enumerate(result.elements[:3]):
            print(f"\nElement {i+1} ({element.properties.tag_name}):")
            print(f"  Text: {element.properties.text_content[:50]}...")
            print(f"  Selectors ({len(element.selectors)}):")
            for selector in element.selectors[:3]:
                print(f"    {selector.selector_type.value}: {selector.value} (reliability: {selector.reliability_score:.2f})")
        
        # Validate selectors
        validation_results = await extractor.validate_selectors(page, result.elements[:5])
        print(f"\nValidation results for first 5 elements: {len(validation_results)} elements validated")
        
    finally:
        await browser_session.close()


if __name__ == "__main__":
    print("Multi Selector Extractor - Example Usage")
    print("=" * 45)
    
    asyncio.run(example_usage())