<script setup>
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'

const activeTab = ref('Verifikasi')
const videoRef = ref(null)
const canvasRef = ref(null)
const resultData = ref(null)
const isLoading = ref(false)
const newName = ref('')
const selectedSession = ref('Praktikum AI Kelas A')
const sessionOptions = ['Praktikum AI Kelas A', 'Praktikum AI Kelas B', 'Praktikum Data Science']
const historyData = ref([])
const isApiConnected = ref(false)
const scanLine = ref(false)

const API_URL = "https://footwork-pastel-daughter.ngrok-free.dev"
const demoVideoUrl = "https://youtu.be/L0Hs5BwAf5I?si=5-i4mpVNQaay6ja_"

const fetchOptions = (method = 'GET', body = null) => {
  const options = { method, headers: { "ngrok-skip-browser-warning": "69420" } }
  if (body) options.body = body
  return options
}

const startCamera = async () => {
  try {
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true })
      if (videoRef.value) videoRef.value.srcObject = stream
    }
  } catch (err) { console.error("Kamera error: ", err) }
}

const stopCamera = () => {
  if (videoRef.value && videoRef.value.srcObject) {
    videoRef.value.srcObject.getTracks().forEach(track => track.stop())
  }
}

const fetchHistory = async () => {
  try {
    const response = await fetch(`${API_URL}/history`, fetchOptions())
    if (response.ok) {
      const json = await response.json()
      historyData.value = json.data
      isApiConnected.value = true
    } else {
      isApiConnected.value = false
    }
  } catch (error) {
    isApiConnected.value = false
    historyData.value = []
  }
}

watch(activeTab, (newTab) => {
  resultData.value = null
  if (newTab === 'Verifikasi' || newTab === 'Tambah') {
    setTimeout(() => startCamera(), 100)
  } else {
    stopCamera()
    fetchHistory()
  }
})

const captureAndVerify = () => {
  isLoading.value = true
  scanLine.value = true
  const context = canvasRef.value.getContext('2d')
  context.drawImage(videoRef.value, 0, 0, 640, 480)

  canvasRef.value.toBlob(async (blob) => {
    const formData = new FormData()
    formData.append('file', blob, 'capture.jpg')
    formData.append('session_class', selectedSession.value)

    try {
      const response = await fetch(`${API_URL}/verify`, fetchOptions('POST', formData))
      const data = await response.json()
      resultData.value = data.data
    } catch (error) { alert("Server AI Offline! Tonton video demo saja.") }
    finally {
      isLoading.value = false
      setTimeout(() => scanLine.value = false, 600)
    }
  }, 'image/jpeg')
}

const captureAndAdd = () => {
  if (!newName.value) return alert("Isi nama dulu bro!")

  isLoading.value = true
  const context = canvasRef.value.getContext('2d')
  context.drawImage(videoRef.value, 0, 0, 640, 480)

  canvasRef.value.toBlob(async (blob) => {
    const formData = new FormData()
    formData.append('file', blob, 'capture.jpg')
    formData.append('name', newName.value)

    try {
      const response = await fetch(`${API_URL}/add-visitor`, fetchOptions('POST', formData))
      const data = await response.json()
      alert(data.message)
      if (data.status === 'success') newName.value = ''
    } catch (error) { alert("Server AI Offline! Tonton video demo saja.") }
    finally { isLoading.value = false }
  }, 'image/jpeg')
}

const downloadCSV = () => {
  if (historyData.value.length === 0) return alert("Belum ada data!")
  const headers = ['ID Pengunjung', 'Nama Mahasiswa', 'Sesi/Kelas', 'Waktu Absen']
  const rows = historyData.value.map(item => [item.id, item.visitor_name, item.session, item.Timing])
  const csvContent = "data:text/csv;charset=utf-8," + headers.join(",") + "\n" + rows.map(e => e.join(",")).join("\n")
  const encodedUri = encodeURI(csvContent)
  const link = document.createElement("a")
  link.setAttribute("href", encodedUri)
  link.setAttribute("download", `Rekap_Presensi_${new Date().toISOString().split('T')[0]}.csv`)
  document.body.appendChild(link)
  link.click()
}

