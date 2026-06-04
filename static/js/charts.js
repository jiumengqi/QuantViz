// 量化投资平台图表工具模块
// 支持 ECharts 高级图表类型：热力图、桑基图、雷达图等

// 全局图表实例存储
const ChartInstances = {};

// ECharts 主题配置
const EChartsTheme = {
    color: ['#165DFF', '#36CFC9', '#722ED1', '#F53F3F', '#F7BA1E', '#13C2C2', '#52C41A', '#EB5B5B'],
    backgroundColor: 'transparent',
    textStyle: {
        color: '#4E5969',
        fontFamily: 'Inter, system-ui, sans-serif'
    },
    title: {
        textStyle: {
            color: '#1D2129',
            fontWeight: '600'
        }
    },
    legend: {
        textStyle: {
            color: '#4E5969'
        }
    },
    tooltip: {
        backgroundColor: 'rgba(29, 33, 41, 0.9)',
        borderColor: '#165DFF',
        textStyle: {
            color: '#fff'
        }
    }
};

// ==================== 热力图 (Heatmap) ====================

/**
 * 创建热力图
 * @param {string} containerId - 容器ID
 * @param {Object} options - 配置选项
 * @returns {Object} ECharts实例
 */
function createHeatmap(containerId, options = {}) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error('热力图容器不存在:', containerId);
        return null;
    }

    // 销毁已存在的图表
    if (ChartInstances[containerId]) {
        ChartInstances[containerId].dispose();
    }

    const chart = echarts.init(container);
    
    const defaultOptions = {
        tooltip: {
            position: 'top',
            formatter: function(params) {
                return `${params.data[2].toFixed(2)}`;
            }
        },
        grid: {
            top: 40,
            bottom: 60,
            left: 100,
            right: 60
        },
        xAxis: {
            type: 'category',
            data: options.xAxisData || [],
            splitArea: { show: true },
            axisLabel: { 
                rotate: options.xAxisRotate || 0,
                fontSize: 11
            }
        },
        yAxis: {
            type: 'category',
            data: options.yAxisData || [],
            splitArea: { show: true },
            axisLabel: { fontSize: 11 }
        },
        visualMap: {
            min: options.minValue || -1,
            max: options.maxValue || 1,
            calculable: true,
            orient: options.visualMapOrient || 'horizontal',
            left: options.visualMapLeft || 'center',
            bottom: options.visualMapBottom || 0,
            inRange: {
                color: ['#F53F3F', '#F7BA1E', '#FFFFFF', '#73C0DE', '#165DFF']
            },
            textStyle: { fontSize: 11 }
        },
        series: [{
            type: 'heatmap',
            data: options.data || [],
            label: {
                show: options.showLabel !== false,
                fontSize: 10,
                formatter: function(params) {
                    return params.data[2].toFixed(2);
                }
            },
            emphasis: {
                itemStyle: {
                    shadowBlur: 10,
                    shadowColor: 'rgba(0, 0, 0, 0.5)'
                }
            }
        }]
    };

    // 合并选项
    const mergedOptions = deepMerge(defaultOptions, options);
    chart.setOption(mergedOptions);
    ChartInstances[containerId] = chart;

    // 响应式调整
    window.addEventListener('resize', () => {
        chart.resize();
    });

    return chart;
}

/**
 * 创建月度收益热力图
 * @param {string} containerId - 容器ID
 * @param {Array} data - 数据格式: [[月份, 年份, 收益率], ...]
 * @param {Object} options - 额外配置
 */
function createMonthlyReturnHeatmap(containerId, data, options = {}) {
    const months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'];
    const years = [...new Set(data.map(d => d[1]))].sort();
    
    return createHeatmap(containerId, {
        xAxisData: months,
        yAxisData: years,
        data: data,
        minValue: options.minValue || -20,
        maxValue: options.maxValue || 20,
        visualMapOrient: 'horizontal',
        visualMapLeft: 'center',
        visualMapBottom: 20,
        xAxisRotate: 0,
        showLabel: true
    });
}

/**
 * 创建相关性热力图
 * @param {string} containerId - 容器ID
 * @param {Array} stocks - 股票列表
 * @param {Array} correlationMatrix - 相关性矩阵
 */
function createCorrelationHeatmap(containerId, stocks, correlationMatrix) {
    const data = [];
    for (let i = 0; i < stocks.length; i++) {
        for (let j = 0; j < stocks.length; j++) {
            data.push([j, i, correlationMatrix[i][j]]);
        }
    }

    return createHeatmap(containerId, {
        xAxisData: stocks,
        yAxisData: stocks,
        data: data,
        minValue: -1,
        maxValue: 1,
        visualMapOrient: 'horizontal',
        visualMapLeft: 'center',
        visualMapBottom: 10,
        xAxisRotate: 30,
        showLabel: true
    });
}

