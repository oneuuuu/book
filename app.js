const grid = document.getElementById("grid")
const sqlQueryInput = document.getElementById("sqlQuery")
const queryError = document.getElementById("queryError")
const sortModeSelect = document.getElementById("sortMode")
const sourceModeSelect = document.getElementById("sourceMode")
const statusFilterSelect = document.getElementById("statusFilter")
const runQueryButton = document.getElementById("runQuery")
const resultCount = document.getElementById("resultCount")
const loadMoreButton = document.getElementById("loadMore")
const pagination = document.getElementById("pagination")

const state = {
  douban: [],
  goodreads: [],
  readIds: new Set(),
  filtered: [],
  visibleCount: 0,
  pageSize: 30,
  hasQueried: false,
  showStatus: false,
}

const formatCount = (count) => {
  if (count >= 1000000) return `${(count / 1000000).toFixed(1)}M`
  if (count >= 1000) return `${(count / 1000).toFixed(1)}K`
  return `${count}`
}

const fieldAliases = {
  r: "r",
  c: "c",
  t: "t",
  a: "a",
  rating: "r",
  count: "c",
  title: "t",
  author: "a",
}

const parseSqlQuery = (input) => {
  if (!input) return { conditions: [], error: "" }
  const tokens = input.trim().split(/\s+/).filter(Boolean)
  const conditions = []
  for (const token of tokens) {
    const match = token.match(/^([^:]+):(>=|<=|=|>|<)?(.+)$/)
    if (!match) return { conditions: [], error: `Cannot parse: ${token}` }
    const fieldKey = match[1].toLowerCase()
    const field = fieldAliases[fieldKey]
    if (!field) return { conditions: [], error: `Unknown field: ${match[1]}` }
    const operator = match[2] || "="
    const value = match[3]
    conditions.push({
      field,
      operator,
      value: field === "t" || field === "a" ? value : Number(value),
    })
  }
  return { conditions, error: "" }
}

const matchCondition = (item, condition) => {
  if (condition.field === "t" || condition.field === "a") {
    const value = String(item[condition.field] || "").toLowerCase()
    const target = String(condition.value).toLowerCase()
    return value.includes(target)
  }
  const value = Number(item[condition.field] || 0)
  const target = condition.value
  switch (condition.operator) {
    case ">": return value > target
    case ">=": return value >= target
    case "<": return value < target
    case "<=": return value <= target
    case "=": return value === target
    default: return false
  }
}

const getSourceItems = () => {
  const source = sourceModeSelect.value
  if (source === "douban") return state.douban.map((b) => ({ ...b, _s: "db" }))
  if (source === "goodreads") return state.goodreads.map((b) => ({ ...b, _s: "gr" }))
  return [
    ...state.douban.map((b) => ({ ...b, _s: "db" })),
    ...state.goodreads.map((b) => ({ ...b, _s: "gr" })),
  ]
}

const applySort = () => {
  const sortMode = sortModeSelect.value
  state.filtered.sort((a, b) => {
    if (sortMode === "rating") return b.r - a.r || b.c - a.c
    if (sortMode === "count") return b.c - a.c || b.r - a.r
    return 0
  })
}

const makeUrl = (item) => {
  if (item._s === "gr") return `https://www.goodreads.com/book/show/${item.i}`
  return `https://book.douban.com/subject/${item.i}/`
}

const escapeHtml = (str) =>
  str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;")

