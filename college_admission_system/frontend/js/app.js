const state = { token: localStorage.getItem('bcu_token'), user: null, courses: [], colleges: [], selectedAdmission: null };
const API_ROOT = window.location.protocol === 'file:' || (window.location.port && window.location.port !== '8000')
  ? 'http://127.0.0.1:8000/api'
  : '/api';
const $ = selector => document.querySelector(selector);
const money = value => `₹${Number(value || 0).toLocaleString('en-IN')}`;
const UNIVERSITY_HERO_IMAGE = 'assets/bangalore-university.jpg';

// Add an accessible show/hide control to every login and registration
// password field across the shared and standalone portal pages.
function setupPasswordToggles() {
  document.querySelectorAll('input[type="password"]').forEach(input => {
    if (input.dataset.passwordToggleReady === 'true') return;
    input.dataset.passwordToggleReady = 'true';

    const group = document.createElement('div');
    group.className = 'input-group password-input-group';
    group.style.margin = '6px 0 16px';
    input.style.margin = '0';
    input.parentNode.insertBefore(group, input);
    group.appendChild(input);

    const toggle = document.createElement('button');
    toggle.type = 'button';
    toggle.className = 'btn btn-outline-secondary password-toggle';
    toggle.style.minWidth = '88px';
    toggle.style.whiteSpace = 'nowrap';
    toggle.style.fontWeight = '600';
    toggle.style.backgroundColor = '#f1f5f9';
    toggle.style.color = '#102a43';
    toggle.textContent = '👁 Show';
    toggle.setAttribute('aria-label', 'Show password');
    toggle.title = 'Show password';
    toggle.addEventListener('click', () => {
      const showing = input.type === 'text';
      input.type = showing ? 'password' : 'text';
      toggle.textContent = showing ? '👁 Show' : '🙈 Hide';
      toggle.setAttribute('aria-label', `${showing ? 'Show' : 'Hide'} password`);
      toggle.title = `${showing ? 'Show' : 'Hide'} password`;
    });
    group.appendChild(toggle);
  });
}

// Run immediately while the auth forms are already present in the page.
setupPasswordToggles();

function applyUniversityBranding() {
  document.querySelectorAll('.eyebrow').forEach(element => { element.textContent = element.textContent.replace(/BENGALURU CITY UNIVERSITY/gi, 'BANGALORE UNIVERSITY'); });
  document.querySelectorAll('.hero.intro').forEach(hero => {
    hero.style.backgroundImage = `linear-gradient(90deg, rgba(8, 30, 57, .22), rgba(255, 255, 255, .16)), url("${UNIVERSITY_HERO_IMAGE}")`;
    hero.style.backgroundPosition = 'center';
    hero.style.backgroundSize = 'cover';
  });
}

function removeAdmitAIBranding() {
  document.title = document.title.replace(/BCU\s+AdmitAI/gi, 'Bangalore University');
  document.querySelectorAll('.navbar-brand').forEach(brand => {
    brand.innerHTML = brand.innerHTML.replace(/<span>\s*AdmitAI\s*<\/span>/gi, '');
  });
  document.querySelectorAll('body *').forEach(element => {
    if (element.children.length === 0 && element.textContent) {
      element.textContent = element.textContent.replace(/AdmitAI/gi, 'Admission Assistant').replace(/AI admission assistant/gi, 'Admission assistant');
    }
  });
}

function setupHome() {
  const landing = $('#landing');
  if (!landing) return;
  document.body.classList.add('home-page');
  if (!document.querySelector('link[data-home-style]')) {
    const style = document.createElement('link');
    style.rel = 'stylesheet';
    style.href = 'css/home.css';
    style.dataset.homeStyle = 'true';
    document.head.appendChild(style);
  }
  const heroContent = landing.querySelector('.hero.intro > div');
  if (heroContent) heroContent.innerHTML = '<p class="eyebrow">BANGALORE UNIVERSITY ADMISSION PORTAL</p><h1>One University.<br><em>Endless Opportunities.</em></h1><div class="home-rule"></div><p class="hero-copy">Bangalore University Admission Portal<br>Your gateway to a seamless admission experience.<br>Choose your portal and get started.</p>';
  const brand = document.querySelector('.navbar-brand');
  if (brand) brand.innerHTML = '<img class="brand-mark" src="assets/bangalore-university-logo.png" alt="Bangalore University logo"><span class="brand-text"><b>ಬೆಂಗಳೂರು ನಗರ ವಿಶ್ವವಿದ್ಯಾಲಯ</b><small>BANGALORE UNIVERSITY</small></span>';
  const cards = landing.querySelectorAll('.portal-card');
  const portalMeta = [
    ['🎓', 'student.html', 'Student Registration / Login'],
    ['🏛', 'college.html', 'Faculty Registration / Login'],
    ['🛡', 'admin.html', 'Administrator Login']
  ];
  cards.forEach((card, index) => {
    if (!card.querySelector('.portal-icon')) card.insertAdjacentHTML('afterbegin', `<div class="portal-icon">${portalMeta[index][0]}</div>`);
    const oldButton = card.querySelector('button');
    if (oldButton) oldButton.outerHTML = `<a class="portal-action" href="${portalMeta[index][1]}">${portalMeta[index][2]} <span>→</span></a>`;
  });
  if (!landing.querySelector('.home-features')) landing.insertAdjacentHTML('beforeend', '<section class="home-features container"><div><b>✓</b><strong>Secure & Reliable</strong><small>Your data is protected.</small></div><div><b>◷</b><strong>Easy & Transparent</strong><small>Simple process with real-time tracking.</small></div><div><b>▥</b><strong>Real-time Updates</strong><small>Get the latest admission updates.</small></div><div><b>◉</b><strong>24/7 Support</strong><small>We are here to help.</small></div></section><footer class="home-footer"><span>© 2025 Bangalore University. All rights reserved.</span><span>Privacy Policy　|　Terms & Conditions　|　Help Desk</span></footer>');
}

