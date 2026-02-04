/**
 * 微信小游戏自动化截图对比脚本
 * 
 * 使用方法：
 * 1. 确保微信开发者工具已安装且在安全设置中开启了 CLI/HTTP 调用功能
 * 2. 安装依赖：npm install miniprogram-automator
 * 3. 运行：node screenshot-compare.js
 * 
 * 功能：
 * - 自动启动微信开发者工具
 * - 遍历小游戏各个界面并截图
 * - 保存截图到 screenshots/ 目录
 */

const automator = require('miniprogram-automator')
const path = require('path')
const fs = require('fs')

// 配置
const CONFIG = {
  // 微信开发者工具CLI路径（Mac默认路径）
  cliPath: '/Applications/wechatwebdevtools.app/Contents/MacOS/cli',
  // 小游戏项目路径
  projectPath: path.resolve(__dirname, '..'),
  // 截图保存目录
  screenshotDir: path.resolve(__dirname, 'screenshots'),
  // 截图等待时间（毫秒）
  waitTime: 2000
}

// 确保截图目录存在
if (!fs.existsSync(CONFIG.screenshotDir)) {
  fs.mkdirSync(CONFIG.screenshotDir, { recursive: true })
}

// 截图场景列表
const SCENES = [
  { name: '01-首页-模式选择', action: null },
  { name: '02-闯关-词库选择', action: 'clickCampaign' },
  { name: '03-闯关-子分组选择', action: 'clickPrimaryGroup' },
  { name: '04-闯关-关卡选择', action: 'clickSubgroup' },
  { name: '05-设置页', action: 'clickSettings' },
  { name: '06-排行榜', action: 'clickLeaderboard' },
  { name: '07-计时模式-时间选择', action: 'clickTimed' },
  { name: '08-无限模式-难度选择', action: 'clickEndless' }
]

/**
 * 主函数
 */
async function main() {
  console.log('🚀 启动微信开发者工具...')
  
  let miniProgram = null
  
  try {
    // 启动开发者工具
    miniProgram = await automator.launch({
      cliPath: CONFIG.cliPath,
      projectPath: CONFIG.projectPath
    })
    
    console.log('✅ 微信开发者工具已启动')
    
    // 等待小游戏加载
    await sleep(3000)
    
    // 截取首页
    await takeScreenshot(miniProgram, '01-首页-模式选择')
    
    // 模拟点击闯关模式并截图
    await simulateClick(miniProgram, 100, 300)  // 闯关模式按钮位置
    await sleep(CONFIG.waitTime)
    await takeScreenshot(miniProgram, '02-闯关-词库选择')
    
    // 点击小学词库
    await simulateClick(miniProgram, 60, 200)
    await sleep(CONFIG.waitTime)
    await takeScreenshot(miniProgram, '03-闯关-子分组选择')
    
    // 点击全部子分组
    await simulateClick(miniProgram, 60, 200)
    await sleep(CONFIG.waitTime)
    await takeScreenshot(miniProgram, '04-闯关-关卡选择')
    
    // 返回首页
    await simulateClick(miniProgram, 50, 50)  // 返回按钮
    await sleep(500)
    await simulateClick(miniProgram, 50, 50)
    await sleep(500)
    await simulateClick(miniProgram, 50, 50)
    await sleep(500)
    await simulateClick(miniProgram, 50, 50)
    await sleep(CONFIG.waitTime)
    
    // 点击设置
    await simulateClick(miniProgram, 200, 520)  // 设置按钮
    await sleep(CONFIG.waitTime)
    await takeScreenshot(miniProgram, '05-设置页')
    
    // 返回首页
    await simulateClick(miniProgram, 50, 50)
    await sleep(CONFIG.waitTime)
    
    // 点击排行榜
    await simulateClick(miniProgram, 280, 380)  // 排行榜按钮
    await sleep(CONFIG.waitTime)
    await takeScreenshot(miniProgram, '06-排行榜')
    
    // 返回首页
    await simulateClick(miniProgram, 50, 50)
    await sleep(CONFIG.waitTime)
    
    // 点击计时模式
    await simulateClick(miniProgram, 100, 380)  // 计时模式按钮
    await sleep(CONFIG.waitTime)
    await takeScreenshot(miniProgram, '07-计时模式-时间选择')
    
    // 返回首页
    await simulateClick(miniProgram, 50, 50)
    await sleep(CONFIG.waitTime)
    
    // 点击无限模式
    await simulateClick(miniProgram, 280, 300)  // 无限模式按钮
    await sleep(CONFIG.waitTime)
    await takeScreenshot(miniProgram, '08-无限模式-难度选择')
    
    console.log('\n✅ 所有截图完成！')
    console.log(`📁 截图保存在: ${CONFIG.screenshotDir}`)
    
  } catch (error) {
    console.error('❌ 错误:', error.message)
    console.error(error.stack)
  } finally {
    if (miniProgram) {
      await miniProgram.close()
      console.log('🔒 已关闭开发者工具')
    }
  }
}

/**
 * 截图
 */
async function takeScreenshot(miniProgram, name) {
  const filename = `${name}.png`
  const filepath = path.join(CONFIG.screenshotDir, filename)
  
  try {
    await miniProgram.screenshot({ path: filepath })
    console.log(`📸 截图成功: ${filename}`)
  } catch (error) {
    console.error(`❌ 截图失败 ${name}:`, error.message)
  }
}

/**
 * 模拟点击
 * 注意：小游戏使用Canvas，需要通过evaluate来触发touch事件
 */
async function simulateClick(miniProgram, x, y) {
  try {
    await miniProgram.evaluate((x, y) => {
      // 创建并派发触摸事件
      const canvas = GameGlobal.canvas
      if (canvas) {
        const touch = {
          identifier: 0,
          clientX: x,
          clientY: y,
          pageX: x,
          pageY: y
        }
        
        // touchstart
        const startEvent = {
          type: 'touchstart',
          touches: [touch],
          changedTouches: [touch],
          timeStamp: Date.now()
        }
        canvas.dispatchEvent && canvas.dispatchEvent('touchstart', startEvent)
        
        // touchend
        setTimeout(() => {
          const endEvent = {
            type: 'touchend',
            touches: [],
            changedTouches: [touch],
            timeStamp: Date.now()
          }
          canvas.dispatchEvent && canvas.dispatchEvent('touchend', endEvent)
        }, 50)
      }
    }, x, y)
  } catch (error) {
    console.log(`⚠️ 点击模拟失败 (${x}, ${y}):`, error.message)
  }
}

/**
 * 延时
 */
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

// 运行
main()
