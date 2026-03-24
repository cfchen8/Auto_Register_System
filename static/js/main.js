/**
 * 國小課後社團自動報名系統 - 前端邏輯
 * 對接：廍子國小 BeClass 報名系統
 */

// ===== 全域狀態 =====
let currentRegistrationId = null;
let countdownInterval      = null;
let statusPollInterval     = null;

// ===== DOM 取得 =====
const $ = id => document.getElementById(id);

const form            = $('registerForm');
const formSection     = $('formSection');
const countdownSection = $('countdownSection');
const submitBtn       = $('submitBtn');
const loadingOverlay  = $('loadingOverlay');
const toast           = $('toast');

// ===== 工具函式 =====

/**
 * 顯示 Toast 通知
 * @param {string} msg     訊息文字
 * @param {'info'|'success'|'error'|'warning'} type 類型
 */
function showToast(msg, type = 'info') {
  const icons = { info: 'ℹ️', success: '✅', error: '❌', warning: '⚠️' };
  $('toastIcon').textContent = icons[type] || 'ℹ️';
  $('toastMsg').textContent  = msg;

  toast.className = `toast ${type}`;
  toast.classList.remove('hidden');

  setTimeout(() => toast.classList.add('hidden'), 3500);
}

function showLoading()  { loadingOverlay.classList.remove('hidden'); }
function hideLoading()  { loadingOverlay.classList.add('hidden'); }

/** 補零（用於倒數計時） */
function pad(n) { return String(n).padStart(2, '0'); }

/** 清除倒數計時 & 輪詢 */
function clearTimers() {
  if (countdownInterval)  { clearInterval(countdownInterval);  countdownInterval = null; }
  if (statusPollInterval) { clearInterval(statusPollInterval); statusPollInterval = null; }
}

// ===== 表單驗證 =====

/** 清除所有錯誤訊息 */
function clearErrors() {
  document.querySelectorAll('.error-msg').forEach(el => el.textContent = '');
  document.querySelectorAll('.error').forEach(el => el.classList.remove('error'));
}

/** 設定單一欄位錯誤 */
function setError(fieldId, msg) {
  const errEl = $(`err_${fieldId}`);
  if (errEl) errEl.textContent = msg;
  const input = $(fieldId) || document.querySelector(`[name="${fieldId}"]`);
  if (input) input.classList.add('error');
}

/** 驗證整份表單，回傳 true 表示通過 */
function validateForm() {
  clearErrors();
  let valid = true;

  // 姓名
  const name = $('student_name').value.trim();
  if (!name) { setError('student_name', '請輸入小朋友姓名'); valid = false; }

  // 身分證
  const idNum = $('id_number').value.trim().toUpperCase();
  if (!idNum) {
    setError('id_number', '請輸入身分證字號'); valid = false;
  } else if (!/^[A-Z][12]\d{8}$/.test(idNum)) {
    setError('id_number', '身分證格式錯誤，如：A123456789'); valid = false;
  }

  // 性別
  if (!document.querySelector('[name="gender"]:checked')) {
    setError('gender', '請選擇性別'); valid = false;
  }

  // 班級座號（5碼：年1碼+班2碼+座2碼，如 10101）
  const classSeat = $('class_seat').value.trim();
  if (!classSeat) {
    setError('class_seat', '請輸入班級座號'); valid = false;
  } else if (!/^[1-6]\d{4}$/.test(classSeat)) {
    setError('class_seat', '格式錯誤，需為5碼數字（如：10101 = 一年一班1號）'); valid = false;
  }

  // Email
  const email = $('parent_email').value.trim();
  if (!email) {
    setError('parent_email', '請輸入家長 Email'); valid = false;
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    setError('parent_email', 'Email 格式不正確'); valid = false;
  }

  // 手機
  const phone = $('phone').value.trim();
  if (!phone) {
    setError('phone', '請輸入行動電話'); valid = false;
  } else if (!/^09\d{8}$/.test(phone)) {
    setError('phone', '手機需為 09 開頭的 10 碼數字'); valid = false;
  }

  // 社團（1~2個）
  const checkedClubs = document.querySelectorAll('[name="club_indexes"]:checked');
  if (checkedClubs.length === 0) {
    setError('club_indexes', '請至少選擇一個社團'); valid = false;
  } else if (checkedClubs.length > 2) {
    setError('club_indexes', '最多只能選擇 2 個社團'); valid = false;
  }

  // 報名時間
  const timeVal = $('register_time').value;
  if (!timeVal) {
    setError('register_time', '請設定報名開放時間'); valid = false;
  } else if (new Date(timeVal) <= new Date()) {
    setError('register_time', '報名時間必須是未來的時間'); valid = false;
  }

  return valid;
}