// ==================== 桑基图 (Sankey) ====================

/**
 * 创建桑基图
 * @param {string} containerId - 容器ID
 * @param {Object} options - 配置选项
 * @returns {Object} ECharts实例
 */
function createSankey(containerId, options = {}) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error('桑基图容器不存在:', containerId);
        return null;
    }

    if (ChartInstances[containerId]) {
        ChartInstances[containerId].dispose();
    }

    const chart = echarts.init(container);

    const defaultOptions = {
        tooltip: {
            trigger: 'item',
            triggerOn: 'mousemove',
            formatter: function(params) {
                if (params.dataType === 'edge') {
                    return `${params.data.source} → ${params.data.target}<br/>流量: ${params.data.value}`;
                }
                return params.name;
            }
        },
        series: [{
            type: 'sankey',
            layout: 'none',
            emphasis: {
                focus: 'adjacency'
            },
            nodeAlign: options.nodeAlign || 'left',
            nodeGap: options.nodeGap || 12,
            nodeWidth: options.nodeWidth || 20,
            lineStyle: {
                color: 'gradient',
                curveness: options.curveness || 0.5,
                opacity: 0.4
            },
            label: {
                position: options.labelPosition || 'right',
                fontSize: 12
            },
            itemStyle: {
                borderWidth: 0
            },
            data: options.nodes || [],
            links: options.links || []
        }]
    };

    const mergedOptions = deepMerge(defaultOptions, options);
    chart.setOption(mergedOptions);
    ChartInstances[containerId] = chart;

    window.addEventListener('resize', () => {
        chart.resize();
    });

    return chart;
}

/**
 * 创建资金流向桑基图
 * @param {string} containerId - 容器ID
 * @param {Array} sources - 资金来源节点
 * @param {Array} targets - 资金去向节点
 * @param {Array} flowData - 流量数据格式: [{source, target, value}, ...]
 */
function createFundFlowSankey(containerId, sources, targets, flowData) {
    const nodes = [
        ...sources.map(s => ({ name: s, itemStyle: { color: '#165DFF' } })),
        ...targets.map(t => ({ name: t, itemStyle: { color: '#36CFC9' } }))
    ];

    return createSankey(containerId, {
        nodes: nodes,
        links: flowData,
        nodeAlign: 'justify',
        nodeGap: 8,
        nodeWidth: 25,
        curveness: 0.5,
        labelPosition: 'right'
    });
}

/**
 * 创建投资组合构成桑基图
 * @param {string} containerId - 容器ID
 * @param {Object} portfolioData - 投资组合数据
 */
function createPortfolioSankey(containerId, portfolioData) {
    const nodes = [];
    const links = [];

    // 根节点：总资产
    nodes.push({ name: '总资产', itemStyle: { color: '#165DFF' } });

    // 资产大类
    portfolioData.assetClasses.forEach((ac, idx) => {
        nodes.push({ name: ac.name, itemStyle: { color: EChartsTheme.color[idx + 1] } });
        links.push({ source: '总资产', target: ac.name, value: ac.value });
    });

    // 具体持仓
    portfolioData.holdings.forEach((h, idx) => {
        nodes.push({ name: h.name, itemStyle: { color: EChartsTheme.color[(idx % 6) + 2] } });
        links.push({ source: h.assetClass, target: h.name, value: h.value });
    });

    return createSankey(containerId, {
        nodes: nodes,
        links: links,
        nodeAlign: 'left',
        nodeGap: 6,
        curveness: 0.6
    });
}

// ==================== 雷达图 (Radar) ====================

/**
 * 创建雷达图
 * @param {string} containerId - 容器ID
 * @param {Object} options - 配置选项
 * @returns {Object} ECharts实例
 */
