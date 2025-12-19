// 
// 问题列表页面的JavaScript功能
// problems.js
// 

// 全局变量
let currentPage = 1;
const itemsPerPage = 10;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    loadEquipmentTypes();
    loadProblems(currentPage);
    
    // 绑定事件监听器
    document.getElementById('applyFilters').addEventListener('click', function() {
        currentPage = 1;
        loadProblems(currentPage);
    });
    
    document.getElementById('refreshBtn').addEventListener('click', function() {
        loadProblems(currentPage);
    });
    
    document.getElementById('searchInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            currentPage = 1;
            loadProblems(currentPage);
        }
    });
});

// 加载设备类型选项
function loadEquipmentTypes() {
    fetch('/api/equipment-types')
        .then(response => response.json())
        .then(data => {
            const select = document.getElementById('equipmentFilter');
            select.innerHTML = '<option value="">所有设备类型</option>';
            
            data.forEach(et => {
                const option = document.createElement('option');
                option.value = et.id;
                option.textContent = et.name;
                select.appendChild(option);
            });
        })
        .catch(error => {
            console.error('加载设备类型失败:', error);
        });
}

// 加载问题列表
function loadProblems(page = 1) {
    const search = document.getElementById('searchInput').value;
    const status = document.getElementById('statusFilter').value;
    const phase = document.getElementById('phaseFilter').value;
    const equipmentTypeId = document.getElementById('equipmentFilter').value;
    
    let url = `/api/problems?page=${page}&limit=${itemsPerPage}`;
    
    if (search) url += `&search=${encodeURIComponent(search)}`;
    if (status) url += `&status=${status}`;
    if (phase) url += `&phase=${phase}`;
    if (equipmentTypeId) url += `&equipment_type=${equipmentTypeId}`;
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            const tbody = document.querySelector('#problemsTable tbody');
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
                        new Date(problem.discovered_at).toLocaleDateString() : '未指定';
                    
                    // AI分析状态
                    const aiAnalysisStatus = problem.ai_analyzed ? 
                        '<span class="badge bg-success"><i class="fas fa-robot"></i> 已分析</span>' : 
                        '<span class="badge bg-secondary"><i class="fas fa-robot"></i> 未分析</span>';
                    
                    row.innerHTML = `
                        <td>${problem.id}</td>
                        <td>${problem.title}</td>
                        <td>${problem.equipment_type_name || '未指定'}</td>
                        <td>${problem.problem_category_name || '未分类'}</td>
                        <td>${problem.phase}</td>
                        <td>${statusBadge}</td>
                        <td>${priorityBadge}</td>
                        <td>${problem.discovered_by || '未知'}</td>
                        <td>${discoveredAt}</td>
                        <td>${aiAnalysisStatus}</td>
                        <td>
                            <button class="btn btn-sm btn-outline-primary me-1" onclick="viewProblemDetail(${problem.id})">
                                <i class="fas fa-eye"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-info me-1" onclick="editProblem(${problem.id})">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger" onclick="deleteProblem(${problem.id})">
                                <i class="fas fa-trash"></i>
                            </button>
                        </td>
                    `;
                    
                    tbody.appendChild(row);
                });
            } else {
                const row = document.createElement('tr');
                row.innerHTML = `<td colspan="11" class="text-center">暂无问题数据</td>`;
                tbody.appendChild(row);
            }
            
            // 加载分页
            loadPagination(data.total, page);
        })
        .catch(error => {
            console.error('加载问题列表失败:', error);
            alert('加载问题列表失败');
        });
}

// 加载分页
function loadPagination(totalItems, currentPage) {
    const totalPages = Math.ceil(totalItems / itemsPerPage);
    const pagination = document.getElementById('pagination');
    pagination.innerHTML = '';
    
    if (totalPages <= 1) return;
    
    // 上一页按钮
    const prevLi = document.createElement('li');
    prevLi.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
    prevLi.innerHTML = `
        <a class="page-link" href="#" onclick="changePage(${Math.max(1, currentPage - 1)})">
            <i class="fas fa-chevron-left"></i> 上一页
        </a>
    `;
    pagination.appendChild(prevLi);
    
    // 页码按钮
    for (let i = Math.max(1, currentPage - 2); i <= Math.min(totalPages, currentPage + 2); i++) {
        const li = document.createElement('li');
        li.className = `page-item ${i === currentPage ? 'active' : ''}`;
        li.innerHTML = `
            <a class="page-link" href="#" onclick="changePage(${i})">${i}</a>
        `;
        pagination.appendChild(li);
    }
    
    // 下一页按钮
    const nextLi = document.createElement('li');
    nextLi.className = `page-item ${currentPage === totalPages ? 'disabled' : ''}`;
    nextLi.innerHTML = `
        <a class="page-link" href="#" onclick="changePage(${Math.min(totalPages, currentPage + 1)})">
            下一页 <i class="fas fa-chevron-right"></i>
        </a>
    `;
    pagination.appendChild(nextLi);
}