// ===== 收集表單資料 =====
function collectFormData() {
  const genderEl      = document.querySelector('[name="gender"]:checked');
  const checkedClubs  = document.querySelectorAll('[name="club_indexes"]:checked');
  const clubIndexes   = Array.from(checkedClubs).map(cb => parseInt(cb.value, 10));

  return {
    student_name:  $('student_name').value.trim(),
    id_number:     $('id_number').value.trim().toUpperCase(),
    gender:        genderEl ? genderEl.value : '',
    parent_email:  $('parent_email').value.trim(),
    phone:         $('phone').value.trim(),
    class_seat:    $('class_seat').value.trim(),
    club_indexes:  clubIndexes,
    register_time: $('register_time').value,
  };
}

// ===== 送出報名 =====
async function submitRegistration(data) {
  showLoading();
  submitBtn.disabled = true;

  try {
    const res  = await fetch('/api/register', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(data),
    });
    const json = await res.json();

    if (json.success) {
      currentRegistrationId = json.registration_id;
      targetTime = new Date(data.register_time);
      showCountdownSection(data, json);
      showToast('報名資料已儲存！系統將自動報名 🎉', 'success');
    } else {
      showToast(json.message || '送出失敗，請稍後再試', 'error');
    }
  } catch (err) {
    showToast('網路錯誤，請確認伺服器是否運行中', 'error');
    console.error(err);
  } finally {
    hideLoading();
    submitBtn.disabled = false;
  }
}

// ===== 顯示倒數計時區 =====
function showCountdownSection(formData, apiRes) {
  const gender = formData.gender === 'male' ? '男' : '女';

  // 將 10101 → 一年一班1號
  function formatClassSeat(cs) {
    const gradeMap = ['', '一', '二', '三', '四', '五', '六'];
    const g = parseInt(cs[0], 10);
    const c = parseInt(cs.slice(1, 3), 10);
    const s = parseInt(cs.slice(3, 5), 10);
    return `${gradeMap[g] || g}年${c}班${s}號`;
  }
  const classSeatDisplay = formatClassSeat(formData.class_seat);

  $('regSummary').innerHTML = `
    <p>👦 <strong>學生姓名：</strong>${formData.student_name}（${gender}）</p>
    <p>🏫 <strong>班級座號：</strong>${classSeatDisplay}（代碼：${formData.class_seat}）</p>
    <p>🎯 <strong>報名社團：</strong>${apiRes.club_name}</p>
    <p>📧 <strong>家長信箱：</strong>${formData.parent_email}</p>
    <p>📱 <strong>行動電話：</strong>${formData.phone}</p>
    <p>⏰ <strong>預定報名時間：</strong>${apiRes.scheduled_time}</p>
  `;

  $('regIdDisplay').textContent    = apiRes.registration_id;
  $('countdownTarget').textContent = `預定時間：${apiRes.scheduled_time}`;

  formSection.classList.add('hidden');
  countdownSection.classList.remove('hidden');

  startCountdown(new Date(formData.register_time));
  startStatusPolling(apiRes.registration_id);
}

