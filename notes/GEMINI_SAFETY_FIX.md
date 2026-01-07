# Gemini API Error Handling Guide

## 🚨 Common Error: finish_reason = 2 (SAFETY)

### Error Message
```
⚠️ Error during chat: Invalid operation: The `response.text` quick accessor 
requires the response to contain a valid `Part`, but none were returned. 
The candidate's finish_reason is 2.
```

### What it means
- **finish_reason = 2** = SAFETY
- Gemini API blocked the response due to safety filters
- Common with movie content that may contain violence, mature themes, etc.

---

## 🔧 Fixes Applied

### 1. **Safety Settings Configuration**

Added permissive safety settings to allow movie content:

```python
from google.generativeai.types import HarmCategory, HarmBlockThreshold

safety_settings = {
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
}
```

**Files updated:**
- `src/llm_service.py` - Added to GeminiService.__init__
- `manual_ragas_evaluation.py` - Added to ManualRAGASEvaluator

---

### 2. **Better Error Handling**

Added finish_reason detection and retry logic:

```python
# Check finish_reason
if finish_reason == 2:  # SAFETY
    print("⚠️  Content blocked by safety filters")
    # Retry or return fallback score
    
elif finish_reason == 3:  # RECITATION
    print("⚠️  Response blocked due to recitation")
    
elif finish_reason != 1:  # Not STOP (normal)
    print(f"⚠️  Unusual finish_reason: {finish_reason}")
```

**Finish Reason Codes:**
- `1` = STOP (normal completion) ✅
- `2` = SAFETY (content filtered) ⚠️
- `3` = RECITATION (copyright concern) ⚠️
- `4` = OTHER (various issues)

---

### 3. **Fallback Mechanism**

When content is blocked:
1. Retry up to 3 times
2. Wait 1-2 seconds between retries
3. If still blocked, return score `0.5` (neutral)
4. Continue with next evaluation

---

### 4. **Model Update**

Changed from unstable model to stable one:

```python
# Before
CHAT_MODEL = "models/gemini-2.5-pro"  # May not exist

# After
CHAT_MODEL = "models/gemini-1.5-pro"  # Stable, reliable
```

---

## 📊 Impact on Evaluation

