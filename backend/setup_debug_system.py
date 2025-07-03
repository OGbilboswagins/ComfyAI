#!/usr/bin/env python3
"""
Setup script for ComfyUI Debug System
This script helps you quickly set up the debug system environment
"""
import os
import sys
import subprocess
from pathlib import Path

from custom_nodes.comfyui_copilot.backend.service.database import db_manager


def check_python_version():
    """Check if Python version is 3.8 or higher"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True


def install_dependencies():
    """Install required Python packages"""
    print("\n📦 Installing dependencies...")
    
    requirements_file = Path(__file__).parent / "requirements.txt"
    if not requirements_file.exists():
        print("❌ requirements.txt not found")
        return False
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False


def setup_env_file():
    """Create .env.llm file if it doesn't exist"""
    env_file = Path(__file__).parent / "service" / ".env.llm"
    
    if env_file.exists():
        print(f"✅ Environment file already exists: {env_file}")
        return True
    
    print("\n🔧 Setting up environment file...")
    
    # Create service directory if it doesn't exist
    env_file.parent.mkdir(exist_ok=True)
    
    # Default environment content
    env_content = """# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1

# Model Configuration
DEFAULT_MODEL=gpt-4o-mini

# Database Configuration
DATABASE_PATH=data/workflow_debug.db
"""
    
    try:
        env_file.write_text(env_content)
        print(f"✅ Created environment file: {env_file}")
        print("\n⚠️  Please edit the .env.llm file and add your OpenAI API key")
        return True
    except Exception as e:
        print(f"❌ Failed to create environment file: {e}")
        return False


def setup_database():
    """Initialize the database"""
    print("\n🗄️  Setting up database...")
    
    try:
        
        # Create data directory
        data_dir = Path(__file__).parent / "data"
        data_dir.mkdir(exist_ok=True)
        
        print(f"✅ Database initialized at: {db_manager.db_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to setup database: {e}")
        return False


def check_comfyui():
    """Check if ComfyUI is accessible"""
    print("\n🔍 Checking ComfyUI connection...")
    
    try:
        import requests
        response = requests.get("http://127.0.0.1:8188/object_info", timeout=5)
        if response.status_code == 200:
            print("✅ ComfyUI is running and accessible")
            return True
        else:
            print(f"⚠️  ComfyUI returned status {response.status_code}")
            return False
    except Exception:
        print("⚠️  Cannot connect to ComfyUI at http://127.0.0.1:8188")
        print("   Make sure ComfyUI is running before using the debug system")
        return False


def create_test_script():
    """Create a simple test script"""
    test_script = Path(__file__).parent / "quick_test.py"
    
    if test_script.exists():
        print(f"✅ Test script already exists: {test_script}")
        return True
    
    test_content = '''#!/usr/bin/env python3
"""Quick test script for debug system"""
import asyncio
from backend.service.debug_agent import debug_workflow_errors

async def quick_test():
    # Test workflow with an error
    workflow = {
        "1": {
            "inputs": {"vae_name": "nonexistent_vae.safetensors"},
            "class_type": "VAELoader"
        }
    }
    
    config = {"session_id": "quick_test", "model": "gpt-4o-mini"}
    
    print("Testing debug agent...")
    async for text, ext in debug_workflow_errors(workflow, config):
        if text:
            print(text[-100:] if len(text) > 100 else text)
    
    print("\\nTest completed!")

if __name__ == "__main__":
    asyncio.run(quick_test())
'''
    
    try:
        test_script.write_text(test_content)
        test_script.chmod(0o755)  # Make executable
        print(f"✅ Created test script: {test_script}")
        return True
    except Exception as e:
        print(f"❌ Failed to create test script: {e}")
        return False


def main():
    """Run all setup steps"""
    print("🚀 ComfyUI Debug System Setup")
    print("=" * 50)
    
    steps = [
        ("Python version", check_python_version),
        ("Dependencies", install_dependencies),
        ("Environment file", setup_env_file),
        ("Database", setup_database),
        ("ComfyUI connection", check_comfyui),
        ("Test script", create_test_script),
    ]
    
    results = []
    for name, func in steps:
        print(f"\n📋 {name}:")
        results.append(func())
    
    print("\n" + "=" * 50)
    print("Setup Summary:")
    successful = sum(results)
    total = len(results)
    print(f"✅ Completed: {successful}/{total}")
    
    if successful == total:
        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Edit backend/service/.env.llm and add your OpenAI API key")
        print("2. Make sure ComfyUI is running")
        print("3. Run the test script: python backend/test_debug_system.py")
    else:
        print("\n⚠️  Some setup steps failed. Please check the errors above.")
        if not results[2]:  # env file
            print("\n💡 Tip: Create backend/service/.env.llm manually with:")
            print("   OPENAI_API_KEY=your-key-here")
    
    return successful == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 