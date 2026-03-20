<template>
  <div class="page-container">
    <el-container>
      <el-header class="header-container">
        <div class="header-logo">
          <el-icon :size="30">
            <Monitor />
          </el-icon>
          <h2>服务器管理</h2>
        </div>
        <el-menu
          mode="horizontal"
          :default-active="activeMenu"
          background-color="transparent"
          text-color="#fff"
          active-text-color="#fff"
          class="header-menu"
          @select="handleMenuSelect"
        >
          <el-menu-item index="/dashboard">
            <el-icon><Odometer /></el-icon>
            仪表盘
          </el-menu-item>
          <el-menu-item index="/servers">
            <el-icon><OfficeBuilding /></el-icon>
            服务器
          </el-menu-item>
          <el-sub-menu index="main-program">
            <template #title>
              <el-icon><Setting /></el-icon>
              主程序功能
            </template>
            <el-menu-item index="/information-query">
              <el-icon><Search /></el-icon>
              信息查询
            </el-menu-item>
            <el-menu-item index="/system-backup">
              <el-icon><FolderOpened /></el-icon>
              系统备份
            </el-menu-item>
            <el-menu-item index="/system-settings">
              <el-icon><Tools /></el-icon>
              系统设置
            </el-menu-item>
          </el-sub-menu>
        </el-menu>
        <el-dropdown @command="handleCommand">
          <span class="user-dropdown">
            <el-icon><User /></el-icon>
            {{ currentUser?.username || '管理员' }}
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="changePassword">
                修改密码
              </el-dropdown-item>
              <el-dropdown-item command="logout">
                退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>
      
      <el-main>
        <div class="content-wrapper">
          <el-card class="server-card">
            <template #header>
              <div class="card-header">
                <span class="card-title">🖥️ 服务器列表</span>
                <div class="header-actions">
                  <el-button
                    type="success"
                    :loading="importing"
                    @click="importServersFromFiles"
                  >
                    <el-icon><Download /></el-icon>
                    获取服务器
                  </el-button>
                  <el-button
                    type="primary"
                    @click="showAddDialog"
                  >
                    <el-icon><Plus /></el-icon>
                    新增服务器
                  </el-button>
                  <el-button @click="loadServers">
                    <el-icon><Refresh /></el-icon>
                    刷新
                  </el-button>
                </div>
              </div>
            </template>
            
            <div class="search-filter-row">
              <el-input
                v-model="searchText"
                placeholder="按IP、用户名或备注搜索"
                class="search-input"
                :prefix-icon="Search"
                clearable
              />
              
              <div class="filter-buttons">
                <el-button
                  type="success"
                  @click="showFilteredServersDialog('normal')"
                >
                  <el-icon><CircleCheck /></el-icon>
                  正常 {{ normalCount }}
                </el-button>
                <el-button
                  type="danger"
                  @click="showFilteredServersDialog('offline')"
                >
                  <el-icon><CircleClose /></el-icon>
                  离线 {{ offlineCount }}
                </el-button>
                <el-button
                  type="info"
                  @click="showFilteredServersDialog('unknown')"
                >
                  <el-icon><QuestionFilled /></el-icon>
                  未知 {{ unknownCount }}
                </el-button>
                <el-button
                  type="warning"
                  @click="showFilteredServersDialog('error')"
                >
                  <el-icon><WarningFilled /></el-icon>
                  错误 {{ errorCount }}
                </el-button>
                <el-button
                  type="primary"
                  @click="showFilteredServersDialog('computer')"
                >
                  <el-icon><Monitor /></el-icon>
                  电脑 {{ computerCount }}
                </el-button>
                <el-button
                  color="#10b981"
                  @click="showFilteredServersDialog('batch_online')"
                >
                  <el-icon><Promotion /></el-icon>
                  一键查询在线 {{ batchOnlineCount }}
                </el-button>
                <el-button
                  color="#f43f5e"
                  @click="showFilteredServersDialog('batch_error')"
                >
                  <el-icon><WarnTriangleFilled /></el-icon>
                  一键查询错误 {{ batchErrorCount }}
                </el-button>
              </div>
            </div>
            
            <!-- Loading State -->
            <div
              v-if="loading"
              class="loading-container"
            >
              <el-icon
                class="loading-icon"
                :size="40"
              >
                <Loading />
              </el-icon>
              <p class="loading-text">
                正在加载服务器...
              </p>
            </div>
            
            <!-- Error State -->
            <el-result
              v-else-if="loadError"
              icon="error"
              title="加载失败"
              :sub-title="loadError"
            >
              <template #extra>
                <el-button
                  type="primary"
                  @click="loadServers"
                >
                  <el-icon><Refresh /></el-icon>
                  重新加载
                </el-button>
              </template>
            </el-result>
            
            <!-- Empty State -->
            <el-empty
              v-else-if="groupedServers.length === 0"
              description="未找到服务器"
              :image-size="150"
            >
              <template #description>
                <p class="empty-description">
                  还没有添加任何服务器
                </p>
                <p class="empty-hint">
                  点击「新增服务器」按钮开始管理您的服务器
                </p>
              </template>
              <el-button
                type="primary"
                @click="showAddDialog"
              >
                <el-icon><Plus /></el-icon>
                新增服务器
              </el-button>
            </el-empty>
            
            <!-- IP段卡片网格布局 - 每行3个 -->
            <div
              v-if="!loading && !loadError && groupedServers.length > 0"
              class="segments-container"
            >
              <div class="segments-grid">
                <div
                  v-for="segment in paginatedSegments"
                  :key="segment.segmentKey"
                  class="segment-card"
                  :class="{ 'is-favorited': isSegmentFavorited(segment.segment) }"
                  @click="viewSegment(segment)"
                >
                  <div class="segment-card-header">
                    <span class="ip-segment-title">{{ segment.segment }}.x</span>
                    <el-tag
                      size="default"
                      type="info"
                      effect="plain"
                      class="count-tag"
                    >
                      {{ segment.count }} 台
                    </el-tag>
                  </div>
                  <div class="segment-card-status">
                    <el-tag
                      v-if="segment.onlineCount > 0"
                      type="success"
                      size="default"
                      effect="dark"
                    >
                      ✓ {{ segment.onlineCount }}<template v-if="segment.errorCount > 0">
                        / <span class="error-count">✗ {{ segment.errorCount }}</span>
                      </template>
                    </el-tag>
                    <el-tag
                      v-if="segment.offlineCount > 0"
                      type="danger"
                      size="default"
                      effect="dark"
                    >
                      ✗ {{ segment.offlineCount }}
                    </el-tag>
                    <el-tag
                      v-if="segment.batchOnlineCount > 0"
                      color="#10b981"
                      size="default"
                      effect="dark"
                    >
                      查询 {{ segment.batchOnlineCount }}
                    </el-tag>
                    <el-tag
                      v-if="segment.batchErrorCount > 0"
                      color="#f43f5e"
                      size="default"
                      effect="dark"
                    >
                      查询✗ {{ segment.batchErrorCount }}
                    </el-tag>
                  </div>
                  <!-- 显示IP段备注信息 -->
                  <div
                    v-if="getSegmentNote(segment.segment)"
                    class="segment-card-note"
                    @click.stop="editSegmentNote(segment.segment)"
                  >
                    <el-icon class="note-display-icon">
                      <EditPen />
                    </el-icon>
                    <span class="note-display-text">{{ getSegmentNote(segment.segment) }}</span>
                  </div>
                  <div class="segment-card-footer">
                    <div class="segment-card-actions-left">
                      <el-tooltip
                        :content="isSegmentFavorited(segment.segment) ? '取消收藏' : '收藏'"
                        placement="top"
                      >
                        <el-icon
                          class="action-icon favorite-icon"
                          :class="{ 'is-favorited': isSegmentFavorited(segment.segment) }"
                          @click.stop="toggleSegmentFavorite(segment.segment)"
                        >
                          <Star />
                        </el-icon>
                      </el-tooltip>
                      <el-tooltip
                        :content="getSegmentNote(segment.segment) ? '编辑备注' : '添加备注'"
                        placement="top"
                      >
                        <el-icon
                          class="action-icon note-icon"
                          :class="{ 'has-note': getSegmentNote(segment.segment) }"
                          @click.stop="editSegmentNote(segment.segment)"
                        >
                          <EditPen />
                        </el-icon>
                      </el-tooltip>
                    </div>
                    <el-button
                      size="default"
                      type="primary"
                      plain
                      @click.stop="viewSegment(segment)"
                    >
                      <el-icon><View /></el-icon>
                      查看详情
                    </el-button>
                  </div>
                </div>
              </div>
              <div
                v-if="groupedServers.length > PAGE_SIZE"
                class="pagination-container"
              >
                <el-pagination
                  v-model:current-page="segmentsCurrentPage"
                  :page-size="PAGE_SIZE"
                  :total="groupedServers.length"
                  layout="prev, pager, next"
                  background
                />
              </div>
            </div>
          </el-card>
        </div>
      </el-main>
    </el-container>
    
    <!-- Add/Edit Server Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑服务器' : '新增服务器'"
      width="720px"
      class="form-dialog"
    >
      <ServerForm
        :server="currentServer"
        :is-edit="isEdit"
        @submit="handleSubmit"
        @cancel="dialogVisible = false"
      />
    </el-dialog>
    
    <!-- View Server Detail Dialog -->
    <el-dialog
      v-model="detailDialogVisible"
      title="服务器详情"
      width="850px"
      class="detail-dialog"
    >
      <div
        v-if="selectedServer"
        class="server-detail"
      >
        <div class="detail-header">
          <div class="detail-title">
            <h3>{{ selectedServer.ip_address }}</h3>
            <p class="detail-updated">
              更新时间：{{ formatDate(getLastUpdateTime(selectedServer)) }}
            </p>
          </div>
          <StatusBadge
            :status="selectedServer.status"
            :detail="selectedServer.checkDetail"
            :error-type="selectedServer.error_type"
          />
        </div>
        
        <el-descriptions
          :column="2"
          border
        >
          <el-descriptions-item label="IP地址">
            {{ selectedServer.ip_address }}
          </el-descriptions-item>
          <el-descriptions-item label="端口">
            <el-tag
              :type="getPortTagType(selectedServer.port)"
              size="small"
              effect="dark"
            >
              {{ getPortTypeIcon(selectedServer.port) }} {{ selectedServer.port }} ({{ getPortTypeName(selectedServer.port) }})
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="用户名 / 密码">
            <div class="credentials-display">
              <span class="credential-value">{{ selectedServer.username }}</span>
              <span class="credential-separator">/</span>
              <span
                v-if="loadingPassword"
                class="credential-loading"
              >
                <el-icon class="is-loading"><Loading /></el-icon>
                加载中...
              </span>
              <span
                v-else
                class="credential-value password-value"
              >{{ selectedServerPassword }}</span>
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <StatusBadge
              :status="selectedServer.status"
              :detail="selectedServer.checkDetail"
              :error-type="selectedServer.error_type"
            />
          </el-descriptions-item>
          <el-descriptions-item
            label="系统信息"
            :span="2"
          >
            <span v-if="selectedServer.os_info">
              {{ getOsIcon(selectedServer.os_info) }} {{ selectedServer.os_info }}
            </span>
            <span
              v-else
              class="no-info"
            >暂无</span>
          </el-descriptions-item>
          <el-descriptions-item
            label="CPU 信息"
            :span="2"
          >
            {{ selectedServer.cpu_info || '暂无' }}
          </el-descriptions-item>
          <el-descriptions-item
            label="内存信息"
            :span="2"
          >
            {{ selectedServer.memory_info || '暂无' }}
          </el-descriptions-item>
          <el-descriptions-item
            label="磁盘信息"
            :span="2"
          >
            {{ selectedServer.disk_info || '暂无' }}
          </el-descriptions-item>
          <el-descriptions-item
            label="运行时间"
            :span="2"
          >
            {{ selectedServer.uptime || '暂无' }}
          </el-descriptions-item>
          <el-descriptions-item
            label="备注"
            :span="2"
          >
            <span
              class="clickable-note"
              @click="editServerNote(selectedServer)"
            >
              {{ selectedServer.notes || '点击添加备注' }}
              <el-icon class="edit-icon"><EditPen /></el-icon>
            </span>
          </el-descriptions-item>
          <el-descriptions-item
            label="最近检查"
            :span="2"
          >
            {{ formatDate(selectedServer.last_checked) }}
          </el-descriptions-item>
        </el-descriptions>
        
        <div class="detail-actions">
          <el-button
            type="primary"
            :loading="refreshing"
            @click="refreshSystemInfo"
          >
            <el-icon><Refresh /></el-icon>
            刷新系统信息
          </el-button>
        </div>
      </div>
    </el-dialog>
    
    <!-- View Segment Servers Dialog -->
    <el-dialog
      v-model="segmentDialogVisible"
      :title="selectedSegment ? `IP段 ${selectedSegment.segment}.x 的服务器` : 'IP段服务器'"
      width="1300px"
      class="segment-dialog"
    >
      <div v-if="selectedSegment">
        <div class="segment-header">
          <span class="segment-count">共 {{ selectedSegment.count }} 台服务器</span>
          <div class="segment-sort-options">
            <el-radio-group
              v-model="segmentDialogSortBy"
              size="small"
            >
              <el-radio-button value="time">
                <el-icon><Clock /></el-icon>
                按时间
              </el-radio-button>
              <el-radio-button value="ip">
                <el-icon><Sort /></el-icon>
                按IP
              </el-radio-button>
            </el-radio-group>
          </div>
        </div>
        <el-table
          :data="paginatedSegmentServers"
          style="width: 100%"
          stripe
          :row-class-name="getRowClassName"
        >
          <el-table-column
            label="IP地址"
            width="160"
          >
            <template #default="scope">
              <div class="ip-cell">
                <el-icon
                  v-if="isServerFavorited(scope.row.id)"
                  class="favorite-star-icon"
                >
                  <Star />
                </el-icon>
                <span class="ip-text">{{ scope.row.ip_address }}</span>
                <span class="updated-time">
                  <el-icon class="time-icon"><Clock /></el-icon>{{ formatDate(getLastUpdateTime(scope.row)) }}
                </span>
              </div>
            </template>
          </el-table-column>
          <el-table-column
            label="端口 / 配置"
            width="140"
          >
            <template #default="scope">
              <div class="port-cell">
                <div class="port-row">
                  <el-tag
                    :type="getPortTagType(scope.row.port)"
                    size="small"
                    effect="dark"
                    round
                  >
                    {{ getPortTypeIcon(scope.row.port) }} {{ scope.row.port }}
                  </el-tag>
                </div>
                <div
                  v-if="getServerSpecs(scope.row)"
                  class="specs-row"
                >
                  <el-tag
                    size="small"
                    effect="plain"
                    type="info"
                    class="specs-tag"
                  >
                    💻 {{ getServerSpecs(scope.row) }}
                  </el-tag>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column
            prop="username"
            label="用户名"
            width="120"
          />
          <el-table-column
            label="状态"
            width="100"
          >
            <template #default="scope">
              <StatusBadge
                :status="scope.row.status"
                :detail="scope.row.checkDetail"
                :error-type="scope.row.error_type"
                size="small"
              />
            </template>
          </el-table-column>
          <el-table-column
            prop="os_info"
            label="系统信息"
            min-width="120"
          >
            <template #default="scope">
              <span
                v-if="scope.row.os_info"
                class="os-info-text"
              >
                {{ getOsIcon(scope.row.os_info) }} {{ scope.row.os_info }}
              </span>
              <span
                v-else
                class="no-info"
              >-</span>
            </template>
          </el-table-column>
          <el-table-column
            prop="notes"
            label="备注"
            min-width="150"
          >
            <template #default="scope">
              <div
                class="editable-note"
                role="button"
                tabindex="0"
                @click="editServerNote(scope.row)"
                @keydown.enter="editServerNote(scope.row)"
                @keydown.space.prevent="editServerNote(scope.row)"
              >
                <span
                  v-if="scope.row.notes"
                  class="notes-text"
                >{{ scope.row.notes }}</span>
                <span
                  v-else
                  class="no-info clickable"
                >点击添加备注</span>
                <el-icon class="edit-note-icon">
                  <EditPen />
                </el-icon>
              </div>
            </template>
          </el-table-column>
          <el-table-column
            label="操作"
            width="250"
            fixed="right"
          >
            <template #default="scope">
              <div class="action-buttons">
                <el-tooltip
                  :content="isServerFavorited(scope.row.id) ? '取消收藏' : '收藏'"
                  placement="top"
                >
                  <el-button
                    size="small"
                    :class="{ 'is-favorited-btn': isServerFavorited(scope.row.id) }"
                    circle
                    @click="toggleServerFavorite(scope.row)"
                  >
                    <el-icon><Star /></el-icon>
                  </el-button>
                </el-tooltip>
                <el-tooltip
                  v-if="scope.row.port === RDP_PORT"
                  content="下载RDP文件"
                  placement="top"
                >
                  <el-button
                    size="small"
                    type="primary"
                    circle
                    @click="downloadRdpFile(scope.row)"
                  >
                    <el-icon><Download /></el-icon>
                  </el-button>
                </el-tooltip>
                <el-tooltip
                  content="连接"
                  placement="top"
                >
                  <el-button
                    size="small"
                    type="success"
                    circle
                    @click="openTerminal(scope.row)"
                  >
                    <el-icon><Connection /></el-icon>
                  </el-button>
                </el-tooltip>
                <el-tooltip
                  content="检测"
                  placement="top"
                >
                  <el-button
                    size="small"
                    type="warning"
                    circle
                    :loading="scope.row.checking"
                    @click="checkServer(scope.row)"
                  >
                    <el-icon><Search /></el-icon>
                  </el-button>
                </el-tooltip>
                <el-tooltip
                  content="详情"
                  placement="top"
                >
                  <el-button
                    size="small"
                    circle
                    @click="viewServer(scope.row)"
                  >
                    <el-icon><View /></el-icon>
                  </el-button>
                </el-tooltip>
                <el-tooltip
                  content="编辑"
                  placement="top"
                >
                  <el-button
                    size="small"
                    type="primary"
                    circle
                    @click="editServer(scope.row)"
                  >
                    <el-icon><Edit /></el-icon>
                  </el-button>
                </el-tooltip>
                <el-tooltip
                  content="删除"
                  placement="top"
                >
                  <el-button
                    size="small"
                    type="danger"
                    circle
                    @click="deleteServer(scope.row)"
                  >
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </el-tooltip>
              </div>
            </template>
          </el-table-column>
        </el-table>
        <div
          v-if="selectedSegment.count > PAGE_SIZE"
          class="pagination-container"
        >
          <el-pagination
            v-model:current-page="segmentDialogCurrentPage"
            :page-size="PAGE_SIZE"
            :total="selectedSegment.count"
            layout="prev, pager, next"
            background
          />
        </div>
      </div>
    </el-dialog>
    <el-dialog
      v-model="filteredDialogVisible"
      :title="filteredDialogTitle"
      width="1300px"
      class="filtered-dialog"
      @closed="onFilteredDialogClosed"
    >
      <div v-if="filteredDialogServers.length > 0">
        <div class="segment-header">
          <span class="segment-count">共 {{ filteredDialogServers.length }} 台服务器<template v-if="isBatchDialogType">，{{ groupedBatchServers.length }} 个IP段</template></span>
          <div class="segment-header-actions">
            <el-button
              v-if="isBatchDialogType"
              size="small"
              @click="toggleAllBatchSegments"
            >
              <el-icon><FolderOpened v-if="allBatchSegmentsExpanded" /><Folder v-else /></el-icon>
              {{ allBatchSegmentsExpanded ? '全部收起' : '全部展开' }}
            </el-button>
            <el-button
              v-if="filteredDialogType === 'normal'"
              type="success"
              size="small"
              :loading="batchGettingSystemInfo"
              @click="batchGetSystemInfo"
            >
              <el-icon><Cpu /></el-icon>
              一键获取系统信息
            </el-button>
          </div>
        </div>
        <!-- 一键查询：按IP段分组显示 -->
        <div
          v-if="isBatchDialogType"
          class="batch-segment-groups"
        >
          <div
            v-for="group in groupedBatchServers"
            :key="group.segment"
            class="batch-segment-group"
          >
            <div
              class="batch-segment-group-header"
              role="button"
              tabindex="0"
              @click="toggleBatchSegment(group.segment)"
              @keydown.enter="toggleBatchSegment(group.segment)"
              @keydown.space.prevent="toggleBatchSegment(group.segment)"
            >
              <div class="batch-segment-group-left">
                <el-icon
                  class="batch-segment-arrow"
                  :class="{ 'is-expanded': isBatchSegmentExpanded(group.segment) }"
                >
                  <ArrowDown />
                </el-icon>
                <span class="batch-segment-name">{{ group.segment }}.x</span>
                <el-tag
                  :color="filteredDialogType === 'batch_online' ? '#10b981' : '#f43f5e'"
                  size="small"
                  effect="dark"
                >
                  {{ group.count }} 台
                </el-tag>
                <span
                  v-if="group.note"
                  class="batch-segment-note"
                >
                  <el-icon><EditPen /></el-icon>
                  {{ group.note }}
                </span>
              </div>
            </div>
            <div
              v-show="isBatchSegmentExpanded(group.segment)"
              class="batch-segment-group-body"
            >
              <el-table
                :data="group.servers"
                style="width: 100%"
                stripe
                :row-class-name="getRowClassName"
              >
                <el-table-column
                  label="IP地址"
                  width="160"
                >
                  <template #default="scope">
                    <div class="ip-cell">
                      <el-icon
                        v-if="isServerFavorited(scope.row.id)"
                        class="favorite-star-icon"
                      >
                        <Star />
                      </el-icon>
                      <span class="ip-text">{{ scope.row.ip_address }}</span>
                      <span class="updated-time">
                        <el-icon class="time-icon"><Clock /></el-icon>{{ formatDate(getLastUpdateTime(scope.row)) }}
                      </span>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column
                  label="端口 / 配置"
                  width="140"
                >
                  <template #default="scope">
                    <div class="port-cell">
                      <div class="port-row">
                        <el-tag
                          :type="getPortTagType(scope.row.port)"
                          size="small"
                          effect="dark"
                          round
                        >
                          {{ getPortTypeIcon(scope.row.port) }} {{ scope.row.port }}
                        </el-tag>
                      </div>
                      <div
                        v-if="getServerSpecs(scope.row)"
                        class="specs-row"
                      >
                        <el-tag
                          size="small"
                          effect="plain"
                          type="info"
                          class="specs-tag"
                        >
                          💻 {{ getServerSpecs(scope.row) }}
                        </el-tag>
                      </div>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column
                  prop="username"
                  label="用户名"
                  width="120"
                />
                <el-table-column
                  label="状态"
                  width="100"
                >
                  <template #default="scope">
                    <StatusBadge
                      :status="scope.row.status"
                      :detail="scope.row.checkDetail"
                      :error-type="scope.row.error_type"
                      size="small"
                    />
                  </template>
                </el-table-column>
                <el-table-column
                  prop="os_info"
                  label="系统信息"
                  min-width="120"
                >
                  <template #default="scope">
                    <span
                      v-if="scope.row.os_info"
                      class="os-info-text"
                    >
                      {{ getOsIcon(scope.row.os_info) }} {{ scope.row.os_info }}
                    </span>
                    <span
                      v-else
                      class="no-info"
                    >-</span>
                  </template>
                </el-table-column>
                <el-table-column
                  prop="notes"
                  label="备注"
                  min-width="150"
                >
                  <template #default="scope">
                    <div
                      class="editable-note"
                      role="button"
                      tabindex="0"
                      @click="editServerNote(scope.row)"
                      @keydown.enter="editServerNote(scope.row)"
                      @keydown.space.prevent="editServerNote(scope.row)"
                    >
                      <span
                        v-if="scope.row.notes"
                        class="notes-text"
                      >{{ scope.row.notes }}</span>
                      <span
                        v-else
                        class="no-info clickable"
                      >点击添加备注</span>
                      <el-icon class="edit-note-icon">
                        <EditPen />
                      </el-icon>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column
                  label="操作"
                  width="250"
                  fixed="right"
                >
                  <template #default="scope">
                    <div class="action-buttons">
                      <el-tooltip
                        :content="isServerFavorited(scope.row.id) ? '取消收藏' : '收藏'"
                        placement="top"
                      >
                        <el-button
                          size="small"
                          :class="{ 'is-favorited-btn': isServerFavorited(scope.row.id) }"
                          circle
                          @click="toggleServerFavorite(scope.row)"
                        >
                          <el-icon><Star /></el-icon>
                        </el-button>
                      </el-tooltip>
                      <el-tooltip
                        v-if="scope.row.port === RDP_PORT"
                        content="下载RDP文件"
                        placement="top"
                      >
                        <el-button
                          size="small"
                          type="primary"
                          circle
                          @click="downloadRdpFile(scope.row)"
                        >
                          <el-icon><Download /></el-icon>
                        </el-button>
                      </el-tooltip>
                      <el-tooltip
                        content="连接"
                        placement="top"
                      >
                        <el-button
                          size="small"
                          type="success"
                          circle
                          @click="openTerminal(scope.row)"
                        >
                          <el-icon><Connection /></el-icon>
                        </el-button>
                      </el-tooltip>
                      <el-tooltip
                        content="检测"
                        placement="top"
                      >
                        <el-button
                          size="small"
                          type="warning"
                          circle
                          :loading="scope.row.checking"
                          @click="checkServer(scope.row)"
                        >
                          <el-icon><Search /></el-icon>
                        </el-button>
                      </el-tooltip>
                      <el-tooltip
                        content="详情"
                        placement="top"
                      >
                        <el-button
                          size="small"
                          circle
                          @click="viewServer(scope.row)"
                        >
                          <el-icon><View /></el-icon>
                        </el-button>
                      </el-tooltip>
                      <el-tooltip
                        content="编辑"
                        placement="top"
                      >
                        <el-button
                          size="small"
                          type="primary"
                          circle
                          @click="editServer(scope.row)"
                        >
                          <el-icon><Edit /></el-icon>
                        </el-button>
                      </el-tooltip>
                      <el-tooltip
                        content="删除"
                        placement="top"
                      >
                        <el-button
                          size="small"
                          type="danger"
                          circle
                          @click="deleteServer(scope.row)"
                        >
                          <el-icon><Delete /></el-icon>
                        </el-button>
                      </el-tooltip>
                    </div>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </div>
        </div>
        <!-- 其他类型：平铺显示 -->
        <template v-else>
          <el-table
            :data="paginatedFilteredServers"
            style="width: 100%"
            stripe
            :row-class-name="getRowClassName"
          >
            <el-table-column
              label="IP地址"
              width="160"
            >
              <template #default="scope">
                <div class="ip-cell">
                  <el-icon
                    v-if="isServerFavorited(scope.row.id)"
                    class="favorite-star-icon"
                  >
                    <Star />
                  </el-icon>
                  <span class="ip-text">{{ scope.row.ip_address }}</span>
                  <span class="updated-time">
                    <el-icon class="time-icon"><Clock /></el-icon>{{ formatDate(getLastUpdateTime(scope.row)) }}
                  </span>
                </div>
              </template>
            </el-table-column>
            <el-table-column
              label="端口 / 配置"
              width="140"
            >
              <template #default="scope">
                <div class="port-cell">
                  <div class="port-row">
                    <el-tag
                      :type="getPortTagType(scope.row.port)"
                      size="small"
                      effect="dark"
                      round
                    >
                      {{ getPortTypeIcon(scope.row.port) }} {{ scope.row.port }}
                    </el-tag>
                  </div>
                  <div
                    v-if="getServerSpecs(scope.row)"
                    class="specs-row"
                  >
                    <el-tag
                      size="small"
                      effect="plain"
                      type="info"
                      class="specs-tag"
                    >
                      💻 {{ getServerSpecs(scope.row) }}
                    </el-tag>
                  </div>
                </div>
              </template>
            </el-table-column>
            <el-table-column
              prop="username"
              label="用户名"
              width="120"
            />
            <el-table-column
              label="状态"
              width="100"
            >
              <template #default="scope">
                <StatusBadge
                  :status="scope.row.status"
                  :detail="scope.row.checkDetail"
                  :error-type="scope.row.error_type"
                  size="small"
                />
              </template>
            </el-table-column>
            <el-table-column
              prop="os_info"
              label="系统信息"
              min-width="120"
            >
              <template #default="scope">
                <span
                  v-if="scope.row.os_info"
                  class="os-info-text"
                >
                  {{ getOsIcon(scope.row.os_info) }} {{ scope.row.os_info }}
                </span>
                <span
                  v-else
                  class="no-info"
                >-</span>
              </template>
            </el-table-column>
            <el-table-column
              prop="notes"
              label="备注"
              min-width="150"
            >
              <template #default="scope">
                <div
                  class="editable-note"
                  role="button"
                  tabindex="0"
                  @click="editServerNote(scope.row)"
                  @keydown.enter="editServerNote(scope.row)"
                  @keydown.space.prevent="editServerNote(scope.row)"
                >
                  <span
                    v-if="scope.row.notes"
                    class="notes-text"
                  >{{ scope.row.notes }}</span>
                  <span
                    v-else
                    class="no-info clickable"
                  >点击添加备注</span>
                  <el-icon class="edit-note-icon">
                    <EditPen />
                  </el-icon>
                </div>
              </template>
            </el-table-column>
            <el-table-column
              label="操作"
              width="250"
              fixed="right"
            >
              <template #default="scope">
                <div class="action-buttons">
                  <el-tooltip
                    :content="isServerFavorited(scope.row.id) ? '取消收藏' : '收藏'"
                    placement="top"
                  >
                    <el-button
                      size="small"
                      :class="{ 'is-favorited-btn': isServerFavorited(scope.row.id) }"
                      circle
                      @click="toggleServerFavorite(scope.row)"
                    >
                      <el-icon><Star /></el-icon>
                    </el-button>
                  </el-tooltip>
                  <el-tooltip
                    v-if="scope.row.port === RDP_PORT"
                    content="下载RDP文件"
                    placement="top"
                  >
                    <el-button
                      size="small"
                      type="primary"
                      circle
                      @click="downloadRdpFile(scope.row)"
                    >
                      <el-icon><Download /></el-icon>
                    </el-button>
                  </el-tooltip>
                  <el-tooltip
                    content="连接"
                    placement="top"
                  >
                    <el-button
                      size="small"
                      type="success"
                      circle
                      @click="openTerminal(scope.row)"
                    >
                      <el-icon><Connection /></el-icon>
                    </el-button>
                  </el-tooltip>
                  <el-tooltip
                    content="检测"
                    placement="top"
                  >
                    <el-button
                      size="small"
                      type="warning"
                      circle
                      :loading="scope.row.checking"
                      @click="checkServer(scope.row)"
                    >
                      <el-icon><Search /></el-icon>
                    </el-button>
                  </el-tooltip>
                  <el-tooltip
                    content="详情"
                    placement="top"
                  >
                    <el-button
                      size="small"
                      circle
                      @click="viewServer(scope.row)"
                    >
                      <el-icon><View /></el-icon>
                    </el-button>
                  </el-tooltip>
                  <el-tooltip
                    content="编辑"
                    placement="top"
                  >
                    <el-button
                      size="small"
                      type="primary"
                      circle
                      @click="editServer(scope.row)"
                    >
                      <el-icon><Edit /></el-icon>
                    </el-button>
                  </el-tooltip>
                  <el-tooltip
                    content="删除"
                    placement="top"
                  >
                    <el-button
                      size="small"
                      type="danger"
                      circle
                      @click="deleteServer(scope.row)"
                    >
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </el-tooltip>
                </div>
              </template>
            </el-table-column>
          </el-table>
          <div
            v-if="filteredDialogServers.length > PAGE_SIZE"
            class="pagination-container"
          >
            <el-pagination
              v-model:current-page="filteredDialogCurrentPage"
              :page-size="PAGE_SIZE"
              :total="filteredDialogServers.length"
              layout="prev, pager, next"
              background
            />
          </div>
        </template>
      </div>
      <el-empty
        v-else
        description="没有符合条件的服务器"
      />
    </el-dialog>
    
    <!-- Terminal Connection Dialog -->
    <el-dialog
      v-model="terminalDialogVisible"
      :title="terminalServer?.port === RDP_PORT ? `🪟 远程桌面 - ${terminalServer?.ip_address || ''}` : `终端 - ${terminalServer?.ip_address || ''}`"
      width="1300px"
      :class="['terminal-dialog', terminalServer?.port === RDP_PORT ? 'rdp-dialog' : '']"
      append-to-body
      :close-on-click-modal="false"
      @closed="handleTerminalDialogClosed"
    >
      <div
        v-if="terminalServer"
        class="terminal-dialog-content"
      >
        <div class="terminal-header-info">
          <el-descriptions
            :column="4"
            border
            size="small"
          >
            <el-descriptions-item label="IP地址">
              <span class="mono-text">{{ terminalServer.ip_address }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="端口">
              <el-tag
                :type="getPortTagType(terminalServer.port)"
                size="small"
                effect="dark"
              >
                {{ terminalServer.port }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="用户名">
              <span class="mono-text">{{ terminalServer.username }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="状态">
              <StatusBadge
                :status="terminalServer.status"
                size="small"
              />
            </el-descriptions-item>
          </el-descriptions>
        </div>
        
        <Terminal
          v-if="terminalServer.port !== RDP_PORT"
          ref="terminalRef"
          :server="terminalServer"
          :visible="terminalDialogVisible"
          @connected="handleTerminalConnected"
          @disconnected="handleTerminalDisconnected"
          @error="handleTerminalError"
        />
        
        <!-- Enhanced RDP Connection Panel -->
        <div
          v-else
          class="rdp-panel"
        >
          <!-- Connection Status Card -->
          <div class="rdp-status-card">
            <div class="rdp-status-header">
              <div class="rdp-status-icon-area">
                <div :class="['rdp-status-dot', rdpPortStatus === 'online' ? 'online' : rdpPortStatus === 'checking' ? 'checking' : 'offline']" />
                <span class="rdp-status-text">
                  {{ rdpPortStatus === 'online' ? 'RDP 端口就绪' : rdpPortStatus === 'checking' ? '正在检测端口...' : rdpPortStatus === 'offline' ? 'RDP 端口未开放' : '等待检测' }}
                </span>
              </div>
              <el-button
                size="small"
                :loading="rdpPortStatus === 'checking'"
                @click="checkRdpPort(terminalServer)"
              >
                <el-icon><Refresh /></el-icon>
                检测端口
              </el-button>
            </div>
          </div>

          <!-- Quick Actions -->
          <div class="rdp-quick-actions">
            <el-button
              type="primary"
              size="large"
              class="rdp-main-btn"
              @click="downloadRdpFile(terminalServer)"
            >
              <el-icon :size="18">
                <Download />
              </el-icon>
              下载 RDP 连接文件
            </el-button>
            <el-button
              type="success"
              size="large"
              class="rdp-main-btn"
              @click="launchRdpConnection(terminalServer)"
            >
              <el-icon :size="18">
                <Connection />
              </el-icon>
              一键连接远程桌面
            </el-button>
            <el-button
              size="large"
              class="rdp-main-btn"
              @click="copySshCommand(terminalServer)"
            >
              <el-icon :size="18">
                <CopyDocument />
              </el-icon>
              复制 mstsc 命令
            </el-button>
          </div>

          <!-- Command Display -->
          <div class="rdp-command-box">
            <code class="rdp-command">{{ getSshCommand(terminalServer) }}</code>
          </div>

          <!-- RDP Settings Panel -->
          <div class="rdp-settings-panel">
            <div class="rdp-settings-title">
              <el-icon><Setting /></el-icon>
              <span>连接设置</span>
            </div>
            <el-form
              :model="rdpSettings"
              label-width="100px"
              size="small"
              class="rdp-settings-form"
            >
              <el-row :gutter="20">
                <el-col :span="8">
                  <el-form-item label="分辨率">
                    <el-select
                      v-model="rdpResolution"
                      placeholder="选择分辨率"
                    >
                      <el-option
                        label="1920 × 1080 (推荐)"
                        value="1920x1080"
                      />
                      <el-option
                        label="1600 × 900"
                        value="1600x900"
                      />
                      <el-option
                        label="1366 × 768"
                        value="1366x768"
                      />
                      <el-option
                        label="1280 × 720"
                        value="1280x720"
                      />
                      <el-option
                        label="2560 × 1440 (2K)"
                        value="2560x1440"
                      />
                      <el-option
                        label="3840 × 2160 (4K)"
                        value="3840x2160"
                      />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="显示模式">
                    <el-select v-model="rdpSettings.fullscreen">
                      <el-option
                        label="窗口模式"
                        :value="false"
                      />
                      <el-option
                        label="全屏模式"
                        :value="true"
                      />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="管理员会话">
                    <el-switch v-model="rdpSettings.admin" />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-row :gutter="20">
                <el-col :span="8">
                  <el-form-item label="共享剪贴板">
                    <el-switch v-model="rdpSettings.clipboard" />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="映射驱动器">
                    <el-switch v-model="rdpSettings.drives" />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="多显示器">
                    <el-switch v-model="rdpSettings.multimon" />
                  </el-form-item>
                </el-col>
              </el-row>
            </el-form>
          </div>

          <!-- Tips -->
          <div class="rdp-tips">
            <p>💡 <strong>使用说明：</strong></p>
            <ul>
              <li>点击「下载 RDP 连接文件」后双击 .rdp 文件即可后台发起远程桌面连接</li>
              <li>点击「一键连接远程桌面」将尝试通过系统协议直接启动远程桌面客户端</li>
              <li>修改上方连接设置后，重新下载 RDP 文件即可应用新的配置</li>
              <li>若需以管理员身份连接（/admin），请开启「管理员会话」选项</li>
            </ul>
          </div>
        </div>
        
        <!-- File Browser Section - Only show after terminal connected and for SSH servers -->
        <div
          v-if="terminalConnected && terminalServer.port !== RDP_PORT"
          class="file-browser-section"
        >
          <div class="file-browser-header">
            <div class="file-browser-title-area">
              <h4 class="file-browser-title">
                <el-icon class="file-browser-title-icon">
                  <Folder />
                </el-icon>
                服务器文件浏览
              </h4>
              <el-tag
                type="info"
                size="small"
                effect="plain"
              >
                {{ fileList.length }} 个项目
              </el-tag>
            </div>
            <div class="file-browser-path">
              <el-icon class="path-home-icon">
                <FolderOpened />
              </el-icon>
              <el-breadcrumb separator="/">
                <el-breadcrumb-item
                  v-for="(pathPart, index) in currentPathParts"
                  :key="index"
                  @click="navigateToPath(index)"
                >
                  <span class="breadcrumb-item-clickable">{{ pathPart || '根目录' }}</span>
                </el-breadcrumb-item>
              </el-breadcrumb>
            </div>
            <el-button
              size="small"
              :loading="fileBrowserLoading"
              type="primary"
              plain
              @click="refreshFileList"
            >
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
          
          <div
            v-if="fileBrowserLoading"
            class="file-browser-loading"
          >
            <div class="loading-animation">
              <el-icon
                class="loading-icon"
                :size="32"
              >
                <Loading />
              </el-icon>
            </div>
            <span>正在加载文件列表...</span>
          </div>
          
          <div
            v-else-if="fileBrowserError"
            class="file-browser-error"
          >
            <el-alert
              :title="fileBrowserError"
              type="error"
              :closable="false"
              show-icon
            />
          </div>
          
          <div
            v-else
            class="file-browser-content"
          >
            <el-table
              :data="fileList"
              style="width: 100%"
              max-height="320"
              stripe
              size="small"
              highlight-current-row
              :row-class-name="getFileRowClass"
              @row-click="handleFileClick"
            >
              <el-table-column
                label="名称"
                min-width="260"
              >
                <template #default="scope">
                  <div class="file-name-cell">
                    <div
                      class="file-icon-wrapper"
                      :class="getFileIconClass(scope.row)"
                    >
                      <el-icon
                        v-if="scope.row.type === 'directory'"
                        class="file-icon folder-icon"
                      >
                        <FolderOpened />
                      </el-icon>
                      <el-icon
                        v-else-if="scope.row.type === 'link'"
                        class="file-icon link-icon"
                      >
                        <Link />
                      </el-icon>
                      <span
                        v-else
                        class="file-ext-icon"
                      >{{ getFileExtIcon(scope.row.name) }}</span>
                    </div>
                    <div class="file-name-info">
                      <span class="file-name">{{ scope.row.name }}</span>
                      <span
                        v-if="isHiddenFile(scope.row.name)"
                        class="hidden-badge"
                      >隐藏</span>
                    </div>
                  </div>
                </template>
              </el-table-column>
              <el-table-column
                prop="type"
                label="类型"
                width="100"
              >
                <template #default="scope">
                  <el-tag
                    :type="getFileTypeTagType(scope.row.type)"
                    size="small"
                    effect="plain"
                  >
                    {{ getFileTypeLabel(scope.row.type) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column
                prop="size"
                label="大小"
                width="100"
              >
                <template #default="scope">
                  <span class="file-size">{{ scope.row.size }}</span>
                </template>
              </el-table-column>
              <el-table-column
                prop="permissions"
                label="权限"
                width="130"
              >
                <template #default="scope">
                  <code class="permission-code">{{ scope.row.permissions }}</code>
                </template>
              </el-table-column>
              <el-table-column
                label="操作"
                width="160"
                fixed="right"
              >
                <template #default="scope">
                  <div class="file-actions">
                    <el-button
                      v-if="scope.row.type === 'directory'"
                      size="small"
                      type="primary"
                      text
                      @click.stop="openDirectory(scope.row)"
                    >
                      <el-icon><FolderOpened /></el-icon>
                      打开
                    </el-button>
                    <el-button
                      v-else
                      size="small"
                      type="primary"
                      text
                      @click.stop="viewFileContent(scope.row)"
                    >
                      <el-icon><View /></el-icon>
                      查看
                    </el-button>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </div>
    </el-dialog>
    
    <!-- File Content Viewer/Editor Dialog -->
    <el-dialog
      v-model="fileEditorVisible"
      :title="`${fileEditorReadonly ? '📄 查看文件' : '✏️ 编辑文件'}`"
      width="1000px"
      class="file-editor-dialog"
      append-to-body
      :close-on-click-modal="false"
    >
      <div
        v-if="fileEditorLoading"
        class="loading-container"
      >
        <el-icon
          class="loading-icon"
          :size="40"
        >
          <Loading />
        </el-icon>
        <p class="loading-text">
          正在加载文件内容...
        </p>
      </div>
      <div
        v-else
        class="file-editor-content"
      >
        <div class="file-editor-header">
          <div class="file-editor-info">
            <div class="file-path-display">
              <el-icon class="path-icon">
                <DocumentIcon />
              </el-icon>
              <code class="file-path-code">{{ fileEditorPath }}</code>
            </div>
            <div class="file-editor-badges">
              <el-tag
                :type="fileEditorReadonly ? 'info' : 'success'"
                size="small"
                effect="dark"
              >
                {{ fileEditorReadonly ? '只读模式' : '编辑模式' }}
              </el-tag>
              <el-tag
                v-if="fileEditorContent"
                type="info"
                size="small"
                effect="plain"
              >
                {{ fileEditorContent.split('\n').length }} 行
              </el-tag>
            </div>
          </div>
          <div class="file-editor-actions">
            <el-button
              v-if="fileEditorReadonly"
              size="small"
              type="warning"
              @click="enableEditing"
            >
              <el-icon><Edit /></el-icon>
              切换编辑
            </el-button>
          </div>
        </div>
        <div class="file-editor-body">
          <div class="line-numbers">
            <span
              v-for="n in lineCount"
              :key="n"
              class="line-number"
            >{{ n }}</span>
          </div>
          <el-input
            v-model="fileEditorContent"
            type="textarea"
            :rows="22"
            :readonly="fileEditorReadonly"
            class="file-editor-textarea"
            placeholder="文件内容为空"
            resize="none"
          />
        </div>
      </div>
      <template #footer>
        <div class="file-editor-footer">
          <el-button @click="fileEditorVisible = false">
            <el-icon><CircleClose /></el-icon>
            关闭
          </el-button>
          <el-button
            v-if="!fileEditorReadonly"
            type="primary"
            :loading="fileEditorSaving"
            @click="saveFileContent"
          >
            <el-icon><DocumentIcon /></el-icon>
            保存文件
          </el-button>
        </div>
      </template>
    </el-dialog>
    
    <!-- Change Password Dialog -->
    <el-dialog
      v-model="passwordDialogVisible"
      title="修改密码"
      width="500px"
      class="password-dialog"
    >
      <el-form
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordRules"
        label-width="80px"
      >
        <el-form-item
          label="旧密码"
          prop="old_password"
        >
          <el-input
            v-model="passwordForm.old_password"
            type="password"
            placeholder="请输入旧密码"
            show-password
          />
        </el-form-item>
        <el-form-item
          label="新密码"
          prop="new_password"
        >
          <el-input
            v-model="passwordForm.new_password"
            type="password"
            placeholder="请输入新密码（至少6位）"
            show-password
          />
        </el-form-item>
        <el-form-item
          label="确认密码"
          prop="confirm_password"
        >
          <el-input
            v-model="passwordForm.confirm_password"
            type="password"
            placeholder="请再次输入新密码"
            show-password
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="passwordDialogVisible = false">
          取消
        </el-button>
        <el-button
          type="primary"
          :loading="changingPassword"
          @click="handleChangePassword"
        >
          确认修改
        </el-button>
      </template>
    </el-dialog>
    
    <!-- Read File Dialog -->
    <el-dialog
      v-model="fileDialogVisible"
      :title="fileDialogServer ? `文件内容 - ${fileDialogServer.ip_address}` : '文件内容'"
      width="700px"
      class="file-dialog"
    >
      <div
        v-if="fileDialogLoading"
        class="loading-container"
      >
        <el-icon
          class="loading-icon"
          :size="40"
        >
          <Loading />
        </el-icon>
        <p class="loading-text">
          正在读取文件...
        </p>
      </div>
      <div
        v-else-if="fileDialogContent"
        class="file-content-container"
      >
        <div class="file-info">
          <el-tag
            type="info"
            effect="plain"
          >
            文件路径: {{ fileDialogFilename }}
          </el-tag>
        </div>
        <pre class="file-content">{{ fileDialogContent }}</pre>
      </div>
      <el-empty
        v-else
        description="文件内容为空或读取失败"
      />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Monitor, Odometer, User, ArrowDown, Plus, Refresh,
  Search, View, Edit, Delete, OfficeBuilding, Connection, CopyDocument, Loading,
  CircleCheck, CircleClose, Download, QuestionFilled, WarningFilled, Cpu, Star, EditPen,
  Clock, Sort, Folder, FolderOpened, Document as DocumentIcon, Link, Setting, Tools,
  Promotion, WarnTriangleFilled
} from '@element-plus/icons-vue'
import { serversAPI, authAPI, preferencesAPI } from '@/api'
import StatusBadge from '@/components/StatusBadge.vue'
import ServerForm from '@/components/ServerForm.vue'
import Terminal from '@/components/Terminal.vue'

// 文件扩展名图标映射配置
const FILE_EXTENSION_ICONS = {
  // 代码文件
  js: '📜', ts: '📜', jsx: '📜', tsx: '📜',
  py: '🐍', java: '☕', rb: '💎', go: '🔷',
  rs: '🦀', c: '⚙️', cpp: '⚙️', h: '⚙️',
  php: '🐘', swift: '🍎', kt: '🔶',
  // 前端
  html: '🌐', htm: '🌐', css: '🎨', scss: '🎨', less: '🎨',
  vue: '💚', svelte: '🧡',
  // 配置
  json: '📋', yaml: '📋', yml: '📋', xml: '📋',
  toml: '📋', ini: '📋', conf: '📋', cfg: '📋',
  env: '🔐',
  // 文档
  md: '📝', txt: '📄', doc: '📄', docx: '📄',
  pdf: '📕', rtf: '📄',
  // 数据
  sql: '🗄️', db: '🗄️', sqlite: '🗄️',
  csv: '📊', xls: '📊', xlsx: '📊',
  // 图片
  jpg: '🖼️', jpeg: '🖼️', png: '🖼️', gif: '🖼️',
  svg: '🖼️', ico: '🖼️', webp: '🖼️',
  // 压缩
  zip: '📦', tar: '📦', gz: '📦', rar: '📦', '7z': '📦',
  // Shell
  sh: '🖥️', bash: '🖥️', zsh: '🖥️', fish: '🖥️',
  // 日志
  log: '📋',
  // 其他
  lock: '🔒', key: '🔑', pem: '🔑', crt: '🔐'
}

// 代码文件扩展名列表
const CODE_FILE_EXTENSIONS = ['js', 'ts', 'jsx', 'tsx', 'py', 'java', 'rb', 'go', 'rs', 'c', 'cpp', 'h', 'php', 'swift', 'kt', 'vue', 'svelte']

// 配置文件扩展名列表
const CONFIG_FILE_EXTENSIONS = ['json', 'yaml', 'yml', 'xml', 'toml', 'ini', 'conf', 'cfg', 'env']

const router = useRouter()
const route = useRoute()
const servers = ref([])
const searchText = ref('')
const dialogVisible = ref(false)
const detailDialogVisible = ref(false)
const segmentDialogVisible = ref(false)
const terminalDialogVisible = ref(false)
const filteredDialogVisible = ref(false)
const filteredDialogTitle = ref('')
const filteredDialogServers = ref([])
const filteredDialogType = ref('')
const batchGettingSystemInfo = ref(false)
const expandedBatchSegments = ref(new Set())
const allBatchSegmentsExpanded = ref(true)
const passwordDialogVisible = ref(false)
const changingPassword = ref(false)
const passwordFormRef = ref(null)
const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})
const passwordRules = {
  old_password: [
    { required: true, message: '请输入旧密码', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6个字符', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== passwordForm.new_password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}
const isEdit = ref(false)
const currentServer = ref(null)
const selectedServer = ref(null)
const selectedServerPassword = ref('')
const loadingPassword = ref(false)
const selectedSegment = ref(null)
const terminalServer = ref(null)
const terminalRef = ref(null)
const refreshing = ref(false)
const currentUser = ref(null)
const loading = ref(false)
const loadError = ref('')
const importing = ref(false)

// 读取文件对话框状态
const fileDialogVisible = ref(false)
const fileDialogLoading = ref(false)
const fileDialogContent = ref(null)
const fileDialogFilename = ref('')
const fileDialogServer = ref(null)

// 终端连接状态
const terminalConnected = ref(false)

// RDP 连接设置
const rdpSettings = reactive({
  fullscreen: false,
  clipboard: true,
  drives: false,
  admin: false,
  multimon: false
})
const rdpResolution = ref('1920x1080')
const rdpPortStatus = ref('unknown') // 'unknown' | 'checking' | 'online' | 'offline'

// 文件浏览器状态
const currentPath = ref('/')
const fileList = ref([])
const fileBrowserLoading = ref(false)
const fileBrowserError = ref('')

// 文件编辑器状态
const fileEditorVisible = ref(false)
const fileEditorPath = ref('')
const fileEditorContent = ref('')
const fileEditorReadonly = ref(true)
const fileEditorLoading = ref(false)
const fileEditorSaving = ref(false)

// 计算文件行数
const lineCount = computed(() => {
  if (!fileEditorContent.value) return 1
  return fileEditorContent.value.split('\n').length
})

// 计算当前路径的各个部分
const currentPathParts = computed(() => {
  if (currentPath.value === '/') {
    return ['']
  }
  return currentPath.value.split('/').filter(p => p !== '')
})

// Pagination variables
const PAGE_SIZE = 10
const segmentsCurrentPage = ref(1)
const segmentDialogCurrentPage = ref(1)
const filteredDialogCurrentPage = ref(1)

// IP段对话框排序选项
const segmentDialogSortBy = ref('time') // 'time' | 'ip'

// IP段收藏和备注功能（从服务器加载）
const segmentFavorites = ref(new Set())
const segmentNotes = ref({})
const serverFavorites = ref(new Set())

// 初始化收藏和备注数据（从服务器加载）
const initSegmentData = async () => {
  try {
    // 并行加载所有数据
    const [favoritesRes, notesRes, serverFavoritesRes] = await Promise.all([
      preferencesAPI.getSegmentFavorites(),
      preferencesAPI.getSegmentNotes(),
      preferencesAPI.getServerFavorites()
    ])
    
    segmentFavorites.value = new Set(favoritesRes.data || [])
    segmentNotes.value = notesRes.data || {}
    serverFavorites.value = new Set(serverFavoritesRes.data || [])
  } catch (_e) {
    segmentFavorites.value = new Set()
    segmentNotes.value = {}
    serverFavorites.value = new Set()
  }
}

// 检查IP段是否被收藏
const isSegmentFavorited = (segment) => {
  return segmentFavorites.value.has(segment)
}

// 切换IP段收藏状态
const toggleSegmentFavorite = async (segment) => {
  try {
    const response = await preferencesAPI.toggleSegmentFavorite(segment)
    if (response.data.favorited) {
      segmentFavorites.value.add(segment)
      ElMessage.success(`已收藏 ${segment}.x`)
    } else {
      segmentFavorites.value.delete(segment)
      ElMessage.success(`已取消收藏 ${segment}.x`)
    }
  } catch (_e) {
    ElMessage.error('操作失败')
  }
}

// 获取IP段备注
const getSegmentNote = (segment) => {
  return segmentNotes.value[segment] || ''
}

// 编辑IP段备注
const editSegmentNote = async (segment) => {
  const currentNote = getSegmentNote(segment)
  try {
    const { value } = await ElMessageBox.prompt(`请输入 ${segment}.x 的备注`, '编辑备注', {
      inputValue: currentNote,
      inputPlaceholder: '请输入备注内容',
      confirmButtonText: '保存',
      cancelButtonText: '取消',
      inputPattern: /^.{0,100}$/,
      inputErrorMessage: '备注长度不能超过100个字符'
    })
    if (value !== undefined) {
      const noteValue = value.trim()
      await preferencesAPI.saveSegmentNote(segment, noteValue)
      if (noteValue) {
        segmentNotes.value[segment] = noteValue
      } else {
        delete segmentNotes.value[segment]
      }
      ElMessage.success('备注已保存')
    }
  } catch (_e) {
    // 用户取消操作或保存失败
  }
}

// 检查服务器是否被收藏
const isServerFavorited = (serverId) => {
  return serverFavorites.value.has(serverId)
}

// 切换服务器收藏状态
const toggleServerFavorite = async (server) => {
  try {
    const response = await preferencesAPI.toggleServerFavorite(server.id)
    if (response.data.favorited) {
      serverFavorites.value.add(server.id)
      ElMessage.success(`已收藏 ${server.ip_address}`)
    } else {
      serverFavorites.value.delete(server.id)
      ElMessage.success(`已取消收藏 ${server.ip_address}`)
    }
  } catch (_e) {
    ElMessage.error('操作失败')
  }
}

// 获取表格行样式类名 - 为收藏的服务器添加高亮
const getRowClassName = ({ row }) => {
  if (serverFavorites.value.has(row.id)) {
    return 'favorited-row'
  }
  return ''
}

const activeMenu = computed(() => route.path)

// 常用端口号常量
const RDP_PORT = 3389
const SSH_PORT = 22

// 端口类型信息
const PORT_TYPE_MAP = {
  [SSH_PORT]: { type: 'SSH', osHint: 'Linux/Unix', icon: '🐧', color: 'success' },
  [RDP_PORT]: { type: 'RDP', osHint: 'Windows', icon: '🪟', color: 'primary' },
  23: { type: 'Telnet', osHint: 'Network', icon: '📡', color: 'warning' },
  21: { type: 'FTP', osHint: 'File', icon: '📁', color: 'info' },
  80: { type: 'HTTP', osHint: 'Web', icon: '🌐', color: '' },
  443: { type: 'HTTPS', osHint: 'Web', icon: '🔒', color: 'success' },
  3306: { type: 'MySQL', osHint: 'DB', icon: '🗄️', color: 'warning' },
  5432: { type: 'PostgreSQL', osHint: 'DB', icon: '🐘', color: 'primary' },
}

const getPortTypeName = (port) => {
  return PORT_TYPE_MAP[port]?.type || 'Custom'
}

const getPortTypeIcon = (port) => {
  return PORT_TYPE_MAP[port]?.icon || '🔌'
}

const getPortTagType = (port) => {
  return PORT_TYPE_MAP[port]?.color || 'info'
}

// 获取服务器配置信息（CPU核数和内存大小）
const getServerSpecs = (server) => {
  if (!server.cpu_info && !server.memory_info) return null
  
  // 解析CPU核数
  let cpuCores = ''
  if (server.cpu_info) {
    // 尝试匹配常见的CPU信息格式
    const cpuMatch = server.cpu_info.match(/(\d+)\s*(核|cores?|cpus?|processors?)/i)
    if (cpuMatch) {
      cpuCores = cpuMatch[1]
    } else {
      // 如果是纯数字
      const numMatch = server.cpu_info.match(/^(\d+)$/)
      if (numMatch) {
        cpuCores = numMatch[1]
      }
    }
  }
  
  // 解析内存大小
  let memorySize = ''
  if (server.memory_info) {
    // 尝试匹配内存信息格式，如 "4GB", "4 GB", "4G", "4096MB"
    const memMatch = server.memory_info.match(/(\d+(?:\.\d+)?)\s*(GB|G|MB|M|TB|T)/i)
    if (memMatch) {
      let size = parseFloat(memMatch[1])
      const unit = memMatch[2].toUpperCase()
      // 转换为GB显示 (使用二进制转换 1024，符合计算机内存标准)
      if (unit === 'MB' || unit === 'M') {
        size = Math.round(size / 1024)
        memorySize = size > 0 ? `${size}G` : '<1G'
      } else if (unit === 'TB' || unit === 'T') {
        size = size * 1024
        memorySize = `${Math.round(size)}G`
      } else {
        memorySize = `${Math.round(size)}G`
      }
    } else {
      // 处理纯数字（假设为MB）
      const numMatch = server.memory_info.match(/^(\d+)$/)
      if (numMatch) {
        const sizeMB = parseInt(numMatch[1])
        const sizeGB = Math.round(sizeMB / 1024)
        memorySize = sizeGB > 0 ? `${sizeGB}G` : '<1G'
      }
    }
  }
  
  // 组合显示
  if (cpuCores && memorySize) {
    return `${cpuCores}核${memorySize}`
  } else if (cpuCores) {
    return `${cpuCores}核`
  } else if (memorySize) {
    return memorySize
  }
  return null
}

// 根据OS信息获取图标
const getOsIcon = (osInfo) => {
  if (!osInfo) return '💻'
  const osLower = osInfo.toLowerCase()
  if (osLower.includes('ubuntu') || osLower.includes('debian')) return '🐧'
  if (osLower.includes('centos') || osLower.includes('red hat') || osLower.includes('rhel')) return '🎩'
  if (osLower.includes('windows')) return '🪟'
  if (osLower.includes('mac') || osLower.includes('darwin')) return '🍎'
  if (osLower.includes('linux')) return '🐧'
  return '💻'
}

// Get IP segment (first 3 octets) from IP address
const getIpSegment = (ipAddress) => {
  if (!ipAddress || typeof ipAddress !== 'string') {
    return ''
  }
  const parts = ipAddress.split('.')
  if (parts.length >= 3) {
    return `${parts[0]}.${parts[1]}.${parts[2]}`
  }
  return ipAddress
}

// Compare IP segments numerically
const compareIpSegments = (a, b) => {
  const partsA = a.segment.split('.').map(Number)
  const partsB = b.segment.split('.').map(Number)
  for (let i = 0; i < Math.min(partsA.length, partsB.length); i++) {
    if (partsA[i] !== partsB[i]) {
      return partsA[i] - partsB[i]
    }
  }
  return partsA.length - partsB.length
}

// Compare IP addresses numerically (e.g., 38.181.53.2 to 38.181.53.10)
const compareIpAddresses = (a, b) => {
  // Handle null/undefined ip_address
  if (!a?.ip_address || !b?.ip_address) {
    if (!a?.ip_address && !b?.ip_address) return 0
    return !a?.ip_address ? 1 : -1
  }
  
  const partsA = a.ip_address.split('.').map(Number)
  const partsB = b.ip_address.split('.').map(Number)
  
  // Compare up to 4 octets, handling cases where IP may have fewer parts
  for (let i = 0; i < 4; i++) {
    const numA = i < partsA.length ? partsA[i] : 0
    const numB = i < partsB.length ? partsB[i] : 0
    // Handle NaN values (invalid IP parts)
    const valA = isNaN(numA) ? 0 : numA
    const valB = isNaN(numB) ? 0 : numB
    if (valA !== valB) {
      return valA - valB
    }
  }
  return 0
}

const getLastUpdateTime = (server) => {
  if (!server) return null
  return server.last_checked || server.updated_at || server.created_at
}

const getUpdatedTimestamp = (server) => {
  const timeStr = getLastUpdateTime(server)
  if (!timeStr) return Number.NEGATIVE_INFINITY
  const time = new Date(timeStr).getTime()
  return isNaN(time) ? Number.NEGATIVE_INFINITY : time
}

// Computed counts for filter buttons
// Helper function to check if a server is from batch query (一键查询)
const isBatchServer = (server) => {
  return server.source === 'batch_online' || server.source === 'batch_error'
}
// Helper function to check if a server is "normal" (root user + online + no error, excluding batch query servers)
const isNormalServer = (server) => {
  return server.username === 'root' && server.status === 'online' && !server.error_type && !isBatchServer(server)
}
// 正常: root用户 + 在线 + 无错误（排除一键查询服务器）
const normalCount = computed(() => servers.value.filter(isNormalServer).length)
// 离线 (排除Administrator用户和一键查询服务器)
const offlineCount = computed(() => servers.value.filter(s => s.status === 'offline' && s.username !== 'Administrator' && !isBatchServer(s)).length)
// 未知（排除一键查询服务器）
const unknownCount = computed(() => servers.value.filter(s => s.status === 'unknown' && !isBatchServer(s)).length)
// 错误: 在线且有error_type的 (排除Administrator用户、离线的服务器和一键查询服务器)
const errorCount = computed(() => servers.value.filter(s => s.status === 'online' && s.error_type && s.username !== 'Administrator' && !isBatchServer(s)).length)
// 电脑 (Windows RDP) - 包含Administrator用户的错误和离线状态（排除一键查询服务器）
const computerCount = computed(() => servers.value.filter(s => s.port === RDP_PORT && !isBatchServer(s)).length)
// 一键查询在线
const batchOnlineCount = computed(() => servers.value.filter(s => s.source === 'batch_online').length)
// 一键查询错误
const batchErrorCount = computed(() => servers.value.filter(s => s.source === 'batch_error').length)

// Show filtered servers in dialog
const showFilteredServersDialog = (filterType) => {
  let result = servers.value
  let title = ''
  
  if (filterType === 'normal') {
    // 正常: root用户 + 在线 + 无错误（排除一键查询服务器）
    result = result.filter(isNormalServer)
    title = '正常服务器'
  } else if (filterType === 'offline') {
    // 离线服务器：排除Administrator用户和一键查询服务器
    result = result.filter(server => server.status === 'offline' && server.username !== 'Administrator' && !isBatchServer(server))
    title = '离线服务器'
  } else if (filterType === 'unknown') {
    // 未知状态服务器（排除一键查询服务器）
    result = result.filter(server => server.status === 'unknown' && !isBatchServer(server))
    title = '未知状态服务器'
  } else if (filterType === 'error') {
    // 错误服务器：在线但有error_type的（排除Administrator用户、离线的服务器和一键查询服务器）
    result = result.filter(server => server.status === 'online' && server.error_type && server.username !== 'Administrator' && !isBatchServer(server))
    title = '错误服务器'
  } else if (filterType === 'computer') {
    // 电脑对话框：显示所有Windows RDP服务器（包含Administrator的错误和离线状态，排除一键查询服务器）
    result = result.filter(server => server.port === RDP_PORT && !isBatchServer(server))
    title = '电脑 (Windows RDP)'
  } else if (filterType === 'batch_online') {
    result = result.filter(server => server.source === 'batch_online')
    title = '一键查询在线'
  } else if (filterType === 'batch_error') {
    result = result.filter(server => server.source === 'batch_error')
    title = '一键查询错误'
  }
  
  // 根据filterType设置排序逻辑
  filteredDialogType.value = filterType
  
  // 辅助函数：收藏优先排序
  const sortWithFavorites = (a, b, secondarySort) => {
    const aFavorited = serverFavorites.value.has(a.id) ? 0 : 1
    const bFavorited = serverFavorites.value.has(b.id) ? 0 : 1
    if (aFavorited !== bFavorited) return aFavorited - bFavorited
    return secondarySort(a, b)
  }
  
  if (filterType === 'computer') {
    // 电脑对话框排序：收藏优先 > 正常 > 错误 > 离线
    filteredDialogServers.value = [...result].sort((a, b) => {
      return sortWithFavorites(a, b, (serverA, serverB) => {
        // 定义状态优先级：正常(0) > 错误(1) > 离线(2)
        const getStatusPriority = (server) => {
          if (server.status === 'online' && !server.error_type) return 0  // 正常
          if (server.error_type) return 1                                  // 错误（包括在线但有错误的）
          if (server.status === 'offline') return 2                        // 离线
          return 3  // 其他状态
        }
        const priorityDiff = getStatusPriority(serverA) - getStatusPriority(serverB)
        if (priorityDiff !== 0) return priorityDiff
        // 同优先级按更新时间排序
        return getUpdatedTimestamp(serverB) - getUpdatedTimestamp(serverA)
      })
    })
  } else if (filterType === 'error') {
    // 错误对话框排序：收藏优先 > 端口关闭 -> 密码错误 -> 其他类型错误
    filteredDialogServers.value = [...result].sort((a, b) => {
      return sortWithFavorites(a, b, (serverA, serverB) => {
        // 定义错误类型优先级：端口关闭(0) -> 密码错误(1) -> 其他错误(2)
        const getErrorPriority = (server) => {
          if (server.error_type === 'port_closed') return 0      // 端口关闭
          if (server.error_type === 'auth_failed') return 1      // 密码错误
          return 2                                                // 其他类型错误
        }
        const priorityDiff = getErrorPriority(serverA) - getErrorPriority(serverB)
        if (priorityDiff !== 0) return priorityDiff
        // 同优先级按更新时间排序
        return getUpdatedTimestamp(serverB) - getUpdatedTimestamp(serverA)
      })
    })
  } else {
    // 其他对话框：收藏优先 > 按更新时间排序
    filteredDialogServers.value = [...result].sort((a, b) => {
      return sortWithFavorites(a, b, (serverA, serverB) => {
        return getUpdatedTimestamp(serverB) - getUpdatedTimestamp(serverA)
      })
    })
  }
  
  filteredDialogTitle.value = title
  filteredDialogCurrentPage.value = 1
  // 一键查询对话框：初始化展开所有IP段
  if (filterType === 'batch_online' || filterType === 'batch_error') {
    expandedBatchSegments.value = new Set(
      filteredDialogServers.value
        .map(server => getIpSegment(server.ip_address))
        .filter(segment => segment !== '')
    )
    allBatchSegmentsExpanded.value = true
  }
  filteredDialogVisible.value = true
}

// Filter servers by search text
const filteredServers = computed(() => {
  let result = servers.value
  
  // Apply search filter
  if (searchText.value) {
    const search = searchText.value.toLowerCase()
    result = result.filter(server =>
      server.ip_address.toLowerCase().includes(search) ||
      server.username.toLowerCase().includes(search) ||
      (server.notes && server.notes.toLowerCase().includes(search))
    )
  }
  
  // Note: Sorting by update time is handled in groupedServers computed property
  return result
})

// Group servers by IP segment
const groupedServers = computed(() => {
  const filtered = filteredServers.value
  const segmentMap = new Map()

  // Group servers by IP segment
  filtered.forEach(server => {
    const segment = getIpSegment(server.ip_address)
    if (!segmentMap.has(segment)) {
      segmentMap.set(segment, [])
    }
    segmentMap.get(segment).push(server)
  })

  // Convert to tree structure for el-table
  const result = []
  segmentMap.forEach((serverList, segment) => {
    // Count online, offline, error, and batch servers in single pass
    let onlineCount = 0
    let offlineCount = 0
    let errorCount = 0
    let batchOnlineCount = 0
    let batchErrorCount = 0
    const sortedServers = [...serverList].sort(
      (a, b) => getUpdatedTimestamp(b) - getUpdatedTimestamp(a)
    )
    for (const s of sortedServers) {
      // 一键查询服务器单独计数，不计入常规分类
      if (s.source === 'batch_online' || s.source === 'batch_error') {
        if (s.source === 'batch_online') {
          batchOnlineCount++
        } else {
          batchErrorCount++
        }
      } else if (s.status === 'online') {
        onlineCount++
        // Count servers that have error_type as having errors
        if (s.error_type) {
          errorCount++
        }
      } else if (s.status === 'offline') {
        offlineCount++
      }
    }

    result.push({
      segmentKey: `segment-${segment}`,
      segment: segment,
      isSegment: true,
      count: serverList.length,
      onlineCount: onlineCount,
      offlineCount: offlineCount,
      errorCount: errorCount,
      batchOnlineCount: batchOnlineCount,
      batchErrorCount: batchErrorCount,
      hasChildren: true,
      latestUpdated: getUpdatedTimestamp(sortedServers[0]),
      servers: sortedServers.map(s => ({
        ...s,
        segmentKey: `server-${s.id}`
      }))
    })
  })

  // Sort: favorites first, then by latest update time, fallback to numeric segment order
  result.sort((a, b) => {
    const aFavorited = segmentFavorites.value.has(a.segment) ? 0 : 1
    const bFavorited = segmentFavorites.value.has(b.segment) ? 0 : 1
    if (aFavorited !== bFavorited) return aFavorited - bFavorited
    const diff = (b.latestUpdated || 0) - (a.latestUpdated || 0)
    if (diff !== 0) return diff
    return compareIpSegments(a, b)
  })

  return result
})

// Paginated segments for the grid display
const paginatedSegments = computed(() => {
  const start = (segmentsCurrentPage.value - 1) * PAGE_SIZE
  const end = start + PAGE_SIZE
  return groupedServers.value.slice(start, end)
})

// Sorted servers for segment dialog based on sortBy option
// 收藏的服务器始终优先显示
const sortedSegmentServers = computed(() => {
  if (!selectedSegment.value) return []
  const servers = [...selectedSegment.value.servers]
  
  // 首先按收藏状态排序，收藏的在前
  servers.sort((a, b) => {
    const aFavorited = serverFavorites.value.has(a.id) ? 0 : 1
    const bFavorited = serverFavorites.value.has(b.id) ? 0 : 1
    if (aFavorited !== bFavorited) return aFavorited - bFavorited
    
    // 同收藏状态下，根据用户选择的排序方式
    if (segmentDialogSortBy.value === 'ip') {
      return compareIpAddresses(a, b)
    } else {
      return getUpdatedTimestamp(b) - getUpdatedTimestamp(a)
    }
  })
  
  return servers
})

// Paginated servers for segment dialog
const paginatedSegmentServers = computed(() => {
  if (!selectedSegment.value) return []
  const start = (segmentDialogCurrentPage.value - 1) * PAGE_SIZE
  const end = start + PAGE_SIZE
  return sortedSegmentServers.value.slice(start, end)
})

// Paginated servers for filtered dialog
const paginatedFilteredServers = computed(() => {
  const start = (filteredDialogCurrentPage.value - 1) * PAGE_SIZE
  const end = start + PAGE_SIZE
  return filteredDialogServers.value.slice(start, end)
})

// 一键查询按IP段分组
const isBatchDialogType = computed(() => {
  return filteredDialogType.value === 'batch_online' || filteredDialogType.value === 'batch_error'
})

const groupedBatchServers = computed(() => {
  if (!isBatchDialogType.value) return []
  const segmentMap = new Map()
  filteredDialogServers.value.forEach(server => {
    const segment = getIpSegment(server.ip_address)
    if (!segment) return // 跳过空IP段
    if (!segmentMap.has(segment)) {
      segmentMap.set(segment, [])
    }
    segmentMap.get(segment).push(server)
  })
  const result = []
  segmentMap.forEach((serverList, segment) => {
    const sortedServers = [...serverList].sort(compareIpAddresses)
    result.push({
      segment,
      servers: sortedServers,
      count: sortedServers.length,
      note: getSegmentNote(segment)
    })
  })
  // Sort segments numerically (NaN treated as -1, sorted to beginning)
  result.sort((a, b) => {
    const partsA = a.segment.split('.').map(Number)
    const partsB = b.segment.split('.').map(Number)
    for (let i = 0; i < Math.min(partsA.length, partsB.length); i++) {
      const valA = isNaN(partsA[i]) ? -1 : partsA[i]
      const valB = isNaN(partsB[i]) ? -1 : partsB[i]
      if (valA !== valB) return valA - valB
    }
    return partsA.length - partsB.length
  })
  return result
})

const isBatchSegmentExpanded = (segment) => expandedBatchSegments.value.has(segment)

const toggleBatchSegment = (segment) => {
  const newSet = new Set(expandedBatchSegments.value)
  if (newSet.has(segment)) {
    newSet.delete(segment)
  } else {
    newSet.add(segment)
  }
  expandedBatchSegments.value = newSet
  allBatchSegmentsExpanded.value = newSet.size === groupedBatchServers.value.length
}

const toggleAllBatchSegments = () => {
  if (allBatchSegmentsExpanded.value) {
    expandedBatchSegments.value = new Set()
    allBatchSegmentsExpanded.value = false
  } else {
    expandedBatchSegments.value = new Set(groupedBatchServers.value.map(g => g.segment))
    allBatchSegmentsExpanded.value = true
  }
}

// 对话框关闭时重置状态
const onFilteredDialogClosed = () => {
  expandedBatchSegments.value = new Set()
  allBatchSegmentsExpanded.value = true
  filteredDialogType.value = ''
}

onMounted(async () => {
  await initSegmentData()
  const userStr = localStorage.getItem('user')
  if (userStr) {
    currentUser.value = JSON.parse(userStr)
  }
  await loadServers()
})

const loadServers = async () => {
  loading.value = true
  loadError.value = ''
  try {
    const response = await serversAPI.getAll()
    const existingServerMap = new Map()
    servers.value.forEach(item => {
      existingServerMap.set(item.id, item)
    })
    servers.value = response.data.map(s => {
      const existing = existingServerMap.get(s.id)
      const checkDetail = s.check_detail ?? existing?.checkDetail ?? ''
      const errorType = s.error_type ?? existing?.error_type ?? ''
      return {
        ...s,
        checking: false,
        checkDetail,
        error_type: errorType
      }
    })
  } catch (error) {
    const message = error.response?.data?.message || error.message || '网络连接失败'
    loadError.value = message
    ElMessage.error(`加载服务器失败: ${message}`)
  } finally {
    loading.value = false
  }
}

const importServersFromFiles = async () => {
  importing.value = true
  try {
    const response = await serversAPI.importFromFiles()
    const { summary, imported: _imported, skipped: _skipped, errors } = response.data
    
    let message = `导入完成: 成功 ${summary.imported_count} 台`
    if (summary.skipped_count > 0) {
      message += `，跳过 ${summary.skipped_count} 台`
    }
    if (summary.error_count > 0) {
      message += `，失败 ${summary.error_count} 个`
    }
    
    if (summary.imported_count > 0) {
      ElMessage.success(message)
      await loadServers()
    } else if (summary.skipped_count > 0 && summary.error_count === 0) {
      ElMessage.warning(message + '（所有服务器已存在）')
    } else if (summary.error_count > 0) {
      ElMessage.warning(message)
      // Consolidate error messages - show first 3 errors max
      const maxErrors = 3
      const errorFiles = errors.slice(0, maxErrors).map(e => e.file).join(', ')
      const remaining = errors.length - maxErrors
      let errorDetail = `失败文件: ${errorFiles}`
      if (remaining > 0) {
        errorDetail += ` 等${remaining}个文件`
      }
      ElMessage.error(errorDetail)
    } else {
      ElMessage.info('未找到可导入的服务器文件')
    }
  } catch (error) {
    const message = error.response?.data?.message || error.message || '导入失败'
    ElMessage.error(`导入服务器失败: ${message}`)
  } finally {
    importing.value = false
  }
}

const showAddDialog = () => {
  isEdit.value = false
  currentServer.value = null
  dialogVisible.value = true
}

const editServer = (server) => {
  isEdit.value = true
  currentServer.value = server
  dialogVisible.value = true
}

const viewServer = async (server) => {
  selectedServer.value = server
  selectedServerPassword.value = ''
  loadingPassword.value = true
  detailDialogVisible.value = true
  
  // Fetch password separately
  try {
    const response = await serversAPI.getPassword(server.id)
    selectedServerPassword.value = response.data.password
  } catch (_error) {
    selectedServerPassword.value = '获取失败'
  } finally {
    loadingPassword.value = false
  }
}

const viewSegment = (segment) => {
  selectedSegment.value = segment
  segmentDialogCurrentPage.value = 1
  segmentDialogVisible.value = true
}

// 检测服务器状态
const checkServer = async (server) => {
  if (server.checking) return
  
  server.checking = true
  try {
    const response = await serversAPI.check(server.id)
    const status = response.data.status

    // Update server status in both servers list and segment
    server.status = status.overall
    server.checkDetail = response.data.check_detail ?? status.detail ?? ''
    server.error_type = response.data.error_type ?? status.error_type ?? ''
    if (response.data.last_checked) {
      server.last_checked = response.data.last_checked
    }
    if (response.data.updated_at) {
      server.updated_at = response.data.updated_at
    }
    
    // Show result message based on status
    if (status.overall === 'online') {
      if (status.auth === true) {
        ElMessage.success(`服务器 ${server.ip_address} 检测成功: ${status.detail}`)
      } else if (status.port === true) {
        ElMessage.success(`服务器 ${server.ip_address} 端口开放，但认证未验证`)
      } else {
        ElMessage.success(`服务器 ${server.ip_address} 可达`)
      }
    } else {
      ElMessage.warning(`服务器 ${server.ip_address}: ${status.detail}`)
    }
  } catch (error) {
    const errorMsg = error.response?.data?.message || error.message || '网络连接失败'
    ElMessage.error(`检测服务器 ${server.ip_address} 失败: ${errorMsg}`)
  } finally {
    server.checking = false
  }
}

// 终端连接功能
const openTerminal = (server) => {
  terminalServer.value = server
  terminalDialogVisible.value = true
  // Auto-check RDP port status when opening RDP server dialog
  if (server.port === RDP_PORT) {
    rdpPortStatus.value = 'unknown'
    checkRdpPort(server)
  }
}

const handleTerminalDialogClosed = () => {
  // 关闭对话框时断开终端连接
  if (terminalRef.value) {
    terminalRef.value.disconnect()
  }
  // 重置文件浏览器状态
  terminalConnected.value = false
  currentPath.value = '/'
  fileList.value = []
  fileBrowserError.value = ''
  // 重置 RDP 端口状态
  rdpPortStatus.value = 'unknown'
}

const handleTerminalConnected = () => {
  ElMessage.success('终端连接成功')
  terminalConnected.value = true
  // 连接成功后自动加载根目录文件列表
  loadDirectoryFiles('/')
}

const handleTerminalDisconnected = () => {
  ElMessage.info('终端已断开')
  terminalConnected.value = false
}

const handleTerminalError = (errorMsg) => {
  ElMessage.error(errorMsg || '终端连接失败')
}

// 文件浏览器方法
const loadDirectoryFiles = async (path) => {
  if (!terminalServer.value) return
  
  fileBrowserLoading.value = true
  fileBrowserError.value = ''
  
  try {
    const response = await serversAPI.listDirectory(terminalServer.value.id, path)
    fileList.value = response.data.files || []
    currentPath.value = response.data.path || path
  } catch (error) {
    const message = error.response?.data?.message || '加载目录失败'
    fileBrowserError.value = message
    fileList.value = []
  } finally {
    fileBrowserLoading.value = false
  }
}

const refreshFileList = () => {
  loadDirectoryFiles(currentPath.value)
}

const navigateToPath = (index) => {
  if (index === 0) {
    loadDirectoryFiles('/')
  } else {
    const parts = currentPath.value.split('/').filter(p => p !== '')
    const newPath = '/' + parts.slice(0, index).join('/')
    loadDirectoryFiles(newPath)
  }
}

const openDirectory = (file) => {
  const newPath = currentPath.value === '/' 
    ? `/${file.name}` 
    : `${currentPath.value}/${file.name}`
  loadDirectoryFiles(newPath)
}

const handleFileClick = (row) => {
  if (row.type === 'directory') {
    openDirectory(row)
  }
}

// 文件浏览器辅助函数
const getFileExtIcon = (filename) => {
  const ext = filename.split('.').pop()?.toLowerCase() || ''
  return FILE_EXTENSION_ICONS[ext] || '📄'
}

const getFileIconClass = (file) => {
  if (file.type === 'directory') return 'folder'
  if (file.type === 'link') return 'link'
  const ext = file.name.split('.').pop()?.toLowerCase() || ''
  if (CODE_FILE_EXTENSIONS.includes(ext)) return 'code'
  if (CONFIG_FILE_EXTENSIONS.includes(ext)) return 'config'
  return 'default'
}

const getFileTypeTagType = (type) => {
  const typeMap = {
    'directory': 'warning',
    'link': 'info',
    'file': ''
  }
  return typeMap[type] || ''
}

const getFileTypeLabel = (type) => {
  const labelMap = {
    'directory': '目录',
    'link': '链接',
    'file': '文件'
  }
  return labelMap[type] || '未知'
}

const isHiddenFile = (filename) => {
  return filename.startsWith('.')
}

const getFileRowClass = ({ row }) => {
  const classes = []
  if (row.type === 'directory') classes.push('directory-row')
  if (isHiddenFile(row.name)) classes.push('hidden-file-row')
  return classes.join(' ')
}

const viewFileContent = async (file) => {
  if (!terminalServer.value) return
  
  const filePath = currentPath.value === '/' 
    ? `/${file.name}` 
    : `${currentPath.value}/${file.name}`
  
  fileEditorPath.value = filePath
  fileEditorReadonly.value = true
  fileEditorLoading.value = true
  fileEditorVisible.value = true
  fileEditorContent.value = ''
  
  try {
    const response = await serversAPI.readFile(terminalServer.value.id, filePath)
    fileEditorContent.value = response.data.content || ''
  } catch (error) {
    const message = error.response?.data?.message || '读取文件失败'
    ElMessage.error(message)
    fileEditorVisible.value = false
  } finally {
    fileEditorLoading.value = false
  }
}

const enableEditing = () => {
  fileEditorReadonly.value = false
}

const saveFileContent = async () => {
  if (!terminalServer.value || !fileEditorPath.value) return
  
  fileEditorSaving.value = true
  
  try {
    await serversAPI.saveFile(terminalServer.value.id, fileEditorPath.value, fileEditorContent.value)
    ElMessage.success('文件保存成功')
    fileEditorReadonly.value = true
  } catch (error) {
    const message = error.response?.data?.message || '保存文件失败'
    ElMessage.error(message)
  } finally {
    fileEditorSaving.value = false
  }
}

const getSshCommand = (server) => {
  if (!server) return ''
  if (server.port === SSH_PORT) {
    return `ssh ${server.username}@${server.ip_address}`
  } else if (server.port === RDP_PORT) {
    return `mstsc /v:${server.ip_address}`
  } else {
    return `ssh -p ${server.port} ${server.username}@${server.ip_address}`
  }
}

const copySshCommand = async (server) => {
  const command = getSshCommand(server)
  try {
    await navigator.clipboard.writeText(command)
    ElMessage.success('命令已复制到剪贴板')
  } catch (_error) {
    ElMessage.error('复制失败，请手动复制')
  }
}

const downloadRdpFile = async (server) => {
  if (!server) return
  try {
    // Parse resolution from the rdpResolution ref
    const [width, height] = rdpResolution.value.split('x').map(Number)
    const settings = {
      width,
      height,
      fullscreen: rdpSettings.fullscreen,
      clipboard: rdpSettings.clipboard,
      drives: rdpSettings.drives,
      admin: rdpSettings.admin,
      multimon: rdpSettings.multimon
    }
    const response = await serversAPI.downloadRdpFile(server.id, settings)
    const blob = new Blob([response.data], { type: 'application/x-rdp' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${server.ip_address}.rdp`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success('RDP 连接文件已下载，双击即可后台连接远程桌面')
  } catch (_error) {
    ElMessage.error('下载 RDP 文件失败')
  }
}

const launchRdpConnection = (server) => {
  if (!server) return
  // Use ms-rd URI scheme to attempt to launch the system RDP client directly
  const encodedUsername = encodeURIComponent(server.username)
  const rdpUri = `ms-rd:full%20address=s:${server.ip_address}:3389&username=s:${encodedUsername}`
  const link = document.createElement('a')
  link.href = rdpUri
  link.style.display = 'none'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  ElMessage.info({
    message: '正在尝试启动远程桌面客户端，如未自动打开，请下载 RDP 文件后双击连接',
    duration: 5000
  })
}

const checkRdpPort = async (server) => {
  if (!server) return
  rdpPortStatus.value = 'checking'
  try {
    const response = await serversAPI.checkIpStatus(server.ip_address)
    const data = response.data
    rdpPortStatus.value = data.port_3389 ? 'online' : 'offline'
  } catch (_error) {
    rdpPortStatus.value = 'offline'
  }
}

const handleSubmit = async (formData) => {
  try {
    if (isEdit.value) {
      await serversAPI.update(currentServer.value.id, formData)
      ElMessage.success('服务器更新成功')
    } else {
      await serversAPI.create(formData)
      ElMessage.success('服务器新增成功')
    }
    dialogVisible.value = false
    await loadServers()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '操作失败')
  }
}

const deleteServer = async (server) => {
  try {
    await ElMessageBox.confirm(
      `确认删除服务器 ${server.ip_address} 吗？`,
      '警告',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await serversAPI.delete(server.id)
    ElMessage.success('删除服务器成功')
    await loadServers()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除服务器失败')
    }
  }
}

const refreshSystemInfo = async () => {
  if (!selectedServer.value) return
  
  refreshing.value = true
  try {
    const response = await serversAPI.getSystemInfo(selectedServer.value.id)
    selectedServer.value.os_info = response.data.os
    selectedServer.value.cpu_info = response.data.cpu
    selectedServer.value.memory_info = response.data.memory
    selectedServer.value.disk_info = response.data.disk
    selectedServer.value.uptime = response.data.uptime
    ElMessage.success('系统信息已刷新')
    await loadServers()
  } catch (_error) {
    ElMessage.error('刷新系统信息失败')
  } finally {
    refreshing.value = false
  }
}

// 编辑服务器备注
const editServerNote = async (server) => {
  const currentNote = server.notes || ''
  try {
    const { value } = await ElMessageBox.prompt(`请输入 ${server.ip_address} 的备注`, '编辑备注', {
      inputValue: currentNote,
      inputPlaceholder: '请输入备注内容',
      confirmButtonText: '保存',
      cancelButtonText: '取消',
      inputPattern: /^.{0,255}$/,
      inputErrorMessage: '备注长度不能超过255个字符'
    })
    if (value !== undefined) {
      const newNote = value.trim()
      // 调用API更新备注
      await serversAPI.update(server.id, { notes: newNote })
      server.notes = newNote
      // 更新servers列表中的对应服务器
      const serverInList = servers.value.find(s => s.id === server.id)
      if (serverInList) {
        serverInList.notes = newNote
      }
      ElMessage.success('备注已保存')
    }
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      ElMessage.error('保存备注失败')
    }
  }
}

// 批量获取正常服务器的系统信息
const batchGetSystemInfo = async () => {
  if (filteredDialogServers.value.length === 0) return
  
  batchGettingSystemInfo.value = true
  
  try {
    // 创建所有请求的Promise数组
    const promises = filteredDialogServers.value.map(server => 
      serversAPI.getSystemInfo(server.id)
        .then(response => ({ server, response, success: true }))
        .catch(() => ({ server, success: false }))
    )
    
    // 并发执行所有请求
    const results = await Promise.all(promises)
    
    let successCount = 0
    let failCount = 0
    
    // 处理结果
    results.forEach(result => {
      if (result.success) {
        result.server.os_info = result.response.data.os
        result.server.cpu_info = result.response.data.cpu
        result.server.memory_info = result.response.data.memory
        result.server.disk_info = result.response.data.disk
        result.server.uptime = result.response.data.uptime
        successCount++
      } else {
        failCount++
      }
    })
    
    if (successCount > 0) {
      ElMessage.success(`成功获取 ${successCount} 台服务器的系统信息${failCount > 0 ? `，${failCount} 台失败` : ''}`)
      await loadServers()
    } else if (failCount > 0) {
      ElMessage.error(`获取系统信息失败，共 ${failCount} 台服务器`)
    }
  } catch (_error) {
    ElMessage.error('批量获取系统信息失败')
  } finally {
    batchGettingSystemInfo.value = false
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return '从未'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })
}

const handleMenuSelect = (index) => {
  router.push(index)
}

const handleCommand = async (command) => {
  if (command === 'changePassword') {
    // Reset form
    passwordForm.old_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm_password = ''
    passwordDialogVisible.value = true
  } else if (command === 'logout') {
    try {
      await authAPI.logout()
    } catch (_error) {
      // 忽略登出错误，因为仍然需要清除本地存储
    }
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    router.push('/login')
  }
}

const handleChangePassword = async () => {
  if (!passwordFormRef.value) return
  
  await passwordFormRef.value.validate(async (valid) => {
    if (valid) {
      changingPassword.value = true
      try {
        await authAPI.changePassword({
          old_password: passwordForm.old_password,
          new_password: passwordForm.new_password
        })
        ElMessage.success('密码修改成功')
        passwordDialogVisible.value = false
      } catch (error) {
        const message = error.response?.data?.message || '密码修改失败'
        ElMessage.error(message)
      } finally {
        changingPassword.value = false
      }
    }
  })
}
</script>

<style scoped>
/* Page container */
.page-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #f0f4f8 0%, #d7e3ec 50%, #e8eef3 100%);
}

/* Header styles - 统一淡蓝色导航美化 */
.header-container {
  background: linear-gradient(135deg, #5b9bd5 0%, #7db8e8 50%, #9ecae1 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 4px 24px 0 rgba(91, 155, 213, 0.35);
  height: 70px;
  padding: 0 30px;
  position: relative;
}

.header-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #90cdf4 0%, #bee3f8 50%, #e0f0ff 100%);
}

.header-logo {
  display: flex;
  align-items: center;
  gap: 14px;
}

.header-logo :deep(.el-icon) {
  color: #ffffff;
  filter: drop-shadow(0 2px 4px rgba(255, 255, 255, 0.4));
}

.header-logo h2 {
  margin: 0;
  font-weight: 700;
  font-size: 22px;
  letter-spacing: 1px;
  background: linear-gradient(135deg, #fff 0%, #e2e8f0 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.header-menu {
  border: none;
  flex: 1;
  margin-left: 50px;
  background: transparent !important;
}

.header-menu :deep(.el-menu-item) {
  color: rgba(255, 255, 255, 0.9) !important;
  font-weight: 500;
  font-size: 15px;
  border-radius: 8px;
  margin: 0 4px;
  transition: all 0.3s ease;
}

.header-menu :deep(.el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.2) !important;
  color: #fff !important;
}

.header-menu :deep(.el-menu-item.is-active) {
  background: rgba(255, 255, 255, 0.25) !important;
  color: #fff !important;
  box-shadow: 0 2px 8px rgba(255, 255, 255, 0.2);
}

/* 子菜单样式 */
.header-menu :deep(.el-sub-menu__title) {
  color: rgba(255, 255, 255, 0.9) !important;
  font-weight: 500;
  font-size: 15px;
  border-radius: 8px;
  margin: 0 4px;
  transition: all 0.3s ease;
}

.header-menu :deep(.el-sub-menu__title:hover) {
  background: rgba(255, 255, 255, 0.2) !important;
  color: #fff !important;
}

.header-menu :deep(.el-sub-menu.is-active .el-sub-menu__title) {
  background: rgba(255, 255, 255, 0.25) !important;
  color: #fff !important;
  box-shadow: 0 2px 8px rgba(255, 255, 255, 0.2);
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 10px 16px;
  color: white;
  transition: all 0.3s ease;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
}

.user-dropdown:hover {
  background: rgba(255, 255, 255, 0.25);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* Content wrapper */
.content-wrapper {
  padding: 28px;
  max-width: 1600px;
  margin: 0 auto;
}

/* Card styles - 企业级卡片美化 */
.server-card {
  border-radius: 16px;
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.1);
  border: none;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
}

.server-card :deep(.el-card__header) {
  padding: 20px 28px;
  border-bottom: 1px solid #e8ecf1;
  background: linear-gradient(135deg, #fafbfc 0%, #f5f7fa 100%);
}

.server-card :deep(.el-card__body) {
  padding: 28px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 22px;
  font-weight: 700;
  color: #1e3a5f;
  letter-spacing: 0.5px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.header-actions :deep(.el-button) {
  border-radius: 10px;
  font-weight: 500;
  padding: 10px 20px;
  transition: all 0.3s ease;
}

.header-actions :deep(.el-button:hover) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.search-filter-row {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 24px;
}

.search-input {
  max-width: 320px;
  flex-shrink: 0;
}

.search-input :deep(.el-input__wrapper) {
  border-radius: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  padding: 4px 16px;
}

.search-input :deep(.el-input__wrapper:hover) {
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
}

.search-input :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.25);
}

.filter-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.filter-buttons :deep(.el-button) {
  border-radius: 20px;
  padding: 8px 16px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.filter-buttons :deep(.el-button:hover) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.filter-buttons :deep(.el-button--success) {
  background: linear-gradient(135deg, #67c23a 0%, #529b2e 100%);
  border-color: #67c23a;
}

.filter-buttons :deep(.el-button--danger) {
  background: linear-gradient(135deg, #f56c6c 0%, #dd6161 100%);
  border-color: #f56c6c;
}

.filter-buttons :deep(.el-button--info) {
  background: linear-gradient(135deg, #909399 0%, #73767a 100%);
  border-color: #909399;
}

.filter-buttons :deep(.el-button--warning) {
  background: linear-gradient(135deg, #e6a23c 0%, #cf9236 100%);
  border-color: #e6a23c;
}

.filter-buttons :deep(.el-button--primary) {
  background: linear-gradient(135deg, #409EFF 0%, #337ecc 100%);
  border-color: #409EFF;
}

@media (max-width: 768px) {
  .search-filter-row {
    flex-direction: column;
    align-items: stretch;
  }
  
  .search-input {
    max-width: 100%;
  }
  
  .filter-buttons {
    justify-content: flex-start;
  }
}

/* IP段卡片网格布局 - 每行3个 */
.segments-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

@media (max-width: 1200px) {
  .segments-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .segments-grid {
    grid-template-columns: 1fr;
  }
}

/* IP段卡片 - 增大尺寸，企业级美化 */
.segment-card {
  background: linear-gradient(145deg, #ffffff 0%, #f8fafc 100%);
  border-radius: 16px;
  padding: 16px 18px;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  border: 2px solid #e2e8f0;
  box-shadow: 0 4px 16px 0 rgba(0, 0, 0, 0.06);
  position: relative;
  overflow: hidden;
}

.segment-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #3182ce 0%, #4fd1c5 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.segment-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px 0 rgba(49, 130, 206, 0.2);
  border-color: #3182ce;
}

.segment-card:hover::before {
  opacity: 1;
}

.segment-card.is-favorited {
  border-color: #ed8936;
  background: linear-gradient(145deg, #fffaf0 0%, #feebc8 100%);
}

.segment-card.is-favorited::before {
  background: linear-gradient(90deg, #ed8936 0%, #f6ad55 100%);
  opacity: 1;
}

/* 高级美化 - 动态光效 */
.segment-card::after {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient(
    45deg,
    transparent 30%,
    rgba(255, 255, 255, 0.15) 50%,
    transparent 70%
  );
  transform: rotate(45deg) translateX(-100%);
  transition: transform 0.6s ease;
  pointer-events: none;
}

.segment-card:hover::after {
  transform: rotate(45deg) translateX(100%);
}

/* 高级美化 - 收藏卡片闪烁动画 */
.segment-card.is-favorited {
  animation: favoritePulse 2s ease-in-out infinite;
}

@keyframes favoritePulse {
  0%, 100% {
    box-shadow: 0 4px 20px 0 rgba(237, 137, 54, 0.2);
  }
  50% {
    box-shadow: 0 8px 30px 0 rgba(237, 137, 54, 0.35);
  }
}

/* 减少动效偏好 */
@media (prefers-reduced-motion: reduce) {
  .segment-card.is-favorited {
    animation: none;
    box-shadow: 0 4px 20px 0 rgba(237, 137, 54, 0.25);
  }
  
  .segment-card::after {
    display: none;
  }
}

.segment-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.ip-segment-title {
  font-size: 20px;
  font-weight: 800;
  color: #1e3a5f;
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  letter-spacing: 0.5px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  position: relative;
  padding-left: 12px;
}

.ip-segment-title::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 20px;
  background: linear-gradient(180deg, #3182ce 0%, #4fd1c5 100%);
  border-radius: 2px;
}

.segment-card.is-favorited .ip-segment-title::before {
  background: linear-gradient(180deg, #ed8936 0%, #f6ad55 100%);
}

.count-tag {
  background: linear-gradient(135deg, #c6f6d5 0%, #9ae6b4 100%);
  border-color: #68d391;
  color: #276749;
  font-size: 13px;
  font-weight: 700;
  padding: 8px 14px;
  border-radius: 20px;
  box-shadow: 0 2px 8px rgba(104, 211, 145, 0.3);
}

.segment-card-status {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.segment-card-status :deep(.el-tag) {
  font-size: 13px;
  padding: 8px 12px;
  font-weight: 600;
  border-radius: 8px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.segment-card-status :deep(.el-tag--success) {
  background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
}

.segment-card-status :deep(.el-tag--danger) {
  background: linear-gradient(135deg, #fc8181 0%, #f56565 100%);
}

.error-count {
  color: #fed7d7;
  font-weight: 700;
}

/* IP段备注显示 */
.segment-card-note {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: linear-gradient(135deg, #ebf8ff 0%, #e6fffa 100%);
  border-radius: 10px;
  margin-bottom: 14px;
  border: 1px solid #bee3f8;
  cursor: pointer;
  transition: all 0.3s ease;
}

.segment-card-note:hover {
  background: linear-gradient(135deg, #bee3f8 0%, #b2f5ea 100%);
  border-color: #90cdf4;
}

.note-display-icon {
  color: #3182ce;
  font-size: 16px;
  flex-shrink: 0;
}

.note-display-text {
  font-size: 14px;
  color: #2c5282;
  line-height: 1.4;
  word-break: break-word;
}

.segment-card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid #e2e8f0;
}

.segment-card-actions-left {
  display: flex;
  gap: 18px;
  align-items: center;
}

.action-icon {
  cursor: pointer;
  font-size: 36px;
  color: #a0aec0;
  transition: all 0.3s ease;
  padding: 12px;
  border-radius: 12px;
}

.action-icon:hover {
  transform: scale(1.15);
  background: rgba(0, 0, 0, 0.06);
}

.favorite-icon:hover {
  color: #ed8936;
  background: rgba(237, 137, 54, 0.1);
}

.favorite-icon.is-favorited {
  color: #ed8936;
}

.note-icon:hover {
  color: #3182ce;
  background: rgba(49, 130, 206, 0.1);
}

.note-icon.has-note {
  color: #3182ce;
}

.segment-card-footer :deep(.el-button) {
  border-radius: 10px;
  font-weight: 600;
  padding: 10px 20px;
}

/* IP cell styles */
.ip-cell {
  display: flex;
  gap: 2px;
  flex-direction: column;
  align-items: flex-start;
}

.ip-text {
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 13px;
  color: #303133;
  font-weight: 500;
}

.updated-time {
  font-size: 11px;
  color: #a0aec0;
  line-height: 1.2;
  display: inline-flex;
  align-items: center;
  gap: 2px;
}

.time-icon {
  font-size: 11px;
}

/* Port cell styles */
.port-cell {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.port-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.specs-row {
  display: flex;
  align-items: center;
}

.specs-tag {
  font-size: 11px;
  padding: 2px 8px;
  background: linear-gradient(135deg, #f0f9eb 0%, #e8f5e1 100%);
  border-color: #c2e7b0;
  color: #67c23a;
  font-weight: 500;
}

/* OS info text in table */
.os-info-text {
  font-size: 13px;
  color: #4a5568;
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Notes text in table */
.notes-text {
  color: #4a5568;
  font-size: 13px;
  word-break: break-word;
  white-space: pre-wrap;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Editable note styles in table */
.editable-note {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: transparent;
  border: 1px solid transparent;
}

.editable-note:hover {
  background: linear-gradient(135deg, #ebf8ff 0%, #e6fffa 100%);
  border-color: #bee3f8;
}

.editable-note .notes-text {
  flex: 1;
  color: #2d3748;
}

.editable-note .no-info.clickable {
  color: #a0aec0;
  font-style: italic;
}

.editable-note:hover .no-info.clickable {
  color: #3182ce;
}

.edit-note-icon {
  font-size: 14px;
  color: #a0aec0;
  opacity: 0;
  transition: all 0.3s ease;
}

.editable-note:hover .edit-note-icon {
  opacity: 1;
  color: #3182ce;
}

/* Action buttons in table */
.action-buttons {
  display: flex;
  flex-wrap: nowrap;
  gap: 4px;
  align-items: center;
}

.action-buttons :deep(.el-button) {
  border-radius: 8px;
}

.action-buttons :deep(.el-button.is-circle) {
  padding: 6px;
}

/* 收藏按钮自定义样式 */
.action-buttons :deep(.el-button.is-favorited-btn) {
  background: linear-gradient(135deg, #ed8936 0%, #f6ad55 100%);
  border-color: #ed8936;
  color: white;
}

.action-buttons :deep(.el-button.is-favorited-btn:hover) {
  background: linear-gradient(135deg, #dd6b20 0%, #ed8936 100%);
  border-color: #dd6b20;
}

/* No info text */
.no-info {
  color: #cbd5e0;
}

/* Form dialog styles (Add/Edit Server) - 企业级对话框美化 */
.form-dialog :deep(.el-dialog) {
  margin-top: 8vh;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 25px 80px rgba(30, 58, 95, 0.25);
}

.form-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #2c5282 0%, #3182ce 50%, #4299e1 100%);
  color: white;
  padding: 24px 32px;
  margin: 0;
}

.form-dialog :deep(.el-dialog__title) {
  color: white;
  font-weight: 700;
  font-size: 20px;
  letter-spacing: 0.5px;
}

.form-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: white;
  font-size: 20px;
}

.form-dialog :deep(.el-dialog__headerbtn:hover .el-dialog__close) {
  color: rgba(255, 255, 255, 0.8);
}

.form-dialog :deep(.el-dialog__body) {
  padding: 32px;
  background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
}

/* Password dialog styles - 企业级对话框美化 */
.password-dialog :deep(.el-dialog) {
  margin-top: 8vh;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 25px 80px rgba(197, 48, 48, 0.25);
}

.password-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #c53030 0%, #e53e3e 50%, #fc8181 100%);
  color: white;
  padding: 24px 32px;
  margin: 0;
}

.password-dialog :deep(.el-dialog__title) {
  color: white;
  font-weight: 700;
  font-size: 20px;
  letter-spacing: 0.5px;
}

.password-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: white;
  font-size: 20px;
}

.password-dialog :deep(.el-dialog__headerbtn:hover .el-dialog__close) {
  color: rgba(255, 255, 255, 0.8);
}

.password-dialog :deep(.el-dialog__body) {
  padding: 32px;
  background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
}

/* Server detail dialog - 企业级对话框美化 */
.detail-dialog :deep(.el-dialog) {
  margin-top: 8vh;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 25px 80px rgba(39, 103, 73, 0.25);
}

.detail-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #276749 0%, #38a169 50%, #48bb78 100%);
  color: white;
  padding: 24px 32px;
  margin: 0;
}

.detail-dialog :deep(.el-dialog__title) {
  color: white;
  font-weight: 700;
  font-size: 20px;
  letter-spacing: 0.5px;
}

.detail-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: white;
  font-size: 20px;
}

.detail-dialog :deep(.el-dialog__headerbtn:hover .el-dialog__close) {
  color: rgba(255, 255, 255, 0.8);
}

.detail-dialog :deep(.el-dialog__body) {
  padding: 32px;
  background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
}

.server-detail {
  padding: 10px;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #ebeef5;
}

.detail-title {
  flex: 1;
}

.detail-title h3 {
  margin: 0 0 5px 0;
  font-size: 20px;
  color: #303133;
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
}

.detail-updated {
  margin: 0;
  color: #909399;
  font-size: 13px;
}

.detail-actions {
  margin-top: 20px;
  text-align: right;
}

/* Credentials display styles */
.credentials-display {
  display: flex;
  align-items: center;
  gap: 8px;
}

.credential-value {
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 14px;
  color: #303133;
  font-weight: 500;
}

.credential-separator {
  color: #909399;
  font-weight: 400;
}

.password-value {
  color: #e6a23c;
  background: #fdf6ec;
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid #faecd8;
}

.credential-loading {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #909399;
  font-size: 13px;
}

/* Segment dialog header */
.segment-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 24px;
  padding-bottom: 18px;
  border-bottom: 2px solid #e2e8f0;
}

.segment-count {
  color: #4a5568;
  font-size: 16px;
  font-weight: 600;
}

.segment-sort-options {
  display: flex;
  align-items: center;
  gap: 8px;
}

.segment-sort-options :deep(.el-radio-button__inner) {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  border-radius: 10px;
}

.segment-sort-options :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: linear-gradient(135deg, #2c5282 0%, #3182ce 100%);
  border-color: #3182ce;
  box-shadow: 0 4px 12px rgba(49, 130, 206, 0.3);
}

/* Clickable note styles in detail dialog */
.clickable-note {
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  border-radius: 10px;
  transition: all 0.3s ease;
  color: #4a5568;
  background: transparent;
  border: 1px solid transparent;
}

.clickable-note:hover {
  background: linear-gradient(135deg, #ebf8ff 0%, #e6fffa 100%);
  border-color: #bee3f8;
  color: #2c5282;
}

.clickable-note .edit-icon {
  font-size: 16px;
  opacity: 0.4;
  transition: all 0.3s ease;
}

.clickable-note:hover .edit-icon {
  opacity: 1;
  color: #3182ce;
}

/* Terminal dialog styles - 企业级对话框美化 */
.terminal-dialog :deep(.el-dialog) {
  margin-top: 8vh;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 25px 80px rgba(0, 0, 0, 0.35);
}

.terminal-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%);
  color: white;
  padding: 20px 28px;
  margin: 0;
}

.terminal-dialog :deep(.el-dialog__title) {
  color: #68d391;
  font-weight: 700;
  font-size: 18px;
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
}

.terminal-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: #a0aec0;
  font-size: 20px;
}

.terminal-dialog :deep(.el-dialog__headerbtn:hover .el-dialog__close) {
  color: #fc8181;
}

.terminal-dialog :deep(.el-dialog__body) {
  padding: 24px;
  background: #1a202c;
}

.terminal-dialog-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.terminal-header-info {
  margin-bottom: 8px;
}

/* RDP Dialog Styles */
.rdp-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #0078d4 0%, #106ebe 50%, #005a9e 100%);
  color: white;
  padding: 16px 24px;
  margin: 0;
}

.rdp-dialog :deep(.el-dialog__title) {
  color: white;
  font-weight: 600;
}

.rdp-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: rgba(255, 255, 255, 0.8);
}

.rdp-dialog :deep(.el-dialog__headerbtn:hover .el-dialog__close) {
  color: white;
}

/* RDP Panel Layout */
.rdp-panel {
  margin-top: 16px;
}

/* Status Card */
.rdp-status-card {
  background: linear-gradient(135deg, #f0f7ff 0%, #e8f4fd 100%);
  border: 1px solid #d0e8ff;
  border-radius: 10px;
  padding: 16px 20px;
  margin-bottom: 20px;
}

.rdp-status-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.rdp-status-icon-area {
  display: flex;
  align-items: center;
  gap: 10px;
}

.rdp-status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}

.rdp-status-dot.online {
  background: #67c23a;
  box-shadow: 0 0 8px rgba(103, 194, 58, 0.6);
}

.rdp-status-dot.checking {
  background: #e6a23c;
  animation: pulse 1.5s ease-in-out infinite;
}

.rdp-status-dot.offline {
  background: #f56c6c;
  box-shadow: 0 0 8px rgba(245, 108, 108, 0.4);
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.rdp-status-text {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

/* Quick Actions */
.rdp-quick-actions {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.rdp-main-btn {
  flex: 1;
  height: 48px;
  font-size: 14px;
  font-weight: 500;
  border-radius: 8px;
}

/* Command Box */
.rdp-command-box {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #1e1e1e;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.rdp-command {
  flex: 1;
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 14px;
  color: #67c23a;
}

/* Settings Panel */
.rdp-settings-panel {
  background: #fafbfc;
  border: 1px solid #ebeef5;
  border-radius: 10px;
  padding: 16px 20px;
  margin-bottom: 16px;
}

.rdp-settings-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 16px;
  padding-bottom: 10px;
  border-bottom: 1px solid #ebeef5;
}

.rdp-settings-form :deep(.el-form-item) {
  margin-bottom: 12px;
}

.rdp-settings-form :deep(.el-form-item__label) {
  font-size: 13px;
  color: #606266;
}

/* Tips */
.rdp-tips {
  background: #fff8e6;
  border: 1px solid #faecd8;
  border-radius: 8px;
  padding: 14px 18px;
  font-size: 13px;
  color: #606266;
  line-height: 1.8;
}

.rdp-tips p {
  margin: 0 0 6px 0;
}

.rdp-tips ul {
  margin: 0;
  padding-left: 20px;
}

.rdp-tips li {
  margin-bottom: 2px;
}

.mono-text {
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
}

/* Segment dialog styles - 企业级对话框美化 */
.segment-dialog :deep(.el-dialog) {
  margin-top: 8vh;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 25px 80px rgba(30, 58, 95, 0.25);
}

.segment-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #2c5282 0%, #3182ce 50%, #4299e1 100%);
  color: white;
  padding: 24px 32px;
  margin: 0;
}

.segment-dialog :deep(.el-dialog__title) {
  color: white;
  font-weight: 700;
  font-size: 20px;
  letter-spacing: 0.5px;
}

.segment-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: white;
  font-size: 20px;
}

.segment-dialog :deep(.el-dialog__headerbtn:hover .el-dialog__close) {
  color: rgba(255, 255, 255, 0.8);
}

.segment-dialog :deep(.el-dialog__body) {
  padding: 32px;
  background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
}

/* Filtered dialog styles - 淡蓝色企业级对话框美化 */
.filtered-dialog :deep(.el-dialog) {
  margin-top: 8vh;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 25px 80px rgba(66, 153, 225, 0.25);
}

.filtered-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #3182ce 0%, #63b3ed 50%, #90cdf4 100%);
  color: white;
  padding: 24px 32px;
  margin: 0;
}

.filtered-dialog :deep(.el-dialog__title) {
  color: white;
  font-weight: 700;
  font-size: 20px;
  letter-spacing: 0.5px;
}

.filtered-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: white;
  font-size: 20px;
}

.filtered-dialog :deep(.el-dialog__headerbtn:hover .el-dialog__close) {
  color: rgba(255, 255, 255, 0.8);
}

.filtered-dialog :deep(.el-dialog__body) {
  padding: 32px;
  background: linear-gradient(135deg, #ebf8ff 0%, #e6fffa 100%);
}

/* 一键查询IP段分组样式 */
.segment-header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.batch-segment-groups {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-height: 70vh;
  overflow-y: auto;
  padding-right: 4px;
}

.batch-segment-group {
  background: white;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition: box-shadow 0.2s ease;
}

.batch-segment-group:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.batch-segment-group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
  cursor: pointer;
  user-select: none;
  transition: background 0.2s ease;
}

.batch-segment-group-header:hover {
  background: linear-gradient(135deg, #edf2f7 0%, #e2e8f0 100%);
}

.batch-segment-group-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.batch-segment-arrow {
  font-size: 14px;
  color: #718096;
  transition: transform 0.3s ease;
  transform: rotate(-90deg);
}

.batch-segment-arrow.is-expanded {
  transform: rotate(0deg);
}

.batch-segment-name {
  font-size: 15px;
  font-weight: 600;
  color: #2d3748;
  font-family: 'SF Mono', 'Cascadia Code', 'Courier New', monospace;
  letter-spacing: 0.3px;
}

.batch-segment-group-body {
  border-top: 1px solid #e2e8f0;
}

.batch-segment-note {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #718096;
  font-weight: 400;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Animations */
@keyframes pulse {
  0% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
  100% {
    opacity: 1;
  }
}

:deep(.el-table__row.is-checking) {
  animation: pulse 1s infinite;
}

/* Table styling - 企业级表格美化 */
:deep(.el-table) {
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  border: 1px solid #e2e8f0;
}

:deep(.el-table th) {
  background: linear-gradient(135deg, #edf2f7 0%, #e2e8f0 100%) !important;
  font-weight: 700;
  color: #1e3a5f;
  border-bottom: 2px solid #cbd5e0;
}

:deep(.el-table th .cell) {
  font-size: 14px;
  letter-spacing: 0.5px;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background: #f7fafc;
}

:deep(.el-table__body tr:hover > td) {
  background: linear-gradient(135deg, #ebf8ff 0%, #e6fffa 100%) !important;
}

:deep(.el-table td) {
  border-bottom: 1px solid #e2e8f0;
  padding: 8px 0;
}

/* 收藏行高亮样式 - 高级美化 */
:deep(.el-table__body tr.favorited-row > td) {
  background: linear-gradient(135deg, #fff7ed 0%, #ffedd5 50%, #fed7aa 100%) !important;
  border-left: 4px solid #f97316;
  position: relative;
}

:deep(.el-table__body tr.favorited-row > td:first-child) {
  border-left: 4px solid #f97316;
  border-radius: 4px 0 0 4px;
}

:deep(.el-table__body tr.favorited-row > td:last-child) {
  border-radius: 0 4px 4px 0;
}

:deep(.el-table__body tr.favorited-row > td::before) {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, rgba(249, 115, 22, 0.08) 0%, transparent 30%);
  pointer-events: none;
}

:deep(.el-table__body tr.favorited-row:hover > td) {
  background: linear-gradient(135deg, #ffedd5 0%, #fed7aa 50%, #fdba74 100%) !important;
  box-shadow: inset 0 0 0 1px rgba(249, 115, 22, 0.2);
}

/* IP列收藏星标 */
.favorite-star-icon {
  color: #f97316;
  font-size: 16px;
  margin-right: 4px;
  vertical-align: middle;
  animation: starPulse 1.5s ease-in-out infinite;
}

@keyframes starPulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.2);
  }
}

/* 减少动效偏好 - 星标动画 */
@media (prefers-reduced-motion: reduce) {
  .favorite-star-icon {
    animation: none;
  }
}

/* Pagination container - 企业级分页美化 */
.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 28px;
  padding-top: 24px;
  border-top: 2px solid #e2e8f0;
}

.pagination-container :deep(.el-pagination.is-background .el-pager li) {
  border-radius: 10px;
  font-weight: 500;
}

.pagination-container :deep(.el-pagination.is-background .el-pager li:not(.is-disabled).is-active) {
  background: linear-gradient(135deg, #2c5282 0%, #3182ce 100%);
  box-shadow: 0 4px 12px rgba(49, 130, 206, 0.35);
}

.pagination-container :deep(.el-pagination.is-background .el-pager li:not(.is-disabled):hover) {
  color: #3182ce;
}

.pagination-container :deep(.el-pagination .btn-prev),
.pagination-container :deep(.el-pagination .btn-next) {
  border-radius: 10px;
}

/* Segments container */
.segments-container {
  display: flex;
  flex-direction: column;
}

/* File dialog styles - 淡蓝色主题 */
.file-dialog :deep(.el-dialog) {
  margin-top: 8vh;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 25px 80px rgba(66, 153, 225, 0.25);
}

.file-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #3182ce 0%, #63b3ed 50%, #90cdf4 100%);
  color: white;
  padding: 24px 32px;
  margin: 0;
}

.file-dialog :deep(.el-dialog__title) {
  color: white;
  font-weight: 700;
  font-size: 20px;
  letter-spacing: 0.5px;
}

.file-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: white;
  font-size: 20px;
}

.file-dialog :deep(.el-dialog__headerbtn:hover .el-dialog__close) {
  color: rgba(255, 255, 255, 0.8);
}

.file-dialog :deep(.el-dialog__body) {
  padding: 32px;
  background: linear-gradient(135deg, #ebf8ff 0%, #e6fffa 100%);
}

.file-content-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.file-content {
  background: #1a202c;
  color: #68d391;
  padding: 20px;
  border-radius: 12px;
  overflow-x: auto;
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.6;
  max-height: 400px;
  overflow-y: auto;
  margin: 0;
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.3);
}

/* File Browser Section Styles - 升级版 */
.file-browser-section {
  margin-top: 20px;
  background: #ffffff;
  border-radius: 16px;
  padding: 20px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.file-browser-header {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e2e8f0;
}

.file-browser-title-area {
  display: flex;
  align-items: center;
  gap: 12px;
}

.file-browser-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1e3a5f;
}

.file-browser-title-icon {
  color: #f0883e;
  font-size: 20px;
}

.file-browser-path {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f7fafc;
  padding: 8px 16px;
  border-radius: 8px;
  min-width: 200px;
}

.path-home-icon {
  color: #f0883e;
  font-size: 18px;
}

.file-browser-path :deep(.el-breadcrumb__separator) {
  color: #909399;
}

.breadcrumb-item-clickable {
  cursor: pointer;
  color: #409EFF;
  transition: all 0.2s;
  padding: 2px 6px;
  border-radius: 4px;
}

.breadcrumb-item-clickable:hover {
  color: #337ecc;
  background: rgba(64, 158, 255, 0.1);
  text-decoration: none;
}

.file-browser-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 60px 20px;
  color: #606266;
}

.loading-animation {
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
  border-radius: 50%;
  border: 2px solid #e2e8f0;
}

.file-browser-error {
  padding: 16px;
}

.file-browser-content {
  background: #ffffff;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #e2e8f0;
}

.file-browser-content :deep(.el-table) {
  background: transparent;
  --el-table-bg-color: #ffffff;
  --el-table-tr-bg-color: #ffffff;
  --el-table-header-bg-color: #f7fafc;
  --el-table-header-text-color: #1e3a5f;
  --el-table-text-color: #303133;
  --el-table-border-color: #e2e8f0;
  --el-table-row-hover-bg-color: rgba(64, 158, 255, 0.08);
}

.file-browser-content :deep(.el-table__body tr.directory-row) {
  background: rgba(240, 136, 62, 0.08);
}

.file-browser-content :deep(.el-table__body tr.hidden-file-row) {
  opacity: 0.7;
}

.file-browser-content :deep(.el-table__body tr:hover) {
  cursor: pointer;
}

.file-name-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.file-icon-wrapper {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  font-size: 18px;
  transition: transform 0.2s;
}

.file-icon-wrapper.folder {
  background: linear-gradient(135deg, #f0883e 0%, #d29922 100%);
  color: white;
}

.file-icon-wrapper.link {
  background: linear-gradient(135deg, #a371f7 0%, #8957e5 100%);
  color: white;
}

.file-icon-wrapper.code {
  background: linear-gradient(135deg, #3fb950 0%, #238636 100%);
}

.file-icon-wrapper.config {
  background: linear-gradient(135deg, #58a6ff 0%, #1f6feb 100%);
}

.file-icon-wrapper.default {
  background: linear-gradient(135deg, #6e7681 0%, #484f58 100%);
}

.file-ext-icon {
  font-size: 16px;
  line-height: 1;
}

.file-name-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.file-name {
  font-family: 'Cascadia Code', 'Fira Code', Monaco, Menlo, Consolas, monospace;
  font-size: 14px;
  color: #1e3a5f;
  font-weight: 500;
}

.hidden-badge {
  font-size: 10px;
  color: #909399;
  background: #f0f2f5;
  padding: 2px 6px;
  border-radius: 4px;
  width: fit-content;
}

.file-size {
  font-family: 'Cascadia Code', monospace;
  font-size: 13px;
  color: #606266;
}

.file-icon {
  font-size: 20px;
  color: #606266;
}

.folder-icon {
  color: #f0883e;
}

.link-icon {
  color: #a371f7;
}

.permission-code {
  font-family: 'Cascadia Code', Monaco, Menlo, Consolas, monospace;
  font-size: 12px;
  background: #f0f2f5;
  padding: 4px 8px;
  border-radius: 6px;
  color: #67c23a;
  letter-spacing: 0.5px;
  font-weight: 500;
}

.file-actions {
  display: flex;
  gap: 4px;
}

/* File Editor Dialog Styles - 升级版 */
.file-editor-dialog :deep(.el-dialog) {
  margin-top: 4vh;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 25px 80px rgba(0, 0, 0, 0.5);
  border: 1px solid #30363d;
}

.file-editor-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
  color: white;
  padding: 20px 28px;
  margin: 0;
  border-bottom: 1px solid #30363d;
}

.file-editor-dialog :deep(.el-dialog__title) {
  color: #f0f6fc;
  font-weight: 600;
  font-size: 18px;
}

.file-editor-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: #8b949e;
  font-size: 20px;
}

.file-editor-dialog :deep(.el-dialog__headerbtn:hover .el-dialog__close) {
  color: #f85149;
}

.file-editor-dialog :deep(.el-dialog__body) {
  padding: 0;
  background: #0d1117;
}

.file-editor-dialog :deep(.el-dialog__footer) {
  background: #161b22;
  border-top: 1px solid #30363d;
  padding: 16px 24px;
}

.file-editor-content {
  display: flex;
  flex-direction: column;
}

.file-editor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: #161b22;
  border-bottom: 1px solid #30363d;
}

.file-editor-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.file-path-display {
  display: flex;
  align-items: center;
  gap: 8px;
}

.path-icon {
  color: #58a6ff;
  font-size: 18px;
}

.file-path-code {
  font-family: 'Cascadia Code', Monaco, Menlo, Consolas, monospace;
  font-size: 13px;
  color: #79c0ff;
  background: #21262d;
  padding: 6px 12px;
  border-radius: 6px;
  border: 1px solid #30363d;
}

.file-editor-badges {
  display: flex;
  gap: 8px;
}

.file-editor-actions {
  display: flex;
  gap: 8px;
}

.file-editor-body {
  display: flex;
  min-height: 450px;
}

.line-numbers {
  display: flex;
  flex-direction: column;
  background: #161b22;
  padding: 16px 12px;
  border-right: 1px solid #30363d;
  user-select: none;
  min-width: 50px;
}

.line-number {
  font-family: 'Cascadia Code', Monaco, Menlo, Consolas, monospace;
  font-size: 13px;
  line-height: 1.6;
  color: #6e7681;
  text-align: right;
}

.file-editor-textarea {
  flex: 1;
}

.file-editor-textarea :deep(.el-textarea__inner) {
  font-family: 'Cascadia Code', 'Fira Code', Monaco, Menlo, Consolas, monospace;
  font-size: 14px;
  line-height: 1.6;
  background: #0d1117;
  color: #e6edf3;
  border-radius: 0;
  padding: 16px;
  min-height: 450px;
  border: none;
  resize: none;
}

.file-editor-textarea :deep(.el-textarea__inner:read-only) {
  background: #0d1117;
  color: #b1bac4;
}

.file-editor-textarea :deep(.el-textarea__inner:focus) {
  box-shadow: none;
}

.file-editor-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
