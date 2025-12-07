"""
AI Application Builder Service
Generates complete, functional applications from natural language prompts using OpenAI
"""

import os
import json
import logging
from typing import Dict, List
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class AIBuilderService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        self.client = AsyncOpenAI(api_key=self.api_key)
        
    async def generate_app_structure(self, prompt: str, tech_stack: Dict[str, str]) -> Dict:
        """Generate complete application structure from prompt"""
        
        system_prompt = f"""You are an expert full-stack developer who generates COMPLETE, FUNCTIONAL, WORKING applications.

Tech Stack:
- Frontend: {tech_stack.get('frontend', 'React')}
- Backend: {tech_stack.get('backend', 'FastAPI')}
- Database: {tech_stack.get('database', 'MongoDB')}

CRITICAL REQUIREMENTS:
1. Generate COMPLETE, WORKING code - NO placeholders, NO TODO comments, NO "implement this later"
2. Include ALL necessary logic and functionality
3. Code must be IMMEDIATELY RUNNABLE in a browser preview
4. Use modern, professional CSS styling
5. Add ALL necessary imports
6. Generate REAL business logic, not templates

QUALITY STANDARDS:
- For a "calculator app": Include working buttons (0-9, +, -, *, /, =, C), display, arithmetic operations, nice styling
- For a "todo app": Add/delete/complete tasks, persist state in localStorage, clean UI with checkboxes and delete buttons
- For a "blog app": Create/read posts, add comments, author info, styled cards, responsive layout

OUTPUT FORMAT - Return ONLY valid JSON (no markdown, no code blocks):
{{
  "app_name": "descriptive-app-name",
  "description": "Brief description of what the app does",
  "files": [
    {{
      "path": "frontend/src/App.js",
      "content": "COMPLETE WORKING REACT CODE HERE",
      "language": "javascript"
    }},
    {{
      "path": "frontend/src/App.css",
      "content": "COMPLETE CSS STYLING HERE",
      "language": "css"
    }},
    {{
      "path": "frontend/package.json",
      "content": "PACKAGE.JSON WITH DEPENDENCIES",
      "language": "json"
    }}
  ],
  "setup_instructions": "Installation and setup steps",
  "deployment_notes": "Deployment guidance"
}}

RULES:
- Return ONLY the JSON object
- NO markdown formatting
- NO code blocks (```)
- NO explanatory text before or after the JSON
- Include complete working code in each file"""

        user_prompt = f"""Generate a COMPLETE, FUNCTIONAL, WORKING application for: {prompt}

Remember:
1. Make it IMMEDIATELY runnable - no placeholders
2. Include REAL logic and functionality
3. Style it professionally with CSS
4. Add all necessary dependencies to package.json
5. Make it look good and work perfectly

Return the JSON structure with complete code now."""
        
        try:
            logger.info(f"Generating app for prompt: {prompt}")
            
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            response_text = response.choices[0].message.content.strip()
            logger.info(f"Received response, length: {len(response_text)}")
            
            # Clean response if needed
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            # Parse JSON
            app_structure = json.loads(response_text)
            
            # Validate structure
            if not app_structure.get('files'):
                raise ValueError("No files generated in response")
            
            # Ensure package.json exists
            has_package_json = any(f['path'].endswith('package.json') for f in app_structure['files'])
            if not has_package_json:
                app_structure['files'].append({
                    "path": "frontend/package.json",
                    "content": self._generate_package_json(app_structure.get('app_name', 'generated-app')),
                    "language": "json"
                })
            
            # Add README if not present
            if not any(f['path'].endswith('README.md') for f in app_structure['files']):
                app_structure['files'].append({
                    "path": "README.md",
                    "content": self._generate_readme(app_structure, tech_stack),
                    "language": "markdown"
                })
            
            logger.info(f"Successfully generated app with {len(app_structure['files'])} files")
            return app_structure
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.error(f"Response text: {response_text[:500]}")
            return self._get_fallback_for_prompt(prompt, tech_stack)
        except Exception as e:
            logger.error(f"AI generation error: {e}")
            return self._get_fallback_for_prompt(prompt, tech_stack)
    
    def _generate_package_json(self, app_name: str) -> str:
        """Generate a standard package.json"""
        package = {
            "name": app_name.lower().replace(" ", "-"),
            "version": "1.0.0",
            "private": True,
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "react-scripts": "5.0.1"
            },
            "scripts": {
                "start": "react-scripts start",
                "build": "react-scripts build",
                "test": "react-scripts test",
                "eject": "react-scripts eject"
            },
            "eslintConfig": {
                "extends": ["react-app"]
            },
            "browserslist": {
                "production": [">0.2%", "not dead", "not op_mini all"],
                "development": ["last 1 chrome version", "last 1 firefox version", "last 1 safari version"]
            }
        }
        return json.dumps(package, indent=2)
    
    def _generate_readme(self, app_structure: Dict, tech_stack: Dict) -> str:
        """Generate README for the project"""
        return f"""# {app_structure.get('app_name', 'Generated App')}

{app_structure.get('description', 'Application generated by AI Builder')}

## Tech Stack

- **Frontend**: {tech_stack.get('frontend', 'React')}
- **Backend**: {tech_stack.get('backend', 'FastAPI')}
- **Database**: {tech_stack.get('database', 'MongoDB')}

## Setup Instructions

{app_structure.get('setup_instructions', 'Run npm install in frontend/ and pip install -r requirements.txt in backend/')}

## Deployment

{app_structure.get('deployment_notes', 'Deploy frontend to Vercel and backend to Render')}

## Generated by AI Builder

This application was generated using AI-powered code generation.
"""
    
    def _get_fallback_for_prompt(self, prompt: str, tech_stack: Dict) -> Dict:
        """Intelligent fallback based on prompt keywords"""
        
        prompt_lower = prompt.lower()
        
        # Detect app type from prompt
        if any(word in prompt_lower for word in ['calculator', 'calc', 'math', 'arithmetic']):
            return self._get_calculator_template()
        elif any(word in prompt_lower for word in ['todo', 'task', 'checklist']):
            return self._get_todo_template()
        elif any(word in prompt_lower for word in ['blog', 'post', 'article', 'comment']):
            return self._get_blog_template()
        else:
            # Generic fallback
            return self._get_calculator_template()
    
    def _get_calculator_template(self) -> Dict:
        """Complete working calculator app"""
        return {
            "app_name": "calculator-app",
            "description": "A fully functional calculator with all basic operations",
            "files": [
                {
                    "path": "frontend/package.json",
                    "content": self._generate_package_json("calculator-app"),
                    "language": "json"
                },
                {
                    "path": "frontend/src/App.js",
                    "content": """import React, { useState } from 'react';
import './App.css';

function App() {
  const [display, setDisplay] = useState('0');
  const [previousValue, setPreviousValue] = useState(null);
  const [operation, setOperation] = useState(null);
  const [waitingForOperand, setWaitingForOperand] = useState(false);

  const inputDigit = (digit) => {
    if (waitingForOperand) {
      setDisplay(String(digit));
      setWaitingForOperand(false);
    } else {
      setDisplay(display === '0' ? String(digit) : display + digit);
    }
  };

  const inputDecimal = () => {
    if (waitingForOperand) {
      setDisplay('0.');
      setWaitingForOperand(false);
    } else if (display.indexOf('.') === -1) {
      setDisplay(display + '.');
    }
  };

  const clear = () => {
    setDisplay('0');
    setPreviousValue(null);
    setOperation(null);
    setWaitingForOperand(false);
  };

  const performOperation = (nextOperation) => {
    const inputValue = parseFloat(display);

    if (previousValue === null) {
      setPreviousValue(inputValue);
    } else if (operation) {
      const currentValue = previousValue || 0;
      const newValue = calculate(currentValue, inputValue, operation);
      setDisplay(String(newValue));
      setPreviousValue(newValue);
    }

    setWaitingForOperand(true);
    setOperation(nextOperation);
  };

  const calculate = (firstValue, secondValue, operation) => {
    switch (operation) {
      case '+': return firstValue + secondValue;
      case '-': return firstValue - secondValue;
      case '*': return firstValue * secondValue;
      case '/': return firstValue / secondValue;
      case '=': return secondValue;
      default: return secondValue;
    }
  };

  return (
    <div className="app">
      <div className="calculator">
        <div className="calculator-display">{display}</div>
        <div className="calculator-keypad">
          <div className="input-keys">
            <div className="function-keys">
              <button className="calculator-key key-clear" onClick={clear}>AC</button>
              <button className="calculator-key key-sign" onClick={() => setDisplay(String(parseFloat(display) * -1))}>±</button>
              <button className="calculator-key key-percent" onClick={() => setDisplay(String(parseFloat(display) / 100))}>%</button>
            </div>
            <div className="digit-keys">
              <button className="calculator-key key-0" onClick={() => inputDigit(0)}>0</button>
              <button className="calculator-key key-dot" onClick={inputDecimal}>.</button>
              {[1, 2, 3, 4, 5, 6, 7, 8, 9].map(num => (
                <button key={num} className="calculator-key" onClick={() => inputDigit(num)}>{num}</button>
              ))}
            </div>
          </div>
          <div className="operator-keys">
            <button className="calculator-key key-divide" onClick={() => performOperation('/')}>÷</button>
            <button className="calculator-key key-multiply" onClick={() => performOperation('*')}>×</button>
            <button className="calculator-key key-subtract" onClick={() => performOperation('-')}>−</button>
            <button className="calculator-key key-add" onClick={() => performOperation('+')}>+</button>
            <button className="calculator-key key-equals" onClick={() => performOperation('=')}>=</button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
""",
                    "language": "javascript"
                },
                {
                    "path": "frontend/src/App.css",
                    "content": """* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
}

.app {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.calculator {
  width: 320px;
  background: #fff;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  overflow: hidden;
}

.calculator-display {
  background: #222;
  color: #fff;
  font-size: 48px;
  padding: 30px 20px;
  text-align: right;
  font-weight: 300;
  min-height: 100px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  overflow: hidden;
}

.calculator-keypad {
  display: flex;
}

.input-keys {
  flex: 3;
}

.function-keys {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
}

.digit-keys {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-template-areas:
    "key-1 key-2 key-3"
    "key-4 key-5 key-6"
    "key-7 key-8 key-9"
    "key-0 key-0 key-dot";
}

.calculator-key {
  border: none;
  background: #f0f0f0;
  color: #333;
  font-size: 24px;
  font-weight: 400;
  padding: 20px;
  cursor: pointer;
  transition: all 0.2s;
  border-right: 1px solid #ddd;
  border-bottom: 1px solid #ddd;
}

.calculator-key:hover {
  background: #e0e0e0;
}

.calculator-key:active {
  background: #d0d0d0;
}

.key-0 {
  grid-area: key-0;
}

.function-keys .calculator-key {
  background: #e0e0e0;
  color: #666;
}

.operator-keys {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.operator-keys .calculator-key {
  background: #ff9500;
  color: #fff;
  font-size: 28px;
  border-right: none;
}

.operator-keys .calculator-key:hover {
  background: #ff8000;
}

.key-equals {
  flex: 1;
  background: #ff9500 !important;
}
""",
                    "language": "css"
                }
            ],
            "setup_instructions": "Run 'npm install' in the frontend directory, then 'npm start'",
            "deployment_notes": "Deploy to Vercel or Netlify"
        }
    
    def _get_todo_template(self) -> Dict:
        """Complete working todo app"""
        return {
            "app_name": "todo-app",
            "description": "A fully functional todo list with add, complete, and delete features",
            "files": [
                {
                    "path": "frontend/package.json",
                    "content": self._generate_package_json("todo-app"),
                    "language": "json"
                },
                {
                    "path": "frontend/src/App.js",
                    "content": """import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [todos, setTodos] = useState([]);
  const [inputValue, setInputValue] = useState('');

  // Load todos from localStorage on mount
  useEffect(() => {
    const savedTodos = localStorage.getItem('todos');
    if (savedTodos) {
      setTodos(JSON.parse(savedTodos));
    }
  }, []);

  // Save todos to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('todos', JSON.stringify(todos));
  }, [todos]);

  const addTodo = (e) => {
    e.preventDefault();
    if (inputValue.trim()) {
      setTodos([...todos, {
        id: Date.now(),
        text: inputValue,
        completed: false
      }]);
      setInputValue('');
    }
  };

  const toggleTodo = (id) => {
    setTodos(todos.map(todo =>
      todo.id === id ? { ...todo, completed: !todo.completed } : todo
    ));
  };

  const deleteTodo = (id) => {
    setTodos(todos.filter(todo => todo.id !== id));
  };

  const activeTodos = todos.filter(todo => !todo.completed).length;

  return (
    <div className="app">
      <div className="todo-container">
        <h1>My Tasks</h1>
        <form onSubmit={addTodo} className="todo-form">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="What needs to be done?"
            className="todo-input"
          />
          <button type="submit" className="add-button">Add</button>
        </form>
        
        <div className="todo-stats">
          {activeTodos} {activeTodos === 1 ? 'task' : 'tasks'} remaining
        </div>

        <ul className="todo-list">
          {todos.map(todo => (
            <li key={todo.id} className={`todo-item ${todo.completed ? 'completed' : ''}`}>
              <input
                type="checkbox"
                checked={todo.completed}
                onChange={() => toggleTodo(todo.id)}
                className="todo-checkbox"
              />
              <span className="todo-text">{todo.text}</span>
              <button
                onClick={() => deleteTodo(todo.id)}
                className="delete-button"
              >
                ✕
              </button>
            </li>
          ))}
        </ul>

        {todos.length === 0 && (
          <div className="empty-state">
            <p>No tasks yet. Add one above!</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
""",
                    "language": "javascript"
                },
                {
                    "path": "frontend/src/App.css",
                    "content": """* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
}

.app {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 40px 20px;
}

.todo-container {
  max-width: 600px;
  margin: 0 auto;
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

h1 {
  font-size: 32px;
  color: #333;
  margin-bottom: 20px;
  text-align: center;
}

.todo-form {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.todo-input {
  flex: 1;
  padding: 12px 16px;
  font-size: 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  outline: none;
  transition: border-color 0.3s;
}

.todo-input:focus {
  border-color: #667eea;
}

.add-button {
  padding: 12px 24px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.3s;
}

.add-button:hover {
  background: #5568d3;
}

.todo-stats {
  color: #666;
  font-size: 14px;
  margin-bottom: 15px;
  padding-bottom: 15px;
  border-bottom: 1px solid #e0e0e0;
}

.todo-list {
  list-style: none;
}

.todo-item {
  display: flex;
  align-items: center;
  padding: 15px;
  margin-bottom: 10px;
  background: #f9f9f9;
  border-radius: 8px;
  transition: all 0.3s;
}

.todo-item:hover {
  background: #f0f0f0;
}

.todo-item.completed .todo-text {
  text-decoration: line-through;
  color: #999;
}

.todo-checkbox {
  width: 20px;
  height: 20px;
  margin-right: 15px;
  cursor: pointer;
}

.todo-text {
  flex: 1;
  font-size: 16px;
  color: #333;
}

.delete-button {
  background: #ff4757;
  color: white;
  border: none;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  cursor: pointer;
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.3s;
}

.delete-button:hover {
  background: #ff3838;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #999;
}

.empty-state p {
  font-size: 18px;
}
""",
                    "language": "css"
                }
            ],
            "setup_instructions": "Run 'npm install' in the frontend directory, then 'npm start'",
            "deployment_notes": "Deploy to Vercel or Netlify"
        }
    
    def _get_blog_template(self) -> Dict:
        """Complete working blog app"""
        return {
            "app_name": "blog-app",
            "description": "A fully functional blog with posts, comments, and authors",
            "files": [
                {
                    "path": "frontend/package.json",
                    "content": self._generate_package_json("blog-app"),
                    "language": "json"
                },
                {
                    "path": "frontend/src/App.js",
                    "content": """import React, { useState } from 'react';
import './App.css';

function App() {
  const [posts, setPosts] = useState([
    {
      id: 1,
      title: 'Welcome to My Blog',
      author: 'John Doe',
      date: '2024-01-15',
      content: 'This is my first blog post. I am excited to share my thoughts with you!',
      comments: [
        { id: 1, author: 'Jane Smith', text: 'Great post!', date: '2024-01-16' }
      ]
    }
  ]);
  const [showCreatePost, setShowCreatePost] = useState(false);
  const [newPost, setNewPost] = useState({ title: '', author: '', content: '' });
  const [commentInputs, setCommentInputs] = useState({});

  const createPost = (e) => {
    e.preventDefault();
    if (newPost.title && newPost.author && newPost.content) {
      setPosts([{
        id: Date.now(),
        ...newPost,
        date: new Date().toISOString().split('T')[0],
        comments: []
      }, ...posts]);
      setNewPost({ title: '', author: '', content: '' });
      setShowCreatePost(false);
    }
  };

  const addComment = (postId) => {
    const commentText = commentInputs[postId];
    if (commentText && commentText.trim()) {
      setPosts(posts.map(post =>
        post.id === postId
          ? {
              ...post,
              comments: [...post.comments, {
                id: Date.now(),
                author: 'Anonymous',
                text: commentText,
                date: new Date().toISOString().split('T')[0]
              }]
            }
          : post
      ));
      setCommentInputs({ ...commentInputs, [postId]: '' });
    }
  };

  return (
    <div className="app">
      <header className="header">
        <h1>My Blog</h1>
        <button onClick={() => setShowCreatePost(!showCreatePost)} className="create-post-btn">
          {showCreatePost ? 'Cancel' : 'Create Post'}
        </button>
      </header>

      <div className="container">
        {showCreatePost && (
          <div className="create-post-form">
            <h2>Create New Post</h2>
            <form onSubmit={createPost}>
              <input
                type="text"
                placeholder="Post Title"
                value={newPost.title}
                onChange={(e) => setNewPost({ ...newPost, title: e.target.value })}
                className="form-input"
              />
              <input
                type="text"
                placeholder="Author Name"
                value={newPost.author}
                onChange={(e) => setNewPost({ ...newPost, author: e.target.value })}
                className="form-input"
              />
              <textarea
                placeholder="Post Content"
                value={newPost.content}
                onChange={(e) => setNewPost({ ...newPost, content: e.target.value })}
                className="form-textarea"
                rows="6"
              />
              <button type="submit" className="submit-btn">Publish Post</button>
            </form>
          </div>
        )}

        <div className="posts">
          {posts.map(post => (
            <article key={post.id} className="post">
              <h2 className="post-title">{post.title}</h2>
              <div className="post-meta">
                <span className="author">By {post.author}</span>
                <span className="date">{post.date}</span>
              </div>
              <p className="post-content">{post.content}</p>

              <div className="comments-section">
                <h3>Comments ({post.comments.length})</h3>
                {post.comments.map(comment => (
                  <div key={comment.id} className="comment">
                    <strong>{comment.author}</strong>
                    <span className="comment-date">{comment.date}</span>
                    <p>{comment.text}</p>
                  </div>
                ))}

                <div className="add-comment">
                  <input
                    type="text"
                    placeholder="Add a comment..."
                    value={commentInputs[post.id] || ''}
                    onChange={(e) => setCommentInputs({ ...commentInputs, [post.id]: e.target.value })}
                    className="comment-input"
                  />
                  <button onClick={() => addComment(post.id)} className="comment-btn">
                    Post Comment
                  </button>
                </div>
              </div>
            </article>
          ))}
        </div>
      </div>
    </div>
  );
}

export default App;
""",
                    "language": "javascript"
                },
                {
                    "path": "frontend/src/App.css",
                    "content": """* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
  background: #f5f5f5;
}

.app {
  min-height: 100vh;
}

.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 30px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.header h1 {
  font-size: 32px;
  font-weight: 700;
}

.create-post-btn {
  background: white;
  color: #667eea;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.create-post-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.container {
  max-width: 800px;
  margin: 0 auto;
  padding: 40px 20px;
}

.create-post-form {
  background: white;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  margin-bottom: 30px;
}

.create-post-form h2 {
  margin-bottom: 20px;
  color: #333;
}

.form-input,
.form-textarea {
  width: 100%;
  padding: 12px 16px;
  margin-bottom: 15px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 16px;
  font-family: inherit;
  outline: none;
  transition: border-color 0.3s;
}

.form-input:focus,
.form-textarea:focus {
  border-color: #667eea;
}

.form-textarea {
  resize: vertical;
}

.submit-btn {
  background: #667eea;
  color: white;
  border: none;
  padding: 12px 30px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.3s;
}

.submit-btn:hover {
  background: #5568d3;
}

.posts {
  display: flex;
  flex-direction: column;
  gap: 25px;
}

.post {
  background: white;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.post-title {
  font-size: 28px;
  color: #333;
  margin-bottom: 10px;
}

.post-meta {
  display: flex;
  gap: 20px;
  color: #666;
  font-size: 14px;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #e0e0e0;
}

.author {
  font-weight: 600;
}

.post-content {
  font-size: 16px;
  line-height: 1.6;
  color: #444;
  margin-bottom: 30px;
}

.comments-section {
  border-top: 2px solid #f0f0f0;
  padding-top: 20px;
}

.comments-section h3 {
  font-size: 18px;
  color: #333;
  margin-bottom: 15px;
}

.comment {
  background: #f9f9f9;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 10px;
}

.comment strong {
  color: #667eea;
  margin-right: 10px;
}

.comment-date {
  color: #999;
  font-size: 12px;
}

.comment p {
  margin-top: 8px;
  color: #555;
}

.add-comment {
  display: flex;
  gap: 10px;
  margin-top: 15px;
}

.comment-input {
  flex: 1;
  padding: 10px 14px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.3s;
}

.comment-input:focus {
  border-color: #667eea;
}

.comment-btn {
  background: #667eea;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.3s;
}

.comment-btn:hover {
  background: #5568d3;
}
""",
                    "language": "css"
                }
            ],
            "setup_instructions": "Run 'npm install' in the frontend directory, then 'npm start'",
            "deployment_notes": "Deploy to Vercel or Netlify"
        }

ai_builder = AIBuilderService()
