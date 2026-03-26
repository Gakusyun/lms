#import "@preview/gakusyun-doc:1.0.0": *

// 设置模板参数
#show: docu.with(
  title: "Leave Management System",
  subtitle: "技术实现及部署文档",
  author: "X. J. Gao",
  show-title: true,
  title-page: false,
  blank-page: true,
  show-index: true,
  index-page: false,
  column-of-index: 2,
  depth-of-index: 3,
  cjk-font: "Source Han Serif",
  emph-cjk-font: "FandolKai",
  latin-font: "New Computer Modern",
  mono-font: "Maple Mono NF",
  default-size: "小四",
  lang: "zh",
  region: "cn",
  paper: "a4",
  margin: 1.2cm,
  date: datetime.today().display("[year]年[month]月[day]日"),
  numbering: "第1页 共1页",
  column: 1,
)

#show table: set align(center)
#show table: set text(size: zh("小五"))

= LMS
LMS请假管理系统是《基于微信小程序的高校学生请假管理系统的设计与实现》的代码实现。

本项目是一个基于 Web 前端 + FastAPI 后端的智能请假管理系统，包含学生、审核员、教师、管理员等多个角色。网页版前端使用 Vue 3 + TypeScript + Vite 实现，小程序端使用微信原生框架实现，后端使用 Python + FastAPI 实现 RESTful API 接口，数据库使用 SQLite 并通过 SQLModel ORM 进行操作。

== 用户角色与权限

=== 学生
+ 提交请假申请（事假/病假/公假/婚假/丧假）
+ 查看审批状态与历史记录
+ 可被担保（紧急情况）
+ 编辑未审批的请假条
+ 导出个人请假记录（Excel/CSV）

=== 审核员
+ 审批请假申请（批准/拒绝，可添加审核备注）
+ 批量处理请假条
+ 直接创建请假条
+ 留言要求补充材料
+ 导出数据（Excel/CSV）

=== 教师
+ 查看课程请假情况
+ 统计缺勤率
+ 导出 CSV / Excel / JSON
+ 生成图表

=== 管理员
+ 用户管理（增删改查）
+ 权限设置
+ 日志查看
+ 数据备份与恢复
+ 批量导入用户
+ 批量创建请假条

== 鉴权机制

系统采用 *JWT（JSON Web Token）* 无状态认证机制，替代了原有的数据库 Token 验证方式：

+ *登录流程*：
  1. 用户提交 ID 和密码
  2. 后端使用 *passlib* (bcrypt) 验证密码
  3. 验证成功后生成 JWT Token（包含用户 ID、角色、姓名、过期时间）
  4. Token 有效期为 30 分钟
  5. 前端将 Token 存储在 localStorage 中

+ *请求认证*：
  1. 前端在请求头中添加 "Authorization: Bearer {token}"
  2. 同时在查询参数中携带 token 参数
  3. 后端使用 python-jose 验证 Token
  4. Token 过期或无效时返回 401 错误

+ *扫码鉴权*（二维码验证）：
  1. 审核通过后，服务器用私钥加密生成二维码
  2. 鉴权端扫码获取密文与明文
  3. 使用公钥解密并与明文比对
  4. 若一致，则从后端获取完整请假信息并判断是否在合法时间内

== 审核权限等级

- *1天以内*：辅导员批准
- *2～3天*：院党总支副书记批准
- *4～7天*：院党总支书记批准
- *7天以上*：学生工作处批准

== 数据库设计

数据库采用 *SQLite*，使用 *SQLModel* ORM 进行操作，所有表均符合第三范式（3NF）。

=== student - 学生表
#table(
  columns: 4,
  stroke: none,
  table.hline(),
  table.header([列名], [类型], [是否为空], [说明]),
  table.hline(stroke: 0.5pt),
  [student_id], [INT], [NO], [主键，学号],
  [student_name], [VARCHAR(8)], [NO], [学生姓名],
  [password], [VARCHAR(60)], [YES], [bcrypt 加密密码],
  [school_id], [INT], [YES], [外键，关联院系表],
  [reviewer_id], [INT], [YES], [外键，关联审核员表],
  [guarantee_permission], [DATETIME], [YES], [担保权限截止时间],
  table.hline(),
)

