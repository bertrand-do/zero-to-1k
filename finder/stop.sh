#!/bin/zsh
lsof -ti tcp:5191 | xargs kill 2>/dev/null; echo "zero-to-1k stopped"