// 更改页面
function changePage(page) {
    currentPage = page;
    loadProblems(page);
}

// 查看问题详情
function viewProblemDetail(problemId) {
    fetch(`/api/problems/${problemId}`)
        .then(response => response.json())
        .then(problem => {
            // 在模态框中显示问题详情
            const modalBody = document.getElementById('problemDetailContent');
            modalBody.innerHTML = `
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>ID:</strong> ${problem.id}</p>
                        <p><strong>标题:</strong> ${problem.title}</p>
                        <p><strong>设备类型:</strong> ${problem.equipment_type_name || '未指定'}</p>
                        <p><strong>问题分类:</strong> ${problem.problem_category_name || '未分类'}</p>
                        <p><strong>解决方案分类:</strong> ${problem.solution_category_name || '未指定'}</p>
                        <p><strong>阶段:</strong> ${problem.phase}</p>
                        <p><strong>状态:</strong> 
                            <span class="badge ${
                                problem.status === 'new' ? 'bg-warning' :
                                problem.status === 'analyzed' ? 'bg-info' :
                                problem.status === 'solved' ? 'bg-success' :
                                problem.status === 'verified' ? 'bg-primary' : 'bg-secondary'
                            }">${problem.status}</span>
                        </p>
                        <p><strong>优先级:</strong> 
                            <span class="badge ${
                                problem.priority === 'critical' ? 'bg-danger' :
                                problem.priority === 'high' ? 'bg-warning text-dark' :
                                problem.priority === 'medium' ? 'bg-primary' :
                                problem.priority === 'low' ? 'bg-success' : 'bg-secondary'
                            }">${problem.priority}</span>
                        </p>
                    </div>
                    <div class="col-md-6">
                        <p><strong>发现者:</strong> ${problem.discovered_by || '未指定'}</p>
                        <p><strong>发现时间:</strong> ${problem.discovered_at || '未指定'}</p>
                        <p><strong>AI已分析:</strong> ${problem.ai_analyzed ? '是' : '否'}</p>
                        <p><strong>创建时间:</strong> ${new Date(problem.created_at).toLocaleString()}</p>
                        <p><strong>更新时间:</strong> ${new Date(problem.updated_at).toLocaleString()}</p>
                    </div>
                </div>
                <hr>
                <div class="row">
                    <div class="col-12">
                        <p><strong>问题描述:</strong></p>
                        <p>${problem.description || '无'}</p>
                        
                        ${problem.ai_analysis ? `
                            <p><strong>AI分析结果:</strong></p>
                            <div class="ai-analysis-content">
                                ${formatAiAnalysis(problem.ai_analysis)}
                            </div>
                        ` : ''}
                        
                        ${problem.solution_description ? `
                            <p><strong>解决方案描述:</strong></p>
                            <p>${problem.solution_description}</p>
                        ` : ''}
                        
                        ${problem.solution_implementation ? `
                            <p><strong>解决方案实施:</strong></p>
                            <p>${problem.solution_implementation}</p>
                        ` : ''}
                        
                        ${problem.solution_verification ? `
                            <p><strong>解决方案验证:</strong></p>
                            <p>${problem.solution_verification}</p>
                        ` : ''}
                    </div>
                </div>
            `;
            
            // 显示模态框
            const modal = new bootstrap.Modal(document.getElementById('problemDetailModal'));
            modal.show();
        })
        .catch(error => {
            console.error('获取问题详情失败:', error);
            alert('获取问题详情失败');
        });
}

// 编辑问题
function editProblem(problemId) {
    alert(`编辑问题功能将在后续版本中实现。问题ID: ${problemId}`);
}

