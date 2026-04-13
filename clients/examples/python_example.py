#!/usr/bin/env python3
"""
MeshCloud Python Client Example

This example demonstrates how to use the MeshCloud Python client library
to upload files, check file existence, and monitor system health.
"""

import asyncio
import os
from pathlib import Path

from meshcloud_client import MeshCloudClient, MeshCloudError


async def main():
    """Main example function demonstrating MeshCloud client usage."""

    # Configuration
    base_url = os.getenv("MESH_CLOUD_URL", "https://localhost:8000")
    username = os.getenv("MESH_CLOUD_USER", "admin")
    password = os.getenv("MESH_CLOUD_PASS", "admin")

    print("🚀 MeshCloud Python Client Example")
    print("=" * 40)

    try:
        # Initialize client with authentication
        print(f"📡 Connecting to {base_url}...")
        client = MeshCloudClient(base_url, username=username, password=password)

        # Test connection and authentication
        print("🔐 Authenticating...")
        status = await client.get_status()
        print(f"✅ Connected to node: {status['node']} v{status['version']}")
        print(f"🌐 Peers connected: {status['peers']}")

        # Health check
        print("\n🏥 Performing health check...")
        health = await client.health_check()
        print(f"💚 System health: {health['status']}")

        # Upload a file
        print("\n📤 Uploading a file...")

        # Create a sample file
        sample_content = b"Hello, MeshCloud! This is a test file for the Python client example."
        sample_file = Path("sample_upload.txt")
        sample_file.write_bytes(sample_content)

        try:
            # Upload with progress callback
            def progress_callback(progress, current, total):
                print(".1f", end="", flush=True)

            result = await client.upload_file(
                sample_file,
                progress_callback=progress_callback
            )
            print(f"\n✅ File uploaded successfully!")
            print(f"🔗 File hash: {result['hash']}")
            print(f"📁 Filename: {result['filename']}")

            # Check file existence
            file_hash = result['hash']
            exists = await client.file_exists(file_hash)
            print(f"🔍 File exists on node: {exists}")

            # Get file locations
            locations = await client.get_file_locations(file_hash)
            print(f"📍 File available on {len(locations)} node(s)")

            # Get upload status (if still uploading)
            if 'upload_id' in result:
                upload_status = await client.get_upload_status(result['upload_id'])
                print(f"📊 Upload chunks completed: {len(upload_status['uploaded_chunks'])}")

        finally:
            # Clean up sample file
            if sample_file.exists():
                sample_file.unlink()

        # Get system metrics
        print("\n📊 Fetching system metrics...")
        metrics = await client.get_metrics('system')
        print(f"🖥️  CPU Usage: {metrics['cpu_percent']:.1f}%")
        print(f"💾 Memory Usage: {metrics['memory_percent']:.1f}%")
        print(f"💿 Disk Usage: {metrics['disk_usage_percent']:.1f}%")

        # Get application metrics
        app_metrics = await client.get_metrics('application')
        print(f"📈 Total Requests: {app_metrics['total_requests']:,}")
        print(f"⚡ Request Rate: {app_metrics['request_rate_per_second']:.2f}/sec")
        print(f"🚨 Error Rate: {app_metrics['error_rate_per_second']:.3f}/sec")

        # Get recent requests
        print("\n📋 Recent API requests:")
        recent = await client.get_recent_requests(limit=3)
        for req in recent['requests'][:3]:
            status_emoji = "✅" if req['status_code'] < 400 else "❌"
            print(f"  {status_emoji} {req['method']} {req['path']} → {req['status_code']} ({req['duration']:.3f}s)")

        print("\n🎉 Example completed successfully!")

    except MeshCloudError as e:
        print(f"❌ MeshCloud error: {e}")
        if hasattr(e, 'status_code'):
            print(f"   Status code: {e.status_code}")
        return 1

    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        return 1

    return 0


def progress_callback_example():
    """Example of using the client with progress callbacks for large files."""

    async def upload_large_file():
        client = MeshCloudClient("https://your-node-url")

        # Custom progress callback
        def on_progress(progress, current_chunk, total_chunks):
            bar_width = 40
            filled = int(bar_width * progress / 100)
            bar = "█" * filled + "░" * (bar_width - filled)
            print(".1f", end="\r", flush=True)

        # Upload large file with progress
        result = await client.upload_file(
            "large_dataset.zip",
            progress_callback=on_progress
        )

        print(f"\n✅ Large file uploaded: {result['hash']}")
        return result

    # Uncomment to run:
    # asyncio.run(upload_large_file())


def batch_upload_example():
    """Example of batch uploading multiple files."""

    async def upload_batch(files):
        client = MeshCloudClient("https://your-node-url")

        results = []
        for i, file_path in enumerate(files, 1):
            print(f"📤 Uploading {i}/{len(files)}: {file_path}")
            try:
                result = await client.upload_file(file_path)
                results.append(result)
                print(f"  ✅ {result['hash']}")
            except Exception as e:
                print(f"  ❌ Failed: {e}")

        return results

    # Usage:
    # files = ["file1.txt", "file2.jpg", "file3.pdf"]
    # results = asyncio.run(upload_batch(files))


if __name__ == "__main__":
    # Run main example
    exit_code = asyncio.run(main())

    # Uncomment to run other examples:
    # progress_callback_example()
    # batch_upload_example()

    exit(exit_code)