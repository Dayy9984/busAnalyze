

// debounce 유틸
function debounce(fn, delay) {
  let timer;
  return function(...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}

const inputEl = document.getElementById('addressInput');
const autoEl  = document.getElementById('autoComplete');
const searchBtn = document.getElementById('searchBtn');

// 자동완성 가져오기
async function fetchAutoComplete(query) {
  if (!query.trim()) {
    autoEl.innerHTML = '';
    return;
  }
  try {
    const res = await fetch(`/backend/autocomplete?address=${encodeURIComponent(query)}`);
    const list = await res.json();
    renderAutoComplete(list);
  } catch (e) {
    console.error(e);
  }
}

// 자동완성 렌더링
function renderAutoComplete(items) {
  autoEl.innerHTML = '';
  items.forEach(text => {
    const li = document.createElement('li');
    li.textContent = text;
    li.addEventListener('click', () => {
      inputEl.value = `부산광역시 ${text}`;
      autoEl.innerHTML = '';
      doSearch();
    });
    autoEl.appendChild(li);
  });
}

// 최종 검색
async function doSearch() {
  const address = inputEl.value.trim();
  try {
    const res = await fetch(`/backend/selected_coordinates?address=${encodeURIComponent(address)}`);
    if (!res.ok) {
      const err = await res.json();
      throw err;
    }
    const data = await res.json();
    // 네이버 지도에 표시 (naver_map.js 의 콜백)
    window.onAddressFound && window.onAddressFound(data);
  } catch (err) {
    alert(err.detail || '알 수 없는 오류');
  }
}

// 이벤트 바인딩
inputEl.addEventListener('input', debounce(e => {
  // '부산광역시 ' 접두어 제거
  const q = e.target.value.replace(/^부산(광역시|시)?\s*/, '');
  fetchAutoComplete(q);
}, 300));

inputEl.addEventListener('keydown', e => {
  if (e.key === 'Enter') {
    autoEl.innerHTML = '';
    doSearch();
  }
});
searchBtn.addEventListener('click', () => {
  autoEl.innerHTML = '';
  doSearch();
});
