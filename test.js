const BASE_URL = 'http://localhost:3001';

async function test() {
  console.log('🧪 Testing Agent Messenger\n');
  
  try {
    // 1. Register two agents
    console.log('1️⃣  Registering agents...');
    const marcos = await register('Marcos', 'Teaching Hugo Villalba frameworks');
    const shipyard = await register('Shipyard', 'On-chain intelligence');
    console.log(`   ✓ Marcos: ${marcos.api_key}`);
    console.log(`   ✓ Shipyard: ${shipyard.api_key}\n`);
    
    // 2. Get profiles
    console.log('2️⃣  Getting profiles...');
    const marcoProfile = await getProfile('Marcos');
    console.log(`   ✓ Found: ${marcoProfile.name}\n`);
    
    // 3. Send message
    console.log('3️⃣  Sending message...');
    const msg = await sendMessage(
      marcos.api_key,
      shipyard.id,
      'Hey Shipyard, your Iran intel is solid. Try the Angles Algorithm on your flows.'
    );
    console.log(`   ✓ Message sent: ${msg.id}\n`);
    
    // 4. Receive message (different agent reads thread)
    console.log('4️⃣  Reading messages...');
    const thread = await getMessages(msg.thread_id, shipyard.api_key);
    console.log(`   ✓ Thread ${msg.thread_id}:`);
    thread.messages.forEach(m => {
      console.log(`      ${m.sender_id === marcos.id ? 'Marcos' : 'Shipyard'}: ${m.content}`);
    });
    console.log();
    
    // 5. Get inbox
    console.log('5️⃣  Getting inbox...');
    const inbox = await getThreads(shipyard.api_key);
    console.log(`   ✓ ${inbox.threads.length} thread(s)\n`);
    
    console.log('✅ All tests passed!\n');
    
  } catch (err) {
    console.error('❌ Test failed:', err.message);
    process.exit(1);
  }
}

async function register(name, bio) {
  const res = await fetch(`${BASE_URL}/api/agents/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, bio })
  });
  if (!res.ok) throw new Error(`Register failed: ${res.statusText}`);
  return res.json();
}

async function getProfile(name) {
  const res = await fetch(`${BASE_URL}/api/agents/${name}`);
  if (!res.ok) throw new Error(`Get profile failed: ${res.statusText}`);
  return res.json();
}

async function sendMessage(api_key, recipient_id, content) {
  const res = await fetch(`${BASE_URL}/api/messages/send`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': api_key
    },
    body: JSON.stringify({ recipient_id, content })
  });
  if (!res.ok) throw new Error(`Send failed: ${res.statusText}`);
  return res.json();
}

async function getMessages(thread_id, api_key) {
  const res = await fetch(`${BASE_URL}/api/messages/thread/${thread_id}`, {
    headers: { 'x-api-key': api_key }
  });
  if (!res.ok) throw new Error(`Get messages failed: ${res.statusText}`);
  return res.json();
}

async function getThreads(api_key) {
  const res = await fetch(`${BASE_URL}/api/threads`, {
    headers: { 'x-api-key': api_key }
  });
  if (!res.ok) throw new Error(`Get threads failed: ${res.statusText}`);
  return res.json();
}

test().catch(console.error);
