// ===== Theme toggle =====
const themeBtn = document.getElementById('themeBtn');
function setTheme(mode){
  document.documentElement.setAttribute('data-theme', mode);
  localStorage.setItem('theme', mode);
  if(themeBtn) themeBtn.textContent = mode === 'dark' ? '🌙' : '☀️';
}
setTheme(localStorage.getItem('theme') || 'dark');
themeBtn?.addEventListener('click', ()=>{
  const cur = document.documentElement.getAttribute('data-theme');
  setTheme(cur === 'dark' ? 'light' : 'dark');
});

// ===== Mobile nav =====
const menuBtn = document.getElementById('menuBtn');
const nav = document.querySelector('.nav');
menuBtn?.addEventListener('click', ()=> nav.classList.toggle('open'));

// ===== Scrollspy + smooth scroll =====
const links = document.querySelectorAll('.nav a');
links.forEach(a=>{
  a.addEventListener('click', e=>{
    e.preventDefault();
    document.querySelector(a.getAttribute('href'))?.scrollIntoView({behavior:'smooth', block:'start'});
    nav.classList.remove('open');
  });
});
const sections = [...document.querySelectorAll('section[id]')];
const spy = new IntersectionObserver((entries)=>{
  entries.forEach(entry=>{
    const id = entry.target.getAttribute('id');
    const link = document.querySelector(`.nav a[href="#${id}"]`);
    if (!link) return;
    if (entry.isIntersecting) {
      links.forEach(l=>l.classList.remove('active'));
      link.classList.add('active');
    }
  });
}, { rootMargin: '-40% 0px -55% 0px', threshold: 0 });
sections.forEach(s=>spy.observe(s));

// ===== Reveal on scroll =====
const revealEls = document.querySelectorAll('.reveal');
const obs = new IntersectionObserver((entries)=>{
  entries.forEach(e=>{
    if(e.isIntersecting){ e.target.classList.add('in'); obs.unobserve(e.target); }
  });
}, { threshold: 0.15 });
revealEls.forEach(el=>obs.observe(el));

// ===== Year in footer =====
document.getElementById('year')?.append(new Date().getFullYear());

// ===== Rolling ticker duplication (infinite) =====
const track = document.getElementById('rolesTrack');
if (track) {
  // Duplicate contents to achieve seamless 50% -> 0% loop
  track.innerHTML = track.innerHTML + track.innerHTML;
}

// ===== Chat logic =====
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
  let i = 0, step = 2;
  const tick = ()=> {
    el.textContent += text.slice(i, i+step);
    i += step;
    log.scrollTop = log.scrollHeight;
    if (i < text.length) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

async function sendMessage(){
  const msg = (input?.value || '').trim();
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
    try { reply = await call('/chat'); }
    catch { reply = await call('/api/chat'); }
    wait.remove();
    addBubble('bot', reply);
  }catch(err){
    wait.remove();
    addBubble('bot', 'Sorry, I hit an error. Please try again.');
    console.error(err);
  }
}
send?.addEventListener('click', sendMessage);
input?.addEventListener('keydown', e=>{ if(e.key==='Enter') sendMessage(); });
clear?.addEventListener('click', ()=>{ log.innerHTML=''; addBubble('bot','Hey! I’m Lokesh’s portfolio Assistant. Ask about my skills, projects, or experience.'); });
