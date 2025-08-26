#!/usr/bin/env bash
set -e
 
# Add NodeSource repo for Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
 
# Install Node.js 18 + npm
apt-get install -y nodejs
 
# Confirm installation
echo "Node version: $(node -v)"
echo "NPM version: $(npm -v)"
 
# Install mcp-remote globally
npm install -g mcp-remote
 
echo "✅ Node.js and mcp-remote installed"