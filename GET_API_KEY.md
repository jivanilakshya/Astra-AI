# GET YOUR API KEY - VISUAL GUIDE

## 🔑 Where to Get Your FREE HuggingFace API Key

### Step 1: Open Link
```
https://huggingface.co/settings/tokens
```

### Step 2: Login or Sign Up
- If you don't have account: https://huggingface.co/join
- If you have account: Login with your credentials

### Step 3: Create New Token

Click **"New token"** button

Fill in the form:
```
Token name: Astra-AI-Testing
Token type: Read         <-- SELECT THIS FROM DROPDOWN
```

Click **"Generate"**

### Step 4: Copy Token

You'll see your token like this:
```
hf_AbCdEfGhIjKlMnOpQrStUvWxYz1234567890
```

**Click COPY button** or manually select and copy (Ctrl+C)

---

## 📝 Add to .env File

Your `.env` file should look like this:

```env
# ========================================
# OPEN SOURCE MODEL SETTINGS
# ========================================

# HuggingFace Configuration (RECOMMENDED - Zero PC Load!)
# Get free API key from: https://huggingface.co/settings/tokens
HUGGINGFACE_API_KEY=hf_AbCdEfGhIjKlMnOpQrStUvWxYz1234567890
                    👆👆👆 PASTE YOUR ACTUAL TOKEN HERE 👆👆👆
HUGGINGFACE_MODEL=microsoft/phi-2
```

**IMPORTANT**: 
- Remove the placeholder `hf_your_token_here`
- Paste your ACTUAL token
- Make sure it starts with `hf_`
- NO spaces around the `=`
- SAVE the file after editing (Ctrl+S)

---

## ✅ Verify It Works

Run the test:
```bash
python test_huggingface.py
```

Expected output:
```
✅ API Key found: hf_AbCdEf...67890
✅ huggingface_hub installed
✅ HuggingFaceProvider imported  
✅ API call successful!
✅ Config is set to use Hugging Face

🎉 All tests passed! You're ready to use Astra AI!
```

---

## ❌ Troubleshooting

### "API key not found"
- Make sure you saved the `.env` file (Ctrl+S)
- Check the file is named `.env` not `.env.example`
- Make sure the line starts exactly with: `HUGGINGFACE_API_KEY=`

### "Invalid API key"
- Make sure key starts with `hf_`
- No spaces around the `=` sign
- Copy the full key (about 50 characters)

### "Rate limit exceeded"
- This is normal for free tier
- Wait a few minutes
- Or use smaller model: `google/flan-t5-base`

---

## 🚀 Next: Run Astra AI!

Once test passes, you're ready!

```bash
python main.py --interactive
```

Enter questions and watch the optimization happen with ZERO PC load! 🎉
