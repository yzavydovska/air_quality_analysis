let currentPage = 1;
const rowsPerPage = 10;
let currentData = [];
let miasta = [];

function pobierzDane() {
  const miasto = document.getElementById('miastaSelect').value;
  const miesiac = document.getElementById('miesiacSelect').value;

  fetch(`http://127.0.0.1:5000/api/dane?miasto=${encodeURIComponent(miasto)}&miesiac=${encodeURIComponent(miesiac)}`)
    .then(res => res.json())
    .then(data => {
      currentData = data.map(row => ({ miasto, ...row }));
      currentPage = 1;
      pokazStrone(currentPage);
      document.getElementById('buttonContainer').style.display = 'block';
      generujWykres(currentData);
    })
    .catch(() => alert('❌ Błąd pobierania danych.'));
}

function pokazStrone(page) {
  const start = (page - 1) * rowsPerPage;
  const end = start + rowsPerPage;
  renderTable(currentData.slice(start, end));
}

function zmienStrone(delta) {
  const totalPages = Math.ceil(currentData.length / rowsPerPage);
  currentPage = Math.min(Math.max(1, currentPage + delta), totalPages);
  pokazStrone(currentPage);
}

function renderTable(data) {
  const container = document.getElementById('tabelaContainer');
  if (!data.length) {
    container.innerHTML = '<p>Brak danych do wyświetlenia.</p>';
    return;
  }

  const keys = Object.keys(data[0]);
  let html = '<table><thead><tr>' +
    keys.map(k => `<th>${k.toUpperCase()}</th>`).join('') +
    '</tr></thead><tbody>';

  data.forEach(row => {
    const pm25Class = getPmClass(row.pm25);
    const pm10Class = getPmClass(row.pm10);

    html += '<tr>' +
      keys.map(k => {
        let val = row[k];
        let klas = '';
        if (k === 'pm25') klas = pm25Class;
        if (k === 'pm10') klas = pm10Class;
        return `<td class="${klas}">${val}</td>`;
      }).join('') +
      '</tr>';
  });

  html += '</tbody></table>';

  const totalPages = Math.ceil(currentData.length / rowsPerPage);
  html += `
    <div style="margin-top:10px;">
      <button ${currentPage === 1 ? 'disabled' : ''} onclick="zmienStrone(-1)">Poprzednia</button>
      Strona ${currentPage} z ${totalPages}
      <button ${currentPage === totalPages ? 'disabled' : ''} onclick="zmienStrone(1)">Następna</button>
    </div>`;

  container.innerHTML = html;
}

function getPmClass(value) {
  if (value === null || value === undefined) return '';
  if (value < 25) return 'low';
  if (value < 50) return 'medium';
  return 'high';
}

function konwertujNaCSV(data) {
  if (!data.length) return '';
  const keys = Object.keys(data[0]);
  return [
    keys.join(','),
    ...data.map(row => keys.map(k => `"${row[k]}"`).join(','))
  ].join('\n');
}

function pobierzPlik(content, filename) {
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
}

function pobierzCSVWidocznych() {
  const start = (currentPage - 1) * rowsPerPage;
  const end = start + rowsPerPage;
  const daneStrony = currentData.slice(start, end);
  const csv = konwertujNaCSV(daneStrony);
  pobierzPlik(csv, 'dane_strona.csv');
}

function pobierzCSVWszystkich() {
  const miasto = document.getElementById('miastaSelect').value;
  const miesiac = document.getElementById('miesiacSelect').value;

  fetch(`http://127.0.0.1:5000/api/dane?miasto=${encodeURIComponent(miasto)}&miesiac=${encodeURIComponent(miesiac)}&all=true`)
    .then(res => res.json())
    .then(data => {
      const allData = data.map(row => ({ miasto, ...row }));
      const csv = konwertujNaCSV(allData);
      pobierzPlik(csv, `dane_wszystkie_${miasto}.csv`);
    })
    .catch(() => alert('❌ Błąd pobierania wszystkich danych.'));
}

