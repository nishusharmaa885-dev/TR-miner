import os
import sys
import json
import time
import asyncio
import urllib.parse
from datetime import datetime

try:
    from aiohttp import web, ClientSession
    from telethon import TelegramClient, functions
    from telethon.errors import SessionPasswordNeededError
except ImportError as e:
    print(f"Required dependency missing: {e}. Please run: pip install aiohttp telethon")
    sys.exit(1)

# --- Configuration ---
API_ID = 28752231
API_HASH = 'ec1c1f2c30e2f1855c3edee7e348480b'

# Global State
active_clients = []
ws_clients = set()
total_ads_run = 0

# Store temporary auth hashes
auth_states = {}  # session_name -> {'phone': str, 'hash': str, 'client': TelegramClient}

async def broadcast_state():
    state = {
        'type': 'state_update',
        'has_clients': len(active_clients) > 0,
        'global_balance': int(sum(c.get('server_balance', 0) for c in active_clients)),
        'total_ads': total_ads_run,
        'clients': [
            {
                'name': c['name'],
                'balance': c.get('server_balance', 0),
                'is_active': c['is_active']
            } for c in active_clients
        ]
    }
    await broadcast(state)

async def broadcast_log(msg):
    await broadcast({'type': 'log', 'message': msg})

async def broadcast(data):
    if not ws_clients:
        return
    msg = json.dumps(data)
    for ws in list(ws_clients):
        try:
            await ws.send_str(msg)
        except Exception:
            ws_clients.discard(ws)

async def ad_watcher_loop(acc_info):
    global total_ads_run
    init_data = acc_info['init_data']
    name = acc_info['name']
    url = "https://trewards.duckdns.org/api/watch-ad"
    ads = ["ad_b1", "ad_b2"]
    headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}

    await broadcast_log(f"[{name}] 🚀 Mining started | 5s interval")

    async with ClientSession() as session:
        while True:
            for ad in ads:
                if not acc_info['is_active']:
                    await asyncio.sleep(5)
                    break

                try:
                    payload = {"init_data": init_data, "ad_id": ad}
                    t_start = time.time()
                    async with session.post(url, json=payload, headers=headers) as resp:
                        result = await resp.json()
                    elapsed = time.time() - t_start
                    sec_str = f"{elapsed:.0f}s"

                    if result.get("success"):
                        new_bal = result.get('new_balance', 'N/A')
                        earned = result.get('coins_earned', 0)
                        
                        log_id = f"log_{name}_{int(time.time()*1000)}"
                        log_text = f"[{name}] ✔ {ad} | Mined: +{earned} | Bal: {new_bal} | sec:- 5s"
                        
                        if new_bal != "N/A":
                            try:
                                acc_info['server_balance'] = float(new_bal)
                            except:
                                pass
                        
                        total_ads_run += 1
                        await broadcast({'type': 'log', 'message': log_text, 'id': log_id})
                        await broadcast_state()
                    else:
                        msg = result.get('message', 'Unknown error')
                        log_id = f"log_{name}_{int(time.time()*1000)}"
                        await broadcast({'type': 'log', 'message': f"[{name}] ✖ {ad} FAILED | {msg} | sec:- 5s", 'id': log_id})

                except Exception as e:
                    log_id = None
                    await broadcast_log(f"[{name}] ⚠ Error: {e}")

                # Live countdown 5 → 0
                for remaining in range(4, -1, -1):
                    await asyncio.sleep(1)
                    await broadcast({'type': 'countdown', 'name': name, 'sec': remaining, 'log_id': log_id})