// ===== 倒數計時 =====
function startCountdown(target) {
  clearTimers();

  function tick() {
    const diff = target - new Date();
    if (diff <= 0) {
      $('cdDays').textContent    = '00';
      $('cdHours').textContent   = '00';
      $('cdMinutes').textContent = '00';
      $('cdSeconds').textContent = '00';
      clearInterval(countdownInterval);
      countdownInterval = null;
      showToast('時間到！系統正在自動報名...', 'info');
      return;
    }
    const days    = Math.floor(diff / 86400000);
    const hours   = Math.floor((diff % 86400000) / 3600000);
    const minutes = Math.floor((diff % 3600000) / 60000);
    const seconds = Math.floor((diff % 60000) / 1000);

    $('cdDays').textContent    = pad(days);
    $('cdHours').textContent   = pad(hours);
    $('cdMinutes').textContent = pad(minutes);
    $('cdSeconds').textContent = pad(seconds);
  }

  tick();
  countdownInterval = setInterval(tick, 1000);
}

// ===== 定期查詢狀態 =====
function startStatusPolling(regId) {
  clearInterval(statusPollInterval);
  statusPollInterval = setInterval(() => queryStatus(regId, false), 10000);
}

// ===== 查詢報名狀態 =====
async function queryStatus(regId, showResult = true) {
  try {
    const res  = await fetch(`/api/status/${regId}`);
    const json = await res.json();

    if (!json.success) {
      if (showResult) showToast(json.message || '查詢失敗', 'error');
      return;
    }

    updateStatusBadge(json.status, json.result_message);

    if (showResult) {
      $('queryResult').innerHTML = buildStatusHTML(json);
      $('queryResult').classList.remove('hidden');
    }

    // 若已完成（成功/失敗/取消），停止輪詢
    if (['success', 'failed', 'cancelled'].includes(json.status)) {
      clearTimers();
      if (json.status === 'success') showToast('🎉 自動報名成功！', 'success');
      if (json.status === 'failed')  showToast('❌ 自動報名失敗，請確認後重新嘗試', 'error');
    }

    return json;
  } catch (err) {
    if (showResult) showToast('網路錯誤', 'error');
    console.error(err);
  }
}

/** 建立狀態資訊 HTML */
function buildStatusHTML(data) {
  const statusMap = {
    pending:   { label: '等待中', icon: '⏳', cls: 'pending' },
    success:   { label: '報名成功', icon: '✅', cls: 'success' },
    failed:    { label: '報名失敗', icon: '❌', cls: 'failed' },
    cancelled: { label: '已取消', icon: '🚫', cls: 'cancelled' },
  };
  const s = statusMap[data.status] || { label: data.status, icon: 'ℹ️', cls: '' };
  const execAt = data.executed_at
    ? `<p><strong>執行時間：</strong>${new Date(data.executed_at).toLocaleString('zh-TW')}</p>` : '';
  const resultMsg = data.result_message
    ? `<p><strong>結果說明：</strong>${data.result_message}</p>` : '';

  return `
    <p><strong>報名編號：</strong>${data.id}</p>
    <p><strong>學生姓名：</strong>${data.student_name}</p>
    <p><strong>報名社團：</strong>${data.club_name}</p>
    <p><strong>預定時間：</strong>${new Date(data.register_time).toLocaleString('zh-TW')}</p>
    <p><strong>目前狀態：</strong>
      <span class="status-badge ${s.cls}" style="display:inline-flex;padding:2px 12px;font-size:.8rem;">
        ${s.icon} ${s.label}
      </span>
    </p>
    ${execAt}
    ${resultMsg}
  `;
}

/** 更新倒數區的狀態徽章 */
function updateStatusBadge(status, message = '') {
  const statusBadge = $('statusBadge');
  const statusText  = $('statusText');
  if (!statusBadge) return;

  statusBadge.className = `status-badge ${status}`;

  const msgs = {
    pending:   { icon: '⏳', text: '等待中，系統將於預定時間自動報名...' },
    success:   { icon: '✅', text: '自動報名成功！' },
    failed:    { icon: '❌', text: `報名失敗：${message || '請確認後重試'}` },
    cancelled: { icon: '🚫', text: '報名已取消' },
  };
  const m = msgs[status] || { icon: 'ℹ️', text: status };
  statusBadge.querySelector('.status-icon').textContent = m.icon;
  statusText.textContent = m.text;
}

