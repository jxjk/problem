// 
// 添加问题页面的JavaScript功能
// add_problem.js
// 

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    loadEquipmentTypes();
    
    // 绑定表单提交事件
    document.getElementById('addProblemForm').addEventListener('submit', function(e) {
        e.preventDefault();
        addProblem();
    });
});

// 加载设备类型选项
function loadEquipmentTypes() {
    fetch('/api/equipment-types')
        .then(response => response.json())
        .then(data => {
            const select = document.getElementById('equipment_type_id');
            select.innerHTML = '<option value="">选择设备类型</option>';
            
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

// 添加问题
function addProblem() {
    const formData = {
        title: document.getElementById('title').value,
        description: document.getElementById('description').value,
        equipment_type_id: document.getElementById('equipment_type_id').value || null,
        phase: document.getElementById('phase').value,
        discovered_by: document.getElementById('discovered_by').value,
        discovered_at: document.getElementById('discovered_at').value || null
    };
    
    // 简单验证
    if (!formData.title.trim() || !formData.description.trim()) {
        alert('标题和描述不能为空');
        return;
    }
    
    // 禁用提交按钮，显示加载状态
    const submitBtn = document.querySelector('#addProblemForm button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 保存中...';
    submitBtn.disabled = true;
    
    fetch('/api/problems', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.id) {
            alert('问题添加成功！');
            
            // 重置表单
            document.getElementById('addProblemForm').reset();
            
            // 可选：跳转到问题列表页面
            // window.location.href = '/problems';
        } else {
            alert('添加失败: ' + (data.error || '未知错误'));
        }
    })
    .catch(error => {
        console.error('添加问题失败:', error);
        alert('添加失败: ' + error.message);
    })
    .finally(() => {
        // 恢复提交按钮
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    });
}

// 验证表单输入
function validateForm() {
    const title = document.getElementById('title').value.trim();
    const description = document.getElementById('description').value.trim();
    const phase = document.getElementById('phase').value;
    
    let isValid = true;
    let errors = [];
    
    if (!title) {
        errors.push('标题不能为空');
        isValid = false;
    }
    
    if (!description) {
        errors.push('描述不能为空');
        isValid = false;
    }
    
    if (!phase) {
        errors.push('请选择发现阶段');
        isValid = false;
    }
    
    if (errors.length > 0) {
        alert(errors.join('\n'));
    }
    
    return isValid;
}