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
        
        # Display results
        logger.info(f"✅ Generated {len(result['test_cases'])} test scenarios")
        logger.info(f"📊 Total exploration steps: {result['total_steps']}")
        
        if result.get('exploration_summary'):
            summary = result['exploration_summary']
            logger.info(f"🌐 Pages visited: {summary.get('pages_visited', 0)}")
            logger.info(f"🔍 Elements discovered: {summary.get('elements_discovered', 0)}")
        
        # Save results
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / "basic_example_results.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        logger.info(f"💾 Results saved to: {output_file}")
        return result
        
    except asyncio.TimeoutError:
        logger.error("⏰ Basic example timed out - this is normal for initial runs")
        raise
    except Exception as e:
        logger.error(f"❌ Example failed: {e}")
        raise

async def form_testing_example():
    """Example of testing a form-heavy website."""
    logger.info("📝 Starting form testing example...")
    
    try:
        generator = ExploratoryQAGenerator(
            timeout=120  # Reduced timeout
        )
        
        # Test a form-heavy site with sufficient steps
        result = await asyncio.wait_for(
            generator.generate_exploratory_tests(
                url="https://httpbin.org/forms/post",
                max_steps=20  # Increased for proper form exploration
            ),
            timeout=300  # 5 minute timeout
        )
        
        logger.info(f"✅ Form testing completed: {len(result['test_cases'])} scenarios")
        
        # Save form-specific results
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / "form_testing_results.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
            
        return result
        
    except asyncio.TimeoutError:
        logger.error("⏰ Form testing timed out")
        raise
    except Exception as e:
        logger.error(f"❌ Form testing failed: {e}")
        raise

async def generate_playwright_scripts():
    """Example of generating Playwright test scripts from results."""
    logger.info("🎭 Generating Playwright test scripts...")
    
    try:
        # Run basic exploration first with sufficient steps
        generator = ExploratoryQAGenerator(timeout=180)
        result = await asyncio.wait_for(
            generator.generate_exploratory_tests(
                url="https://www.saucedemo.com",
                max_steps=15  # Increased for better script generation
            ),
            timeout=300  # 5 minute timeout
        )
        
        # Generate Playwright scripts
        formatter = TestCaseFormatter()
        scripts_dir = Path("outputs/playwright_scripts")
        scripts_dir.mkdir(parents=True, exist_ok=True)
        
        for i, test_case in enumerate(result['test_cases']):
            script_content = formatter.to_playwright_script(test_case)
            script_file = scripts_dir / f"test_scenario_{i+1}.py"
            
            with open(script_file, 'w') as f:
                f.write(script_content)
            
            logger.info(f"📜 Generated script: {script_file}")
        
        logger.info(f"✅ Generated {len(result['test_cases'])} Playwright scripts")
        return scripts_dir
        
    except asyncio.TimeoutError:
        logger.error("⏰ Script generation timed out")
        raise
    except Exception as e:
        logger.error(f"❌ Script generation failed: {e}")
        raise

async def batch_testing_example():
    """Example of testing multiple URLs in batch."""
    logger.info("🔄 Starting batch testing example...")
    
    test_urls = [
        "https://www.saucedemo.com",
        "https://httpbin.org/get",
        "https://httpbin.org/forms/post"
    ]
    
    generator = ExploratoryQAGenerator(llm_provider="anthropic", timeout=120)
    all_results = []
    
    for i, url in enumerate(test_urls):
        try:
            logger.info(f"🌐 Testing URL {i+1}/{len(test_urls)}: {url}")
            
            # Add timeout for each URL test with sufficient steps
            result = await asyncio.wait_for(
                generator.generate_exploratory_tests(
                    url=url,
                    max_steps=15  # Increased for better batch testing
                ),
                timeout=300  # 5 minute timeout per URL
            )
            
            result['source_url'] = url
            all_results.append(result)
            
            logger.info(f"✅ Completed: {len(result['test_cases'])} test cases")
            
        except asyncio.TimeoutError:
            logger.error(f"⏰ Timeout testing {url}")
            all_results.append({
                'source_url': url,
                'error': 'Timeout after 2.5 minutes',
                'test_cases': [],
                'total_steps': 0
            })
        except Exception as e:
            logger.error(f"❌ Failed testing {url}: {e}")
            all_results.append({
                'source_url': url,
                'error': str(e),
                'test_cases': [],
                'total_steps': 0
            })
    
    # Save batch results
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    
    batch_file = output_dir / "batch_testing_results.json"
    with open(batch_file, 'w') as f:
        json.dump({
            'batch_summary': {
                'total_urls': len(test_urls),
                'successful_tests': len([r for r in all_results if 'error' not in r]),
                'total_test_cases': sum(len(r.get('test_cases', [])) for r in all_results)
            },
            'results': all_results
        }, f, indent=2, default=str)
    
    logger.info(f"💾 Batch results saved to: {batch_file}")
    return all_results