=== reviewer - 审核员表
#table(
  columns: 4,
  stroke: none,
  table.hline(),
  table.header([列名], [类型], [是否为空], [说明]),
  table.hline(stroke: 0.5pt),
  [reviewer_id], [INT], [NO], [主键，工号],
  [reviewer_name], [VARCHAR(8)], [NO], [审核员姓名],
  [school_id], [INT], [YES], [外键，关联院系表],
  [role_id], [INT], [YES], [外键，关联角色表],
  [password], [VARCHAR(60)], [YES], [bcrypt 加密密码],
  table.hline(),
)

=== teacher - 教师表
#table(
  columns: 4,
  stroke: none,
  table.hline(),
  table.header([列名], [类型], [是否为空], [说明]),
  table.hline(stroke: 0.5pt),
  [teacher_id], [INT], [NO], [主键，工号],
  [teacher_name], [VARCHAR(8)], [NO], [教师姓名],
  [password], [VARCHAR(60)], [YES], [bcrypt 加密密码],
  table.hline(),
)

=== course - 课程表
#table(
  columns: 4,
  stroke: none,
  table.hline(),
  table.header([列名], [类型], [是否为空], [说明]),
  table.hline(stroke: 0.5pt),
  [course_id], [INT], [NO], [主键，课程ID],
  [course_name], [VARCHAR(12)], [NO], [课程名称],
  [teacher_id], [INT], [NO], [外键，关联教师表],
  [class_hours], [VARCHAR(8)], [YES], [课时数],
  table.hline(),
)

=== leave - 请假记录表
#table(
  columns: 4,
  stroke: none,
  table.hline(),
  table.header([列名], [类型], [是否为空], [说明]),
  table.hline(stroke: 0.5pt),
  [leave_id], [INT], [NO], [主键，请假编号],
  [student_id], [INT], [NO], [外键，关联学生表],
  [leave_date], [DATETIME], [NO], [请假日期时间],
  [leave_hours], [VARCHAR(8)], [YES], [请假时长（课时数）],
  [status], [VARCHAR(8)], [NO], [状态：待审批/已批准/已拒绝/已撤销],
  [leave_type], [VARCHAR(8)], [YES], [请假类型：事假/病假/公假/婚假/丧假],
  [remarks], [VARCHAR(100)], [YES], [请假备注/原因],
  [materials], [VARCHAR(100)], [YES], [证明材料链接],
  [reviewer_id], [INT], [YES], [外键，关联审核员表],
  [teacher_id], [INT], [YES], [外键，关联教师表],
  [audit_remarks], [VARCHAR(100)], [YES], [审核备注],
  [audit_time], [DATETIME], [YES], [审核时间],
  [course_id], [INT], [YES], [外键，关联课程表],
  [is_modified], [BOOLEAN], [NO], [是否被修改过，默认 false],
  [guarantee_student_id], [INT], [YES], [外键，关联担保学生表],
  table.hline(),
)

=== school - 院系表
#table(
  columns: 4,
  stroke: none,
  table.hline(),
  table.header([列名], [类型], [是否为空], [说明]),
  table.hline(stroke: 0.5pt),
  [school_id], [INT], [NO], [主键，院系ID],
  [school_name], [VARCHAR(20)], [NO], [院系名称（唯一）],
  table.hline(),
)

=== role - 角色表
#table(
  columns: 4,
  stroke: none,
  table.hline(),
  table.header([列名], [类型], [是否为空], [说明]),
  table.hline(stroke: 0.5pt),
  [role_id], [INT], [NO], [主键，角色ID],
  [role_name], [VARCHAR(20)], [NO], [角色名称（唯一）：系主任/辅导员等],
  table.hline(),
)

=== admin - 管理员表
#table(
  columns: 4,
  stroke: none,
  table.hline(),
  table.header([列名], [类型], [是否为空], [说明]),
  table.hline(stroke: 0.5pt),
  [admin_id], [INT], [NO], [主键，管理员ID],
  [name], [VARCHAR(8)], [NO], [管理员姓名],
  [password], [VARCHAR(60)], [YES], [bcrypt 加密密码],
  table.hline(),
)

=== student_course - 学生选课表
#table(
  columns: 4,
  stroke: none,
  table.hline(),
  table.header([列名], [类型], [是否为空], [说明]),
  table.hline(stroke: 0.5pt),
  [id], [INT], [NO], [主键，自增ID],
  [student_id], [INT], [NO], [外键，关联学生表],
  [course_id], [INT], [NO], [外键，关联课程表],
  [enrollment_date], [DATE], [YES], [选课日期],
  [status], [VARCHAR(20)], [YES], [选课状态],
  table.hline(),
)

