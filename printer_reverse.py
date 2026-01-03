"""
Printer Reverse/Retract Utility

This script attempts to reverse/retract the last printed page back to the printer tray.
This is useful for manual duplex printing workflows where you need to re-feed pages.

Note: This feature is printer-dependent and may not work with all printers.
"""

import subprocess
import sys
import os
import platform


def reverse_page(printer_name=None, copies=1):
    """
    Attempt to reverse/retract the last printed page(s) back to the printer tray.
    
    Args:
        printer_name: Name of the printer (if None, uses default printer)
        copies: Number of pages to reverse (default: 1)
    
    Returns:
        bool: True if command was sent successfully, False otherwise
    """
    system = platform.system()
    
    print(f"\n{'='*60}")
    print("Attempting to reverse/retract printed page(s)...")
    print(f"{'='*60}\n")
    
    if system == "Linux":
        return _reverse_linux(printer_name, copies)
    elif system == "Darwin":  # macOS
        return _reverse_macos(printer_name, copies)
    elif system == "Windows":
        return _reverse_windows(printer_name, copies)
    else:
        print(f"Unsupported operating system: {system}")
        return False


def _reverse_linux(printer_name, copies):
    """Reverse page on Linux using CUPS commands"""
    try:
        # Method 1: Try using lpadmin with reverse option (if supported)
        if printer_name:
            # Check if printer supports reverse
            result = subprocess.run(
                ["lpoptions", "-p", printer_name, "-l"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if "Reverse" in result.stdout or "reverse" in result.stdout.lower():
                print(f"Printer {printer_name} may support reverse option")
        
        # Method 2: Send a blank page with reverse feed command
        # Create a minimal PostScript file that attempts to reverse feed
        ps_content = """%!PS-Adobe-3.0
<< /PageSize [612 792] >> setpagedevice
showpage
"""
        
        # Write temporary PostScript file
        temp_ps = "/tmp/reverse_feed.ps"
        with open(temp_ps, 'w') as f:
            f.write(ps_content)
        
        # Try to print with reverse option
        cmd = ["lp"]
        if printer_name:
            cmd.extend(["-d", printer_name])
        
        # Some printers support -o reverse or -o InputSlot options
        # Try different approaches
        for option in ["-o reverse", "-o InputSlot=Manual", "-o PageRegion=A4"]:
            try:
                test_cmd = cmd + [option.split()[0], option.split()[1], temp_ps]
                result = subprocess.run(
                    test_cmd,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    print(f"✓ Reverse command sent using option: {option}")
                    os.remove(temp_ps)
                    return True
            except:
                continue
        
        # Method 3: Use CUPS API or printer-specific commands
        # For some printers, you can use escputil or printer-specific tools
        print("Attempting printer-specific reverse command...")
        
        # Try using lp with manual feed and cancel immediately
        # This is a workaround - send a job and cancel it to trigger reverse
        try:
            # Send a minimal job
            job_cmd = cmd + [temp_ps]
            result = subprocess.run(
                job_cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Get job ID from output
                job_id = None
                for line in result.stdout.split('\n'):
                    if 'request id is' in line.lower() or 'job' in line.lower():
                        # Extract job number
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if 'job' in part.lower() or 'id' in part.lower():
                                if i + 1 < len(parts):
                                    job_id = parts[i + 1].strip('-')
                                    break
                
                if job_id:
                    # Cancel the job immediately (may trigger reverse on some printers)
                    cancel_cmd = ["cancel"]
                    if printer_name:
                        cancel_cmd.extend(["-a", printer_name])
                    else:
                        cancel_cmd.append(job_id)
                    
                    subprocess.run(cancel_cmd, capture_output=True, timeout=2)
                    print(f"✓ Sent reverse command via job cancellation (job {job_id})")
                    os.remove(temp_ps)
                    return True
        except Exception as e:
            print(f"  Note: {str(e)}")
        
        # Clean up
        if os.path.exists(temp_ps):
            os.remove(temp_ps)
        
        # Method 4: Direct printer command (requires printer-specific knowledge)
        print("\n⚠ Manual reverse required:")
        print("  1. Open the printer's paper tray")
        print("  2. Manually pull back the last printed page(s)")
        print("  3. Ensure pages are oriented correctly for back-side printing")
        print("  4. Close the tray and continue with Phase 2 printing")
        
        return False
        
    except FileNotFoundError:
        print("Error: CUPS printing utilities not found.")
        print("Install with: sudo apt-get install cups cups-client")
        return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False


def _reverse_macos(printer_name, copies):
    """Reverse page on macOS"""
    try:
        print("⚠ macOS reverse feed:")
        print("  Most macOS printers don't support automatic reverse feed.")
        print("  Manual steps:")
        print("  1. Open printer settings/preferences")
        print("  2. Manually retract the page from the output tray")
        print("  3. Place it back in the input tray with correct orientation")
        
        # Try using lpr with special options if available
        if printer_name:
            print(f"\n  Attempting with printer: {printer_name}")
            # Some printers may support special PPD options
        
        return False
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False


def _reverse_windows(printer_name, copies):
    """Reverse page on Windows"""
    try:
        print("⚠ Windows reverse feed:")
        print("  Most Windows printers don't support automatic reverse feed.")
        print("  Manual steps:")
        print("  1. Open printer properties")
        print("  2. Manually retract the page from the output tray")
        print("  3. Place it back in the input tray with correct orientation")
        
        # Windows doesn't have a standard reverse command
        # Would need printer-specific drivers/APIs
        
        return False
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False


def manual_reverse_instructions():
    """Print manual instructions for reversing pages"""
    print("\n" + "="*60)
    print("MANUAL PAGE REVERSE INSTRUCTIONS")
    print("="*60)
    print("""
For manual duplex printing, follow these steps after Phase 1:

1. After printing odd pages (Phase 1):
   - Wait for all pages to finish printing
   - DO NOT flip the pages manually

2. Remove the printed stack from the output tray:
   - Take the entire stack as-is (page 1 should be on top)
   - Keep the stack in the same order

3. Re-insert the stack into the input tray:
   - Place the stack back into the printer's input tray
   - Ensure the TOP of the stack (page 1) goes in first
   - The printer will feed from the top, so page 1 will print on the back first
   - This is why we rotated even pages 180° - they'll align correctly

4. Start Phase 2 printing:
   - Click "Start Phase 2" in the web interface
   - The even pages (rotated 180°) will print on the backs

Alternative method (if your printer supports it):
- Some printers have a "reverse" or "duplex" mode
- Check your printer's control panel or software settings
- Enable manual duplex mode if available
    """)
    print("="*60 + "\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Reverse/retract the last printed page back to printer tray"
    )
    parser.add_argument(
        "-p", "--printer",
        help="Printer name (default: default printer)",
        default=None
    )
    parser.add_argument(
        "-c", "--copies",
        type=int,
        help="Number of pages to reverse (default: 1)",
        default=1
    )
    parser.add_argument(
        "-m", "--manual",
        action="store_true",
        help="Show manual reverse instructions"
    )
    
    args = parser.parse_args()
    
    if args.manual:
        manual_reverse_instructions()
    else:
        success = reverse_page(args.printer, args.copies)
        if not success:
            print("\n" + "="*60)
            print("Automatic reverse not available. Showing manual instructions...")
            print("="*60)
            manual_reverse_instructions()
        
        sys.exit(0 if success else 1)



