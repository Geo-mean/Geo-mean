"""
地球化学模块初始化文件
geochemistry/__init__.py

导出地球化学分析相关的所有功能
"""

# 地球化学筛选管理器
try:
    from .geochem_filter_manager import (
        GeochemicalFilterManager,
        GeochemicalFilterPresets,
        create_filter_manager_from_processor
    )

    FILTER_MANAGER_AVAILABLE = True
except ImportError as e:
    print(f"[WARNING] 无法导入地球化学筛选管理器: {e}")
    FILTER_MANAGER_AVAILABLE = False

# 移动窗口分析集成接口
try:
    from .moving_window_integration import (
        MovingWindowIntegration,
        create_integration_from_processor,
        run_quick_moving_window_analysis
    )

    INTEGRATION_AVAILABLE = True
except ImportError as e:
    print(f"[WARNING] 无法导入移动窗口分析集成接口: {e}")
    INTEGRATION_AVAILABLE = False

# 边界分析器
try:
    from .boundary_analyzer import BoundaryAnalyzer
    BOUNDARY_ANALYZER_AVAILABLE = True
except ImportError as e:
    print(f"[WARNING] 无法导入边界分析器: {e}")
    BOUNDARY_ANALYZER_AVAILABLE = False

# 导出所有可用的功能
__all__ = []

if FILTER_MANAGER_AVAILABLE:
    __all__.extend([
        'GeochemicalFilterManager',
        'GeochemicalFilterPresets',
        'create_filter_manager_from_processor'
    ])

if INTEGRATION_AVAILABLE:
    __all__.extend([
        'MovingWindowIntegration',
        'create_integration_from_processor',
        'run_quick_moving_window_analysis'
    ])

if BOUNDARY_ANALYZER_AVAILABLE:
    __all__.extend([
        'BoundaryAnalyzer'
    ])

# 模块信息
__version__ = "1.0.0"
__author__ = "Geochemical Analysis Team"
__description__ = "地球化学数据移动窗口分析模块"


# 功能可用性检查
def check_module_availability():
    """检查模块功能可用性"""
    status = {
        'filter_manager': FILTER_MANAGER_AVAILABLE,
        'integration': INTEGRATION_AVAILABLE,
        'boundary_analyzer': BOUNDARY_ANALYZER_AVAILABLE,
        'all_available': FILTER_MANAGER_AVAILABLE and INTEGRATION_AVAILABLE and BOUNDARY_ANALYZER_AVAILABLE
    }

    print("[INFO] 地球化学模块功能可用性:")
    print(f"[INFO]   筛选管理器: {'✓' if status['filter_manager'] else '✗'}")
    print(f"[INFO]   集成接口: {'✓' if status['integration'] else '✗'}")
    print(f"[INFO]   边界分析器: {'✓' if status['boundary_analyzer'] else '✗'}")
    print(f"[INFO]   完整功能: {'✓' if status['all_available'] else '✗'}")

    return status


# 快速入门函数
def get_quick_start_guide():
    """获取快速入门指南"""
    guide = """
=== 地球化学移动窗口分析 - 快速入门指南 ===

1. 基本使用流程:
   from geochemistry import create_integration_from_processor

   # 创建集成接口
   integration = create_integration_from_processor(data_processor)

   # 获取推荐参数
   params = integration.get_recommended_analysis_parameters()

   # 运行分析
   success, message, results = integration.run_complete_analysis(params)

2. 快速分析（一键完成）:
   from geochemistry import run_quick_moving_window_analysis

   success, msg, results = run_quick_moving_window_analysis(
       data_processor, 'AGE', 'ThU', output_dir='/path/to/output'
   )

3. 主要功能模块:
   - MovingWindowIntegration: 高级集成接口
   - GeochemicalFilterManager: 地球化学数据筛选
   - BoundaryAnalyzer: 移动窗口边界处理分析

4. 所需数据列（自动检测）:
   - AGE: 年龄数据
   - SiO2, Lg_NbTh, Lg_Th, LOI: 地球化学筛选
   - ThU 或其他目标列: 分析目标

5. 输出结果:
   - CSV数据文件: 分析结果
   - PNG图表文件: 可视化结果
   - 筛选报告: 数据筛选统计

更多详细信息请参考各模块的文档。
    """
    return guide


def print_quick_start_guide():
    """打印快速入门指南"""
    print(get_quick_start_guide())


# 模块初始化检查
if __name__ == "__main__":
    check_module_availability()
    print_quick_start_guide()
else:
    # 在导入时进行简单的可用性检查
    status = check_module_availability()
    if not status['all_available']:
        print("[WARNING] 地球化学模块部分功能不可用，请检查依赖项")
    else:
        print("[SUCCESS] 地球化学模块已成功加载，所有功能可用")