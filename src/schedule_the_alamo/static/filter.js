// Client-side tag filtering for showing cards
const activeFilters = {};  // {category: value}

function toggleFilter(category, value) {
  if (activeFilters[category] === value) {
    delete activeFilters[category];
  } else {
    activeFilters[category] = value;
  }
  applyFilters();
}

function removeFilter(category) {
  delete activeFilters[category];
  applyFilters();
}

function clearFilters() {
  for (const k of Object.keys(activeFilters)) delete activeFilters[k];
  applyFilters();
}

function applyFilters() {
  const cards = document.querySelectorAll('.showing-card');
  const hasFilters = Object.keys(activeFilters).length > 0;

  cards.forEach(card => {
    if (!hasFilters) {
      card.removeAttribute('hidden');
      return;
    }
    let match = true;
    for (const [cat, val] of Object.entries(activeFilters)) {
      if (!(card.dataset[cat] || '').includes(val)) {
        match = false;
        break;
      }
    }
    if (match) card.removeAttribute('hidden');
    else card.setAttribute('hidden', '');
  });

  renderFilterBar();
}

function renderFilterBar() {
  const bar = document.getElementById('filter-bar');
  if (!bar) return;
  const entries = Object.entries(activeFilters);
  if (!entries.length) {
    bar.classList.remove('active');
    return;
  }
  bar.classList.add('active');
  bar.innerHTML = '<span class="filter-label">Filters:</span>' +
    entries.map(([cat, val]) =>
      `<span class="filter-pill tag-${cat}">${val} <span class="remove-filter" onclick="removeFilter('${cat}')">×</span></span>`
    ).join('') +
    '<button class="clear-filters" onclick="clearFilters()">Clear all</button>';
}

// Re-apply active filters after HTMX swaps in fresh results
document.body.addEventListener('htmx:afterSettle', function() {
  if (Object.keys(activeFilters).length > 0) {
    applyFilters();
  }
});
