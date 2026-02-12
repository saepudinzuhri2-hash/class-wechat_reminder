// 主要JavaScript功能

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    loadTeachingWeek();
    initWeekTypeSelectors();
});

// 加载教学周设置
function loadTeachingWeek() {
    fetch('/api/teaching-week')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const currentWeekSelect = document.getElementById('current_week');
                const totalWeeksSelect = document.getElementById('total_weeks');
                const semesterStartInput = document.getElementById('semester_start');
                
                if (currentWeekSelect && data.data.current_week) {
                    currentWeekSelect.value = data.data.current_week;
                }
                
                if (totalWeeksSelect && data.data.total_weeks) {
                    totalWeeksSelect.value = data.data.total_weeks;
                }
                
                if (semesterStartInput && data.data.semester_start) {
                    semesterStartInput.value = data.data.semester_start;
                }
            }
        })
        .catch(error => {
            console.error('加载教学周设置失败:', error);
        });
}

// 保存教学周设置
function saveTeachingWeek() {
    const currentWeek = document.getElementById('current_week').value;
    const totalWeeks = document.getElementById('total_weeks').value;
    const semesterStart = document.getElementById('semester_start').value;
    
    const data = {
        current_week: parseInt(currentWeek),
        total_weeks: parseInt(totalWeeks),
        semester_start: semesterStart
    };
    
    fetch('/api/teaching-week', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        const resultDiv = document.getElementById('teachingWeekResult');
        const alertDiv = document.getElementById('teachingWeekAlert');
        resultDiv.style.display = 'block';
        
        if (data.success) {
            alertDiv.className = 'alert alert-success';
            alertDiv.innerHTML = '<i class="bi bi-check-circle"></i> 教学周设置保存成功！';
        } else {
            alertDiv.className = 'alert alert-danger';
            alertDiv.innerHTML = '<i class="bi bi-x-circle"></i> 保存失败：' + data.error;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        const resultDiv = document.getElementById('teachingWeekResult');
        const alertDiv = document.getElementById('teachingWeekAlert');
        resultDiv.style.display = 'block';
        alertDiv.className = 'alert alert-danger';
        alertDiv.innerHTML = '<i class="bi bi-x-circle"></i> 保存失败，请重试';
    });
}

// 自动计算当前周
function autoCalcWeek() {
    fetch('/api/teaching-week/auto', { method: 'POST' })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(data.message);
            loadTeachingWeek();
        } else {
            alert('计算失败：' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('计算失败，请检查网络连接');
    });
}

// 初始化周次选择器事件
function initWeekTypeSelectors() {
    document.querySelectorAll('input[name="week_type"]').forEach(radio => {
        radio.addEventListener('change', function() {
            const customInput = document.getElementById('custom_week_input');
            if (customInput) {
                customInput.style.display = this.value === 'custom' ? 'block' : 'none';
            }
        });
    });
    
    document.querySelectorAll('input[name="edit_week_type"]').forEach(radio => {
        radio.addEventListener('change', function() {
            const customInput = document.getElementById('edit_custom_week_input');
            if (customInput) {
                customInput.style.display = this.value === 'custom' ? 'block' : 'none';
            }
        });
    });
}

