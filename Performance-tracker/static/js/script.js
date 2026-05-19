/* -------------------------------------------------------------
 * Client-Side Controller
 * Handles SPA navigation, sliders, prediction fetches, results
 * highlighting, and dynamic feature importance charts.
 * ------------------------------------------------------------- */

const API_BASE =
  window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? "http://127.0.0.1:5000"
    : window.location.origin;


document.addEventListener('DOMContentLoaded', () => {
    // 1. Setup SPA Tab Navigation based on Location Hash
    initNavigation();

    // 2. Load Model Feature Importances when landing on About page
    loadFeatureImportances();
});

/**
 * 🗺️ Dynamic Tab / SPA Page Navigation
 */
function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const tabId = item.getAttribute('data-tab');
            switchTab(tabId);
        });
    });

    // Handle initial load with hash
    const currentHash = window.location.hash.replace('#', '');
    const validTabs = ['home', 'predict', 'about', 'contact'];
    if (currentHash && validTabs.includes(currentHash)) {
        switchTab(currentHash);
    } else {
        switchTab('home');
    }

    // Bind hash change listener
    window.addEventListener('hashchange', () => {
        const hash = window.location.hash.replace('#', '');
        if (hash && validTabs.includes(hash)) {
            switchTab(hash, false);
        }
    });
}

function switchTab(tabId, updateHash = true) {
    // 1. Update navigation items active state
    document.querySelectorAll('.nav-item').forEach(item => {
        if (item.getAttribute('data-tab') === tabId) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });

    // 2. Toggle visible SPA view panels
    document.querySelectorAll('.tab-view').forEach(view => {
        view.classList.remove('active');
    });
    
    const targetView = document.getElementById(`${tabId}-view`);
    if (targetView) {
        targetView.classList.add('active');
    }

    // 3. Update window hash history if requested
    if (updateHash) {
        window.location.hash = tabId;
    }

    // 4. Scroll smoothly to top of view
    window.scrollTo({ top: 0, behavior: 'smooth' });

    // 5. Special hook for animating About page progress bars
    if (tabId === 'about') {
        animateFeatureBars();
    }
}

/**
 * 🎚️ Dynamic slider label tracking
 */
function updateSliderValue(sliderEl, suffix = ' hrs') {
    const valId = `val-${sliderEl.name}`;
    const indicator = document.getElementById(valId);
    if (indicator) {
        indicator.textContent = `${sliderEl.value}${suffix}`;
    }
}

/**
 * 🚀 Form Submission and AI Prediction API Call
 */