// 删除问题
function deleteProblem(problemId) {
    if (confirm('确定要删除这个问题吗？此操作不可撤销。')) {
        fetch(`/api/problems/${problemId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (response.ok) {
                alert('问题删除成功');
                loadProblems(currentPage);
            } else {
                alert('删除失败');
            }
        })
        .catch(error => {
            console.error('删除问题失败:', error);
            alert('删除失败');
        });
    }
}

// 搜索功能
function searchProblems() {
    currentPage = 1;
    loadProblems(currentPage);
}

// 格式化AI分析结果
function formatAiAnalysis(aiAnalysis) {
    // 尝试解析AI分析结果，提取结构化信息
    let result = '';
    
    // 分割AI分析内容到行
    const lines = aiAnalysis.split('\n');
    
    // 识别和格式化不同的部分
    let currentSection = '';
    let sectionContent = '';
    
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        
        if (!line) continue;
        
        // 识别标题行
        if (line.includes('问题分类:') || 
            line.includes('系统内部原因分析:') || 
            line.includes('系统外部原因分析:') || 
            line.includes('解决方案:') || 
            line.includes('问题严重程度:') || 
            line.includes('发现阶段:') ||
            line.includes('根本原因分析:')) {
            
            // 如果有上一个section，先处理它
            if (currentSection && sectionContent) {
                result += renderSection(currentSection, sectionContent);
                sectionContent = '';
            }
            
            // 提取section标题和内容
            if (line.includes('问题分类:')) {
                currentSection = '问题分类';
                sectionContent = line.replace('问题分类:', '').trim();
            } else if (line.includes('系统内部原因分析:')) {
                currentSection = '系统内部原因分析';
                sectionContent = line.replace('系统内部原因分析:', '').trim();
            } else if (line.includes('系统外部原因分析:')) {
                currentSection = '系统外部原因分析';
                sectionContent = line.replace('系统外部原因分析:', '').trim();
            } else if (line.includes('解决方案:')) {
                currentSection = '解决方案';
                sectionContent = line.replace('解决方案:', '').trim();
            } else if (line.includes('问题严重程度:')) {
                currentSection = '问题严重程度';
                sectionContent = line.replace('问题严重程度:', '').trim();
            } else if (line.includes('发现阶段:')) {
                currentSection = '发现阶段';
                sectionContent = line.replace('发现阶段:', '').trim();
            } else if (line.includes('根本原因分析:')) {
                currentSection = '根本原因分析';
                sectionContent = line.replace('根本原因分析:', '').trim();
            }
        } else if (line.startsWith('- ') || line.startsWith('   -')) {
            // 处理列表项
            if (currentSection) {
                sectionContent += '<br>' + line;
            }
        } else if (line.startsWith('1.') || line.startsWith('2.') || line.startsWith('3.') || 
                   line.startsWith('4.') || line.startsWith('5.')) {
            // 处理编号列表项
            if (currentSection) {
                sectionContent += '<br>' + line;
            }
        } else {
            // 添加到当前section的内容中
            if (currentSection && sectionContent) {
                sectionContent += '<br>' + line;
            } else if (currentSection) {
                sectionContent = line;
            }
        }
    }
    
    // 处理最后一个section
    if (currentSection && sectionContent) {
        result += renderSection(currentSection, sectionContent);
    }
    
    // 如果没有识别到结构化内容，直接显示原始内容
    if (!result) {
        return `<pre class="bg-light p-3 rounded">${aiAnalysis}</pre>`;
    }
    
    return result;
}

// 渲染section
function renderSection(title, content) {
    let badgeClass = '';
    
    // 根据标题设置不同的样式
    if (title.includes('内部')) {
        badgeClass = 'bg-info';
    } else if (title.includes('外部')) {
        badgeClass = 'bg-warning text-dark';
    } else if (title.includes('解决方案')) {
        badgeClass = 'bg-success';
    } else if (title.includes('严重程度')) {
        if (content.toLowerCase().includes('高') || content.toLowerCase().includes('严重')) {
            badgeClass = 'bg-danger';
        } else if (content.toLowerCase().includes('中')) {
            badgeClass = 'bg-primary';
        } else if (content.toLowerCase().includes('低')) {
            badgeClass = 'bg-success';
        } else {
            badgeClass = 'bg-secondary';
        }
    } else {
        badgeClass = 'bg-secondary';
    }
    
    return `
        <div class="mb-3">
            <h6>
                <span class="badge ${badgeClass}">${title}</span>
            </h6>
            <div class="border-start border-primary ps-2 py-1">${content}</div>
        </div>
    `;
}