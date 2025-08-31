// --- Theme toggle ---
const themeBtn = document.getElementById('themeBtn');
function setTheme(mode){
  document.documentElement.setAttribute('data-theme', mode);
  localStorage.setItem('theme', mode);
  themeBtn.textContent = mode === 'dark' ? '☀️' : '🌙';
}
setTheme(localStorage.getItem('theme') || 'dark');
themeBtn.addEventListener('click', ()=>{
  const cur = document.documentElement.getAttribute('data-theme');
  setTheme(cur === 'dark' ? 'light' : 'dark');
});

// --- Chat helpers ---
const chatLog = document.getElementById('chatLog');
const chatInput = document.getElementById('chatInput');
const chatSend = document.getElementById('chatSend');
const clearBtn = document.getElementById('clearBtn');

function addBubble(role, text){
  const div = document.createElement('div');
  div.className = 'bubble ' + (role === 'user' ? 'user' : 'bot');
  chatLog.appendChild(div);
  if(role === 'bot'){
    typeWriter(div, text);
  } else {
    div.textContent = text;
  }
  chatLog.scrollTop = chatLog.scrollHeight;
  return div;
}

// Typing effect for bot responses
function typeWriter(el, text){
  el.textContent = '';
  let i = 0;
  const speed = 12; // chars per tick
  function tick(){
    el.textContent += text.slice(i, i + speed);
    i += speed;
    chatLog.scrollTop = chatLog.scrollHeight;
    if(i < text.length) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

async function sendMessage(){
  const msg = chatInput.value.trim();
  if(!msg) return;
  addBubble('user', msg);
  chatInput.value = '';

  const waiting = document.createElement('div');
  waiting.className = 'bubble bot';
  waiting.textContent = '…';
  chatLog.appendChild(waiting);
  chatLog.scrollTop = chatLog.scrollHeight;

  const body = { message: msg };
  const headers = { 'Content-Type': 'application/json' };

  async function call(endpoint){
    const res = await fetch(endpoint, { method: 'POST', headers, body: JSON.stringify(body) });
    if(!res.ok) throw new Error(await res.text());
    const data = await res.json();
    return data.reply || 'Sorry, I could not generate a response.';
  }

  try{
    let reply;
    try { reply = await call('/chat'); }
    catch { reply = await call('/api/chat'); }
    waiting.remove();
    addBubble('bot', reply);
  }catch(err){
    waiting.remove();
    addBubble('bot', 'Sorry, I hit an error. Please try again.');
    console.error(err);
  }
}

chatSend.addEventListener('click', sendMessage);
chatInput.addEventListener('keydown', (e)=>{ if(e.key==='Enter') sendMessage(); });
clearBtn.addEventListener('click', ()=>{ chatLog.innerHTML=''; addBubble('bot','Hi! I’m your AI assistant. Ask about my skills, projects, or experience.'); });

// Keyboard hover feedback
document.querySelectorAll('.hoverable').forEach(el=>{
  el.addEventListener('keydown', e=>{
    if(e.key === 'Enter' || e.key === ' '){
      e.currentTarget.classList.add('hover');
      setTimeout(()=>e.currentTarget.classList.remove('hover'), 250);
    }
  });
});
