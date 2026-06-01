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

// --- KONFIGURASI URL CLOUD & FALLBACK ---
const API_URL = "https://[id-ngrok-lu].ngrok-free.app" // <- MASUKIN LINK NGROK LU
const demoVideoUrl = "https://youtube.com/watch?v=GANTI_LINK_VIDEO_LU" // <- MASUKIN LINK VIDEO LU

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
    finally { isLoading.value = false }
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
      if(data.status === 'success') newName.value = '' 
    } catch (error) { alert("Server AI Offline! Tonton video demo saja.") } 
    finally { isLoading.value = false }
  }, 'image/jpeg')
}

const downloadCSV = () => {
  if(historyData.value.length === 0) return alert("Belum ada data!")
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
  if(!confirm("Yakin mau hapus SEMUA data presensi? Ini nggak bisa di-undo bro!")) return;
  try {
    const response = await fetch(`${API_URL}/reset-history`, fetchOptions('DELETE'))
    if(response.ok) {
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
  <div class="min-h-screen bg-[#f3f4f6] flex flex-col items-center py-6 px-4 md:py-10 md:px-8 font-sans relative overflow-hidden">
    
    <div class="absolute top-[-10%] left-[-10%] w-96 h-96 bg-red-200 rounded-full mix-blend-multiply filter blur-3xl opacity-50 animate-pulse"></div>
    <div class="absolute bottom-[-10%] right-[-10%] w-96 h-96 bg-blue-200 rounded-full mix-blend-multiply filter blur-3xl opacity-50"></div>

    <div class="relative w-full max-w-5xl rounded-3xl shadow-2xl p-6 md:p-8 mb-6 md:mb-8 text-center text-white bg-gradient-to-br from-[#8B0000] via-[#A52A2A] to-[#600000] overflow-hidden group">
      <div class="absolute inset-0 bg-white/10 backdrop-blur-sm opacity-0 group-hover:opacity-100 transition-opacity duration-700"></div>
      <h1 class="text-2xl md:text-4xl font-extrabold mb-2 md:mb-3 tracking-tight relative z-10 drop-shadow-md">Sistem Presensi Fasilkom</h1>
      <p class="text-xs md:text-sm text-red-100 font-medium tracking-wider relative z-10 opacity-90 leading-relaxed md:leading-normal">
        Lab AI & Data Science <br class="block md:hidden" /> 
        <span class="hidden md:inline"> | </span>
        <span class="bg-white/20 py-1 px-3 mt-2 md:mt-0 inline-block whitespace-nowrap rounded-full text-[10px] md:text-xs border border-white/30 backdrop-blur-md">Edge Computing Node</span>
      </p>
    </div>

    <div class="flex flex-col md:flex-row gap-2 mb-8 w-full max-w-2xl bg-white/60 backdrop-blur-xl p-2 rounded-2xl md:rounded-full shadow-lg border border-white/50 relative z-10">
      <button @click="activeTab = 'Verifikasi'" :class="['flex-1 py-3 px-2 rounded-xl md:rounded-full font-bold text-xs md:text-sm transition-all duration-300', activeTab === 'Verifikasi' ? 'bg-gradient-to-r from-[#8B0000] to-[#b30000] text-white shadow-md transform scale-[1.02]' : 'text-gray-500 hover:bg-white/80']">
        📸 Visitor Validation
      </button>
      <button @click="activeTab = 'Riwayat'" :class="['flex-1 py-3 px-2 rounded-xl md:rounded-full font-bold text-xs md:text-sm transition-all duration-300', activeTab === 'Riwayat' ? 'bg-gradient-to-r from-[#8B0000] to-[#b30000] text-white shadow-md transform scale-[1.02]' : 'text-gray-500 hover:bg-white/80']">
        🕒 View History
      </button>
      <button @click="activeTab = 'Tambah'" :class="['flex-1 py-3 px-2 rounded-xl md:rounded-full font-bold text-xs md:text-sm transition-all duration-300', activeTab === 'Tambah' ? 'bg-gradient-to-r from-[#8B0000] to-[#b30000] text-white shadow-md transform scale-[1.02]' : 'text-gray-500 hover:bg-white/80']">
        ➕ Add to Database
      </button>
    </div>

    <div class="w-full max-w-5xl relative z-10">
      
      <transition name="fade" mode="out-in">
        <div v-if="activeTab === 'Verifikasi'" class="flex flex-col md:flex-row gap-4 md:gap-6">
          <div class="bg-white/80 backdrop-blur-lg p-5 md:p-6 rounded-3xl shadow-xl border border-white w-full md:w-2/3 flex flex-col items-center transition-all hover:shadow-2xl">
            
            <div class="w-full mb-4 md:mb-5">
              <label class="block text-xs md:text-sm font-extrabold text-gray-600 mb-2 uppercase tracking-wide">Pilih Sesi Kelas</label>
              <select v-model="selectedSession" class="w-full p-3 border-2 border-gray-200 rounded-xl focus:ring-0 focus:border-[#8B0000] bg-gray-50 text-gray-800 font-medium transition-all shadow-inner text-sm md:text-base">
                <option v-for="option in sessionOptions" :key="option" :value="option">{{ option }}</option>
              </select>
            </div>

            <div class="relative w-full rounded-2xl overflow-hidden bg-gray-900 shadow-inner border-4 border-gray-100 flex justify-center items-center aspect-video group">
              <video ref="videoRef" autoplay playsinline class="w-full h-full object-cover transform scale-x-[-1]"></video>
              <canvas ref="canvasRef" width="640" height="480" class="hidden"></canvas>
              <div class="absolute inset-0 border-2 border-transparent group-hover:border-[#8B0000]/50 rounded-2xl transition-all duration-500 pointer-events-none"></div>
            </div>
            
            <button @click="captureAndVerify" :disabled="isLoading" class="mt-6 md:mt-8 bg-gradient-to-r from-[#8B0000] to-[#b30000] hover:from-[#600000] hover:to-[#8B0000] text-white font-bold py-3 md:py-4 px-8 md:px-10 rounded-full shadow-lg shadow-red-900/30 transition-all duration-300 flex items-center gap-3 disabled:opacity-50 hover:-translate-y-1 active:translate-y-0 w-full md:w-auto justify-center">
              <span v-if="isLoading" class="flex items-center gap-2 text-sm md:text-lg">
                <svg class="animate-spin h-5 w-5 text-white" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                Memproses AI...
              </span>
              <span v-else class="text-sm md:text-lg">📸 Verifikasi Wajah</span>
            </button>
          </div>

          <div class="bg-white/80 backdrop-blur-lg p-5 md:p-8 rounded-3xl shadow-xl border border-white w-full md:w-1/3 flex flex-col justify-start relative overflow-hidden">
            <div class="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-[#8B0000] to-red-500"></div>
            <h2 class="text-lg md:text-xl font-bold mb-4 md:mb-6 text-gray-800 border-b-2 border-gray-100 pb-3">Live Status</h2>
            
            <div v-if="!resultData && !isLoading" class="text-gray-400 text-center mt-6 md:mt-12 flex flex-col items-center">
              <span class="text-4xl md:text-5xl mb-4 opacity-30">👤</span>
              <p class="font-medium text-sm md:text-base">Menunggu pemindaian wajah...</p>
            </div>
            
            <div v-if="resultData && !isLoading" class="space-y-4 md:space-y-6 animate-fade-in-up">
              <div :class="resultData.spoof_status === 'REAL' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'" class="p-3 md:p-4 rounded-2xl text-center shadow-inner">
                <span class="block text-sm md:text-md font-extrabold tracking-wide uppercase">{{ resultData.spoof_status === 'REAL' ? 'Berhasil Diabsen!' : 'Akses Ditolak!' }}</span>
              </div>
              <div class="bg-gray-50 p-3 md:p-4 rounded-2xl border border-gray-100">
                <label class="text-[10px] md:text-xs text-gray-400 uppercase font-bold tracking-wider">Nama Mahasiswa</label>
                <p class="text-lg md:text-xl font-black text-gray-800 mt-1">{{ resultData.nama }}</p>
              </div>
              <div class="flex gap-3 md:gap-4">
                <div class="bg-gray-50 p-3 md:p-4 rounded-2xl border border-gray-100 flex-1">
                  <label class="text-[10px] md:text-xs text-gray-400 uppercase font-bold tracking-wider">Liveness</label>
                  <p class="text-base md:text-lg font-black mt-1" :class="resultData.spoof_status === 'REAL' ? 'text-green-600' : 'text-red-600'">{{ resultData.spoof_status === 'REAL' ? 'ASLI' : 'PALSU' }}</p>
                </div>
                <div class="bg-gray-50 p-3 md:p-4 rounded-2xl border border-gray-100 flex-1">
                  <label class="text-[10px] md:text-xs text-gray-400 uppercase font-bold tracking-wider">Jarak</label>
                  <p class="text-base md:text-lg font-black text-gray-700 mt-1">{{ resultData.similarity }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </transition>

      <transition name="fade" mode="out-in">
        <div v-if="activeTab === 'Riwayat'" class="w-full flex flex-col gap-4 md:gap-6">
          <div class="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-5">
            <div class="bg-white/90 backdrop-blur-lg p-4 md:p-6 rounded-2xl md:rounded-3xl shadow-md border border-white border-l-4 border-l-blue-500 flex flex-col justify-center">
              <h3 class="text-gray-400 text-[10px] md:text-xs font-bold uppercase tracking-wider">Kehadiran</h3>
              <p class="text-2xl md:text-4xl font-black text-gray-800 mt-1">{{ totalHadir }} <span class="text-[10px] md:text-sm font-semibold text-gray-400">Data</span></p>
            </div>
            
            <div :class="isApiConnected ? 'border-l-green-500' : 'border-l-red-500'" class="bg-white/90 backdrop-blur-lg p-4 md:p-6 rounded-2xl md:rounded-3xl shadow-md border border-white border-l-4 relative overflow-hidden flex flex-col justify-center">
              <h3 class="text-gray-400 text-[10px] md:text-xs font-bold uppercase tracking-wider">API Server</h3>
              <div v-if="isApiConnected">
                <p class="text-2xl md:text-4xl font-black text-green-500 mt-1">Aktif</p>
              </div>
              <div v-else>
                <p class="text-xl md:text-3xl font-black text-red-500 mt-1">Offline</p>
                <a :href="demoVideoUrl" target="_blank" class="mt-1 inline-block bg-red-100 text-red-800 text-[9px] font-bold py-1 px-2 rounded-full">
                  ▶️ Nonton Video
                </a>
              </div>
            </div>

            <button @click="downloadCSV" class="bg-white/90 backdrop-blur-lg p-4 md:p-6 rounded-2xl md:rounded-3xl shadow-md border border-white flex flex-col items-center justify-center cursor-pointer hover:bg-gray-50 transition-all">
              <span class="text-2xl md:text-3xl mb-1 md:mb-2">📥</span>
              <span class="font-extrabold text-[#8B0000] text-[10px] md:text-sm text-center">Export CSV</span>
            </button>
            <button @click="resetHistory" class="bg-red-50/90 backdrop-blur-lg p-4 md:p-6 rounded-2xl md:rounded-3xl shadow-md border border-red-100 flex flex-col items-center justify-center cursor-pointer hover:bg-red-100 transition-all">
              <span class="text-2xl md:text-3xl mb-1 md:mb-2">🗑️</span>
              <span class="font-extrabold text-red-700 text-[10px] md:text-sm text-center">Clear Data</span>
            </button>
          </div>

          <div class="bg-white/90 backdrop-blur-lg p-5 md:p-8 rounded-3xl shadow-xl border border-white relative overflow-hidden">
            <h2 class="text-lg md:text-2xl font-extrabold mb-4 md:mb-6 text-gray-800">Log Presensi Praktikum</h2>
            <div class="overflow-x-auto rounded-xl border border-gray-100 shadow-inner">
              <table class="min-w-full text-left border-collapse whitespace-nowrap md:whitespace-normal">
                <thead>
                  <tr class="bg-gray-50 text-gray-500 text-[10px] md:text-xs uppercase tracking-wider font-bold">
                    <th class="p-3 md:p-5 border-b border-gray-200">ID</th>
                    <th class="p-3 md:p-5 border-b border-gray-200">Nama Mahasiswa</th>
                    <th class="p-3 md:p-5 border-b border-gray-200">Kelas / Sesi</th>
                    <th class="p-3 md:p-5 border-b border-gray-200">Waktu Absen</th>
                  </tr>
                </thead>
                <tbody class="text-xs md:text-sm font-medium">
                  <tr v-if="historyData.length === 0"><td colspan="4" class="p-6 md:p-8 text-center text-gray-400 font-bold">Belum ada data presensi yang masuk.</td></tr>
                  <tr v-for="(item, index) in historyData" :key="index" class="border-b border-gray-50 hover:bg-blue-50/50 transition-colors">
                    <td class="p-3 md:p-5 font-mono text-gray-400 text-[10px] md:text-xs">{{ item.id }}</td>
                    <td class="p-3 md:p-5 text-gray-800 font-bold">{{ item.visitor_name }}</td>
                    <td class="p-3 md:p-5">
                      <span class="bg-red-50 text-[#8B0000] py-1 px-2 md:px-3 rounded-full text-[10px] md:text-xs font-bold border border-red-100">{{ item.session || 'Umum' }}</span>
                    </td>
                    <td class="p-3 md:p-5 text-gray-500 text-[10px] md:text-sm">{{ item.Timing }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </transition>

      <transition name="fade" mode="out-in">
        <div v-if="activeTab === 'Tambah'" class="flex flex-col md:flex-row gap-4 md:gap-6">
          <div class="bg-white/80 backdrop-blur-lg p-5 md:p-6 rounded-3xl shadow-xl border border-white w-full md:w-2/3 flex flex-col items-center hover:shadow-2xl transition-shadow">
             <div class="relative w-full rounded-2xl overflow-hidden bg-gray-900 shadow-inner border-4 border-gray-100 flex justify-center items-center aspect-video mb-2">
              <video ref="videoRef" autoplay playsinline class="w-full h-full object-cover transform scale-x-[-1]"></video>
              <canvas ref="canvasRef" width="640" height="480" class="hidden"></canvas>
            </div>
          </div>

          <div class="bg-white/80 backdrop-blur-lg p-5 md:p-8 rounded-3xl shadow-xl border border-white w-full md:w-1/3 flex flex-col justify-start relative overflow-hidden">
            <div class="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-blue-600 to-cyan-500"></div>
            <h2 class="text-lg md:text-xl font-bold mb-4 md:mb-6 text-gray-800 border-b-2 border-gray-100 pb-3">Registrasi Wajah Baru</h2>
            <div class="space-y-4 md:space-y-6">
              <div>
                <label class="block text-[10px] md:text-xs font-bold text-gray-500 mb-2 uppercase tracking-wide">Nama Lengkap</label>
                <input v-model="newName" @keyup.enter="captureAndAdd" type="text" placeholder="Masukkan nama..." class="w-full p-3 md:p-4 border-2 border-gray-200 rounded-xl focus:outline-none focus:border-blue-500 focus:ring-0 bg-gray-50 font-bold text-gray-800 transition-colors text-sm md:text-base">
              </div>
              <button @click="captureAndAdd" :disabled="isLoading || !newName" class="w-full bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 text-white font-bold py-3 md:py-4 px-4 rounded-xl shadow-lg shadow-blue-500/30 transition-all hover:-translate-y-1 active:translate-y-0 disabled:opacity-50 text-sm md:text-base">
                <span v-if="isLoading">Mengekstrak AI...</span>
                <span v-else>💾 Simpan ke Database</span>
              </button>
              <div class="bg-blue-50 p-3 md:p-4 rounded-xl border border-blue-100">
                <p class="text-[10px] md:text-xs text-blue-800 font-medium leading-relaxed">💡 Pastikan wajah terlihat jelas, tidak menggunakan kacamata gelap, dan pencahayaan ruangan merata sebelum menyimpan.</p>
              </div>
            </div>
          </div>
        </div>
      </transition>
    </div>
  </div>
</template>

<style>
/* Animasi pindah Tab biar ga kaku */
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease, transform 0.3s ease; }
.fade-enter-from { opacity: 0; transform: translateY(10px); }
.fade-leave-to { opacity: 0; transform: translateY(-10px); }
.animate-fade-in-up { animation: fadeInUp 0.5s ease-out forwards; }
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>