// ===== 取消排程報名 =====
async function cancelRegistration() {
  if (!currentRegistrationId) return;
  if (!confirm(`確定要取消報名編號 ${currentRegistrationId} 的自動報名排程嗎？`)) return;

  showLoading();
  try {
    const res  = await fetch(`/api/cancel/${currentRegistrationId}`, { method: 'DELETE' });
    const json = await res.json();
    if (json.success) {
      clearTimers();
      updateStatusBadge('cancelled');
      showToast('已成功取消報名排程', 'info');
    } else {
      showToast(json.message || '取消失敗', 'error');
    }
  } catch (err) {
    showToast('網路錯誤', 'error');
  } finally {
    hideLoading();
  }
}

// ===== 事件綁定 =====

// 表單送出
form.addEventListener('submit', async e => {
  e.preventDefault();
  if (!validateForm()) {
    showToast('請修正表單中的錯誤', 'warning');
    // 捲動到第一個錯誤
    const firstErr = document.querySelector('.error');
    if (firstErr) firstErr.scrollIntoView({ behavior: 'smooth', block: 'center' });
    return;
  }
  await submitRegistration(collectFormData());
});

// 取消報名
$('cancelBtn').addEventListener('click', cancelRegistration);

// 查詢最新狀態
$('checkStatusBtn').addEventListener('click', () => {
  if (currentRegistrationId) queryStatus(currentRegistrationId, true);
});

// 新增報名
$('newRegBtn').addEventListener('click', () => {
  clearTimers();
  currentRegistrationId = null;
  form.reset();
  clearErrors();
  countdownSection.classList.add('hidden');
  formSection.classList.remove('hidden');
  window.scrollTo({ top: 0, behavior: 'smooth' });
});

// 獨立查詢按鈕
$('queryBtn').addEventListener('click', async () => {
  const id = $('queryId').value.trim().toUpperCase();
  if (!id) { showToast('請輸入報名編號', 'warning'); return; }
  showLoading();
  await queryStatus(id, true);
  hideLoading();
});

$('queryId').addEventListener('keydown', e => {
  if (e.key === 'Enter') $('queryBtn').click();
});

// ===== 社團選擇即時回饋（最多2個） =====
document.querySelectorAll('[name="club_indexes"]').forEach(cb => {
  cb.addEventListener('change', () => {
    const checked = document.querySelectorAll('[name="club_indexes"]:checked');
    $('err_club_indexes').textContent = '';

    // 超過2個時取消本次勾選
    if (checked.length > 2) {
      cb.checked = false;
      showToast('最多只能選擇 2 個社團', 'warning');
    }

    // 若已選2個，停用其餘未選的
    const allCbs = document.querySelectorAll('[name="club_indexes"]');
    const nowChecked = document.querySelectorAll('[name="club_indexes"]:checked');
    allCbs.forEach(c => {
      const card = c.closest('.club-card');
      if (nowChecked.length >= 2 && !c.checked) {
        card && card.classList.add('disabled');
      } else {
        card && card.classList.remove('disabled');
      }
    });

    // 顯示已選清單
    const display = $('selectedClubsDisplay');
    if (nowChecked.length > 0) {
      const names = Array.from(nowChecked).map(c => {
        const label = document.querySelector(`label[for="${c.id}"] .club-name`);
        return label ? label.textContent : c.value;
      });
      $('selectedClubsText').textContent = names.join('、');
      display.style.display = 'block';
    } else {
      display.style.display = 'none';
    }
  });
});

// 設定 datetime-local 的最小值為現在
(function initDatetime() {
  const now = new Date();
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
  $('register_time').min = now.toISOString().slice(0, 16);
})();