function createRadar(containerId, options = {}) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error('雷达图容器不存在:', containerId);
        return null;
    }

    if (ChartInstances[containerId]) {
        ChartInstances[containerId].dispose();
    }

    const chart = echarts.init(container);

    const defaultOptions = {
        tooltip: {
            trigger: 'item',
            backgroundColor: 'rgba(29, 33, 41, 0.9)',
            borderColor: '#165DFF',
            textStyle: { color: '#fff' }
        },
        legend: {
            bottom: 10,
            data: options.legendData || [],
            textStyle: { fontSize: 12 }
        },
        radar: {
            indicator: options.indicator || [],
            shape: options.shape || 'polygon',
            splitNumber: options.splitNumber || 5,
            axisName: {
                color: '#4E5969',
                fontSize: 12
            },
            splitLine: {
                lineStyle: {
                    color: 'rgba(22, 93, 255, 0.1)'
                }
            },
            splitArea: {
                show: true,
                areaStyle: {
                    color: ['rgba(22, 93, 255, 0.02)', 'rgba(22, 93, 255, 0.05)', 'rgba(22, 93, 255, 0.08)', 'rgba(22, 93, 255, 0.12)', 'rgba(22, 93, 255, 0.15)']
                }
            },
            axisLine: {
                lineStyle: {
                    color: 'rgba(22, 93, 255, 0.2)'
                }
            }
        },
        series: [{
            type: 'radar',
            emphasis: {
                lineStyle: {
                    width: 4
                }
            },
            data: options.seriesData || []
        }]
    };

    const mergedOptions = deepMerge(defaultOptions, options);
    chart.setOption(mergedOptions);
    ChartInstances[containerId] = chart;

    window.addEventListener('resize', () => {
        chart.resize();
    });

    return chart;
}

/**
 * 创建策略评价雷达图
 * @param {string} containerId - 容器ID
 * @param {Object} metrics - 策略指标
 * @param {Array} benchmark - 基准对比数据(可选)
 */
function createStrategyRadar(containerId, metrics, benchmark = null) {
    const indicator = [
        { name: '收益率', max: metrics.maxReturn || 100 },
        { name: '风险控制', max: 100 },
        { name: '夏普比率', max: metrics.maxSharpe || 3 },
        { name: '胜率', max: 100 },
        { name: '流动性', max: 100 },
        { name: '稳定性', max: 100 }
    ];

    const seriesData = [{
        value: [
            metrics.return || 0,
            metrics.riskControl || 0,
            metrics.sharpeRatio || 0,
            metrics.winRate || 0,
            metrics.liquidity || 0,
            metrics.stability || 0
        ],
        name: '策略评价',
        lineStyle: {
            width: 2,
            color: '#165DFF'
        },
        areaStyle: {
            color: new echarts.graphic.RadialGradient(0.5, 0.5, 1, [
                { offset: 0, color: 'rgba(22, 93, 255, 0.3)' },
                { offset: 1, color: 'rgba(22, 93, 255, 0.05)' }
            ])
        },
        itemStyle: {
            color: '#165DFF'
        }
    }];

    if (benchmark) {
        seriesData.push({
            value: [
                benchmark.return || 0,
                benchmark.riskControl || 0,
                benchmark.sharpeRatio || 0,
                benchmark.winRate || 0,
                benchmark.liquidity || 0,
                benchmark.stability || 0
            ],
            name: '基准',
            lineStyle: {
                width: 2,
                color: '#86909C',
                type: 'dashed'
            },
            areaStyle: {
                color: 'rgba(134, 144, 156, 0.1)'
            },
            itemStyle: {
                color: '#86909C'
            }
        });
    }

    return createRadar(containerId, {
        indicator: indicator,
        legendData: ['策略评价', ...(benchmark ? ['基准'] : [])],
        seriesData: seriesData,
        shape: 'polygon',
        splitNumber: 5
    });
}

/**
 * 创建股票特征对比雷达图
 * @param {string} containerId - 容器ID
 * @param {Array} stocks - 股票数据格式: [{name, data: [value1, value2, ...]}, ...]
 */
function createStockFeatureRadar(containerId, stocks) {
    if (stocks.length === 0) return null;

    // 从第一只股票获取指标名称
    const indicatorNames = stocks[0].features || ['估值', '成长', '盈利', '运营', '财务', '市场'];
    const maxValues = stocks[0].maxValues || indicatorNames.map(() => 100);

    const indicator = indicatorNames.map((name, idx) => ({
        name: name,
        max: maxValues[idx]
    }));

    const seriesData = stocks.map((stock, idx) => ({
        value: stock.data,
        name: stock.name,
        lineStyle: {
            width: 2,
            color: EChartsTheme.color[idx]
        },
        areaStyle: {
            color: new echarts.graphic.RadialGradient(0.5, 0.5, 1, [
                { offset: 0, color: EChartsTheme.color[idx % EChartsTheme.color.length] + '40' },
                { offset: 1, color: EChartsTheme.color[idx % EChartsTheme.color.length] + '05' }
            ])
        },
        itemStyle: {
            color: EChartsTheme.color[idx]
        }
    }));

    return createRadar(containerId, {
        indicator: indicator,
        legendData: stocks.map(s => s.name),
        seriesData: seriesData,
        shape: 'polygon',
        splitNumber: 4
    });
}

