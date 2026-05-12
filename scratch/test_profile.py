import asyncio
from core.agent_loop import BAYMAXAgent
import sqlite3

async def test():
    agent = BAYMAXAgent()
    # Step 1: Tell it the name
    print('User: my name is Samuel')
    resp1 = await agent.run('my name is Samuel')
    print('Agent Response 1:', resp1.get('response'))
    
    # Check DB
    conn = sqlite3.connect('memory/baymax.db')
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM user_profile WHERE key='user_name'")
    row = cursor.fetchone()
    print('DB user_name:', row[0] if row else 'Not found')
    conn.close()
    
    # Step 2: Next response to see if it remembers
    print('User: what is my name?')
    resp2 = await agent.run('what is my name?')
    print('Agent Response 2:', resp2.get('response'))

asyncio.run(test())
