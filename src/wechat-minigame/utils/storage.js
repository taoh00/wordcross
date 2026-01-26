/**
 * 本地存储封装
 * 使用 wx.setStorageSync / wx.getStorageSync
 */

const storage = {
  /**
   * 获取存储值
   * @param {string} key 键名
   * @returns {*} 存储的值，不存在返回 null
   */
  get(key) {
    try {
      const value = wx.getStorageSync(key)
      return value || null
    } catch (e) {
      console.error('读取存储失败:', key, e)
      return null
    }
  },

  /**
   * 设置存储值
   * @param {string} key 键名
   * @param {*} value 值
   * @returns {boolean} 是否成功
   */
  set(key, value) {
    try {
      wx.setStorageSync(key, value)
      return true
    } catch (e) {
      console.error('写入存储失败:', key, e)
      return false
    }
  },

  /**
   * 删除存储值
   * @param {string} key 键名
   * @returns {boolean} 是否成功
   */
  remove(key) {
    try {
      wx.removeStorageSync(key)
      return true
    } catch (e) {
      console.error('删除存储失败:', key, e)
      return false
    }
  },

  /**
   * 清空所有存储
   * @returns {boolean} 是否成功
   */
  clear() {
    try {
      wx.clearStorageSync()
      return true
    } catch (e) {
      console.error('清空存储失败:', e)
      return false
    }
  },

  /**
   * 获取存储信息
   * @returns {Object} 存储信息
   */
  getInfo() {
    try {
      return wx.getStorageInfoSync()
    } catch (e) {
      console.error('获取存储信息失败:', e)
      return { keys: [], currentSize: 0, limitSize: 0 }
    }
  },
}

module.exports = {
  storage,
}