// ==================== 树图 (Treemap) ====================

/**
 * 创建树图
 * @param {string} containerId - 容器ID
 * @param {Object} options - 配置选项
 * @returns {Object} ECharts实例
 */
function createTreemap(containerId, options = {}) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error('树图容器不存在:', containerId);
        return null;
    }

    if (ChartInstances[containerId]) {
        ChartInstances[containerId].dispose();
    }

    const chart = echarts.init(container);

    const defaultOptions = {
        tooltip: {
            trigger: 'item',
            formatter: function(params) {
                return `${params.name}<br/>市值: ${params.value}`;
            }
        },
        series: [{
            type: 'treemap',
            visibleMin: options.visibleMin || 100,
            label: {
                show: true,
                formatter: '{b}',
                fontSize: 11,
                color: '#fff'
            },
            upperLabel: {
                show: true,
                height: 30,
                color: '#fff',
                fontSize: 12
            },
            itemStyle: {
                borderColor: '#fff',
                borderWidth: 2,
                gapWidth: 2
            },
            emphasis: {
                itemStyle: {
                    shadowBlur: 10,
                    shadowColor: 'rgba(0, 0, 0, 0.5)'
                }
            },
            levels: options.levels || getDefaultTreemapLevels(),
            data: options.data || []
        }]
    };

    const mergedOptions = deepMerge(defaultOptions, options);
    chart.setOption(mergedOptions);
    ChartInstances[containerId] = chart;

    window.addEventListener('resize', () => {
        chart.resize();
    });

    return chart;
}

function getDefaultTreemapLevels() {
    return [
        {
            itemStyle: {
                borderColor: '#fff',
                borderWidth: 5,
                gapWidth: 5
            },
            emphasis: {
                itemStyle: {
                    shadowBlur: 20,
                    shadowColor: 'rgba(0, 0, 0, 0.5)'
                }
            }
        },
        {
            colorSaturation: [0.35, 0.5],
            itemStyle: {
                borderWidth: 5,
                gapWidth: 1,
                borderColorSaturation: 0.6
            }
        }
    ];
}

/**
 * 创建行业分布树图
 * @param {string} containerId - 容器ID
 * @param {Array} sectors - 行业数据格式: [{name, value, children: [{name, value}, ...]}, ...]
 */
function createSectorTreemap(containerId, sectors) {
    return createTreemap(containerId, {
        data: sectors.map((sector, idx) => ({
            name: sector.name,
            value: sector.value,
            children: sector.stocks.map((stock, sIdx) => ({
                name: stock.name,
                value: stock.value
            })),
            itemStyle: {
                color: EChartsTheme.color[idx % EChartsTheme.color.length]
            }
        }))
    });
}

// ==================== 仪表盘 (Gauge) ====================

/**
 * 创建仪表盘
 * @param {string} containerId - 容器ID
 * @param {Object} options - 配置选项
 * @returns {Object} ECharts实例
 */
function createGauge(containerId, options = {}) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error('仪表盘容器不存在:', containerId);
        return null;
    }

    if (ChartInstances[containerId]) {
        ChartInstances[containerId].dispose();
    }

    const chart = echarts.init(container);

    const defaultOptions = {
        series: [{
            type: 'gauge',
            startAngle: 200,
            endAngle: -20,
            min: options.min || 0,
            max: options.max || 100,
            splitNumber: options.splitNumber || 10,
            radius: options.radius || '90%',
            center: ['50%', '60%'],
            axisLine: {
                lineStyle: {
                    width: options.axisLineWidth || 15,
                    color: options.axisLineColor || [
                        [0.3, '#F53F3F'],
                        [0.7, '#F7BA1E'],
                        [1, '#52C41A']
                    ]
                }
            },
            pointer: {
                icon: 'path://M12.8,0.7l12,40.1H0.7L12.8,0.7z',
                length: '50%',
                width: 10,
                offsetCenter: [0, '-10%'],
                itemStyle: {
                    color: 'auto'
                }
            },
            axisTick: {
                length: 8,
                lineStyle: {
                    color: 'auto',
                    width: 1
                }
            },
            splitLine: {
                length: 15,
                lineStyle: {
                    color: 'auto',
                    width: 2
                }
            },
            axisLabel: {
                color: '#4E5969',
                fontSize: 11,
                distance: -50
            },
            title: {
                offsetCenter: [0, '-10%'],
                fontSize: 14,
                color: '#1D2129'
            },
            detail: {
                valueAnimation: true,
                formatter: options.formatter || '{value}%',
                fontSize: options.detailFontSize || 24,
                fontWeight: 'bold',
                offsetCenter: [0, '60%'],
                color: 'auto'
            },
            data: options.data || [{ value: 0, name: '' }]
        }]
    };

    const mergedOptions = deepMerge(defaultOptions, options);
    chart.setOption(mergedOptions);
    ChartInstances[containerId] = chart;

    window.addEventListener('resize', () => {
        chart.resize();
    });

    return chart;
}

