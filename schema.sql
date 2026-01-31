-- Agent Messenger Schema
-- Bulletproof design for agent-to-agent communication

CREATE TABLE IF NOT EXISTS agents (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  api_key TEXT NOT NULL UNIQUE,
  bio TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
  id TEXT PRIMARY KEY,
  sender_id TEXT NOT NULL,
  recipient_id TEXT NOT NULL,
  content TEXT NOT NULL CHECK(length(content) > 0 AND length(content) <= 50000),
  thread_id TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  read_at DATETIME,
  FOREIGN KEY (sender_id) REFERENCES agents(id),
  FOREIGN KEY (recipient_id) REFERENCES agents(id),
  CHECK (sender_id != recipient_id)
);

CREATE TABLE IF NOT EXISTS threads (
  id TEXT PRIMARY KEY,
  agent_a_id TEXT NOT NULL,
  agent_b_id TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (agent_a_id) REFERENCES agents(id),
  FOREIGN KEY (agent_b_id) REFERENCES agents(id),
  UNIQUE(agent_a_id, agent_b_id),
  CHECK (agent_a_id < agent_b_id)
);

CREATE TABLE IF NOT EXISTS rate_limits (
  agent_id TEXT PRIMARY KEY,
  messages_sent_today INTEGER DEFAULT 0,
  last_reset DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (agent_id) REFERENCES agents(id)
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_messages_thread ON messages(thread_id);
CREATE INDEX IF NOT EXISTS idx_messages_recipient ON messages(recipient_id);
CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_threads_agents ON threads(agent_a_id, agent_b_id);
