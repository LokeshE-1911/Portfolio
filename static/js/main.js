// theme toggle
const themeBtn = document.getElementById('themeBtn');
function setTheme(mode){
  document.documentElement.setAttribute('data-theme', mode);
  localStorage.setItem('theme', mode);
  themeBtn.textContent = mode === 'dark' ? '🌙' : '☀️';
}
setTheme(localStorage.getItem('theme') || 'dark');
themeBtn.addEventListener('click', ()=>{
  const cur = document.documentElement.getAttribute('data-theme');
  setTheme(cur === 'dark' ? 'light' : 'dark');
});

// smooth scroll on nav
document.querySelectorAll('.nav a').forEach(a=>{
  a.addEventListener('click', e=>{
    e.preventDefault();
    document.querySelector(a.getAttribute('href'))?.scrollIntoView({behavior:'smooth', block:'start'});
  });
});

// chat logic with typing effect + fallback to /api/chat
const log = document.getElementById('chatLog');
const input = document.getElementById('chatInput');
const send  = document.getElementById('chatSend');
const clear = document.getElementById('clearBtn');

function addBubble(role, text){
  const div = document.createElement('div');
  div.className = 'bubble ' + (role==='user' ? 'user' : 'bot');
  log.appendChild(div);
  if(role==='bot'){ typeWriter(div, text); } else { div.textContent = text; }
  log.scrollTop = log.scrollHeight;
}
function typeWriter(el, text){
  el.textContent = '';
  let i = 0, speed = 14;
  (function step(){
    el.textContent += text.slice(i, i+speed);
    i += speed;
    log.scrollTop = log.scrollHeight;
    if(i < text.length) requestAnimationFrame(step);
  })();
}
async function sendMessage(){
  const msg = input.value.trim();
  if(!msg) return;
  addBubble('user', msg);
  input.value = '';

  const wait = document.createElement('div');
  wait.className = 'bubble bot';
  wait.textContent = '…';
  log.appendChild(wait);
  log.scrollTop = log.scrollHeight;

  const body = { message: msg };
  const headers = { 'Content-Type': 'application/json' };
  async function call(ep){
    const r = await fetch(ep, { method:'POST', headers, body: JSON.stringify(body) });
    if(!r.ok) throw new Error(await r.text());
    const data = await r.json();
    return data.reply || 'Sorry, I could not generate a response.';
  }

  try{
    let reply;
    try { reply = await call('/chat'); }  // works with your current mounting
    catch { reply = await call('/api/chat'); }
    wait.remove();
    addBubble('bot', reply);
  }catch(err){
    wait.remove();
    addBubble('bot', 'Sorry, I hit an error. Please try again.');
    console.error(err);
  }
}
send.addEventListener('click', sendMessage);
input.addEventListener('keydown', e=>{ if(e.key==='Enter') sendMessage(); });
clear.addEventListener('click', ()=>{ log.innerHTML=''; addBubble('bot','Hey! I’m Lokesh’s portfolio bot. Ask about my skills, projects, or experience.'); });

// subtle keyboard hover effect for accessibility
document.querySelectorAll('.hoverable').forEach(el=>{
  el.tabIndex = 0;
  el.addEventListener('keydown', e=>{
    if(e.key === 'Enter' || e.key === ' '){
      el.classList.add('hover');
      setTimeout(()=>el.classList.remove('hover'), 220);
    }
  });
});
