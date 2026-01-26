<template>
  <div class="settings-screen">
    <!-- 顶部标题 -->
    <div class="settings-header">
      <button @click="goBack" class="back-btn">← 返回</button>
      <h1 class="settings-title">⚙️ 设置</h1>
    </div>

    <!-- 设置卡片 -->
    <div class="settings-card">
      <!-- 发音设置 -->
      <div class="settings-section">
        <div class="section-title">🔊 发音设置</div>
        
        <!-- 自动发音 -->
        <div class="setting-item">
          <div class="setting-info">
            <div class="setting-name">自动发音</div>
            <div class="setting-desc">单词填对后自动播放发音</div>
          </div>
          <label class="toggle-switch">
            <input type="checkbox" v-model="settingsStore.autoSpeak">
            <span class="toggle-slider"></span>
          </label>
        </div>

        <!-- 发音类型 -->
        <div class="setting-item">
          <div class="setting-info">
            <div class="setting-name">发音类型</div>
            <div class="setting-desc">选择美式或英式发音</div>
          </div>
          <div class="voice-toggle">
            <button 
              :class="['voice-btn', { active: settingsStore.voiceType === 'us' }]"
              @click="settingsStore.voiceType = 'us'"
            >
              🇺🇸 美音
            </button>
            <button 
              :class="['voice-btn', { active: settingsStore.voiceType === 'uk' }]"
              @click="settingsStore.voiceType = 'uk'"
            >
              🇬🇧 英音
            </button>
          </div>
        </div>

        <!-- 测试发音 -->
        <div class="setting-item test-speak">
          <button @click="testSpeak" class="test-btn">
            🔊 测试发音 "Hello"
          </button>
        </div>
      </div>

      <!-- 翻译设置 -->
      <div class="settings-section">
        <div class="section-title">📝 翻译设置</div>
        
        <!-- 显示翻译 -->
        <div class="setting-item">
          <div class="setting-info">
            <div class="setting-name">显示翻译</div>
            <div class="setting-desc">在单词列表中显示中文翻译</div>
          </div>
          <label class="toggle-switch">
            <input type="checkbox" v-model="settingsStore.showTranslation">
            <span class="toggle-slider"></span>
          </label>
        </div>
      </div>

      <!-- 音效设置 -->
      <div class="settings-section">
        <div class="section-title">🎵 音效设置</div>
        
        <!-- 背景音乐 -->
        <div class="setting-item">
          <div class="setting-info">
            <div class="setting-name">背景音乐</div>
            <div class="setting-desc">游戏时播放轻松的背景音乐</div>
          </div>
          <label class="toggle-switch">
            <input type="checkbox" v-model="settingsStore.bgMusic">
            <span class="toggle-slider"></span>
          </label>
        </div>

        <!-- 音效 -->
        <div class="setting-item">
          <div class="setting-info">
            <div class="setting-name">游戏音效</div>
            <div class="setting-desc">按键、正确、通关等音效</div>
          </div>
          <label class="toggle-switch">
            <input type="checkbox" v-model="settingsStore.soundEffect">
            <span class="toggle-slider"></span>
          </label>
        </div>

        <!-- 震动反馈 -->
        <div class="setting-item">
          <div class="setting-info">
            <div class="setting-name">震动反馈</div>
            <div class="setting-desc">移动端按键震动反馈</div>
          </div>
          <label class="toggle-switch">
            <input type="checkbox" v-model="settingsStore.vibration">
            <span class="toggle-slider"></span>
          </label>
        </div>
      </div>

      <!-- 用户信息 -->
      <div class="settings-section">
        <div class="section-title">👤 用户信息</div>
        
        <div class="user-info-card">
          <div class="user-avatar">{{ userStore.avatar }}</div>
          <div class="user-details">
            <div class="user-nickname">{{ userStore.nickname || '未设置昵称' }}</div>
            <div class="user-id">ID: {{ userStore.id?.slice(0, 8) || '--' }}</div>
          </div>
          <button @click="showEditNickname = true" class="edit-btn">✏️</button>
        </div>

        <!-- 头像选择 -->
        <div class="avatar-selection">
          <div class="setting-name">选择头像</div>
          <div class="avatar-grid">
            <button 
              v-for="avatar in userStore.avatarOptions" 
              :key="avatar"
              :class="['avatar-btn', { active: userStore.avatar === avatar }]"
              @click="userStore.updateAvatar(avatar)"
            >
              {{ avatar }}
            </button>
          </div>
        </div>
      </div>

      <!-- 开发者选项（仅开发环境显示） -->
      <div v-if="showDevOptions" class="settings-section">
        <div class="section-title">🔧 开发者选项</div>
        
        <!-- Debug模式 -->
        <div class="setting-item">
          <div class="setting-info">
            <div class="setting-name">Debug模式</div>
            <div class="setting-desc">开启后可选择任意关卡（便于测试）</div>
          </div>
          <label class="toggle-switch">
            <input type="checkbox" v-model="debugMode" @change="saveDebugMode">
            <span class="toggle-slider"></span>
          </label>
        </div>
        
        <!-- 后台管理入口 -->
        <router-link to="/admin" class="setting-link-item">
          <div class="setting-info">
            <div class="setting-name">🛠️ 后台管理</div>
            <div class="setting-desc">数据统计与用户管理（需管理员密钥）</div>
          </div>
          <span class="link-arrow">›</span>
        </router-link>
      </div>

      <!-- 关于 -->
      <div class="settings-section">
        <div class="section-title">ℹ️ 关于</div>
        <div class="about-info">
          <div class="about-item">
            <span class="about-label">版本</span>
            <span class="about-value">v1.0.0</span>
          </div>
          <div class="about-item">
            <span class="about-label">词库数量</span>
            <span class="about-value">12 个</span>
          </div>
          <div class="about-item">
            <span class="about-label">音频词汇</span>
            <span class="about-value">23,000+</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 编辑昵称弹窗 -->
    <div v-if="showEditNickname" class="modal-overlay" @click.self="showEditNickname = false">
      <div class="modal-card animate-bounce-in">
        <h3 class="modal-title">✏️ 修改昵称</h3>
        <input 
          v-model="newNickname" 
          type="text" 
          class="nickname-input" 
          placeholder="请输入新昵称"
          maxlength="12"
        >
        <div class="modal-actions">
          <button @click="showEditNickname = false" class="cancel-btn">取消</button>
          <button @click="saveNickname" class="confirm-btn">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useSettingsStore } from '../stores/settings'
