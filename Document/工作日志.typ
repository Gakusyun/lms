#import "@preview/gakusyun-doc:1.0.0": *

// 设置模板参数
#show: docu.with(
  title: "Leave Management System",
  subtitle: "工作日志",
  author: "X. J. Gao",
  show-title: true,
  title-page: false,
  blank-page: true,
  show-index: true,
  index-page: false,
  column-of-index: 1,
  depth-of-index: 3,
  cjk-font: "Source Han Serif",
  emph-cjk-font: "FandolKai",
  latin-font: "New Computer Modern",
  mono-font: "Maple Mono NF",
  default-size: "小四",
  lang: "zh",
  region: "cn",
  paper: "a4",
  margin: 1.5cm,
  date: datetime.today().display("[year]年[month]月[day]日"),
  numbering: "第1页 共1页",
  column: 2,
)

= 2025年12月4日
== 目前已完成
+ 后端
  - 数据库的创建
  - 数据库查询包括表行数、查询表、通过id查询行的GET方法
  - 创建学生、审核员、教师、课程表、请假表的POST方法
  - 通过用户（学生、审核员、教师、课程）id查询请假的记录的方法
  - 最基本的登录、验证
+ 网页前端
  - 首页显示所有的数据
  - 点击进入分页列表显示
+ 小程序端
  - 前端所有功能
  - 扫码的按钮（无任何处理逻辑）

== TODO
+ 后端

+ 网页前端
  - 创建请假条的实现
  - 登录，分角色显示内容
+ 小程序端
  - 扫码功能的完善，可以通过扫码登录网页前端

== 已知问题
担保权限不是在期限内有权限，而是这个时间以后的才有权限。

如果违规，惩罚就是把担保权限时间移到today+7、30、90、180天不等

= 未来设想
- 扫码考勤

= 2025年12月5日
== 目前已完成
+ 后端
  - 登录及验证
+ 前端
  - 登录及验证
+ 小程序端
  - 小程序端扫码登录前端

= 2025年12月8日
== 目前已完成
+ 后端
  - 鉴权，区分角色信息不同
+ 前端
  - 统一的样式
+ 小程序端
  - 无

== TODO
审核员的审核，用户对请假条的修改

及已完成的请假条应禁止修改

需要创建时可以上传文件

= 2025年12月9日
== 目前已完成
+ 后端
  - 修改密码，审核员的审核，用户对请假条的修改API
+ 前端
  - 修改密码，审核员的审核，用户对请假条的修改，导出为xlsx
+ 小程序端
  - 无

= 2026年3月19日
== 目前已完成
+ 后端
  - *JWT 认证重构*：从数据库 Token 验证改为无状态 JWT 认证
  - 使用 *python-jose[cryptography]* 实现 JWT 签名与验证
  - 使用 *passlib[bcrypt]* 替代原有 MD5 密码哈希
  - 配置 CORS 中间件，支持跨域请求
  - 添加全局异常处理器
  - 实现 FastAPI *lifespan* 事件，自动创建数据库表
  - 完善日志系统（结构化日志记录）
  - 添加数据库连接池配置优化

+ 前端
  - 更新 Axios 拦截器，自动添加 JWT Token 到请求头
  - 实现 401 错误自动处理，清除 Token 并跳转登录页
  - 完善路由守卫，检查登录状态
  - 添加管理员初始化页面（首次部署时创建管理员）
  - 优化通用列表组件（GenericList.vue）
  - 优化通用创建弹窗组件（GenericCreateModal.vue）
  - 完善用户管理弹窗组件（UserManagementModal.vue）

+ 测试
  - 添加完整的单元测试（test_auth.py, test_students.py, test_teachers.py, test_reviewers.py, test_leaves.py）
  - 添加集成测试（test_integration.py）
  - 配置 pytest-cov 生成覆盖率报告