async def performance_testing_example():
    """Example demonstrating performance monitoring."""
    logger.info("⚡ Starting performance testing example...")
    
    import time
    import psutil
    import os
    
    # Monitor resource usage
    process = psutil.Process(os.getpid())
    start_memory = process.memory_info().rss / 1024 / 1024  # MB
    start_time = time.time()
    
    try:
        generator = ExploratoryQAGenerator(timeout=120)
        
        result = await asyncio.wait_for(
            generator.generate_exploratory_tests(
                url="https://www.saucedemo.com",
                max_steps=20  # Increased for performance testing
            ),
            timeout=300  # 5 minute timeout
        )
        
        # Calculate performance metrics
        end_time = time.time()
        end_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        duration = end_time - start_time
        memory_used = end_memory - start_memory
        
        performance_metrics = {
            'execution_time_seconds': round(duration, 2),
            'memory_usage_mb': round(memory_used, 2),
            'test_cases_generated': len(result['test_cases']),
            'steps_executed': result['total_steps'],
            'test_cases_per_second': round(len(result['test_cases']) / duration, 2),
            'steps_per_second': round(result['total_steps'] / duration, 2)
        }
        
        logger.info("📊 Performance Metrics:")
        for metric, value in performance_metrics.items():
            logger.info(f"   {metric}: {value}")
        
        # Save performance results
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)
        
        perf_file = output_dir / "performance_metrics.json"
        with open(perf_file, 'w') as f:
            json.dump({
                'performance_metrics': performance_metrics,
                'test_results': result
            }, f, indent=2, default=str)
        
        logger.info(f"💾 Performance data saved to: {perf_file}")
        return performance_metrics
        
    except asyncio.TimeoutError:
        logger.error("⏰ Performance testing timed out")
        raise
    except Exception as e:
        logger.error(f"❌ Performance testing failed: {e}")
        raise

async def run_examples_parallel():
    """Run examples in parallel for faster execution."""
    logger.info("⚡ Running examples in parallel mode...")
    
    examples = [
        ("Basic Example", basic_example),
        ("Form Testing", form_testing_example),
        ("Playwright Script Generation", generate_playwright_scripts),
        ("Batch Testing", batch_testing_example),
        ("Performance Testing", performance_testing_example)
    ]
    
    # Run all examples concurrently
    tasks = []
    for name, example_func in examples:
        task = asyncio.create_task(example_func(), name=name)
        tasks.append((name, task))
    
    results = {}
    for name, task in tasks:
        try:
            logger.info(f"🚀 Started: {name}")
            result = await asyncio.wait_for(task, timeout=300)  # 5 min per example
            results[name] = {
                'status': 'success',
                'result': result
            }
            logger.info(f"✅ {name} completed successfully!")
        except asyncio.TimeoutError:
            logger.error(f"⏰ {name} timed out after 5 minutes")
            results[name] = {
                'status': 'failed',
                'error': 'Timeout after 5 minutes'
            }
        except Exception as e:
            logger.error(f"❌ {name} failed: {e}")
            results[name] = {
                'status': 'failed',
                'error': str(e)
            }
    
    return results

async def quick_demo():
    """Quick demo mode - just run basic example for fast validation."""
    logger.info("⚡ Quick demo mode - running basic example only...")
    
    try:
        result = await asyncio.wait_for(basic_example(), timeout=300)  # 5 min max
        logger.info("✅ Quick demo completed successfully!")
        return {"Basic Example": {"status": "success", "result": result}}
    except Exception as e:
        logger.error(f"❌ Quick demo failed: {e}")
        return {"Basic Example": {"status": "failed", "error": str(e)}}

async def main(mode="sequential"):
    """Run examples in sequential or parallel mode."""
    logger.info("🎯 Starting Exploratory QA Test Case Generator POC Examples")
    logger.info("=" * 60)
    
    if mode == "quick":
        results = await quick_demo()
    elif mode == "parallel":
        results = await run_examples_parallel()
    else:
        # Sequential mode (original behavior with timeouts)
        examples = [
            ("Basic Example", basic_example),
            ("Form Testing", form_testing_example),
            ("Playwright Script Generation", generate_playwright_scripts),
            ("Batch Testing", batch_testing_example),
            ("Performance Testing", performance_testing_example)
        ]
        
        results = {}
        
        for name, example_func in examples:
            try:
                logger.info(f"\n📋 Running: {name}")
                logger.info("-" * 40)
                
                # Add timeout for each example in sequential mode
                result = await asyncio.wait_for(example_func(), timeout=300)  # 5 min per example
                results[name] = {
                    'status': 'success',
                    'result': result
                }
                
                logger.info(f"✅ {name} completed successfully!")
                
            except asyncio.TimeoutError:
                logger.error(f"⏰ {name} timed out after 5 minutes")
                results[name] = {
                    'status': 'failed',
                    'error': 'Timeout after 5 minutes'
                }
            except Exception as e:
                logger.error(f"❌ {name} failed: {e}")
                results[name] = {
                    'status': 'failed',
                    'error': str(e)
                }
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📈 EXAMPLES SUMMARY")
    logger.info("=" * 60)
    
    successful = sum(1 for r in results.values() if r['status'] == 'success')
    total = len(results)
    
    logger.info(f"✅ Successful: {successful}/{total}")
    logger.info(f"❌ Failed: {total - successful}/{total}")
    
    for name, result in results.items():
        status_icon = "✅" if result['status'] == 'success' else "❌"
        logger.info(f"   {status_icon} {name}")
    
    logger.info("\n🎉 All examples completed!")
    logger.info("📁 Check the 'outputs/' directory for generated files")
    
    return results

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