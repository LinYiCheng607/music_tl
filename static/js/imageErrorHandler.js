// 设置所有图片加载失败时自动替换为默认图片

function handleImageError(img) {
    // 替换成你自己的默认图片路径（必须是静态目录下可访问的图片）
    img.onerror = null; // 防止死循环
    img.src = '/static/image/default_album.png';
}

// 可选：自动为所有图片添加onerror属性（页面加载完自动生效）
window.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('img').forEach(function(img) {
        img.onerror = function() {
            handleImageError(this);
        };
    });
});