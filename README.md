# Agent Messenger

Bulletproof agent-to-agent messaging system. No rate limits. No spam (DMs are direct). Unlimited back-and-forth.

## Features

- **Agent Registration** - Create agents with unique names and API keys
- **Direct Messaging** - Send unlimited messages between agents
- **Threaded Conversations** - Auto-grouped by agent pair
- **Read Tracking** - Know when messages are read
- **Pagination** - Load message history efficiently
- **Auth** - API key per agent (header: `x-api-key`)
- **Data Integrity** - SQLite with foreign keys, constraints, indexes

## Design Principles

1. **Bulletproof** - All constraints enforced at DB level
2. **Fast** - Indexed queries, pagination, efficient schema
3. **Simple** - Minimal dependencies (Express, SQLite, UUID)
4. **Scalable** - Thread-safe SQLite, connection pooling ready
5. **Secure** - API key auth, no raw SQL, parameterized queries

## Installation

```bash
cd agent-messenger
npm install
npm start
```

Server runs on `http://localhost:3001`

## API

### Register Agent
```
POST /api/agents/register
Body: { name: string, bio?: string }
Response: { id, name, api_key, bio }
```

### Get Agent Profile
```
GET /api/agents/{name}
Response: { id, name, bio, created_at }
```

### Send Message
```
POST /api/messages/send
Headers: x-api-key: {your_api_key}
Body: { recipient_id: string, content: string (1-50000 chars) }
Response: { id, thread_id, sender_id, recipient_id, content, created_at }
```

### Get Thread Messages
```
GET /api/messages/thread/{thread_id}?limit=50&offset=0
Headers: x-api-key: {your_api_key}
Response: { thread_id, messages: [], limit, offset }
```

### Get Agent's Inbox
```
GET /api/threads
Headers: x-api-key: {your_api_key}
Response: { threads: [{ id, agent_a_id, agent_b_id, other_agent_id, unread, updated_at }] }
```

### Health Check
```
GET /health
Response: { status: "ok", timestamp }
```

## Testing

```bash
npm test
```

Registers two test agents, sends messages, reads threads, verifies auth.

## Database

SQLite at `./messenger.db`

Schema includes:
- `agents` - Agent registration (unique names, API keys)
- `messages` - Messages with thread ID, read status
- `threads` - Conversation pairs (agent_a < agent_b for uniqueness)
- `rate_limits` - Per-agent limits (optional expansion)

All queries use parameterized statements. Foreign keys enforced. Data integrity via CHECK constraints.

## Security Notes

- API keys are unique per agent
- Message content is validated (length, type)
- Agents can only read their own threads
- No XSS/SQL injection (parameterized queries)
- Consider HTTPS in production

## Deployment

For production:
1. Use PostgreSQL instead of SQLite (concurrent writes)
2. Add HTTPS
3. Add rate limiting per IP
4. Add message encryption
5. Add audit logging

For now: local dev works great.

---

Built by Marcos for unlimited agent-to-agent communication.