const resetHistory = async () => {
  if (!confirm("Yakin mau hapus SEMUA data presensi? Ini nggak bisa di-undo bro!")) return;
  try {
    const response = await fetch(`${API_URL}/reset-history`, fetchOptions('DELETE'))
    if (response.ok) {
      historyData.value = []
      alert("Boom! Data presensi berhasil dibersihkan.")
    }
  } catch (error) { alert("Server AI Offline! Tonton video demo saja.") }
}

onMounted(() => { startCamera() })
onUnmounted(() => { stopCamera() })

const totalHadir = computed(() => historyData.value.length)
</script>

<template>
  <div class="app-root">

    <!-- Subtle grid background -->
    <div class="bg-grid" aria-hidden="true"></div>

    <!-- Header -->
    <header class="app-header">
      <div class="header-inner">
        <div class="header-brand">
          <div class="brand-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
              <circle cx="12" cy="7" r="4"/>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
              <path d="M21 21v-2a4 4 0 0 0-3-3.87"/>
            </svg>
          </div>
          <div>
            <h1 class="brand-title">Presensi Fasilkom</h1>
            <p class="brand-sub">Lab AI &amp; Data Science · Edge Node</p>
          </div>
        </div>
        <div class="header-badge">
          <span class="pulse-dot"></span>
          Live System
        </div>
      </div>
    </header>

    <!-- Navigation -->
    <nav class="app-nav">
      <div class="nav-inner">
        <button
          v-for="tab in [
            { id: 'Verifikasi', icon: 'scan', label: 'Verifikasi' },
            { id: 'Riwayat',   icon: 'history', label: 'Riwayat' },
            { id: 'Tambah',    icon: 'user-plus', label: 'Tambah' }
          ]"
          :key="tab.id"
          @click="activeTab = tab.id"
          :class="['nav-btn', activeTab === tab.id ? 'nav-btn--active' : '']"
        >
          <span class="nav-icon">
            <!-- scan icon -->
            <svg v-if="tab.icon === 'scan'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/>
              <path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/>
              <line x1="7" y1="12" x2="17" y2="12"/>
            </svg>
            <!-- history icon -->
            <svg v-if="tab.icon === 'history'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-3.51"/>
            </svg>
            <!-- user-plus icon -->
            <svg v-if="tab.icon === 'user-plus'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
              <line x1="19" y1="8" x2="19" y2="14"/><line x1="16" y1="11" x2="22" y2="11"/>
            </svg>
          </span>
          {{ tab.label }}
        </button>
      </div>
    </nav>

    <!-- Main Content -->
    <main class="app-main">

      <!-- TAB: VERIFIKASI -->
      <transition name="slide-up" mode="out-in">
        <div v-if="activeTab === 'Verifikasi'" class="tab-grid tab-grid--verify" key="verify">

          <!-- Camera panel -->
          <div class="card card--camera">
            <div class="card-header">
              <span class="card-label">Kamera Aktif</span>
              <div class="live-indicator">
                <span class="live-dot"></span>
                LIVE
              </div>
            </div>

            <div :class="['cam-viewport', scanLine ? 'cam-viewport--scanning' : '']">
              <video ref="videoRef" autoplay playsinline class="cam-video"></video>
              <canvas ref="canvasRef" width="640" height="480" class="cam-canvas"></canvas>

              <!-- Corner brackets -->
              <span class="corner corner--tl" aria-hidden="true"></span>
              <span class="corner corner--tr" aria-hidden="true"></span>
              <span class="corner corner--bl" aria-hidden="true"></span>
              <span class="corner corner--br" aria-hidden="true"></span>

              <!-- Scan animation -->
              <div v-if="isLoading" class="scan-line" aria-hidden="true"></div>
            </div>

            <!-- Session selector -->
            <div class="session-row">
              <label class="field-label">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                  <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
                </svg>
                Sesi Kelas
              </label>
              <select v-model="selectedSession" class="field-select">
                <option v-for="option in sessionOptions" :key="option" :value="option">{{ option }}</option>
              </select>
            </div>

            <!-- CTA -->
            <button @click="captureAndVerify" :disabled="isLoading" class="btn btn--primary btn--full">
              <span v-if="isLoading" class="btn-loader">
                <svg class="spin" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                  <line x1="12" y1="2" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="22"/>
                  <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"/><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"/>
                  <line x1="2" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="22" y2="12"/>
                  <line x1="4.93" y1="19.07" x2="7.76" y2="16.24"/><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"/>
                </svg>
                Memproses AI...
              </span>
              <span v-else>
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
                </svg>
                Pindai Wajah
              </span>
            </button>
          </div>

          <!-- Result panel -->
          <div class="card card--result">
            <div class="card-header">
              <span class="card-label">Hasil Verifikasi</span>
            </div>

            <!-- Empty state -->
            <div v-if="!resultData && !isLoading" class="result-empty">
              <div class="empty-icon" aria-hidden="true">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
              </div>
              <p class="empty-text">Arahkan wajah ke kamera<br>lalu tekan Pindai Wajah</p>
            </div>

            <!-- Loading state -->
            <div v-if="isLoading && !resultData" class="result-loading">
              <div class="loading-ring" aria-label="Memproses">
                <span></span><span></span><span></span>
              </div>
              <p class="loading-text">Memproses data wajah...</p>
            </div>

            <!-- Result data -->
            <div v-if="resultData && !isLoading" class="result-data">
              <div :class="['result-status', resultData.spoof_status === 'REAL' ? 'result-status--success' : 'result-status--danger']">
                <span class="status-icon" aria-hidden="true">
                  <svg v-if="resultData.spoof_status === 'REAL'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                  <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                  </svg>
                </span>
                {{ resultData.spoof_status === 'REAL' ? 'Absensi Berhasil' : 'Akses Ditolak' }}
              </div>

              <div class="result-name">
                <p class="result-name-label">Nama Mahasiswa</p>
                <p class="result-name-value">{{ resultData.nama }}</p>
              </div>

              <div class="result-metrics">
                <div class="metric-chip">
                  <p class="metric-label">Liveness</p>
                  <p :class="['metric-value', resultData.spoof_status === 'REAL' ? 'metric-value--green' : 'metric-value--red']">
                    {{ resultData.spoof_status === 'REAL' ? 'ASLI' : 'PALSU' }}
                  </p>
                </div>
                <div class="metric-chip">
                  <p class="metric-label">Jarak</p>
                  <p class="metric-value">{{ resultData.similarity }}</p>
                </div>
              </div>

              <div class="result-session">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                  <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
                </svg>
                {{ selectedSession }}
              </div>
            </div>
          </div>

        </div>
      </transition>

      <!-- TAB: RIWAYAT -->
      <transition name="slide-up" mode="out-in">
        <div v-if="activeTab === 'Riwayat'" class="tab-stack" key="history">

          <!-- Stats bar -->
          <div class="stats-row">
            <div class="stat-card">
              <p class="stat-label">Total Hadir</p>
              <p class="stat-value">{{ totalHadir }}</p>
            </div>
            <div :class="['stat-card', isApiConnected ? 'stat-card--online' : 'stat-card--offline']">
              <p class="stat-label">API Server</p>
              <p class="stat-value">
                {{ isApiConnected ? 'Online' : 'Offline' }}
              </p>
              <a v-if="!isApiConnected" :href="demoVideoUrl" target="_blank" class="stat-demo-link">Lihat demo ↗</a>
            </div>
            <button @click="downloadCSV" class="action-card action-card--export">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
              <span>Export CSV</span>
            </button>
            <button @click="resetHistory" class="action-card action-card--danger">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
              </svg>
              <span>Reset Data</span>
            </button>
          </div>

          <!-- Table card -->
          <div class="card card--table">
            <div class="card-header card-header--spread">
              <span class="card-label">Log Presensi Praktikum</span>
              <span class="record-count">{{ totalHadir }} entri</span>
            </div>
            <div class="table-wrap">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Nama Mahasiswa</th>
                    <th>Kelas / Sesi</th>
                    <th>Waktu Absen</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="historyData.length === 0">
                    <td colspan="4" class="table-empty">Belum ada data presensi yang masuk.</td>
                  </tr>
                  <tr v-for="(item, index) in historyData" :key="index">
                    <td class="td-id">{{ item.id }}</td>
                    <td class="td-name">{{ item.visitor_name }}</td>
                    <td>
                      <span class="session-badge">{{ item.session || 'Umum' }}</span>
                    </td>
                    <td class="td-time">{{ item.Timing }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

        </div>
      </transition>

      <!-- TAB: TAMBAH -->
      <transition name="slide-up" mode="out-in">
        <div v-if="activeTab === 'Tambah'" class="tab-grid tab-grid--add" key="add">

          <!-- Camera panel -->
          <div class="card card--camera">
            <div class="card-header">
              <span class="card-label">Preview Kamera</span>
              <div class="live-indicator">
                <span class="live-dot"></span>
                LIVE
              </div>
            </div>
            <div class="cam-viewport cam-viewport--blue">
              <video ref="videoRef" autoplay playsinline class="cam-video"></video>
              <canvas ref="canvasRef" width="640" height="480" class="cam-canvas"></canvas>
              <span class="corner corner--tl corner--blue" aria-hidden="true"></span>
              <span class="corner corner--tr corner--blue" aria-hidden="true"></span>
              <span class="corner corner--bl corner--blue" aria-hidden="true"></span>
              <span class="corner corner--br corner--blue" aria-hidden="true"></span>
            </div>
          </div>

          <!-- Register panel -->
          <div class="card card--register">
            <div class="card-header">
              <span class="card-label">Registrasi Wajah Baru</span>
            </div>

            <div class="register-form">
              <div class="field-group">
                <label class="field-label">Nama Lengkap Mahasiswa</label>
                <input
                  v-model="newName"
                  @keyup.enter="captureAndAdd"
                  type="text"
                  placeholder="Contoh: Budi Santoso"
                  class="field-input"
                />
              </div>

              <button @click="captureAndAdd" :disabled="isLoading || !newName" class="btn btn--blue btn--full">
                <span v-if="isLoading">
                  <svg class="spin" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                    <line x1="12" y1="2" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="22"/>
                    <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"/><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"/>
                    <line x1="2" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="22" y2="12"/>
                    <line x1="4.93" y1="19.07" x2="7.76" y2="16.24"/><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"/>
                  </svg>
                  Menyimpan...
                </span>
                <span v-else>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                    <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
                    <polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/>
                  </svg>
                  Simpan ke Database
                </span>
              </button>

              <div class="register-tip">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                  <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
                <p>Pastikan wajah terlihat jelas, pencahayaan merata, dan tidak menggunakan kacamata gelap sebelum menyimpan.</p>
              </div>
            </div>
          </div>

        </div>
      </transition>

    </main>

    <!-- Footer -->
    <footer class="app-footer">
      Fasilkom · Sistem Presensi Berbasis AI · {{ new Date().getFullYear() }}
    </footer>

  </div>
</template>

<style scoped>
/* ===================================
   RESET & BASE
=================================== */
@import url('https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600&family=Geist+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

.app-root {
  min-height: 100vh;
  background-color: #0c0c0e;
  color: #e8e6e1;
  font-family: 'Geist', -apple-system, sans-serif;
  font-size: 14px;
  line-height: 1.6;
  position: relative;
  overflow-x: hidden;
}

/* ===================================
   BACKGROUND GRID
=================================== */
.bg-grid {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background-image:
    linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px);
  background-size: 40px 40px;
}

/* ===================================
   HEADER
=================================== */
.app-header {
  position: relative;
  z-index: 10;
  border-bottom: 1px solid rgba(255,255,255,0.07);
  background: rgba(12,12,14,0.9);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  padding: 0 24px;
}

.header-inner {
  max-width: 1100px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 60px;
}

.header-brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: #8B0000;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffd0d0;
  flex-shrink: 0;
}

