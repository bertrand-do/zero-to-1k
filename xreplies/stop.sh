#!/bin/zsh
lsof -ti tcp:5191 | xargs kill 2>/dev/null; echo "xreplies stopped"