async function api(path, options = {}) {
  const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData;
  const headers = { ...(options.body && !isFormData ? { 'Content-Type': 'application/json' } : {}), ...(options.headers || {}) };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  const response = await fetch(`${API_ROOT}${path}`, { ...options, headers });
  const body = await response.json().catch(() => null);
  if (!response.ok) throw new Error(body?.detail || 'Request failed');
  return body;
}

function toast(message, isError = false) {
  const element = $('#toast');
  element.textContent = message;
  element.style.background = isError ? '#9d3843' : '#153c67';
  element.style.display = 'block';
  window.setTimeout(() => { element.style.display = 'none'; }, 3500);
}

function show(id) {
  document.querySelectorAll('.view').forEach(element => element.classList.remove('active'));
  const target = $(`#${id}`);
  if (target) target.classList.add('active');
  else if (id === 'landing') { window.location.href = 'index.html'; return; }
  const landing = $('#landing');
  if (landing) landing.classList.toggle('hidden', id !== 'landing');
  window.scrollTo({ top: 0, behavior: 'smooth' });
  if (id === 'applications') loadApplications();
  if (id === 'admin-dashboard') loadAdminDashboard();
  if (id === 'faculty-dashboard') loadFacultyDashboard();
}

function openPortal(portal) {
  const destinations = { student: 'student.html', faculty: 'college.html', admin: 'admin.html' };
  if (destinations[portal]) window.location.assign(destinations[portal]);
}

function toggleTab(portal, tab) {
  const prefix = portal === 'student' ? 'student' : 'faculty';
  $(`#${prefix}Login`).classList.toggle('d-none', tab !== 'login');
  $(`#${prefix}Register`).classList.toggle('d-none', tab !== 'register');
}

function setMessage(id, text, error = false) {
  const element = $(`#${id}`);
  if (element) { element.textContent = text; element.style.color = error ? '#b33a45' : '#247a5a'; }
}

