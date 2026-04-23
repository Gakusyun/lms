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
