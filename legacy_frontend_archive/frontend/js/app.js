/* ============================================
   KAVACH – Main App Logic
   Tab navigation, Risk meter, Result display
   ============================================ */

const KavachApp = {
    currentTab: 'dashboard',

    init() {
        this.setupTabs();
        I18n.init();
    },

    initDashboard() {
        this.switchTab('dashboard');
    },

    /* ---- Tab Navigation ---- */
    setupTabs() {
        // Event delegation to catch all .tab-trigger elements (cards, buttons, tabs)
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('.tab-trigger');
            if (btn && btn.dataset.tab) {
                e.preventDefault();
                this.switchTab(btn.dataset.tab);
            }
        });
        
        // Ensure starting tab is processed correctly
        this.switchTab(this.currentTab || 'dashboard');
    },

    switchTab(tab) {
        this.currentTab = tab;

        const scannerWrapper = document.getElementById('scanner-wrapper');
        const panelDashboard = document.getElementById('panel-dashboard');
        const gridContainer = document.getElementById('scanner-grid-container');

        // Update active states for Sidebar (Desktop)
        document.querySelectorAll('aside .tab-trigger').forEach(asideBtn => {
            if (asideBtn.getAttribute('data-tab') === tab || (tab !== 'dashboard' && asideBtn.getAttribute('data-tab') === 'screenshot')) {
                asideBtn.classList.replace('text-slate-300', 'text-background-dark');
                asideBtn.classList.replace('hover:text-white', 'hover:text-background-dark');
                asideBtn.classList.replace('hover:bg-white/5', 'hover:bg-primary');
                asideBtn.classList.add('bg-primary', 'font-bold');
            } else {
                asideBtn.classList.replace('text-background-dark', 'text-slate-300');
                asideBtn.classList.remove('bg-primary', 'font-bold');
                asideBtn.classList.add('hover:text-white', 'hover:bg-white/5');
            }
        });

        // Update active states for Bottom Nav & General Triggers
        document.querySelectorAll('nav.lg\\:hidden .tab-trigger, #scanner-wrapper .tab-trigger').forEach(btn => {
            const isActive = btn.dataset.tab === tab;
            btn.classList.toggle('active', isActive);
            
            if (btn.classList.contains('tool-tab-btn')) {
                if (isActive) {
                    btn.classList.add('bg-cyan-500', 'text-slate-950', 'shadow-[0_0_12px_rgba(13,200,242,0.4)]');
                    btn.classList.remove('text-slate-300', 'hover:text-white', 'bg-transparent');
                } else {
                    btn.classList.remove('bg-cyan-500', 'text-slate-950', 'shadow-[0_0_12px_rgba(13,200,242,0.4)]');
                    btn.classList.add('text-slate-300', 'hover:text-white');
                }
            } else {
                btn.classList.toggle('text-cyan-400', isActive);
                btn.classList.toggle('text-slate-400', !isActive);
            }
        });

        if (tab === 'dashboard') {
            if (scannerWrapper) scannerWrapper.classList.add('hidden');
            if (panelDashboard) panelDashboard.classList.remove('hidden');
        } else {
            if (panelDashboard) panelDashboard.classList.add('hidden');
            if (scannerWrapper) scannerWrapper.classList.remove('hidden');
            
            const isPlaceholder = (tab === 'email' || tab === 'link');
            if (gridContainer) {
                gridContainer.classList.toggle('hidden', isPlaceholder);
            }

            // Show specific scanner panel inside wrapper
            document.querySelectorAll('#scanner-wrapper .tab-panel').forEach(panel => {
                const isActive = panel.id === `panel-${tab}`;
                panel.classList.toggle('hidden', !isActive);
                panel.classList.toggle('active', isActive);
            });

            // Update Hero Text using i18n
            const titleEl = document.getElementById(`main-hero-title-${tab}`);
            const descEl = document.getElementById(`main-hero-desc-${tab}`);
            
            const titles = {
                'screenshot': 'Screenshot Scam Detector',
                'qrcode': 'QR-Code Scam Detector',
                'url': 'Fraudulent Website Checker',
                'email': 'Phishing Email Detector',
                'link': 'Malicious Link Scanner'
            };
            const descs = {
                'screenshot': 'Inspect suspicious messages, payment screenshots, and receipts for potential fraud indicators.',
                'qrcode': 'Check QR codes before opening unfamiliar destinations or making payments.',
                'url': 'Check suspicious websites for potentially unsafe destinations and phishing indicators.',
                'email': 'Email analysis will be available in a future update.',
                'link': 'Advanced malicious-link scanning will be available in a future update.'
            };

            if (titleEl && titles[tab]) titleEl.textContent = titles[tab];
            if (descEl && descs[tab]) descEl.textContent = descs[tab];
        }

        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    },

    /* ---- Results & Animations ---- */
    displayResult(targetId, data) {
        const container = document.getElementById('result-container');
        const defaultTips = document.getElementById('default-tips');
        
        container.classList.remove('hidden');
        if (defaultTips) defaultTips.classList.add('hidden');

        // Clone template
        const template = document.getElementById('result-template');
        const clone = template.content.cloneNode(true);
        
        // 1. Risk Meter
        const score = data.risk_score || 0;
        const meterFill = clone.getElementById('meter-fill');
        const scoreEl = clone.getElementById('meter-score');
        
        // Calculate offset (251.2 is circumference)
        const offset = 251.2 - (score / 100) * 251.2;
        
        // Color shifts based on risk
        if (score >= 70) {
            meterFill.classList.replace('text-primary', 'text-red-500');
        } else if (score >= 30) {
            meterFill.classList.replace('text-primary', 'text-yellow-500');
        }

        // Apply with a delay for transition effect
        setTimeout(() => {
            if (meterFill) meterFill.style.strokeDashoffset = offset;
            this.animateNumber(scoreEl, 0, score, 1000);
        }, 100);

        // 2. Status Badge
        const badge = clone.getElementById('status-badge');
        const statusText = clone.getElementById('status-text');
        const statusIcon = clone.getElementById('status-icon');
        const status = data.status || 'safe';

        if (status === 'safe') {
            badge.classList.add('bg-green-500/20', 'border', 'border-green-500', 'text-green-500');
            statusText.textContent = I18n.t('status_safe');
            statusIcon.textContent = 'verified';
        } else if (status === 'suspicious') {
            badge.classList.add('bg-yellow-500/20', 'border', 'border-yellow-500', 'text-yellow-500');
            statusText.textContent = I18n.t('status_suspicious');
            statusIcon.textContent = 'gpp_maybe';
        } else {
            badge.classList.add('bg-red-500/20', 'border', 'border-red-500', 'text-red-500');
            statusText.textContent = I18n.t('status_blocked');
            statusIcon.textContent = 'report';
        }

        // 3. Reasons (Flaws)
        const reasonsList = clone.getElementById('reasons-list');
        (data.reasons || []).forEach(reason => {
            const item = document.createElement('div');
            item.className = `p-3 rounded-lg flex items-start gap-3 border ${status === 'safe' ? 'bg-green-500/5 border-green-500/10' : 'bg-red-500/5 border-red-500/10'}`;
            
            const icon = status === 'safe' ? 'check_circle' : 'warning';
            const iconColor = status === 'safe' ? 'text-green-500' : 'text-red-500';
            
            item.innerHTML = `
                <div class="shrink-0 pt-0.5">
                    <span class="material-symbols-outlined text-[18px] ${iconColor} leading-none">${icon}</span>
                </div>
                <p class="text-[11px] text-slate-300 font-medium leading-[1.4] break-words">${reason}</p>
            `;
            reasonsList.appendChild(item);
        });

        // 4. Data Section
        const fieldsData = data.extracted_fields || data.decoded_data || {};
        if (Object.keys(fieldsData).length > 0) {
            const dataSection = clone.getElementById('data-section');
            const grid = clone.getElementById('fields-grid');
            dataSection.classList.remove('hidden');
            dataSection.classList.add('flex'); // Because we use flex-col on it
            
            Object.entries(fieldsData).forEach(([key, value]) => {
                if (!value) return;
                const field = document.createElement('div');
                field.className = 'bg-[#121f26] p-3 rounded-lg border border-[#1a2c32]';
                field.innerHTML = `
                    <p class="text-[9px] uppercase text-[#0dc8f2] font-black tracking-widest mb-1 truncate">${key.replace(/_/g, ' ')}</p>
                    <p class="text-[11px] text-white font-medium break-words leading-[1.3]">${value}</p>
                `;
                grid.appendChild(field);
            });
        }

        // 5. Summary
        const summaryEl = clone.getElementById('evidence-summary');
        summaryEl.textContent = data.evidence_summary || I18n.t('evidence_summary_default') || "Automated SignalSafe verification based on visual and textual patterns.";

        // 6. Report Section (New)
        const reportSection = clone.getElementById('report-section');
        if (reportSection) {
            const reportCountText = clone.getElementById('report-count-text');
            const reportBtn = clone.getElementById('report-btn');
            const reportCount = data.report_count || 0;
            const url = data.url;
            
            // Only show for URL scans that are suspicious or blocked
            if (this.currentTab === 'url' && status !== 'safe' && url) {
                reportSection.classList.remove('hidden');
                reportCountText.textContent = `${reportCount} report${reportCount !== 1 ? 's' : ''} as scam`;
                
                reportBtn.addEventListener('click', async (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    reportBtn.disabled = true;
                    reportBtn.innerHTML = `<span class="material-symbols-outlined animate-spin text-[12px]">block</span> Reporting...`;
                    
                    try {
                        const response = await fetch('/api/url/report', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ url })
                        });
                        const result = await response.json();
                        if (result.status === 'success') {
                            reportCountText.textContent = `${result.report_count} report${result.report_count !== 1 ? 's' : ''} as scam`;
                            reportBtn.innerHTML = '<span class="material-symbols-outlined text-[14px]">check</span> Reported';
                            reportBtn.classList.replace('bg-red-500/10', 'bg-green-500/20');
                            reportBtn.classList.replace('text-red-500', 'text-green-500');
                            reportBtn.classList.replace('border-red-500/30', 'border-green-500/50');
                        }
                    } catch (e) {
                        console.error('Report failed:', e);
                        reportBtn.disabled = false;
                        reportBtn.innerHTML = '<span class="material-symbols-outlined text-[14px]">flag</span> Report as Scam';
                    }
                });
            }
        }

        // Inject into DOM
        container.innerHTML = '';
        container.appendChild(clone);
    },

    animateNumber(el, start, end, duration) {
        if (!el) return;
        const startTime = performance.now();
        const update = (currentTime) => {
            const progress = Math.min((currentTime - startTime) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            const value = Math.round(start + (end - start) * eased);
            el.textContent = value;
            if (progress < 1) requestAnimationFrame(update);
        };
        requestAnimationFrame(update);
    },

    setLoading(btn, isLoading) {
        if (isLoading) {
            btn._originalContent = btn.innerHTML;
            btn.innerHTML = `<span class="material-symbols-outlined animate-spin">sync</span><span>Analyzing...</span>`;
            btn.disabled = true;
        } else {
            btn.innerHTML = btn._originalContent;
            btn.disabled = false;
        }
    }
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => KavachApp.init());
