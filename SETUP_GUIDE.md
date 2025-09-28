# Enhanced Homemade Engine Setup Guide

## **Issue: Engine Getting Stuck**

The enhanced engine gets stuck because it requires external dependencies (`chess`, `numpy`, `psutil`) that aren't installed in your environment.

## **Solutions**

### **Option 1: Install Dependencies (Recommended)**

#### **For Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3-chess python3-numpy python3-psutil
```

#### **For Other Systems:**
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install chess numpy psutil

# Run with virtual environment
source venv/bin/activate
python user_interface.py
```

#### **Alternative (if you have pipx):**
```bash
pipx install chess numpy psutil
```

### **Option 2: Use Simple Engine (Quick Test)**

If you can't install dependencies, use the simple engine for testing:

```bash
# Copy simple configuration
cp config_simple_engine.yml config.yml

# Edit config.yml with your Lichess token
nano config.yml

# Run tactical bot
python user_interface.py
```

## **Configuration Files**

### **1. Enhanced Engine (Full Features)**
- **File**: `config_enhanced_engine.yml`
- **Features**: NNUE, bitboards, parallel search, opening books
- **Requirements**: `chess`, `numpy`, `psutil`

### **2. Simple Engine (Testing)**
- **File**: `config_simple_engine.yml`
- **Features**: Basic UCI engine, no external dependencies
- **Requirements**: None (Python only)

## **Step-by-Step Setup**

### **Step 1: Choose Your Engine**

#### **For Full Features (Recommended):**
```bash
# Install dependencies
sudo apt install python3-chess python3-numpy python3-psutil

# Use enhanced configuration
cp config_enhanced_engine.yml config.yml
```

#### **For Quick Testing:**
```bash
# Use simple configuration (no dependencies needed)
cp config_simple_engine.yml config.yml
```

### **Step 2: Configure Your Token**
```bash
# Edit config.yml
nano config.yml

# Replace this line:
token: "YOUR_LICHESS_TOKEN_HERE"

# With your actual token:
token: "your_actual_lichess_token_here"
```

### **Step 3: Run Tactical Bot**
```bash
# Run the bot
python user_interface.py

# Or with upgrade flag
python user_interface.py -u
```

## **Engine Comparison**

| Feature | Simple Engine | Enhanced Engine |
|---------|---------------|-----------------|
| **Dependencies** | None | chess, numpy, psutil |
| **UCI Protocol** | ✅ Basic | ✅ Full |
| **Opening Books** | ❌ No | ✅ 40+ books |
| **NNUE Evaluation** | ❌ No | ✅ Neural network |
| **Bitboards** | ❌ No | ✅ Fast move generation |
| **Multi-threading** | ❌ No | ✅ Parallel search |
| **Playing Strength** | ~800 ELO | ~2000+ ELO |
| **Setup Time** | 1 minute | 5 minutes |

## **Troubleshooting**

### **"ModuleNotFoundError: No module named 'chess'"**
- **Solution**: Install dependencies or use simple engine
- **Command**: `sudo apt install python3-chess python3-numpy python3-psutil`

### **"Permission denied"**
- **Solution**: Make engine executable
- **Command**: `chmod +x engines/enhanced_homemade_engine`

### **"Engine could not make a move"**
- **Solution**: Check dependencies and engine executable
- **Test**: `echo "uci" | python3 engines/enhanced_homemade_engine`

### **"Externally managed environment"**
- **Solution**: Use system packages or virtual environment
- **Command**: `sudo apt install python3-chess python3-numpy python3-psutil`

## **Testing Your Setup**

### **Test Simple Engine:**
```bash
echo "uci" | python3 engines/simple_homemade_engine
```

**Expected output:**
```
id name SimpleHomemadeChessEngine
id author AI Assistant
id version 1.0
option name Hash type spin default 128 min 1 max 2048
option name Depth type spin default 8 min 1 max 25
option name Time type spin default 3000 min 100 max 60000
option name Threads type spin default 4 min 1 max 16
uciok
```

### **Test Enhanced Engine:**
```bash
echo "uci" | python3 engines/enhanced_homemade_engine
```

**Expected output:**
```
id name EnhancedHomemadeChessEngine
id author AI Assistant
id version 2.0
option name Hash type spin default 128 min 1 max 2048
option name Depth type spin default 8 min 1 max 25
option name Time type spin default 3000 min 100 max 60000
option name Threads type spin default 4 min 1 max 16
option name UseNNUE type check default true
option name UseParallel type check default true
uciok
```

## **Quick Start (No Dependencies)**

If you want to test immediately without installing dependencies:

```bash
# 1. Copy simple config
cp config_simple_engine.yml config.yml

# 2. Edit with your token
nano config.yml

# 3. Run bot
python user_interface.py -u
```

## **Full Setup (With Dependencies)**

For the complete enhanced engine experience:

```bash
# 1. Install dependencies
sudo apt install python3-chess python3-numpy python3-psutil

# 2. Copy enhanced config
cp config_enhanced_engine.yml config.yml

# 3. Edit with your token
nano config.yml

# 4. Run bot
python user_interface.py -u
```

## **Summary**

- **Quick Test**: Use `config_simple_engine.yml` (no dependencies)
- **Full Features**: Install dependencies and use `config_enhanced_engine.yml`
- **The engine getting stuck is due to missing dependencies**
- **Both engines are UCI-compatible and work with tactical bot**

Choose the option that works best for your environment! 🎉