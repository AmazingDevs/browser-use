#!/usr/bin/env python3
"""
Basic usage example for the Exploratory QA Test Case Generator POC.

This script demonstrates how to use the ExploratoryQAGenerator to perform
automated exploratory testing on web applications and generate test cases.
"""

import asyncio
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the POC modules
import sys
sys.path.append(str(Path(__file__).parent.parent / "src"))

from exploratory_qa_generator import ExploratoryQAGenerator
from test_models import TestCaseFormatter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
)
logger = logging.getLogger(__name__)

async def basic_example():
    """Basic example of exploratory testing."""
    logger.info("🚀 Starting basic exploratory testing example...")
    
    try:
        # Initialize the generator with shorter timeout
        generator = ExploratoryQAGenerator(
            timeout=120  # Reduced from 300 to 120 seconds
        )
        
        # Run exploratory testing with sufficient steps for proper exploration
        result = await asyncio.wait_for(
            generator.generate_exploratory_tests(
                url="https://www.saucedemo.com",
                max_steps=10  # Increased for proper exploration
            ),
            timeout=300  # 5 minute timeout for proper exploration
        )
        
    except asyncio.TimeoutError:
        logger.error("⏰ Basic example timed out - this is normal for initial runs")
        raise
    except Exception as e:
        logger.error(f"❌ Example failed: {e}")
        raise

async def main():
    """Main function to run the examples."""
    await basic_example()
    return

if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Exploratory QA Test Case Generator POC")
    parser.add_argument(
        "--mode", 
        choices=["sequential", "parallel", "quick"], 
        default="sequential",
        help="Execution mode: sequential (default), parallel, or quick"
    )
    args = parser.parse_args()
    
    # Ensure outputs directory exists
    Path("outputs").mkdir(exist_ok=True)
    
    # Display mode information
    mode_info = {
        "sequential": "🔄 Sequential mode - run examples one by one (safest, slower)",
        "parallel": "⚡ Parallel mode - run all examples concurrently (faster, more resource intensive)",
        "quick": "🚀 Quick mode - run only basic example (fastest, for validation)"
    }
    
    print(f"\n{mode_info[args.mode]}")
    print("=" * 60)
    
    # Run examples
    start_time = asyncio.get_event_loop().time() if hasattr(asyncio.get_event_loop(), 'time') else 0
    results = asyncio.run(main(mode=args.mode))
    
    print("\n" + "=" * 60)
    print("🚀 POC EXAMPLES COMPLETED")
    print("=" * 60)
    print(f"🎯 Mode: {args.mode}")
    print("📋 Check logs above for detailed results")
    print("📁 Generated files are in the 'outputs/' directory")
    print("🎭 Playwright scripts are in 'outputs/playwright_scripts/'")
    print("\n💡 Usage tips:")
    print("   python basic_usage.py --mode quick     # Fastest validation")
    print("   python basic_usage.py --mode parallel  # All examples concurrently") 
    print("   python basic_usage.py --mode sequential # Safe sequential execution")
    print("=" * 60)