async function submitPrediction(e) {
    e.preventDefault();

    const form = document.getElementById('prediction-form');
    const btnPredict = document.getElementById('btn-predict');
    const btnText = document.getElementById('btn-text');
    const btnSpinner = document.getElementById('btn-spinner');
    const resultContainer = document.getElementById('result-container');

    // 1. Gather all form values
    const formData = new FormData(form);
    const payload = {};
    formData.forEach((value, key) => {
        payload[key] = value;
    });

    // 2. Set UI loading state
    btnPredict.disabled = true;
    btnText.textContent = "AI Analysis In Progress...";
    btnSpinner.classList.remove('hidden');
    resultContainer.classList.add('hidden');

    try {
        // 3. Make Flask API Call
        const response = await fetch(`${API_BASE}/predict`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (!response.ok || !result.success) {
            throw new Error(result.error || 'Server error during prediction.');
        }

        // 4. Render prediction output dynamically
        renderPredictionResults(result);

    } catch (err) {
        alert(`Prediction Error: ${err.message}`);
        console.error("Prediction Error details:", err);
    } finally {
        // 5. Reset loading button state
        btnPredict.disabled = false;
        btnText.textContent = "Predict Student Performance";
        btnSpinner.classList.add('hidden');
    }
}

/**
 * 🌟 Dynamic Highlighted Results Rendering & Insights
 */
function renderPredictionResults(data) {
    const resultContainer = document.getElementById('result-container');
    const scoreVal = document.getElementById('result-score');
    const levelVal = document.getElementById('result-level');
    const attendanceVal = document.getElementById('result-attendance');
    const engagementVal = document.getElementById('result-engagement');
    const insightText = document.getElementById('result-insight-text');

    // Update Scores
    scoreVal.textContent = data.exam_score.toFixed(1);
    attendanceVal.textContent = data.attendance_status;
    engagementVal.textContent = `${data.engagement_level}%`;

    // Apply level styling badges
    levelVal.textContent = data.performance_level;
    levelVal.className = 'detail-val badge-level'; // Reset

    // Highlight card color glows matching performance level
    resultContainer.className = 'result-card glass-panel'; // Reset
    
    if (data.performance_level === "Excellent" || data.performance_level === "Good") {
        levelVal.classList.add('level-excellent');
    } else if (data.performance_level === "Average") {
        levelVal.classList.add('level-average');
    } else {
        levelVal.classList.add('level-low');
    }

    let insightHTML = "";

    if (data.exam_score > 75) {
        resultContainer.classList.add('glow-green');
        insightHTML = `
            <div style="color: var(--color-green); font-weight: bold; margin-bottom: 0.5rem;">
                <i class="fa-solid fa-circle-check"></i> High Performance Expected
            </div>
            The student demonstrates strong academic performance and high engagement levels. Continued consistency can help maintain excellent outcomes.
        `;
    } else if (data.exam_score >= 40) {
        resultContainer.classList.add('glow-cyan');
        insightHTML = `
            <div style="color: var(--color-cyan); font-weight: bold; margin-bottom: 0.5rem;">
                <i class="fa-solid fa-circle-info"></i> Moderate Performance Expected
            </div>
            The student shows stable academic performance with moderate consistency. Improving study efficiency and engagement may further increase results.
        `;
    } else {
        resultContainer.classList.add('glow-pink');
        insightHTML = `
            <div style="color: var(--color-pink); font-weight: bold; margin-bottom: 0.5rem;">
                <i class="fa-solid fa-triangle-exclamation"></i> Action Recommended
            </div>
            Performance indicates academic risk. Increased attendance, consistent study habits, and tutoring support are recommended.
        `;
    }

    insightText.innerHTML = insightHTML;

    // Show output card
    resultContainer.classList.remove('hidden');

    // Scroll smoothly to output analysis
    setTimeout(() => {
        resultContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 100);
}

function closeResult() {
    const resultContainer = document.getElementById('result-container');
    resultContainer.classList.add('hidden');
}

/**
 * 📊 Query Live Feature Importances from RandomForest model
 */
let importancesLoaded = false;

async function loadFeatureImportances() {
    const container = document.getElementById('feature-importance-container');
    if (!container) return;

    try {
        const response = await fetch(`${API_BASE}/about-features`);
        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.error || 'Failed to fetch features');
        }

        let html = "";
        data.importances.forEach((item, index) => {
            // Keep it tidy by showing top 10 features, but can display more
            if (index >= 10) return; 

            html += `
                <div class="importance-row">
                    <div class="importance-info">
                        <span class="importance-name">${item.feature}</span>
                        <span class="importance-value">${item.importance.toFixed(1)}%</span>
                    </div>
                    <div class="bar-track">
                        <div class="bar-fill" data-width="${item.importance}%"></div>
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;
        importancesLoaded = true;

        // If we are currently looking at the About page, animate immediately
        if (document.getElementById('about-view').classList.contains('active')) {
            animateFeatureBars();
        }

    } catch (err) {
        container.innerHTML = `
            <div style="color: var(--color-red); padding: 2rem 0; text-align: center;">
                <i class="fa-solid fa-triangle-exclamation"></i> Error loading features: ${err.message}
            </div>
        `;
    }
}

/**
 * ⚡ Animate Feature Progress Bars (Width 0 -> Target)
 */
function animateFeatureBars() {
    if (!importancesLoaded) return;
    
    // Tiny delay to allow DOM render
    setTimeout(() => {
        const fills = document.querySelectorAll('.bar-fill');
        fills.forEach(fill => {
            const targetWidth = fill.getAttribute('data-width');
            fill.style.width = targetWidth;
        });
    }, 150);
}