= Backend

后端采用 *Python* + *FastAPI* 框架实现 RESTful API。

== 技术栈

+ *Web 框架*：FastAPI 0.123+
+ *ORM*：SQLModel 0.0.27+
+ *数据库*：SQLite（可配置 MySQL）
+ *认证*：JWT (python-jose[cryptography])
+ *密码加密*：passlib[bcrypt]
+ *ASGI 服务器*：Uvicorn 0.38+
+ *包管理器*：uv
+ *测试框架*：pytest 9.0+ + pytest-cov

== 核心功能

=== 用户权限管理
+ 登录鉴权（JWT，30分钟有效期）
+ 角色权限验证（学生/审核员/教师/管理员）
+ 密码修改（自己修改/管理员修改指定用户）
+ 登出（无状态，前端删除 Token）

=== 数据接口
+ RESTful API 设计，统一前缀 `/api/v1/`
+ ORM 操作数据库（防止 SQL 注入）
+ 分页查询支持（page, page_size 参数）
+ CORS 跨域支持（可配置允许的源）

=== 系统设置
+ 结构化日志记录（logs/app.log）
+ 数据备份与恢复（JSON 格式）
+ 用户批量导入（CSV/XLSX）
+ 健康检查端点（`/health`）
+ 统计分析接口

== API 结构

=== 认证相关 (`/api/v1/auth`)
+ `POST /login` - 用户登录，返回 JWT Token
+ `GET /login/check` - 检查登录状态
+ `GET /logout` - 登出
+ `POST /register` - 用户注册
+ `POST /change-password` - 修改密码

=== 学生管理 (`/api/v1/students`)
+ `GET /students` - 获取学生列表（分页）
+ `GET /students/count` - 获取学生总数
+ `GET /students/{id}` - 获取学生详情
+ `POST /students` - 创建学生
+ `PUT /students/{id}` - 更新学生信息
+ `DELETE /students/{id}` - 删除学生

=== 审核员管理 (`/api/v1/reviewers`)
+ `GET /reviewers` - 获取审核员列表（分页）
+ `POST /reviewers` - 创建审核员
+ `PUT /reviewers/{id}` - 更新审核员信息
+ `DELETE /reviewers/{id}` - 删除审核员

=== 教师管理 (`/api/v1/teachers`)
+ `GET /teachers` - 获取教师列表（分页）
+ `GET /teachers/count` - 获取教师总数
+ `GET /teachers/{id}` - 获取教师详情
+ `POST /teachers` - 创建教师
+ `PUT /teachers/{id}` - 更新教师信息
+ `DELETE /teachers/{id}` - 删除教师

=== 课程管理 (`/api/v1/courses`)
+ `GET /courses` - 获取课程列表（分页）
+ `POST /courses` - 创建课程
+ `PUT /courses/{id}` - 更新课程信息
+ `DELETE /courses/{id}` - 删除课程

=== 请假管理 (`/api/v1/leaves`)
+ `GET /leaves` - 获取请假列表（分页，需认证）
+ `POST /leaves` - 创建请假条（需认证）
+ `POST /leaves/edit/{id}` - 编辑/审核请假条（需认证）
+ `GET /leaves/student/{id}` - 获取学生请假记录

=== 学生选课 (`/api/v1/student-courses`)
+ `POST /student-courses` - 学生选课
+ `DELETE /student-courses/student/{sid}/course/{cid}` - 学生退课
+ `GET /student-courses/student/{id}` - 获取学生选课列表
+ `GET /student-courses/course/{id}` - 获取课程学生列表
+ `GET /student-courses/course/{id}/count` - 获取课程选课人数

=== 统计分析 (`/api/v1/statistics`)
+ `GET /statistics/leaves` - 获取请假统计
+ `GET /statistics/leaves/trend` - 获取请假趋势
+ `GET /statistics/courses/enrollment` - 获取课程选课统计
+ `GET /statistics/users` - 获取用户统计
+ `GET /statistics/reviewers/performance` - 获取审核员绩效

=== 数据备份 (`/api/v1/backup`)
+ `POST /backup/export` - 导出数据（JSON）
+ `POST /backup/import` - 导入数据

== 项目结构

