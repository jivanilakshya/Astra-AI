# INSTALL OLLAMA RIGHT NOW - Windows Guide

## ❌ Current Error:
```
Ollama not installed
No connection could be made because the target machine actively refused it
```

## ✅ Solution: Install Ollama (5 minutes)

---

## Step 1: Download Ollama

### Option A: Direct Download (RECOMMENDED)
1. **Open this link in your browser:**
   ```
   https://ollama.com/download/windows
   ```

2. **Click the big "Download for Windows" button**

3. **You'll download**: `OllamaSetup.exe` (~200 MB)

### Option B: PowerShell Download
```powershell
# Download Ollama installer
Invoke-WebRequest -Uri "https://ollama.com/download/OllamaSetup.exe" -OutFile "$env:TEMP\OllamaSetup.exe"

# Run installer
Start-Process "$env:TEMP\OllamaSetup.exe"
```

---

## Step 2: Install Ollama

1. **Run `OllamaSetup.exe`** (from Downloads folder or temp)

2. **Click through installer:**
   - Click "Next"
   - Accept license
   - Click "Install"
   - Wait for installation (~30 seconds)
   - Click "Finish"

3. **Ollama will install to**: `C:\Users\YourName\AppData\Local\Programs\Ollama\`

4. **System tray icon**: You'll see Ollama icon in system tray (bottom-right)

---

## Step 3: Start Ollama Server

After installation, Ollama should auto-start. If not:

```powershell
# Start Ollama server
ollama serve
```

**Keep this terminal open!** (Ollama server needs to run in background)

---

## Step 4: Download LLaMA 3 Model

**Open a NEW PowerShell window** and run:

```powershell
# Download llama3 model (~4.7 GB)
ollama pull llama3
```

**This will take 10-15 minutes** depending on your internet speed.

You'll see progress:
```
pulling manifest
pulling 6a0746a1ec1a... 100% ▕████████████████▏ 4.7 GB
verifying sha256 digest
writing manifest
success
```

---

## Step 5: Verify Installation

```powershell
# Check Ollama version
ollama --version

# List installed models
ollama list

# Test the model
ollama run llama3 "Hello, test!"
```

Expected output:
```
NAME            ID              SIZE      MODIFIED
llama3:latest   xxxxx           4.7 GB    X minutes ago
```

---

## Step 6: Test Astra-AI Integration

```powershell
# Navigate to project
cd "D:\CHARUSAT\Sem-6\Astra AI"

# Run test script again
python test_ollama.py
```

**NOW ALL TESTS SHOULD PASS! ✅**

---

## 🚨 Troubleshooting

### Error: "ollama: command not found"
**Solution**: Close and reopen PowerShell after installation

### Error: "Connection refused"
**Solution**: Start Ollama server in another terminal:
```powershell
ollama serve
```

### Error: "Model not found"
**Solution**: Download the model:
```powershell
ollama pull llama3
```

---

## ⚡ Quick Install (Copy-Paste All)

```powershell
# 1. Download installer
Invoke-WebRequest -Uri "https://ollama.com/download/OllamaSetup.exe" -OutFile "$env:TEMP\OllamaSetup.exe"

# 2. Run installer (follow GUI prompts)
Start-Process "$env:TEMP\OllamaSetup.exe" -Wait

# 3. Close this PowerShell and open a NEW one, then:

# 4. Start server (in Terminal 1, keep running)
ollama serve

# 5. In NEW Terminal 2, download model
ollama pull llama3

# 6. Test it
ollama run llama3 "Test"

# 7. Test Astra-AI
cd "D:\CHARUSAT\Sem-6\Astra AI"
python test_ollama.py
```

---

## 🎯 After Installation

Once `python test_ollama.py` shows **ALL PASS**, run:

```powershell
# See real AI in action!
python main.py --interactive
```

**Enter a question** and watch it generate REAL answers with REAL scores! 🎉
