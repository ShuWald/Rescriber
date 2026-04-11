# Installation Guide

Please refer to the installation sample video for guidance: [https://drive.google.com/file/d/1Jwx-GTh2EWEWsK7heWo2LndlECKfATM-/view?usp=sharing](https://drive.google.com/file/d/1Jwx-GTh2EWEWsK7heWo2LndlECKfATM-/view?usp=sharing)

## **Prerequisites**

1. **Install Python 3:**

   - Download Python 3 from [https://www.python.org/downloads/](https://www.python.org/downloads/).
   - Ensure you can run Python scripts using the command line:
     ```bash
     python3 --version
     ```
   - Ensure `pip3` is available for installing dependencies:  
     [https://pypi.org/project/pip/](https://pypi.org/project/pip/).

2. **Install Ollama:**

   - Download and install Ollama from [https://ollama.com/download/Ollama-darwin.zip](https://ollama.com/download/Ollama-darwin.zip).
   - Once you see that Ollama is running, please open a Terminal window, and type the following command:
     ```bash
     ollama pull llama3
     ```

3. **Install Google Chrome:**
   - Ensure Chrome is installed and and it will later be closed before using the tool.

---

## **Steps**

1. **Download and Set Up Frontend:**

   - Download the ZIP file from [https://github.com/jigglypuff96/Rescriber_frontend/archive/refs/heads/ondevice.zip](https://github.com/jigglypuff96/Rescriber_frontend/archive/refs/heads/ondevice.zip).
   - Unzip it inside your Mac's `Downloads` folder.

2. **Download and Set Up Backend:**

   - Download the ZIP file from [https://github.com/jigglypuff96/Rescriber_backend/archive/refs/heads/main.zip](https://github.com/jigglypuff96/Rescriber_backend/archive/refs/heads/main.zip).
   - Unzip it inside your Mac's `Downloads` folder.

3. **Start the Backend Server:**

   - Open **Terminal** and type the following commands line by line:
     1. Go to the folder that contains Rescriber backend files
     ```bash
     cd ~/Downloads/Rescriber_backend-main
     ```
     2. Pip install all the necessary dependencies:
     ```bash
     python3 -m pip install -r requirements.txt
     ```
     3. Start running the python server
     ```bash
     python3 prod.py
     ```
   - Wait for the message `"Initialization complete. Now you can start using the tool!"` to appear in the terminal. It might take around 1 minute. If you see any errors, contact the research team.

4. **Close and Launch Chrome with SSL Error Ignored:**

   - Open a new **Terminal** and type the following command line by line. Please feel free to copy the current link [https://github.com/jigglypuff96/Rescriber_frontend/tree/ondevice](https://github.com/jigglypuff96/Rescriber_frontend/tree/ondevice), as well as the two commands, into any text editor or open the link in Safari. This way, you'll still have access to them if Chrome is closed. The second command will automatically reopen Chrome: 
     ```bash
     killall Google\ Chrome
     open -a "Google Chrome" --args --ignore-certificate-errors
     ```

5. **Install the Chrome Extension:**

   - Once Chrome is opened, you will see a notification indicating that you are using the --ignore-certificate-errors flag. This is normal and nothing to worry about; it is required because the extension is currently under development, and this flag allows us to bypass certain production-level security checks during testing.
   - Leave the current tab unchanged, and open a new tab, go to [chrome://extensions](chrome://extensions)
   - Follow the instructions at [https://github.com/jigglypuff96/Rescriber_frontend/blob/ondevice/InstallChromeExtension.md](https://github.com/jigglypuff96/Rescriber_frontend/blob/ondevice/InstallChromeExtension.md) to install the extension.
   - Verify that the extension **"Rescriber"** appears in the list of installed extensions.

6. **Start Chatting:**
   - Navigate to [https://chat.openai.com/](https://chat.openai.com/).
   - Check the bottom-right corner of the page for a green circle.
     - If you don’t see it, refresh the page.
     - If it still doesn’t appear, contact the research team.
   - Use this link to copy and paste content into the chat:  
     [https://docs.google.com/document/d/1_rLaj6Ap0zFebnS-yZTCbe9Sz1-O4-aBKdyJdbjVvu0/edit?usp=sharing](https://docs.google.com/document/d/1_rLaj6Ap0zFebnS-yZTCbe9Sz1-O4-aBKdyJdbjVvu0/edit?usp=sharing).

---

# Post-study data sharing

Please open ~/Downloads/Rescriber_backend-main folder, and share with us the timing log "timing.txt" with the researcher.
A sample timing log contains contents like this: 
2024-11-26 00:02:59 - Result chunk: {'results': []} (Time: 61.62s)
2024-11-26 00:03:17 - Detect request received!
2024-11-26 00:03:22 - Result chunk: {'results': [{'entity_type': 'NAME', 'text': 'Lisa'}]} (Time: 4.66s)

---

# Uninstallation Guide

Please refer to the uninstallation sample videos for guidance:
1. [https://drive.google.com/file/d/1FDaqUF6ypkoK3wF0TIQ8q-V_rkGpi0SC/view?usp=sharing](https://drive.google.com/file/d/1FDaqUF6ypkoK3wF0TIQ8q-V_rkGpi0SC/view?usp=sharing) 
2. [https://drive.google.com/file/d/1NZwrO-kMh2j4HEN9AhQaPu-i9jKyUMOg/view?usp=sharing](https://drive.google.com/file/d/1NZwrO-kMh2j4HEN9AhQaPu-i9jKyUMOg/view?usp=sharing)


## **Stop the Backend Server**

1. Open the **same terminal** where you ran `python prod.py`.
2. Press `Control + C` to stop the server.

---

## **Remove Backend and Frontend Files**

1. **Locate the files:**

   - The backend files are in the `~/Downloads/Rescriber_backend-main` folder.
   - The frontend files are in the `~/Downloads/Rescriber_frontend-ondevice` folder.

2. **Delete the folders:**
   - Drag both folders to the Trash.

---

## **Uninstall the Chrome Extension**

1. Go to [chrome://extensions](chrome://extensions).
2. Locate the extension named **"Rescriber"**.
3. Click **Remove** to uninstall it.

---

## **Optional Uninstall Steps**

If you installed Python, Ollama, or Google Chrome specifically for this task, you can uninstall them as follows:

1. **Uninstall Python:**

   - **If installed using `brew`:**
     ```bash
     brew uninstall python
     ```
   - **If installed manually:**
     - Open Finder and go to `/Library/Frameworks/Python.framework/Versions/`.
     - Delete the folder corresponding to the Python version you installed.
     - Remove the `python3` or `python` binary from `/usr/local/bin/`.

2. **Uninstall Ollama:**

   - Find the Ollama app in your Applications and Downloads folder.
   - Drag it to the Trash.

3. **Uninstall Google Chrome:**
   - Find the Chrome app in your Applications folder.
   - Drag it to the Trash.