// ==================== 图表工具函数 ====================

/**
 * 深拷贝合并对象
 */
function deepMerge(target, source) {
    const result = { ...target };
    for (const key in source) {
        if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
            result[key] = deepMerge(target[key] || {}, source[key]);
        } else {
            result[key] = source[key];
        }
    }
    return result;
}

/**
 * 销毁指定图表实例
 */
function disposeChart(containerId) {
    if (ChartInstances[containerId]) {
        ChartInstances[containerId].dispose();
        delete ChartInstances[containerId];
    }
}

/**
 * 销毁所有图表实例
 */
function disposeAllCharts() {
    Object.keys(ChartInstances).forEach(id => {
        if (ChartInstances[id]) {
            ChartInstances[id].dispose();
            delete ChartInstances[id];
        }
    });
}

/**
 * 导出图表为图片
 */
function exportChartAsImage(containerId, filename = 'chart') {
    const chart = ChartInstances[containerId];
    if (!chart) {
        console.error('图表实例不存在:', containerId);
        return;
    }

    const url = chart.getDataURL({
        type: 'png',
        pixelRatio: 2,
        backgroundColor: '#fff'
    });

    const link = document.createElement('a');
    link.download = `${filename}.png`;
    link.href = url;
    link.click();
}

// ==================== Chart.js 兼容函数 ====================

/**
 * 创建Chart.js热力图(兼容旧代码)
 */
function createChartJSHeatmap(containerId, data, labels) {
    const ctx = document.getElementById(containerId);
    if (!ctx) return null;

    // 将数据转换为Chart.js matrix格式
    const matrixData = [];
    for (let i = 0; i < data.length; i++) {
        for (let j = 0; j < data[i].length; j++) {
            matrixData.push({
                x: j,
                y: i,
                v: data[i][j]
            });
        }
    }

    if (ChartInstances[containerId + '_chartjs']) {
        ChartInstances[containerId + '_chartjs'].destroy();
    }

    const chart = new Chart(ctx, {
        type: 'matrix',
        data: {
            datasets: [{
                label: '热力图',
                data: matrixData,
                backgroundColor: function(context) {
                    const value = context.raw.v;
                    const alpha = Math.abs(value);
                    if (value > 0) {
                        return `rgba(22, 93, 255, ${alpha})`;
                    } else {
                        return `rgba(245, 63, 63, ${alpha})`;
                    }
                },
                borderColor: 'rgba(0, 0, 0, 0.1)',
                borderWidth: 1,
                width: ({ chart }) => (chart.chartArea || {}).width / labels.length - 1,
                height: ({ chart }) => (chart.chartArea || {}).height / labels.length - 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            return `${labels[context[0].raw.y]} vs ${labels[context[0].raw.x]}`;
                        },
                        label: function(context) {
                            return `值: ${context.raw.v.toFixed(2)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'category',
                    labels: labels,
                    offset: true,
                    grid: { display: false }
                },
                y: {
                    type: 'category',
                    labels: labels,
                    offset: true,
                    grid: { display: false }
                }
            }
        }
    });

    ChartInstances[containerId + '_chartjs'] = chart;
    return chart;
}

// 导出函数供全局使用
window.QuantCharts = {
    // 热力图
    createHeatmap,
    createMonthlyReturnHeatmap,
    createCorrelationHeatmap,
    // 桑基图
    createSankey,
    createFundFlowSankey,
    createPortfolioSankey,
    // 雷达图
    createRadar,
    createStrategyRadar,
    createStockFeatureRadar,
    // 树图
    createTreemap,
    createSectorTreemap,
    // 仪表盘
    createGauge,
    // 工具函数
    disposeChart,
    disposeAllCharts,
    exportChartAsImage,
    // Chart.js兼容
    createChartJSHeatmap,
    // 主题
    EChartsTheme
};
