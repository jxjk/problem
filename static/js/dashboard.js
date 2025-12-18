// 
// 仪表盘页面的JavaScript功能
// dashboard.js
// 

// 全局变量
let equipmentChart = null;
let categoryChart = null;
let phaseChart = null;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    loadDashboardStats();
    loadEquipmentChart();
    loadCategoryChart();
    loadPhaseChart();
    loadLatestProblems();
    
    // 设置定时刷新
    setInterval(function() {
        loadDashboardStats();
        loadEquipmentChart();
        loadCategoryChart();
        loadPhaseChart();
        loadLatestProblems();
    }, 60000); // 每分钟刷新一次
});

// 加载仪表盘统计信息
function loadDashboardStats() {
    fetch('/api/dashboard-stats')
        .then(response => response.json())
        .then(data => {
            document.getElementById('totalProblems').textContent = data.total_problems || 0;
            document.getElementById('newProblems').textContent = data.new_problems || 0;
            document.getElementById('analyzedProblems').textContent = data.analyzed_problems || 0;
            document.getElementById('solvedProblems').textContent = data.solved_problems || 0;
            document.getElementById('criticalProblems').textContent = data.critical_problems || 0;
            document.getElementById('verifiedProblems').textContent = data.verified_problems || 0;
        })
        .catch(error => {
            console.error('加载统计信息失败:', error);
        });
}

// 加载设备类型图表
function loadEquipmentChart() {
    fetch('/api/problems-by-equipment')
        .then(response => response.json())
        .then(data => {
            const ctx = document.getElementById('equipmentChart').getContext('2d');
            
            // 销毁之前的图表实例
            if (equipmentChart) {
                equipmentChart.destroy();
            }
            
            const labels = data.map(item => item.equipment_type);
            const values = data.map(item => item.problem_count);
            
            equipmentChart = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: labels,
                    datasets: [{
                        data: values,
                        backgroundColor: [
                            'rgba(255, 99, 132, 0.8)',
                            'rgba(54, 162, 235, 0.8)',
                            'rgba(255, 205, 86, 0.8)',
                            'rgba(75, 192, 192, 0.8)',
                            'rgba(153, 102, 255, 0.8)',
                            'rgba(255, 159, 64, 0.8)',
                            'rgba(199, 199, 199, 0.8)',
                            'rgba(83, 102, 255, 0.8)'
                        ],
                        borderColor: [
                            'rgba(255, 99, 132, 1)',
                            'rgba(54, 162, 235, 1)',
                            'rgba(255, 205, 86, 1)',
                            'rgba(75, 192, 192, 1)',
                            'rgba(153, 102, 255, 1)',
                            'rgba(255, 159, 64, 1)',
                            'rgba(199, 199, 199, 1)',
                            'rgba(83, 102, 255, 1)'
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return `${context.label}: ${context.parsed} 个问题`;
                                }
                            }
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error('加载设备类型统计失败:', error);
        });
}

// 加载问题分类图表
function loadCategoryChart() {
    fetch('/api/problems-by-category')
        .then(response => response.json())
        .then(data => {
            const ctx = document.getElementById('categoryChart').getContext('2d');
            
            // 销毁之前的图表实例
            if (categoryChart) {
                categoryChart.destroy();
            }
            
            const labels = data.map(item => item.category_name);
            const values = data.map(item => item.problem_count);
            
            categoryChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: '问题数量',
                        data: values,
                        backgroundColor: 'rgba(54, 162, 235, 0.6)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: '问题数量'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: '问题分类'
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error('加载问题分类统计失败:', error);
        });
}

// 加载发现问题阶段图表
function loadPhaseChart() {
    fetch('/api/dashboard-stats')
        .then(response => response.json())
        .then(data => {
            const ctx = document.getElementById('phaseChart').getContext('2d');
            
            // 销毁之前的图表实例
            if (phaseChart) {
                phaseChart.destroy();
            }
            
            const labels = ['设计阶段', '开发阶段', '使用阶段', '维护阶段'];
            const values = [
                data.design_phase_problems || 0,
                data.development_phase_problems || 0,
                data.usage_phase_problems || 0,
                data.maintenance_phase_problems || 0
            ];
            
            phaseChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: '问题数量',
                        data: values,
                        fill: false,
                        borderColor: 'rgb(75, 192, 192)',
                        tension: 0.1,
                        backgroundColor: 'rgba(75, 192, 192, 0.2)'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: '问题数量'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: '问题阶段'
                            }
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error('加载问题阶段统计失败:', error);
        });
}