// 添加课程
function submitAddCourse() {
    const form = document.getElementById('addCourseForm');
    const formData = new FormData(form);
    
    const name = formData.get('name');
    const dayOfWeek = formData.get('day_of_week');
    const startTime = formData.get('start_time');
    const endTime = formData.get('end_time');
    
    if (!name || !dayOfWeek || !startTime || !endTime) {
        alert('请填写所有必填字段');
        return;
    }
    
    const weekType = document.querySelector('input[name="week_type"]:checked').value;
    let weekPattern = 'all';
    
    if (weekType === 'custom') {
        const customWeeks = document.getElementById('custom_weeks').value.trim();
        if (!customWeeks) {
            alert('请填写自定义周次');
            return;
        }
        weekPattern = customWeeks;
    } else {
        weekPattern = weekType;
    }
    
    const courseData = {
        name: name,
        day_of_week: parseInt(dayOfWeek),
        start_time: startTime,
        end_time: endTime,
        location: formData.get('location') || '',
        remark: formData.get('remark') || '',
        week_pattern: weekPattern
    };
    
    fetch('/api/courses', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(courseData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const modal = bootstrap.Modal.getInstance(document.getElementById('addCourseModal'));
            modal.hide();
            window.location.reload();
        } else {
            alert('添加失败：' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('添加失败，请重试');
    });
}

// 编辑课程
function editCourse(courseId) {
    fetch(`/api/courses/${courseId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const course = data.course;
                document.getElementById('edit_course_id').value = course.id;
                document.getElementById('edit_name').value = course.name;
                document.getElementById('edit_day_of_week').value = course.day_of_week;
                document.getElementById('edit_start_time').value = course.start_time;
                document.getElementById('edit_end_time').value = course.end_time;
                document.getElementById('edit_location').value = course.location || '';
                document.getElementById('edit_remark').value = course.remark || '';
                
                // 设置周次选择
                const weekPattern = course.week_pattern || 'all';
                if (weekPattern === 'all') {
                    document.getElementById('edit_week_all').checked = true;
                } else if (weekPattern === 'odd') {
                    document.getElementById('edit_week_odd').checked = true;
                } else if (weekPattern === 'even') {
                    document.getElementById('edit_week_even').checked = true;
                } else {
                    document.getElementById('edit_week_custom').checked = true;
                    document.getElementById('edit_custom_weeks').value = weekPattern;
                    document.getElementById('edit_custom_week_input').style.display = 'block';
                }
                
                const modal = new bootstrap.Modal(document.getElementById('editCourseModal'));
                modal.show();
            } else {
                alert('获取课程信息失败：' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('获取课程信息失败');
        });
}

// 提交编辑
function submitEditCourse() {
    const form = document.getElementById('editCourseForm');
    const formData = new FormData(form);
    
    const courseId = formData.get('id');
    
    const weekType = document.querySelector('input[name="edit_week_type"]:checked').value;
    let weekPattern = 'all';
    
    if (weekType === 'custom') {
        const customWeeks = document.getElementById('edit_custom_weeks').value.trim();
        if (!customWeeks) {
            alert('请填写自定义周次');
            return;
        }
        weekPattern = customWeeks;
    } else {
        weekPattern = weekType;
    }
    
    const courseData = {
        name: formData.get('name'),
        day_of_week: parseInt(formData.get('day_of_week')),
        start_time: formData.get('start_time'),
        end_time: formData.get('end_time'),
        location: formData.get('location') || '',
        remark: formData.get('remark') || '',
        week_pattern: weekPattern
    };
    
    fetch(`/api/courses/${courseId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(courseData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const modal = bootstrap.Modal.getInstance(document.getElementById('editCourseModal'));
            modal.hide();
            window.location.reload();
        } else {
            alert('修改失败：' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('修改失败，请重试');
    });
}

// 删除课程
function deleteCourse(courseId, courseName) {
    if (confirm(`确定要删除课程 "${courseName}" 吗？`)) {
        fetch(`/api/courses/${courseId}`, { method: 'DELETE' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.reload();
            } else {
                alert('删除失败：' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('删除失败，请重试');
        });
    }
}

// 清空所有课程
function clearAllCourses() {
    if (confirm('确定要清空所有课程吗？此操作不可恢复！')) {
        fetch('/api/courses/clear', { method: 'DELETE' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('已清空所有课程');
                window.location.reload();
            } else {
                alert('清空失败：' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('清空失败，请重试');
        });
    }
}

// Excel上传
document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const fileInput = document.getElementById('excelFile');
            const file = fileInput.files[0];
            
            if (!file) {
                alert('请选择Excel文件');
                return;
            }
            
            const formData = new FormData();
            formData.append('file', file);
            
            const uploadBtn = document.getElementById('uploadBtn');
            const originalText = uploadBtn.innerHTML;
            uploadBtn.disabled = true;
            uploadBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> 上传中...';
            
            fetch('/api/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                const resultDiv = document.getElementById('uploadResult');
                const messageDiv = document.getElementById('uploadMessage');
                resultDiv.style.display = 'block';
                
                if (data.success) {
                    resultDiv.querySelector('.alert').className = 'alert alert-success';
                    messageDiv.innerHTML = `<strong><i class="bi bi-check-circle"></i> 导入成功！</strong><br>成功导入 ${data.count} 门课程`;
                    setTimeout(() => { window.location.href = '/'; }, 2000);
                } else {
                    resultDiv.querySelector('.alert').className = 'alert alert-danger';
                    messageDiv.innerHTML = `<strong><i class="bi bi-x-circle"></i> 导入失败</strong><br>${data.error}`;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                const resultDiv = document.getElementById('uploadResult');
                const messageDiv = document.getElementById('uploadMessage');
                resultDiv.style.display = 'block';
                resultDiv.querySelector('.alert').className = 'alert alert-danger';
                messageDiv.innerHTML = '<strong><i class="bi bi-x-circle"></i> 上传失败</strong><br>请检查网络连接后重试';
            })
            .finally(() => {
                uploadBtn.disabled = false;
                uploadBtn.innerHTML = originalText;
            });
        });
    }
    
    // 设置表单提交
    const settingsForm = document.getElementById('settingsForm');
    if (settingsForm) {
        settingsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(settingsForm);
            const settings = {
                pushplus_token: formData.get('pushplus_token'),
                skip_holidays: document.getElementById('skip_holidays').checked
            };
            
            fetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            })
            .then(response => response.json())
            .then(data => {
                const resultDiv = document.getElementById('settingsResult');
                const alertDiv = document.getElementById('settingsAlert');
                resultDiv.style.display = 'block';
                
                if (data.success) {
                    alertDiv.className = 'alert alert-success';
                    alertDiv.innerHTML = '<i class="bi bi-check-circle"></i> 设置保存成功！';
                } else {
                    alertDiv.className = 'alert alert-danger';
                    alertDiv.innerHTML = '<i class="bi bi-x-circle"></i> 保存失败：' + data.error;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                const resultDiv = document.getElementById('settingsResult');
                const alertDiv = document.getElementById('settingsAlert');
                resultDiv.style.display = 'block';
                alertDiv.className = 'alert alert-danger';
                alertDiv.innerHTML = '<i class="bi bi-x-circle"></i> 保存失败，请重试';
            });
        });
    }
});

// 测试Token连接
function testToken() {
    const token = document.getElementById('pushplus_token').value;
    
    if (!token) {
        alert('请先输入Token');
        return;
    }
    
    const btn = event.target;
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> 测试中...';
    
    fetch('/api/test-push', { method: 'POST' })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('连接测试成功！请检查您的微信是否收到测试消息。');
        } else {
            alert('连接测试失败：' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('测试失败，请检查网络连接');
    })
    .finally(() => {
        btn.disabled = false;
        btn.innerHTML = originalText;
    });
}
