#!/usr/bin/env python3
"""
Test Runner for STR Compliance Toolkit

Provides an easy way to run tests with coverage reporting and different test categories.
"""

import sys
import subprocess
import argparse


def run_tests(test_type='all', coverage=False, verbose=False):
    """
    Run tests with specified options.
    
    Args:
        test_type: Type of tests to run ('all', 'unit', 'api', 'integration')
        coverage: Whether to run with coverage reporting
        verbose: Whether to run in verbose mode
    """
    cmd = ['python', '-m', 'pytest']
    
    # Add test type markers
    if test_type != 'all':
        cmd.extend(['-m', test_type])
    
    # Add coverage options
    if coverage:
        cmd.extend(['--cov=app', '--cov=models', '--cov-report=html', '--cov-report=term'])
    
    # Add verbosity
    if verbose:
        cmd.append('-v')
    else:
        cmd.append('-q')
    
    # Add test directory
    cmd.append('tests/')
    
    print(f"Running command: {' '.join(cmd)}")
    return subprocess.run(cmd)


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description='Run STR Compliance Toolkit tests')
    parser.add_argument('--type', choices=['all', 'unit', 'api', 'integration'],
                       default='all', help='Type of tests to run')
    parser.add_argument('--coverage', action='store_true',
                       help='Run with coverage reporting')
    parser.add_argument('--verbose', action='store_true',
                       help='Run in verbose mode')
    
    args = parser.parse_args()
    
    # Install test dependencies if needed
    print("Installing test dependencies...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                  capture_output=True)
    
    # Run tests
    result = run_tests(args.type, args.coverage, args.verbose)
    
    if result.returncode == 0:
        print("\n✅ All tests passed!")
        if args.coverage:
            print("📊 Coverage report generated in htmlcov/index.html")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)


if __name__ == '__main__':
    main() 