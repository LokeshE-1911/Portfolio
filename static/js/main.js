// ========= Theme toggle =========
const themeBtn = document.getElementById('themeBtn');
function setTheme(mode){
  document.documentElement.setAttribute('data-theme', mode);
  localStorage.setItem('theme', mode);
  if(themeBtn) themeBtn.textContent = mode === 'dark' ? '🌙' : '☀️';
}
setTheme(localStorage.getItem('theme') || 'dark');
if (themeBtn) {
  themeBtn.addEventListener('click', ()=>{
    const cur = document.documentElement.getAttribute('data-theme');
    setTheme(cur === 'dark' ? 'light' : 'dark');
  });
}

// ========= Mobile sidebar toggle =========
const sidebar = document.querySelector('.sidebar');
const menuToggle = document.getElementById('menuToggle');
if (menuToggle) {
  menuToggle.addEventListener('click', () => {
    sidebar.classList.toggle('open');
  });
}

// ========= Smooth scroll + scrollspy =========
const navLinks = document.querySelectorAll('.nav a');
navLinks.forEach(a=>{
  a.addEventListener('click', e=>{
    e.preventDefault();
    const id = a.getAttribute('href');
    document.querySelector(id)?.scrollIntoView({behavior:'smooth', block:'start'});
    // Close mobile sidebar after click
    if (sidebar.classList.contains('open')) sidebar.classList.remove('open');
  });
});

// Scrollspy intersection observer
const sections = [...document.querySelectorAll('section[id]')];
const spy = new IntersectionObserver((entries)=>{
  entries.forEach(entry=>{
    const id = entry.target.getAttribute('id');
    const link = document.querySelector(`.nav a[href="#${id}"]`);
    if (!link) return;
    if (entry.isIntersecting) {
      navLinks.forEach(l=>l.classList.remove('active'));
      link.classList.add('active');
    }
  });
}, { rootMargin: '-40% 0px -55% 0px', threshold: 0 });

sections.forEach(s=>spy.observe(s));

// ========= Section reveal on scroll =========
const revealEls = document.querySelectorAll('.reveal');
const obs = new IntersectionObserver((entries)=>{
  entries.forEach(e=>{
    if(e.isIntersecting){
      e.target.classList.add('in');
      obs.unobserve(e.target);
    }
  });
}, { threshold: 0.18 });
revealEls.forEach(el=>obs.observe(el));

// ========= Year in footer =========
const y = document.getElementById('year');
if (y) y.textContent = new Date().getFullYear();

// ========= Chat logic (kept from your version, tightened) =========
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
if (send) send.addEventListener('click', sendMessage);
if (input) input.addEventListener('keydown', e=>{ if(e.key==='Enter') sendMessage(); });
if (clear) clear.addEventListener('click', ()=>{ log.innerHTML=''; addBubble('bot','Hey! I’m Lokesh’s portfolio Assistant. Ask about my skills, projects, or experience.'); });
