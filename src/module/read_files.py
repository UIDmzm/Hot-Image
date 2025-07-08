

# module/read_files.py
import os
import xlrd

def read_column_from_xls(folder_path, column_index, sheet_name=None, start_row=0, end_row=None):
    """从文件夹中的Excel文件中读取指定列的数据
    
    Args:
        folder_path (str): 文件夹路径
        column_index (int): 要读取的列索引（0-based）
        sheet_name (str, optional): 工作表名称，默认为第一个工作表
        start_row (int): 起始行索引（0-based）
        end_row (int): 结束行索引（0-based，不包括此行）
    
    Returns:
        list: 包含每个文件数据的列表
    """
    all_data = []
    
    # 获取文件夹中的所有xls文件
    files = [f for f in os.listdir(folder_path) if f.endswith('.xls')]
    # 按照文件名中的数字顺序排序
    files.sort(key=lambda x: int(''.join(filter(str.isdigit, x))))
    
    for file in files:
        file_path = os.path.join(folder_path, file)
        
        # 确保文件存在
        if not os.path.isfile(file_path):
            print(f"文件不存在: {file_path}")
            continue
        
        try:
            workbook = xlrd.open_workbook(file_path)
            # 获取指定工作表，如果未指定则默认选择第一个工作表
            if sheet_name:
                sheet = workbook.sheet_by_name(sheet_name)
            else:
                sheet = workbook.sheet_by_index(0)
            
            # 确定结束行
            if end_row is None or end_row > sheet.nrows:
                end_row = sheet.nrows
            
            # 读取指定列的数据
            column_data = []
            for row_idx in range(start_row, end_row):
                try:
                    cell_value = sheet.cell_value(row_idx, column_index)
                    column_data.append(cell_value)
                except IndexError:
                    # 处理列索引超出范围的情况
                    break
            
            all_data.append(column_data)
        
        except Exception as e:
            print(f"读取文件 {file} 时出错: {str(e)}")
    
    return all_data


if __name__ == "__main__":
    read_column_from_xls()