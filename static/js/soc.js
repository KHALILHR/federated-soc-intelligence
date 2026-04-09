/* ============================================================
   SOC Platform — Core JavaScript
   Live clock, Chart.js defaults, auto-refresh, and interactions
   ============================================================ */

document.addEventListener('DOMContentLoaded', function () {

    // ---------- Live Clock ----------
    const clockEl = document.getElementById('live-clock');
    if (clockEl) {
        function updateClock() {
            const now = new Date();
            const h = String(now.getHours()).padStart(2, '0');
            const m = String(now.getMinutes()).padStart(2, '0');
            const s = String(now.getSeconds()).padStart(2, '0');
            clockEl.textContent = `${h}:${m}:${s} UTC`;
        }
        updateClock();
        setInterval(updateClock, 1000);
    }

    // ---------- Chart.js Global Defaults ----------
    if (typeof Chart !== 'undefined') {
        Chart.defaults.color = '#8892a4';
        Chart.defaults.borderColor = 'rgba(255,255,255,0.06)';
        Chart.defaults.font.family = "'Inter', sans-serif";
        Chart.defaults.font.size = 11;
        Chart.defaults.plugins.legend.labels.usePointStyle = true;
        Chart.defaults.plugins.legend.labels.pointStyle = 'circle';
        Chart.defaults.plugins.legend.labels.padding = 16;
        Chart.defaults.scale.grid = {
            color: 'rgba(255,255,255,0.04)',
            drawBorder: false,
        };
        Chart.defaults.elements.line.tension = 0.4;
        Chart.defaults.elements.line.borderWidth = 2;
        Chart.defaults.elements.point.radius = 3;
        Chart.defaults.elements.point.hoverRadius = 6;
        Chart.defaults.plugins.tooltip.backgroundColor = '#131a2b';
        Chart.defaults.plugins.tooltip.titleColor = '#e8edf5';
        Chart.defaults.plugins.tooltip.bodyColor = '#8892a4';
        Chart.defaults.plugins.tooltip.borderColor = 'rgba(0,212,255,0.2)';
        Chart.defaults.plugins.tooltip.borderWidth = 1;
        Chart.defaults.plugins.tooltip.padding = 12;
        Chart.defaults.plugins.tooltip.cornerRadius = 8;
        Chart.defaults.plugins.tooltip.displayColors = true;
    }

    // ---------- Sidebar Active State Enhancement ----------
    const currentPath = window.location.pathname;
    document.querySelectorAll('.sidebar-nav .nav-link').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });

    // ---------- Metric Card Counter Animation ----------
    document.querySelectorAll('.metric-value[data-target]').forEach(el => {
        const target = parseFloat(el.dataset.target);
        const duration = 1500;
        const isFloat = el.dataset.float === 'true';
        const suffix = el.dataset.suffix || '';
        const start = performance.now();

        function animate(now) {
            const elapsed = now - start;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            const current = target * eased;

            if (isFloat) {
                el.textContent = current.toFixed(2) + suffix;
            } else {
                el.textContent = Math.floor(current).toLocaleString() + suffix;
            }

            if (progress < 1) requestAnimationFrame(animate);
        }
        requestAnimationFrame(animate);
    });

    // ---------- Auto-refresh data ----------
    window.socRefresh = function(url, callback, interval) {
        function fetchData() {
            fetch(url)
                .then(r => r.json())
                .then(data => callback(data))
                .catch(err => console.warn('SOC refresh error:', err));
        }
        fetchData();
        if (interval) setInterval(fetchData, interval);
    };

    // ---------- Node Map Rendering ----------
    window.renderNodeMap = function(containerId, nodes) {
        const container = document.getElementById(containerId);
        if (!container || !nodes || nodes.length === 0) return;

        container.innerHTML = '';

        const width = container.offsetWidth;
        const height = container.offsetHeight || 300;

        nodes.forEach((node, i) => {
            // Convert lat/lng to approximate x/y positions on the container
            const x = ((node.lng + 180) / 360) * width;
            const y = ((90 - node.lat) / 180) * height;

            const dot = document.createElement('div');
            dot.className = `node-map-dot ${node.status}`;
            dot.style.left = `${Math.max(10, Math.min(width - 10, x))}px`;
            dot.style.top = `${Math.max(10, Math.min(height - 10, y))}px`;
            dot.title = `${node.name} (${node.status}) — ${node.samples.toLocaleString()} samples`;

            const label = document.createElement('div');
            label.className = 'node-map-label';
            label.style.left = dot.style.left;
            label.style.top = dot.style.top;
            label.textContent = node.name;

            container.appendChild(dot);
            container.appendChild(label);
        });
    };

    // ---------- Log Stream Simulator ----------
    window.appendLogLine = function(containerId, entry) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const line = document.createElement('div');
        line.className = 'log-line';

        const ts = new Date(entry.timestamp).toISOString().replace('T', ' ').substring(0, 19);

        line.innerHTML = `
            <span class="log-ts">${ts}</span>
            <span class="log-src">${entry.source_ip}</span>
            <span class="log-dst">${entry.destination_ip}</span>
            <span class="log-sev ${entry.severity}">${entry.severity.toUpperCase()}</span>
            <span class="log-event">${entry.event_type}</span>
        `;

        container.prepend(line);

        // Keep max 100 lines
        while (container.children.length > 100) {
            container.removeChild(container.lastChild);
        }
    };
});