import { useUserStore } from '../stores/user'
import { useGameStore } from '../stores/game'

const router = useRouter()
const settingsStore = useSettingsStore()
const userStore = useUserStore()
const gameStore = useGameStore()

const showEditNickname = ref(false)
const newNickname = ref('')
const debugMode = ref(false)

// 是否显示开发者选项（根据环境变量控制）
const showDevOptions = import.meta.env.VITE_SHOW_DEV_OPTIONS === 'true'

// 加载debug模式设置
onMounted(() => {
  try {
    const saved = localStorage.getItem('game_debug_mode')
    debugMode.value = saved === 'true'
  } catch (e) {
    debugMode.value = false
  }
})

// 保存debug模式设置
function saveDebugMode() {
  try {
    localStorage.setItem('game_debug_mode', debugMode.value ? 'true' : 'false')
  } catch (e) {
    console.error('保存debug模式失败:', e)
  }
}

function goBack() {
  router.push('/')
}

function testSpeak() {
  gameStore.speakWord('hello', settingsStore.voiceType)
}

function saveNickname() {
  if (newNickname.value.trim()) {
    userStore.updateNickname(newNickname.value.trim())
  }
  showEditNickname.value = false
  newNickname.value = ''
}
</script>

<style scoped>
.settings-screen {
  min-height: 100vh;
  min-height: 100dvh;
  width: 100%;
  max-width: 100vw;
  padding: clamp(12px, 2vw, 24px);
  padding-bottom: clamp(30px, 5vw, 60px);
  box-sizing: border-box;
  margin: 0 auto;
  overflow-y: auto;
  overflow-x: hidden;
}

.settings-header {
  display: flex;
  align-items: center;
  gap: clamp(12px, 2vw, 20px);
  margin-bottom: clamp(16px, 3vw, 28px);
  width: 100%;
  box-sizing: border-box;
}

