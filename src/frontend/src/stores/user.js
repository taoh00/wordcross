import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { userApi } from '../api/client.js'

export const useUserStore = defineStore('user', () => {
  // 用户状态
  const id = ref('')
  const nickname = ref('')
  const avatar = ref('😊')
  const createdAt = ref('')
  const loading = ref(false)

  // 可选头像列表
  const avatarOptions = ['😊', '😎', '🤓', '😺', '🐶', '🦊', '🐰', '🐼', '🦄', '🌟']

  // 是否已注册
  const isRegistered = computed(() => {
    return !!nickname.value && nickname.value.trim().length > 0
  })

  // 从 localStorage 加载用户信息（作为备份缓存）
  function loadUserFromLocal() {
    try {
      const saved = localStorage.getItem('game_user')
      if (saved) {
        const user = JSON.parse(saved)
        id.value = user.id || ''
        nickname.value = user.nickname || ''
        avatar.value = user.avatar || '😊'
        createdAt.value = user.createdAt || user.created_at || ''
        return true
      }
    } catch (e) {
      console.warn('加载本地用户信息失败:', e)
    }
    return false
  }

  // 保存用户信息到本地（作为缓存）
  function saveUserToLocal() {
    try {
      const user = {
        id: id.value,
        nickname: nickname.value,
        avatar: avatar.value,
        createdAt: createdAt.value
      }
      localStorage.setItem('game_user', JSON.stringify(user))
    } catch (e) {
      console.warn('保存本地用户信息失败:', e)
    }
  }

  // 从后端加载用户信息（通过cookie）
  async function loadUser() {
    loading.value = true
    try {
      const data = await userApi.getInfo()
      
      if (data.registered) {
        id.value = data.id
        nickname.value = data.nickname
        avatar.value = data.avatar || '😊'
        createdAt.value = data.created_at || ''
        saveUserToLocal()  // 缓存到本地
        loading.value = false
        return true
      }
    } catch (e) {
      console.warn('从后端加载用户信息失败，尝试本地缓存:', e)
    }
    
    // 后端加载失败，尝试从本地加载
    const hasLocal = loadUserFromLocal()
    loading.value = false
    return hasLocal
  }

  // 注册用户（调用后端API，后端生成ID）
  async function register(name, selectedAvatar = '😊') {
    loading.value = true
    try {
      const data = await userApi.register(name.trim(), selectedAvatar)
      
      // 后端返回用户信息（包含生成的ID）
      id.value = data.id
      nickname.value = data.nickname
      avatar.value = data.avatar
      createdAt.value = data.created_at
      
      // 缓存到本地
      saveUserToLocal()
      loading.value = false
      return true
    } catch (e) {
      console.warn('注册失败，使用本地生成ID:', e)
      // 后端注册失败时，回退到本地生成ID
      id.value = generateUUID()
      nickname.value = name.trim()
      avatar.value = selectedAvatar
      createdAt.value = new Date().toISOString()
      saveUserToLocal()
      loading.value = false
      return true
    }
  }

  // 更新头像
  async function updateAvatar(newAvatar) {
    avatar.value = newAvatar
    saveUserToLocal()
    
    // 尝试同步到后端
    try {
      await userApi.update(nickname.value, newAvatar)
    } catch (e) {
      console.warn('同步头像到后端失败:', e)
    }
  }

  // 更新昵称
  async function updateNickname(newName) {
    nickname.value = newName.trim()
    saveUserToLocal()
    
    // 尝试同步到后端
    try {
      await userApi.update(newName.trim(), avatar.value)
    } catch (e) {
      console.warn('同步昵称到后端失败:', e)
    }
  }

  // 退出登录
  async function logout() {
    try {
      await userApi.logout()
    } catch (e) {
      console.warn('退出登录API调用失败:', e)
    }
    
    // 清除本地数据
    id.value = ''
    nickname.value = ''
    avatar.value = '😊'
    createdAt.value = ''
    localStorage.removeItem('game_user')
  }

  // 生成 UUID（作为回退方案）
  function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0
      const v = c === 'x' ? r : (r & 0x3 | 0x8)
      return v.toString(16)
    })
  }

  // 初始化时先从本地缓存加载（快速恢复状态）
  loadUserFromLocal()

  return {
    id,
    nickname,
    avatar,
    createdAt,
    loading,
    avatarOptions,
    isRegistered,
    loadUser,
    register,
    updateAvatar,
    updateNickname,
    logout
  }
})