.brand-title {
  font-size: 15px;
  font-weight: 600;
  color: #f0ede8;
  letter-spacing: -0.3px;
}

.brand-sub {
  font-size: 11px;
  color: #666;
  letter-spacing: 0.2px;
}

.header-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 500;
  color: #888;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.pulse-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #22c55e;
  animation: pulseDot 2s ease-in-out infinite;
}

@keyframes pulseDot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.7); }
}

/* ===================================
   NAVIGATION
=================================== */
.app-nav {
  position: relative;
  z-index: 10;
  padding: 0 24px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  background: rgba(14,14,17,0.8);
}

.nav-inner {
  max-width: 1100px;
  margin: 0 auto;
  display: flex;
  gap: 2px;
}

.nav-btn {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 14px 18px;
  font-size: 13px;
  font-weight: 500;
  color: #888;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  transition: color 0.2s, border-color 0.2s;
  letter-spacing: 0.1px;
  margin-bottom: -1px;
}

.nav-btn:hover { color: #ccc; }

.nav-btn--active {
  color: #f87171;
  border-bottom-color: #8B0000;
}

.nav-icon {
  display: flex;
  align-items: center;
  opacity: 0.8;
}

/* ===================================
   MAIN CONTENT
=================================== */
.app-main {
  position: relative;
  z-index: 5;
  max-width: 1100px;
  margin: 0 auto;
  padding: 28px 24px 60px;
}

/* ===================================
   CARD
=================================== */
.card {
  background: #141417;
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 12px;
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px 12px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.card-header--spread {
  justify-content: space-between;
}

.card-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  color: #666;
}

.record-count {
  font-size: 11px;
  color: #555;
}

/* ===================================
   LIVE INDICATOR
=================================== */
.live-indicator {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 1px;
  color: #e74c3c;
}

.live-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #e74c3c;
  animation: blink 1.2s step-start infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* ===================================
   TAB LAYOUTS
=================================== */
.tab-grid {
  display: grid;
  gap: 16px;
}

.tab-grid--verify {
  grid-template-columns: 1fr 380px;
}

.tab-grid--add {
  grid-template-columns: 1fr 380px;
}

.tab-stack {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ===================================
   CAMERA
=================================== */
.card--camera {
  display: flex;
  flex-direction: column;
}

.cam-viewport {
  position: relative;
  background: #000;
  aspect-ratio: 16/10;
  overflow: hidden;
}

.cam-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transform: scaleX(-1);
  display: block;
}

.cam-canvas { display: none; }

/* Corner brackets */
.corner {
  position: absolute;
  width: 20px;
  height: 20px;
  border-color: rgba(220, 38, 38, 0.7);
  border-style: solid;
  z-index: 5;
}
.corner--blue { border-color: rgba(59, 130, 246, 0.7) !important; }
.corner--tl { top: 12px; left: 12px; border-width: 2px 0 0 2px; }
.corner--tr { top: 12px; right: 12px; border-width: 2px 2px 0 0; }
.corner--bl { bottom: 12px; left: 12px; border-width: 0 0 2px 2px; }
.corner--br { bottom: 12px; right: 12px; border-width: 0 2px 2px 0; }

/* Scan line animation */
.scan-line {
  position: absolute;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, #dc2626, transparent);
  animation: scanMove 1.5s linear infinite;
  z-index: 6;
}

@keyframes scanMove {
  from { top: 0%; }
  to { top: 100%; }
}

/* ===================================
   SESSION & FORM ELEMENTS
=================================== */
.session-row {
  padding: 14px 16px;
  border-top: 1px solid rgba(255,255,255,0.06);
  display: flex;
  align-items: center;
  gap: 12px;
}

.field-label {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  color: #666;
  white-space: nowrap;
}

.field-select {
  flex: 1;
  background: #0c0c0e;
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 7px;
  color: #d0cdc8;
  padding: 8px 12px;
  font-size: 13px;
  font-family: 'Geist', sans-serif;
  outline: none;
  transition: border-color 0.2s;
  cursor: pointer;
}

.field-select:focus { border-color: rgba(139, 0, 0, 0.6); }

/* ===================================
   BUTTONS
=================================== */
.btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 11px 22px;
  font-size: 13px;
  font-weight: 600;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.18s, transform 0.12s, opacity 0.18s;
  letter-spacing: 0.1px;
}

.btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  transform: none !important;
}

.btn:not(:disabled):active { transform: scale(0.98); }

.btn--full {
  width: 100%;
  margin: 14px 16px;
  width: calc(100% - 32px);
}

.btn--primary {
  background: #8B0000;
  color: #ffd0d0;
}
.btn--primary:not(:disabled):hover { background: #a00000; }

.btn--blue {
  background: #1e3a5f;
  color: #93c5fd;
}
.btn--blue:not(:disabled):hover { background: #244872; }

.btn-loader {
  display: flex;
  align-items: center;
  gap: 8px;
}

.spin {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* ===================================
   RESULT PANEL
=================================== */
.card--result {
  display: flex;
  flex-direction: column;
}

.result-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  gap: 16px;
}

.empty-icon {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #3a3a3a;
}

.empty-text {
  font-size: 13px;
  color: #555;
  text-align: center;
  line-height: 1.8;
}

.result-loading {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  gap: 20px;
}

.loading-ring {
  display: flex;
  gap: 6px;
}

.loading-ring span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #8B0000;
  animation: dotBounce 1.4s ease-in-out infinite both;
}
.loading-ring span:nth-child(2) { animation-delay: 0.2s; }
.loading-ring span:nth-child(3) { animation-delay: 0.4s; }

@keyframes dotBounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

.loading-text {
  font-size: 12px;
  color: #555;
  letter-spacing: 0.3px;
}

.result-data {
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  animation: fadeUp 0.3s ease forwards;
}

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.result-status {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.3px;
}

.result-status--success {
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.2);
  color: #4ade80;
}

