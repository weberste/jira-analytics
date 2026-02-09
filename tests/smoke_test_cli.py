#!/usr/bin/env python3
"""Cross-platform CLI smoke tests against real JIRA."""

import argparse
import subprocess
import sys
import time


def run_tests(jql: str, from_date: str, to_date: str, verbose: bool = False):
    tests = [
        ("help", ["--help"]),
        ("analyze help", ["utilization", "--help"]),
        ("config show", ["config", "show"]),
        ("basic analyze", ["utilization", "--jql", jql, "--from", from_date, "--to", to_date]),
        ("analyze no-cache", ["utilization", "--jql", jql, "--from", from_date, "--to", to_date, "--no-cache"]),
        ("analyze track-epic-time", ["utilization", "--jql", jql, "--from", from_date, "--to", to_date, "--track-epic-time"]),
        ("analyze csv output", ["utilization", "--jql", jql, "--from", from_date, "--to", to_date, "--output", "csv"]),
        ("analyze all options", ["utilization", "--jql", jql, "--from", from_date, "--to", to_date, "--no-cache", "--track-epic-time", "--output", "csv"]),
    ]

    failed = []
    total_time = 0

    for desc, args in tests:
        cmd = ["jira-analyzer"] + args
        print(f"Testing: {desc}...", end=" ", flush=True)

        start = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        elapsed = time.time() - start
        total_time += elapsed

        if result.returncode == 0:
            print(f"OK ({elapsed:.1f}s)")
            if verbose:
                print(f"  Output: {result.stdout[:200]}...")
        else:
            print(f"FAILED ({elapsed:.1f}s)")
            failed.append((desc, result.stderr or result.stdout))
            if verbose:
                print(f"  Error: {result.stderr or result.stdout}")

    print(f"\n{'=' * 40}")
    if failed:
        print(f"{len(failed)}/{len(tests)} test(s) failed:")
        for desc, output in failed:
            print(f"  - {desc}")
            print(f"    {output[:300]}")
        sys.exit(1)
    else:
        print(f"All {len(tests)} tests passed in {total_time:.1f}s")


def main():
    parser = argparse.ArgumentParser(description="CLI smoke tests against real JIRA")
    parser.add_argument("jql", help="JQL query to test with (e.g., 'project = TEST')")
    parser.add_argument("--from", dest="from_date", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--to", dest="to_date", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show command output")

    args = parser.parse_args()
    run_tests(args.jql, args.from_date, args.to_date, args.verbose)


if __name__ == "__main__":
    main()