// 加载最新问题
function loadLatestProblems() {
    fetch('/api/problems?page=1&limit=5')
        .then(response => response.json())
        .then(data => {
            const tbody = document.querySelector('#latestProblemsTable tbody');
            tbody.innerHTML = '';
            
            if (data.problems && data.problems.length > 0) {
                data.problems.forEach(problem => {
                    const row = document.createElement('tr');
                    
                    // 根据状态和优先级添加标签
                    let statusBadge = '';
                    switch(problem.status) {
                        case 'new':
                            statusBadge = '<span class="badge bg-warning">新问题</span>';
                            break;
                        case 'analyzed':
                            statusBadge = '<span class="badge bg-info">已分析</span>';
                            break;
                        case 'solved':
                            statusBadge = '<span class="badge bg-success">已解决</span>';
                            break;
                        case 'verified':
                            statusBadge = '<span class="badge bg-primary">已验证</span>';
                            break;
                        default:
                            statusBadge = '<span class="badge bg-secondary">未知</span>';
                    }
                    
                    let priorityBadge = '';
                    switch(problem.priority) {
                        case 'critical':
                            priorityBadge = '<span class="badge bg-danger">严重</span>';
                            break;
                        case 'high':
                            priorityBadge = '<span class="badge bg-warning text-dark">高</span>';
                            break;
                        case 'medium':
                            priorityBadge = '<span class="badge bg-primary">中</span>';
                            break;
                        case 'low':
                            priorityBadge = '<span class="badge bg-success">低</span>';
                            break;
                        default:
                            priorityBadge = '<span class="badge bg-secondary">未知</span>';
                    }
                    
                    // 格式化日期
                    const discoveredAt = problem.discovered_at ? 
                        new Date(problem.discovered_at).toLocaleDateString() : '未知';
                    
                    row.innerHTML = `
                        <td>${problem.title}</td>
                        <td>${problem.equipment_type_name || '未指定'}</td>
                        <td>${problem.phase}</td>
                        <td>${statusBadge}</td>
                        <td>${priorityBadge}</td>
                        <td>${discoveredAt}</td>
                        <td>
                            <button class="btn btn-sm btn-outline-primary" onclick="viewProblem(${problem.id})">
                                <i class="fas fa-eye"></i> 查看
                            </button>
                        </td>
                    `;
                    
                    tbody.appendChild(row);
                });
            } else {
                const row = document.createElement('tr');
                row.innerHTML = `<td colspan="7" class="text-center">暂无问题数据</td>`;
                tbody.appendChild(row);
            }
        })
        .catch(error => {
            console.error('加载最新问题失败:', error);
        });
}

// 查看问题详情
function viewProblem(problemId) {
    fetch(`/api/problems/${problemId}`)
        .then(response => response.json())
        .then(problem => {
            // 在这里可以打开模态框或跳转到详情页面
            alert(`问题详情:\n标题: ${problem.title}\n描述: ${problem.description}\n状态: ${problem.status}`);
        })
        .catch(error => {
            console.error('获取问题详情失败:', error);
            alert('获取问题详情失败');
        });
}

// 刷新数据
function refreshData() {
    loadDashboardStats();
    loadEquipmentChart();
    loadCategoryChart();
    loadPhaseChart();
    loadLatestProblems();
}

// 页面大小改变时重新调整图表
window.addEventListener('resize', function() {
    if (equipmentChart) equipmentChart.resize();
    if (categoryChart) categoryChart.resize();
    if (phaseChart) phaseChart.resize();
});