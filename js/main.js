/**
 * 每日新闻摘要 — 主脚本
 * 加载 news.json 并渲染页面
 */

(function () {
  'use strict';

  // ---- 日期显示 ----
  const now = new Date();
  const weekdays = ['日', '一', '二', '三', '四', '五', '六'];
  const dateStr =
    now.getFullYear() + '年' +
    (now.getMonth() + 1) + '月' +
    now.getDate() + '日 · 星期' +
    weekdays[now.getDay()];
  const dateEl = document.getElementById('currentDate');
  if (dateEl) dateEl.textContent = dateStr;

  // ---- 栏目映射 ----
  const categoryMap = {
    politics: 'politics',
    economy: 'economy',
    military: 'military',
    tech: 'tech',
    world: 'world'
  };

  const categoryNames = {
    politics: '政治',
    economy: '经济',
    military: '军事',
    tech: '科技',
    world: '国际'
  };

  // ---- 渲染函数 ----
  function renderCard(article) {
    const time = article.publishedAt
      ? new Date(article.publishedAt).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
      : '';
    return '' +
      '<a class="card" href="' + (article.url || '#') + '" target="_blank" rel="noopener">' +
        '<div class="card-title">' +
          '<span class="card-dot"></span>' +
          escapeHtml(article.title || '无标题') +
        '</div>' +
        '<div class="card-meta">' +
          '<span>📰 ' + escapeHtml(article.source?.name || '') + '</span>' +
          (time ? '<span>🕒 ' + time + '</span>' : '') +
        '</div>' +
        (article.description
          ? '<p class="card-desc">' + escapeHtml(article.description) + '</p>'
          : '') +
        '<span class="card-link">阅读全文</span>' +
      '</a>';
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function renderCategory(key, articles) {
    const container = document.getElementById('cards-' + key);
    if (!container) return;
    if (!articles || articles.length === 0) {
      container.innerHTML = '<div class="empty-card">暂无' + (categoryNames[key] || key) + '新闻，请稍后再来</div>';
      return;
    }
    container.innerHTML = articles.map(renderCard).join('');
  }

  // ---- 加载数据 ----
  function loadNews() {
    return fetch('data/news.json')
      .then(function (res) {
        if (!res.ok) throw new Error('HTTP ' + res.status);
        return res.json();
      })
      .then(function (data) {
        // 更新时间戳
        var timeEl = document.getElementById('updateTime');
        var barEl = document.getElementById('updateBar');
        if (data.updatedAt) {
          if (timeEl) timeEl.textContent = data.updatedAt;
        } else {
          if (timeEl) timeEl.textContent = dateStr;
        }
        if (barEl) barEl.style.display = 'block';

        // 渲染各栏目
        Object.keys(categoryMap).forEach(function (key) {
          var articles = (data.categories && data.categories[key]) ? data.categories[key] : [];
          renderCategory(key, articles);
        });
      })
      .catch(function (err) {
        console.warn('新闻数据加载失败，使用示例数据:', err.message);
        var timeEl = document.getElementById('updateTime');
        if (timeEl) timeEl.textContent = '示例数据 (' + dateStr + ')';
        renderFallback();
      });
  }

  // ---- Fallback 示例数据 ----
  function renderFallback() {
    var sampleArticles = [
      { title: '每日新闻摘要已就绪', description: '每天早上 6:00 将自动更新最新的政治、经济、军事、科技、国际新闻摘要。', source: { name: '系统' }, publishedAt: new Date().toISOString(), url: '#' },
      { title: '配置 NewsAPI 后自动拉取新闻', description: '在 GitHub Actions 中配置 NEWSAPI_KEY 密钥，系统将每天自动从 NewsAPI 拉取最新新闻并展示在此页面。', source: { name: '系统' }, publishedAt: new Date().toISOString(), url: '#' },
    ];
    Object.keys(categoryMap).forEach(function (key) {
      renderCategory(key, sampleArticles);
    });
  }

  // ---- 启动 ----
  loadNews();
})();