#figure(
  ```text
  Backend/
  ├── app/
  │   ├── api/v1/              # API 路由模块
  │   │   ├── auth.py          # 认证相关接口
  │   │   ├── students.py      # 学生管理接口
  │   │   ├── teachers.py      # 教师管理接口
  │   │   ├── reviewers.py     # 审核员管理接口
  │   │   ├── courses.py       # 课程管理接口
  │   │   ├── leaves.py        # 请假管理接口
  │   │   ├── student_courses.py  # 选课管理接口
  │   │   ├── statistics.py    # 统计分析接口
  │   │   └── backup.py        # 数据备份接口
  │   ├── models/              # SQLModel 数据模型
  │   ├── services/            # 业务逻辑层
  │   ├── utils/               # 工具函数（JWT、日志等）
  │   ├── config/              # 配置管理
  │   └── database/            # 数据库连接
  ├── tests/                   # pytest 测试文件
  ├── config.toml              # 配置文件
  ├── main.py                  # 应用入口
  └── pyproject.toml           # 项目依赖
  ```,
  caption: "后端项目结构",
)<backendStructure>

== 部署

=== 环境要求
+ Python 3.14+
+ uv（包管理器）

=== 部署步骤

#figure(
  ```bash
  # 1. 克隆项目
  git clone <repository-url>
  cd Backend

  # 2. 安装依赖
  uv sync

  # 3. 配置文件
  cp config_sample.toml config.toml
  # 编辑 config.toml，设置数据库路径和 CORS 配置

  # 4. 初始化管理员（首次运行）
  python init_data.py

  # 5. 启动服务
  uv run python main.py --port 8000

  # 6. 生产环境部署（使用 gunicorn + uvicorn）
  uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
  ```,
  caption: "后端部署步骤",
)<deploySteps>

=== 配置说明 (`config.toml`)

#figure(
  ```toml
  [database]
  path = "./test.db"      # SQLite 数据库路径
  type = "sqlite"         # 数据库类型
  host = "localhost"      # 主机（MySQL 使用）
  port = 3306             # 端口（MySQL 使用）

  [cors]
  origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://gxj62.cn",
    "https://gxj62.cn",
    "http://*.gxj62.cn",
    "https://*.gxj62.cn",
  ]
  ```,
  caption: "配置文件示例",
)<configExample>

=== 测试

#figure(
  ```bash
  # 运行所有测试
  uv run pytest

  # 运行单个测试文件
  uv run pytest tests/test_auth.py

  # 生成覆盖率报告
  uv run pytest --cov

  # 详细输出
  uv run pytest -v
  ```,
  caption: "测试命令",
)<testCommands>

= Frontend

Web 前端采用 *Vue 3* + *TypeScript* + *Vite* 实现。

== 技术栈

+ *框架*：Vue 3.5+ (Composition API)
+ *语言*：TypeScript 5.9+
+ *构建工具*：Vite 8.0+
+ *路由*：Vue Router 5.0+
+ *HTTP 客户端*：Axios 1.13+
+ *其他*：xlsx（Excel 导出）、qrcode（二维码生成）

== 核心功能

=== 首页 (`/`)
+ 统计卡片展示（学生/教师/课程/请假统计）
+ 快捷操作入口
+ 最近请假条（按状态颜色区分）
+ 审核员可进入待审核列表
+ 长时间未处理的请假条置顶

=== 列表页面
+ 通用列表组件 (`GenericList.vue`)
+ 分页查询
+ 搜索过滤
+ 批量操作
+ 导出功能（Excel/CSV）

=== 用户管理
+ 学生管理 (`/students`)
+ 教师管理 (`/teachers`)
+ 审核员管理 (`/reviewers`)
+ 课程管理 (`/courses`)
+ 请假条管理 (`/leaves`)

=== 个人中心 (`/profile`)
+ 显示个人信息
+ 修改密码
+ 历史请假条（学生）
+ 所带课程请假统计（教师）
+ 所带学生请假汇总（辅导员）

=== 登录/初始化
+ 登录页 (`/login`)
+ 管理员初始化页 (`/admin/setup`)

== 项目结构

