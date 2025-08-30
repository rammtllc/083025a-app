import os
import subprocess

def run_script(script_name):
    """Run a Python script by name."""
    try:
        subprocess.run(["python", script_name], check=True)
    except subprocess.CalledProcessError:
        print(f"Error running {script_name}")
    input("\nPress Enter to return to the menu...")

def main_menu():
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("=== Python Script Launcher ===")
        print("1. Channel Research")
        print("2. Video Research")
        print("3. Get Audio")
        print("4. Timestamp by word")
        print("5. Timestamp by sentence")
        print("6. Create fine-tune JSON")
        print("7. Check fine-tune JSON")
        print("8. Upload fine-tune JSON")
        print("9. Generate Script")
        print("10. Generate Outline")
        print("0. Exit")
        choice = input("Enter your choice: ")

        if choice == "1":
            run_script("cinfo.py")
        if choice == "2":
            run_script("vinfo.py")
        if choice == "3":
            run_script("ytb.py")
        elif choice == "4":
            run_script("transcribe.py")
        elif choice == "5":
            run_script("stime.py")
        elif choice == "6":
            run_script("cjson.py")
        elif choice == "7":
            run_script("scheck.py")
        elif choice == "8":
            run_script("ftupload.py")
        elif choice == "9":
            run_script("outline.py")
        elif choice == "10":
            run_script("survey.py")
        elif choice == "0":
            print("Exiting...")
            break
        else:
            print("Invalid choice! Try again.")
            input("Press Enter to continue...")

if __name__ == "__main__":
    main_menu()
