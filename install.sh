#!/bin/bash

# Installation script for SearchBoost

# Dynamically set the target path to the current working directory
CURRENT_DIR=$(pwd)
TARGET_PATH="$CURRENT_DIR/main.py"

echo "Installing SearchBoost..."

# Check if main.py exists in the current directory
if [ ! -f main.py ]; then
    echo "Error: main.py not found in the current directory."
    exit 1
fi

# Install Python dependencies
if [ -f requirements.txt ]; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
else
    echo "Error: requirements.txt not found in the current directory."
    exit 1
fi

# Copy the library folder and set the target executable
cp -r searchboost "$CURRENT_DIR/"  # Ensure the library files are in the working directory
cp main.py $TARGET_PATH
chmod +x $TARGET_PATH

# Add to bashrc
BASHRC="$HOME/.bashrc"
ZSHRC="$HOME/.zshrc"
ALIAS_COMMAND="alias searchboost='python3 $TARGET_PATH'"

# Add alias to bashrc
if ! grep -Fxq "$ALIAS_COMMAND" "$BASHRC"; then
    echo "$ALIAS_COMMAND" >> "$BASHRC"
    echo "Added alias to $BASHRC"
fi

# Add alias to zshrc (if using Zsh)
if [ -f "$ZSHRC" ] && ! grep -Fxq "$ALIAS_COMMAND" "$ZSHRC"; then
    echo "$ALIAS_COMMAND" >> "$ZSHRC"
    echo "Added alias to $ZSHRC"
fi

echo "Installation complete. Restart your terminal or run 'source ~/.bashrc' to use SearchBoost."
