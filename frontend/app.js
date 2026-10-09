const $ = (s, r=document) => r.querySelector(s);
const $$ = (s, r=document) => [...r.querySelectorAll(s)];
const API = '';
let token = localStorage.getItem('resolve_token') || '';
let currentUser = JSON.parse(localStorage.getItem('resolve_user') || 'null');
let complaints = [], notifications = [], users = [];

function toast(message, type='success') {
  const el=$('#toast'); el.textContent=message; el.className=`toast ${type}`;
  clearTimeout(window.toastTimer); window.toastTimer=setTimeout(()=>el.classList.add('hidden'),4500);
}
async function api(path, options={}) {
  const headers={'Content-Type':'application/json', ...(options.headers||{})};
  if(token) headers.Authorization=`Bearer ${token}`;
  const response=await fetch(API+path,{...options,headers});
  const text=await response.text(); let data={};
  try{data=text?JSON.parse(text):{}}catch{data={detail:text||'Unexpected response'};}
  if(!response.ok) throw new Error(data.detail||data.message||`Request failed (${response.status})`);
  return data;
}
function esc(v=''){return String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function statusPill(s='OPEN'){const key=s.toLowerCase();return `<span class="pill pill-${key}">${esc(s.replaceAll('_',' '))}</span>`;}
function empty(msg){return `<div class="empty">${esc(msg)}</div>`;}
function dateText(s){if(!s)return '—'; const d=new Date(s.replace(' ','T')+'Z');return isNaN(d)?esc(s):d.toLocaleDateString(undefined,{day:'2-digit',month:'short',year:'numeric'});}
function tableRows(items, admin=false){
 if(!items.length)return empty('No complaints yet. Use “New complaint” to register your first request.');
 return `<div class="table-wrap"><table><thead><tr><th>ID</th><th>Complaint</th><th>Category</th><th>Status</th><th>Created</th>${admin?'<th>Assigned to</th><th>Action</th>':''}</tr></thead><tbody>${items.map(c=>`<tr><td class="id-cell">#${c.id}</td><td><b>${esc(c.title)}</b><br><span style="color:#9aa3b1">${esc((c.description||'').slice(0,65))}${(c.description||'').length>65?'…':''}</span></td><td>${esc(c.category)}</td><td>${statusPill(c.status)}</td><td>${dateText(c.created_at)}</td>${admin?`<td>${c.assigned_to?`User #${c.assigned_to}`:'<span style="color:#a0a8b5">Unassigned</span>'}</td><td><div class="admin-actions"><select id="assignee-${c.id}" aria-label="Assignee">${users.map(u=>`<option value="${u.id}" ${String(c.assigned_to)===String(u.id)?'selected':''}>${esc(u.name)} (#${u.id})</option>`).join('')}</select><button class="small-btn" onclick="assignComplaint(${c.id})">Assign</button><select id="status-${c.id}" aria-label="Status">${['OPEN','ASSIGNED','IN_PROGRESS','RESOLVED','CLOSED','REJECTED'].map(s=>`<option ${c.status===s?'selected':''}>${s}</option>`).join('')}</select><button class="small-btn" onclick="changeStatus(${c.id})">Save</button></div></td>`:''}</tr>`).join('')}</tbody></table></div>`;
}
function showView(view){
 $$('.view').forEach(v=>v.classList.add('hidden')); const el=$(`#${view}-view`); if(el)el.classList.remove('hidden');
 $$('.nav').forEach(b=>b.classList.toggle('active',b.dataset.view===view));
 const titles={dashboard:'Dashboard',complaints:'My complaints',new:'New complaint',notifications:'Notifications',admin:'Admin desk'};
 $('#page-title').textContent=titles[view]||'Dashboard';
 if(view==='new')$('#complaint-form').reset();
 if(view==='complaints')$('#complaints-table').innerHTML=tableRows(complaints);
 if(view==='admin')renderAdmin();
 if(view==='notifications')renderNotifications();
}
function showAuthTab(tab){
 $$('.auth-tab').forEach(b=>b.classList.toggle('active',b.dataset.auth===tab));
 $('#login-form').classList.toggle('hidden',tab!=='login'); $('#register-form').classList.toggle('hidden',tab!=='register');
}
function renderDashboard(){
 $('#stat-total').textContent=complaints.length;
 $('#stat-open').textContent=complaints.filter(c=>['OPEN','ASSIGNED'].includes(c.status)).length;
 $('#stat-progress').textContent=complaints.filter(c=>c.status==='IN_PROGRESS').length;
 $('#stat-resolved').textContent=complaints.filter(c=>['RESOLVED','CLOSED'].includes(c.status)).length;
 $('#recent-table').innerHTML=complaints.length?tableRows(complaints.slice(0,5)):empty('No complaints yet. Register a request to see it here.');
}
function renderAdmin(){ $('#admin-table').innerHTML=tableRows(complaints,true); }
function renderNotifications(){
 $('#notifications-list').innerHTML=notifications.length?notifications.map(n=>`<div class="notification"><div class="notification-icon">${n.is_read?'✓':'♧'}</div><div><b>${esc(n.message)}</b><p>Complaint ${n.complaint_id?'#'+n.complaint_id:'update'}</p><small>${dateText(n.created_at)} ${n.is_read?'· Read':'· New'}</small></div>${!n.is_read?`<button class="text-button" onclick="markRead(${n.id})">Mark read</button>`:''}</div>`).join(''):empty('You’re all caught up. Notifications will appear here when something changes.');
}
async function loadData(){
 try{
  complaints=await api('/api/complaints/complaints');
  notifications=await api('/api/notifications/notifications');
  if(currentUser.role==='ADMIN'){
   try{users=await api('/api/users/users');}catch(e){users=[];}
   try{await api('/api/assignments/assignments');}catch(e){}
  }
  renderDashboard(); $('#complaints-table').innerHTML=tableRows(complaints); renderNotifications(); renderAdmin();
 }catch(e){toast(e.message+' — please sign in again if your session expired.','error');}
}
async function enterWorkspace(){
 $('#auth-panel').classList.add('hidden');$('#workspace').classList.remove('hidden');$('#logout').classList.remove('hidden');
 $('#side-email').textContent=currentUser.email;$('#side-role').textContent=currentUser.role==='ADMIN'?'Administrator':'Standard user';
 $('#avatar').textContent=(currentUser.email||'U').charAt(0).toUpperCase();$('#welcome-name').textContent=(currentUser.email||'there').split('@')[0];
 $$('.admin-only').forEach(x=>x.classList.toggle('hidden',currentUser.role!=='ADMIN'));
 $('#connection-label').textContent='Connected'; showView('dashboard'); await loadData();
}
function signOut(){token='';currentUser=null;localStorage.removeItem('resolve_token');localStorage.removeItem('resolve_user');complaints=[];notifications=[];$('#workspace').classList.add('hidden');$('#auth-panel').classList.remove('hidden');$('#logout').classList.add('hidden');$$('.admin-only').forEach(x=>x.classList.add('hidden'));showAuthTab('login');$('#connection-label').textContent='Signed out';}
$$('.nav').forEach(b=>b.addEventListener('click',()=>showView(b.dataset.view)));
$$('[data-goto]').forEach(b=>b.addEventListener('click',()=>showView(b.dataset.goto)));
$('#header-new').addEventListener('click',()=>{if(currentUser)showView('new');else{showAuthTab('login');$('#auth-panel').scrollIntoView({behavior:'smooth'});}});
$$('.auth-tab').forEach(b=>b.addEventListener('click',()=>showAuthTab(b.dataset.auth)));
$('#logout').addEventListener('click',signOut);
$('#login-form').addEventListener('submit',async e=>{
 e.preventDefault();const f=new FormData(e.currentTarget);
 try{const data=await api('/api/auth/login',{method:'POST',body:JSON.stringify({email:f.get('email'),password:f.get('password')})});token=data.access_token;currentUser=data.user;localStorage.setItem('resolve_token',token);localStorage.setItem('resolve_user',JSON.stringify(currentUser));await enterWorkspace();toast('Signed in successfully.');}
 catch(err){toast(err.message,'error');}
});
$('#register-form').addEventListener('submit',async e=>{
 e.preventDefault();const f=new FormData(e.currentTarget);
 try{await api('/api/auth/register',{method:'POST',body:JSON.stringify({name:f.get('name'),email:f.get('email'),password:f.get('password')})});toast('Account created. You can now sign in.');showAuthTab('login');$('#login-form [name=email]').value=f.get('email');}
 catch(err){toast(err.message,'error');}
});
$('#complaint-form').addEventListener('submit',async e=>{
 e.preventDefault();const f=new FormData(e.currentTarget);
 try{const c=await api('/api/complaints/complaints',{method:'POST',body:JSON.stringify({title:f.get('title'),category:f.get('category'),description:f.get('description')})});toast(`Complaint #${c.id} registered successfully.`);await loadData();showView('complaints');}
 catch(err){toast(err.message,'error');}
});
async function assignComplaint(id){
 const assignee=Number($(`#assignee-${id}`).value);if(!assignee){toast('Please select an assignee first.','error');return;}
 try{await api('/api/assignments/assignments',{method:'POST',body:JSON.stringify({complaint_id:id,assignee_id:assignee,note:'Assigned from admin dashboard'})});toast(`Complaint #${id} assigned.`);await loadData();}
 catch(e){toast(e.message,'error');}
}
async function changeStatus(id){
 const status=$(`#status-${id}`).value;
 try{await api(`/api/complaints/complaints/${id}/status`,{method:'PATCH',body:JSON.stringify({status})});toast(`Complaint #${id} updated to ${status.replaceAll('_',' ')}.`);await loadData();}
 catch(e){toast(e.message,'error');}
}
async function markRead(id){try{await api(`/api/notifications/notifications/${id}/read`,{method:'PATCH',body:'{}'});notifications=await api('/api/notifications/notifications');renderNotifications();}catch(e){toast(e.message,'error');}}
$('#refresh-notifications').addEventListener('click',async()=>{try{notifications=await api('/api/notifications/notifications');renderNotifications();toast('Notifications refreshed.');}catch(e){toast(e.message,'error');}});
$('#refresh-admin').addEventListener('click',async()=>{await loadData();toast('Admin desk refreshed.');});
async function checkConnection(){try{await fetch('/health');$('#connection-label').textContent='Connected';}catch{$('#connection-label').textContent='API unavailable';}}
checkConnection();
if(token&&currentUser)enterWorkspace().catch(()=>signOut());