.result-status--danger {
  background: rgba(220, 38, 38, 0.12);
  border: 1px solid rgba(220, 38, 38, 0.25);
  color: #f87171;
}

.status-icon {
  display: flex;
  align-items: center;
}

.result-name {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 8px;
  padding: 12px 14px;
}

.result-name-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.7px;
  color: #555;
  margin-bottom: 4px;
  font-weight: 600;
}

.result-name-value {
  font-size: 17px;
  font-weight: 600;
  color: #e8e6e1;
  letter-spacing: -0.2px;
}

.result-metrics {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.metric-chip {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 8px;
  padding: 10px 14px;
}

.metric-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.7px;
  color: #555;
  font-weight: 600;
  margin-bottom: 4px;
}

.metric-value {
  font-size: 15px;
  font-weight: 700;
  color: #ccc;
  font-family: 'Geist Mono', monospace;
}

.metric-value--green { color: #4ade80; }
.metric-value--red { color: #f87171; }

.result-session {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #555;
}

/* ===================================
   STATS ROW
=================================== */
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.stat-card {
  background: #141417;
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 10px;
  padding: 16px 18px;
  position: relative;
  overflow: hidden;
}

.stat-card--online { border-left: 3px solid #22c55e; }
.stat-card--offline { border-left: 3px solid #ef4444; }

.stat-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.7px;
  color: #555;
  font-weight: 600;
  margin-bottom: 6px;
}

.stat-value {
  font-size: 22px;
  font-weight: 600;
  color: #e8e6e1;
  letter-spacing: -0.5px;
  line-height: 1;
}

.stat-card--online .stat-value { color: #4ade80; }
.stat-card--offline .stat-value { color: #f87171; }

.stat-demo-link {
  display: inline-block;
  margin-top: 6px;
  font-size: 11px;
  color: #888;
  text-decoration: none;
  transition: color 0.2s;
}
.stat-demo-link:hover { color: #ccc; }

.action-card {
  background: #141417;
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 10px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  transition: background 0.18s, border-color 0.18s;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.2px;
}

.action-card--export {
  color: #93c5fd;
  border-color: rgba(59, 130, 246, 0.15);
}
.action-card--export:hover {
  background: rgba(59, 130, 246, 0.08);
  border-color: rgba(59, 130, 246, 0.3);
}

.action-card--danger {
  color: #f87171;
  border-color: rgba(239, 68, 68, 0.15);
}
.action-card--danger:hover {
  background: rgba(239, 68, 68, 0.08);
  border-color: rgba(239, 68, 68, 0.3);
}

/* ===================================
   TABLE
=================================== */
.card--table { overflow: hidden; }

.table-wrap {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.data-table thead tr {
  background: rgba(255,255,255,0.02);
}

.data-table th {
  padding: 11px 16px;
  text-align: left;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.7px;
  color: #555;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.data-table tbody tr {
  border-bottom: 1px solid rgba(255,255,255,0.04);
  transition: background 0.15s;
}

.data-table tbody tr:last-child { border-bottom: none; }

.data-table tbody tr:hover { background: rgba(255,255,255,0.02); }

.data-table td { padding: 12px 16px; color: #b0ada8; vertical-align: middle; }

.td-id {
  font-family: 'Geist Mono', monospace;
  font-size: 11px;
  color: #444 !important;
}

.td-name {
  font-weight: 500;
  color: #d8d5d0 !important;
}

.td-time {
  font-family: 'Geist Mono', monospace;
  font-size: 12px;
  color: #555 !important;
}

.session-badge {
  display: inline-block;
  background: rgba(139, 0, 0, 0.18);
  color: #f87171;
  border: 1px solid rgba(139, 0, 0, 0.3);
  border-radius: 4px;
  padding: 3px 8px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.2px;
}

.table-empty {
  text-align: center;
  padding: 40px !important;
  color: #444 !important;
  font-style: italic;
}

/* ===================================
   REGISTER FORM
=================================== */
.card--register {
  display: flex;
  flex-direction: column;
}

.register-form {
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field-input {
  background: #0c0c0e;
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 7px;
  color: #d0cdc8;
  padding: 10px 13px;
  font-size: 13px;
  font-family: 'Geist', sans-serif;
  outline: none;
  transition: border-color 0.2s;
  width: 100%;
}

.field-input::placeholder { color: #3a3a3a; }
.field-input:focus { border-color: rgba(59, 130, 246, 0.5); }

.btn--full {
  margin: 0;
  width: 100%;
}

.register-tip {
  display: flex;
  align-items: flex-start;
  gap: 9px;
  background: rgba(59, 130, 246, 0.05);
  border: 1px solid rgba(59, 130, 246, 0.12);
  border-radius: 8px;
  padding: 12px 14px;
  color: #6b8fc5;
}

.register-tip svg { flex-shrink: 0; margin-top: 1px; }
.register-tip p { font-size: 12px; line-height: 1.7; }

/* ===================================
   FOOTER
=================================== */
.app-footer {
  position: relative;
  z-index: 5;
  text-align: center;
  padding: 20px 24px;
  font-size: 11px;
  color: #333;
  letter-spacing: 0.3px;
  border-top: 1px solid rgba(255,255,255,0.04);
}

/* ===================================
   TRANSITIONS
=================================== */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: opacity 0.22s ease, transform 0.22s ease;
}

.slide-up-enter-from {
  opacity: 0;
  transform: translateY(12px);
}

.slide-up-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* ===================================
   RESPONSIVE
=================================== */
@media (max-width: 800px) {
  .tab-grid--verify,
  .tab-grid--add {
    grid-template-columns: 1fr;
  }

  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }

  .header-inner { height: 52px; }

  .nav-btn { padding: 12px 12px; font-size: 12px; }
}

@media (max-width: 480px) {
  .app-main { padding: 16px 14px 48px; }
  .stats-row { grid-template-columns: 1fr 1fr; }
  .brand-title { font-size: 14px; }
  .header-badge { display: none; }
}
</style>