async def handle_send_code(data):
    phone = data.get('phone')
    session_name = data.get('session', 'treward_main')
    
    try:
        client = TelegramClient(session_name, API_ID, API_HASH)
        await client.connect()
        
        if not await client.is_user_authorized():
            res = await client.send_code_request(phone)
            auth_states[session_name] = {'phone': phone, 'hash': res.phone_code_hash, 'client': client}
            
            # Determine where the code was sent
            try:
                code_type = type(res.type).__name__
                if 'App' in code_type:
                    detail = "Telegram App"
                elif 'Sms' in code_type:
                    detail = "SMS"
                else:
                    detail = "other method"
            except:
                detail = "unknown method"
                
            await broadcast({'type': 'code_requested', 'session': session_name, 'detail': detail})
        else:
            # Already logged in
            auth_states[session_name] = {'phone': phone, 'hash': None, 'client': client}
            await finalize_account(session_name)
    except Exception as e:
        await broadcast({'type': 'error', 'session': session_name, 'message': str(e)})

async def handle_verify_code(data):
    code = data.get('code')
    session_name = data.get('session', 'treward_main')
    state = auth_states.get(session_name)
    
    if not state:
        await broadcast({'type': 'error', 'session': session_name, 'message': 'Session expired'})
        return
        
    try:
        client = state['client']
        await client.sign_in(state['phone'], code, phone_code_hash=state['hash'])
        await finalize_account(session_name)
    except SessionPasswordNeededError:
        await broadcast({'type': 'error', 'session': session_name, 'message': '2FA Password Required (Not Supported Yet)'})
    except Exception as e:
        await broadcast({'type': 'error', 'session': session_name, 'message': str(e)})

async def finalize_account(session_name):
    try:
        state = auth_states.get(session_name)
        client = state['client']
        
        me = await client.get_me()
        username = me.first_name or me.username or session_name
        
        bot = await client.get_entity("treward_ton_bot")
        web_view = await client(functions.messages.RequestWebViewRequest(
            peer=bot, bot=bot, platform='android', from_bot_menu=True,
            url='https://trewards-frontend.onrender.com'
        ))
        init_data = urllib.parse.unquote(web_view.url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0])
        
        acc_info = {
            'client': client,
            'init_data': init_data,
            'name': username,
            'is_active': True,
            'server_balance': 0
        }
        
        active_clients.append(acc_info)
        await broadcast({'type': 'login_success', 'session': session_name})
        await broadcast_log(f"[*] ✅ Account added: {username}")
        await broadcast_state()
        
        # Start background mining task
        asyncio.create_task(ad_watcher_loop(acc_info))
        
        # Clean up state
        if session_name in auth_states:
            del auth_states[session_name]
            
    except Exception as e:
        await broadcast({'type': 'error', 'session': session_name, 'message': f"Fetch Error: {str(e)}"})

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    ws_clients.add(ws)
    
    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                data = json.loads(msg.data)
                action = data.get('action')
                
                if action == 'get_state':
                    await broadcast_state()
                elif action == 'send_code':
                    asyncio.create_task(handle_send_code(data))
                elif action == 'verify_code':
                    asyncio.create_task(handle_verify_code(data))
                elif action == 'toggle_account':
                    idx = data.get('index')
                    if 0 <= idx < len(active_clients):
                        acc = active_clients[idx]
                        acc['is_active'] = not acc['is_active']
                        await broadcast_log(f"[{acc['name']}] {'▶ Resumed' if acc['is_active'] else '⏸ Paused'} mining.")
                        await broadcast_state()
                        
    finally:
        ws_clients.discard(ws)
    return ws

async def index_handler(request):
    return web.FileResponse(os.path.join(os.path.dirname(__file__), 'index.html'))

async def style_handler(request):
    return web.FileResponse(os.path.join(os.path.dirname(__file__), 'style.css'))

async def js_handler(request):
    return web.FileResponse(os.path.join(os.path.dirname(__file__), 'app.js'))

app = web.Application()
app.router.add_get('/', index_handler)
app.router.add_get('/style.css', style_handler)
app.router.add_get('/app.js', js_handler)
app.router.add_get('/ws', websocket_handler)
app.router.add_static('/static', os.path.dirname(__file__))

if __name__ == '__main__':
    print("Starting Web Server at http://127.0.0.1:8000")
    print("Open this URL in your Desktop or Mobile browser!")
    web.run_app(app, host='127.0.0.1', port=8000)
