<template>
  <div class="terminal-wrapper">
    <!-- 工具栏 -->
    <div class="terminal-toolbar">
      <div class="toolbar-left">
        <div class="status-indicator">
          <span
            class="status-dot"
            :class="statusClass"
          />
          <span class="status-text">{{ statusText }}</span>
        </div>
      </div>
      <div class="toolbar-center">
        <el-button-group size="small">
          <el-tooltip
            content="清屏"
            placement="top"
          >
            <el-button
              :disabled="!connected"
              @click="clearTerminal"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </el-tooltip>
          <el-tooltip
            content="字体变小"
            placement="top"
          >
            <el-button
              :disabled="!connected"
              @click="decreaseFontSize"
            >
              <el-icon><Minus /></el-icon>
            </el-button>
          </el-tooltip>
          <el-tooltip
            content="字体变大"
            placement="top"
          >
            <el-button
              :disabled="!connected"
              @click="increaseFontSize"
            >
              <el-icon><Plus /></el-icon>
            </el-button>
          </el-tooltip>
          <el-tooltip
            content="重置字体"
            placement="top"
          >
            <el-button
              :disabled="!connected"
              @click="resetFontSize"
            >
              <el-icon><Refresh /></el-icon>
            </el-button>
          </el-tooltip>
        </el-button-group>
      </div>
      <div class="toolbar-right">
        <el-tag
          v-if="connected"
          type="success"
          size="small"
          effect="dark"
        >
          <el-icon class="tag-icon">
            <Monitor />
          </el-icon>
          {{ fontSize }}px
        </el-tag>
        <el-button
          v-if="connected"
          type="danger"
          size="small"
          plain
          @click="disconnect"
        >
          <el-icon><CircleClose /></el-icon>
          断开
        </el-button>
      </div>
    </div>
    
    <!-- 终端容器 -->
    <div
      ref="terminalRef"
      class="terminal-container"
    />
    
    <!-- 未连接遮罩 -->
    <div
      v-if="!connected && !connecting && !error"
      class="terminal-overlay"
    >
      <div class="overlay-content">
        <div class="overlay-icon-wrapper">
          <el-icon
            :size="64"
            class="terminal-icon"
          >
            <Monitor />
          </el-icon>
        </div>
        <h3 class="overlay-title">
          SSH 终端
        </h3>
        <p class="overlay-desc">
          点击下方按钮连接到远程服务器
        </p>
        <el-button
          type="primary"
          size="large"
          class="connect-button"
          @click="connect"
        >
          <el-icon><Connection /></el-icon>
          连接终端
        </el-button>
      </div>
    </div>
    
    <!-- 连接中遮罩 -->
    <div
      v-if="connecting"
      class="terminal-overlay connecting-overlay"
    >
      <div class="overlay-content">
        <div class="connecting-animation">
          <div class="pulse-ring" />
          <el-icon
            :size="48"
            class="loading-icon"
          >
            <Loading />
          </el-icon>
        </div>
        <h3 class="overlay-title">
          正在连接
        </h3>
        <p class="overlay-desc">
          请稍候，正在建立SSH连接...
        </p>
      </div>
    </div>
    
    <!-- 错误遮罩 -->
    <div
      v-if="error"
      class="terminal-overlay error-overlay"
    >
      <div class="overlay-content">
        <div class="overlay-icon-wrapper error">
          <el-icon
            :size="64"
            class="error-icon"
          >
            <CircleClose />
          </el-icon>
        </div>
        <h3 class="overlay-title error-title">
          连接失败
        </h3>
        <p class="overlay-desc error-desc">
          {{ error }}
        </p>
        <el-button
          type="primary"
          size="large"
          class="connect-button"
          @click="connect"
        >
          <el-icon><Refresh /></el-icon>
          重新连接
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { Terminal } from 'xterm'
import { FitAddon } from 'xterm-addon-fit'
import { WebLinksAddon } from 'xterm-addon-web-links'
import { io } from 'socket.io-client'
import { Monitor, Connection, Loading, CircleClose, Delete, Plus, Minus, Refresh } from '@element-plus/icons-vue'
import 'xterm/css/xterm.css'