+ 文档
  - 创建 API_USAGE.md：详细的 API 使用说明
  - 创建 API_CHANGES.md：记录 API 变更历史
  - 创建 CLAUDE.md：项目开发指南

== 技术债务
+ 数据库设计：
  - 原有文档中的数据库字段类型与实际代码不一致（char(12) vs INT）
  - 密码加密方式从 MD5 升级到 bcrypt（已完成）
  - 部分表结构需要进一步规范化

+ 功能完善：
  - 文件上传功能（材料附件）尚未实现
  - 批量导入用户功能需要完善
  - 统计图表展示功能需要实现

= 2026年3月23日
== 目前已完成
+ 文档完善
  - 更新技术实现文档（main.typ）
  - 同步数据库设计文档与实际代码模型
  - 补充系统架构图和认证流程图
  - 添加详细的部署步骤和配置说明
  - 添加 API 结构说明
  - 添加常见问题解答
  - 添加开发规范和测试要求

== 当前系统状态
+ *认证系统*：✅ JWT 无状态认证（30分钟 Token 有效期）
+ *密码加密*：✅ bcrypt（passlib）
+ *ORM*：✅ SQLModel（符合第三范式）
+ *API 设计*：✅ RESTful API（统一 /api/v1/ 前缀）
+ *前端框架*：✅ Vue 3 + TypeScript + Vite
+ *路由守卫*：✅ 自动认证检查
+ *日志系统*：✅ 结构化日志（logs/app.log）
+ *测试覆盖*：✅ pytest 单元测试 + 集成测试

== 待实现功能
+ *文件上传*：请假材料附件上传与存储
+ *批量导入*：用户批量导入（Excel/CSV）
+ *数据统计*：可视化统计图表
+ *消息通知*：审核结果通知（小程序/邮件）
+ *数据备份*：定期自动备份
+ *权限细化*：基于角色的细粒度权限控制

== 已知问题
无

= 开发计划

+ 实现文件上传功能（请假材料）
+ 完善批量导入用户功能
+ 添加数据统计可视化
+ 实现消息通知系统
+ 添加数据自动备份功能
+ 完善权限控制系统
+ 添加数据分析和报表功能
+ 实现扫码考勤功能

= 技术栈总结

=== 后端技术栈
- *Python* 3.14+
- *FastAPI* 0.123+（Web 框架）
- *SQLModel* 0.0.27+（ORM）
- *SQLite*（数据库）
- *python-jose*（JWT 处理）
- *passlib[bcrypt]*（密码加密）
- *Uvicorn* 0.38+（ASGI 服务器）
- *pytest* 9.0+（测试框架）
- *uv*（包管理器）

=== 前端技术栈
- *Vue 3* 3.5+（前端框架）
- *TypeScript* 5.9+（类型系统）
- *Vite* 8.0+（构建工具）
- *Vue Router* 5.0+（路由）
- *Axios* 1.13+（HTTP 客户端）
- *xlsx*（Excel 导出）

=== 小程序技术栈
- *微信原生框架*

=== 开发工具
- *Git*（版本控制）
- *VS Code*（IDE）
- *微信开发者工具*（小程序开发）
- *Typst*（文档编写）

= 部署环境

=== 开发环境
- 后端：`http://localhost:8000`
- 前端：`http://localhost:5173`
- 数据库：SQLite（test.db）

=== 生产环境
- 后端：`https://lms.gxj62.cn`（FastAPI + Uvicorn）
- 前端：`https://gxj62.cn`（Nginx 静态托管）
- 数据库：SQLite（生产环境）

= 参考资料

=== 官方文档
- FastAPI：https://fastapi.tiangolo.com/
- SQLModel：https://sqlmodel.tiangolo.com/
- Vue 3：https://vuejs.org/
- Typst：https://typst.app/docs/

=== 项目文档
- API 使用说明：`Backend/API_USAGE.md`
- API 变更历史：`API_CHANGES.md`
- 开发指南：`CLAUDE.md`
- 技术文档：`Document/main.typ`