.back-btn {
  padding: 10px 16px;
  background: linear-gradient(180deg, #ffffff, #f1f5f9);
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  font-size: 0.9rem;
  font-weight: 700;
  color: #6b7280;
  cursor: pointer;
  box-shadow: 0 3px 0 #cbd5e1;
  transition: all 0.15s ease;
}

.back-btn:active {
  transform: translateY(2px);
  box-shadow: 0 1px 0 #cbd5e1;
}

.settings-title {
  font-size: var(--font-2xl, clamp(1.5rem, 4vw, 2.2rem));
  font-weight: 900;
  color: white;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  margin: 0;
}

.settings-card {
  background: rgba(255, 255, 255, 0.98);
  border-radius: clamp(18px, 3vw, 28px);
  padding: clamp(16px, 3vw, 28px);
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  box-shadow: 0 8px 0 rgba(0, 0, 0, 0.08), 0 15px 40px rgba(0, 0, 0, 0.12);
  border: clamp(2px, 0.4vw, 4px) solid rgba(255, 255, 255, 0.9);
  max-height: calc(100vh - 150px);
  max-height: calc(100dvh - 150px);
  overflow-y: auto;
  overflow-x: hidden;
  /* 自定义滚动条 */
  scrollbar-width: thin;
  scrollbar-color: #c4b5fd #f3f4f6;
}

.settings-card::-webkit-scrollbar {
  width: 6px;
}

.settings-card::-webkit-scrollbar-track {
  background: #f3f4f6;
  border-radius: 3px;
}

.settings-card::-webkit-scrollbar-thumb {
  background: #c4b5fd;
  border-radius: 3px;
}

.settings-card::-webkit-scrollbar-thumb:hover {
  background: #a78bfa;
}

.settings-section {
  margin-bottom: 24px;
}

.settings-section:last-child {
  margin-bottom: 0;
}

.section-title {
  font-size: var(--font-lg, clamp(1rem, 2.5vw, 1.3rem));
  font-weight: 800;
  color: #5b21b6;
  margin-bottom: clamp(12px, 2vw, 18px);
  padding-bottom: clamp(6px, 1vw, 12px);
  border-bottom: 2px dashed #e5e7eb;
}

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  background: linear-gradient(180deg, #f9fafb, #f3f4f6);
  border-radius: 14px;
  margin-bottom: 10px;
  border: 2px solid #e5e7eb;
}

.setting-link-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  background: linear-gradient(180deg, #f9fafb, #f3f4f6);
  border-radius: 14px;
  margin-bottom: 10px;
  border: 2px solid #e5e7eb;
  text-decoration: none;
  transition: all 0.15s ease;
}

.setting-link-item:active {
  transform: translateY(2px);
  box-shadow: 0 0 0 #d1d5db;
}

.link-arrow {
  font-size: 1.5rem;
  color: #9ca3af;
  font-weight: 300;
}

.setting-info {
  flex: 1;
}

.setting-name {
  font-size: var(--font-md, clamp(0.95rem, 2.2vw, 1.2rem));
  font-weight: 700;
  color: #374151;
  margin-bottom: 2px;
}

.setting-desc {
  font-size: var(--font-sm, clamp(0.8rem, 1.8vw, 1rem));
  color: #6b7280;
}

/* 开关样式 */
.toggle-switch {
  position: relative;
  width: 52px;
  height: 28px;
  cursor: pointer;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(180deg, #e5e7eb, #d1d5db);
  border-radius: 28px;
  border: 2px solid #9ca3af;
  transition: all 0.3s ease;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
}

.toggle-slider::before {
  content: '';
  position: absolute;
  width: 20px;
  height: 20px;
  left: 2px;
  bottom: 2px;
  background: white;
  border-radius: 50%;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.toggle-switch input:checked + .toggle-slider {
  background: linear-gradient(180deg, #a78bfa, #8b5cf6);
  border-color: #7c3aed;
}

.toggle-switch input:checked + .toggle-slider::before {
  transform: translateX(24px);
}

/* 发音类型切换 */
.voice-toggle {
  display: flex;
  gap: 8px;
}

.voice-btn {
  padding: 8px 14px;
  background: linear-gradient(180deg, #f3f4f6, #e5e7eb);
  border: 2px solid #d1d5db;
  border-radius: 10px;
  font-size: 0.8rem;
  font-weight: 700;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.15s ease;
  box-shadow: 0 2px 0 #9ca3af;
}

.voice-btn.active {
  background: linear-gradient(180deg, #dbeafe, #bfdbfe);
  border-color: #60a5fa;
  color: #1e40af;
  box-shadow: 0 2px 0 #3b82f6;
}

.voice-btn.active:last-child {
  background: linear-gradient(180deg, #fce7f3, #fbcfe8);
  border-color: #f472b6;
  color: #9d174d;
  box-shadow: 0 2px 0 #ec4899;
}

/* 测试发音 */
.setting-item.test-speak {
  justify-content: center;
  background: transparent;
  border: none;
  padding: 8px;
}

.test-btn {
  padding: 12px 24px;
  background: linear-gradient(180deg, #fef3c7, #fde68a);
  border: 2px solid #fbbf24;
  border-radius: 14px;
  font-size: 0.95rem;
  font-weight: 700;
  color: #92400e;
  cursor: pointer;
  box-shadow: 0 3px 0 #d97706;
  transition: all 0.15s ease;
}

.test-btn:active {
  transform: translateY(2px);
  box-shadow: 0 1px 0 #d97706;
}

/* 用户信息卡片 */
.user-info-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
  background: linear-gradient(180deg, #ede9fe, #ddd6fe);
  border-radius: 16px;
  border: 2px solid #c4b5fd;
  margin-bottom: 16px;
}

.user-avatar {
  font-size: 2.5rem;
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  border-radius: 50%;
  border: 3px solid #a78bfa;
  box-shadow: 0 3px 0 #8b5cf6;
}

.user-details {
  flex: 1;
}

.user-nickname {
  font-size: 1.1rem;
  font-weight: 800;
  color: #5b21b6;
}

.user-id {
  font-size: 0.75rem;
  color: #7c3aed;
  font-family: monospace;
}

.edit-btn {
  padding: 10px 14px;
  background: white;
  border: 2px solid #c4b5fd;
  border-radius: 10px;
  font-size: 1rem;
  cursor: pointer;
  box-shadow: 0 2px 0 #a78bfa;
  transition: all 0.15s ease;
}

.edit-btn:active {
  transform: translateY(2px);
  box-shadow: 0 0 0 #a78bfa;
}

/* 头像选择 */
.avatar-selection .setting-name {
  margin-bottom: 10px;
}

.avatar-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.avatar-btn {
  width: 48px;
  height: 48px;
  font-size: 1.5rem;
  background: linear-gradient(180deg, #f9fafb, #f3f4f6);
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.15s ease;
  box-shadow: 0 2px 0 #d1d5db;
}

.avatar-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 0 #d1d5db;
}

.avatar-btn.active {
  background: linear-gradient(180deg, #fef3c7, #fde68a);
  border-color: #fbbf24;
  box-shadow: 0 2px 0 #d97706;
}

/* 关于信息 */
.about-info {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.about-item {
  display: flex;
  justify-content: space-between;
  padding: 12px 16px;
  background: #f9fafb;
  border-radius: 12px;
}

.about-label {
  color: #6b7280;
  font-size: var(--font-md, clamp(1rem, 2.2vw, 1.2rem));
  font-weight: 600;
}

.about-value {
  color: #374151;
  font-weight: 700;
  font-size: var(--font-md, clamp(1rem, 2.2vw, 1.2rem));
}

/* 弹窗 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal-card {
  background: white;
  border-radius: 20px;
  padding: 24px;
  max-width: 320px;
  width: 90%;
  box-shadow: 0 8px 0 rgba(0, 0, 0, 0.1), 0 15px 40px rgba(0, 0, 0, 0.2);
}

.modal-title {
  font-size: 1.2rem;
  font-weight: 800;
  color: #5b21b6;
  text-align: center;
  margin: 0 0 16px;
}

.nickname-input {
  width: 100%;
  padding: 14px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 16px;
  box-sizing: border-box;
}

.nickname-input:focus {
  outline: none;
  border-color: #8b5cf6;
}

.modal-actions {
  display: flex;
  gap: 12px;
}

.cancel-btn, .confirm-btn {
  flex: 1;
  padding: 12px;
  border-radius: 12px;
  font-size: 0.95rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s ease;
}

.cancel-btn {
  background: linear-gradient(180deg, #f3f4f6, #e5e7eb);
  border: 2px solid #d1d5db;
  color: #6b7280;
  box-shadow: 0 3px 0 #9ca3af;
}

.confirm-btn {
  background: linear-gradient(180deg, #a78bfa, #8b5cf6);
  border: 2px solid #7c3aed;
  color: white;
  box-shadow: 0 3px 0 #5b21b6;
}

.cancel-btn:active, .confirm-btn:active {
  transform: translateY(2px);
  box-shadow: 0 1px 0;
}

.animate-bounce-in {
  animation: bounceIn 0.3s ease-out;
}

@keyframes bounceIn {
  0% { transform: scale(0.8); opacity: 0; }
  70% { transform: scale(1.02); }
  100% { transform: scale(1); opacity: 1; }
}
</style>
