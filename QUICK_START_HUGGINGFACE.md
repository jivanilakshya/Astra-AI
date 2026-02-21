# 🚀 Quick Start with Hugging Face (2 Minutes!)

## ✅ **ZERO PC Load Solution - All processing on Hugging Face servers!**

---

## Step 1: Get FREE API Key (1 minute)

### Option A: If you already have a Hugging Face account
1. Go to: **https://huggingface.co/settings/tokens**
2. Click **"New token"**
3. Name: `Astra-AI-Testing`
4. Type: Select **"Read"**
5. Click **"Generate token"**
6. **COPY** the token (starts with `hf_...`)

### Option B: If you don't have an account
1. Go to: **https://huggingface.co/join**
2. Sign up (free)
3. Then follow Option A above

---

## Step 2: Add API Key (30 seconds)

### Create `.env` file:

```bash
# Copy the example file
copy .env.example .env
```

### Edit `.env` file and add your key:

```env
HUGGINGFACE_API_KEY=hf_your_actual_token_here
```

**Replace `hf_your_actual_token_here` with the token you copied!**

---

## Step 3: Verify Setup (30 seconds)

Run the test script:

```bash
python test_huggingface.py
```

You should see:
```
✅ API Key found
✅ huggingface_hub installed
✅ HuggingFaceProvider imported
✅ API call successful!
✅ All tests passed!
```

---

## Step 4: RUN ASTRA AI! 🎉

```bash
python main.py --interactive
```

Enter test questions and watch the magic happen! ✨

---

## 🎯 What You'll See

### With Hugging Face (RECOMMENDED):
```
Using Models:
  Generator: microsoft/phi-2 (fast & efficient)
  Judge: mistralai/Mistral-7B-Instruct (high quality)
  Optimizer: microsoft/phi-2 (fast iterations)

Optimization running...

✅ Iteration 1: Score 6.8/10
✅ Iteration 2: Score 7.5/10
✅ Iteration 3: Score 8.2/10

Final Results:
  Composite Score: 8.2/10 (⬆️ +1.4 improvement!)
  Cost: $0.00 (FREE tier)
  PC Load: ZERO ✅
```

---

## 📊 Multiple Models for Cost Testing

The system is now configured with **3 different models**:

| Agent | Model | Why? |
|-------|-------|------|
| **Generator** | microsoft/phi-2 | Small & fast - generates answers quickly |
| **Judge** | Mistral-7B-Instruct | Medium quality - evaluates accurately |
| **Optimizer** | microsoft/phi-2 | Fast optimization iterations |

This lets you see **real cost optimization** in action! The CLI will show you:
- Model names used for each step
- Latency differences between models
- Cost per agent (all $0 with free tier!)
- Speed vs quality tradeoffs

---

## 🎮 Try These Test Questions

```
Question 1: "What is photosynthesis?"
Question 2: "Explain gravity in simple terms"
Question 3: "How do vaccines work?"
```

Then explore the **Developer Mode** features:
- **Option 3**: View intermediate results (see each model's output)
- **Option 4**: View detailed metrics (statistics across iterations)
- **Option 5**: View cost breakdown (by agent and model)

---

## ⚡ Troubleshooting

### Error: "HUGGINGFACE_API_KEY not found"
**Fix**: Make sure you created `.env` file (not `.env.example`) and added your key

### Error: "Rate limit exceeded"  
**Fix**: Free tier has limits. Wait a few minutes or:
- Use smaller model: `google/flan-t5-base`
- Reduce max_iterations in config.yaml
- Upgrade to HuggingFace Pro ($9/month)

### API call very slow
**Normal**: First call can be slow (model loading). Subsequent calls are faster.

### Want faster responses?
**Switch to smaller model** in `config/config.yaml`:
```yaml
generator:
  model_name: "google/flan-t5-base"  # Ultra fast
```

---

## 🔄 Switching Between Providers

You can easily switch between different providers:

### Use Hugging Face (RECOMMENDED - Zero PC load):
```yaml
# config/config.yaml
provider: "huggingface"
model_name: "microsoft/phi-2"
```

### Use Ollama (Local - Requires installation):
```yaml
provider: "ollama"
model_name: "llama3"
```

### Use OpenAI (Paid - High quality):
```yaml
provider: "openai"
model_name: "gpt-4"
```

---

## 💡 Why Hugging Face is Perfect for You

| Feature | Hugging Face | Ollama | OpenAI |
|---------|--------------|--------|--------|
| **PC Load** | ✅ ZERO | ❌ HIGH | ✅ ZERO |
| **Cost** | ✅ FREE* | ✅ FREE | ❌ $$$ |
| **Setup Time** | ✅ 2 min | ❌ 30 min | ✅ 2 min |
| **Installation** | ✅ None | ❌ ~200 MB | ✅ None |
| **Model Choice** | ✅ 1000+ | ⚠️ Limited | ⚠️ 5-10 |

*Free tier with rate limits

---

## 🎯 Next: See REAL Optimization!

Once running, you'll see **actual AI outputs** instead of those 0.00 placeholders:

**Before** (without LLM):
```
Composite Score: 0.00/10
Cost: $0.00
```

**After** (with Hugging Face):
```
Composite Score: 8.2/10
Generated Answer: "Photosynthesis is the process where plants..."
Explanation: "Plants use sunlight to convert CO2 and water..."

Cost Breakdown:
  - Generator (phi-2): $0.00
  - Judge (Mistral-7B): $0.00
  - Optimizer (phi-2): $0.00
  Total: $0.00 (FREE!)
```

---

## 🚀 Ready? Let's Go!

```bash
# 1. Get API key from: https://huggingface.co/settings/tokens
# 2. Add to .env file
# 3. Test setup
python test_huggingface.py

# 4. Run Astra AI!
python main.py --interactive

# 5. Enjoy real AI optimization! 🎉
```

---

## Need Help?

- **HuggingFace Tokens**: https://huggingface.co/settings/tokens
- **Model Browser**: https://huggingface.co/models
- **Free Rate Limits**: https://huggingface.co/pricing
- **Documentation**: See HUGGINGFACE_SETUP.md for detailed guide
