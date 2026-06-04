/**
 * 全局HTML转义函数 - 防止XSS攻击
 * 将用户数据安全地插入HTML，转义所有特殊字符
 * @param {string} str - 需要转义的字符串
 * @returns {string} 转义后的安全HTML字符串
 */
window.escapeHTML = function(str) {
    if (str == null) return '';
    const div = document.createElement('div');
    div.textContent = String(str);
    return div.innerHTML;
};

/**
 * 全局交互体验工具模块
 * 包含加载状态、表单验证、Toast通知、快捷键支持等功能
 */

(function() {
    'use strict';

    // ============================================
    // 1. 加载状态管理
    // ============================================
    
    let loadingCount = 0;
    let loadingElement = null;

    /**
     * 显示全屏加载遮罩
     * @param {string} message - 加载提示文字
     */
    function showLoading(message) {
        loadingCount++;
        
        if (loadingElement) {
            loadingElement.classList.remove('hidden');
            const messageEl = loadingElement.querySelector('.loading-message');
            if (messageEl && message) {
                messageEl.textContent = message;
            }
            return;
        }

        loadingElement = document.createElement('div');
        loadingElement.id = 'global-loading';
        loadingElement.className = 'fixed inset-0 bg-black/50 flex items-center justify-center z-[9999]';
        loadingElement.innerHTML = `
            <div class="bg-white rounded-xl shadow-2xl p-8 flex flex-col items-center transform scale-100 transition-all duration-300">
                <div class="relative w-16 h-16 mb-4">
                    <div class="absolute inset-0 border-4 border-primary/20 rounded-full"></div>
                    <div class="absolute inset-0 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
                </div>
                <p class="loading-message text-gray-600 font-medium">${message || '加载中...'}</p>
                <p class="text-xs text-gray-400 mt-2">请稍候...</p>
            </div>
        `;
        document.body.appendChild(loadingElement);
        
        // 添加淡入动画
        requestAnimationFrame(() => {
            loadingElement.style.opacity = '1';
        });
    }

    /**
     * 隐藏全屏加载遮罩
     */
    function hideLoading() {
        loadingCount--;
        if (loadingCount > 0) return;
        loadingCount = 0;
        
        if (loadingElement) {
            // 添加淡出动画
            loadingElement.style.opacity = '0';
            loadingElement.style.transition = 'opacity 0.3s ease';
            
            setTimeout(() => {
                if (loadingElement && loadingElement.parentNode) {
                    loadingElement.parentNode.removeChild(loadingElement);
                }
                loadingElement = null;
            }, 300);
        }
    }

    /**
     * 带加载状态的异步函数包装器
     * @param {Function} asyncFn - 异步函数
     * @param {Object} options - 配置选项
     * @returns {Promise}
     */
    function withLoading(asyncFn, options = {}) {
        const { loadingMessage = '处理中...' } = options;
        return async function(...args) {
            showLoading(loadingMessage);
            try {
                return await asyncFn.apply(this, args);
            } finally {
                hideLoading();
            }
        };
    }

    // ============================================
    // 2. 表单验证增强
    // ============================================

    /**
     * 表单验证规则定义
     */
    const validationRules = {
        required: {
            validate: (value) => value !== null && value !== undefined && String(value).trim() !== '',
            message: '此字段为必填项'
        },
        email: {
            validate: (value) => !value || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
            message: '请输入有效的邮箱地址'
        },
        phone: {
            validate: (value) => !value || /^1[3-9]\d{9}$/.test(value),
            message: '请输入有效的手机号码'
        },
        number: {
            validate: (value) => !value || !isNaN(parseFloat(value)),
            message: '请输入有效的数字'
        },
        positive: {
            validate: (value) => !value || (parseFloat(value) > 0),
            message: '请输入正数'
        },
        integer: {
            validate: (value) => !value || /^\d+$/.test(value),
            message: '请输入整数'
        },
        minLength: {
            validate: (value, length) => !value || value.length >= length,
            message: (length) => `长度不能少于 ${length} 个字符`
        },
        maxLength: {
            validate: (value, length) => !value || value.length <= length,
            message: (length) => `长度不能超过 ${length} 个字符`
        },
        min: {
            validate: (value, min) => !value || parseFloat(value) >= min,
            message: (min) => `值不能小于 ${min}`
        },
        max: {
            validate: (value, max) => !value || parseFloat(value) <= max,
            message: (max) => `值不能大于 ${max}`
        },
        pattern: {
            validate: (value, pattern) => !value || new RegExp(pattern).test(value),
            message: '格式不正确'
        },
        stockCode: {
            validate: (value) => !value || /^[0-9]{6}(.SH|.SZ)?$/i.test(value),
            message: '请输入有效的股票代码（如：600036.SH 或 600036）'
        },
        date: {
            validate: (value) => !value || !isNaN(Date.parse(value)),
            message: '请输入有效的日期'
        },
        dateRange: {
            validate: (value, startDate, endDate) => {
                if (!value) return true;
                const date = new Date(value);
                if (startDate && date < new Date(startDate)) return false;
                if (endDate && date > new Date(endDate)) return false;
                return true;
            },
            message: '日期超出范围'
        }
    };

    /**
     * 为表单添加实时验证功能
     * @param {string} formSelector - 表单选择器
     * @param {Object} customRules - 自定义验证规则
     * @returns {Object} - 表单验证控制器
     */
    function addFormValidation(formSelector, customRules = {}) {
        const form = document.querySelector(formSelector);
        if (!form) {
            console.warn(`表单未找到: ${formSelector}`);
            return null;
        }

        const validators = { ...validationRules, ...customRules };
        const validatedFields = new Map();

        /**
         * 显示字段错误
         */
        function showFieldError(input, message) {
            const field = input.closest('.form-group, .mb-4, .mb-6');
            if (!field) return;

            // 移除已有的错误
            clearFieldError(input);

            // 添加错误样式
            input.classList.add('border-red-500', 'focus:ring-2', 'focus:ring-red-500/50');
            input.classList.remove('border-gray-300', 'focus:border-primary');

            // 创建错误消息元素
            const errorEl = document.createElement('p');
            errorEl.className = 'form-error text-red-500 text-xs mt-1 flex items-center';
            errorEl.innerHTML = `<i class="fa fa-exclamation-circle mr-1"></i>${message}`;
            errorEl.style.animation = 'slideIn 0.2s ease';

            // 插入错误消息
            if (input.parentElement.classList.contains('relative')) {
                input.parentElement.after(errorEl);
            } else {
                input.after(errorEl);
            }

            validatedFields.set(input, { valid: false, message });
        }

        /**
         * 清除字段错误
         */
        function clearFieldError(input) {
            const field = input.closest('.form-group, .mb-4, .mb-6');
            if (!field) return;

            input.classList.remove('border-red-500', 'focus:ring-2', 'focus:ring-red-500/50');
            input.classList.add('border-gray-300', 'focus:border-primary');

            const errorEl = field.querySelector('.form-error');
            if (errorEl) {
                errorEl.style.animation = 'slideOut 0.2s ease';
                setTimeout(() => errorEl.remove(), 200);
            }

            validatedFields.delete(input);
        }

        /**
         * 显示字段成功状态
         */
        function showFieldSuccess(input) {
            const field = input.closest('.form-group, .mb-4, .mb-6');
            if (!field) return;

            clearFieldError(input);
            input.classList.remove('border-red-500');
            input.classList.add('border-green-500');

            validatedFields.set(input, { valid: true });
        }

        /**
         * 验证单个字段
         */
        function validateField(input) {
            const value = input.value;
            const rules = input.dataset.validateRules;
            if (!rules) return true;

            const ruleList = rules.split(',').map(r => r.trim());
            for (const rule of ruleList) {
                const [ruleName, param] = rule.split(':');
                const validator = validators[ruleName];
                if (!validator) continue;

                const isValid = param 
                    ? validator.validate(value, ...param.split('|').map(p => isNaN(p) ? p : parseFloat(p)))
                    : validator.validate(value);

                if (!isValid) {
                    showFieldError(input, typeof validator.message === 'function' 
                        ? validator.message(...param.split('|').map(p => isNaN(p) ? p : parseFloat(p)))
                        : validator.message);
                    return false;
                }
            }

            if (value) {
                showFieldSuccess(input);
            }
            return true;
        }

        /**
         * 验证整个表单
         */
        function validateForm() {
            const inputs = form.querySelectorAll('input, select, textarea');
            let isValid = true;

            inputs.forEach(input => {
                if (input.disabled) return;
                if (!validateField(input)) {
                    isValid = false;
                }
            });

            return isValid;
        }

        /**
         * 获取表单数据
         */
        function getFormData() {
            const formData = new FormData(form);
            const data = {};
            for (const [key, value] of formData.entries()) {
                data[key] = value;
            }
            return data;
        }

        /**
         * 重置表单验证状态
         */
        function resetValidation() {
            const inputs = form.querySelectorAll('input, select, textarea');
            inputs.forEach(input => clearFieldError(input));
            validatedFields.clear();
        }

        // 绑定实时验证事件
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            // 失焦时验证
            input.addEventListener('blur', () => {
                if (input.dataset.validateRules) {
                    validateField(input);
                }
            });

            // 输入时清除错误（可选）
            input.addEventListener('input', () => {
                const field = validatedFields.get(input);
                if (field && !field.valid) {
                    // 延迟验证，让用户完成输入
                    clearTimeout(input.validateTimer);
                    input.validateTimer = setTimeout(() => validateField(input), 500);
                }
            });

            // 回车时验证并移动到下一个字段
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    const inputsArray = Array.from(inputs).filter(i => !i.disabled);
                    const currentIndex = inputsArray.indexOf(input);
                    if (currentIndex < inputsArray.length - 1) {
                        inputsArray[currentIndex + 1].focus();
                    } else {
                        form.dispatchEvent(new Event('submit'));
                    }
                }
            });
        });

        // 表单提交验证
        form.addEventListener('submit', (e) => {
            if (!validateForm()) {
                e.preventDefault();
                e.stopPropagation();
                
                // 滚动到第一个错误字段
                const firstError = form.querySelector('.border-red-500');
                if (firstError) {
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    firstError.focus();
                }
            }
        });

        return {
            validateField,
            validateForm,
            getFormData,
            resetValidation,
            clearFieldError,
            showFieldError,
            isFieldValid: (input) => validatedFields.get(input)?.valid ?? true
        };
    }

    // ============================================
    // 3. Toast通知
    // ============================================

    const toastContainer = createToastContainer();

    /**
     * 创建Toast容器
     */
    function createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'fixed top-20 right-4 z-[9998] flex flex-col gap-2 max-w-sm';
        container.style.pointerEvents = 'none';
        document.body.appendChild(container);
        return container;
    }

    /**
     * 显示Toast通知
     * @param {string} message - 提示消息
     * @param {string} type - 消息类型: success, error, warning, info
     * @param {Object} options - 配置选项
     */
    function showToast(message, type = 'info', options = {}) {
        const {
            duration = 4000,
            dismissable = true,
            title = ''
        } = options;

        const toast = document.createElement('div');
        toast.className = `toast-notification transform transition-all duration-300 translate-x-full`;
        toast.style.pointerEvents = 'auto';

        // 类型样式配置
        const typeConfig = {
            success: {
                bg: 'bg-green-50',
                border: 'border-green-500',
                icon: 'fa-check-circle',
                iconColor: 'text-green-500',
                titleBg: 'bg-green-500',
                titleColor: 'text-white'
            },
            error: {
                bg: 'bg-red-50',
                border: 'border-red-500',
                icon: 'fa-times-circle',
                iconColor: 'text-red-500',
                titleBg: 'bg-red-500',
                titleColor: 'text-white'
            },
            warning: {
                bg: 'bg-yellow-50',
                border: 'border-yellow-500',
                icon: 'fa-exclamation-triangle',
                iconColor: 'text-yellow-500',
                titleBg: 'bg-yellow-500',
                titleColor: 'text-white'
            },
            info: {
                bg: 'bg-blue-50',
                border: 'border-blue-500',
                icon: 'fa-info-circle',
                iconColor: 'text-blue-500',
                titleBg: 'bg-blue-500',
                titleColor: 'text-white'
            }
        };

        const config = typeConfig[type] || typeConfig.info;

        toast.innerHTML = `
            <div class="${config.bg} ${config.border} border-l-4 rounded-lg shadow-lg overflow-hidden">
                <div class="flex items-start p-4">
                    ${title ? `
                        <div class="flex-shrink-0">
                            <i class="fa ${config.icon} ${config.iconColor} text-xl"></i>
                        </div>
                    ` : ''}
                    <div class="ml-3 flex-1">
                        ${title ? `<p class="${config.titleBg} ${config.titleColor} text-sm font-semibold px-2 py-1 -ml-2 mb-1 rounded">${title}</p>` : ''}
                        <p class="text-gray-700 text-sm">${message}</p>
                    </div>
                    ${dismissable ? `
                        <button class="toast-close ml-2 text-gray-400 hover:text-gray-600 transition-colors">
                            <i class="fa fa-times"></i>
                        </button>
                    ` : ''}
                </div>
                <div class="h-1 bg-gray-200">
                    <div class="h-full ${config.border.replace('border-', 'bg-')} progress-bar" style="width: 100%"></div>
                </div>
            </div>
        `;

        toastContainer.appendChild(toast);

        // 动画显示
        requestAnimationFrame(() => {
            toast.classList.remove('translate-x-full');
        });

        // 进度条动画
        const progressBar = toast.querySelector('.progress-bar');
        if (progressBar) {
            progressBar.style.transition = `width ${duration}ms linear`;
            requestAnimationFrame(() => {
                progressBar.style.width = '0%';
            });
        }

        // 关闭按钮事件
        const closeBtn = toast.querySelector('.toast-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => dismissToast(toast));
        }

        // 自动关闭
        const autoCloseTimer = setTimeout(() => dismissToast(toast), duration);

        // 鼠标悬停暂停计时
        toast.addEventListener('mouseenter', () => {
            clearTimeout(autoCloseTimer);
            if (progressBar) {
                progressBar.style.transition = 'none';
                const currentWidth = progressBar.offsetWidth;
                progressBar.style.width = `${currentWidth}px`;
            }
        });

        toast.addEventListener('mouseleave', () => {
            if (progressBar) {
                const currentWidth = progressBar.offsetWidth;
                const containerWidth = toastContainer.offsetWidth;
                const remainingPercent = (currentWidth / containerWidth) * 100;
                const remainingTime = (remainingPercent / 100) * duration;
                
                progressBar.style.transition = `width ${remainingTime}ms linear`;
                progressBar.style.width = '0%';
            }
            setTimeout(() => dismissToast(toast), remainingTime || 0);
        });

        function dismissToast(element) {
            element.classList.add('opacity-0', 'translate-x-full');
            setTimeout(() => element.remove(), 300);
        }

        return toast;
    }

    // 快捷方法
    const toast = {
        success: (message, options) => showToast(message, 'success', options),
        error: (message, options) => showToast(message, 'error', options),
        warning: (message, options) => showToast(message, 'warning', options),
        info: (message, options) => showToast(message, 'info', options)
    };

    // ============================================
    // 4. 快捷键支持
    // ============================================

    const shortcutHandlers = {};

    /**
     * 注册快捷键
     * @param {string} shortcut - 快捷键描述
     * @param {Function} handler - 处理函数
     * @param {Object} options - 配置选项
     */
    function registerShortcut(shortcut, handler, options = {}) {
        const { preventDefault = true, description = '' } = options;
        
        const keys = parseShortcut(shortcut);
        const id = `${keys.ctrl ? 'ctrl+' : ''}${keys.alt ? 'alt+' : ''}${keys.shift ? 'shift+' : ''}${keys.key}`.toLowerCase();
        
        if (!shortcutHandlers[id]) {
            shortcutHandlers[id] = [];
        }
        
        shortcutHandlers[id].push({ handler, preventDefault, description });
    }

    /**
     * 解析快捷键字符串
     */
    function parseShortcut(shortcut) {
        const parts = shortcut.toLowerCase().split('+').map(p => p.trim());
        return {
            ctrl: parts.includes('ctrl') || parts.includes('control'),
            alt: parts.includes('alt'),
            shift: parts.includes('shift'),
            key: parts[parts.length - 1]
        };
    }

    /**
     * 全局快捷键事件处理
     */
    document.addEventListener('keydown', function(e) {
        // 忽略在输入框中的快捷键（除了Escape）
        const target = e.target;
        const isInputField = target.tagName === 'INPUT' || 
                            target.tagName === 'TEXTAREA' || 
                            target.tagName === 'SELECT' ||
                            target.isContentEditable;
        
        const key = e.key.toLowerCase();
        
        // Escape 键特殊处理：关闭弹窗
        if (key === 'escape') {
            e.preventDefault();
            
            // 关闭所有打开的模态框
            const modals = document.querySelectorAll('.modal:not(.hidden), .modal-overlay:not(.hidden), [data-modal-open="true"]');
            modals.forEach(modal => {
                modal.classList.add('hidden');
                modal.removeAttribute('data-modal-open');
            });
            
            // 关闭Toast
            const toasts = document.querySelectorAll('.toast-notification');
            toasts.forEach(toast => {
                toast.classList.add('opacity-0', 'translate-x-full');
                setTimeout(() => toast.remove(), 300);
            });
            
            // 调用全局Escape处理程序
            if (shortcutHandlers['escape']) {
                shortcutHandlers['escape'].forEach(({ handler }) => handler(e));
            }
            return;
        }

        // 如果在输入字段中，不处理其他快捷键
        if (isInputField) return;

        const id = `${e.ctrlKey ? 'ctrl+' : ''}${e.altKey ? 'alt+' : ''}${e.shiftKey ? 'shift+' : ''}${key}`;
        
        if (shortcutHandlers[id]) {
            e.preventDefault();
            shortcutHandlers[id].forEach(({ handler, preventDefault }) => {
                if (preventDefault !== false) {
                    e.preventDefault();
                }
                handler(e);
            });
        }
    });

    /**
     * 快捷键菜单组件
     */
    function createShortcutMenu() {
        const menu = document.createElement('div');
        menu.id = 'shortcut-menu';
        menu.className = 'fixed bottom-4 left-4 bg-white rounded-lg shadow-xl border border-gray-200 p-4 z-50 hidden';
        menu.style.minWidth = '280px';
        
        menu.innerHTML = `
            <div class="flex justify-between items-center mb-3 pb-2 border-b">
                <h4 class="font-semibold text-gray-700">键盘快捷键</h4>
                <button id="close-shortcut-menu" class="text-gray-400 hover:text-gray-600">
                    <i class="fa fa-times"></i>
                </button>
            </div>
            <div id="shortcut-list" class="space-y-2 text-sm"></div>
        `;
        
        document.body.appendChild(menu);
        
        document.getElementById('close-shortcut-menu').addEventListener('click', () => {
            menu.classList.add('hidden');
        });
        
        return menu;
    }

    /**
     * 显示快捷键菜单
     */
    function showShortcutMenu() {
        let menu = document.getElementById('shortcut-menu');
        if (!menu) {
            menu = createShortcutMenu();
        }
        
        const list = menu.querySelector('#shortcut-list');
        list.innerHTML = '';
        
        const shortcuts = [
            { key: 'Ctrl+K', desc: '全局搜索' },
            { key: 'Ctrl+E', desc: '编辑个人资料' },
            { key: 'Ctrl+N', desc: '新建策略' },
            { key: 'Escape', desc: '关闭弹窗' }
        ];
        
        shortcuts.forEach(s => {
            list.innerHTML += `
                <div class="flex justify-between items-center py-1">
                    <span class="text-gray-600">${s.desc}</span>
                    <kbd class="px-2 py-1 bg-gray-100 rounded text-xs font-mono">${s.key}</kbd>
                </div>
            `;
        });
        
        menu.classList.remove('hidden');
    }

    // ============================================
    // 初始化默认快捷键
    // ============================================

    function initDefaultShortcuts() {
        // Ctrl+K: 全局搜索
        registerShortcut('ctrl+k', function(e) {
            e.preventDefault();
            const searchModal = document.getElementById('global-search-modal') || document.getElementById('searchModal');
            if (searchModal) {
                searchModal.classList.remove('hidden');
                searchModal.setAttribute('data-modal-open', 'true');
                const searchInput = searchModal.querySelector('input[type="text"], input[type="search"]');
                if (searchInput) {
                    setTimeout(() => searchInput.focus(), 100);
                }
            } else {
                // 触发自定义搜索事件
                document.dispatchEvent(new CustomEvent('global-search'));
            }
        }, { description: '全局搜索' });

        // Ctrl+E: 编辑个人资料
        registerShortcut('ctrl+e', function(e) {
            e.preventDefault();
            const profileLink = document.querySelector('a[href*="profile"], a[href*="edit_profile"]');
            if (profileLink) {
                window.location.href = profileLink.href;
            } else {
                document.dispatchEvent(new CustomEvent('edit-profile'));
            }
        }, { description: '编辑个人资料' });

        // Ctrl+N: 新建策略
        registerShortcut('ctrl+n', function(e) {
            e.preventDefault();
            const newStrategyLink = document.querySelector('a[href*="create"], a[href*="new"]');
            if (newStrategyLink) {
                window.location.href = newStrategyLink.href;
            } else {
                document.dispatchEvent(new CustomEvent('new-strategy'));
            }
        }, { description: '新建策略' });

        // Ctrl+?: 显示快捷键帮助
        registerShortcut('ctrl+?', function(e) {
            e.preventDefault();
            showShortcutMenu();
        }, { description: '显示快捷键帮助' });
    }

    // ============================================
    // 5. 全局搜索功能
    // ============================================

    let searchDebounceTimer = null;

    /**
     * 创建全局搜索模态框
     */
    function createSearchModal() {
        const modal = document.createElement('div');
        modal.id = 'global-search-modal';
        modal.className = 'fixed inset-0 bg-black/50 z-[9997] hidden items-center justify-center';
        modal.innerHTML = `
            <div class="bg-white rounded-xl shadow-2xl w-full max-w-2xl mx-4 overflow-hidden" onclick="event.stopPropagation()">
                <div class="p-4 border-b">
                    <div class="flex items-center bg-gray-50 rounded-lg px-4 py-3">
                        <i class="fa fa-search text-gray-400 mr-3"></i>
                        <input type="text" 
                               id="global-search-input"
                               class="flex-1 bg-transparent outline-none text-gray-700 placeholder-gray-400"
                               placeholder="搜索股票、策略、功能..."
                               autocomplete="off">
                        <kbd class="hidden md:inline px-2 py-1 bg-gray-200 rounded text-xs text-gray-500">ESC</kbd>
                    </div>
                </div>
                <div id="search-results" class="max-h-96 overflow-y-auto p-2">
                    <div class="text-center text-gray-400 py-8">
                        <i class="fa fa-search text-4xl mb-3"></i>
                        <p>输入关键词开始搜索</p>
                    </div>
                </div>
                <div class="p-3 border-t bg-gray-50 text-xs text-gray-400 flex justify-between">
                    <span><kbd class="px-1 bg-gray-200 rounded">↑↓</kbd> 导航</span>
                    <span><kbd class="px-1 bg-gray-200 rounded">Enter</kbd> 选择</span>
                    <span><kbd class="px-1 bg-gray-200 rounded">ESC</kbd> 关闭</span>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // 事件绑定
        const searchInput = modal.querySelector('#global-search-input');
        const resultsContainer = modal.querySelector('#search-results');

        // 点击背景关闭
        modal.addEventListener('click', () => {
            modal.classList.add('hidden');
            modal.removeAttribute('data-modal-open');
        });

        // 搜索输入
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchDebounceTimer);
            const query = e.target.value.trim();
            
            if (!query) {
                resultsContainer.innerHTML = `
                    <div class="text-center text-gray-400 py-8">
                        <i class="fa fa-search text-4xl mb-3"></i>
                        <p>输入关键词开始搜索</p>
                    </div>
                `;
                return;
            }

            searchDebounceTimer = setTimeout(() => performSearch(query), 300);
        });

        // 键盘导航
        searchInput.addEventListener('keydown', (e) => {
            const items = resultsContainer.querySelectorAll('.search-result-item:not(.hidden)');
            const activeItem = resultsContainer.querySelector('.search-result-item.active');
            
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                const currentIndex = activeItem ? Array.from(items).indexOf(activeItem) : -1;
                if (currentIndex < items.length - 1) {
                    items.forEach(i => i.classList.remove('active'));
                    items[currentIndex + 1].classList.add('active');
                    items[currentIndex + 1].scrollIntoView({ block: 'nearest' });
                }
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                const currentIndex = activeItem ? Array.from(items).indexOf(activeItem) : 0;
                if (currentIndex > 0) {
                    items.forEach(i => i.classList.remove('active'));
                    items[currentIndex - 1].classList.add('active');
                    items[currentIndex - 1].scrollIntoView({ block: 'nearest' });
                }
            } else if (e.key === 'Enter' && activeItem) {
                e.preventDefault();
                activeItem.click();
            }
        });

        return modal;
    }

    /**
     * 执行搜索
     */
    async function performSearch(query) {
        const resultsContainer = document.getElementById('search-results');
        if (!resultsContainer) return;

        resultsContainer.innerHTML = `
            <div class="text-center text-gray-400 py-8">
                <i class="fa fa-spinner fa-spin text-2xl mb-3"></i>
                <p>搜索中...</p>
            </div>
        `;

        try {
            // 搜索结果数据（可扩展为API调用）
            const results = await searchIndex(query);
            
            if (results.length === 0) {
                resultsContainer.innerHTML = `
                    <div class="text-center text-gray-400 py-8">
                        <i class="fa fa-search text-4xl mb-3"></i>
                        <p>未找到相关结果</p>
                        <p class="text-sm mt-1">尝试其他关键词</p>
                    </div>
                `;
                return;
            }

            resultsContainer.innerHTML = results.map((r, i) => `
                <a href="${r.url}" 
                   class="search-result-item flex items-center p-3 rounded-lg hover:bg-gray-50 cursor-pointer ${i === 0 ? 'active bg-gray-50' : ''}"
                   data-index="${i}">
                    <div class="w-10 h-10 rounded-full bg-${r.categoryColor || 'primary'}/10 flex items-center justify-center mr-3">
                        <i class="fa fa-${r.categoryIcon || 'file'} text-${r.categoryColor || 'primary'}"></i>
                    </div>
                    <div class="flex-1">
                        <p class="font-medium text-gray-700">${highlightMatch(escapeHTML(r.title), query)}</p>
                        <p class="text-sm text-gray-400">${escapeHTML(r.subtitle || r.category)}</p>
                    </div>
                    <i class="fa fa-chevron-right text-gray-300"></i>
                </a>
            `).join('');

            // 绑定点击事件
            resultsContainer.querySelectorAll('.search-result-item').forEach(item => {
                item.addEventListener('click', () => {
                    const modal = document.getElementById('global-search-modal');
                    if (modal) {
                        modal.classList.add('hidden');
                        modal.removeAttribute('data-modal-open');
                    }
                });
            });

        } catch (error) {
            resultsContainer.innerHTML = `
                <div class="text-center text-red-400 py-8">
                    <i class="fa fa-exclamation-triangle text-4xl mb-3"></i>
                    <p>搜索失败，请重试</p>
                </div>
            `;
        }
    }

    /**
     * 搜索索引（调用后端API）
     */
    async function searchIndex(query) {
        try {
            const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            if (data.success && data.results && data.results.length > 0) {
                return data.results;
            }
        } catch (e) {
            console.warn('搜索API调用失败，使用本地回退:', e);
        }

        // 本地回退搜索
        const searchData = [
            { title: '回测系统', url: '/backtest', category: '策略回测', categoryIcon: 'refresh', categoryColor: 'green' },
            { title: '新建策略', url: '/backtest/strategies', category: '策略模板', categoryIcon: 'cube', categoryColor: 'blue' },
            { title: '我的策略', url: '/backtest/history', category: '回测历史', categoryIcon: 'history', categoryColor: 'purple' },
            { title: '投资组合', url: '/portfolio', category: '投资组合', categoryIcon: 'briefcase', categoryColor: 'orange' },
            { title: '市场数据分析', url: '/data', category: '数据中心', categoryIcon: 'database', categoryColor: 'cyan' },
            { title: '技术指标', url: '/analysis', category: '数据分析', categoryIcon: 'bar-chart', categoryColor: 'indigo' },
            { title: 'Black-Scholes模型', url: '/models/black-scholes', category: '金融模型', categoryIcon: 'calculator', categoryColor: 'pink' },
            { title: '风险价值(VaR)', url: '/models/var', category: '金融模型', categoryIcon: 'shield', categoryColor: 'red' },
            { title: '个人资料', url: '/auth/profile', category: '账户', categoryIcon: 'user', categoryColor: 'gray' },
            { title: '通知中心', url: '/notifications', category: '账户', categoryIcon: 'bell', categoryColor: 'yellow' },
            { title: '功能介绍', url: '/features', category: '关于平台', categoryIcon: 'star', categoryColor: 'orange' },
            { title: '联系我们', url: '/contact', category: '关于平台', categoryIcon: 'envelope', categoryColor: 'blue' },
            { title: '关于我们', url: '/about', category: '关于平台', categoryIcon: 'info-circle', categoryColor: 'indigo' },
            { title: '课程中心', url: '/courses', category: '课程实践', categoryIcon: 'graduation-cap', categoryColor: 'yellow' },
            { title: '策略社区', url: '/community', category: '策略社区', categoryIcon: 'users', categoryColor: 'green' },
            { title: 'AI助手', url: '/ai-assistant', category: 'AI服务', categoryIcon: 'android', categoryColor: 'blue' },
        ];

        const q = query.toLowerCase();
        return searchData.filter(item => 
            item.title.toLowerCase().includes(q) || 
            item.category.toLowerCase().includes(q)
        ).slice(0, 8);
    }

    /**
     * 高亮匹配文本
     */
    function highlightMatch(text, query) {
        const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
        return text.replace(regex, '<mark class="bg-yellow-200 rounded px-0.5">$1</mark>');
    }

    // ============================================
    // 6. 确认对话框
    // ============================================

    /**
     * 显示确认对话框
     * @param {Object} options - 配置选项
     * @returns {Promise<boolean>}
     */
    function showConfirm(options = {}) {
        const {
            title = '确认',
            message = '确定要执行此操作吗？',
            confirmText = '确定',
            cancelText = '取消',
            confirmClass = 'bg-red-500 hover:bg-red-600',
            icon = 'fa-exclamation-triangle',
            iconColor = 'text-yellow-500'
        } = options;

        return new Promise((resolve) => {
            const overlay = document.createElement('div');
            overlay.className = 'fixed inset-0 bg-black/50 flex items-center justify-center z-[9999]';
            overlay.innerHTML = `
                <div class="bg-white rounded-xl shadow-2xl w-full max-w-md mx-4 overflow-hidden transform transition-all">
                    <div class="p-6">
                        <div class="flex items-start">
                            <div class="flex-shrink-0 w-12 h-12 rounded-full bg-yellow-100 flex items-center justify-center mr-4">
                                <i class="fa ${icon} ${iconColor} text-xl"></i>
                            </div>
                            <div class="flex-1">
                                <h3 class="text-lg font-semibold text-gray-900">${title}</h3>
                                <p class="mt-2 text-gray-600">${message}</p>
                            </div>
                        </div>
                    </div>
                    <div class="bg-gray-50 px-6 py-4 flex justify-end gap-3">
                        <button class="cancel-btn px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors">
                            ${cancelText}
                        </button>
                        <button class="confirm-btn px-4 py-2 ${confirmClass} text-white rounded-lg transition-colors">
                            ${confirmText}
                        </button>
                    </div>
                </div>
            `;

            document.body.appendChild(overlay);

            const confirmBtn = overlay.querySelector('.confirm-btn');
            const cancelBtn = overlay.querySelector('.cancel-btn');

            const cleanup = (result) => {
                overlay.style.opacity = '0';
                overlay.style.transition = 'opacity 0.2s';
                setTimeout(() => {
                    overlay.remove();
                    resolve(result);
                }, 200);
            };

            confirmBtn.addEventListener('click', () => cleanup(true));
            cancelBtn.addEventListener('click', () => cleanup(false));
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) cleanup(false);
            });
        });
    }

    // ============================================
    // 7. 主题管理（暗黑模式支持）
    // ============================================

    let themeInitialized = false;

    /**
     * 主题初始化函数
     */
    function initTheme() {
        // 防止重复初始化
        if (themeInitialized) return;
        themeInitialized = true;

        const html = document.documentElement;
        const savedTheme = localStorage.getItem('theme');
        
        // 尝试获取用户主题偏好（从页面注入的变量）
        const userThemePreference = window.__userThemePreference || 'system';
        
        // 优先级：用户设置 > localStorage > 系统偏好
        if (userThemePreference && userThemePreference !== 'system') {
            // 使用用户设置
            html.setAttribute('data-theme', userThemePreference);
            localStorage.setItem('theme', userThemePreference);
        } else if (savedTheme) {
            // 使用 localStorage
            html.setAttribute('data-theme', savedTheme);
        } else {
            // 检测系统偏好
            if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
                html.setAttribute('data-theme', 'dark');
            } else {
                html.setAttribute('data-theme', 'light');
            }
        }
        
        // 更新图标
        updateThemeIcon();
    }

    /**
     * 更新主题图标
     */
    function updateThemeIcon() {
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
        const themeIcon = document.getElementById('theme-icon');
        const mobileThemeIcon = document.getElementById('mobile-theme-icon');
        
        const iconClass = currentTheme === 'dark' ? 'fa-sun-o' : 'fa-moon-o';
        const mobileIconClass = currentTheme === 'dark' ? 'fa-sun-o' : 'fa-moon-o';
        
        if (themeIcon) {
            themeIcon.classList.remove('fa-sun-o', 'fa-moon-o');
            themeIcon.classList.add(iconClass);
        }
        
        if (mobileThemeIcon) {
            mobileThemeIcon.classList.remove('fa-sun-o', 'fa-moon-o');
            mobileThemeIcon.classList.add(mobileIconClass);
        }
        
        // 更新 body class
        document.body.classList.toggle('dark-mode', currentTheme === 'dark');
        
        // 更新 html class
        document.documentElement.classList.toggle('dark', currentTheme === 'dark');
    }

    /**
     * 切换主题
     */
    function toggleTheme() {
        const html = document.documentElement;
        const currentTheme = html.getAttribute('data-theme') || 'light';
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        html.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        
        // 同步到服务器
        syncThemeToServer(newTheme);
        
        updateThemeIcon();
        
        // 触发图表主题更新
        if (typeof updateChartThemes === 'function') {
            updateChartThemes(newTheme);
        }
    }

    /**
     * 同步主题到服务器
     */
    async function syncThemeToServer(theme) {
        try {
            await fetch('/api/user/theme', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ theme: theme })
            });
        } catch (error) {
            console.log('主题同步失败:', error);
        }
    }

    /**
     * 监听系统主题变化
     */
    function initSystemThemeListener() {
        if (!window.matchMedia) return;
        
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
            const savedTheme = localStorage.getItem('theme');
            const userThemePreference = window.__userThemePreference || 'system';
            
            // 只有在用户设置为"跟随系统"时才响应系统变化
            if (!savedTheme && userThemePreference !== 'system') {
                return;
            }
            
            if (e.matches) {
                document.documentElement.setAttribute('data-theme', 'dark');
            } else {
                document.documentElement.setAttribute('data-theme', 'light');
            }
            updateThemeIcon();
        });
    }

    // 将主题函数暴露到全局
    window.toggleTheme = toggleTheme;
    window.updateThemeIcon = updateThemeIcon;

    // ============================================
    // 初始化
    // ============================================

    function init() {
        initDefaultShortcuts();
        createSearchModal();
        initTheme();
        initSystemThemeListener();
        
        // 监听全局搜索事件
        document.addEventListener('global-search', () => {
            const modal = document.getElementById('global-search-modal');
            if (modal) {
                modal.classList.remove('hidden');
                const searchInput = modal.querySelector('input');
                if (searchInput) {
                    setTimeout(() => searchInput.focus(), 100);
                }
            }
        });
    }

    // DOM加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // ============================================
    // 导出全局API
    // ============================================

    window.Utils = {
        // 加载状态
        showLoading,
        hideLoading,
        withLoading,
        
        // 表单验证
        addFormValidation,
        validationRules,
        
        // Toast通知
        showToast,
        toast,
        
        // 快捷键
        registerShortcut,
        showShortcutMenu,
        
        // 全局搜索
        showGlobalSearch: () => document.dispatchEvent(new CustomEvent('global-search')),
        
        // 确认对话框
        showConfirm,
        
        // 主题管理
        toggleTheme,
        updateThemeIcon,
        initTheme
    };

    // 保持向后兼容
    window.showToast = showToast;
    window.showLoading = showLoading;
    window.hideLoading = hideLoading;
    window.addFormValidation = addFormValidation;
    window.toggleTheme = toggleTheme;
    window.updateThemeIcon = updateThemeIcon;
    window.showConfirm = showConfirm;

})();
