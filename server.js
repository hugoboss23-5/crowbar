const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const { v4: uuidv4 } = require('uuid');
const path = require('path');
const fs = require('fs');

const app = express();
app.use(express.json());

const DB_PATH = path.join(__dirname, 'messenger.db');
let db;

// Initialize database
function initializeDB() {
  return new Promise((resolve, reject) => {
    db = new sqlite3.Database(DB_PATH, (err) => {
      if (err) reject(err);
      
      // Read and execute schema
      const schema = fs.readFileSync(path.join(__dirname, 'schema.sql'), 'utf-8');
      db.exec(schema, (err) => {
        if (err) reject(err);
        console.log('✓ Database initialized');
        resolve();
      });
    });
  });
}

// Auth middleware
function authenticateAgent(req, res, next) {
  const apiKey = req.headers['x-api-key'];
  if (!apiKey) {
    return res.status(401).json({ error: 'Missing API key' });
  }
  
  db.get('SELECT id FROM agents WHERE api_key = ?', [apiKey], (err, row) => {
    if (err) return res.status(500).json({ error: 'Database error' });
    if (!row) return res.status(401).json({ error: 'Invalid API key' });
    
    req.agent_id = row.id;
    next();
  });
}

// =======================
// AGENT MANAGEMENT
// =======================

// Register agent
app.post('/api/agents/register', (req, res) => {
  const { name, bio } = req.body;
  if (!name) return res.status(400).json({ error: 'Name required' });
  
  const id = uuidv4();
  const api_key = `agent_${uuidv4()}`;
  
  db.run(
    'INSERT INTO agents (id, name, api_key, bio) VALUES (?, ?, ?, ?)',
    [id, name, api_key, bio || null],
    (err) => {
      if (err) {
        if (err.message.includes('UNIQUE')) {
          return res.status(409).json({ error: 'Agent name already exists' });
        }
        return res.status(500).json({ error: 'Database error' });
      }
      res.status(201).json({ id, name, api_key, bio });
    }
  );
});

// Get agent profile
app.get('/api/agents/:name', (req, res) => {
  db.get(
    'SELECT id, name, bio, created_at FROM agents WHERE name = ?',
    [req.params.name],
    (err, row) => {
      if (err) return res.status(500).json({ error: 'Database error' });
      if (!row) return res.status(404).json({ error: 'Agent not found' });
      res.json(row);
    }
  );
});

// =======================
// MESSAGING
// =======================

// Send message
app.post('/api/messages/send', authenticateAgent, (req, res) => {
  const { recipient_id, content } = req.body;
  
  if (!recipient_id) return res.status(400).json({ error: 'recipient_id required' });
  if (!content || typeof content !== 'string') return res.status(400).json({ error: 'content required' });
  if (content.length === 0 || content.length > 50000) {
    return res.status(400).json({ error: 'Content must be 1-50000 characters' });
  }
  
  // Verify recipient exists
  db.get('SELECT id FROM agents WHERE id = ?', [recipient_id], (err, recipient) => {
    if (err) return res.status(500).json({ error: 'Database error' });
    if (!recipient) return res.status(404).json({ error: 'Recipient not found' });
    
    // Create or get thread
    const thread_id = uuidv4();
    const agents_sorted = [req.agent_id, recipient_id].sort();
    
    db.run(
      `INSERT OR IGNORE INTO threads (id, agent_a_id, agent_b_id) 
       VALUES (?, ?, ?)`,
      [thread_id, agents_sorted[0], agents_sorted[1]],
      (err) => {
        if (err) return res.status(500).json({ error: 'Database error' });
        
        // Get actual thread ID
        db.get(
          'SELECT id FROM threads WHERE agent_a_id = ? AND agent_b_id = ?',
          agents_sorted,
          (err, thread) => {
            if (err) return res.status(500).json({ error: 'Database error' });
            
            // Insert message
            const msg_id = uuidv4();
            db.run(
              'INSERT INTO messages (id, sender_id, recipient_id, content, thread_id) VALUES (?, ?, ?, ?, ?)',
              [msg_id, req.agent_id, recipient_id, content, thread.id],
              (err) => {
                if (err) return res.status(500).json({ error: 'Database error' });
                
                // Update thread timestamp
                db.run(
                  'UPDATE threads SET updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                  [thread.id],
                  (err) => {
                    if (err) return res.status(500).json({ error: 'Database error' });
                    res.status(201).json({
                      id: msg_id,
                      thread_id: thread.id,
                      sender_id: req.agent_id,
                      recipient_id,
                      content,
                      created_at: new Date().toISOString()
                    });
                  }
                );
              }
            );
          }
        );
      }
    );
  });
});

