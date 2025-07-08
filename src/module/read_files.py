

# module/read_files.py
import os
import xlrd


def get_excel_files_info(folder_path):
    """获取文件夹中Excel文件的信息（文件名、路径、行数）

    Args:
        folder_path (str): 文件夹路径

    Returns:
        list: 包含文件信息的元组列表 (file_name, file_path, row_count)
    """
    files_info = []

    if not os.path.isdir(folder_path):
        return files_info

    # 获取所有xls文件
    all_files = [f for f in os.listdir(folder_path) if f.endswith('.xls')]

    # 按照文件名中的数字顺序排序
    all_files.sort(key=lambda x: int(''.join(filter(str.isdigit, x))))

    for file in all_files:
        file_path = os.path.join(folder_path, file)
        row_count = 0

        try:
            workbook = xlrd.open_workbook(file_path)
            sheet = workbook.sheet_by_index(0)
            row_count = sheet.nrows
        except Exception:
            row_count = 0

        files_info.append((file, file_path, row_count))

    return files_info


def read_column_from_xls(file_paths, column_index, start_row=1, end_row=None):
    """从指定的Excel文件中读取指定列的数据

    Args:
        file_paths (list): 文件路径列表
        column_index (int): 要读取的列索引（0-based）
        start_row (int): 起始行索引（0-based）
        end_row (int): 结束行索引（0-based，不包括此行）

    Returns:
        list: 包含每个文件数据的列表
    """
    all_data = []
    for file_path in file_paths:
        # 确保文件存在
        if not os.path.isfile(file_path):
            print(f"文件不存在: {file_path}")
            continue

        try:
            workbook = xlrd.open_workbook(file_path)
            sheet = workbook.sheet_by_index(0)

            # 确定结束行
            nrows = sheet.nrows
            if end_row is None or end_row > nrows:
                use_end_row = nrows
            else:
                use_end_row = end_row

            # 读取指定列的数据
            column_data = []
            for row_idx in range(start_row, use_end_row):
                try:
                    cell_value = sheet.cell_value(row_idx, column_index)
                    column_data.append(cell_value)
                except IndexError:
                    # 处理列索引超出范围的情况
                    break

            all_data.append(column_data)

        except Exception as e:
            print(f"读取文件 {os.path.basename(file_path)} 时出错: {str(e)}")
    print(all_data)
    return all_data


if __name__ == "__main__":
    get_excel_files_info()
    read_column_from_xls()