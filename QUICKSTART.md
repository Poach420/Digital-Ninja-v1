# Quick Start Guide 🚀

Get Digital Ninja running in less than 5 minutes!

## Prerequisites

- **Node.js**: Version 18 or higher ([Download](https://nodejs.org/))
- **npm**: Usually comes with Node.js
- **Code Editor**: VS Code recommended

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Poach420/Digital-Ninja-v1.git
cd Digital-Ninja-v1
```

### 2. Install Dependencies

```bash
npm install
```

This will install:
- Next.js 16
- React 19
- TypeScript
- Tailwind CSS 4
- All other dependencies

### 3. Start Development Server

```bash
npm run dev
```

You should see:
```
▲ Next.js 16.1.1
- Local:        http://localhost:3000
✓ Ready in 413ms
```

### 4. Open Your Browser

Navigate to: **http://localhost:3000**

🎉 **You're ready to build!**

---

## First Steps

### Explore the Interface

1. **Project Explorer** (Left): Browse the file tree
   - Click folders to expand/collapse
   - Click files to "open" them

2. **Code Editor** (Center): Write your code
   - Type directly into the editor
   - See line and character counts
   - Use Format and AI Optimize buttons

3. **Preview Panel** (Top Right): See your app
   - Toggle between Desktop, Tablet, Mobile views
   - Real-time preview (coming soon)

4. **AI Assistant** (Bottom Right): Get help
   - Click quick action buttons
   - Type questions in the input
   - Get AI-generated code

### Try the AI Assistant

Click one of the quick action buttons:
- **"Create a login form"** → Get a complete login component
- **"Build a dashboard"** → Get a dashboard layout
- **"Add dark mode"** → Get dark mode implementation
- **"Create API routes"** → Get API handlers

Or type your own request:
```
"Create a user profile page"
"Add a navigation menu"
"Build a contact form"
```

### Save Your Work

Click the **Save** button in the toolbar (functionality coming soon)

---

## Common Commands

```bash
# Development
npm run dev          # Start dev server

# Production
npm run build        # Build for production
npm start            # Run production build

# Code Quality
npm run lint         # Run ESLint (when configured)
```

---

## Project Structure

```
Digital-Ninja-v1/
├── src/
│   ├── app/              # Next.js pages
│   │   ├── page.tsx      # Main app builder
│   │   └── layout.tsx    # Root layout
│   ├── components/       # React components
│   │   ├── ToolBar.tsx
│   │   ├── ProjectExplorer.tsx
│   │   ├── CodeEditor.tsx
│   │   ├── PreviewPanel.tsx
│   │   └── AIAssistant.tsx
│   ├── lib/              # Utilities
│   │   ├── aiGenerator.ts
│   │   ├── codeUtils.ts
│   │   └── templates.ts
│   └── types/            # TypeScript types
├── public/               # Static files
└── [config files]
```

---

## Tips & Tricks

### 💡 Use Quick Actions
The AI Assistant has preset buttons for common tasks. Use these for the fastest code generation!

### 💡 Explore the File Tree
Click around the Project Explorer to see the demo file structure. This shows what a real project looks like.

### 💡 Check the Preview Panel
The Preview Panel will show your app in real-time (feature coming soon). Toggle between device sizes to test responsiveness.

### 💡 Read the Docs
Check out:
- `README.md` - Full feature guide
- `CONTRIBUTING.md` - How to contribute
- `ARCHITECTURE.md` - Technical details
- `API.md` - API documentation

---

## Troubleshooting

### Port Already in Use

If port 3000 is busy:
```bash
npm run dev -- -p 3001
```

### Node Version Too Old

Check your version:
```bash
node --version
```

Should be 18.x or higher. Update at [nodejs.org](https://nodejs.org/)

### Build Errors

Try cleaning and reinstalling:
```bash
rm -rf node_modules package-lock.json .next
npm install
npm run dev
```

### Browser Won't Load

- Check the terminal for errors
- Try http://localhost:3000 explicitly
- Clear browser cache
- Try a different browser

---

## What's Next?

### Customize the App
1. Edit `src/app/page.tsx` to change the main layout
2. Modify components in `src/components/`
3. Update styles in `src/app/globals.css`

### Add Real AI
Currently using mock AI. To add real AI:
1. Get an API key from OpenAI, Anthropic, or Google
2. Update `src/lib/aiGenerator.ts`
3. Add API calls to the AI service

### Deploy Your Build
```bash
npm run build
```

Deploy to:
- **Vercel**: `npx vercel`
- **Netlify**: Connect your repo
- **AWS/GCP**: Use their deployment tools

---

## Need Help?

- 📖 Read the [README.md](./README.md)
- 🐛 Report bugs on [GitHub Issues](https://github.com/Poach420/Digital-Ninja-v1/issues)
- 💬 Join discussions (coming soon)
- 📧 Contact support (coming soon)

---

## Next Steps

✅ **Explore**: Click around and explore all features
✅ **Experiment**: Try different AI prompts
✅ **Build**: Start creating your own app
✅ **Share**: Show others what you've built
✅ **Contribute**: Help make it even better!

---

**Ready to build amazing apps with AI?** 🥷

Let's make this the best app builder on the market together!