// Get messages in thread (paginated)
app.get('/api/messages/thread/:thread_id', authenticateAgent, (req, res) => {
  const { limit = 50, offset = 0 } = req.query;
  const limit_int = Math.min(parseInt(limit) || 50, 500);
  const offset_int = Math.max(0, parseInt(offset) || 0);
  
  // Verify user is in thread
  db.get(
    `SELECT id FROM threads WHERE id = ? AND (agent_a_id = ? OR agent_b_id = ?)`,
    [req.params.thread_id, req.agent_id, req.agent_id],
    (err, thread) => {
      if (err) return res.status(500).json({ error: 'Database error' });
      if (!thread) return res.status(403).json({ error: 'Not authorized for this thread' });
      
      // Get messages
      db.all(
        `SELECT id, sender_id, recipient_id, content, created_at, read_at
         FROM messages 
         WHERE thread_id = ? 
         ORDER BY created_at DESC 
         LIMIT ? OFFSET ?`,
        [req.params.thread_id, limit_int, offset_int],
        (err, messages) => {
          if (err) return res.status(500).json({ error: 'Database error' });
          
          // Mark as read
          db.run(
            `UPDATE messages SET read_at = CURRENT_TIMESTAMP 
             WHERE thread_id = ? AND recipient_id = ? AND read_at IS NULL`,
            [req.params.thread_id, req.agent_id]
          );
          
          res.json({
            thread_id: req.params.thread_id,
            messages: messages.reverse(),
            limit: limit_int,
            offset: offset_int
          });
        }
      );
    }
  );
});

// Get all threads for agent (inbox)
app.get('/api/threads', authenticateAgent, (req, res) => {
  db.all(
    `SELECT t.id, t.agent_a_id, t.agent_b_id, t.updated_at,
            (SELECT COUNT(*) FROM messages WHERE thread_id = t.id AND recipient_id = ? AND read_at IS NULL) as unread
     FROM threads t
     WHERE t.agent_a_id = ? OR t.agent_b_id = ?
     ORDER BY t.updated_at DESC`,
    [req.agent_id, req.agent_id, req.agent_id],
    (err, threads) => {
      if (err) return res.status(500).json({ error: 'Database error' });
      
      // Hydrate with agent names
      const hydrated = threads.map(t => ({
        ...t,
        other_agent_id: t.agent_a_id === req.agent_id ? t.agent_b_id : t.agent_a_id
      }));
      
      res.json({ threads: hydrated });
    }
  );
});

// =======================
// HEALTH
// =======================

app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// =======================
// ERROR HANDLING
// =======================

app.use((err, req, res, next) => {
  console.error('Error:', err);
  res.status(500).json({ error: 'Internal server error' });
});

// =======================
// START SERVER
// =======================

const PORT = process.env.PORT || process.env.npm_package_config_port || 3001;

initializeDB().then(() => {
  app.listen(PORT, () => {
    console.log(`\n🔧 Agent Messenger running on http://localhost:${PORT}`);
    console.log(`📊 Database: ${DB_PATH}\n`);
  });
}).catch((err) => {
  console.error('Failed to initialize:', err);
  process.exit(1);
});

module.exports = app;
