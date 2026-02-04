<template>
  <div class="app-container">
    <!-- 背景装饰 -->
    <div class="bg-decoration">
      <div class="bg-circle c1"></div>
      <div class="bg-circle c2"></div>
      <div class="bg-circle c3"></div>
    </div>
    
    <!-- 主内容 -->
    <router-view />
    
    <!-- 快速注册弹窗 -->
    <div v-if="showRegisterModal" class="modal-overlay">
      <div class="register-card animate-bounce-in">
        <div class="register-header">
          <div class="register-emoji">🎮</div>
          <h2 class="register-title">欢迎来到</h2>
          <h1 class="register-app-name">我爱填单词！</h1>
        </div>
        
        <div class="register-form">
          <label class="input-label">请输入你的昵称</label>
          <input 
            v-model="registerNickname" 
            type="text" 
            class="nickname-input" 
            placeholder="如：小明同学"
            maxlength="12"
            @keyup.enter="completeRegistration"
          >
          
          <label class="input-label">选择一个头像</label>
          <div class="avatar-grid">
            <button 
              v-for="avatar in avatarOptions" 
              :key="avatar"
              :class="['avatar-btn', { active: selectedAvatar === avatar }]"
              @click="selectedAvatar = avatar"
            >
              {{ avatar }}
            </button>
          </div>
        </div>
        
        <button 
          @click="completeRegistration" 
          :disabled="!registerNickname.trim()"
          class="start-btn"
        >
          开始游戏 🚀
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useUserStore } from './stores/user'
import { trackApi } from './api/index.js'

const userStore = useUserStore()

const showRegisterModal = ref(false)
const registerNickname = ref('')
const selectedAvatar = ref('😊')
const sessionId = ref(null)

const avatarOptions = ['😊', '😎', '🤓', '😺', '🐶', '🦊', '🐰', '🐼', '🦄', '🌟']

onMounted(async () => {
  // 等待用户信息加载完成（从后端或本地缓存）
  const hasUser = await userStore.loadUser()
  
  // 加载完成后检查是否已注册
  if (!hasUser && !userStore.isRegistered) {
    showRegisterModal.value = true
  }
  
  // 启动会话追踪
  sessionId.value = trackApi.generateSessionId()
  const deviceInfo = trackApi.getDeviceInfo()
  trackApi.startSession(sessionId.value, deviceInfo)
})

onUnmounted(() => {
  // 结束会话追踪
  if (sessionId.value) {
    trackApi.endSession(sessionId.value)
  }
})

function completeRegistration() {
  const name = registerNickname.value.trim()
  if (!name) return
  
  userStore.register(name, selectedAvatar.value)
  showRegisterModal.value = false
}
</script>

<style>
/* 全局样式 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Nunito', -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background: linear-gradient(135deg, #a78bfa 0%, #FFB6C1 50%, #FF69B4 100%);
  min-height: 100vh;
  overflow-x: hidden;
}

/* 导入 Nunito 字体 */
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap');
</style>

<style scoped>
.app-container {
  min-height: 100vh;
  min-height: 100dvh;
  position: relative;
}

/* 背景装饰圆圈 */
.bg-decoration {
  position: fixed;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
  z-index: 0;
}

.bg-circle {
  position: absolute;
  border-radius: 50%;
  opacity: 0.15;
}

.bg-circle.c1 {
  width: 300px;
  height: 300px;
  background: #fbbf24;
  top: -100px;
  right: -100px;
  animation: float1 8s ease-in-out infinite;
}

.bg-circle.c2 {
  width: 200px;
  height: 200px;
  background: #34d399;
  bottom: 20%;
  left: -80px;
  animation: float2 10s ease-in-out infinite;
}

.bg-circle.c3 {
  width: 150px;
  height: 150px;
  background: #f472b6;
  bottom: -50px;
  right: 20%;
  animation: float3 12s ease-in-out infinite;
}

@keyframes float1 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(-20px, 30px) scale(1.1); }
}

@keyframes float2 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(30px, -20px) scale(0.9); }
}

@keyframes float3 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(-15px, -25px) scale(1.05); }
}

/* 注册弹窗 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.register-card {
  background: white;
  border-radius: 28px;
  padding: 32px 28px;
  max-width: 360px;
  width: 100%;
  box-shadow: 0 12px 0 rgba(0, 0, 0, 0.1), 0 25px 60px rgba(0, 0, 0, 0.25);
  border: 3px solid rgba(255, 255, 255, 0.9);
}

.register-header {
  text-align: center;
  margin-bottom: 24px;
}

.register-emoji {
  font-size: 3.5rem;
  margin-bottom: 8px;
  animation: bounce 1s ease-in-out infinite;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.register-title {
  font-size: 1.1rem;
  color: #6b7280;
  font-weight: 700;
  margin: 0;
}

.register-app-name {
  font-size: 1.8rem;
  font-weight: 900;
  color: #FF69B4;
  margin: 4px 0 0;
  letter-spacing: 2px;
}

.register-form {
  margin-bottom: 24px;
}

.input-label {
  display: block;
  font-size: 0.9rem;
  font-weight: 700;
  color: #374151;
  margin-bottom: 8px;
}

.nickname-input {
  width: 100%;
  padding: 14px 18px;
  border: 3px solid #e5e7eb;
  border-radius: 14px;
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 20px;
  transition: all 0.2s ease;
  box-sizing: border-box;
}

.nickname-input:focus {
  outline: none;
  border-color: #FFB6C1;
  box-shadow: 0 0 0 4px rgba(139, 92, 246, 0.2);
}

.avatar-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
}

.avatar-btn {
  width: 50px;
  height: 50px;
  font-size: 1.6rem;
  background: linear-gradient(180deg, #f9fafb, #f3f4f6);
  border: 3px solid #e5e7eb;
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.15s ease;
  box-shadow: 0 3px 0 #d1d5db;
}

.avatar-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 0 #d1d5db;
}

.avatar-btn.active {
  background: linear-gradient(180deg, #fef3c7, #fde68a);
  border-color: #fbbf24;
  box-shadow: 0 3px 0 #d97706;
  transform: scale(1.1);
}

.start-btn {
  width: 100%;
  padding: 16px;
  background: linear-gradient(180deg, #a78bfa, #FFB6C1);
  border: 3px solid #FF69B4;
  border-radius: 16px;
  font-size: 1.15rem;
  font-weight: 800;
  color: #5D5D5D;
  cursor: pointer;
  box-shadow: 0 5px 0 #FF69B4;
  transition: all 0.15s ease;
}

.start-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 7px 0 #FF69B4;
}

.start-btn:active:not(:disabled) {
  transform: translateY(3px);
  box-shadow: 0 2px 0 #FF69B4;
}

.start-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.animate-bounce-in {
  animation: bounceIn 0.4s ease-out;
}

@keyframes bounceIn {
  0% { transform: scale(0.5); opacity: 0; }
  70% { transform: scale(1.05); }
  100% { transform: scale(1); opacity: 1; }
}
</style>
