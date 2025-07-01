#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查视频文件状态和修复常见问题的脚本
"""

import os
import subprocess
import sys

def check_ffmpeg():
    """检查是否安装了ffmpeg"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def get_video_info(file_path):
    """获取视频文件信息"""
    if not check_ffmpeg():
        print("❌ 未安装ffmpeg，无法获取详细视频信息")
        return None
    
    try:
        cmd = [
            'ffmpeg', '-i', file_path,
            '-f', 'null', '-'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # 解析输出获取视频信息
        output = result.stderr  # ffmpeg信息输出到stderr
        
        info = {}
        
        # 提取时长
        if 'Duration:' in output:
            duration_line = [line for line in output.split('\n') if 'Duration:' in line][0]
            info['duration'] = duration_line.split('Duration: ')[1].split(',')[0]
        
        # 提取分辨率
        if 'Video:' in output:
            video_line = [line for line in output.split('\n') if 'Video:' in line][0]
            if 'x' in video_line:
                resolution = video_line.split(',')[2].strip()
                info['resolution'] = resolution
        
        # 提取编码格式
        if 'Video:' in output:
            video_line = [line for line in output.split('\n') if 'Video:' in line][0]
            codec = video_line.split('Video: ')[1].split(' ')[0]
            info['codec'] = codec
        
        return info
    except Exception as e:
        print(f"❌ 获取视频信息失败: {e}")
        return None

def check_video_file(file_path):
    """检查单个视频文件"""
    print(f"\n📹 检查文件: {file_path}")
    
    if not os.path.exists(file_path):
        print("❌ 文件不存在")
        return False
    
    # 检查文件大小
    file_size = os.path.getsize(file_path)
    print(f"📊 文件大小: {file_size / (1024*1024):.2f} MB")
    
    if file_size < 1024*1024:  # 小于1MB
        print("⚠️  文件可能太小，可能不是有效的视频文件")
    
    # 检查文件扩展名
    if not file_path.lower().endswith('.mp4'):
        print("⚠️  文件不是MP4格式")
    
    # 获取视频信息
    info = get_video_info(file_path)
    if info:
        print(f"⏱️  时长: {info.get('duration', '未知')}")
        print(f"📐 分辨率: {info.get('resolution', '未知')}")
        print(f"🎬 编码: {info.get('codec', '未知')}")
        
        # 检查时长是否有效
        duration = info.get('duration', '')
        if duration and duration != '00:00:00.00':
            print("✅ 视频时长有效")
        else:
            print("❌ 视频时长无效，可能是损坏的文件")
            return False
    
    return True

def repair_video_file(input_path, output_path):
    """修复视频文件（重新编码）"""
    if not check_ffmpeg():
        print("❌ 需要安装ffmpeg才能修复视频文件")
        return False
    
    try:
        print(f"🔧 正在修复视频文件...")
        cmd = [
            'ffmpeg', '-i', input_path,
            '-c:v', 'libx264',  # 使用H.264编码
            '-c:a', 'aac',      # 使用AAC音频编码
            '-movflags', '+faststart',  # 优化网络播放
            '-y',  # 覆盖输出文件
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ 视频修复完成: {output_path}")
            return True
        else:
            print(f"❌ 视频修复失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 修复过程中出错: {e}")
        return False

def main():
    print("🎬 视频文件检查工具")
    print("=" * 50)
    
    # 检查MV目录
    mv_dir = "static/songMV"
    if not os.path.exists(mv_dir):
        print(f"❌ MV目录不存在: {mv_dir}")
        return
    
    # 查找所有视频文件
    video_files = []
    for file in os.listdir(mv_dir):
        if file.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            video_files.append(os.path.join(mv_dir, file))
    
    if not video_files:
        print(f"❌ 在 {mv_dir} 目录中未找到视频文件")
        return
    
    print(f"📁 找到 {len(video_files)} 个视频文件:")
    
    all_valid = True
    for video_file in video_files:
        is_valid = check_video_file(video_file)
        if not is_valid:
            all_valid = False
    
    print("\n" + "=" * 50)
    
    if all_valid:
        print("✅ 所有视频文件检查通过")
    else:
        print("❌ 发现视频文件问题")
        print("\n💡 建议解决方案:")
        print("1. 确保视频文件完整且未损坏")
        print("2. 使用ffmpeg重新编码视频文件")
        print("3. 检查视频文件格式是否为MP4")
        print("4. 确保视频文件有正确的元数据")
        
        # 询问是否要修复
        if check_ffmpeg():
            choice = input("\n是否要尝试修复有问题的视频文件？(y/n): ").lower()
            if choice == 'y':
                for video_file in video_files:
                    if not check_video_file(video_file):
                        backup_path = video_file + '.backup'
                        repair_path = video_file + '.fixed.mp4'
                        
                        print(f"\n🔧 修复文件: {video_file}")
                        
                        # 备份原文件
                        os.rename(video_file, backup_path)
                        
                        # 修复文件
                        if repair_video_file(backup_path, repair_path):
                            # 替换原文件
                            os.remove(backup_path)
                            os.rename(repair_path, video_file)
                            print(f"✅ 文件修复并替换完成")
                        else:
                            # 恢复原文件
                            os.rename(backup_path, video_file)
                            print(f"❌ 修复失败，已恢复原文件")
        else:
            print("\n💡 安装ffmpeg以获得更多功能:")
            print("Windows: 下载ffmpeg并添加到PATH")
            print("macOS: brew install ffmpeg")
            print("Linux: sudo apt install ffmpeg")

if __name__ == "__main__":
    main() 