#figure(
  ```text
  Frontend/
  ├── src/
  │   ├── api/                # API 调用封装
  │   │   └── index.ts        # 统一 API 接口
  │   ├── components/         # 可复用组件
  │   │   ├── GenericList.vue          # 通用列表
  │   │   ├── GenericCreateModal.vue   # 通用创建弹窗
  │   │   ├── UserManagementModal.vue  # 用户管理弹窗
  │   │   ├── ChangePasswordModal.vue  # 修改密码弹窗
  │   │   └── PaginationControls.vue   # 分页控件
  │   ├── composables/        # 组合式函数
  │   │   ├── useApiData.ts           # API 数据获取
  │   │   └── usePagedData.ts         # 分页数据获取
  │   ├── router/             # 路由配置
  │   │   └── index.ts        # 路由守卫
  │   ├── utils/              # 工具函数
  │   │   ├── http.ts         # Axios 配置
  │   │   ├── auth.ts         # 认证工具
  │   │   └── excelExporter.ts # Excel 导出
  │   ├── views/              # 页面组件
  │   │   ├── LoginView.vue
  │   │   ├── HomePage.vue
  │   │   ├── StudentsList.vue
  │   │   ├── TeachersList.vue
  │   │   ├── ReviewersList.vue
  │   │   ├── CoursesList.vue
  │   │   ├── LeavesList.vue
  │   │   └── ProfileView.vue
  │   ├── types/              # TypeScript 类型定义
  │   └── styles/             # 全局样式
  ├── .env                    # 环境变量
  ├── vite.config.ts          # Vite 配置
  └── package.json            # 项目依赖
  ```,
  caption: "前端项目结构",
)<frontendStructure>

== 认证流程

=== 登录流程
1. 用户在登录页输入 ID 和密码
2. 调用 `/api/v1/login` 接口
3. 后端验证成功返回 JWT Token
4. 前端将 Token 存储在 `localStorage`
5. Axios 拦截器自动在请求头添加 Token
6. 路由守卫检查认证状态，未登录重定向到 `/login`

=== Token 处理
+ 请求拦截器：自动在请求头添加 `Authorization: Bearer {token}`
+ 响应拦截器：捕获 401 错误，清除 Token 并跳转登录页
+ Token 存储：`localStorage`（token, role, id, name）

== 部署

=== 环境要求
+ Node.js 20.19+ 或 22.12+

=== 部署步骤

#figure(
  ```bash
  # 1. 安装依赖
  npm install

  # 2. 配置环境变量
  cp .env.sample .env
  # 编辑 .env，设置 VITE_API_BASE_URL

  # 3. 开发环境运行
  npm run dev

  # 4. 生产环境构建
  npm run build

  # 5. 部署到 Web 服务器
  # 将 dist/ 目录下的文件部署到 Nginx/Caddy 等
  ```,
  caption: "前端部署步骤",
)<frontendDeploySteps>

=== 环境变量 (`.env`)

#figure(
  ```env
  # 开发环境
  VITE_API_BASE_URL=http://localhost:8000/api/v1

  # 生产环境
  # VITE_API_BASE_URL=https://your-domain.com/api/v1
  ```,
  caption: "环境变量配置",
)<envConfig>

=== Nginx 配置示例

#figure(
  ```nginx
  server {
      listen 80;
      server_name your-domain.com;
      root /path/to/dist;
      index index.html;

      location / {
          try_files $uri $uri/ /index.html;
      }

      location /api/ {
          proxy_pass http://localhost:8000;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
      }
  }
  ```,
  caption: "Nginx 配置示例",
)<nginxConfig>

= Mini Program

微信小程序端使用原生框架开发。

== 核心功能

=== 首页
+ 创建请假条
+ 显示请假条列表（按状态分类）
+ 快捷操作（编辑/查看详情）

=== 请假详情
+ 查看完整请假信息
+ 编辑未审批的请假条
+ 上传/查看证明材料
+ 查看审核进度和备注

=== 我的
+ 个人信息展示
+ 历史请假记录
+ 导出功能
+ 设置

=== 鉴权页
+ 扫码验证请假有效性
+ 显示请假详情
+ 验证结果显示

=== 扫码登录
+ 扫描网页端/PC 端二维码
+ 使用小程序已登录账号快速登录
+ 实现方式：
  1. 网页端生成二维码，包含临时 token
  2. 小程序扫码获取 token
  3. 小程序用已登录账号将 token 和用户信息提交到服务器
  4. 服务器验证后建立绑定关系
  5. 网页端轮询获取登录状态

== 部署

#figure(
  ```bash
  # 1. 使用微信开发者工具打开 Minipro-cli/ 目录

  # 2. 配置 project.config.json
  # - 修改 appid
  # - 设置 projectname

  # 3. 构建上传
  # 在微信开发者工具中点击"上传"按钮

  # 4. 提交审核
  # 在微信小程序管理后台提交审核
  ```,
  caption: "小程序部署步骤",
)<miniproDeploySteps>

