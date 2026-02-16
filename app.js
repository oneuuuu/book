const grid = document.getElementById("grid")
const sqlQueryInput = document.getElementById("sqlQuery")
const queryError = document.getElementById("queryError")
const sortModeSelect = document.getElementById("sortMode")
const runQueryButton = document.getElementById("runQuery")
const resultCount = document.getElementById("resultCount")
const loadMoreButton = document.getElementById("loadMore")
const pagination = document.getElementById("pagination")

const state = {
  items: [],
  filtered: [],
  visibleCount: 0,
  pageSize: 30,
  hasQueried: false,
}

const formatCount = (count) => {
  if (count >= 10000) {
    return `${(count / 10000).toFixed(1)}万`
  }
  return `${count}`
}

const fieldAliases = {
  "评分": "r",
  "人数": "c",
  "标题": "t",
}

const parseSqlQuery = (input) => {
  if (!input) {
    return { conditions: [], error: "" }
  }
  const tokens = input.trim().split(/\s+/).filter(Boolean)
  const conditions = []
  for (const token of tokens) {
    const match = token.match(/^([^:]+):(>=|<=|=|>|<)?(.+)$/)
    if (!match) {
      return { conditions: [], error: `无法解析条件: ${token}` }
    }
    const fieldKey = match[1].toLowerCase()
    const field = fieldAliases[fieldKey]
    if (!field) {
      return { conditions: [], error: `不支持的字段: ${match[1]}` }
    }
    const operator = match[2] || "="
    const value = match[3]
    conditions.push({
      field,
      operator,
      value: field === "t" ? value : Number(value),
    })
  }
  return { conditions, error: "" }
}

const matchCondition = (item, condition) => {
  if (condition.field === "t") {
    const value = String(item.t || "").toLowerCase()
    const target = String(condition.value).toLowerCase()
    return value.includes(target)
  }

  const value = Number(item[condition.field] || 0)
  const target = condition.value
  switch (condition.operator) {
    case ">":
      return value > target
    case ">=":
      return value >= target
    case "<":
      return value < target
    case "<=":
      return value <= target
    case "=":
      return value === target
    default:
      return false
  }
}

const applySort = () => {
  const sortMode = sortModeSelect.value
  state.filtered.sort((a, b) => {
    if (sortMode === "rating") {
      return b.r - a.r || b.c - a.c
    }
    if (sortMode === "count") {
      return b.c - a.c || b.r - a.r
    }
    return 0
  })
}

const runQuery = () => {
  const query = sqlQueryInput.value.trim()
  const { conditions, error } = parseSqlQuery(query)
  queryError.textContent = error
  if (error) {
    state.filtered = []
    state.visibleCount = 0
    state.hasQueried = true
    resultCount.textContent = "解析失败"
    render()
    return
  }

  const filtered = state.items.filter((item) => {
    for (const condition of conditions) {
      if (!matchCondition(item, condition)) {
        return false
      }
    }
    return true
  })

  state.filtered = filtered
  state.visibleCount = state.pageSize
  state.hasQueried = true
  applySort()
  resultCount.textContent = `返回 ${filtered.length} 本`
  render()
}

const render = () => {
  if (!state.hasQueried) {
    grid.innerHTML = `<div class="empty">请输入条件后点击查询</div>`
    pagination.style.display = "none"
    return
  }

  if (state.filtered.length === 0) {
    grid.innerHTML = `<div class="empty">无结果</div>`
    pagination.style.display = "none"
    return
  }

  const visibleItems = state.filtered.slice(0, state.visibleCount)
  grid.innerHTML = visibleItems
    .map((item) => {
      return `
        <article class="card">
          <div class="content">
            <h2><a href="${item.u}" target="_blank" rel="noreferrer">${item.t}</a></h2>
            <div class="rating">
              <span class="score">${item.r.toFixed(1)}</span>
              <span class="count">${formatCount(item.c)}人评价</span>
            </div>
          </div>
        </article>
      `
    })
    .join("")

  if (state.visibleCount >= state.filtered.length) {
    pagination.style.display = "none"
  } else {
    pagination.style.display = "flex"
  }
}

const loadData = async () => {
  const resp = await fetch("./books.json")
  if (!resp.ok) {
    throw new Error("无法加载数据")
  }
  const data = await resp.json()
  state.items = Array.isArray(data) ? data : data.items || []
  resultCount.textContent = "请输入条件后查询"
  render()
}

const bindEvents = () => {
  runQueryButton.addEventListener("click", runQuery)
  sqlQueryInput.addEventListener("input", () => {
    queryError.textContent = ""
  })
  sqlQueryInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      runQuery()
    }
  })
  sortModeSelect.addEventListener("change", () => {
    if (!state.hasQueried) return
    applySort()
    render()
  })
  loadMoreButton.addEventListener("click", () => {
    state.visibleCount += state.pageSize
    render()
  })
}

bindEvents()
loadData().catch((err) => {
  resultCount.textContent = err.message
  grid.innerHTML = `<div class="empty">无法加载 books.json</div>`
  pagination.style.display = "none"
})
