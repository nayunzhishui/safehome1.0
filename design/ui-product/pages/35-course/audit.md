# 课程页功能审查

- 页面任务：读取真实课程目录，按真实分类筛选，并进入真实课程详情。
- 数据与接口：保留 `api.listCourses()`、服务端课程字段、边界说明与错误信息。
- 交互：保留 `selectCategory`、`retryLoadCourses`、`openCourse` 及课程 ID 跳转。
- 状态：保留 loading、error、正常列表和空筛选结果的真实状态。
- 禁止：不新增课程、进度、分类或推荐；不修改 JS、API、后端和业务语义。
