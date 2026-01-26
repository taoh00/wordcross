/**
 * 网络请求封装
 * 使用 wx.request 实现，支持 X-User-Id 认证
 */

const app = getApp()

/**
 * 发起网络请求
 * @param {Object} options 请求选项
 * @param {string} options.url 请求路径（不含基础URL）
 * @param {string} options.method 请求方法
 * @param {Object} options.data 请求数据
 * @param {Object} options.header 额外请求头
 * @returns {Promise} 响应数据
 */
function request(options) {
  return new Promise((resolve, reject) => {
    const globalData = app?.globalData || {}
    const baseUrl = globalData.apiBase || 'https://superhe.art:10010'
    const userId = globalData.userId || ''
    
    wx.request({
      url: baseUrl + options.url,
      method: options.method || 'GET',
      data: options.data,
      header: {
        'Content-Type': 'application/json',
        'X-User-Id': userId,
        ...(options.header || {}),
      },
      timeout: options.timeout || 30000,
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data)
        } else if (res.statusCode === 401) {
          console.warn('认证失败，尝试重新登录')
          // 触发重新登录
          if (app && app.silentLogin) {
            app.silentLogin()
          }
          reject(new Error('认证失败'))
        } else {
          const errorMsg = res.data?.detail || res.data?.message || '请求失败'
          reject(new Error(errorMsg))
        }
      },
      fail: (err) => {
        console.error('网络请求失败:', err)
        reject(new Error(err.errMsg || '网络错误'))
      },
    })
  })
}

/**
 * GET 请求
 */
function get(url, data = {}) {
  return request({ url, method: 'GET', data })
}

/**
 * POST 请求
 */
function post(url, data = {}) {
  return request({ url, method: 'POST', data })
}

/**
 * PUT 请求
 */
function put(url, data = {}) {
  return request({ url, method: 'PUT', data })
}

/**
 * DELETE 请求
 */
function del(url, data = {}) {
  return request({ url, method: 'DELETE', data })
}

module.exports = {
  request,
  get,
  post,
  put,
  del,
}