const runQuery = () => {
  const query = sqlQueryInput.value.trim()
  const { conditions, error } = parseSqlQuery(query)
  const statusFilter = statusFilterSelect.value

  queryError.textContent = error
  if (error) {
    state.filtered = []
    state.visibleCount = 0
    state.hasQueried = true
    resultCount.textContent = "Parse error"
    render()
    return
  }

  const pool = getSourceItems()
  const filtered = pool.filter((item) => {
    // Basic conditions
    if (!conditions.every((cond) => matchCondition(item, cond))) return false

    // Status filter (only applied if showStatus is true)
    if (state.showStatus) {
      if (statusFilter === "read") {
        return state.readIds.has(String(item.i))
      } else if (statusFilter === "unread") {
        return !state.readIds.has(String(item.i))
      }
    }

    return true
  })

  state.filtered = filtered
  state.visibleCount = state.pageSize
  state.hasQueried = true
  applySort()

  const dbCount = filtered.filter(b => b._s === "db").length
  const grCount = filtered.filter(b => b._s === "gr").length
  resultCount.innerHTML = `<span>${filtered.length} books found</span> <span class="badge badge-db">${dbCount}</span> <span class="badge badge-gr">${grCount}</span>`

  render()
}

const render = () => {
  if (!state.hasQueried) {
    grid.innerHTML = `<div class="empty">Enter a filter and click Search</div>`
    pagination.style.display = "none"
    return
  }

  if (state.filtered.length === 0) {
    grid.innerHTML = `<div class="empty">No results</div>`
    pagination.style.display = "none"
    return
  }

  const visibleItems = state.filtered.slice(0, state.visibleCount)
  grid.innerHTML = visibleItems
    .map((item) => {
      const url = makeUrl(item)
      const badgeClass = item._s === "gr" ? "badge-gr" : "badge-db"
      const authorContent = item.a ? escapeHtml(item.a) : ""
      const sourceClass = badgeClass === 'badge-db' ? 'source-db' : 'source-gr'
      const isRead = state.readIds.has(String(item.i))
      const readBadge = (state.showStatus && isRead) ? `<span class="badge badge-read">Read</span>` : ""

      return `
        <article class="card">
          <div class="col-title">
            <a href="${url}" target="_blank" rel="noreferrer">${escapeHtml(item.t)}</a>
            ${readBadge}
          </div>
          <div class="col-author" title="${authorContent}">
            ${authorContent}
          </div>
          <div class="col-rating ${sourceClass}">
            <span class="score">${item.r}</span>
          </div>
          <div class="col-count ${sourceClass}">
            <span class="count">${formatCount(item.c)}</span>
          </div>
        </article>
      `
    })
    .join("")

  pagination.style.display = state.visibleCount >= state.filtered.length ? "none" : "flex"
}

const loadData = async () => {
  const [booksResp, readResp] = await Promise.all([
    fetch("./data/books.json"),
    fetch("./data/read.json").catch(() => null)
  ])

  if (!booksResp.ok) throw new Error("Failed to load books.json")

  const booksData = await booksResp.json()
  state.douban = booksData.douban || []
  state.goodreads = booksData.goodreads || []

  if (readResp && readResp.ok) {
    const readData = await readResp.json()
    state.readIds = new Set(readData.map(item => String(item.id)))
  }

  resultCount.textContent = `${state.douban.length + state.goodreads.length} books loaded`
  render()
}

const bindEvents = () => {
  const urlParams = new URLSearchParams(window.location.search)
  if (urlParams.has('s')) {
    state.showStatus = true
    document.querySelector('.controls').classList.add('show-status')
  }

  runQueryButton.addEventListener("click", runQuery)
  sqlQueryInput.addEventListener("input", () => { queryError.textContent = "" })
  sqlQueryInput.addEventListener("keydown", (e) => { if (e.key === "Enter") runQuery() })
  sortModeSelect.addEventListener("change", () => {
    if (!state.hasQueried) return
    applySort()
    render()
  })
  sourceModeSelect.addEventListener("change", () => {
    if (!state.hasQueried) return
    runQuery()
  })
  statusFilterSelect.addEventListener("change", () => {
    if (!state.hasQueried) return
    runQuery()
  })
  loadMoreButton.addEventListener("click", () => {
    state.visibleCount += state.pageSize
    render()
  })
}

bindEvents()
loadData().catch((err) => {
  resultCount.textContent = err.message
  grid.innerHTML = `<div class="empty">Failed to load data</div>`
  pagination.style.display = "none"
})