function generujWykres(dane) {
  const labels = dane.map(r => r.data);
  const pm25 = dane.map(r => r.pm25);
  const pm10 = dane.map(r => r.pm10);

  const ctx = document.getElementById('wykresCanvas').getContext('2d');
  if (window.wykresInstance) window.wykresInstance.destroy();

  window.wykresInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'PM2.5 (μg/m³)',
          data: pm25,
          borderColor: '#3498db',
          backgroundColor: 'rgba(52,152,219,0.2)',
          pointRadius: 3,
          pointHoverRadius: 6,
          tension: 0.3,
        },
        {
          label: 'PM10 (μg/m³)',
          data: pm10,
          borderColor: '#e74c3c',
          backgroundColor: 'rgba(231,76,60,0.2)',
          pointRadius: 3,
          pointHoverRadius: 6,
          tension: 0.3,
        }
      ]
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: 'Wykres stężenia pyłów PM2.5 i PM10 w czasie',
          font: {
            size: 18,
            family: 'Arial',
            weight: 'bold'
          },
          padding: {
            top: 10,
            bottom: 20
          }
        },
        legend: {
          position: 'top',
          labels: {
            font: {
              size: 14
            }
          }
        },
        tooltip: {
          mode: 'index',
          intersect: false,
          callbacks: {
            label: ctx => `${ctx.dataset.label}: ${ctx.parsed.y} μg/m³`
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Stężenie (μg/m³)'
          }
        },
        x: {
          title: {
            display: true,
            text: 'Data'
          }
        }
      },
      hover: {
        mode: 'nearest',
        intersect: true
      }
    }
  });
}

function pobierzMiasta() {
  fetch('http://127.0.0.1:5000/api/miasta')
    .then(res => res.json())
    .then(data => {
      miasta = data;
      const select = document.getElementById('miastaSelect');
      const prognozaSelect = document.getElementById('miastoPrognozaSelect');
      select.innerHTML = '';
      prognozaSelect.innerHTML = '';
      miasta.forEach(m => {
        select.innerHTML += `<option value="${m}">${m}</option>`;
        prognozaSelect.innerHTML += `<option value="${m}">${m}</option>`;
      });
      if (miasta.length) {
        select.value = miasta[0];
        prognozaSelect.value = miasta[0];
        pobierzDane();
        pobierzPrognoze();
      }
    })
    .catch(() => alert('❌ Błąd pobierania listy miast.'));
}

function pokazPrognoze(dane) {
  if (dane.error) {
    document.getElementById('wynikPrognozy').classList.add('error');
    document.getElementById('wynikPrognozy').textContent = dane.error;
    return;
  }
  document.getElementById('wynikPrognozy').classList.remove('error');

  const dateObj = new Date(dane.data);
  const options = { year: 'numeric', month: 'long', day: 'numeric' };
  const dataFormatted = dateObj.toLocaleDateString('pl-PL', options);

  function ocenaPM(pm) {
    if (pm <= 12) return `${pm} μg/m³ (dobry poziom)`;
    if (pm <= 35) return `${pm} μg/m³ (umiarkowany poziom)`;
    if (pm <= 55) return `${pm} μg/m³ (niezdrowy dla wrażliwych)`;
    return `${pm} μg/m³ (niezdrowy poziom)`;
  }

  // Zamiana "bydgoszcz" na "Bydgoszcz" itd.
  const miastoFormatted = dane.miasto
    .split('-')
    .map(s => s.charAt(0).toUpperCase() + s.slice(1))
    .join(' ');

  const tekst =
    `Prognoza jakości powietrza dla miasta ${miastoFormatted} na dzień ${dataFormatted}:\n\n` +
    `• PM2.5: ${ocenaPM(dane.prognoza_pm25)}\n` +
    `• PM10: ${ocenaPM(dane.prognoza_pm10)}`;

  document.getElementById('wynikPrognozy').textContent = tekst;
}

function pobierzPrognoze() {
  const miasto = document.getElementById('miastoPrognozaSelect').value;
  const dzien = document.getElementById('dzienPrognozaSelect').value || 'today';
  const kontener = document.getElementById('wynikPrognozy');

  if (!miasto) {
    kontener.textContent = 'Proszę wybrać miasto.';
    kontener.classList.add('error');
    return;
  }

  kontener.textContent = 'Ładowanie prognozy...';
  kontener.classList.remove('error');

  fetch(`http://127.0.0.1:5000/api/prognoza?miasto=${encodeURIComponent(miasto)}&dzien=${dzien}`)
    .then(res => res.json())
    .then(dane => {
      pokazPrognoze(dane);
    })
    .catch(() => {
      kontener.textContent = 'Błąd podczas pobierania prognozy.';
      kontener.classList.add('error');
    });
}



// Inicjalizacja po załadowaniu strony
window.onload = () => {
  pobierzMiasta();

  document.getElementById('miastaSelect').addEventListener('change', () => {
    pobierzDane();
  });

  document.getElementById('miastoPrognozaSelect').addEventListener('change', () => {
    pobierzPrognoze();
  });
};
