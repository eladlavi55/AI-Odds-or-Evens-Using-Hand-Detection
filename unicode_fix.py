#!/usr/bin/env python3
"""
Unicode Encoding Fix for Windows Systems
==========================================

This module provides comprehensive Unicode support for Windows console applications
that need to display emojis and other Unicode characters.

The main issue is that Windows PowerShell and Command Prompt use the 'charmap' codec
by default, which can't encode Unicode characters like emojis (U+1F44B, etc.).

Usage:
    from unicode_fix import initialize_unicode
    initialize_unicode()
    
    # Now you can safely print Unicode characters
    print("🎮 Game started!")
"""

import sys
import os
import locale
import io
import codecs

def set_environment_variables():
    """Set environment variables to force UTF-8 encoding"""
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'
    
    # For Windows specifically
    if sys.platform.startswith('win'):
        os.environ['PYTHONLEGACYWINDOWSSTDIO'] = '0'

def configure_console_encoding():
    """Configure console encoding for Windows"""
    if sys.platform.startswith('win'):
        try:
            # Try to set console code page to UTF-8
            import subprocess
            result = subprocess.run(['chcp', '65001'], 
                                  shell=True, 
                                  capture_output=True, 
                                  text=True)
            if result.returncode == 0:
                print("[INFO] Console code page set to UTF-8 (65001)")
            else:
                print("[WARNING] Could not set console code page to UTF-8")
        except Exception as e:
            print(f"[WARNING] Error setting console code page: {e}")

def reconfigure_streams():
    """Reconfigure stdout and stderr for UTF-8"""
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
            print("[INFO] Streams reconfigured for UTF-8")
        else:
            # For older Python versions
            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer, 
                encoding='utf-8', 
                errors='replace',
                line_buffering=True
            )
            sys.stderr = io.TextIOWrapper(
                sys.stderr.buffer, 
                encoding='utf-8', 
                errors='replace',
                line_buffering=True
            )
            print("[INFO] Streams wrapped for UTF-8 (legacy method)")
    except Exception as e:
        print(f"[WARNING] Could not reconfigure streams: {e}")

def set_locale():
    """Set locale to UTF-8"""
    try:
        # Try different UTF-8 locales
        for loc in ['en_US.UTF-8', 'C.UTF-8', 'UTF-8']:
            try:
                locale.setlocale(locale.LC_ALL, loc)
                print(f"[INFO] Locale set to: {loc}")
                return
            except locale.Error:
                continue
        print("[WARNING] Could not set UTF-8 locale")
    except Exception as e:
        print(f"[WARNING] Error setting locale: {e}")

def create_safe_print():
    """Create a safe print function that handles Unicode gracefully"""
    
    # Emoji fallback mapping
    EMOJI_FALLBACKS = {
        '🎮': '[GAME]',
        '🤖': '[ROBOT]',
        '✅': '[OK]',
        '❌': '[ERROR]',
        '⚠️': '[WARNING]',
        '🔍': '[SEARCH]',
        '🔄': '[RELOAD]',
        '🚦': '[TEST]',
        '🔊': '[SOUND]',
        '🔘': '[BUTTON]',
        '🧹': '[CLEANUP]',
        '🎉': '[SUCCESS]',
        '👋': '[WAVE]',
        '🧪': '[TEST]',
        '💡': '[TIP]',
        '📦': '[INSTALL]',
        '📷': '[CAMERA]',
        '📁': '[FOLDER]',
        '🚀': '[START]',
        '📖': '[INFO]',
        '🎭': '[REACTION]',
    }
    
    def safe_print(*args, **kwargs):
        """Print function that handles Unicode encoding errors gracefully"""
        try:
            # First try normal print
            print(*args, **kwargs)
        except UnicodeEncodeError:
            # If that fails, replace emojis with fallbacks
            safe_args = []
            for arg in args:
                if isinstance(arg, str):
                    safe_str = str(arg)
                    for emoji, fallback in EMOJI_FALLBACKS.items():
                        safe_str = safe_str.replace(emoji, fallback)
                    safe_args.append(safe_str)
                else:
                    safe_args.append(arg)
            
            try:
                print(*safe_args, **kwargs)
            except UnicodeEncodeError:
                # Final fallback - encode to ASCII with errors ignored
                ascii_args = []
                for arg in safe_args:
                    if isinstance(arg, str):
                        ascii_args.append(arg.encode('ascii', errors='replace').decode('ascii'))
                    else:
                        ascii_args.append(str(arg))
                print(*ascii_args, **kwargs)
    
    return safe_print

def initialize_unicode():
    """Initialize Unicode support for the application"""
    print("[INIT] Initializing Unicode support...")
    
    # Step 1: Set environment variables
    set_environment_variables()
    
    # Step 2: Configure console (Windows specific)
    configure_console_encoding()
    
    # Step 3: Set locale
    set_locale()
    
    # Step 4: Reconfigure streams
    reconfigure_streams()
    
    print("[SUCCESS] Unicode initialization completed!")
    
    # Return safe_print function
    return create_safe_print()

# Create global safe_print function
safe_print = create_safe_print()

# Auto-initialize when module is imported
if __name__ != "__main__":
    try:
        initialize_unicode()
    except Exception as e:
        print(f"[WARNING] Unicode initialization failed: {e}")

# Test function
def test_unicode():
    """Test Unicode functionality"""
    print("\n" + "="*60)
    print("UNICODE FUNCTIONALITY TEST")
    print("="*60)
    
    test_emojis = [
        "🎮 Game emoji",
        "🤖 Robot emoji", 
        "✅ Success emoji",
        "❌ Error emoji",
        "👋 Wave emoji"
    ]
    
    print("\nTesting regular print:")
    for emoji_text in test_emojis:
        try:
            print(f"  {emoji_text}")
        except UnicodeEncodeError as e:
            print(f"  ERROR: {e}")
    
    print("\nTesting safe_print:")
    for emoji_text in test_emojis:
        safe_print(f"  {emoji_text}")
    
    print("\n" + "="*60)
    print("Test completed!")

if __name__ == "__main__":
    # Run test if script is executed directly
    initialize_unicode()
    test_unicode() 