function uniqueCourseItems(items) {
  const seen = new Set();
  return (items || []).filter(item => {
    const key = (item.course_name || '').replace(/[–—-]/g, ' ').replace(/\s+/g, ' ').trim().toLowerCase() || `id:${item.course_id}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function nav() {
  const links = $('#navLinks');
  if (!links) return;
  if (!state.user) {
    if ($('#landing')) links.innerHTML = '<a class="nav-link active" href="index.html">Home</a><a class="nav-link" href="#about">About Us</a><a class="nav-link" href="portals.html">Admission⌄</a><a class="nav-link" href="portals.html">Colleges</a><a class="nav-link" href="#notices">Notices</a><a class="nav-link" href="#contact">Contact Us</a><a class="login-button" href="student.html">♙ Login</a>';
    else links.innerHTML = '<a class="nav-link" href="index.html">Home</a><a class="nav-link" onclick="openPortal(\'student\')">Student</a><a class="nav-link" onclick="openPortal(\'faculty\')">College</a><a class="nav-link" onclick="openPortal(\'admin\')">Admin</a>';
    return;
  }
  if (state.user.role === 'student') {
    links.innerHTML = `<span class="nav-profile text-white small align-self-center me-2">${state.user.name}</span><a class="nav-link" href="student.html">Dashboard</a><a class="nav-link" href="index.html#assistant">Admission assistant</a><a class="nav-link" href="student-admission.html">Admission process</a><a class="nav-link" href="student-status.html">Selection status</a><button class="btn btn-sm btn-outline-light ms-2" onclick="logout()">Logout</button>`;
  } else if (state.user.role === 'faculty') {
    links.innerHTML = `<span class="nav-profile text-white small align-self-center me-2">${state.user.name}</span><a class="nav-link" onclick="show('faculty-dashboard')">Applicants</a><a class="nav-link" onclick="loadLatestMerit()">Merit list</a><button class="btn btn-sm btn-outline-light ms-2" onclick="logout()">Logout</button>`;
  } else {
    links.innerHTML = `<span class="nav-profile text-white small align-self-center me-2">${state.user.name}</span><a class="nav-link" href="admin.html">Admin dashboard</a><button class="btn btn-sm btn-outline-light ms-2" onclick="logout()">Logout</button>`;
  }
}

async function refreshUser() {
  if (!state.token) { state.user = null; nav(); if (document.body.dataset.adminPage) window.location.assign('admin.html'); return; }
  try {
    state.user = await api('/auth/me');
    nav();
    if (state.user.role === 'student') {
      if ($('#studentWelcome')) $('#studentWelcome').textContent = `Welcome, ${state.user.name.split(' ')[0]}`;
      const p = state.user.profile || {};
      if ($('#studentProfileText')) $('#studentProfileText').textContent = p.qualification ? `${p.qualification}${p.percentage ? ` • ${p.percentage}%` : ''}` : 'Complete your academic profile.';
      if ($('#profileForm')) fillProfile();
      loadChatHistory();
      loadStudentDocuments();
      if ($('#student-dashboard') && !$('#landing')) show('student-dashboard');
    } else if (state.user.role === 'faculty') {
      if ($('#facultyWelcome')) $('#facultyWelcome').textContent = `${state.user.name} · ${state.user.faculty.college_name}`;
      if ($('#faculty-dashboard') && !$('#landing')) show('faculty-dashboard');
    } else if (state.user.role === 'admin') {
      if ($('#admin-dashboard') && !$('#landing')) show('admin-dashboard');
      else if (document.body.dataset.adminPage) loadAdminPage();
    }
  } catch (_) { if (document.body.dataset.adminPage) window.location.assign('admin.html'); else logout(false); }
}

function logout(showLanding = true) {
  state.token = null; state.user = null; localStorage.removeItem('bcu_token'); nav();
  if (showLanding) show('landing');
}

function saveToken(result) {
  state.token = result.access_token;
  localStorage.setItem('bcu_token', state.token);
}

function formObject(form) { return Object.fromEntries(new FormData(form)); }

async function loadCollegeOptions() {
  try {
    const [colleges, courses] = await Promise.all([api('/colleges'), api('/courses')]);
    $('#facultyCollege').innerHTML = '<option value="">Select your college</option>' + colleges.map(c => `<option value="${c.id}">${c.college_name} — ${c.location}</option>`).join('');
    if (!$('#facultyRegisterCourse')) $('#facultyCollege').insertAdjacentHTML('afterend', '<label>Assigned course</label><select class="form-select" id="facultyRegisterCourse" name="course_id" required></select>');
    $('#facultyRegisterCourse').innerHTML = '<option value="">Select the course you will manage</option>' + courses.map(course => `<option value="${course.id}">${course.course_name}</option>`).join('');
  } catch (error) { setMessage('facultyAuthMessage', error.message, true); }
}

async function loadCatalogue() {
  const [courses, colleges] = await Promise.all([api('/courses'), api('/colleges')]);
  state.courses = uniqueCourseItems(courses);
  state.colleges = colleges;
  fillAdmissionSelects();
}

function fillAdmissionSelects() {
  const courseSelect = $('#courseSelect');
  if (!courseSelect) return;
  courseSelect.innerHTML = '<option value="">Choose a course</option>' + state.courses.map(c => `<option value="${c.id}">${c.course_name} — ${money(c.fees)}</option>`).join('');
  const updateColleges = () => {
    const id = Number(courseSelect.value);
    $('#collegeSelect').innerHTML = '<option value="">Choose a college</option>' + state.colleges.filter(c => c.offerings.some(o => o.course_id === id)).map(c => `<option value="${c.id}">${c.college_name} — ${c.location}</option>`).join('');
  };
  courseSelect.onchange = updateColleges;
  updateColleges();
}

function fillProfile() {
  const profile = state.user?.profile || {};
  Object.entries(profile).forEach(([key, value]) => { if ($('#profileForm')?.elements[key]) $('#profileForm').elements[key].value = value ?? ''; });
}

function addMessage(text, kind) {
  const element = document.createElement('article');
  element.className = `message ${kind}`;
  element.textContent = text;
  $('#chatMessages').appendChild(element);
  $('#chatMessages').scrollTop = $('#chatMessages').scrollHeight;
}

async function loadChatHistory() {
  if (!state.user || state.user.role !== 'student' || !$('#chatMessages')) return;
  try {
    const history = await api('/student/chat-history');
    if (!history.length) return;
    $('#chatMessages').innerHTML = '';
    history.forEach(record => {
      addMessage(record.message, 'student');
      addMessage(record.response, 'agent');
    });
  } catch (_) { /* Chat history is optional if the database is temporarily unavailable. */ }
}

function recommendationCards(data) {
  const courses = uniqueCourseItems(data.courses).map(course => `<div class="col-md-4"><article class="recommend-card"><div class="score">${course.match_score}% MATCH</div><h5 class="mt-2">${course.course_name}</h5><p class="small">${course.reason}</p><b>${money(course.fees)}</b><button class="btn btn-sm btn-outline-primary d-block mt-3" onclick="startApplication(${course.course_id}, null)">Select course</button></article></div>`).join('');
  const colleges = (data.colleges || []).filter((college, index, list) => list.findIndex(item => `${item.college_id}:${item.course_id}` === `${college.college_id}:${college.course_id}`) === index).map(college => `<div class="col-md-4"><article class="recommend-card"><div class="score">COLLEGE OPTION</div><h5 class="mt-2">${college.college_name}</h5><p class="small">${college.reason}</p><button class="btn btn-sm btn-outline-primary" onclick="startApplication(${college.course_id}, ${college.college_id})">Apply here</button></article></div>`).join('');
  const message = data.message ? `<div class="col-12"><p class="form-message ${courses.length ? '' : 'text-danger'}">${data.message}</p></div>` : '';
  $('#recommendationArea').innerHTML = message + courses + colleges;
}

async function startApplication(courseId, collegeId) {
  await loadCatalogue();
  show('applications');
  $('#courseSelect').value = courseId;
  $('#courseSelect').dispatchEvent(new Event('change'));
  if (collegeId) $('#collegeSelect').value = collegeId;
  if ($('#admissionForm')) $('#admissionForm').classList.remove('d-none');
  if ($('#selectedCourseSummary')) $('#selectedCourseSummary').textContent = `Selected course: ${state.courses.find(course => course.id === Number(courseId))?.course_name || 'Selected course'}. Complete the address and previous-institution fields below.`;
}

async function loadApplications() {
  if (!state.user || state.user.role !== 'student') return;
  try {
    await loadCatalogue();
    const applications = await api('/admissions/my');
    $('#applicationList').innerHTML = applications.length ? applications.map(a => `<div class="college-item"><b>${a.application_number}</b> — ${a.course_name}<br>${a.college_name}<br><span class="badge-status">${a.status}</span> <span class="badge-status">Payment: ${a.payment?.payment_status || 'PENDING'}</span>${a.payment?.payment_status === 'PENDING' ? ` <button class="btn btn-sm btn-primary ms-2" onclick="pay(${a.id})">Pay ₹500 (Demo)</button>` : ''}</div>`).join('') : '<p class="muted">No application submitted yet.</p>';
  } catch (error) { toast(error.message, true); }
}

async function pay(admissionId) {
  try {
    const result = await api(`/payments/${admissionId}/simulate`, { method: 'POST' });
    $('#confirmation').innerHTML = `<b>Payment successful</b><br>Transaction ID: ${result.transaction_id}<br>Your application is now ready for college review.`;
    toast(result.message); loadApplications();
  } catch (error) { toast(error.message, true); }
}

async function loadFacultyDashboard() {
  if (!state.user || state.user.role !== 'faculty') return;
  try {
    if ($('#facultyWelcome') && state.user.faculty) $('#facultyWelcome').textContent = `${state.user.name} · ${state.user.faculty.course_name || 'Assigned course'} dashboard`;
    if (!$('#facultyCourse')) {
      $('#facultyApplications').closest('.card-panel').insertAdjacentHTML('beforebegin', '<div class="card-panel mb-4"><h4>Release merit list</h4><div class="row align-items-end"><div class="col-md-6"><label>Course</label><select id="facultyCourse" class="form-select"></select></div><div class="col-md-3"><label>Number of students</label><input id="facultyLimit" class="form-control" type="number" min="1" max="100" value="10"></div><div class="col-md-3"><button class="btn btn-dark w-100" onclick="releaseMeritList()">Release list</button></div></div><p class="small muted mt-2 mb-0">Enter 10, 20, or any number up to 100. Only paid applications for the selected course are ranked.</p></div>');
    }
    const courses = await api('/faculty/courses');
    const courseSelect = $('#facultyCourse');
    if (courseSelect) courseSelect.innerHTML = '<option value="">Choose course for merit list</option>' + courses.map(course => `<option value="${course.course_id}">${course.course_name}</option>`).join('');
    const applications = await api('/faculty/applications');
    const row = a => `<tr><td>${a.application_number}</td><td>${a.student_name}<br><small>${a.student_email}</small></td><td>${a.student_degree || '—'} / ${a.student_percentage || '—'}%</td><td>${a.course_name}</td><td>${a.payment?.payment_status || 'PENDING'}</td><td>${a.status}</td></tr>`;
    const pending = applications.filter(a => a.admission_pending);
    const applied = applications.filter(a => !a.admission_pending);
    $('#facultyApplications').innerHTML = applied.length ? applied.map(row).join('') : '<tr><td colspan="6">No applications for your assigned course yet.</td></tr>';
    if (!$('#facultyPendingAdmissions')) $('#facultyApplications').closest('.card-panel').insertAdjacentHTML('afterend', '<div class="card-panel mt-4"><h4>Admission pending list (merit listed)</h4><div class="table-responsive"><table class="table"><thead><tr><th>Rank</th><th>Application</th><th>Student</th><th>Course</th><th>Percentage</th></tr></thead><tbody id="facultyPendingAdmissions"></tbody></table></div></div>');
    $('#facultyPendingAdmissions').innerHTML = pending.length ? pending.map((a, index) => `<tr><td>${index + 1}</td><td>${a.application_number}</td><td>${a.student_name}</td><td>${a.course_name}</td><td>${a.student_percentage || '—'}%</td></tr>`).join('') : '<tr><td colspan="5">No merit-listed students yet.</td></tr>';
    await loadLatestMerit(false);
  } catch (error) { toast(error.message, true); }
}

async function releaseMeritList() {
  const courseId = Number($('#facultyCourse')?.value || 0);
  const limit = Number($('#facultyLimit')?.value || 10);
  if (!courseId) { toast('Choose a course before releasing the merit list', true); return; }
  try {
    const list = await api('/faculty/merit-list/release', { method: 'POST', body: JSON.stringify({ course_id: courseId, limit }) });
    renderMeritList(list);
    const deliveries = list.email_delivery || [];
    const sent = deliveries.filter(result => result.sent).length;
    const failed = deliveries.length - sent;
    toast(`Merit list released. Congratulations emails sent: ${sent}${failed ? `; failed: ${failed}` : ''}`, failed > 0);
  }
  catch (error) { toast(error.message, true); }
}

async function loadLatestMerit(navigate = true) {
  if (navigate) show('faculty-dashboard');
  try { const list = await api('/faculty/merit-list'); renderMeritList(list); }
  catch (error) { toast(error.message, true); }
}

function renderMeritList(list) {
  $('#meritList').innerHTML = list ? `<div class="card-panel"><h4>Latest released merit list</h4><p class="muted">Published ${new Date(list.published_at).toLocaleString()} by ${list.released_by}</p><ol>${list.entries.map(entry => `<li class="mb-2"><b>${entry.student_name}</b> — ${entry.course_name} (${entry.student_percentage || '—'}%)<br><small>${entry.application_number}</small></li>`).join('')}</ol></div>` : '<p class="muted">No merit list has been released yet.</p>';
}

const ADMIN_PAGE_LINKS = [
  ['overview', 'Overview', 'admin.html'],
  ['faculty', 'Faculty approvals', 'admin-faculty.html'],
  ['courses', 'Courses & colleges', 'admin-courses.html'],
  ['applications', 'Student applications', 'admin-applications.html'],
  ['documents', 'Student documents', 'admin-documents.html']
];

function ensureAdminPageNavigation() {
  const navigation = $('#adminPageNavigation') || $('#adminPanelNavigation');
  if (!navigation) return;
  const active = document.body.dataset.adminPage || 'overview';
  navigation.innerHTML = ADMIN_PAGE_LINKS.map(([key, label, href]) => `<a class="btn ${key === active ? 'btn-primary' : 'btn-outline-primary'} admin-panel-btn" href="${href}">${label}</a>`).join('');
}

function ensureAdminDashboardNavigation() { ensureAdminPageNavigation(); }

function adminTableState(message, colspan) { return `<tr><td colspan="${colspan}" class="muted">${message}</td></tr>`; }

async function loadAdminDashboard() {
  if (!state.user || state.user.role !== 'admin') return;
  try {
    ensureAdminPageNavigation();
    const stats = await api('/admin/dashboard');
    if ($('#adminStats')) $('#adminStats').innerHTML = Object.entries(stats).map(([key, value]) => `<div class="col-6 col-lg-3"><div class="stat"><div class="muted small">${key.replaceAll('_', ' ').toUpperCase()}</div><b>${value}</b></div></div>`).join('');
  } catch (error) { toast(error.message, true); }
}

async function loadAdminPage() {
  if (!state.user || state.user.role !== 'admin') return;
  ensureAdminPageNavigation();
  const page = document.body.dataset.adminPage;
  try {
    if (page === 'faculty') {
      const faculty = await api('/admin/faculty');
      $('#adminFaculty').innerHTML = faculty.length ? faculty.map(f => `<tr><td>${f.name}<br><small>${f.email}</small></td><td>${f.college_name}<br><small>${f.course_name || 'Course not assigned'}</small></td><td>${f.designation}</td><td><select class="form-select form-select-sm" onchange="setFacultyApproval(${f.id}, this.value)"><option ${f.approval_status === 'PENDING' ? 'selected' : ''}>PENDING</option><option ${f.approval_status === 'APPROVED' ? 'selected' : ''}>APPROVED</option><option ${f.approval_status === 'REJECTED' ? 'selected' : ''}>REJECTED</option></select></td></tr>`).join('') : adminTableState('No faculty registrations yet.', 4);
    } else if (page === 'courses') {
      const [courseRows, colleges] = await Promise.all([api('/courses'), api('/colleges')]);
      const courses = uniqueCourseItems(courseRows);
      if ($('#adminCourses')) $('#adminCourses').innerHTML = courses.length ? courses.map(course => `<tr><td>${course.course_name}</td><td>${course.minimum_percentage}%</td><td>${money(course.fees)}</td><td>${course.duration}</td></tr>`).join('') : adminTableState('No courses available.', 4);
      if ($('#adminColleges')) $('#adminColleges').innerHTML = colleges.length ? colleges.map(college => `<tr><td>${college.college_name}</td><td>${college.location}</td><td>${college.offerings.length}</td><td>${college.offerings.map(offering => offering.course_name).join(', ')}</td></tr>`).join('') : adminTableState('No colleges available.', 4);
    } else if (page === 'applications') {
      const applications = await api('/admin/admissions?completed_only=true');
      $('#adminApplications').innerHTML = applications.length ? applications.map(a => `<tr><td>${a.application_number}</td><td>${a.student_name}<br><small>${a.student_email}</small></td><td>${a.course_name}<br><small>${a.college_name}</small></td><td>${a.payment?.payment_status || 'PENDING'}</td><td><span class="badge-status">${a.status}</span></td></tr>`).join('') : adminTableState('No completed admissions yet. Student names appear after successful payment and approval.', 5);
    } else if (page === 'documents') {
      const documents = await api('/admin/documents');
      $('#adminDocumentsTable').innerHTML = documents.length ? documents.map(document => `<tr><td>${document.student_name}<br><small>${document.student_email}</small></td><td>${document.document_type}<br><small>${document.original_filename}</small></td><td>${new Date(document.uploaded_at).toLocaleString()}</td><td><select class="form-select form-select-sm" onchange="reviewDocument(${document.id}, this.value)"><option ${document.verification_status === 'PENDING' ? 'selected' : ''}>PENDING</option><option ${document.verification_status === 'VERIFIED' ? 'selected' : ''}>VERIFIED</option><option ${document.verification_status === 'REJECTED' ? 'selected' : ''}>REJECTED</option></select></td></tr>`).join('') : adminTableState('No student documents uploaded yet.', 4);
    }
  } catch (error) { toast(error.message, true); }
}

function showAdminPanel(panelName) { window.location.assign(ADMIN_PAGE_LINKS.find(item => item[0] === panelName)?.[2] || 'admin.html'); }

async function addAdminCourse(event) {
  event.preventDefault();
  try {
    const data = formObject(event.target);
    data.minimum_percentage = Number(data.minimum_percentage); data.fees = Number(data.fees);
    await api('/admin/courses', { method: 'POST', body: JSON.stringify(data) });
    event.target.reset(); toast('Course added successfully'); loadAdminPage();
  } catch (error) { toast(error.message, true); }
}

async function setFacultyApproval(id, approval_status) {
  try { await api(`/admin/faculty/${id}/approval`, { method: 'PATCH', body: JSON.stringify({ approval_status }) }); toast('Faculty approval updated'); loadAdminPage(); }
  catch (error) { toast(error.message, true); }
}

async function setAdmissionStatus(id, status) {
  try { await api(`/admin/admissions/${id}`, { method: 'PATCH', body: JSON.stringify({ status }) }); toast('Application status updated'); loadAdminPage(); }
  catch (error) { toast(error.message, true); }
}

async function reviewDocument(id, verification_status) {
  try { await api(`/admin/documents/${id}`, { method: 'PATCH', body: JSON.stringify({ verification_status }) }); toast('Document verification updated'); loadAdminPage(); }
  catch (error) { toast(error.message, true); }
}

function bindSubmit(selector, handler) { const element = $(selector); if (element) element.onsubmit = handler; }

async function loadStudentDocuments() {
  if (!state.user || state.user.role !== 'student' || !$('#studentDocuments')) return;
  try {
    const records = await api('/student/documents');
    $('#studentDocuments').innerHTML = records.length ? records.map(record => `<div class="college-item"><b>${record.document_type}</b><span class="badge-status ms-2">${record.verification_status}</span><p class="small muted mb-0">${record.original_filename}</p>${record.verification_note ? `<p class="small mb-0">${record.verification_note}</p>` : ''}</div>`).join('') : '<p class="muted small">No documents uploaded yet.</p>';
  } catch (error) { $('#studentDocuments').innerHTML = `<p class="form-message">${error.message}</p>`; }
}

function setupDocumentUpload() {
  const applicationSection = $('#applications');
  if (!applicationSection || $('#documentUploadForm')) return;
  const panel = document.createElement('div');
  panel.className = 'card-panel mt-4';
  panel.innerHTML = '<h4>Required documents</h4><p class="muted small">Upload your marks card, ID proof, or certificate as PDF or image (maximum 10 MB).</p><form id="documentUploadForm" class="row g-2"><div class="col-md-4"><label>Document type</label><select class="form-select" name="document_type" required><option value="Marks card">Marks card</option><option value="ID proof">ID proof</option><option value="Degree certificate">Degree certificate</option><option value="Passport photo">Passport photo</option></select></div><div class="col-md-5"><label>File</label><input class="form-control" type="file" name="file" accept=".pdf,.png,.jpg,.jpeg,.webp" required></div><div class="col-md-3 d-flex align-items-end"><button class="btn btn-primary w-100">Upload document</button></div><p id="documentMessage" class="form-message"></p></form><div id="studentDocuments" class="mt-3"></div>';
  const listHeading = applicationSection.querySelector('#applicationList')?.parentElement;
  if (listHeading) listHeading.before(panel); else applicationSection.append(panel);
  panel.querySelector('#documentUploadForm').addEventListener('submit', async event => {
    event.preventDefault();
    try {
      await api('/student/documents', { method: 'POST', body: new FormData(event.target) });
      event.target.reset();
      setMessage('documentMessage', 'Document uploaded for administrator verification.');
      loadStudentDocuments();
    } catch (error) { setMessage('documentMessage', error.message, true); }
  });
}

function setupEligibilityAnalyzer() {
  const admissionForm = $('#admissionForm');
  if (!admissionForm || $('#eligibilityAnalyzer')) return;
  const analyzer = document.createElement('section');
  analyzer.id = 'eligibilityAnalyzer';
  analyzer.className = 'card-panel mb-4';
  analyzer.innerHTML = '<div class="section-title"><div><p class="eyebrow">ELIGIBILITY ANALYZER</p><h3>Find courses that match your profile</h3><p class="muted">Enter your qualification, percentage and interests. We will show only courses for which you are eligible.</p></div></div><form id="eligibilityAnalyzerForm" class="row g-3"><div class="col-md-4"><label>Qualification</label><input class="form-control" name="qualification" placeholder="e.g. BCA or B.Sc" required></div><div class="col-md-3"><label>Percentage</label><input class="form-control" type="number" name="percentage" min="0" max="100" step="0.1" placeholder="e.g. 72" required></div><div class="col-md-5"><label>Interests</label><input class="form-control" name="interests" placeholder="e.g. AI, data science" required></div><div class="col-12"><button class="btn btn-primary">Analyze eligible courses</button><span id="eligibilityMessage" class="form-message ms-2"></span></div></form><div id="eligibleCourses" class="row g-3 mt-2"></div>';
  admissionForm.before(analyzer);
  const courseSelect = $('#courseSelect');
  const collegeSelect = $('#collegeSelect');
  [courseSelect, collegeSelect].forEach(select => {
    if (!select) return;
    select.classList.add('d-none');
    if (select.previousElementSibling?.tagName === 'LABEL') select.previousElementSibling.classList.add('d-none');
  });
  const selectedSummary = document.createElement('p');
  selectedSummary.id = 'selectedCourseSummary';
  selectedSummary.className = 'small muted mb-0';
  admissionForm.insertBefore(selectedSummary, admissionForm.firstChild);
  admissionForm.classList.add('d-none');
  $('#eligibilityAnalyzerForm').addEventListener('submit', async event => {
    event.preventDefault();
    try {
      const data = formObject(event.target);
      data.percentage = Number(data.percentage);
      await api('/student/profile', { method: 'PUT', body: JSON.stringify(data) });
      const result = await api('/recommendations');
      const courses = uniqueCourseItems(result.courses);
      $('#eligibleCourses').innerHTML = courses.length ? courses.map(course => `<div class="col-lg-6"><article class="recommend-card h-100"><div class="score">${course.match_score}% MATCH</div><h4>${course.course_name}</h4><p>${course.reason}</p><div class="small mb-2"><b>Duration:</b> ${course.duration} &nbsp; <b>Fees:</b> ${money(course.fees)}</div><div class="small mb-3"><b>Minimum qualification:</b> ${course.eligibility.minimum_qualification}<br><b>Minimum percentage:</b> ${course.eligibility.minimum_percentage}%</div><button class="btn btn-primary" type="button" onclick="chooseEligibleCourse(${course.course_id})">Apply for this course</button></article></div>`).join('') : `<div class="col-12"><p class="text-danger">${result.message || 'Course is not available for this interest. Please check with another interest.'}</p></div>`;
      setMessage('eligibilityMessage', result.message || (courses.length ? `${courses.length} matching course option(s) found.` : 'Course is not available for this interest. Please check with another interest.'), !courses.length);
    } catch (error) { setMessage('eligibilityMessage', error.message, true); }
  });
}

async function chooseEligibleCourse(courseId) {
  try {
    await loadCatalogue();
    const course = state.courses.find(item => item.id === Number(courseId));
    const college = state.colleges.find(item => item.offerings.some(offering => offering.course_id === Number(courseId)));
    if (!course || !college) throw new Error('This course is not currently offered by Bangalore University.');
    $('#courseSelect').value = course.id;
    $('#courseSelect').dispatchEvent(new Event('change'));
    $('#collegeSelect').value = college.id;
    $('#selectedCourseSummary').textContent = `Selected course: ${course.course_name} at ${college.college_name}. Complete the address and previous-institution fields below.`;
    $('#admissionForm').classList.remove('d-none');
    $('#admissionForm').scrollIntoView({ behavior: 'smooth', block: 'start' });
  } catch (error) { toast(error.message, true); }
}

let notificationCache = [];
async function loadNotifications() {
  if (!state.user) return;
  try {
    notificationCache = await api('/notifications');
    const links = $('#navLinks');
    if (links && !links.querySelector('.notifications-link')) links.insertAdjacentHTML('afterbegin', `<a class="nav-link notifications-link" href="#" onclick="showNotifications(); return false;">Notifications <span class="badge bg-warning text-dark">${notificationCache.filter(item => !item.is_read).length}</span></a>`);
  } catch (_) { notificationCache = []; }
}

function showNotifications() {
  if (!notificationCache.length) return toast('No notifications yet.');
  const unread = notificationCache.filter(item => !item.is_read);
  toast(unread.length ? unread.map(item => `${item.title}: ${item.message}`).join(' | ') : 'No new notifications.');
  unread.forEach(item => api(`/notifications/${item.id}/read`, { method: 'PATCH' }).catch(() => {}));
}

bindSubmit('#studentLogin', async event => {
  event.preventDefault();
  try { const result = await api('/auth/login', { method: 'POST', body: JSON.stringify(formObject(event.target)) }); saveToken(result); window.location.assign('student.html'); }
  catch (error) { setMessage('studentAuthMessage', error.message, true); }
});

bindSubmit('#studentRegister', async event => {
  event.preventDefault();
  try { const result = await api('/auth/register', { method: 'POST', body: JSON.stringify(formObject(event.target)) }); setMessage('studentAuthMessage', `${result.message} You can now log in.`); event.target.reset(); toggleTab('student', 'login'); }
  catch (error) { setMessage('studentAuthMessage', error.message, true); }
});

bindSubmit('#facultyLogin', async event => {
  event.preventDefault();
  try { const result = await api('/auth/login', { method: 'POST', body: JSON.stringify(formObject(event.target)) }); saveToken(result); window.location.href = 'college.html'; }
  catch (error) { setMessage('facultyAuthMessage', error.message, true); }
});

bindSubmit('#facultyRegister', async event => {
  event.preventDefault();
  try { const result = await api('/faculty/register', { method: 'POST', body: JSON.stringify({ ...formObject(event.target), college_id: Number(event.target.college_id.value), course_id: Number(event.target.course_id.value) }) }); setMessage('facultyAuthMessage', result.message); event.target.reset(); toggleTab('faculty', 'login'); }
  catch (error) { setMessage('facultyAuthMessage', error.message, true); }
});

bindSubmit('#adminLogin', async event => {
  event.preventDefault();
  try { const result = await api('/auth/login', { method: 'POST', body: JSON.stringify(formObject(event.target)) }); saveToken(result); window.location.href = 'admin.html'; }
  catch (error) { setMessage('adminAuthMessage', error.message, true); }
});

bindSubmit('#profileForm', async event => {
  event.preventDefault();
  try { const data = formObject(event.target); data.percentage = data.percentage ? Number(data.percentage) : null; data.budget = data.budget ? Number(data.budget) : null; await api('/student/profile', { method: 'PUT', body: JSON.stringify(data) }); await refreshUser(); setMessage('profileMessage', 'Profile saved.'); }
  catch (error) { setMessage('profileMessage', error.message, true); }
});

bindSubmit('#chatForm', async event => {
  event.preventDefault(); const input = $('#chatInput'); const message = input.value.trim(); if (!message) return; addMessage(message, 'student'); input.value = '';
  try { const result = await api('/ai/chat', { method: 'POST', body: JSON.stringify({ message }) }); addMessage(result.reply, 'agent'); recommendationCards(result); await refreshUser(); }
  catch (error) { addMessage(error.message, 'agent'); }
});

bindSubmit('#admissionForm', async event => {
  event.preventDefault();
  try { const data = formObject(event.target); data.course_id = Number($('#courseSelect').value); data.college_id = Number($('#collegeSelect').value); const result = await api('/admissions', { method: 'POST', body: JSON.stringify(data) }); state.selectedAdmission = result.id; $('#paymentButton').disabled = false; $('#paymentButton').onclick = () => pay(result.id); setMessage('admissionMessage', `Application ${result.application_number} created. Complete the demo payment.`); loadApplications(); }
  catch (error) { setMessage('admissionMessage', error.message, true); }
});

bindSubmit('#adminCourseForm', addAdminCourse);

async function loadStudentStatus() {
  try {
    const records = await api('/student/selection-status');
    $('#statusList').innerHTML = records.length ? records.map(record => `<article class="college-item"><b>${record.application_number}</b><br>${record.course_name} at ${record.college_name}<br><span class="badge-status">${record.selection_status}</span>${record.merit_rank ? ` <span class="badge-status">Merit rank: ${record.merit_rank}</span>` : ''}<p class="small muted mt-2 mb-2">${record.selection_message}</p><div class="small"><b>Application timeline</b>${(record.timeline || []).map(step => `<div class="mt-1"><span class="badge-status">${step.status}</span> ${step.note}</div>`).join('')}</div></article>`).join('') : '<p class="muted">No applications found.</p>';
  } catch (error) { toast(error.message, true); }
}

applyUniversityBranding();
removeAdmitAIBranding();
setupPasswordToggles();
setupHome();
setupDocumentUpload();
setupEligibilityAnalyzer();
const initialPage = window.location.hash.slice(1);
if ($('#facultyCollege')) loadCollegeOptions();
refreshUser().then(() => {
  loadNotifications();
  if (document.body.dataset.adminPage && state.user?.role === 'admin') loadAdminPage();
  if (initialPage && $(`#${initialPage}`)) show(initialPage);
  if ($('#applications') && !$('#landing') && state.user?.role === 'student') show('applications');
  if ($('#statusList') && state.user?.role === 'student') loadStudentStatus();
});