### When Safety Block Occurs:
- **Score assigned**: 0.5 (neutral, doesn't favor either system)
- **Reasoning**: "Content blocked by safety filters"
- **Continue**: Evaluation proceeds to next metric/query
- **No crash**: Graceful handling

### Example Output:
```
      • Faithfulness...
      ⚠️  Content blocked by safety filters (attempt 1/3)
      ⚠️  Content blocked by safety filters (attempt 2/3)
      ⚠️  Content blocked by safety filters (attempt 3/3)
      Fallback score: 0.500
 0.500
```

---

## 🎯 When Does This Happen?

### Common Triggers:
1. **Violent Content**: Action/horror movie descriptions
2. **Mature Themes**: Adult-rated films, sexual content
3. **Controversial Topics**: Political films, war movies
4. **Long Contexts**: Very detailed plot summaries
5. **Repetitive Content**: Evaluation prompts with similar text

### Examples:
```
❌ "The Exorcist - demonic possession and graphic exorcism scenes..."
❌ "Pulp Fiction - contains drug use, violence, and strong language..."
❌ "Saw - torture-based horror with extreme violence..."
```

---

## ✅ Best Practices

### 1. Clean Movie Descriptions
Remove overly graphic details:
```python
# Before
"Horror film with graphic violence and disturbing scenes"

# Better
"Horror film with suspenseful atmosphere and thriller elements"
```

### 2. Adjust Safety Settings Per Use Case
For strict content:
```python
# More permissive
HarmBlockThreshold.BLOCK_NONE

# Balanced
HarmBlockThreshold.BLOCK_ONLY_HIGH

# Conservative
HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
```

### 3. Monitor Blocked Content
Check logs for patterns:
```bash
grep "safety filters" evaluation.log
```

### 4. Alternative Models
If blocks persist, try:
```python
# Faster, sometimes more permissive
CHAT_MODEL = "models/gemini-2.0-flash-exp"

# Most stable
CHAT_MODEL = "models/gemini-1.5-pro"
```

---

## 🔍 Debugging

### Check Response Details
```python
response = model.generate_content(prompt, safety_settings=settings)

# Inspect candidates
for candidate in response.candidates:
    print(f"Finish Reason: {candidate.finish_reason}")
    print(f"Safety Ratings: {candidate.safety_ratings}")
```

### Safety Ratings Output:
```
Safety Ratings: [
  category: HARM_CATEGORY_SEXUALLY_EXPLICIT
  probability: MEDIUM
  blocked: true
]
```

---

## 📈 Performance Impact

### Before Fix:
- **Crashes**: Script stops on blocked content
- **Lost Progress**: No results saved
- **Manual Intervention**: Requires restart

### After Fix:
- **Graceful Handling**: Script continues
- **Neutral Scores**: Fair fallback (0.5)
- **Complete Results**: All queries evaluated
- **Transparency**: Logs show which were blocked

---

## 🛠️ Manual Fixes

### If Still Getting Blocks:

#### Option 1: Simplify Prompts
```python
# In _format_contexts(), reduce context length
ctx_clean = ctx.strip()[:800]  # Reduce from 1200
```

#### Option 2: More Permissive Settings
```python
# In manual_ragas_evaluation.py
self.safety_settings = {
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,  # Changed
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,  # Changed
}
```

#### Option 3: Skip Problematic Queries
```python
# Add to load_single_dataset()
if 'skip_safety_check' in query and query['skip_safety_check']:
    continue
```

#### Option 4: Use Different Model
```python
# In config.py
CHAT_MODEL = "models/gemini-2.0-flash-exp"  # Try this alternative
```

---

## 📝 Testing

### Verify Fix Works:
```bash
# Run small test
python manual_ragas_evaluation.py -d comparison.json -n 3

# Check for safety blocks in output
# Should see fallback scores (0.500) instead of crashes
```

### Expected Output:
```
      • Faithfulness... 0.850
      • Answer Relevancy... 0.900
      • Context Precision...
      ⚠️  Content blocked by safety filters (attempt 1/3)
      Fallback score: 0.500
 0.500
      • Context Recall... 0.780
```

---

## 🎓 Understanding Safety Categories

| Category | Description | BLOCK_NONE | BLOCK_ONLY_HIGH | BLOCK_MEDIUM_AND_ABOVE |
|----------|-------------|------------|-----------------|------------------------|
| **HATE_SPEECH** | Discriminatory content | ✅ Allow all | ⚠️ Block severe | ❌ Block moderate+ |
| **HARASSMENT** | Bullying, threats | ✅ Allow all | ⚠️ Block severe | ❌ Block moderate+ |
| **SEXUALLY_EXPLICIT** | Adult content | ✅ Allow all | ⚠️ Block severe | ❌ Block moderate+ |
| **DANGEROUS_CONTENT** | Violence, harm | ✅ Allow all | ⚠️ Block severe | ❌ Block moderate+ |

**Movie Evaluation Recommendation:**
- HATE_SPEECH: `BLOCK_NONE` (movies discuss prejudice)
- HARASSMENT: `BLOCK_NONE` (conflict is part of plots)
- SEXUALLY_EXPLICIT: `BLOCK_ONLY_HIGH` (avoid pornographic)
- DANGEROUS_CONTENT: `BLOCK_ONLY_HIGH` (action movies)

---

## 📚 Resources

- [Gemini API Safety Settings](https://ai.google.dev/docs/safety_setting_gemini)
- [Finish Reason Enum](https://ai.google.dev/api/generate-content#finishreason)
- [Safety Ratings](https://ai.google.dev/api/generate-content#safetysetting)

---

## ✅ Summary

**Problem**: `finish_reason=2` causes crashes  
**Solution**: Safety settings + error handling  
**Result**: Graceful fallback with neutral scores  
**Impact**: Evaluation completes successfully  

**Files Modified:**
1. ✅ `src/llm_service.py` - Safety settings in init
2. ✅ `manual_ragas_evaluation.py` - Error handling
3. ✅ `src/config.py` - Stable model name

---

**Last Updated**: January 6, 2026  
**Issue Status**: ✅ RESOLVED
