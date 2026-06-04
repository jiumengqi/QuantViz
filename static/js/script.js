// 股票分析与量化投资平台前端脚本
// 模块化组织结构

// 全局变量
const QuantPlatform = {
    // 初始化函数
    init: function() {
        this.setupEventListeners();
        this.initializeComponents();
        this.loadTheme();
    },
    
    // 设置事件监听器
    setupEventListeners: function() {
        // 导航栏滚动效果
        window.addEventListener('scroll', this.handleNavbarScroll);
        
        // 平滑滚动
        this.setupSmoothScroll();
        
        // 卡片悬停效果
        this.setupCardHoverEffects();
        
        // 按钮点击效果
        this.setupButtonEffects();
        
        // 输入框焦点效果
        this.setupInputEffects();
        
        // 响应式导航菜单
        this.setupResponsiveNavigation();
        
        // 移动端下拉菜单
        this.setupMobileDropdowns();
        
        // 深色模式切换
        this.setupThemeToggle();
        
        // 模型卡片展开/折叠功能
        this.setupModelCards();
        
        // 回测系统开始按钮
        this.setupBacktestSystem();
        
        // 课程页面交互功能
        this.setupCoursePage();
        
        // 联系我们表单提交功能
        this.setupContactForm();
        
        // 数据分析页面功能
        this.setupAnalysisPage();
        
        // 投资组合页面功能
        this.setupPortfolioPage();
        
        // 课程实践页面功能
        this.setupCoursesPage();
    },
    
    // 初始化组件
    initializeComponents: function() {
        // 页面加载动画
        this.setupPageAnimations();
        
        // 学习进度条动画
        this.setupProgressBars();
        
        // 首页功能模块点击处理
        this.setupHomePageInteractions();
    },
    
    // 首页功能模块点击处理
    setupHomePageInteractions: function() {
        // 英雄区域按钮点击
        const heroButtons = document.querySelectorAll('.hero-section button, .hero-section a.btn');
        heroButtons.forEach(button => {
            button.addEventListener('click', function() {
                console.log('点击英雄区域按钮:', this.textContent.trim());
                // 这里可以添加额外的逻辑，比如记录用户点击行为
            });
        });
        
        // 功能模块卡片点击
        const featureCards = document.querySelectorAll('.feature-card, .card-hover');
        featureCards.forEach(card => {
            card.addEventListener('click', function(e) {
                // 避免点击卡片内部链接时触发卡片点击事件
                if (!e.target.closest('a')) {
                    console.log('点击功能卡片');
                    // 这里可以添加卡片点击逻辑
                }
            });
        });
        
        // 功能模块链接点击
        const featureLinks = document.querySelectorAll('.feature-card a, .card-hover a');
        featureLinks.forEach(link => {
            link.addEventListener('click', function() {
                console.log('点击功能模块链接:', this.getAttribute('href'));
                // 这里可以添加额外的逻辑，比如记录用户点击行为
            });
        });
    },
    
    // 加载主题
    loadTheme: function() {
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark') {
            this.updateChartThemes('dark');
        }
    },
    
    // 图表主题更新函数
    updateChartThemes: function(theme) {
        const isDarkMode = theme === 'dark';
        
        // 更新全局Chart.js默认配置
        if (typeof Chart !== 'undefined') {
            Chart.defaults.color = isDarkMode ? '#d1d5db' : '#4E5969';
            Chart.defaults.borderColor = isDarkMode ? '#4b5563' : '#C9CDD4';
            
            // 更新所有已创建的图表
            const charts = Chart.getChart('all');
            if (charts) {
                charts.forEach(chart => {
                    // 更新图表的颜色配置
                    chart.options.scales.x.grid.color = isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.05)';
                    chart.options.scales.y.grid.color = isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.05)';
                    
                    // 重新渲染图表
                    chart.update();
                });
            }
        }
    },
    
    // 导航栏滚动效果
    handleNavbarScroll: function() {
        const navbar = document.getElementById('navbar');
        if (navbar) {
            if (window.scrollY > 50) {
                navbar.classList.add('py-2', 'shadow-md');
                navbar.classList.remove('py-3', 'shadow-sm');
            } else {
                navbar.classList.add('py-3', 'shadow-sm');
                navbar.classList.remove('py-2', 'shadow-md');
            }
        }
    },
    
    // 平滑滚动
    setupSmoothScroll: function() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function(e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    },
    
    // 卡片悬停效果
    setupCardHoverEffects: function() {
        const cards = document.querySelectorAll('.card, .feature-card');
        cards.forEach(card => {
            card.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-5px)';
                this.style.boxShadow = '0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)';
            });
            
            card.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0)';
                this.style.boxShadow = '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)';
            });
        });
    },
    
    // 按钮点击效果
    setupButtonEffects: function() {
        const buttons = document.querySelectorAll('button, .btn');
        buttons.forEach(button => {
            button.addEventListener('mousedown', function() {
                this.style.transform = 'scale(0.95)';
            });
            
            button.addEventListener('mouseup', function() {
                this.style.transform = 'scale(1)';
            });
            
            button.addEventListener('mouseleave', function() {
                this.style.transform = 'scale(1)';
            });
        });
    },
    
    // 输入框焦点效果
    setupInputEffects: function() {
        const inputs = document.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('focus', function() {
                this.style.transform = 'scale(1.01)';
            });
            
            input.addEventListener('blur', function() {
                this.style.transform = 'scale(1)';
            });
        });
    },
    
    // 数字动画效果
    animateValue: function(element, start, end, duration) {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            const value = Math.floor(progress * (end - start) + start);
            element.textContent = value;
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    },
    
    // 页面加载动画
    setupPageAnimations: function() {
        const fadeElements = document.querySelectorAll('.fade-in');
        fadeElements.forEach((element, index) => {
            element.style.opacity = '0';
            element.style.transform = 'translateY(20px)';
            element.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
            
            setTimeout(() => {
                element.style.opacity = '1';
                element.style.transform = 'translateY(0)';
            }, 100 * index);
        });
        
        // 启动数字动画
        const valueElements = document.querySelectorAll('.animate-value');
        valueElements.forEach(element => {
            const target = parseInt(element.getAttribute('data-target'));
            if (target) {
                this.animateValue(element, 0, target, 2000);
            }
        });
    },
    
    // 响应式导航菜单
    setupResponsiveNavigation: function() {
        const menuToggle = document.getElementById('menu-toggle');
        const mobileMenu = document.getElementById('mobile-menu');
        
        if (menuToggle && mobileMenu) {
            menuToggle.addEventListener('click', function() {
                mobileMenu.classList.toggle('hidden');
                const icon = menuToggle.querySelector('i');
                if (mobileMenu.classList.contains('hidden')) {
                    icon.classList.remove('fa-times');
                    icon.classList.add('fa-bars');
                    icon.style.transform = 'rotate(0deg)';
                } else {
                    icon.classList.remove('fa-bars');
                    icon.classList.add('fa-times');
                    icon.style.transform = 'rotate(180deg)';
                }
            });
        }
    },
    
    // 移动端下拉菜单
    setupMobileDropdowns: function() {
        const mobileDropdowns = document.querySelectorAll('.mobile-dropdown');
        mobileDropdowns.forEach(dropdown => {
            const button = dropdown.querySelector('button');
            const content = dropdown.querySelector('div');
            const icon = button.querySelector('i');
            
            if (button && content && icon) {
                button.addEventListener('click', function() {
                    content.classList.toggle('hidden');
                    if (content.classList.contains('hidden')) {
                        icon.style.transform = 'rotate(0deg)';
                    } else {
                        icon.style.transform = 'rotate(180deg)';
                    }
                });
            }
        });
    },
    
    // 深色模式切换
    setupThemeToggle: function() {
        const themeToggle = document.getElementById('theme-toggle');
        const mobileThemeToggle = document.getElementById('mobile-theme-toggle');
        const themeIcon = document.getElementById('theme-icon');
        const htmlElement = document.documentElement;
        
        // 检查本地存储中的主题偏好
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {
            htmlElement.setAttribute('data-theme', savedTheme);
            if (savedTheme === 'dark') {
                if (themeIcon) {
                    themeIcon.classList.remove('fa-moon-o');
                    themeIcon.classList.add('fa-sun-o');
                }
                document.body.classList.add('dark-mode');
            }
        }
        
        // 切换主题的函数
        function toggleTheme() {
            const currentTheme = htmlElement.getAttribute('data-theme') || 'light';
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            
            htmlElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            
            if (themeIcon) {
                if (newTheme === 'dark') {
                    themeIcon.classList.remove('fa-moon-o');
                    themeIcon.classList.add('fa-sun-o');
                } else {
                    themeIcon.classList.remove('fa-sun-o');
                    themeIcon.classList.add('fa-moon-o');
                }
            }
            
            document.body.classList.toggle('dark-mode', newTheme === 'dark');
            
            // 触发图表主题更新
            if (typeof updateChartThemes === 'function') {
                updateChartThemes(newTheme);
            }
        }
        
        // 添加事件监听器
        if (themeToggle) {
            themeToggle.addEventListener('click', toggleTheme);
        }
        if (mobileThemeToggle) {
            mobileThemeToggle.addEventListener('click', toggleTheme);
        }
    },
    
    // 模型卡片展开/折叠功能
    setupModelCards: function() {
        const modelCardHeaders = document.querySelectorAll('.model-card-header');
        modelCardHeaders.forEach(header => {
            header.addEventListener('click', function() {
                const targetId = this.getAttribute('data-target');
                const content = document.getElementById(targetId);
                const icon = this.querySelector('i.fa-chevron-down');
                
                if (content) {
                    content.classList.toggle('hidden');
                    if (icon) {
                        if (content.classList.contains('hidden')) {
                            icon.style.transform = 'rotate(0deg)';
                        } else {
                            icon.style.transform = 'rotate(180deg)';
                        }
                    }
                }
            });
        });
        
        // 模型卡片内部链接点击功能
        const modelLinks = document.querySelectorAll('.model-card-content a');
        modelLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                console.log('点击模型链接:', this.getAttribute('href'));
                // 这里可以添加额外的逻辑，比如记录用户点击行为
            });
        });
    },
    
    // 回测系统开始按钮点击事件处理
    setupBacktestSystem: function() {
        const startBacktestBtn = document.getElementById('start-backtest-btn');
        if (startBacktestBtn) {
            startBacktestBtn.addEventListener('click', function() {
                // 获取回测参数
                const strategySelect = document.querySelector('select');
                const stockCodeInput = document.querySelector('input[value="600036.SH"]');
                const dateInputs = document.querySelectorAll('input[type="date"]');
                const initialCapitalInput = document.querySelector('input[type="number"][value="1000000"]');
                const shortWindowInput = document.querySelector('input[type="number"][value="10"]');
                const longWindowInput = document.querySelector('input[type="number"][value="30"]');
                
                // 构建回测参数对象
                const backtestParams = {
                    strategy: strategySelect ? strategySelect.value : '移动平均线交叉策略',
                    stock_code: stockCodeInput ? stockCodeInput.value : '600036.SH',
                    start_date: dateInputs[0] ? dateInputs[0].value : '2020-01-01',
                    end_date: dateInputs[1] ? dateInputs[1].value : '2023-12-31',
                    initial_capital: initialCapitalInput ? parseFloat(initialCapitalInput.value) : 1000000,
                    // 根据策略类型添加相应参数
                    short_window: shortWindowInput ? parseInt(shortWindowInput.value) : 10,
                    long_window: longWindowInput ? parseInt(longWindowInput.value) : 30,
                    rsi_period: 14,
                    rsi_overbought: 70,
                    rsi_oversold: 30
                };
                
                // 显示加载状态
                startBacktestBtn.disabled = true;
                startBacktestBtn.innerHTML = '<i class="fa fa-spinner fa-spin mr-2"></i> 回测中...';
                
                // 模拟API请求
                setTimeout(() => {
                    // 恢复按钮状态
                    startBacktestBtn.disabled = false;
                    startBacktestBtn.innerHTML = '<i class="fa fa-play mr-2"></i> 开始回测';
                    
                    // 显示回测结果
                    alert('回测完成！\n\n总收益率: 24.6%\n年化收益率: 7.8%\n夏普比率: 1.87\n最大回撤: -12.3%\n胜率: 62.5%\n交易次数: 24');
                    
                    // 更新回测结果展示
                    this.updateBacktestResults({
                        total_return: 24.6,
                        annual_return: 7.8,
                        sharpe_ratio: 1.87,
                        max_drawdown: -12.3,
                        win_rate: 62.5,
                        trade_count: 24
                    });
                    
                    // 这里可以添加实际的API调用逻辑
                    /*
                    fetch('/backtest/run', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(backtestParams)
                    })
                    .then(response => response.json())
                    .then(data => {
                        // 处理回测结果
                        console.log('回测结果:', data);
                        // 更新页面显示
                        this.updateBacktestResults(data);
                    })
                    .catch(error => {
                        console.error('回测失败:', error);
                        alert('回测失败，请稍后重试');
                    })
                    .finally(() => {
                        // 恢复按钮状态
                        startBacktestBtn.disabled = false;
                        startBacktestBtn.innerHTML = '<i class="fa fa-play mr-2"></i> 开始回测';
                    });
                    */
                }, 2000);
            });
        }
    },
    
    // 更新回测结果展示
    updateBacktestResults: function(results) {
        // 更新总收益率
        const totalReturnElement = document.getElementById('total-return-value');
        if (totalReturnElement) {
            totalReturnElement.textContent = results.total_return + '%';
        }
        
        // 更新年化收益率
        const annualReturnElement = document.getElementById('annual-return-value');
        if (annualReturnElement) {
            annualReturnElement.textContent = results.annual_return + '%';
        }
        
        // 更新夏普比率
        const sharpeRatioElement = document.getElementById('sharpe-ratio-value');
        if (sharpeRatioElement) {
            sharpeRatioElement.textContent = results.sharpe_ratio;
        }
        
        // 更新最大回撤
        const maxDrawdownElement = document.getElementById('max-drawdown-value');
        if (maxDrawdownElement) {
            maxDrawdownElement.textContent = results.max_drawdown + '%';
        }
        
        // 更新胜率
        const winRateElement = document.getElementById('win-rate-value');
        if (winRateElement) {
            winRateElement.textContent = results.win_rate + '%';
        }
        
        // 更新交易次数
        const tradeCountElement = document.getElementById('trade-count-value');
        if (tradeCountElement) {
            tradeCountElement.textContent = results.trade_count;
        }
        
        // 更新回测结果图表
        this.updateBacktestChart(results);
    },
    
    // 更新回测结果图表
    updateBacktestChart: function(results) {
        const ctx = document.getElementById('backtestChart');
        if (ctx) {
            // 销毁旧图表
            if (window.backtestChart) {
                window.backtestChart.destroy();
            }
            
            // 创建新图表
            window.backtestChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: ['2020-01', '2020-06', '2020-12', '2021-06', '2021-12', '2022-06', '2022-12', '2023-06', '2023-12'],
                    datasets: [
                        {
                            label: '策略收益',
                            data: [0, 5.2, 12.5, 18.7, 22.3, 19.8, 15.6, 20.1, 24.6],
                            borderColor: 'rgba(59, 130, 246, 1)',
                            backgroundColor: 'rgba(59, 130, 246, 0.1)',
                            borderWidth: 2,
                            tension: 0.2,
                            fill: true
                        },
                        {
                            label: '基准收益',
                            data: [0, 3.1, 8.7, 12.4, 15.2, 14.5, 12.1, 14.8, 16.3],
                            borderColor: 'rgba(156, 163, 175, 1)',
                            backgroundColor: 'rgba(156, 163, 175, 0.1)',
                            borderWidth: 2,
                            tension: 0.2,
                            fill: true
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                        },
                        tooltip: {
                            mode: 'index',
                            intersect: false,
                        }
                    },
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: '日期'
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: '累计收益率 (%)'
                            },
                            ticks: {
                                callback: function(value) {
                                    return value + '%';
                                }
                            }
                        }
                    }
                }
            });
        }
    },
    
    // 课程页面交互功能
    setupCoursePage: function() {
        // 分类切换功能
        const categoryPills = document.querySelectorAll('.category-pill');
        categoryPills.forEach(pill => {
            pill.addEventListener('click', function() {
                // 移除所有分类的active状态
                categoryPills.forEach(p => {
                    p.classList.remove('active', 'bg-primary', 'text-white');
                    p.classList.add('bg-white', 'text-gray-700');
                });
                
                // 添加当前分类的active状态
                this.classList.add('active', 'bg-primary', 'text-white');
                this.classList.remove('bg-white', 'text-gray-700');
                
                // 这里可以添加分类筛选逻辑
                const category = this.textContent.trim();
                console.log('切换到分类:', category);
            });
        });
        
        // 搜索功能
        const searchInput = document.getElementById('courseSearch');
        const searchBtn = document.getElementById('searchBtn');
        const searchResults = document.getElementById('searchResults');
        
        if (searchInput && searchBtn) {
            function performSearch() {
                const query = searchInput.value.trim();
                if (query) {
                    console.log('搜索课程:', query);
                    // 这里可以添加实际的搜索逻辑
                    if (searchResults) {
                        searchResults.innerHTML = `<div class="text-sm text-gray-500 mb-2">搜索结果: "${query}"</div>`;
                        searchResults.classList.remove('hidden');
                    }
                } else {
                    if (searchResults) {
                        searchResults.classList.add('hidden');
                    }
                }
            }
            
            searchBtn.addEventListener('click', performSearch);
            
            searchInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    performSearch();
                }
            });
            
            searchInput.addEventListener('input', function() {
                if (!this.value.trim() && searchResults) {
                    searchResults.classList.add('hidden');
                }
            });
        }
        
        // 排序功能
        const sortOptions = document.getElementById('sortOptions');
        if (sortOptions) {
            sortOptions.addEventListener('change', function() {
                const sortValue = this.value;
                console.log('排序方式:', sortValue);
                // 这里可以添加实际的排序逻辑
            });
        }
        
        // 筛选按钮
        const filterBtn = document.getElementById('filterBtn');
        if (filterBtn) {
            filterBtn.addEventListener('click', function() {
                console.log('打开筛选选项');
                // 这里可以添加打开筛选面板的逻辑
            });
        }
        
        // 清除筛选
        const clearFilters = document.getElementById('clearFilters');
        if (clearFilters) {
            clearFilters.addEventListener('click', function() {
                console.log('清除所有筛选');
                // 这里可以添加清除筛选的逻辑
            });
        }
        
        // 收藏按钮
        const favoriteBtns = document.querySelectorAll('.favorite-btn');
        favoriteBtns.forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                const icon = this.querySelector('i');
                if (icon) {
                    if (icon.classList.contains('fa-heart-o')) {
                        icon.classList.remove('fa-heart-o');
                        icon.classList.add('fa-heart');
                        this.classList.remove('text-gray-500');
                        this.classList.add('text-red-500');
                        console.log('收藏课程');
                    } else {
                        icon.classList.remove('fa-heart');
                        icon.classList.add('fa-heart-o');
                        this.classList.remove('text-red-500');
                        this.classList.add('text-gray-500');
                        console.log('取消收藏');
                    }
                }
            });
        });
        
        // 分享按钮
        const shareBtns = document.querySelectorAll('.share-btn');
        shareBtns.forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                console.log('分享课程');
                // 这里可以添加分享逻辑
                if (navigator.share) {
                    navigator.share({
                        title: '股票分析与量化投资平台',
                        text: '推荐一门好课程',
                        url: window.location.href
                    });
                } else {
                    //  fallback for browsers that don't support Web Share API
                    const url = window.location.href;
                    navigator.clipboard.writeText(url).then(() => {
                        alert('链接已复制到剪贴板');
                    });
                }
            });
        });
        
        // 立即报名按钮
        const enrollBtns = document.querySelectorAll('button');
        enrollBtns.forEach(btn => {
            if (btn.textContent.includes('立即报名')) {
                btn.addEventListener('click', function() {
                    console.log('立即报名');
                    // 这里可以添加报名逻辑
                    alert('报名成功！');
                });
            }
        });
        
        // 预览课程按钮
        const previewBtns = document.querySelectorAll('button');
        previewBtns.forEach(btn => {
            if (btn.querySelector('i.fa-play-circle')) {
                btn.addEventListener('click', function() {
                    console.log('预览课程');
                    // 这里可以添加预览逻辑
                    alert('预览课程功能');
                });
            }
        });
    },
    
    // 学习进度条动画
    setupProgressBars: function() {
        const progressBars = document.querySelectorAll('.progress-bar');
        progressBars.forEach(bar => {
            const width = bar.style.width;
            bar.style.width = '0%';
            setTimeout(() => {
                bar.style.width = width;
            }, 500);
        });
    },
    
    // 联系我们表单提交功能
    setupContactForm: function() {
        // 支持两种表单ID格式
        const contactForm = document.getElementById('contactForm') || document.getElementById('contact-form');
        if (contactForm) {
            contactForm.addEventListener('submit', function(e) {
                e.preventDefault();
                
                // 获取表单元素
                const nameInput = document.getElementById('name');
                const emailInput = document.getElementById('email');
                const messageInput = document.getElementById('message');
                const submitBtn = this.querySelector('button[type="submit"]');
                const formSuccess = document.getElementById('formSuccess') || document.getElementById('success-message');
                
                // 表单验证
                let isValid = true;
                
                // 验证姓名
                if (!nameInput.value.trim()) {
                    isValid = false;
                }
                
                // 验证邮箱
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailRegex.test(emailInput.value.trim())) {
                    isValid = false;
                }
                
                // 验证留言内容
                if (!messageInput.value.trim()) {
                    isValid = false;
                }
                
                if (isValid) {
                    // 显示加载状态
                    if (submitBtn) {
                        submitBtn.disabled = true;
                        submitBtn.innerHTML = '<i class="fa fa-spinner fa-spin mr-2"></i> 提交中...';
                    }
                    
                    // 模拟表单提交
                    setTimeout(() => {
                        // 恢复按钮状态
                        if (submitBtn) {
                            submitBtn.disabled = false;
                            submitBtn.innerHTML = '<i class="fa fa-paper-plane mr-2"></i> 发送消息';
                        }
                        
                        // 显示成功消息
                        if (formSuccess) {
                            formSuccess.classList.remove('hidden');
                        }
                        
                        // 重置表单
                        contactForm.reset();
                        
                        // 3秒后隐藏成功消息
                        setTimeout(() => {
                            if (formSuccess) {
                                formSuccess.classList.add('hidden');
                            }
                        }, 3000);
                    }, 1500);
                }
            });
        }
        
        // FAQ 折叠功能
        const faqToggles = document.querySelectorAll('.faq-toggle');
        faqToggles.forEach(toggle => {
            toggle.addEventListener('click', function() {
                const content = this.nextElementSibling;
                const icon = this.querySelector('i');
                
                // 切换当前FAQ的显示状态
                content.classList.toggle('hidden');
                icon.classList.toggle('fa-plus');
                icon.classList.toggle('fa-minus');
                icon.classList.toggle('rotate-45');
            });
        });
        
        // 社交媒体链接点击
        const socialLinks = document.querySelectorAll('.bg-neutral-light a');
        socialLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                console.log('点击社交媒体链接:', this.getAttribute('href'));
                // 这里可以添加额外的逻辑，比如记录用户点击行为
            });
        });
    },
    
    // 数据分析页面功能
    setupAnalysisPage: function() {
        // 开始分析按钮
        const analyzeBtn = document.getElementById('analyzeBtn');
        if (analyzeBtn) {
            analyzeBtn.addEventListener('click', function() {
                // 显示加载状态
                analyzeBtn.disabled = true;
                analyzeBtn.innerHTML = '<i class="fa fa-spinner fa-spin mr-2"></i> 分析中...';
                
                // 模拟分析过程
                setTimeout(() => {
                    // 恢复按钮状态
                    analyzeBtn.disabled = false;
                    analyzeBtn.innerHTML = '<i class="fa fa-bar-chart mr-2"></i> 开始分析';
                    
                    // 显示分析完成消息
                    alert('分析完成！\n\n技术指标已更新，风险收益分析已完成。');
                    
                    // 这里可以添加实际的API调用逻辑
                    /*
                    fetch('/analysis/run', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            stock_code: document.getElementById('stockSelect').value,
                            start_date: document.getElementById('startDate').value,
                            end_date: document.getElementById('endDate').value,
                            indicators: {
                                ma: document.getElementById('indicatorMA').checked,
                                rsi: document.getElementById('indicatorRSI').checked,
                                macd: document.getElementById('indicatorMACD').checked,
                                bb: document.getElementById('indicatorBB').checked,
                                kdj: document.getElementById('indicatorKDJ').checked,
                                atr: document.getElementById('indicatorATR').checked,
                                obv: document.getElementById('indicatorOBV').checked,
                                cci: document.getElementById('indicatorCCI').checked
                            },
                            params: {
                                ma_short: document.getElementById('maShort').value,
                                ma_medium: document.getElementById('maMedium').value,
                                ma_long: document.getElementById('maLong').value,
                                rsi_period: document.getElementById('rsiPeriod').value,
                                rsi_overbought: document.getElementById('rsiOverbought').value,
                                rsi_oversold: document.getElementById('rsiOversold').value,
                                macd_fast: document.getElementById('macdFast').value,
                                macd_slow: document.getElementById('macdSlow').value,
                                macd_signal: document.getElementById('macdSignal').value
                            }
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        // 处理分析结果
                        console.log('分析结果:', data);
                        // 更新页面显示
                    })
                    .catch(error => {
                        console.error('分析失败:', error);
                        alert('分析失败，请稍后重试');
                    })
                    .finally(() => {
                        // 恢复按钮状态
                        analyzeBtn.disabled = false;
                        analyzeBtn.innerHTML = '<i class="fa fa-bar-chart mr-2"></i> 开始分析';
                    });
                    */
                }, 2000);
            });
        }
        
        // 导出分析报告按钮
        const exportBtn = document.getElementById('exportBtn');
        if (exportBtn) {
            exportBtn.addEventListener('click', function() {
                // 显示加载状态
                exportBtn.disabled = true;
                exportBtn.innerHTML = '<i class="fa fa-spinner fa-spin mr-2"></i> 导出中...';
                
                // 模拟导出过程
                setTimeout(() => {
                    // 恢复按钮状态
                    exportBtn.disabled = false;
                    exportBtn.innerHTML = '<i class="fa fa-download mr-2"></i> 导出分析报告';
                    
                    // 显示导出成功消息
                    alert('分析报告导出成功！\n\n报告已保存为PDF格式。');
                }, 1500);
            });
        }
        
        // 周期按钮切换
        const periodBtns = document.querySelectorAll('.period-btn');
        periodBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                // 更新按钮样式
                periodBtns.forEach(b => {
                    b.classList.remove('bg-primary', 'text-white');
                    b.classList.add('bg-gray-100', 'text-gray-600');
                });
                this.classList.remove('bg-gray-100', 'text-gray-600');
                this.classList.add('bg-primary', 'text-white');
                
                // 这里可以添加周期切换逻辑
                const period = this.textContent.trim();
                console.log('切换到周期:', period);
            });
        });
    },
    
    // 投资组合页面功能
    setupPortfolioPage: function() {
        // 创建投资组合按钮
        const createPortfolioBtn = document.querySelector('a[href*="create_portfolio"]');
        if (createPortfolioBtn) {
            createPortfolioBtn.addEventListener('click', function(e) {
                console.log('创建投资组合');
                // 这里可以添加额外的逻辑，比如记录用户点击行为
            });
        }
        
        // 查看详情按钮
        const viewDetailBtns = document.querySelectorAll('a[href*="portfolio_detail"]');
        viewDetailBtns.forEach(btn => {
            btn.addEventListener('click', function(e) {
                console.log('查看投资组合详情:', this.getAttribute('href'));
                // 这里可以添加额外的逻辑，比如记录用户点击行为
            });
        });
        
        // 优化按钮
        const optimizeBtns = document.querySelectorAll('a[href*="optimize_portfolio"]');
        optimizeBtns.forEach(btn => {
            btn.addEventListener('click', function(e) {
                console.log('优化投资组合:', this.getAttribute('href'));
                // 这里可以添加额外的逻辑，比如记录用户点击行为
            });
        });
        
        // 快速操作链接
        const quickActionLinks = document.querySelectorAll('.card-hover');
        quickActionLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                // 避免点击卡片内部链接时触发卡片点击事件
                if (!e.target.closest('a')) {
                    console.log('点击快速操作卡片');
                    // 这里可以添加卡片点击逻辑
                }
            });
        });
        
        // 市场概览卡片点击
        const marketCards = document.querySelectorAll('.card-hover');
        marketCards.forEach(card => {
            card.addEventListener('click', function(e) {
                // 避免点击卡片内部链接时触发卡片点击事件
                if (!e.target.closest('a')) {
                    console.log('点击市场概览卡片');
                    // 这里可以添加市场概览卡片点击逻辑
                }
            });
        });
        
        // 板块表现卡片点击
        const sectorCards = document.querySelectorAll('.border');
        sectorCards.forEach(card => {
            card.addEventListener('click', function() {
                const sectorName = this.querySelector('span').textContent;
                console.log('点击板块:', sectorName);
                // 这里可以添加板块详情查看逻辑
                alert(`查看板块详情: ${sectorName}`);
            });
        });
    },
    
    // 课程实践页面功能
    setupCoursesPage: function() {
        // 课程分类切换
        const categoryLinks = document.querySelectorAll('.category-link');
        categoryLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                console.log('切换课程分类:', this.textContent.trim());
                // 这里可以添加分类切换逻辑
            });
        });
        
        // 课程卡片点击
        const courseCards = document.querySelectorAll('.course-card');
        courseCards.forEach(card => {
            card.addEventListener('click', function(e) {
                // 避免点击卡片内部链接时触发卡片点击事件
                if (!e.target.closest('a') && !e.target.closest('button')) {
                    console.log('点击课程卡片');
                    // 这里可以添加课程卡片点击逻辑
                }
            });
        });
        
        // 课程详情链接
        const courseDetailLinks = document.querySelectorAll('.course-card a');
        courseDetailLinks.forEach(link => {
            link.addEventListener('click', function() {
                console.log('查看课程详情:', this.getAttribute('href'));
                // 这里可以添加课程详情查看逻辑
            });
        });
        
        // 立即报名按钮
        const enrollBtns = document.querySelectorAll('button');
        enrollBtns.forEach(btn => {
            if (btn.textContent.includes('立即报名') || btn.textContent.includes('报名')) {
                btn.addEventListener('click', function() {
                    console.log('立即报名');
                    // 这里可以添加报名逻辑
                    alert('报名成功！');
                });
            }
        });
        
        // 预览课程按钮
        const previewBtns = document.querySelectorAll('button');
        previewBtns.forEach(btn => {
            if (btn.querySelector('i.fa-play-circle') || btn.textContent.includes('预览')) {
                btn.addEventListener('click', function() {
                    console.log('预览课程');
                    // 这里可以添加预览逻辑
                    alert('预览课程功能');
                });
            }
        });
        
        // 收藏按钮
        const favoriteBtns = document.querySelectorAll('.favorite-btn');
        favoriteBtns.forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                const icon = this.querySelector('i');
                if (icon) {
                    if (icon.classList.contains('fa-heart-o')) {
                        icon.classList.remove('fa-heart-o');
                        icon.classList.add('fa-heart');
                        this.classList.remove('text-gray-500');
                        this.classList.add('text-red-500');
                        console.log('收藏课程');
                    } else {
                        icon.classList.remove('fa-heart');
                        icon.classList.add('fa-heart-o');
                        this.classList.remove('text-red-500');
                        this.classList.add('text-gray-500');
                        console.log('取消收藏');
                    }
                }
            });
        });
        
        // 分享按钮
        const shareBtns = document.querySelectorAll('.share-btn');
        shareBtns.forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                console.log('分享课程');
                // 这里可以添加分享逻辑
                if (navigator.share) {
                    navigator.share({
                        title: '股票分析与量化投资平台',
                        text: '推荐一门好课程',
                        url: window.location.href
                    });
                } else {
                    //  fallback for browsers that don't support Web Share API
                    const url = window.location.href;
                    navigator.clipboard.writeText(url).then(() => {
                        alert('链接已复制到剪贴板');
                    });
                }
            });
        });
    }
};

// 导出函数供其他脚本使用
if (typeof window !== 'undefined') {
    window.QuantPlatform = QuantPlatform;
    window.updateChartThemes = QuantPlatform.updateChartThemes;
    
    // 页面加载完成后初始化
    window.addEventListener('DOMContentLoaded', function() {
        QuantPlatform.init();
    });
}