const props = defineProps({
  server: {
    type: Object,
    required: true
  },
  visible: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['connected', 'disconnected', 'error'])

const terminalRef = ref(null)
const connected = ref(false)
const connecting = ref(false)
const error = ref('')
const fontSize = ref(14)

const DEFAULT_FONT_SIZE = 14
const MIN_FONT_SIZE = 10
const MAX_FONT_SIZE = 24

// 状态指示器
const statusClass = computed(() => {
  if (connected.value) return 'connected'
  if (connecting.value) return 'connecting'
  if (error.value) return 'error'
  return 'disconnected'
})

const statusText = computed(() => {
  if (connected.value) return '已连接'
  if (connecting.value) return '连接中...'
  if (error.value) return '连接失败'
  return '未连接'
})

// 终端配置常量
const TERMINAL_FONT_FAMILY = '"Cascadia Code", "Fira Code", Monaco, Menlo, Consolas, "Liberation Mono", monospace'

let terminal = null
let fitAddon = null
let socket = null
let resizeObserver = null

const initTerminal = () => {
  if (!terminalRef.value || terminal) return

  terminal = new Terminal({
    cursorBlink: true,
    cursorStyle: 'block',
    fontSize: fontSize.value,
    fontFamily: TERMINAL_FONT_FAMILY,
    fontWeight: '400',
    fontWeightBold: '700',
    letterSpacing: 0,
    lineHeight: 1.2,
    theme: {
      background: '#0d1117',
      foreground: '#c9d1d9',
      cursor: '#58a6ff',
      cursorAccent: '#0d1117',
      selection: 'rgba(56, 139, 253, 0.4)',
      black: '#484f58',
      red: '#ff7b72',
      green: '#3fb950',
      yellow: '#d29922',
      blue: '#58a6ff',
      magenta: '#bc8cff',
      cyan: '#39c5cf',
      white: '#b1bac4',
      brightBlack: '#6e7681',
      brightRed: '#ffa198',
      brightGreen: '#56d364',
      brightYellow: '#e3b341',
      brightBlue: '#79c0ff',
      brightMagenta: '#d2a8ff',
      brightCyan: '#56d4dd',
      brightWhite: '#f0f6fc'
    },
    scrollback: 5000,
    tabStopWidth: 4,
    allowTransparency: true,
    convertEol: true
  })

  fitAddon = new FitAddon()
  terminal.loadAddon(fitAddon)
  terminal.loadAddon(new WebLinksAddon())

  terminal.open(terminalRef.value)

  // 发送输入到服务器
  terminal.onData((data) => {
    if (socket && connected.value) {
      socket.emit('terminal_input', { data })
    }
  })

  // 监听终端大小变化
  resizeObserver = new ResizeObserver(() => {
    if (fitAddon && terminal) {
      try {
        fitAddon.fit()
        if (socket && connected.value) {
          socket.emit('terminal_resize', {
            cols: terminal.cols,
            rows: terminal.rows
          })
        }
      } catch (e) {
        // Resize errors are non-critical, log for debugging
        if (import.meta.env.DEV) {
          // eslint-disable-next-line no-console
          console.warn('Terminal resize error:', e)
        }
      }
    }
  })
  resizeObserver.observe(terminalRef.value)

  nextTick(() => {
    try {
      fitAddon.fit()
    } catch (e) {
      // Initial fit errors are non-critical
      if (import.meta.env.DEV) {
        // eslint-disable-next-line no-console
        console.warn('Terminal initial fit error:', e)
      }
    }
  })
}

const connect = () => {
  if (connecting.value || connected.value) return

  connecting.value = true
  error.value = ''

  const token = localStorage.getItem('token')
  if (!token) {
    error.value = '请先登录'
    connecting.value = false
    return
  }

  // 获取WebSocket URL
  // 优先使用 VITE_WS_URL 环境变量
  // 如果未设置，则从 VITE_API_BASE_URL 推断后端地址
  // 最后回退到 window.location.origin
  let wsUrl = import.meta.env.VITE_WS_URL
  if (!wsUrl) {
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL
    if (apiBaseUrl && apiBaseUrl.startsWith('http')) {
      // 从 API URL 中提取基础URL（去掉/api路径）
      try {
        const url = new URL(apiBaseUrl)
        wsUrl = url.origin
      } catch (_e) {
        wsUrl = window.location.origin
      }
    } else {
      wsUrl = window.location.origin
    }
  }

  socket = io(`${wsUrl}/terminal`, {
    transports: ['polling', 'websocket'],
    reconnection: true,
    reconnectionAttempts: 3,
    reconnectionDelay: 1000,
    timeout: 20000,
    upgrade: true
  })

  socket.on('connect', () => {
    // 发送启动终端请求
    socket.emit('start_terminal', {
      server_id: props.server.id,
      token: token
    })
  })

  socket.on('terminal_connected', (data) => {
    connecting.value = false
    connected.value = true
    error.value = ''
    terminal.writeln(`\r\n\x1b[32m${data.message}\x1b[0m\r\n`)
    emit('connected')

    // 发送终端大小
    if (terminal) {
      socket.emit('terminal_resize', {
        cols: terminal.cols,
        rows: terminal.rows
      })
    }
  })

  socket.on('terminal_output', (data) => {
    if (terminal && data.data) {
      terminal.write(data.data)
    }
  })

  socket.on('terminal_error', (data) => {
    connecting.value = false
    connected.value = false
    error.value = data.message || '连接失败'
    emit('error', error.value)
  })

  socket.on('terminal_disconnected', () => {
    connecting.value = false
    connected.value = false
    terminal.writeln('\r\n\x1b[31m连接已断开\x1b[0m')
    emit('disconnected')
  })

  socket.on('disconnect', () => {
    if (connected.value) {
      connected.value = false
      terminal.writeln('\r\n\x1b[31m连接已断开\x1b[0m')
      emit('disconnected')
    }
    connecting.value = false
  })

  socket.on('connect_error', () => {
    connecting.value = false
    error.value = '无法连接到服务器'
    emit('error', error.value)
  })
}

const disconnect = () => {
  if (socket) {
    socket.emit('stop_terminal')
    socket.disconnect()
    socket = null
  }
  connected.value = false
  connecting.value = false
}

// 终端工具函数
const clearTerminal = () => {
  if (terminal) {
    terminal.clear()
    terminal.write('\x1b[2J\x1b[H')
  }
}

const increaseFontSize = () => {
  if (fontSize.value < MAX_FONT_SIZE) {
    fontSize.value += 1
    updateFontSize()
  }
}

const decreaseFontSize = () => {
  if (fontSize.value > MIN_FONT_SIZE) {
    fontSize.value -= 1
    updateFontSize()
  }
}

const resetFontSize = () => {
  fontSize.value = DEFAULT_FONT_SIZE
  updateFontSize()
}

const updateFontSize = () => {
  if (terminal) {
    terminal.options.fontSize = fontSize.value
    if (fitAddon) {
      nextTick(() => {
        try {
          fitAddon.fit()
          if (socket && connected.value) {
            socket.emit('terminal_resize', {
              cols: terminal.cols,
              rows: terminal.rows
            })
          }
        } catch (e) {
          if (import.meta.env.DEV) {
            // eslint-disable-next-line no-console
            console.warn(`Terminal font resize failed (fontSize: ${fontSize.value}px):`, e.message || e)
          }
        }
      })
    }
  }
}

// 监听visible变化，初始化终端
watch(() => props.visible, (newVal) => {
  if (newVal) {
    nextTick(() => {
      initTerminal()
    })
  }
})

onMounted(() => {
  if (props.visible) {
    nextTick(() => {
      initTerminal()
    })
  }
})

onUnmounted(() => {
  disconnect()
  if (resizeObserver) {
    resizeObserver.disconnect()
  }
  if (terminal) {
    terminal.dispose()
    terminal = null
  }
})

// 暴露方法给父组件
defineExpose({
  connect,
  disconnect
})
</script>

<style scoped>
.terminal-wrapper {
  position: relative;
  width: 100%;
  height: 550px;
  background: #0d1117;
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  border: 1px solid #30363d;
}

/* 工具栏样式 */
.terminal-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background: linear-gradient(180deg, #161b22 0%, #0d1117 100%);
  border-bottom: 1px solid #30363d;
  min-height: 44px;
  gap: 12px;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toolbar-center {
  display: flex;
  align-items: center;
  justify-content: center;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  transition: all 0.3s ease;
}

.status-dot.connected {
  background: #3fb950;
  box-shadow: 0 0 8px rgba(63, 185, 80, 0.6);
  animation: pulse-green 2s infinite;
}

.status-dot.connecting {
  background: #d29922;
  box-shadow: 0 0 8px rgba(210, 153, 34, 0.6);
  animation: pulse-yellow 1s infinite;
}

.status-dot.error {
  background: #f85149;
  box-shadow: 0 0 8px rgba(248, 81, 73, 0.6);
}

.status-dot.disconnected {
  background: #484f58;
}

.status-text {
  font-size: 13px;
  color: #8b949e;
  font-weight: 500;
}

.tag-icon {
  margin-right: 4px;
  vertical-align: middle;
}

@keyframes pulse-green {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

@keyframes pulse-yellow {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.8; transform: scale(1.1); }
}

/* 工具栏按钮样式 */
.toolbar-center :deep(.el-button-group .el-button) {
  background: #21262d;
  border-color: #30363d;
  color: #8b949e;
}

.toolbar-center :deep(.el-button-group .el-button:hover:not(:disabled)) {
  background: #30363d;
  border-color: #58a6ff;
  color: #58a6ff;
}

.toolbar-center :deep(.el-button-group .el-button:disabled) {
  background: #161b22;
  border-color: #21262d;
  color: #484f58;
  cursor: not-allowed;
}

/* 终端容器 */
.terminal-container {
  flex: 1;
  width: 100%;
  padding: 12px 16px;
  box-sizing: border-box;
  overflow: hidden;
}

/* 遮罩层样式 */
.terminal-overlay {
  position: absolute;
  top: 44px;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.connecting-overlay {
  background: linear-gradient(135deg, #0d1117 0%, #1a2332 100%);
}

.error-overlay {
  background: linear-gradient(135deg, #0d1117 0%, #21141a 100%);
}

.overlay-content {
  text-align: center;
  color: #c9d1d9;
  padding: 24px;
}

.overlay-icon-wrapper {
  width: 120px;
  height: 120px;
  margin: 0 auto 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #21262d 0%, #161b22 100%);
  border-radius: 50%;
  border: 2px solid #30363d;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

.overlay-icon-wrapper.error {
  border-color: #f85149;
  background: linear-gradient(135deg, #21141a 0%, #1a0f14 100%);
}

.overlay-title {
  font-size: 22px;
  font-weight: 600;
  margin: 0 0 12px;
  color: #f0f6fc;
}

.error-title {
  color: #f85149;
}

.overlay-desc {
  font-size: 14px;
  color: #8b949e;
  margin: 0 0 24px;
  line-height: 1.5;
}

.error-desc {
  color: #ffa198;
}

.connect-button {
  min-width: 140px;
  height: 44px;
  font-size: 15px;
  font-weight: 500;
  border-radius: 8px;
  background: linear-gradient(135deg, #238636 0%, #2ea043 100%);
  border: none;
  box-shadow: 0 4px 16px rgba(46, 160, 67, 0.3);
  transition: all 0.3s ease;
}

.connect-button:hover {
  background: linear-gradient(135deg, #2ea043 0%, #3fb950 100%);
  box-shadow: 0 6px 20px rgba(46, 160, 67, 0.4);
  transform: translateY(-2px);
}

/* 连接动画 */
.connecting-animation {
  position: relative;
  width: 100px;
  height: 100px;
  margin: 0 auto 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pulse-ring {
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  border: 3px solid #58a6ff;
  animation: pulse-ring 1.5s ease-out infinite;
}

@keyframes pulse-ring {
  0% {
    transform: scale(0.5);
    opacity: 1;
  }
  100% {
    transform: scale(1.2);
    opacity: 0;
  }
}

.terminal-icon {
  color: #3fb950;
}

.loading-icon {
  color: #58a6ff;
  animation: spin 1s linear infinite;
}

.error-icon {
  color: #f85149;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* xterm样式覆盖 */
:deep(.xterm) {
  padding: 0;
  height: 100%;
}

:deep(.xterm-viewport) {
  overflow-y: auto !important;
}

:deep(.xterm-viewport::-webkit-scrollbar) {
  width: 10px;
}

:deep(.xterm-viewport::-webkit-scrollbar-track) {
  background: #161b22;
}

:deep(.xterm-viewport::-webkit-scrollbar-thumb) {
  background: #30363d;
  border-radius: 5px;
}

:deep(.xterm-viewport::-webkit-scrollbar-thumb:hover) {
  background: #484f58;
}

/* 减少动效偏好 */
@media (prefers-reduced-motion: reduce) {
  .status-dot.connected,
  .status-dot.connecting,
  .pulse-ring,
  .loading-icon {
    animation: none;
  }
}
</style>