= 系统架构图

== 整体架构

#figure(
  ```text
  ┌─────────────────────────────────────────────────────────┐
  │                        用户层                            │
  ├──────────────┬──────────────┬───────────────────────────┤
  │  Web 前端     │  小程序端     │       管理后台            │
  │  (Vue 3)     │  (原生框架)   │       (Vue 3)            │
  └──────┬───────┴──────┬───────┴───────────┬───────────────┘
         │              │                   │
         │ HTTP/HTTPS   │ HTTPS/WSS         │ HTTP/HTTPS
         │              │                   │
  ┌──────▼──────────────▼───────────────────▼───────────────┐
  │                     API 网关                              │
  │                  (FastAPI + JWT)                         │
  └──────┬───────────────────────────────────────────────────┘
         │
  ┌──────▼───────────────────────────────────────────────────┐
  │                     业务逻辑层                            │
  ├──────────┬──────────┬──────────┬──────────┬──────────────┤
  │ 认证服务  │ 请假服务  │ 用户服务  │ 课程服务  │  统计服务    │
  └──────┬───┴──────┬───┴──────┬───┴──────┬───┴──────┬───────┘
         │          │          │          │          │
  ┌──────▼──────────▼──────────▼──────────▼──────────▼───────┐
  │                     数据访问层                            │
  │                   (SQLModel ORM)                         │
  └──────┬────────────────────────────────────────────────────┘
         │
  ┌──────▼────────────────────────────────────────────────────┐
  │                    SQLite 数据库                          │
  └───────────────────────────────────────────────────────────┘
  ```,
  caption: "系统整体架构",
)<systemArchitecture>

== 认证流程

#figure(
  ```text
  ┌──────────┐                  ┌──────────┐                  ┌──────────┐
  │   客户端   │                  │   后端    │                  │  数据库   │
  └─────┬────┘                  └─────┬────┘                  └─────┬────┘
        │                             │                             │
        │ 1. POST /login              │                             │
        │    {id, password}           │                             │
        ├────────────────────────────>│                             │
        │                             │ 2. 查询用户信息              │
        │                             ├────────────────────────────>│
        │                             │                             │
        │                             │ 3. 返回用户数据              │
        │                             │<────────────────────────────┤
        │                             │                             │
        │                             │ 4. bcrypt 验证密码           │
        │                             │                             │
        │                             │ 5. 生成 JWT Token            │
        │ 6. 返回 Token               │    (包含: sub, role, name)  │
        │    {token, role, id, name}  │                             │
        │<────────────────────────────┤                             │
        │                             │                             │
        │ 7. 存储 Token 到 localStorage                              │
        │                             │                             │
        │ 8. 后续请求携带 Token        │                             │
        │    Authorization: Bearer...  │                             │
        │                             │                             │
        │ 9. 验证 Token                │                             │
        ├────────────────────────────>│                             │
        │                             │                             │
        │ 10. 返回数据/401             │                             │
        │<────────────────────────────┤                             │
  ```,
  caption: "JWT 认证流程",
)<authFlow>

= API 文档

详细的 API 文档请参考项目根目录下的 `API_USAGE.md` 文件，或访问后端服务的 `/docs` 端点查看自动生成的 Swagger/OpenAPI 文档。

= 常见问题

=== Q: 如何重置管理员密码？
A: 在 Backend 目录下运行 `python reset_admin_password.py`，按提示输入新密码。

=== Q: 如何查看日志？
A: 日志文件位于 `Backend/logs/app.log`，包含所有请求和错误信息。

=== Q: 如何备份数据？
A: 调用 `POST /api/v1/backup/export` 接口，数据将以 JSON 格式导出。

=== Q: Token 过期后如何处理？
A: 前端会自动捕获 401 错误，清除本地 Token 并跳转到登录页。用户需要重新登录。

= 开发规范

=== 代码风格
+ Python：遵循 PEP 8 规范
+ TypeScript：使用 ESLint + Prettier
+ Vue 3：使用 Composition API

=== Git 提交规范
+ `feat:` 新功能
+ `fix:` 修复 bug
+ `docs:` 文档更新
+ `refactor:` 代码重构
+ `test:` 测试相关
+ `chore:` 构建/工具链更新

=== 测试要求
+ 新增功能需编写单元测试
+ 测试覆盖率不低于 70%
+ 所有测试通过后方可合并

= 许可证

本项目采用 MIT 许可证。
