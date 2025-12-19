// 
// CSV导入页面的JavaScript功能
// import_csv.js
// 

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 绑定表单提交事件
    document.getElementById('csvUploadForm').addEventListener('submit', function(e) {
        e.preventDefault();
        uploadCSVFile();
    });
});

// 上传CSV文件
function uploadCSVFile() {
    const fileInput = document.getElementById('csvFile');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('请选择要上传的CSV文件');
        return;
    }
    
    // 检查文件类型
    if (!file.name.toLowerCase().endsWith('.csv')) {
        alert('请选择CSV格式的文件');
        return;
    }
    
    // 检查文件大小（限制100MB，放宽限制）
    if (file.size > 100 * 1024 * 1024) {
        alert('文件大小不能超过100MB');
        return;
    }
    
    const formData = new FormData();
    formData.append('csvFile', file);
    
    // 显示上传进度
    document.getElementById('uploadProgress').style.display = 'block';
    document.getElementById('uploadResult').style.display = 'none';
    
    // 禁用提交按钮
    const submitBtn = document.querySelector('#csvUploadForm button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 上传中...';
    submitBtn.disabled = true;
    
    // 更新进度条
    updateProgress(0, '开始上传...');
    
    fetch('/api/import-csv', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw err; });
        }
        return response.json();
    })
    .then(data => {
        updateProgress(100, '上传完成');
        
        // 显示成功结果
        document.getElementById('successMessage').textContent = 
            `CSV文件导入成功！导入了 ${data.importedCount} 条记录，总共处理了 ${data.totalCount} 条记录。`;
        document.getElementById('successResult').style.display = 'block';
        document.getElementById('errorResult').style.display = 'none';
        document.getElementById('uploadResult').style.display = 'block';
        
        // 滚动到结果区域
        document.getElementById('uploadResult').scrollIntoView({ behavior: 'smooth' });
    })
    .catch(error => {
        console.error('CSV导入失败:', error);
        
        // 显示错误结果
        document.getElementById('errorMessage').textContent = 
            error.error || error.message || 'CSV导入失败';
        document.getElementById('errorResult').style.display = 'block';
        document.getElementById('successResult').style.display = 'none';
        document.getElementById('uploadResult').style.display = 'block';
        
        // 滚动到结果区域
        document.getElementById('uploadResult').scrollIntoView({ behavior: 'smooth' });
    })
    .finally(() => {
        // 恢复提交按钮
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    });
}

// 更新上传进度
function updateProgress(percent, text) {
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    
    progressBar.style.width = percent + '%';
    progressBar.textContent = percent + '%';
    progressText.textContent = text;
}

// 文件选择事件
document.getElementById('csvFile').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        // 这里可以添加文件预览或验证逻辑
        console.log('选择的文件:', file.name);
    }
});